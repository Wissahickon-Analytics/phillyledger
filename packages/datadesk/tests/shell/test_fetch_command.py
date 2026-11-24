import shutil
from copy import deepcopy
from dataclasses import dataclass, replace
from datetime import date, datetime
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from typing import Any

import pytest
from packages.datadesk.tests.core.fixtures.qcmr_feed import FEED
from packages.datadesk.tests.shell.fakes import (
    DictStore,
    FakeHttp,
    FakePdf,
    FlakyHttp,
    FlakyStore,
    LostReplyStore,
    answer,
)
from packages.datadesk.tests.shell.pdfs import text_pdf

from datadesk.core.domain import ArchiveIndex, DocumentVersion, EditionKey, Period
from datadesk.core.fetch import Rejection
from datadesk.core.index import render_index
from datadesk.core.watch import FetchRequest
from datadesk.shell import cli
from datadesk.shell.adapters.http_saved import SavedHttp
from datadesk.shell.adapters.s3 import S3Store, s3_store
from datadesk.shell.cli import FetchRun, FetchStopped, fetch_command, main
from datadesk.shell.ports import Deps, EffectError, Http, ObjectStore, PreconditionFailed
from datadesk.shell.settings import Settings

REPO = Path(__file__).parents[4]
CATALOG_FILE = "packages/datadesk/src/datadesk/data/catalog.toml"
INDEX_FILE = "packages/datadesk/src/datadesk/data/index.jsonl"
LISTING_URL = "https://api.phila.gov/phila/document-finder/v1/151831"
CATEGORY = "Quarterly City Managers Report"
FLOOR = date(2021, 9, 30)
TODAY = date(2026, 11, 24)
FY2026_Q4_URL = (
    "https://admin.phila.gov/media/20260817162758/Quarterly-City-Managers-Report-June-30-2026.pdf"
)
ENVIRON = {
    "DATADESK_R2_ENDPOINT_URL": "http://store.invalid:9000",
    "DATADESK_R2_ACCESS_KEY_ID": "access-key-PLANTED",
    "DATADESK_R2_SECRET_ACCESS_KEY": "secret-key-PLANTED",
    "DATADESK_R2_ARCHIVE_BUCKET": "archive",
}


@dataclass(frozen=True)
class Report:
    edition: EditionKey
    url: str
    title: str
    listed_at: str
    body: bytes
    cover: str

    @property
    def sha(self) -> str:
        return sha256(self.body).hexdigest()

    @property
    def key(self) -> str:
        return f"pdf/{self.sha[:2]}/{self.sha}.pdf"


def reports(feed: list[dict[str, Any]]) -> list[Report]:
    (category,) = (category for category in feed if category["title"] == CATEGORY)
    found = []
    for document in category["documents"]:
        title = document["title"]
        end = datetime.strptime(title.rpartition(" - ")[2], "%B %d, %Y").date()
        if "Infographic" in title or end < FLOOR:
            continue
        url = document["url"].replace("https://admin.phila.gov/", "https://www.phila.gov/")
        found.append(
            Report(
                edition=EditionKey("qcmr", Period(date(end.year, end.month - 2, 1), end)),
                url=url,
                title=title,
                listed_at=url.split("/")[4],
                body=f"%PDF-1.4 the report at {url}\n".encode(),
                cover=f"FOR THE PERIOD ENDING {end:%B} {end.day}, {end.year}".upper(),
            )
        )
    return found


