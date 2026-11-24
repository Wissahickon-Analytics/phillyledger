from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import date
from re import compile
from types import MappingProxyType

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
PERIOD_ENDING = compile(r"(?i)PERIOD\s+ENDING\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})(?!\d)")


@dataclass(frozen=True, slots=True)
class Fetched:
    request: FetchRequest
    status: int
    sha256: str | None
    size: int
    page1_text: str | None


@dataclass(frozen=True, slots=True)
class StoreObject:
    sha256: str
    dest_key: str


@dataclass(frozen=True, slots=True)
class Rejection:
    request: FetchRequest
    reason: str


@dataclass(frozen=True, slots=True)
class FetchPlan:
    store: tuple[StoreObject, ...]
    index_add: tuple[DocumentVersion, ...]
    rejections: tuple[Rejection, ...]
    pull_request: PullRequestPlan


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
    if any(_clears(note, page1_text, printed, reader) for note in notes):
        return printed
    return _block("period_mismatch", expected, f"page 1 prints the period ending {printed.end}")


def plan_fetch(
    fetched: Sequence[Fetched], index: ArchiveIndex, notes: Sequence[EditionNote]
) -> FetchPlan:
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
        return None if request.url in held.urls else replace(held, urls=(request.url,))
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


def _pdf_key(sha: str) -> str:
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
    note: EditionNote, page1_text: str, printed: Period, reader: Callable[[str], Period | str]
) -> bool:
    return (
        note.kind == NoteKind.PRINTED_PERIOD
        and note.page in (None, 1)
        and _collapsed(note.printed) in _collapsed(page1_text)
        and reader(note.printed) == printed
        and note.value == printed.end.isoformat()
    )


def _collapsed(text: str) -> str:
    return " ".join(text.split())


def _block(code: str, expected: EditionKey, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, expected.id(), message)
