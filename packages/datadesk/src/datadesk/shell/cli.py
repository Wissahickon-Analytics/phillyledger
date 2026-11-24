import sys
from argparse import ArgumentParser
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import partial
from os import environ
from pathlib import Path

from checkedtables.table import Finding
from datadesk.core.fetch import FetchPlan
from datadesk.core.listings import parse_listing
from datadesk.core.watch import plan_watch
from datadesk.shell.adapters.http_saved import SavedFolderError, SavedHttp
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.adapters.s3 import s3_store
from datadesk.shell.gather import gather_repo
from datadesk.shell.ports import Deps, EffectError
from datadesk.shell.run_fetch import retried, run_fetch
from datadesk.shell.settings import MissingSettings, load_settings


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
    try:
        entry = repo.catalog.entry(source)
    except KeyError:
        raise FetchStopped(f"the catalog has no source {source!r}") from None
    response = retried(partial(deps.http.get, entry.listing_url))
    if response.status != 200:
        raise FetchStopped(f"the listing {entry.listing_url} answered {response.status}")
    listing = parse_listing(entry, entry.listing_url, response.text)
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
        deps = Deps(SavedHttp(args.saved), s3_store(settings), PdfPlumberReader())
        run = fetch_command(deps, Path.cwd(), args.source, today)
    except (MissingSettings, SavedFolderError, FetchStopped, EffectError) as error:
        print(f"datadesk: {error}", file=sys.stderr)
        return 1
    print(f"listing sha256 {run.listing_sha256}")
    for finding in run.findings:
        print(f"{finding.severity} {finding.code} {finding.subject}: {finding.message}")
    print(f"\n{run.plan.pull_request.title}\n\n{run.plan.pull_request.body}")
    for path, _ in run.plan.pull_request.files:
        print(f"wrote {path}")
    return 0


def _findings(heading: str, findings: Sequence[Finding]) -> str:
    return "; ".join([heading, *(f"{f.code} {f.subject}: {f.message}" for f in findings)])
