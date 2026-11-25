import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import partial
from os import environ
from pathlib import Path
from traceback import format_exc

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


@dataclass(frozen=True, slots=True)
class FetchRun:
    listing_sha256: str
    findings: tuple[Finding, ...]
    plan: FetchPlan


class FetchStopped(Exception):
    pass


def fetch_command(deps: Deps, root: Path, source: str, today: date) -> FetchRun:
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(prog="datadesk")
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="archive the reports a listing names")
    fetch.add_argument("source", help="a source id from catalog.toml, such as qcmr")
    fetch.add_argument(
        "--saved", type=Path, required=True, help="a folder of saved responses with responses.tsv"
    )
    args = parser.parse_args(argv)
    today = date.today()
    try:
        settings = load_settings(environ)
    except MissingSettings as error:
        print(f"datadesk: {error}", file=sys.stderr)
        return 1
    try:
        deps = Deps(SavedHttp(args.saved), s3_store(settings), PdfPlumberReader())
        run = fetch_command(deps, Path.cwd(), args.source, today)
    except (SavedFolderError, FetchStopped, EffectError) as error:
        print(hide_keys(f"datadesk: {error}", settings), file=sys.stderr)
        return 1
    except PreconditionFailed as error:
        print(
            hide_keys(f"datadesk: the store holds other bytes under {error}", settings),
            file=sys.stderr,
        )
        return 1
    except BaseException:  # noqa: BLE001
        print(hide_keys(format_exc(), settings), end="", file=sys.stderr)
        return 1
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
    return 0


def _findings(heading: str, findings: Sequence[Finding]) -> str:
    return "; ".join([heading, *(f"{f.code} {f.subject}: {f.message}" for f in findings)])