def with_fy2026_q4(feed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grown = deepcopy(feed)
    (category,) = (category for category in grown if category["title"] == CATEGORY)
    newest = category["documents"][0]
    title = "Quarterly City Managers Report - June 30, 2026"
    category["documents"].insert(0, {**newest, "url": FY2026_Q4_URL, "title": title})
    return grown


def only(feed: list[dict[str, Any]], *titles: str) -> list[dict[str, Any]]:
    cut = deepcopy(feed)
    for category in cut:
        if category["title"] == CATEGORY:
            category["documents"] = [d for d in category["documents"] if d["title"] in titles]
    return cut


def feed_bytes(feed: list[dict[str, Any]]) -> bytes:
    return dumps(feed).encode()


def fake_http(feed: list[dict[str, Any]], listed: list[Report]) -> FakeHttp:
    return FakeHttp({LISTING_URL: feed_bytes(feed), **{r.url: r.body for r in listed}})


def fake_pdf(listed: list[Report]) -> FakePdf:
    return FakePdf({report.body: report.cover for report in listed})


def checkout(root: Path, index: str = "") -> Path:
    (root / INDEX_FILE).parent.mkdir(parents=True)
    shutil.copyfile(REPO / CATALOG_FILE, root / CATALOG_FILE)
    (root / INDEX_FILE).write_text(index, encoding="utf-8")
    return root


def index_lines(root: Path) -> list[tuple[str, str, str, str, str]]:
    lines = [loads(line) for line in (root / INDEX_FILE).read_text().splitlines()]
    return [
        (
            line["edition"]["series"],
            line["edition"]["period"]["start"],
            line["edition"]["period"]["end"],
            line["edition"]["stage"],
            line["sha256"],
        )
        for line in lines
    ]


def expected_lines(listed: list[Report]) -> list[tuple[str, str, str, str, str]]:
    return sorted(
        (
            "qcmr",
            report.edition.period.start.isoformat(),
            report.edition.period.end.isoformat(),
            "none",
            report.sha,
        )
        for report in listed
    )


def stored(listed: list[Report]) -> dict[str, bytes]:
    return {report.key: report.body for report in listed}


def run(http: Http, store: ObjectStore, listed: list[Report], root: Path) -> FetchRun:
    return fetch_command(Deps(http, store, fake_pdf(listed)), root, "qcmr", TODAY)


def test_the_fixture_lists_19_reports_from_fy2022_q1_to_fy2026_q3() -> None:
    ends = [report.edition.period.end for report in reports(FEED)]
    assert (len(ends), min(ends), max(ends)) == (19, date(2021, 9, 30), date(2026, 3, 31))


def test_fetching_the_same_listing_again_adds_nothing(tmp_path: Path) -> None:
    root = checkout(tmp_path)
    listed = reports(FEED)
    http, store = fake_http(FEED, listed), DictStore()

    first = run(http, store, listed, root)
    assert store.objects == stored(listed)
    assert index_lines(root) == expected_lines(listed)
    assert sorted(http.calls) == sorted([LISTING_URL, *(report.url for report in listed)])
    assert first.listing_sha256 == sha256(feed_bytes(FEED)).hexdigest()
    assert (first.findings, first.plan.rejections) == ((), ())
    index_after_first = (root / INDEX_FILE).read_bytes()
    puts_after_first = list(store.puts)
    calls_after_first = len(http.calls)

    second = run(http, store, listed, root)
    assert store.puts == puts_after_first
    assert (root / INDEX_FILE).read_bytes() == index_after_first
    assert second.plan.pull_request.files == ()
    assert http.calls[calls_after_first:] == [LISTING_URL]
    assert second.listing_sha256 == first.listing_sha256
    assert (second.findings, second.plan.rejections) == ((), ())

    grown = with_fy2026_q4(FEED)
    (new,) = [report for report in reports(grown) if report not in listed]
    assert new.edition.period.end == date(2026, 6, 30)
    http.bodies.update({LISTING_URL: feed_bytes(grown), new.url: new.body})
    third = run(http, store, [*listed, new], root)
    assert store.puts == [*puts_after_first, new.key]
    assert store.objects == stored([*listed, new])
    assert index_lines(root) == expected_lines([*listed, new])
    assert (third.findings, third.plan.rejections) == ((), ())


@pytest.mark.parametrize("failing", ["listing", "report"])
def test_a_get_that_fails_once_is_tried_again_and_stores_once(failing: str, tmp_path: Path) -> None:
    root = checkout(tmp_path)
    listed = reports(FEED)
    url = LISTING_URL if failing == "listing" else listed[3].url
    store = DictStore()
    run(FlakyHttp(fake_http(FEED, listed), url, 1), store, listed, root)
    assert sorted(store.puts) == sorted(stored(listed))
    assert store.objects == stored(listed)
    assert index_lines(root) == expected_lines(listed)


def test_a_put_that_fails_once_is_tried_again_and_stores_once(tmp_path: Path) -> None:
    root = checkout(tmp_path)
    listed = reports(FEED)
    store = DictStore()
    run(fake_http(FEED, listed), FlakyStore(store, 1), listed, root)
    assert sorted(store.puts) == sorted(stored(listed))
    assert store.objects == stored(listed)
    assert index_lines(root) == expected_lines(listed)


def test_a_put_whose_reply_was_lost_completes_on_the_next_try(tmp_path: Path) -> None:
    root = checkout(tmp_path)
    listed = reports(FEED)
    store = DictStore()
    run(fake_http(FEED, listed), LostReplyStore(store, 1), listed, root)
    assert store.objects == stored(listed)
    assert index_lines(root) == expected_lines(listed)


def test_other_bytes_under_a_report_s_key_stop_the_command_after_one_put(tmp_path: Path) -> None:
    root = checkout(tmp_path)
    listed = reports(FEED)
    store = DictStore({listed[0].key: b"other bytes"})
    with pytest.raises(PreconditionFailed):
        run(fake_http(FEED, listed), store, listed, root)
    assert store.puts.count(listed[0].key) == 1
    assert store.objects[listed[0].key] == b"other bytes"
    assert (root / INDEX_FILE).read_text() == ""


@pytest.mark.parametrize("failing", ["listing", "report", "put"])
@pytest.mark.parametrize("failures", [2, 3])
def test_three_failures_stop_the_command_with_the_index_unchanged(
    failing: str, failures: int, tmp_path: Path
) -> None:
    root = checkout(tmp_path)
    listed = reports(FEED)
    store = DictStore()
    run(fake_http(FEED, listed), store, listed, root)
    index_before = (root / INDEX_FILE).read_bytes()
    grown = with_fy2026_q4(FEED)
    (new,) = [report for report in reports(grown) if report not in listed]
    http: Http = fake_http(grown, [*listed, new])
    flaky: ObjectStore = store
    match failing:
        case "listing":
            http = FlakyHttp(http, LISTING_URL, failures)
        case "report":
            http = FlakyHttp(http, new.url, failures)
        case "put":
            flaky = FlakyStore(store, failures)
    if failures == 3:
        with pytest.raises(EffectError):
            run(http, flaky, [*listed, new], root)
        assert (root / INDEX_FILE).read_bytes() == index_before
        assert store.objects == stored(listed)
    else:
        run(http, flaky, [*listed, new], root)
        assert index_lines(root) == expected_lines([*listed, new])
        assert store.objects == stored([*listed, new])


@pytest.mark.parametrize(
    ("catalog", "index", "source"),
    [
        pytest.param("[[source]\n", "", "qcmr", id="a_catalog_that_is_not_toml"),
        pytest.param(None, "not json\n", "qcmr", id="an_index_that_is_not_json"),
        pytest.param(None, '{"sha256": "x"}\n', "qcmr", id="an_index_line_with_missing_keys"),
        pytest.param(None, "[]\n", "qcmr", id="an_index_line_that_is_not_an_object"),
        pytest.param(None, "", "qsmr", id="a_source_the_catalog_lacks"),
    ],
)
def test_a_checkout_the_command_cannot_read_stops_it_before_any_request(
    catalog: str | None, index: str, source: str, tmp_path: Path
) -> None:
    root = checkout(tmp_path, index)
    if catalog is not None:
        (root / CATALOG_FILE).write_text(catalog)
    listed = reports(FEED)
    http, store = fake_http(FEED, listed), DictStore()
    with pytest.raises(FetchStopped):
        fetch_command(Deps(http, store, fake_pdf(listed)), root, source, TODAY)
    assert (http.calls, store.puts) == ([], [])
    assert (root / INDEX_FILE).read_text() == index


@pytest.mark.parametrize(
    "path", [pytest.param(CATALOG_FILE, id="catalog"), pytest.param(INDEX_FILE, id="index")]
)
@pytest.mark.parametrize(
    "body", [pytest.param(None, id="absent"), pytest.param(b"\xff\n", id="not_utf_8")]
)
def test_a_checkout_file_the_command_cannot_read_or_decode_stops_it_before_any_request(
    path: str, body: bytes | None, tmp_path: Path
) -> None:
    root = checkout(tmp_path)
    if body is None:
        (root / path).unlink()
    else:
        (root / path).write_bytes(body)
    listed = reports(FEED)
    http, store = fake_http(FEED, listed), DictStore()
    with pytest.raises(FetchStopped, match=path):
        run(http, store, listed, root)
    assert (http.calls, store.puts) == ([], [])


def test_an_index_that_breaks_its_own_rules_stops_the_command(tmp_path: Path) -> None:
    listed = reports(FEED)
    one, other = listed[0], listed[1]
    line = DocumentVersion(
        one.sha, one.edition, one.listed_at, (one.url,), one.title, one.edition.period, None
    )
    alias = replace(line, edition=other.edition, printed_period=other.edition.period)
    index = render_index(ArchiveIndex((line,))) + render_index(ArchiveIndex((alias,)))
    root = checkout(tmp_path, index)
    http, store = fake_http(FEED, listed), DictStore()
    with pytest.raises(FetchStopped):
        run(http, store, listed, root)
    assert (http.calls, store.puts) == ([], [])


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(b"not json", id="a_listing_that_is_not_json"),
        pytest.param(b"\xff[]", id="a_listing_that_is_not_utf_8"),
        pytest.param(
            feed_bytes([c for c in FEED if c["title"] != CATEGORY]),
            id="a_listing_without_the_category",
        ),
    ],
)
def test_a_listing_the_command_cannot_read_stops_it_before_any_put(
    body: bytes, tmp_path: Path
) -> None:
    root = checkout(tmp_path)
    listed = reports(FEED)
    http, store = fake_http(FEED, listed), DictStore()
    http.bodies[LISTING_URL] = body
    with pytest.raises(FetchStopped):
        run(http, store, listed, root)
    assert (http.calls, store.puts) == ([LISTING_URL], [])
    assert (root / INDEX_FILE).read_text() == ""


