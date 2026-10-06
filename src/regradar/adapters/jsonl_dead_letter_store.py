import json
from datetime import UTC, datetime
from pathlib import Path

from regradar.core.application.ports.raw_document import RawDocument


class JsonlDeadLetterStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def add(self, raw: RawDocument, error: str) -> None:
        entry = {
            "failed_at": datetime.now(UTC).isoformat(),
            "error": error,
            "document": raw,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
