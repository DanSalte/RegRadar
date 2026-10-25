import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from regradar.core.domain.procedure import Procedure

type FieldTexts = Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class KeywordGroup:
    name: str
    label: str
    terms: tuple[str, ...] = ()
    acronyms: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()


@dataclass(frozen=True)
class KeywordHit:
    keyword_group: str
    term: str
    field: str


class KeywordMatcher:
    def __init__(self, groups: Sequence[KeywordGroup]) -> None:
        self._groups = tuple(groups)

    def match(self, procedure: Procedure) -> list[KeywordHit]:
        fields = _field_texts(procedure)
        hits: list[KeywordHit] = []
        for group in self._groups:
            if not _is_excluded(group, fields):
                hits.extend(_group_hits(group, fields))
        return hits


def _field_texts(procedure: Procedure) -> FieldTexts:
    return {
        "title": (procedure.title,),
        "abstract": (procedure.abstract,) if procedure.abstract else (),
        "descriptors": tuple(d.name for d in procedure.descriptors),
        "subject_areas": procedure.subject_areas,
    }


def _is_excluded(group: KeywordGroup, fields: FieldTexts) -> bool:
    # An exclude term anywhere in the procedure drops the whole group, so a
    # single false friend cannot leave a stray hit in another field.
    return any(
        _has_term(term, text)
        for term in group.exclude
        for texts in fields.values()
        for text in texts
    )


def _group_hits(group: KeywordGroup, fields: FieldTexts) -> list[KeywordHit]:
    hits: list[KeywordHit] = []
    for field, texts in fields.items():
        hits += [
            KeywordHit(group.name, term, field)
            for term in group.terms
            if any(_has_term(term, text) for text in texts)
        ]
        hits += [
            KeywordHit(group.name, acronym, field)
            for acronym in group.acronyms
            if any(_has_acronym(acronym, text) for text in texts)
        ]
    return hits


def _has_term(term: str, text: str) -> bool:
    return term.casefold() in text.casefold()


def _has_acronym(acronym: str, text: str) -> bool:
    pattern = rf"(?<!\w){re.escape(acronym)}(?!\w)"
    return re.search(pattern, text) is not None
