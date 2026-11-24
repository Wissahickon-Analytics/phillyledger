from collections.abc import Callable
from datetime import date
from re import compile
from types import MappingProxyType

from datadesk.core.domain import EditionKey, Period
from datadesk.core.periods import MONTHS

QUARTER_ENDS = frozenset({(3, 31), (6, 30), (9, 30), (12, 31)})
QCMR_REPORT = compile(
    r"Quarterly City Manager'?s Report\s+[-–]\s+"
    r"(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),\s+(?P<year>[1-9]\d{3})"
)


def qcmr_title(title: str) -> EditionKey | str:
    if "infographic" in title.casefold():
        return "infographic"
    report = QCMR_REPORT.fullmatch(title)
    if report is None:
        return "unrelated"
    month = MONTHS.get(report["month"].casefold(), 0)
    day = int(report["day"])
    if (month, day) not in QUARTER_ENDS:
        return "not_a_quarter_end"
    end = date(int(report["year"]), month, day)
    return EditionKey("qcmr", Period(date(end.year, month - 2, 1), end))


TITLE_RULES: MappingProxyType[str, Callable[[str], EditionKey | str]] = MappingProxyType(
    {"qcmr": qcmr_title}
)
