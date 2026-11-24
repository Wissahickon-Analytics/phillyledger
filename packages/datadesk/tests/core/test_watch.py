from copy import deepcopy
from dataclasses import replace
from datetime import date
from hashlib import sha256
from json import dumps
from typing import Any

from hypothesis import given
from hypothesis import strategies as st
from packages.datadesk.tests.core.fixtures.qcmr_feed import FEED

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import ListingShape, SourceCatalog, SourceEntry
from datadesk.core.domain import ArchiveIndex, DocumentVersion, EditionKey, Period
from datadesk.core.listings import Listing, parse_listing
from datadesk.core.watch import FetchRequest, WatchPlan, plan_watch

QCMR = SourceEntry(
    id="qcmr",
    series="qcmr",
    shape=ListingShape.DOCUMENT_FINDER,
    listing_url="https://api.phila.gov/phila/document-finder/v1/151831",
    category="Quarterly City Managers Report",
    first_period_end=date(2021, 9, 30),
)
TODAY = date(2026, 11, 24)
EMPTY = ArchiveIndex(())
MEDIA = "https://www.phila.gov/media"
FY2021_Q4 = EditionKey("qcmr", Period(date(2021, 4, 1), date(2021, 6, 30)))
FY2022_Q1 = EditionKey("qcmr", Period(date(2021, 7, 1), date(2021, 9, 30)))
FY2025_Q4 = EditionKey("qcmr", Period(date(2025, 4, 1), date(2025, 6, 30)))
FY2026_Q2 = EditionKey("qcmr", Period(date(2025, 10, 1), date(2025, 12, 31)))
FY2026_Q3 = EditionKey("qcmr", Period(date(2026, 1, 1), date(2026, 3, 31)))
Q3_URL = f"{MEDIA}/20260515154446/Quarterly-City-Managers-Report-March-30-2026R.pdf"
Q4_2025_URL = f"{MEDIA}/20250815155820/Quarterly-City-Managers-Report-June-30-2025.pdf"


def feed() -> list[dict[str, Any]]:
    return deepcopy(FEED)


