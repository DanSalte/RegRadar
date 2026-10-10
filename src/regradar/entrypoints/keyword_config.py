from pathlib import Path
from typing import Annotated

import pydantic
import yaml

from regradar.core.application.errors import ConfigurationError
from regradar.core.domain.keyword_matcher import KeywordGroup

# An empty term would match every procedure.
Term = Annotated[str, pydantic.StringConstraints(min_length=1)]


class _GroupConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

    label: str
    terms: tuple[Term, ...] = ()
    acronyms: tuple[Term, ...] = ()
    exclude: tuple[Term, ...] = ()

    @pydantic.model_validator(mode="after")
    def _has_search_terms(self) -> _GroupConfig:
        if not self.terms and not self.acronyms:
            msg = "a group needs at least one term or acronym"
            raise ValueError(msg)
        return self


class _KeywordConfig(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid", frozen=True)

    groups: dict[str, _GroupConfig] = pydantic.Field(min_length=1)


def load_keyword_groups(path: Path) -> tuple[KeywordGroup, ...]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        config = _KeywordConfig.model_validate(data)
    except (OSError, yaml.YAMLError, pydantic.ValidationError) as err:
        msg = f"invalid keyword configuration: {path}"
        raise ConfigurationError(msg) from err
    return tuple(
        KeywordGroup(
            name=name,
            label=group.label,
            terms=group.terms,
            acronyms=group.acronyms,
            exclude=group.exclude,
        )
        for name, group in config.groups.items()
    )
