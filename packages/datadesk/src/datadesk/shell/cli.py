"""The `datadesk` command line, the one module that imports typer."""

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import partial
from os import environ
from pathlib import Path
from re import MULTILINE, compile
from traceback import format_exc
from typing import Annotated, assert_never

import typer

from checkedtables.kinds import SourceKind
from checkedtables.lines import Line
from checkedtables.refs import Sha256
from checkedtables.table import Finding
from checkedtables.words import Page
from datadesk.core.codec import render_fixture
from datadesk.core.domain import EditionKey, Stage
from datadesk.core.fetch import FetchPlan, pdf_key
from datadesk.core.listings import Listing, parse_listing
from datadesk.core.parse_plan import WordJob, word_key
from datadesk.core.watch import plan_watch
from datadesk.shell.adapters.cache_dir import DirCache
from datadesk.shell.adapters.http_saved import SavedFolderError, SavedHttp
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.adapters.s3 import s3_store
from datadesk.shell.gather import RepoSnapshot, gather_repo
from datadesk.shell.ports import (
    Deps,
    EffectError,
    LocalCache,
    ObjectStore,
    PdfReader,
    PreconditionFailed,
)
from datadesk.shell.report import (
    CropRow,
    NoLine,
    TwoLines,
    contact_sheet,
    read_crop_rows,
    row_band,
    row_line,
)
from datadesk.shell.run_fetch import retried, run_fetch
from datadesk.shell.run_parse import extract_words, merged_document
from datadesk.shell.settings import MissingSettings, hide_keys, load_settings

FIXTURE_FOLDER = "packages/datadesk/tests/fixtures/words"
CROP_DPI = 200
_WORD_CACHE = ".cache/words"

_PAGES = compile(r"[1-9][0-9]*(,[1-9][0-9]*)*")
_FIXTURE_SHA = compile(r"^SHA = Sha256\('([0-9a-f]{64})'\)$", MULTILINE)

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False, rich_markup_mode=None)


@dataclass(frozen=True, slots=True)
class FetchRun:
    """What one fetch did: the listing's digest, the watch findings and the fetch plan.

    `listing_sha256` is the `Sha256` of the listing's text, and `findings` are the findings that
    `plan_watch` returned.
    """

    listing_sha256: Sha256
    findings: tuple[Finding, ...]
    plan: FetchPlan


class FetchStopped(Exception):
    """A fetch stopped before it fetched any report. The message says why."""


class FixtureStopped(Exception):
    """A fixture run stopped before it read the PDF or wrote any file. The message says why."""


class CropsStopped(Exception):
    """A crops run stopped before it wrote any row crop or the sheet. The message says why."""


def fetch_command(deps: Deps, root: Path, source: str, today: date) -> FetchRun:
    """Fetch the reports that a source's listing names, store them, and index them.

    `root` is the checkout. The files of the plan are written last, after every put, each to a
    temporary file with a fixed name in the same folder and then renamed, so a run that stops
    leaves the index file as it was.

    Raises
    ------
    FetchStopped
        Before any report is fetched, for a checkout that cannot be read, a source the catalog
        lacks, a listing that answers with a status other than 200 or is not UTF-8, and a
        listing that `parse_listing` cannot read.
    EffectError
        When a GET or a put fails on its third try, or when the PDF reader cannot read a
        report's page 1, which it tries once.
    PreconditionFailed
        When the store holds other bytes under a report's key.
    """
    repo = gather_repo(root)
    match repo:
        case RepoSnapshot():
            pass
        case tuple():
            raise FetchStopped(_findings("the checkout cannot be read", repo))
        case _:
            assert_never(repo)
    if source not in (listed.id for listed in repo.catalog.entries):
        raise FetchStopped(f"the catalog has no source {source!r}")
    entry = repo.catalog.entry(source)
    response = retried(partial(deps.http.get, entry.listing_url))
    if response.status != 200:
        raise FetchStopped(f"the listing {entry.listing_url} answered {response.status}")
    try:
        text = response.text
    except UnicodeDecodeError as error:
        raise FetchStopped(f"the listing {entry.listing_url} is not UTF-8: {error}") from None
    listing = parse_listing(entry, entry.listing_url, text)
    match listing:
        case Listing():
            pass
        case Finding():
            raise FetchStopped(_findings("the listing cannot be read", (listing,)))
        case _:
            assert_never(listing)
    watch = plan_watch(repo.catalog, [listing], repo.index, today)
    plan = run_fetch(deps, watch, repo)
    for path, text in plan.pull_request.files:
        target = root / path
        written = target.with_name(f".{target.name}.tmp")
        written.write_text(text, encoding="utf-8", newline="")
        written.replace(target)
    return FetchRun(listing.html_sha256, watch.findings, plan)


