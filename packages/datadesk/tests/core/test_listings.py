from copy import deepcopy
from dataclasses import replace
from datetime import date
from hashlib import sha256
from json import dumps
from typing import Any

import pytest
from packages.datadesk.tests.core.fixtures.qcmr_feed import FEED

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import ListingShape, SourceEntry
from datadesk.core.domain import EditionKey, Period
from datadesk.core.listings import ListedLink, Listing, parse_listing

QCMR = SourceEntry(
    id="qcmr",
    series="qcmr",
    shape=ListingShape.DOCUMENT_FINDER,
    listing_url="https://api.phila.gov/phila/document-finder/v1/151831",
    category="Quarterly City Managers Report",
    first_period_end=date(2021, 9, 30),
)
FLOOR = date(2021, 9, 30)
FY2026_Q3 = EditionKey("qcmr", Period(date(2026, 1, 1), date(2026, 3, 31)))
FY2023_Q2 = EditionKey("qcmr", Period(date(2022, 10, 1), date(2022, 12, 31)))
OVERTIME = "https://admin.phila.gov/media/20201204144825/overtime-report-202009.pdf"


def feed() -> list[dict[str, Any]]:
    return deepcopy(FEED)


def qcmr_documents(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    (category,) = (c for c in categories if c["title"] == QCMR.category)
    return category["documents"]


def listing(categories: list[dict[str, Any]] = FEED, source: SourceEntry = QCMR) -> Listing:
    read = parse_listing(source, source.listing_url, dumps(categories))
    assert isinstance(read, Listing), read
    return read


def quarter_ends(first: date, last: date) -> list[date]:
    ends = (
        date(year, month, day)
        for year in range(first.year, last.year + 1)
        for month, day in ((3, 31), (6, 30), (9, 30), (12, 31))
    )
    return [end for end in ends if first <= end <= last]


def test_report_links_get_editions_and_infographics_are_skipped() -> None:
    links = listing().links
    assert len(links) == 34
    ends = [link.edition.period.end for link in links if link.edition]
    assert ends == quarter_ends(date(2021, 6, 30), date(2026, 3, 31))[::-1]
    assert sum(end >= FLOOR for end in ends) == 19
    infographics = [link for link in links if link.skip_reason == "infographic"]
    assert len(infographics) == 14
    assert all("Infographic" in link.title for link in infographics)
    assert infographics[-1].title == "Quarterly City Managers Report Infographic - June 30, 2021"
    assert {link.skip_reason for link in links} == {None, "infographic"}


def test_a_link_of_another_category_is_never_listed() -> None:
    changed = feed()
    (overtime,) = (c for c in changed if c["title"] != QCMR.category)
    report = deepcopy(qcmr_documents(changed)[0])
    overtime["documents"].append({**report, "url": report["url"].replace("R.pdf", "-2.pdf")})
    for categories in (FEED, changed):
        urls = [link.url for link in listing(categories).links]
        assert OVERTIME.replace("admin.", "www.") not in urls
        assert not any(url.endswith("-2.pdf") for url in urls)
        assert listing(categories).links == listing().links


def test_managers_and_manager_s_read_the_same() -> None:
    changed = feed()
    for document in qcmr_documents(changed):
        document["title"] = document["title"].replace("Manager's", "Managers")
    titles = [document["title"] for document in qcmr_documents(FEED)]
    assert sum("Manager's" in title for title in titles) == 9
    assert [link.edition for link in listing(changed).links] == [
        link.edition for link in listing().links
    ]
    (december,) = (link for link in listing().links if link.edition == FY2023_Q2)
    assert december.title == "Quarterly City Manager's Report - December 31, 2022"


def test_the_admin_host_becomes_www() -> None:
    urls = [document["url"] for document in qcmr_documents(FEED)]
    assert all(url.startswith("https://admin.phila.gov/media/") for url in urls)
    assert [link.url for link in listing().links] == [
        url.replace("https://admin.phila.gov/", "https://www.phila.gov/") for url in urls
    ]


def test_the_edition_comes_from_the_title_and_never_from_the_url() -> None:
    first = listing().links[0]
    assert first.url.endswith("/Quarterly-City-Managers-Report-March-30-2026R.pdf")
    assert first.title == "Quarterly City Managers Report - March 31, 2026"
    assert first.edition == FY2026_Q3


def test_each_link_is_listed_at_its_upload_stamp_in_feed_order() -> None:
    links = listing().links
    assert [link.position for link in links] == list(range(34))
    assert [link.listed_at for link in links] == [link.url.split("/")[4] for link in links]
    assert all(len(link.listed_at) == 14 and link.listed_at.isdigit() for link in links)
    assert links[0].listed_at == "20260515154446"


def test_the_listing_names_its_source_its_url_and_the_digest_of_its_text() -> None:
    text = dumps(FEED)
    assert listing() == Listing(
        "qcmr", QCMR.listing_url, sha256(text.encode()).hexdigest(), listing().links
    )


@pytest.mark.parametrize("shape", [ListingShape.PHILA_DOCUMENTS, ListingShape.MANUAL])
def test_a_shape_with_no_parser_yet_is_a_finding(shape: ListingShape) -> None:
    read = parse_listing(replace(QCMR, shape=shape), QCMR.listing_url, dumps(FEED))
    assert isinstance(read, Finding)
    assert (read.severity, read.code, read.subject) == (
        Severity.BLOCK,
        "listing_unsupported",
        "qcmr",
    )
    assert str(shape) in read.message


def test_a_series_with_no_title_rule_is_a_finding() -> None:
    read = parse_listing(replace(QCMR, series="collections_city"), QCMR.listing_url, "[]")
    assert isinstance(read, Finding)
    assert (read.severity, read.code, read.subject) == (
        Severity.BLOCK,
        "listing_unsupported",
        "qcmr",
    )
    assert "collections_city" in read.message


def without_url(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    del qcmr_documents(categories)[3]["url"]
    return categories


def without_stamp(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    document = qcmr_documents(categories)[3]
    document["url"] = document["url"].replace("/20250815155820/", "/")
    return categories


@pytest.mark.parametrize(
    ("text", "message"),
    [
        pytest.param("<html>Request blocked</html>", "not JSON", id="not_json"),
        pytest.param(dumps({"title": QCMR.category}), "not a list", id="not_a_list"),
        pytest.param(dumps(FEED[1:]), QCMR.category, id="no_such_category"),
        pytest.param(dumps(without_url(feed())), "document 3", id="a_document_with_no_url"),
        pytest.param(
            dumps(without_stamp(feed())),
            "https://admin.phila.gov/media/Quarterly-City-Managers-Report-June-30-2025.pdf",
            id="a_url_with_no_upload_stamp",
        ),
    ],
)
def test_a_feed_the_parser_cannot_read_is_a_finding(text: str, message: str) -> None:
    read = parse_listing(QCMR, QCMR.listing_url, text)
    assert isinstance(read, Finding)
    assert (read.severity, read.code, read.subject) == (
        Severity.BLOCK,
        "listing_unreadable",
        "qcmr",
    )
    assert message in read.message


def with_first_document(change: dict[str, Any]) -> str:
    categories = feed()
    qcmr_documents(categories)[0].update(change)
    return dumps(categories)


def assert_unreadable(text: str) -> None:
    read = parse_listing(QCMR, QCMR.listing_url, text)
    assert isinstance(read, Finding)
    assert (read.severity, read.code, read.subject) == (
        Severity.BLOCK,
        "listing_unreadable",
        "qcmr",
    )


@pytest.mark.parametrize(
    "change",
    [
        pytest.param({"title": ""}, id="an_empty_title"),
        pytest.param({"title": " \t"}, id="a_blank_title"),
        pytest.param({"url": ""}, id="an_empty_url"),
        pytest.param({"url": " "}, id="a_blank_url"),
    ],
)
def test_a_blank_title_or_url_makes_the_feed_unreadable(change: dict[str, str]) -> None:
    assert_unreadable(with_first_document(change))


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            "https://admin.phila.gov/report.pdf?old=/media/20260515154446/", id="in_the_query"
        ),
        pytest.param(
            "https://admin.phila.gov/report.pdf#/media/20260515154446/", id="in_the_fragment"
        ),
        pytest.param("https://media/20260515154446/report.pdf", id="in_the_host"),
    ],
)
def test_an_upload_stamp_outside_the_url_path_makes_the_feed_unreadable(url: str) -> None:
    assert_unreadable(with_first_document({"url": url}))


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity"])
def test_a_bare_nan_or_infinity_makes_the_feed_unreadable(token: str) -> None:
    text = with_first_document({"modified": float(token)})
    assert f'"modified": {token},' in text
    assert_unreadable(text)


def test_a_listed_link_has_an_edition_or_a_skip_reason() -> None:
    link = listing().links[0]
    with pytest.raises(ValueError, match="edition or a skip reason"):
        replace(link, skip_reason="infographic")
    with pytest.raises(ValueError, match="edition or a skip reason"):
        ListedLink(link.url, link.title, 0, None, None, link.listed_at)
