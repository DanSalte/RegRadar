"""Building block (DIP adapter): DTOs that validate DIP API responses."""

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class _DipModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")


class DipDescriptorDto(_DipModel):
    name: str
    kind: str = Field(validation_alias="typ")


class DipProcedureDto(_DipModel):
    id: str = Field(pattern=r"^\d+$")
    title: str = Field(validation_alias="titel")
    procedure_type: str = Field(validation_alias="vorgangstyp")
    updated: dt.datetime = Field(validation_alias="aktualisiert")
    date: dt.date | None = Field(default=None, validation_alias="datum")
    abstract: str | None = None
    status: str | None = Field(default=None, validation_alias="beratungsstand")
    subject_areas: list[str] = Field(
        default_factory=list, validation_alias="sachgebiet"
    )
    descriptors: list[DipDescriptorDto] = Field(
        default_factory=list, validation_alias="deskriptor"
    )
    initiative: list[str] = Field(default_factory=list)


class DipPageDto(_DipModel):
    cursor: str
    num_found: int = Field(validation_alias="numFound")
    documents: list[dict[str, object]]