def saved_folder(folder: Path, feed: list[dict[str, Any]] | None, listed: list[Report]) -> Path:
    folder.mkdir()
    rows = []
    if feed is not None:
        (folder / "feed.json").write_bytes(feed_bytes(feed))
        rows.append(f"{LISTING_URL}\tfeed.json")
    for report in listed:
        name = f"qcmr-{report.edition.period.end}.pdf"
        (folder / name).write_bytes(report.body)
        rows.append(f"{report.url}\t{name}")
    (folder / "responses.tsv").write_text("".join(f"{row}\n" for row in ["url\tfile", *rows]))
    return folder


def test_the_command_stores_and_indexes_what_a_saved_folder_lists(tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout")
    listed = reports(FEED)
    store = DictStore()
    run(SavedHttp(saved_folder(tmp_path / "saved", FEED, listed)), store, listed, root)
    assert store.objects == stored(listed)
    assert index_lines(root) == expected_lines(listed)


def test_a_saved_folder_without_the_feed_s_row_stops_the_command_before_any_put(
    tmp_path: Path,
) -> None:
    root = checkout(tmp_path / "checkout")
    listed = reports(FEED)
    store = DictStore()
    with pytest.raises(FetchStopped, match="404"):
        run(SavedHttp(saved_folder(tmp_path / "saved", None, listed)), store, listed, root)
    assert store.puts == []
    assert (root / INDEX_FILE).read_text() == ""


@pytest.mark.parametrize("serves", ["the_indexed_bytes", "other_bytes"])
def test_an_edition_listed_at_a_url_another_edition_holds_is_fetched_and_judged_by_its_sha(
    serves: str, tmp_path: Path
) -> None:
    listed = reports(FEED)
    march = next(report for report in listed if report.edition.period.end == date(2026, 3, 31))
    december = next(r for r in listed if r.edition.period.end == date(2025, 12, 31))
    held = DocumentVersion(
        december.sha,
        december.edition,
        december.listed_at,
        (december.url, march.url),
        december.title,
        december.edition.period,
        None,
    )
    index = render_index(ArchiveIndex((held,)))
    root = checkout(tmp_path / "checkout", index)
    feed = only(FEED, march.title)
    body = december.body if serves == "the_indexed_bytes" else march.body
    folder = saved_folder(tmp_path / "saved", feed, [])
    (folder / "march.pdf").write_bytes(body)
    with (folder / "responses.tsv").open("a") as responses:
        responses.write(f"{march.url}\tmarch.pdf\n")
    store = DictStore()
    result = run(SavedHttp(folder), store, [march, december], root)
    request = FetchRequest(march.edition, march.url, march.title, march.listed_at, "new")
    if serves == "the_indexed_bytes":
        assert result.plan.rejections == (Rejection(request, "content_alias"),)
        assert store.puts == []
        assert (root / INDEX_FILE).read_text() == index
    else:
        assert result.plan.rejections == ()
        assert store.objects == stored([march])
        assert index_lines(root) == expected_lines([december, march])


def test_main_runs_the_fetch_from_the_working_directory_and_prints_the_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout")
    feed = only(FEED, *(report.title for report in reports(FEED)[:2]))
    pdfs = [replace(report, body=text_pdf(report.cover)) for report in reports(feed)]
    folder = saved_folder(tmp_path / "saved", feed, pdfs)
    store = DictStore()
    monkeypatch.setattr(cli, "s3_store", lambda settings: store)
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["fetch", "qcmr", "--saved", str(folder)]) == 0
    assert store.objects == stored(pdfs)
    assert index_lines(root) == expected_lines(pdfs)
    out, err = capsys.readouterr()
    assert sha256(feed_bytes(feed)).hexdigest() in out
    assert "feat(datadesk): index fetched reports" in out
    assert all(report.sha in out for report in pdfs)
    assert INDEX_FILE in out
    assert err == ""


