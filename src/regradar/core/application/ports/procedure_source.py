from collections.abc import Iterator
from typing import Protocol

from regradar.core.application.ports.raw_document import RawDocument
from regradar.core.domain.procedure import Procedure
from regradar.core.domain.window import Window


class ProcedureSource(Protocol):
    def fetch(self, window: Window) -> Iterator[RawDocument]: ...

    def parse(self, raw: RawDocument) -> Procedure: ...
