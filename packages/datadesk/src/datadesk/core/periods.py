"""Month names and the City's fiscal calendar, whose year starts on July 1."""

from datetime import date, timedelta
from types import MappingProxyType

from datadesk.core.domain import Period
from datadesk.core.vocab import Window

MONTHS: MappingProxyType[str, int] = MappingProxyType(
    {
        name: number
        for number, name in enumerate(
            (
                "january",
                "february",
                "march",
                "april",
                "may",
                "june",
                "july",
                "august",
                "september",
                "october",
                "november",
                "december",
            ),
            1,
        )
    }
)
_FISCAL_BASIS = frozenset({Window.FISCAL_YTD, Window.FISCAL_YEAR})


def fiscal_year_of(d: date) -> int:
    """Return the fiscal year a day falls in, so 2025-07-01 is in FY2026."""
    return d.year + 1 if d.month >= 7 else d.year


def fiscal_quarter(period_end: date) -> tuple[int, int]:
    """Return the fiscal year and quarter a day falls in, so 2021-09-30 gives (2022, 1)."""
    return fiscal_year_of(period_end), (period_end.month - 7) % 12 // 3 + 1


def fiscal_period(kind: Window, label_year: int, months: tuple[int, int]) -> Period:
    """Return the days from the first of one month to the last of another, as a window dates them.

    The fiscal year to date and the fiscal year label their months with the fiscal year, so July
    to December of FY2026 is 2025-07-01 to 2025-12-31 (WAGE-Q07). Every other window labels them
    with the calendar year (RTT-Q41, WAGE-Q34).

    Parameters
    ----------
    kind : Window
        The window whose basis the label year has.
    label_year : int
        The year the months are labeled with: a fiscal year for FISCAL_YTD and FISCAL_YEAR, and
        a calendar year for every other window.
    months : tuple[int, int]
        The first and the last month, 1 for January to 12 for December, both included.

    Raises
    ------
    ValueError
        When a month is not 1 to 12, or the last month falls before the first.
    """
    first, last = months
    if not (1 <= first <= 12 and 1 <= last <= 12):
        raise ValueError(f"months {months} are not 1 to 12")
    start = date(_calendar_year(kind, label_year, first), first, 1)
    following = date(_calendar_year(kind, label_year, last) + last // 12, last % 12 + 1, 1)
    return Period(start, following - timedelta(days=1))


def _calendar_year(kind: Window, label_year: int, month: int) -> int:
    return label_year - 1 if kind in _FISCAL_BASIS and month >= 7 else label_year