def test_main_with_a_missing_variable_names_it_and_prints_no_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout")
    folder = saved_folder(tmp_path / "saved", FEED, [])
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("DATADESK_R2_SECRET_ACCESS_KEY")
    monkeypatch.chdir(root)
    assert main(["fetch", "qcmr", "--saved", str(folder)]) != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert "DATADESK_R2_SECRET_ACCESS_KEY" in err
    assert len(err.splitlines()) == 1
    assert not [value for value in ENVIRON.values() if value in out + err]
    assert (root / INDEX_FILE).read_text() == ""


def test_main_prints_neither_r2_key_when_the_store_echoes_both(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout")
    feed = only(FEED, reports(FEED)[0].title)
    pdfs = [replace(report, body=text_pdf(report.cover)) for report in reports(feed)]
    folder = saved_folder(tmp_path / "saved", feed, pdfs)
    keys = (ENVIRON["DATADESK_R2_ACCESS_KEY_ID"], ENVIRON["DATADESK_R2_SECRET_ACCESS_KEY"])
    echo = (
        "<Error><Code>InvalidAccessKeyId</Code><Message>no key {} with secret {}</Message></Error>"
    )

    def refusing_store(settings: Settings) -> S3Store:
        store = s3_store(settings)
        answer(store, 403, {}, echo.format(*keys).encode())
        return store

    monkeypatch.setattr(cli, "s3_store", refusing_store)
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["fetch", "qcmr", "--saved", str(folder)]) == 1
    out, err = capsys.readouterr()
    assert "InvalidAccessKeyId" in err
    assert not [key for key in keys if key in out + err]