def fixture_command(
    store: ObjectStore, pdf: PdfReader, cache: LocalCache, root: Path, *, sha: str, pages: str
) -> tuple[Path, ...]:
    """Write a word fixture of each page asked for, from an archived PDF, into the checkout.

    `root` is the checkout. `sha` and `pages` are the words the user typed: a sha that the
    index holds, and page numbers joined by commas, such as ``35,36``, which are sorted and
    read once each. Each page's fixture is ``<series>_<YYYY_MM_DD>_p<n>.py`` in
    `FIXTURE_FOLDER`, named by the indexed edition of the sha, with ``_<stage>`` before ``_p``
    when the stage is not none. The words come from the cache when it holds the key of these
    pages, and otherwise from one read of the PDF, cached under that key. Each file is written
    to a temporary file with a fixed name in the same folder and then renamed.

    Returns
    -------
    tuple[Path, ...]
        The files written, in page order.

    Raises
    ------
    FixtureStopped
        Before the PDF is read and before any file is written, for a sha that is not 64
        lowercase hex characters, pages that are not such a list, a checkout that cannot be
        read, a sha the index lacks, and a fixture of that name that holds no sha or another
        sha, as a fixture of another version of the same edition does. That file is left as
        it was.
    KeyError
        When the store holds no PDF of the sha.
    EffectError
        When the store, the reader or the cache fails, or the PDF lacks a page asked for.
    """
    try:
        doc_sha256 = Sha256(sha)
    except ValueError:
        raise FixtureStopped(f"{sha!r} is not a sha256 of 64 lowercase hex characters") from None
    if _PAGES.fullmatch(pages) is None:
        raise FixtureStopped(f"{pages!r} are not page numbers joined by commas, such as 35,36")
    numbers = tuple(sorted({int(number) for number in pages.split(",")}))
    repo = gather_repo(root)
    match repo:
        case RepoSnapshot():
            pass
        case tuple():
            raise FixtureStopped(_findings("the checkout cannot be read", repo))
        case _:
            assert_never(repo)
    version = repo.index.by_sha(doc_sha256)
    if version is None:
        raise FixtureStopped(f"the index holds no file with sha256 {doc_sha256}")
    folder = root / FIXTURE_FOLDER
    targets = [folder / f"{_fixture_stem(version.edition)}_p{number}.py" for number in numbers]
    for target in targets:
        if target.exists() and (held := _fixture_sha(target)) != doc_sha256:
            named = "no sha" if held is None else f"the sha {held}"
            raise FixtureStopped(f"{target} names {named}, not {doc_sha256}, and stays as it was")
    key = word_key(doc_sha256, numbers, pdf.tool())
    cached = cache.keys()
    if key not in cached:
        job = WordJob(doc_sha256, numbers, SourceKind.TEXT_LAYER, None, key)
        extract_words(store, pdf, cache, [job])
    document = merged_document(cache, [key])
    folder.mkdir(parents=True, exist_ok=True)
    for target, page in zip(targets, document.pages, strict=True):
        written = target.with_name(f".{target.name}.tmp")
        written.write_text(render_fixture(page), encoding="utf-8", newline="")
        written.replace(target)
    return tuple(targets)


