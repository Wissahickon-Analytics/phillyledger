"""Read a publisher's listing page into links, each with the edition its title names."""

from dataclasses import dataclass
from hashlib import sha256
from re import compile
from typing import assert_never

from checkedtables.refs import Sha256
from checkedtables.table import Finding, Severity
from datadesk.core.catalog import ListingShape, SourceEntry
from datadesk.core.domain import EditionKey
from datadesk.core.listings import document_finder
from datadesk.core.listings.titles import TITLE_RULES, SkipReason

ADMIN_HOST = compile(r"^(https?://)admin\.phila\.gov/")


@dataclass(frozen=True, slots=True)
class ListedLink:
    """One link on a listing page, read as an edition or skipped with a reason.

    Attributes
    ----------
    url
        The link's URL on the canonical host, since admin.phila.gov and www.phila.gov serve
        the same file (QCASH-Q04).
    position
        Its place on the page, counted from 0.
    skip_reason
        Why the link names no edition, as the title rule returned it. A link has an edition or
        a skip reason, never both or neither.
    listed_at
        A stamp from the shape's parser. For a document-finder listing it is the 14-digit
        upload stamp in the URL's path.
    """

    url: str
    title: str
    position: int
    edition: EditionKey | None
    skip_reason: SkipReason | None
    listed_at: str

    def __post_init__(self) -> None:
        """Raise ValueError unless the link has an edition or a skip reason, and not both."""
        if (self.edition is None) == (self.skip_reason is None):
            raise ValueError(
                f"a link has an edition or a skip reason, never both or neither: {self}"
            )


@dataclass(frozen=True, slots=True)
class Listing:
    """The links of one listing page, in page order.

    Attributes
    ----------
    source
        The catalog id of the listing's source.
    html_sha256
        The sha256 of the page's text encoded as UTF-8.
    """

    source: str
    url: str
    html_sha256: Sha256
    links: tuple[ListedLink, ...]


def parse_listing(source: SourceEntry, url: str, html: str) -> Listing | Finding:
    """Read a listing page into its links, or return a BLOCK finding.

    The source's shape picks the parser, and the title rule of its series reads each link's title.
    Each URL moves to the canonical host. The findings are listing_unsupported, for a series with
    no title rule or a shape with no parser yet, and listing_unreadable from the shape's parser.
    """
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
        match read_title(link.title):
            case EditionKey() as edition:
                skip_reason = None
            case SkipReason() as skip_reason:
                edition = None
            case unhandled:
                assert_never(unhandled)
        # QCASH-Q04: admin.phila.gov and www.phila.gov serve the same file.
        canonical = ADMIN_HOST.sub(r"\1www.phila.gov/", link.url)
        links.append(
            ListedLink(canonical, link.title, position, edition, skip_reason, link.listed_at)
        )
    return Listing(source.id, url, Sha256(sha256(html.encode()).hexdigest()), tuple(links))


def _unsupported(source: SourceEntry, message: str) -> Finding:
    return Finding(Severity.BLOCK, "listing_unsupported", source.id, message)
