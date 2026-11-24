from collections.abc import Callable, Sequence
from datetime import date
from re import compile
from types import MappingProxyType

from checkedtables.table import Finding, Severity
from datadesk.core.domain import EditionKey, Period
from datadesk.core.listings.titles import QUARTER_ENDS
from datadesk.core.periods import MONTHS
from datadesk.core.records import EditionNote, NoteKind

# QCASH-Q05, QOBL-Q04: the cover prints "FOR THE PERIOD ENDING <Month> <D>, <YYYY>".
# QOBL-Q02: a line break or U+00A0 may stand between any two of its words.
PERIOD_ENDING = compile(r"(?i)PERIOD\s+ENDING\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})(?!\d)")


def qcmr_period(page1_text: str) -> Period | str:
    read = [_printed_date(*phrase) for phrase in PERIOD_ENDING.findall(page1_text)]
    ends = {end for end in read if end is not None}
    if not read or None in read:
        return "period_unreadable"
    if len(ends) > 1:
        return "period_ambiguous"
    (end,) = ends
    if (end.month, end.day) not in QUARTER_ENDS:
        return "period_not_a_quarter_end"
    return Period(date(end.year, end.month - 2, 1), end)


PERIOD_READERS: MappingProxyType[str, Callable[[str], Period | str]] = MappingProxyType(
    {"qcmr": qcmr_period}
)


def confirm_period(
    series: str, page1_text: str, expected: EditionKey, notes: Sequence[EditionNote]
) -> Period | Finding:
    reader = PERIOD_READERS.get(series)
    if reader is None:
        return _block("period_unsupported", expected, f"no period reader for {series!r}")
    printed = reader(page1_text)
    if isinstance(printed, str):
        return _block(printed, expected, f"the {series} period reader refuses page 1")
    if printed == expected.period:
        return expected.period
    if any(_clears(note, page1_text, printed) for note in notes):
        return printed
    return _block("period_mismatch", expected, f"page 1 prints the period ending {printed.end}")


def _printed_date(month: str, day: str, year: str) -> date | None:
    number = MONTHS.get(month.casefold())
    if number is None:
        return None
    try:
        return date(int(year), number, int(day))
    except ValueError:
        return None


def _clears(note: EditionNote, page1_text: str, printed: Period) -> bool:
    return (
        note.kind == NoteKind.PRINTED_PERIOD
        and note.page in (None, 1)
        and _collapsed(note.printed) in _collapsed(page1_text)
        and note.value == printed.end.isoformat()
    )


def _collapsed(text: str) -> str:
    return " ".join(text.split())


def _block(code: str, expected: EditionKey, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, expected.id(), message)
