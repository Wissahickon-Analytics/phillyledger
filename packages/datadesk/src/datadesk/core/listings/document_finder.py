from dataclasses import dataclass
from json import JSONDecodeError, loads
from re import compile
from typing import Any
from urllib.parse import urlsplit

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import SourceEntry

UPLOAD_STAMP = compile(r"/media/(\d{14})/")


@dataclass(frozen=True, slots=True)
class PageLink:
    title: str
    url: str
    listed_at: str


def parse(source: SourceEntry, text: str) -> tuple[PageLink, ...] | Finding:
    try:
        feed = loads(text)
    except JSONDecodeError as error:
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
                stamp = UPLOAD_STAMP.search(urlsplit(url).path)
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


def _unreadable(source: SourceEntry, message: str) -> Finding:
    return Finding(Severity.BLOCK, "listing_unreadable", source.id, message)
