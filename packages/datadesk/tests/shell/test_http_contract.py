from collections.abc import Callable, Mapping
from pathlib import Path

import pytest
from packages.datadesk.tests.shell.fakes import FakeHttp

from datadesk.shell.adapters.http_saved import SavedFolderError, SavedHttp
from datadesk.shell.ports import Http, HttpResponse

FEED_URL = "https://api.phila.gov/phila/document-finder/v1/151831"
REPORT_URL = "https://www.phila.gov/media/20211116102946/Quarterly-City-Managers-Report-September-30-2021.pdf"
BODIES = {FEED_URL: b'[{"title": "feed"}]', REPORT_URL: b"%PDF-1.4 report\n"}

type MakeHttp = Callable[[Mapping[str, bytes], Path], Http]


def write_folder(folder: Path, rows: list[tuple[str, str]], files: Mapping[str, bytes]) -> Path:
    folder.mkdir(exist_ok=True)
    for name, body in files.items():
        (folder / name).write_bytes(body)
    lines = ["url\tfile", *(f"{url}\t{name}" for url, name in rows)]
    (folder / "responses.tsv").write_text("".join(f"{line}\n" for line in lines))
    return folder


def saved_http(bodies: Mapping[str, bytes], folder: Path) -> Http:
    names = {url: f"file-{number}.bin" for number, url in enumerate(bodies)}
    files = {names[url]: body for url, body in bodies.items()}
    return SavedHttp(write_folder(folder, list(names.items()), files))


def fake_http(bodies: Mapping[str, bytes], _folder: Path) -> Http:
    return FakeHttp(bodies)


HTTPS = [pytest.param(fake_http, id="fake"), pytest.param(saved_http, id="saved_folder")]


@pytest.mark.parametrize("make", HTTPS)
def test_a_listed_url_gives_200_and_its_bytes(make: MakeHttp, tmp_path: Path) -> None:
    http = make(BODIES, tmp_path / "saved")
    assert http.get(FEED_URL) == HttpResponse(200, BODIES[FEED_URL])
    assert http.get(REPORT_URL) == HttpResponse(200, BODIES[REPORT_URL])
    assert http.get(FEED_URL).text == '[{"title": "feed"}]'


@pytest.mark.parametrize("make", HTTPS)
def test_any_other_url_gives_404(make: MakeHttp, tmp_path: Path) -> None:
    http = make(BODIES, tmp_path / "saved")
    for url in (f"{FEED_URL}/other", REPORT_URL.replace("www.", "admin."), ""):
        assert http.get(url).status == 404


@pytest.mark.parametrize(
    ("text", "files"),
    [
        pytest.param("", {}, id="an_empty_file"),
        pytest.param("url\tbody\n", {}, id="another_header"),
        pytest.param(f"{FEED_URL}\tfeed.json\n", {"feed.json"}, id="no_header"),
        pytest.param(f"url\tfile\n{FEED_URL}\n", {}, id="a_row_with_one_field"),
        pytest.param(
            f"url\tfile\n{FEED_URL}\tfeed.json\textra\n",
            {"feed.json"},
            id="a_row_with_three_fields",
        ),
        pytest.param("url\tfile\n\tfeed.json\n", {"feed.json"}, id="a_row_with_no_url"),
        pytest.param(
            "url\tfile\nnot a URL\tfeed.json\n", {"feed.json"}, id="a_row_that_is_not_a_url"
        ),
        pytest.param(
            "url\tfile\napi.phila.gov/feed\tfeed.json\n", {"feed.json"}, id="a_url_with_no_scheme"
        ),
        pytest.param(
            "url\tfile\nhttps://www.phila.gov/a report.pdf\tfeed.json\n",
            {"feed.json"},
            id="a_url_with_a_space",
        ),
        pytest.param(f"url\tfile\n{FEED_URL}\t\n", {}, id="a_row_with_no_file"),
        pytest.param(
            f"url\tfile\n{FEED_URL}\tfeed.json\n{FEED_URL}\tother.json\n",
            {"feed.json", "other.json"},
            id="a_repeated_url",
        ),
        pytest.param(f"url\tfile\n{FEED_URL}\tfeed.json\n", set(), id="a_file_the_folder_lacks"),
        pytest.param(f"url\tfile\n{FEED_URL}\tsub\n", set(), id="a_folder_in_place_of_a_file"),
        pytest.param(
            f"url\tfile\n{FEED_URL}\t../outside.json\n", set(), id="a_file_outside_the_folder"
        ),
        pytest.param(
            f"url\tfile\n{FEED_URL}\tlink.json\n", set(), id="a_link_to_a_file_outside_the_folder"
        ),
    ],
)
def test_saved_http_refuses_a_folder_it_cannot_trust(
    text: str, files: set[str], tmp_path: Path
) -> None:
    (tmp_path / "outside.json").write_bytes(b"{}")
    folder = tmp_path / "saved"
    (folder / "sub").mkdir(parents=True)
    (folder / "link.json").symlink_to(tmp_path / "outside.json")
    for name in files:
        (folder / name).write_bytes(b"{}")
    (folder / "responses.tsv").write_text(text)
    with pytest.raises(SavedFolderError):
        SavedHttp(folder)


def test_saved_http_refuses_a_folder_with_no_responses_file(tmp_path: Path) -> None:
    with pytest.raises(SavedFolderError, match=r"responses\.tsv"):
        SavedHttp(tmp_path)