def test_main_with_a_saved_row_that_names_a_missing_file_stops_before_any_put(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout")
    listed = reports(FEED)
    folder = saved_folder(tmp_path / "saved", FEED, listed)
    (folder / f"qcmr-{listed[0].edition.period.end}.pdf").unlink()
    store = DictStore()
    monkeypatch.setattr(cli, "s3_store", lambda settings: store)
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["fetch", "qcmr", "--saved", str(folder)]) != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert f"qcmr-{listed[0].edition.period.end}.pdf" in err
    assert len(err.splitlines()) == 1
    assert store.puts == []
    assert (root / INDEX_FILE).read_text() == ""


@pytest.mark.parametrize(
    "broken",
    [
        "a_responses_file_that_is_not_utf_8",
        "a_listing_that_is_not_utf_8",
        "a_working_directory_that_is_not_a_checkout",
    ],
)
def test_main_prints_one_line_for_an_input_it_cannot_read(
    broken: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = checkout(tmp_path / "checkout")
    folder = saved_folder(tmp_path / "saved", FEED, [])
    match broken:
        case "a_responses_file_that_is_not_utf_8":
            (folder / "responses.tsv").write_bytes(b"url\tfile\n\xff\tfeed.json\n")
        case "a_listing_that_is_not_utf_8":
            (folder / "feed.json").write_bytes(b"\xff[]")
        case "a_working_directory_that_is_not_a_checkout":
            root = tmp_path / "elsewhere"
            root.mkdir()
    store = DictStore()
    monkeypatch.setattr(cli, "s3_store", lambda settings: store)
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["fetch", "qcmr", "--saved", str(folder)]) == 1
    out, err = capsys.readouterr()
    assert (out, len(err.splitlines()), store.puts) == ("", 1, [])


def test_main_requires_a_saved_folder(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["fetch", "qcmr"])
    assert raised.value.code != 0
    assert "--saved" in capsys.readouterr().err
