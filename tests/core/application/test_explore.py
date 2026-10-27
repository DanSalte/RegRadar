from collections import Counter
from dataclasses import replace
from datetime import date

import pytest

from regradar.core.application.explore import explore
from regradar.core.domain.keyword_matcher import KeywordGroup
from regradar.core.domain.procedure import Descriptor
from regradar.core.domain.window import Window
from tests.factories import make_procedure

WINDOW = Window(start=date(2026, 9, 1), end=date(2026, 9, 14))
BANKS = KeywordGroup("banks", "Banken", terms=("Kreditinstitut",))
CYBER = KeywordGroup("cyber", "Cyber", terms=("Cyber",))


def test_counts_totals_hits_and_weeks() -> None:
    procedures = [
        make_procedure("1", title="Kreditinstitute", day=date(2026, 9, 1)),
        make_procedure("2", title="Haushalt", day=date(2026, 9, 8)),
        make_procedure("3", title="Cyberabwehr", day=None),
    ]

    report = explore(WINDOW, procedures, [BANKS, CYBER])

    assert (report.total, report.hits) == (len(procedures), 2)
    assert report.weeks == Counter(
        {"2026-W36": 1, "2026-W37": 1, "ohne Datum": 1}
    )
    assert report.per_week == pytest.approx(1.5)


def test_counts_each_group_once_per_procedure_in_config_order() -> None:
    procedure = make_procedure(
        title="Kreditinstitute", abstract="Kreditinstitute und Cyber"
    )

    report = explore(WINDOW, [procedure], [CYBER, BANKS])

    assert [(g.name, n) for g, n in report.groups] == [
        ("cyber", 1),
        ("banks", 1),
    ]
    assert report.hit_fields == Counter({"title": 1, "abstract": 1})


def test_metadata_coverage_and_metadata_only_hits() -> None:
    via_metadata = replace(
        make_procedure("1", title="Haushalt"),
        descriptors=(Descriptor("Kreditinstitut", "Sachbegriffe"),),
        subject_areas=("Wirtschaft",),
    )
    via_title = replace(
        make_procedure("2", title="Kreditinstitute", abstract="Text"),
        subject_areas=("Wirtschaft", "Recht"),
    )

    report = explore(WINDOW, [via_metadata, via_title], [BANKS])

    assert report.coverage == Counter(
        {"abstract": 1, "descriptors": 1, "subject_areas": 2}
    )
    assert report.metadata_only == 1
    assert report.hit_subject_areas == Counter({"Wirtschaft": 2, "Recht": 1})


def test_procedure_types_total_and_hits() -> None:
    procedures = [
        make_procedure("1", title="Kreditinstitute"),
        replace(make_procedure("2"), procedure_type="Kleine Anfrage"),
    ]

    report = explore(WINDOW, procedures, [BANKS])

    assert report.procedure_types == Counter(
        {"Gesetzgebung": 1, "Kleine Anfrage": 1}
    )
    assert report.hit_procedure_types == Counter({"Gesetzgebung": 1})
