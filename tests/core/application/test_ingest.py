from collections.abc import Iterator
from datetime import date

import pytest
from structlog.testing import capture_logs

from regradar.core.application.errors import InvalidDocumentError
from regradar.core.application.ingest import (
    IngestDependencies,
    RunSummary,
    ingest,
)
from regradar.core.application.ports.raw_document import RawDocument
from regradar.core.domain.procedure import Procedure
from regradar.core.domain.window import Window
from tests.factories import make_procedure

WINDOW = Window(start=date(2026, 9, 1), end=date(2026, 9, 30))


class FakeSource:
    def __init__(self, documents: list[RawDocument]) -> None:
        self.documents = documents
        self.fetches = 0

    def fetch(self, window: Window) -> Iterator[RawDocument]:
        self.fetches += 1
        yield from self.documents

    def parse(self, raw: RawDocument) -> Procedure:
        if raw.get("invalid"):
            msg = f"document {raw['id']} is invalid"
            raise InvalidDocumentError(msg)
        return make_procedure(str(raw["id"]), title=str(raw["title"]))


class FakeRawStore:
    def __init__(self, documents: list[RawDocument] | None = None) -> None:
        self.documents = documents
        self.saved: list[list[RawDocument]] = []

    def load(self, window: Window) -> list[RawDocument] | None:
        return self.documents

    def save(self, window: Window, documents: list[RawDocument]) -> None:
        self.saved.append(documents)


class FakeDeadLetters:
    def __init__(self) -> None:
        self.entries: list[tuple[RawDocument, str]] = []

    def add(self, raw: RawDocument, error: str) -> None:
        self.entries.append((raw, error))


def deps(
    source: FakeSource,
    store: FakeRawStore | None = None,
    dead_letters: FakeDeadLetters | None = None,
) -> IngestDependencies:
    return IngestDependencies(
        source=source,
        raw_store=store or FakeRawStore(),
        dead_letters=dead_letters or FakeDeadLetters(),
    )


def test_fetches_parses_and_stores() -> None:
    documents: list[RawDocument] = [
        {"id": "1", "title": "DORA"},
        {"id": "2", "title": "Haushalt"},
    ]
    source, store = FakeSource(documents), FakeRawStore()

    result = ingest(WINDOW, deps(source, store), refresh=False)

    assert store.saved == [documents]
    assert [p.title for p in result.procedures] == ["DORA", "Haushalt"]
    assert result.summary == RunSummary(
        loaded=2, stored=2, discarded=0, failed=0
    )


def test_stored_raw_data_skips_source() -> None:
    source = FakeSource([])
    store = FakeRawStore([{"id": "1", "title": "DORA"}])

    result = ingest(WINDOW, deps(source, store), refresh=False)

    assert source.fetches == 0
    assert store.saved == []
    assert result.summary.stored == 1


def test_refresh_ignores_stored_raw_data() -> None:
    source = FakeSource([{"id": "2", "title": "neu"}])
    store = FakeRawStore([{"id": "1", "title": "alt"}])

    result = ingest(WINDOW, deps(source, store), refresh=True)

    assert source.fetches == 1
    assert [p.source_id for p in result.procedures] == ["2"]


def test_invalid_document_goes_to_dead_letters() -> None:
    bad: RawDocument = {"id": "2", "invalid": True}
    source = FakeSource([{"id": "1", "title": "ok"}, bad])
    dead_letters = FakeDeadLetters()

    with capture_logs() as logs:
        result = ingest(
            WINDOW, deps(source, dead_letters=dead_letters), refresh=False
        )

    assert dead_letters.entries == [(bad, "document 2 is invalid")]
    assert result.summary == RunSummary(
        loaded=2, stored=1, discarded=0, failed=1
    )
    error = next(e for e in logs if e["event"] == "invalid_document")
    assert error["exc_info"] is True
    assert error["document_id"] == "2"


def test_duplicates_are_discarded() -> None:
    source = FakeSource([{"id": "1", "title": "a"}, {"id": "1", "title": "a"}])

    result = ingest(WINDOW, deps(source), refresh=False)

    assert result.summary == RunSummary(
        loaded=2, stored=1, discarded=1, failed=0
    )


@pytest.mark.parametrize(
    ("summary", "reconciles", "succeeded"),
    [
        (RunSummary(loaded=0, stored=0, discarded=0, failed=0), True, True),
        (RunSummary(loaded=20, stored=19, discarded=0, failed=1), True, True),
        (RunSummary(loaded=19, stored=17, discarded=0, failed=2), True, False),
        (RunSummary(loaded=3, stored=1, discarded=1, failed=0), False, False),
    ],
)
def test_run_summary(
    summary: RunSummary, reconciles: bool, succeeded: bool
) -> None:
    assert summary.reconciles is reconciles
    assert summary.succeeded is succeeded


def test_failure_rate_without_documents_is_zero() -> None:
    summary = RunSummary(loaded=0, stored=0, discarded=0, failed=0)

    assert summary.failure_rate == 0.0
