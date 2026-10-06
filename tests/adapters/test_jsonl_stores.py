import json
from datetime import date
from pathlib import Path

import pytest

from regradar.adapters.jsonl_dead_letter_store import JsonlDeadLetterStore
from regradar.adapters.jsonl_raw_store import JsonlRawStore
from regradar.core.application.errors import SystemicError
from regradar.core.application.ports.raw_document import RawDocument
from regradar.core.domain.window import Window, WindowField

WINDOW = Window(start=date(2026, 9, 1), end=date(2026, 9, 30))


def test_raw_store_round_trip(tmp_path: Path) -> None:
    store = JsonlRawStore(tmp_path, "dip_procedure")
    documents: list[RawDocument] = [{"id": "1", "titel": "Ä"}, {"id": "2"}]

    store.save(WINDOW, documents)

    assert store.load(WINDOW) == documents
    assert store.path(WINDOW).name == (
        "dip_procedure_date_2026-09-01_2026-09-30.jsonl"
    )


def test_raw_store_key_includes_field(tmp_path: Path) -> None:
    store = JsonlRawStore(tmp_path, "dip_procedure")
    updated = Window(WINDOW.start, WINDOW.end, WindowField.UPDATED)

    store.save(WINDOW, [])

    assert store.load(WINDOW) == []
    assert store.load(updated) is None


def test_raw_store_rejects_corrupt_file(tmp_path: Path) -> None:
    store = JsonlRawStore(tmp_path, "dip_procedure")
    store.path(WINDOW).write_text('{"id": "1"}\n{"id', encoding="utf-8")

    with pytest.raises(SystemicError, match="--refresh"):
        store.load(WINDOW)


def test_dead_letters_append_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "raw" / "dead_letters.jsonl"
    store = JsonlDeadLetterStore(path)

    store.add({"id": "1"}, "missing titel")
    store.add({"id": "2", "titel": "Ä"}, "bad id")

    entries = [json.loads(line) for line in path.read_text().splitlines()]
    assert [e["document"] for e in entries] == [
        {"id": "1"},
        {"id": "2", "titel": "Ä"},
    ]
    assert [e["error"] for e in entries] == ["missing titel", "bad id"]
    assert all(e["failed_at"].endswith("+00:00") for e in entries)
