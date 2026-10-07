from datetime import date

import pytest

from regradar.core.domain.window import Window, WindowField


def test_window_defaults_to_date_field() -> None:
    window = Window(start=date(2026, 9, 1), end=date(2026, 9, 30))

    assert window.field is WindowField.DATE


def test_window_rejects_start_after_end() -> None:
    with pytest.raises(ValueError, match="after end"):
        Window(start=date(2026, 9, 2), end=date(2026, 9, 1))


@pytest.mark.parametrize(
    ("today", "months", "start"),
    [
        (date(2026, 10, 5), 1, date(2026, 9, 5)),
        (date(2026, 10, 5), 6, date(2026, 4, 5)),
        (date(2026, 1, 15), 1, date(2025, 12, 15)),
        (date(2026, 3, 31), 1, date(2026, 2, 28)),
        (date(2024, 3, 31), 1, date(2024, 2, 29)),
    ],
)
def test_last_months(today: date, months: int, start: date) -> None:
    assert Window.last_months(today, months) == Window(start, today)


def test_last_months_rejects_non_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        Window.last_months(date(2026, 10, 5), 0)