def qcmr_documents(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    (category,) = (c for c in categories if c["title"] == QCMR.category)
    return category["documents"]


def plan(
    categories: list[dict[str, Any]] = FEED,
    index: ArchiveIndex = EMPTY,
    source: SourceEntry = QCMR,
) -> WatchPlan:
    listing = parse_listing(source, source.listing_url, dumps(categories))
    assert isinstance(listing, Listing), listing
    return plan_watch(SourceCatalog((source,)), [listing], index, TODAY)


def indexed(*requests: FetchRequest, edition: EditionKey | None = None) -> ArchiveIndex:
    return ArchiveIndex(
        tuple(
            DocumentVersion(
                sha256=sha256(request.url.encode()).hexdigest(),
                edition=edition or request.edition,
                listed_at=request.listed_at,
                urls=(request.url,),
                title=request.title,
                printed_period=None,
                supersedes=None,
            )
            for request in requests
        )
    )


def quarter_ends(first: date, last: date) -> list[date]:
    ends = (
        date(year, month, day)
        for year in range(first.year, last.year + 1)
        for month, day in ((3, 31), (6, 30), (9, 30), (12, 31))
    )
    return [end for end in ends if first <= end <= last]


def test_plan_watch_asks_for_one_fetch_for_each_listed_edition_on_an_empty_index() -> None:
    watch = plan()
    assert [request.edition.period.end for request in watch.fetch] == quarter_ends(
        date(2021, 9, 30), date(2026, 3, 31)
    )
    assert {request.reason for request in watch.fetch} == {"new"}
    assert watch.fetch[-1] == FetchRequest(
        FY2026_Q3,
        Q3_URL,
        "Quarterly City Managers Report - March 31, 2026",
        "20260515154446",
        "new",
    )
    assert (watch.wayback, watch.gaps, watch.findings) == ((), (), ())


def test_the_report_before_the_floor_gets_no_request_and_the_first_after_it_gets_one() -> None:
    watch = plan()
    assert FY2021_Q4 not in [request.edition for request in watch.fetch]
    assert watch.fetch[0] == FetchRequest(
        FY2022_Q1,
        f"{MEDIA}/20211116102946/Quarterly-City-Managers-Report-September-30-2021.pdf",
        "Quarterly City Managers Report - September 30, 2021",
        "20211116102946",
        "new",
    )
    lower = plan(source=replace(QCMR, first_period_end=date(2021, 6, 30)))
    assert [request.edition for request in lower.fetch[:2]] == [FY2021_Q4, FY2022_Q1]


def test_plan_watch_asks_for_nothing_when_the_index_holds_every_url() -> None:
    assert plan(index=indexed(*plan().fetch)).fetch == ()


@given(st.sets(st.integers(min_value=0, max_value=18)))
def test_plan_watch_asks_for_each_edition_whose_url_the_index_lacks(held: set[int]) -> None:
    requests = plan().fetch
    index = indexed(*(requests[number] for number in sorted(held)))
    assert plan(index=index).fetch == tuple(
        request for number, request in enumerate(requests) if number not in held
    )


def test_the_last_of_two_attachments_for_one_quarter_is_asked_for_alone() -> None:
    changed = feed()
    original = next(
        document
        for document in qcmr_documents(changed)
        if document["title"] == "Quarterly City Managers Report - June 30, 2025"
    )
    revised = "https://admin.phila.gov/media/20250901120000/Quarterly-City-Managers-Report-June-30-2025-1.pdf"
    qcmr_documents(changed).append({**original, "url": revised})
    fetch = plan(changed).fetch
    assert len(fetch) == 19
    assert [request.url for request in fetch if request.edition == FY2025_Q4] == [
        revised.replace("admin.", "www.")
    ]


def test_an_earlier_stamp_listed_last_does_not_win() -> None:
    changed = feed()
    original = next(
        document
        for document in qcmr_documents(changed)
        if document["title"] == "Quarterly City Managers Report - June 30, 2025"
    )
    earlier = "https://admin.phila.gov/media/20250801120000/Quarterly-City-Managers-Report-June-30-2025-1.pdf"
    qcmr_documents(changed).append({**original, "url": earlier})
    fetch = plan(changed).fetch
    assert [request.url for request in fetch if request.edition == FY2025_Q4] == [Q4_2025_URL]


def test_a_tie_of_upload_stamps_goes_to_the_link_listed_first() -> None:
    changed = feed()
    first = qcmr_documents(changed)[0]
    second = {**first, "url": first["url"].replace("R.pdf", "-1.pdf")}
    qcmr_documents(changed).insert(1, second)
    fetch = plan(changed).fetch
    assert [request.url for request in fetch if request.edition == FY2026_Q3] == [Q3_URL]


def test_a_report_title_dated_march_30_gives_a_finding_and_no_fetch() -> None:
    changed = feed()
    qcmr_documents(changed)[0]["title"] = "Quarterly City Managers Report - March 30, 2026"
    watch = plan(changed)
    assert FY2026_Q3 not in [request.edition for request in watch.fetch]
    assert len(watch.fetch) == 18
    assert watch.findings == (
        Finding(
            Severity.WARN,
            "not_a_quarter_end",
            Q3_URL,
            "'Quarterly City Managers Report - March 30, 2026' reads as a report "
            "whose date is not a quarter end, so it is not fetched",
        ),
    )


def test_a_new_url_for_an_indexed_edition_is_a_revision() -> None:
    held = replace(plan().fetch[-1], url=f"{MEDIA}/20260514000000/Report-March-31-2026.pdf")
    fetch = plan(index=indexed(held)).fetch
    assert fetch[-1] == replace(plan().fetch[-1], reason="revision")
    assert {request.reason for request in fetch[:-1]} == {"new"}


def test_a_url_that_another_edition_holds_is_still_asked_for() -> None:
    q3 = plan().fetch[-1]
    fetch = plan(index=indexed(q3, edition=FY2026_Q2)).fetch
    assert fetch[-1] == q3
    assert [request.reason for request in fetch if request.edition == FY2026_Q2] == ["revision"]
