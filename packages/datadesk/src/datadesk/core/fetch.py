"""Decide what a fetch stores and indexes, from the bytes it downloaded and the index."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum
from re import compile, escape
from types import MappingProxyType
from typing import assert_never

from checkedtables.refs import Sha256
from checkedtables.table import Finding, Severity
from datadesk.core.domain import ArchiveIndex, DocumentVersion, EditionKey, Period
from datadesk.core.index import add_versions, render_index
from datadesk.core.listings.titles import QUARTER_ENDS
from datadesk.core.periods import MONTHS
from datadesk.core.records import EditionNote, NoteKind
from datadesk.core.watch import FetchRequest, PullRequestPlan

INDEX_PATH = "packages/datadesk/src/datadesk/data/index.jsonl"
BRANCH = "fetch/index"
TITLE = "feat(datadesk): index fetched reports"

# QCASH-Q05, QOBL-Q04: the cover prints "FOR THE PERIOD ENDING <Month> <D>, <YYYY>".
# QOBL-Q02: a line break or U+00A0 may stand between any two of its words.
PERIOD_ENDING = compile(r"(?i)\bPERIOD\s+ENDING\b(?:\s+(\w+)\s+(\d{1,2}),?\s+(\d{4})(?!\d))?")


@dataclass(frozen=True, slots=True)
class Fetched:
    """What the shell got for one fetch request, before any decision.

    `size` is the length of the body. `page1_text` is the text the PDF reader read from page 1.
    For a status other than 200, `sha256` and `page1_text` are None and `size` is 0.
    """

    request: FetchRequest
    status: int
    sha256: Sha256 | None
    size: int
    page1_text: str | None


@dataclass(frozen=True, slots=True)
class StoreObject:
    """A file to put in the archive bucket, under the key "pdf/<sha[:2]>/<sha>.pdf".

    `dest_key` is plain text.
    """

    sha256: Sha256
    dest_key: str


@dataclass(frozen=True, slots=True)
class Rejection:
    """A fetch request whose bytes are not indexed, and why.

    `reason` is a code such as "period_mismatch", "content_alias" or "http_404".
    """

    request: FetchRequest
    reason: str


@dataclass(frozen=True, slots=True)
class FetchPlan:
    """Everything a fetch decided: what to store, what to index, what it refused, and the PR.

    `pull_request.files` is empty when no line is added. Otherwise it holds one file,
    `INDEX_PATH` with the whole index after every added line. The body lists each added line
    (edition id, sha, URLs) and each rejection (edition id, URL, reason).
    """

    store: tuple[StoreObject, ...]
    index_add: tuple[DocumentVersion, ...]
    rejections: tuple[Rejection, ...]
    pull_request: PullRequestPlan


class PeriodRefusal(StrEnum):
    """Why a period reader cannot read a period from page 1. Each value is a finding code.

    Attributes
    ----------
    UNREADABLE
        The page has no caption, or has one with no date a program can read.
    AMBIGUOUS
        Two captions give different dates.
    NOT_A_QUARTER_END
        The printed date ends no quarter.
    """

    UNREADABLE = "period_unreadable"
    AMBIGUOUS = "period_ambiguous"
    NOT_A_QUARTER_END = "period_not_a_quarter_end"


def qcmr_period(page1_text: str) -> Period | PeriodRefusal:
    """Read the quarter that a QCMR cover prints.

    The cover prints "FOR THE PERIOD ENDING <Month> <D>, <YYYY>" (QCASH-Q05, QOBL-Q04). Every
    such caption on page 1 is read, and all of them must give one date.

    Returns
    -------
    Period | PeriodRefusal
        The three months that end on the printed date, or the reason no period is read.
    """
    read = [_printed_date(*phrase) for phrase in PERIOD_ENDING.findall(page1_text)]
    ends = {end for end in read if end is not None}
    if not read or None in read:
        return PeriodRefusal.UNREADABLE
    if len(ends) > 1:
        return PeriodRefusal.AMBIGUOUS
    (end,) = ends
    if (end.month, end.day) not in QUARTER_ENDS:
        return PeriodRefusal.NOT_A_QUARTER_END
    return Period(date(end.year, end.month - 2, 1), end)


PERIOD_READERS: MappingProxyType[str, Callable[[str], Period | PeriodRefusal]] = MappingProxyType(
    {"qcmr": qcmr_period}
)


def confirm_period(
    series: str, page1_text: str, expected: EditionKey, notes: Sequence[EditionNote]
) -> Period | Finding:
    """Confirm the period that page 1 prints against the period the listing gave.

    The listing date and the printed period can disagree (QOBL-Q06). A printed period equal to
    `expected.period` is confirmed. Another one is confirmed only by a PRINTED_PERIOD note, on
    page 1 or on no page, that quotes words page 1 prints, with each run of whitespace read as
    one space and no word character right before or after the quote. The series' reader must
    read the quote alone as that same period, and the note's value must be its end in ISO form.
    No note clears a refusal. The caller passes only the notes on the file.

    Returns
    -------
    Period | Finding
        The confirmed period, or a BLOCK finding whose subject is `expected.id()`:
        period_unsupported for a series with no reader, the value of the reader's
        `PeriodRefusal` as plain text, or period_mismatch.
    """
    reader = PERIOD_READERS.get(series)
    if reader is None:
        return _block("period_unsupported", expected, f"no period reader for {series!r}")
    match reader(page1_text):
        case PeriodRefusal() as refusal:
            return _block(refusal.value, expected, f"the {series} period reader refuses page 1")
        case Period() as printed:
            if printed == expected.period:
                return expected.period
            if any(_clears(note, page1_text, printed, reader) for note in notes):
                return printed
            message = f"page 1 prints the period ending {printed.end}"
            return _block("period_mismatch", expected, message)
        case unhandled:
            assert_never(unhandled)


def plan_fetch(
    fetched: Sequence[Fetched], index: ArchiveIndex, notes: Sequence[EditionNote]
) -> FetchPlan:
    """Decide, for each fetched file in order, whether to store it, index it or refuse it.

    A working index starts as `index` and grows after each added line, so two requests in one
    batch see each other. The first rule that fits a fetch decides it.

    1. A status other than 200 is refused as "http_<status>".
    2. A sha indexed under another edition is refused as content_alias (MSCH-Q01).
    3. A sha indexed under the request's edition that is not its current version is refused as
       superseded_sha_relisted. With bytes A, then B, then A again, B stays current.
    4. The current sha at a URL its line holds adds nothing.
    5. The current sha at a new URL stores nothing and adds the URL to its line, which keeps the
       later listed_at.
    6. A new sha must pass `confirm_period`, with the notes on that sha. New bytes listed before
       the current version are refused as listed_before_current. Otherwise the sha gets one
       object to store and a line that supersedes the current version.

    A finding from `add_versions` refuses the fetch with its code.
    """
    working = index
    store: list[StoreObject] = []
    index_add: list[DocumentVersion] = []
    rejections: list[Rejection] = []
    for fetch in fetched:
        match _decide(fetch, working, notes):
            case Rejection() as rejection:
                rejections.append(rejection)
            case DocumentVersion() as version:
                match add_versions(working, (version,)):
                    case Finding() as finding:
                        rejections.append(Rejection(fetch.request, finding.code))
                    case ArchiveIndex() as grown:
                        if working.by_sha(version.sha256) is None:
                            store.append(StoreObject(version.sha256, _pdf_key(version.sha256)))
                        index_add.append(version)
                        working = grown
            case None:
                pass
    files = ((INDEX_PATH, render_index(working)),) if index_add else ()
    pull_request = PullRequestPlan(files, BRANCH, TITLE, _body(index_add, rejections))
    return FetchPlan(tuple(store), tuple(index_add), tuple(rejections), pull_request)


def _decide(
    fetch: Fetched, index: ArchiveIndex, notes: Sequence[EditionNote]
) -> Rejection | DocumentVersion | None:
    request = fetch.request
    edition = request.edition
    if fetch.status != 200 or fetch.sha256 is None:
        return Rejection(request, f"http_{fetch.status}")
    held = index.by_sha(fetch.sha256)
    current = index.current(edition)
    if held is not None:
        if held.edition != edition:
            return Rejection(request, "content_alias")
        if held != current:
            return Rejection(request, "superseded_sha_relisted")
        if request.url in held.urls:
            return None
        return replace(held, urls=(request.url,), listed_at=request.listed_at)
    own_notes = [note for note in notes if note.doc_sha256 == fetch.sha256]
    period = confirm_period(edition.series, fetch.page1_text or "", edition, own_notes)
    if isinstance(period, Finding):
        return Rejection(request, period.code)
    if current is not None and request.listed_at < current.listed_at:
        return Rejection(request, "listed_before_current")
    return DocumentVersion(
        sha256=fetch.sha256,
        edition=edition,
        listed_at=request.listed_at,
        urls=(request.url,),
        title=request.title,
        printed_period=period,
        supersedes=None if current is None else current.sha256,
    )


def _pdf_key(sha: Sha256) -> str:
    return f"pdf/{sha[:2]}/{sha}.pdf"


def _body(added: Sequence[DocumentVersion], rejections: Sequence[Rejection]) -> str:
    lines = [f"{v.edition.id()} {v.sha256} {' '.join(v.urls)}" for v in added]
    refused = [f"{r.request.edition.id()} {r.request.url} {r.reason}" for r in rejections]
    return f"{_section('Index lines added', lines)}\n{_section('Rejected', refused)}"


def _section(heading: str, items: Sequence[str]) -> str:
    return f"{heading}:\n" + "".join(f"- {item}\n" for item in items or ["none"])


def _printed_date(month: str, day: str, year: str) -> date | None:
    number = MONTHS.get(month.casefold())
    if number is None:
        return None
    try:
        return date(int(year), number, int(day))
    except ValueError:
        return None


def _clears(
    note: EditionNote,
    page1_text: str,
    printed: Period,
    reader: Callable[[str], Period | PeriodRefusal],
) -> bool:
    return (
        note.kind == NoteKind.PRINTED_PERIOD
        and note.page in (None, 1)
        and _quotes(page1_text, note.printed)
        and reader(note.printed) == printed
        and note.value == printed.end.isoformat()
    )


def _quotes(page1_text: str, quote: str) -> bool:
    pattern = compile(rf"(?<!\w){escape(_collapsed(quote))}(?!\w)")
    return pattern.search(_collapsed(page1_text)) is not None


def _collapsed(text: str) -> str:
    return " ".join(text.split())


def _block(code: str, expected: EditionKey, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, expected.id(), message)
