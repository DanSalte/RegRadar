import json
from pathlib import Path

import structlog

from regradar.adapters.shared.file_writer import write_file_atomically
from regradar.core.application.errors import SystemicError
from regradar.core.application.ports.raw_document import RawDocument
from regradar.core.domain.window import Window

log = structlog.get_logger()


class JsonlRawStore:
    def __init__(self, directory: Path, name: str) -> None:
        self._directory = directory
        self._name = name

    def path(self, window: Window) -> Path:
        stem = f"{self._name}_{window.field}_{window.start}_{window.end}"
        return self._directory / f"{stem}.jsonl"

    def load(self, window: Window) -> list[RawDocument] | None:
        path = self.path(window)
        if not path.exists():
            return None
        try:
            return [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line
            ]
        except json.JSONDecodeError as err:
            msg = f"Corrupt raw data file {path}; rerun with --refresh"
            raise SystemicError(msg) from err

    def save(self, window: Window, documents: list[RawDocument]) -> None:
        lines = (json.dumps(doc, ensure_ascii=False) for doc in documents)
        write_file_atomically(
            self.path(window), "".join(f"{ln}\n" for ln in lines)
        )
        log.info("raw_data_stored", path=str(self.path(window)))
