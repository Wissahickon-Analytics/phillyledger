"""The `datadesk` command line, the one module that imports typer."""

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import partial
from os import environ
from pathlib import Path
from traceback import format_exc
from typing import Annotated

import typer

from checkedtables.table import Finding
from datadesk.core.fetch import FetchPlan
from datadesk.core.listings import parse_listing
from datadesk.core.watch import plan_watch
from datadesk.shell.adapters.http_saved import SavedFolderError, SavedHttp
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.adapters.s3 import s3_store
from datadesk.shell.gather import gather_repo
from datadesk.shell.ports import Deps, EffectError, PreconditionFailed
from datadesk.shell.run_fetch import retried, run_fetch
from datadesk.shell.settings import MissingSettings, hide_keys, load_settings

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False, rich_markup_mode=None)


@dataclass(frozen=True, slots=True)
class FetchRun:
    """What one fetch did: the listing's digest, the watch findings and the fetch plan.

    `listing_sha256` is the sha256 of the listing's text, and `findings` are the findings that
    `plan_watch` returned.
    """

    listing_sha256: str
    findings: tuple[Finding, ...]
    plan: FetchPlan


class FetchStopped(Exception):
    """A fetch stopped before it fetched any report. The message says why."""


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
    if isinstance(repo, tuple):
        raise FetchStopped(_findings("the checkout cannot be read", repo))
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
    if isinstance(listing, Finding):
        raise FetchStopped(_findings("the listing cannot be read", (listing,)))
    watch = plan_watch(repo.catalog, [listing], repo.index, today)
    plan = run_fetch(deps, watch, repo)
    for path, text in plan.pull_request.files:
        target = root / path
        written = target.with_name(f".{target.name}.tmp")
        written.write_text(text, encoding="utf-8", newline="")
        written.replace(target)
    return FetchRun(listing.html_sha256, watch.findings, plan)


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
