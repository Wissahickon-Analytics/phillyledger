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
    return d.year + 1 if d.month >= 7 else d.year


def fiscal_quarter(period_end: date) -> tuple[int, int]:
    return fiscal_year_of(period_end), (period_end.month - 7) % 12 // 3 + 1
