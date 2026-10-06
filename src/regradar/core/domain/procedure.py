from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Descriptor:
    name: str
    kind: str


@dataclass(frozen=True)
class Procedure:
    source: str
    source_id: str
    source_url: str
    title: str
    procedure_type: str
    updated: datetime
    date: date | None = None
    abstract: str | None = None
    status: str | None = None
    subject_areas: tuple[str, ...] = ()
    descriptors: tuple[Descriptor, ...] = ()
    initiative: tuple[str, ...] = ()
