from typing import Protocol

from regradar.core.application.ports.raw_document import RawDocument


class DeadLetterStore(Protocol):
    def add(self, raw: RawDocument, error: str) -> None: ...
