"""Read the JSON feed of a document-finder listing into its links."""

from dataclasses import dataclass
from json import loads
from re import compile
from typing import Any, Never

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import SourceEntry

# RFC 3986, appendix B: the scheme and the authority, then the path, which ends at "?" or "#".
UPLOAD_STAMP = compile(r"(?>(?:[^:/?#]+:)?(?://[^/?#]*)?)[^?#]*?/media/(\d{14})/")


@dataclass(frozen=True, slots=True)
class PageLink:
    """One document that the feed lists, before its title is read.

    `listed_at` is the 14-digit upload stamp in the path of `url`.
    """

    title: str
    url: str
    listed_at: str


def parse(source: SourceEntry, text: str) -> tuple[PageLink, ...] | Finding:
    """Read the documents of the feed's categories titled `source.category`, in feed order.

    The feed is a JSON list of categories, each with a title and its documents. Each of these is
    a BLOCK listing_unreadable finding: text that is not JSON (NaN and Infinity included), a feed
    that is not a list, no category with that title, a document with no title, a blank title or
    no URL, and a URL with no upload stamp in its path.
    """
    try:
        feed = loads(text, parse_constant=_not_json)
    except ValueError as error:
        return _unreadable(source, f"the feed is not JSON: {error}")
    if not isinstance(feed, list):
        return _unreadable(source, "the feed is not a list of categories")
    groups = [group["documents"] for group in feed if _holds_documents(group, source.category)]
    if not groups:
        return _unreadable(source, f"the feed has no category {source.category!r} of documents")
    links: list[PageLink] = []
    for position, document in enumerate(document for documents in groups for document in documents):
        match document:
            case {"title": str() as title, "url": str() as url} if title.strip():
                stamp = UPLOAD_STAMP.match(url)
                if stamp is None:
                    return _unreadable(source, f"{url} has no upload stamp in its path")
                links.append(PageLink(title, url, stamp[1]))
            case _:
                return _unreadable(source, f"document {position} has no title or no URL")
    return tuple(links)


def _holds_documents(group: Any, category: str) -> bool:
    match group:
        case {"title": str() as title, "documents": list()}:
            return title == category
    return False


def _not_json(constant: str) -> Never:
    raise ValueError(f"{constant} is not a JSON value")


def _unreadable(source: SourceEntry, message: str) -> Finding:
    return Finding(Severity.BLOCK, "listing_unreadable", source.id, message)
