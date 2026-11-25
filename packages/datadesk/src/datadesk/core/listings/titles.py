"""Title rules: read a listing title as the edition it names, or as the reason to skip it."""

from collections.abc import Callable
from datetime import date
from re import compile
from types import MappingProxyType

from datadesk.core.domain import EditionKey, Period
from datadesk.core.periods import MONTHS

QUARTER_ENDS = frozenset({(3, 31), (6, 30), (9, 30), (12, 31)})
QCMR_REPORT = compile(
    r"Quarterly City Manager'?s Report\s+[-–]\s+"
    r"(?P<month>\w+)\s+(?P<day>\d{1,2}),\s+(?P<year>[1-9]\d{3})"
)


def qcmr_title(title: str) -> EditionKey | str:
    """Read a QCMR listing title as its edition, or as the reason to skip the link.

    "infographic" anywhere in the title, in any case, gives "infographic". A report title is
    "Quarterly City Managers Report" or "Quarterly City Manager's Report", a hyphen or an en dash,
    then "<Word> <D>, <YYYY>" and nothing more, where <Word> is a run of letters. A report title
    whose date ends a quarter gives the edition from the first day of that fiscal quarter to the
    date. Any other report title, one whose word names no month included, gives
    "not_a_quarter_end", so `plan_watch` warns of it instead of dropping it. Every other title
    gives "unrelated". The edition comes from the title alone, never from the URL.
    """
    if "infographic" in title.casefold():
        return "infographic"
    report = QCMR_REPORT.fullmatch(title)
    if report is None or not report["month"].isalpha():
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
