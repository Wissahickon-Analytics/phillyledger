from dataclasses import dataclass
from hashlib import sha256
from re import compile

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import ListingShape, SourceEntry
from datadesk.core.domain import EditionKey
from datadesk.core.listings import document_finder
from datadesk.core.listings.titles import TITLE_RULES

ADMIN_HOST = compile(r"^(https?://)admin\.phila\.gov/")


@dataclass(frozen=True, slots=True)
class ListedLink:
    url: str
    title: str
    position: int
    edition: EditionKey | None
    skip_reason: str | None
    listed_at: str

    def __post_init__(self) -> None:
        if (self.edition is None) == (self.skip_reason is None):
            raise ValueError(
                f"a link has an edition or a skip reason, never both or neither: {self}"
            )


@dataclass(frozen=True, slots=True)
class Listing:
    source: str
    url: str
    html_sha256: str
    links: tuple[ListedLink, ...]


def parse_listing(source: SourceEntry, url: str, html: str) -> Listing | Finding:
    read_title = TITLE_RULES.get(source.series)
    if read_title is None:
        return _unsupported(source, f"no title rule reads the series {source.series}")
    match source.shape:
        case ListingShape.DOCUMENT_FINDER:
            page = document_finder.parse(source, html)
        case ListingShape.PHILA_DOCUMENTS | ListingShape.MANUAL:
            return _unsupported(source, f"no parser reads the shape {source.shape} yet")
    if isinstance(page, Finding):
        return page
    links = []
    for position, link in enumerate(page):
        reading = read_title(link.title)
        edition, skip_reason = (
            (reading, None) if isinstance(reading, EditionKey) else (None, reading)
        )
        # QCASH-Q04: admin.phila.gov and www.phila.gov serve the same file.
        canonical = ADMIN_HOST.sub(r"\1www.phila.gov/", link.url)
        links.append(
            ListedLink(canonical, link.title, position, edition, skip_reason, link.listed_at)
        )
    return Listing(source.id, url, sha256(html.encode()).hexdigest(), tuple(links))


def _unsupported(source: SourceEntry, message: str) -> Finding:
    return Finding(Severity.BLOCK, "listing_unsupported", source.id, message)
