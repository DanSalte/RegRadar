from typing import Protocol

from regradar.core.application.ports.raw_document import RawDocument
from regradar.core.domain.window import Window


class RawStore(Protocol):
    def load(self, window: Window) -> list[RawDocument] | None: ...

    def save(self, window: Window, documents: list[RawDocument]) -> None: ...