def crops_command(
    store: ObjectStore, pdf: PdfReader, cache: LocalCache, root: Path, *, tsv: Path, folder: Path
) -> tuple[Path, ...]:
    """Draw the pages and the row crops that a crop file names, from the archived PDFs.

    `root` is the checkout, `tsv` a crop file that `read_crop_rows` reads, and `folder` where
    the images go. For each sha the words of the pages its rows name come from the word cache
    when it holds the key of those pages, and otherwise from one read of the PDF, cached under
    that key. Each page is drawn at `CROP_DPI` by `PdfReader.render` and written as
    ``pages/<stem>_p<n>.png``, where ``<stem>`` names the edition as a word fixture does. Each
    row with a ``page_label`` gets ``rows/<stem>_p<n>_<first|last>.png``, the band of the one
    line that `row_line` finds for that label. When every row has a crop, a ``crop_label`` and
    ``values``, ``sheet.png`` stacks the crops in the file's order with each one's reading.
    Each file is written to a temporary file with a fixed name in its folder and then renamed.

    Returns
    -------
    tuple[Path, ...]
        The files written: the pages by edition and page, then the rows and the sheet in the
        file's order.

    Raises
    ------
    CropsStopped
        Before any PDF is read, for a crop file that cannot be read or that `read_crop_rows`
        refuses, a checkout that cannot be read, a sha the index lacks, and an ``edition`` that
        is not the indexed edition of its sha. After the pages are written and before any row
        crop or the sheet is, for every label that begins no line or more than one, each named.
    KeyError
        When the store holds no PDF of a sha.
    EffectError
        When the store, the reader or the cache fails, or a PDF lacks a page the file names.
    """
    try:
        rows = read_crop_rows(tsv.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        raise CropsStopped(f"{tsv} cannot be read: {error}") from None
    repo = gather_repo(root)
    match repo:
        case RepoSnapshot():
            pass
        case tuple():
            raise CropsStopped(_findings("the checkout cannot be read", repo))
        case _:
            assert_never(repo)
    stems: dict[Sha256, str] = {}
    for row in rows:
        version = repo.index.by_sha(row.sha256)
        if version is None:
            raise CropsStopped(f"the index holds no file with sha256 {row.sha256}")
        if (indexed := version.edition.id()) != row.edition:
            raise CropsStopped(f"the index names sha256 {row.sha256} {indexed}, not {row.edition}")
        stems[row.sha256] = _fixture_stem(version.edition)
    pages: dict[tuple[Sha256, int], Page] = {}
    images: dict[tuple[Sha256, int], bytes] = {}
    cached = cache.keys()
    for sha in stems:
        numbers = tuple(sorted({row.page for row in rows if row.sha256 == sha}))
        key = word_key(sha, numbers, pdf.tool())
        if key not in cached:
            extract_words(
                store, pdf, cache, [WordJob(sha, numbers, SourceKind.TEXT_LAYER, None, key)]
            )
        data = store.get(pdf_key(sha))
        for page in merged_document(cache, [key]).pages:
            pages[sha, page.number] = page
            images[sha, page.number] = pdf.render(data, page.number, CROP_DPI)
    written = [
        _write(folder / "pages" / f"{stems[sha]}_p{number}.png", image)
        for (sha, number), image in images.items()
    ]
    lines: dict[CropRow, Line] = {}
    refused: list[str] = []
    for row in (row for row in rows if row.page_label):
        found = row_line(pages[row.sha256, row.page], row.page_label)
        named = f"{row.edition} page {row.page} {row.row} {row.page_label!r}"
        match found:
            case Line():
                lines[row] = found
            case NoLine():
                refused.append(f"{named}: no line")
            case TwoLines():
                refused.append(f"{named}: {len(found.lines)} lines")
            case _:
                assert_never(found)
    if refused:
        raise CropsStopped(
            f"each label must begin one line, and these do not: {'; '.join(refused)}. "
            f"The page images are in {folder / 'pages'}"
        )
    crops = {
        row: row_band(images[row.sha256, row.page], line, CROP_DPI) for row, line in lines.items()
    }
    written += [
        _write(folder / "rows" / f"{stems[row.sha256]}_p{row.page}_{row.row}.png", crop)
        for row, crop in crops.items()
    ]
    if rows and all(row in crops and row.crop_label and row.values for row in rows):
        sheet = contact_sheet([(row, crops[row]) for row in rows])
        written.append(_write(folder / "sheet.png", sheet))
    return tuple(written)


@app.callback()
def datadesk() -> None:
    """Archive Philadelphia's budget and finance reports."""


@app.command()
def fetch(
    source: Annotated[str, typer.Argument(help="a source id from catalog.toml, such as qcmr")],
    saved: Annotated[Path, typer.Option(help="a folder of saved responses with responses.tsv")],
) -> None:
    """Archive the reports a listing names."""
    today = date.today()
    try:
        settings = load_settings(environ)
    except MissingSettings as error:
        print(f"datadesk: {error}", file=sys.stderr)
        raise typer.Exit(1) from None
    try:
        deps = Deps(SavedHttp(saved), s3_store(settings), PdfPlumberReader())
        run = fetch_command(deps, Path.cwd(), source, today)
        lines = [
            f"listing sha256 {run.listing_sha256}",
            *(f"{f.severity} {f.code} {f.subject}: {f.message}" for f in run.findings),
            "",
            run.plan.pull_request.title,
            "",
            run.plan.pull_request.body,
            *(f"wrote {path}" for path, _ in run.plan.pull_request.files),
        ]
        print(hide_keys("\n".join(lines), settings))
    except (SavedFolderError, FetchStopped, EffectError) as error:
        print(hide_keys(f"datadesk: {error}", settings), file=sys.stderr)
        raise typer.Exit(1) from None
    except PreconditionFailed as error:
        print(
            hide_keys(f"datadesk: the store holds other bytes under {error}", settings),
            file=sys.stderr,
        )
        raise typer.Exit(1) from None
    except BaseException:  # noqa: BLE001
        print(hide_keys(format_exc(), settings), end="", file=sys.stderr)
        raise typer.Exit(1) from None


@app.command()
def fixture(
    sha: Annotated[str, typer.Argument(help="the sha256 of a file the index holds")],
    pages: Annotated[str, typer.Argument(help="page numbers joined by commas, such as 35,36")],
) -> None:
    """Write word fixtures of pages of an archived PDF."""
    try:
        settings = load_settings(environ)
    except MissingSettings as error:
        print(f"datadesk: {error}", file=sys.stderr)
        raise typer.Exit(1) from None
    root = Path.cwd()
    try:
        store, cache = s3_store(settings), DirCache(root / _WORD_CACHE)
        written = fixture_command(store, PdfPlumberReader(), cache, root, sha=sha, pages=pages)
        print(hide_keys("\n".join(f"wrote {path.relative_to(root)}" for path in written), settings))
    except (FixtureStopped, EffectError) as error:
        print(hide_keys(f"datadesk: {error}", settings), file=sys.stderr)
        raise typer.Exit(1) from None
    except BaseException:  # noqa: BLE001
        print(hide_keys(format_exc(), settings), end="", file=sys.stderr)
        raise typer.Exit(1) from None


@app.command()
def crops(
    tsv: Annotated[Path, typer.Argument(help="a crop file, such as one in docs/evidence/crops")],
    folder: Annotated[Path, typer.Argument(help="the folder for pages/, rows/ and sheet.png")],
) -> None:
    """Draw archived pages, and the rows that a crop file names."""
    try:
        settings = load_settings(environ)
    except MissingSettings as error:
        print(f"datadesk: {error}", file=sys.stderr)
        raise typer.Exit(1) from None
    try:
        root = Path.cwd()
        store, cache = s3_store(settings), DirCache(root / _WORD_CACHE)
        written = crops_command(store, PdfPlumberReader(), cache, root, tsv=tsv, folder=folder)
        for path in written:
            print(hide_keys(f"wrote {path}", settings))
    except (CropsStopped, EffectError) as error:
        print(hide_keys(f"datadesk: {error}", settings), file=sys.stderr)
        raise typer.Exit(1) from None
    except BaseException:  # noqa: BLE001
        print(hide_keys(format_exc(), settings), end="", file=sys.stderr)
        raise typer.Exit(1) from None


def main(argv: Sequence[str] | None = None) -> int:
    """Run the `datadesk` command line on `argv`, or on `sys.argv[1:]`, and return its exit code.

    The code is the integer code of a SystemExit that reaches `main`. Any other exception
    propagates.
    """
    try:
        app(args=argv, prog_name="datadesk")
    except SystemExit as stop:
        if isinstance(stop.code, int):
            return stop.code
        raise
    return 0


def _findings(heading: str, findings: Sequence[Finding]) -> str:
    return "; ".join([heading, *(f"{f.code} {f.subject}: {f.message}" for f in findings)])


def _fixture_stem(edition: EditionKey) -> str:
    """Name an edition's fixtures, as ``qcmr_2022_09_30`` for ``qcmr:2022-09-30:none``."""
    stage = "" if edition.stage is Stage.NONE else f"_{edition.stage}"
    return f"{edition.series}_{edition.period.end:%Y_%m_%d}{stage}"


def _write(target: Path, data: bytes) -> Path:
    """Write `data` to `target` through a temporary file with a fixed name in its folder."""
    target.parent.mkdir(parents=True, exist_ok=True)
    written = target.with_name(f".{target.name}.tmp")
    written.write_bytes(data)
    written.replace(target)
    return target


def _fixture_sha(path: Path) -> str | None:
    """Return the sha that the ``SHA`` line of a fixture `render_fixture` wrote names, or None."""
    found = _FIXTURE_SHA.search(path.read_text(encoding="utf-8"))
    return None if found is None else found.group(1)
