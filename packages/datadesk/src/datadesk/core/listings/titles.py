"""Title rules: read a listing title as the edition it names, or as the reason to skip it."""

from collections.abc import Callable
from datetime import date
from enum import StrEnum
from re import compile
from types import MappingProxyType

from datadesk.core.domain import EditionKey, Period
from datadesk.core.periods import MONTHS

QUARTER_ENDS = frozenset({(3, 31), (6, 30), (9, 30), (12, 31)})
QCMR_REPORT = compile(
    r"Quarterly City Manager'?s Report\s+[-–]\s+"
    r"(?P<month>\w+)\s+(?P<day>\d{1,2}),\s+(?P<year>[1-9]\d{3})"
)


class SkipReason(StrEnum):
    """Why a listed link names no edition.

    Attributes
    ----------
    INFOGRAPHIC
        The title names an infographic.
    UNRELATED
        The title is not a report title, such as an executive summary.
    NOT_A_QUARTER_END
        A report title whose date ends no quarter, or whose month word names no month.
    UNSTAGED
        A title that names no budget stage, such as "FY2024 Budget in Brief" (BIB-Q04). No
        title rule returns it yet.
    """

    INFOGRAPHIC = "infographic"
    UNRELATED = "unrelated"
    NOT_A_QUARTER_END = "not_a_quarter_end"
    UNSTAGED = "unstaged"


def qcmr_title(title: str) -> EditionKey | SkipReason:
    """Read a QCMR listing title as its edition, or as the reason to skip the link.

    "infographic" anywhere in the title, in any case, gives `SkipReason.INFOGRAPHIC`. A report
    title is "Quarterly City Managers Report" or "Quarterly City Manager's Report", a hyphen or
    an en dash, then "<Word> <D>, <YYYY>" and nothing more, where <Word> is a run of letters. A
    report title whose date ends a quarter gives the edition from the first day of that fiscal
    quarter to the date. Any other report title, one whose word names no month included, gives
    `SkipReason.NOT_A_QUARTER_END`, so `plan_watch` warns of it instead of dropping it. Every
    other title gives `SkipReason.UNRELATED`. The edition comes from the title alone, never from
    the URL.
    """
    if "infographic" in title.casefold():
        return SkipReason.INFOGRAPHIC
    report = QCMR_REPORT.fullmatch(title)
    if report is None or not report["month"].isalpha():
        return SkipReason.UNRELATED
    month = MONTHS.get(report["month"].casefold(), 0)
    day = int(report["day"])
    if (month, day) not in QUARTER_ENDS:
        return SkipReason.NOT_A_QUARTER_END
    end = date(int(report["year"]), month, day)
    return EditionKey("qcmr", Period(date(end.year, month - 2, 1), end))


TITLE_RULES: MappingProxyType[str, Callable[[str], EditionKey | SkipReason]] = MappingProxyType(
    {"qcmr": qcmr_title}
)
