"""Month names and the City's fiscal calendar, whose year starts on July 1."""

from datetime import date
from types import MappingProxyType

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


def fiscal_year_of(d: date) -> int:
    """Return the fiscal year a day falls in, so 2025-07-01 is in FY2026."""
    return d.year + 1 if d.month >= 7 else d.year


def fiscal_quarter(period_end: date) -> tuple[int, int]:
    """Return the fiscal year and quarter a day falls in, so 2021-09-30 gives (2022, 1)."""
    return fiscal_year_of(period_end), (period_end.month - 7) % 12 // 3 + 1
