from dataclasses import dataclass, field

import structlog

from regradar.core.application.errors import InvalidDocumentError
from regradar.core.application.ports.dead_letter_store import DeadLetterStore
from regradar.core.application.ports.procedure_source import ProcedureSource
from regradar.core.application.ports.raw_document import RawDocument
from regradar.core.application.ports.raw_store import RawStore
from regradar.core.domain.procedure import Procedure
from regradar.core.domain.window import Window

log = structlog.get_logger()

MAX_FAILURE_RATE = 0.05


@dataclass(frozen=True)
class RunSummary:
    loaded: int
    stored: int
    discarded: int
    failed: int

    @property
    def reconciles(self) -> bool:
        return self.loaded == self.stored + self.discarded + self.failed

    @property
    def failure_rate(self) -> float:
        return self.failed / self.loaded if self.loaded else 0.0

    @property
    def succeeded(self) -> bool:
        return self.reconciles and self.failure_rate <= MAX_FAILURE_RATE


@dataclass
class IngestResult:
    window: Window
    summary: RunSummary
    procedures: list[Procedure] = field(default_factory=list)


@dataclass(frozen=True)
class IngestDependencies:
    source: ProcedureSource
    raw_store: RawStore
    dead_letters: DeadLetterStore


def ingest(
    window: Window, deps: IngestDependencies, *, refresh: bool
) -> IngestResult:
    raw_documents = _load_raw(window, deps, refresh=refresh)
    procedures: list[Procedure] = []
    seen: set[str] = set()
    failed = duplicates = 0
    for raw in raw_documents:
        procedure = _parse(raw, deps)
        if procedure is None:
            failed += 1
        elif procedure.source_id in seen:
            # Pagination over a changing result set can repeat entries.
            duplicates += 1
        else:
            seen.add(procedure.source_id)
            procedures.append(procedure)
    summary = RunSummary(
        loaded=len(raw_documents),
        stored=len(procedures),
        discarded=duplicates,
        failed=failed,
    )
    return IngestResult(window, summary, procedures)


def _load_raw(
    window: Window, deps: IngestDependencies, *, refresh: bool
) -> list[RawDocument]:
    stored = None if refresh else deps.raw_store.load(window)
    if stored is not None:
        log.info("raw_data_reused", documents=len(stored))
        return stored
    documents = list(deps.source.fetch(window))
    deps.raw_store.save(window, documents)
    log.info("fetched", documents=len(documents))
    return documents


def _parse(raw: RawDocument, deps: IngestDependencies) -> Procedure | None:
    try:
        return deps.source.parse(raw)
    except InvalidDocumentError as err:
        log.exception("invalid_document", document_id=raw.get("id"))
        deps.dead_letters.add(raw, str(err))
        return None
