from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from regradar.core.domain.keyword_matcher import (
    KeywordGroup,
    KeywordHit,
    KeywordMatcher,
)
from regradar.core.domain.procedure import Procedure
from regradar.core.domain.window import Window

METADATA_FIELDS = frozenset({"descriptors", "subject_areas"})
TOP_SUBJECT_AREAS = 10
DAYS_PER_WEEK = 7


@dataclass(frozen=True)
class ExplorationReport:
    window: Window
    total: int
    hits: int
    weeks: Counter[str]
    coverage: Counter[str]
    groups: tuple[tuple[KeywordGroup, int], ...]
    hit_fields: Counter[str]
    metadata_only: int
    procedure_types: Counter[str]
    hit_procedure_types: Counter[str]
    hit_subject_areas: Counter[str]

    @property
    def per_week(self) -> float:
        days = (self.window.end - self.window.start).days + 1
        return self.total / days * DAYS_PER_WEEK


def explore(
    window: Window,
    procedures: Sequence[Procedure],
    groups: Sequence[KeywordGroup],
) -> ExplorationReport:
    matcher = KeywordMatcher(groups)
    matched = [(p, hits) for p in procedures if (hits := matcher.match(p))]
    hit_procedures = [p for p, _ in matched]
    hit_lists = [hits for _, hits in matched]
    group_counts = _distinct_counts(hit_lists, lambda h: h.keyword_group)
    return ExplorationReport(
        window=window,
        total=len(procedures),
        hits=len(matched),
        weeks=Counter(map(_week, procedures)),
        coverage=_coverage(procedures),
        groups=tuple((g, group_counts[g.name]) for g in groups),
        hit_fields=_distinct_counts(hit_lists, lambda h: h.field),
        metadata_only=sum(map(_metadata_only, hit_lists)),
        procedure_types=_procedure_types(procedures),
        hit_procedure_types=_procedure_types(hit_procedures),
        hit_subject_areas=_subject_areas(hit_procedures),
    )


def _distinct_counts(
    hit_lists: Sequence[Sequence[KeywordHit]],
    key: Callable[[KeywordHit], str],
) -> Counter[str]:
    """Counts procedures per key, not hits."""
    return Counter(value for hits in hit_lists for value in set(map(key, hits)))


def _procedure_types(procedures: Sequence[Procedure]) -> Counter[str]:
    return Counter(p.procedure_type for p in procedures)


def _subject_areas(procedures: Sequence[Procedure]) -> Counter[str]:
    return Counter(area for p in procedures for area in p.subject_areas)


def _week(procedure: Procedure) -> str:
    if procedure.date is None:
        return "ohne Datum"
    year, week, _ = procedure.date.isocalendar()
    return f"{year}-W{week:02d}"


def _coverage(procedures: Sequence[Procedure]) -> Counter[str]:
    return Counter(
        {
            "abstract": sum(bool(p.abstract) for p in procedures),
            "descriptors": sum(bool(p.descriptors) for p in procedures),
            "subject_areas": sum(bool(p.subject_areas) for p in procedures),
        }
    )


def _metadata_only(hits: Sequence[KeywordHit]) -> bool:
    # Hits only via descriptors or subject areas show how much the
    # documentalists' metadata adds beyond title and abstract.
    return all(h.field in METADATA_FIELDS for h in hits)
