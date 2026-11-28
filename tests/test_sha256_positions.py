from typing import Any, get_type_hints

from checkedtables.records import ReviewedReading
from checkedtables.refs import Sha256, WordRef
from checkedtables.testing import page_from_text
from checkedtables.words import Document, Page
from datadesk.core.domain import ArchiveIndex, DocumentVersion
from datadesk.core.fetch import Fetched, StoreObject
from datadesk.core.listings import ListedLink, Listing
from datadesk.core.listings.titles import SkipReason
from datadesk.core.records import EditionNote, TablePages, illegible_pages
from datadesk.shell.cli import FetchRun
from datadesk.shell.run_fetch import put_immutable

POSITIONS: tuple[tuple[Any, str, object], ...] = (
    (WordRef, "doc_sha256", Sha256),
    (Page, "doc_sha256", Sha256),
    (Document, "sha256", Sha256),
    (ReviewedReading, "doc_sha256", Sha256),
    (page_from_text, "sha", Sha256),
    (DocumentVersion, "sha256", Sha256),
    (DocumentVersion, "supersedes", Sha256 | None),
    (ArchiveIndex.by_sha, "sha", Sha256),
    (Fetched, "sha256", Sha256 | None),
    (StoreObject, "sha256", Sha256),
    (EditionNote, "doc_sha256", Sha256),
    (TablePages, "doc_sha256", Sha256),
    (illegible_pages, "sha", Sha256),
    (Listing, "html_sha256", Sha256),
    (ListedLink, "skip_reason", SkipReason | None),
    (FetchRun, "listing_sha256", Sha256),
    (put_immutable, "sha", Sha256),
)


def test_every_sha_position_is_annotated_sha256() -> None:
    wrong = [
        (owner.__qualname__, name, get_type_hints(owner)[name])
        for owner, name, annotation in POSITIONS
        if get_type_hints(owner)[name] != annotation
    ]
    assert wrong == []
