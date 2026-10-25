from dataclasses import replace

import pytest

from regradar.core.domain.keyword_matcher import (
    KeywordGroup,
    KeywordHit,
    KeywordMatcher,
)
from regradar.core.domain.procedure import Descriptor
from tests.factories import make_procedure

BANKS = KeywordGroup(
    name="banks", label="Banken", terms=("Kreditinstitut",), acronyms=("KWG",)
)


def test_term_matches_substring_ignoring_case() -> None:
    procedure = make_procedure(title="Aufsicht über KREDITINSTITUTE")

    hits = KeywordMatcher([BANKS]).match(procedure)

    assert hits == [KeywordHit("banks", "Kreditinstitut", "title")]


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Änderung des KWG", True),
        ("KWG-Novelle", True),
        ("(KWG)", True),
        ("KWGX-Verordnung", False),
        ("Änderung des kwg", False),
        ("XKWG", False),
    ],
)
def test_acronym_needs_word_boundaries_and_exact_case(
    title: str, *, expected: bool
) -> None:
    hits = KeywordMatcher([BANKS]).match(make_procedure(title=title))

    assert (KeywordHit("banks", "KWG", "title") in hits) is expected


def test_reports_each_field_with_a_hit() -> None:
    procedure = replace(
        make_procedure(title="Titel", abstract="Pflichten für Kreditinstitute"),
        descriptors=(Descriptor("Kreditinstitut", "Sachbegriffe"),),
        subject_areas=("Kreditinstitute und KWG",),
    )

    hits = KeywordMatcher([BANKS]).match(procedure)

    assert hits == [
        KeywordHit("banks", "Kreditinstitut", "abstract"),
        KeywordHit("banks", "Kreditinstitut", "descriptors"),
        KeywordHit("banks", "Kreditinstitut", "subject_areas"),
        KeywordHit("banks", "KWG", "subject_areas"),
    ]


def test_exclude_anywhere_drops_all_hits_of_the_group() -> None:
    cyber = KeywordGroup(
        name="cyber", label="Cyber", terms=("Cyber",), exclude=("Cybermobbing",)
    )
    procedure = make_procedure(
        title="Cyberangriffe", abstract="Schutz vor Cybermobbing"
    )

    hits = KeywordMatcher([cyber, BANKS]).match(procedure)

    assert hits == []


def test_exclude_does_not_affect_other_groups() -> None:
    cyber = KeywordGroup(
        name="cyber", label="Cyber", terms=("Cyber",), exclude=("Cybermobbing",)
    )
    procedure = make_procedure(title="Cybermobbing bei Kreditinstituten")

    hits = KeywordMatcher([cyber, BANKS]).match(procedure)

    assert hits == [KeywordHit("banks", "Kreditinstitut", "title")]


def test_no_hits_for_unrelated_procedure() -> None:
    procedure = make_procedure(title="Verkehrswegeplan", abstract=None)

    assert KeywordMatcher([BANKS]).match(procedure) == []
