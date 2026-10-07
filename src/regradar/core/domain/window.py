import calendar
from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class WindowField(StrEnum):
    DATE = "date"
    UPDATED = "updated"


@dataclass(frozen=True)
class Window:
    start: date
    end: date
    field: WindowField = WindowField.DATE

    def __post_init__(self) -> None:
        if self.start > self.end:
            msg = f"Window start {self.start} is after end {self.end}"
            raise ValueError(msg)

    @classmethod
    def last_months(cls, today: date, months: int) -> Window:
        if months < 1:
            msg = f"months must be positive, got {months}"
            raise ValueError(msg)
        return cls(start=subtract_months(today, months), end=today)


def subtract_months(day: date, months: int) -> date:
    month_index = day.year * 12 + day.month - 1 - months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))
