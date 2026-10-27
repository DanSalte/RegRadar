from datetime import date

from regradar.adapters.markdown_exploration_report import (
    render_exploration_report,
)
from regradar.core.application.explore import explore
from regradar.core.domain.keyword_matcher import KeywordGroup
from regradar.core.domain.window import Window
from tests.factories import make_procedure

WINDOW = Window(start=date(2026, 9, 1), end=date(2026, 9, 7))
BANKS = KeywordGroup("banks", "Banken", terms=("Kreditinstitut",))


def test_renders_sections_with_german_numbers_and_source() -> None:
    procedures = [
        make_procedure("1", title="Kreditinstitute"),
        make_procedure("2", title="Haushalt"),
        make_procedure("3", title="Verkehr"),
    ]

    text = render_exploration_report(explore(WINDOW, procedures, [BANKS]))

    assert text.startswith("# DIP-Exploration\n")
    assert "- Treffer: 1 (33,3 %)" in text
    assert "| Banken | 1 | 33,3 % |" in text
    assert "| Gesetzgebung | 3 | 1 | 33,3 % |" in text
    assert "## Top-10-Sachgebiete der Treffer" in text
    assert "Quelle: Deutscher Bundestag/Bundesrat – DIP" in text


def test_empty_window_shows_dash_instead_of_share() -> None:
    text = render_exploration_report(explore(WINDOW, [], [BANKS]))

    assert "- Treffer: 0 (–)" in text
    assert "| Banken | 0 | – |" in text
