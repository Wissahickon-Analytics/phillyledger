from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import SourceCatalog
from datadesk.core.domain import ArchiveIndex, EditionKey
from datadesk.core.listings import ListedLink, Listing


@dataclass(frozen=True, slots=True)
class FetchRequest:
    edition: EditionKey
    url: str
    title: str
    listed_at: str
    reason: str


@dataclass(frozen=True, slots=True)
class WaybackLookup:
    url: str
    edition: EditionKey


@dataclass(frozen=True, slots=True)
class Gap:
    series: str
    edition: EditionKey
    note: str


@dataclass(frozen=True, slots=True)
class WatchPlan:
    fetch: tuple[FetchRequest, ...]
    wayback: tuple[WaybackLookup, ...]
    gaps: tuple[Gap, ...]
    findings: tuple[Finding, ...]


@dataclass(frozen=True, slots=True)
class PullRequestPlan:
    files: tuple[tuple[str, str], ...]
    branch: str
    title: str
    body: str


def plan_watch(
    catalog: SourceCatalog, listings: Sequence[Listing], index: ArchiveIndex, today: date
) -> WatchPlan:
    kept = [
        (link.edition, link)
        for listing in listings
        for link in listing.links
        if link.edition is not None
        and link.edition.period.end >= catalog.entry(listing.source).first_period_end
    ]
    last = dict(sorted(kept, key=_recency))
    fetch = tuple(
        request
        for edition, link in sorted(last.items())
        if (request := _request(edition, link, index)) is not None
    )
    findings = tuple(
        Finding(
            Severity.WARN,
            "not_a_quarter_end",
            link.url,
            f"{link.title!r} reads as a report whose date is not a quarter end, "
            "so it is not fetched",
        )
        for listing in listings
        for link in listing.links
        if link.skip_reason == "not_a_quarter_end"
    )
    return WatchPlan(fetch, (), (), findings)


def _recency(kept: tuple[EditionKey, ListedLink]) -> tuple[str, int]:
    _, link = kept
    return link.listed_at, -link.position


def _request(edition: EditionKey, link: ListedLink, index: ArchiveIndex) -> FetchRequest | None:
    versions = [version for version in index.versions if version.edition == edition]
    if any(link.url in version.urls for version in versions):
        return None
    reason = "revision" if versions else "new"
    return FetchRequest(edition, link.url, link.title, link.listed_at, reason)
