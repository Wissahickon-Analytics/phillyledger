"""Plan which listed reports to fetch, from the listings and the archive index."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import SourceCatalog
from datadesk.core.domain import ArchiveIndex, EditionKey
from datadesk.core.listings import ListedLink, Listing


@dataclass(frozen=True, slots=True)
class FetchRequest:
    """One report to download, with the listing facts that its index line will carry.

    `reason` is "new" when the index holds no version of the edition, and "revision" when it
    holds one.
    """

    edition: EditionKey
    url: str
    title: str
    listed_at: str
    reason: str


@dataclass(frozen=True, slots=True)
class WaybackLookup:
    """A URL to look up in the Wayback Machine for an edition's file.

    `plan_watch` makes none yet.
    """

    url: str
    edition: EditionKey


@dataclass(frozen=True, slots=True)
class Gap:
    """An edition that the catalog expects and the index lacks.

    `plan_watch` makes none yet.
    """

    series: str
    edition: EditionKey
    note: str


@dataclass(frozen=True, slots=True)
class WatchPlan:
    """What a watch decided: the reports to fetch and the findings about the listings.

    `plan_watch` leaves `wayback` and `gaps` empty.
    """

    fetch: tuple[FetchRequest, ...]
    wayback: tuple[WaybackLookup, ...]
    gaps: tuple[Gap, ...]
    findings: tuple[Finding, ...]


@dataclass(frozen=True, slots=True)
class PullRequestPlan:
    """The pull request a run proposes: the files it writes, its branch, title and body.

    `files` pairs each path in the checkout with the whole text of that file.
    """

    files: tuple[tuple[str, str], ...]
    branch: str
    title: str
    body: str


def plan_watch(
    catalog: SourceCatalog, listings: Sequence[Listing], index: ArchiveIndex, today: date
) -> WatchPlan:
    """Choose the listed reports to fetch.

    The last link for each edition wins: the greatest listed_at, and on equal stamps the latest
    position, since the City appends a revised attachment after the original (QPOS-Q32). An
    edition that ends before its source's `first_period_end` is dropped. A kept link is requested
    unless an indexed version of its own edition holds its URL. A URL that another edition holds
    is still requested, and `plan_fetch` judges the bytes by their sha. Each link skipped as
    not_a_quarter_end is a WARN finding with that code. `today` is not read yet.
    """
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
    # QPOS-Q32: the City appends a revised attachment after the original.
    return link.listed_at, link.position


def _request(edition: EditionKey, link: ListedLink, index: ArchiveIndex) -> FetchRequest | None:
    versions = [version for version in index.versions if version.edition == edition]
    if any(link.url in version.urls for version in versions):
        return None
    reason = "revision" if versions else "new"
    return FetchRequest(edition, link.url, link.title, link.listed_at, reason)
