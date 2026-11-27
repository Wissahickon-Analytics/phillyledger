import shutil
from collections.abc import Sequence
from datetime import date
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from packages.datadesk.tests.shell.fakes import DictCache, DictStore
from packages.datadesk.tests.shell.pdfs import text_pdf

from checkedtables.refs import Sha256
from checkedtables.words import Document
from datadesk.core.domain import ArchiveIndex, DocumentVersion, EditionKey, Period
from datadesk.core.fetch import INDEX_PATH, pdf_key
from datadesk.core.index import render_index
from datadesk.core.parse_plan import word_key
from datadesk.shell import cli
from datadesk.shell.adapters.cache_dir import DirCache
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.cli import FIXTURE_FOLDER, FixtureStopped, fixture_command, main
from datadesk.shell.gather import CATALOG_PATH
from datadesk.shell.ports import LocalCache, PdfReader

REPO = Path(__file__).parents[4]
EDITION = EditionKey("qcmr", Period(date(2022, 7, 1), date(2022, 9, 30)))
PDF = text_pdf(*(f"PAGE {number}" for number in range(1, 37)))
SHA = Sha256(sha256(PDF).hexdigest())
NEWER_PDF = text_pdf("NEWER")
NEWER_SHA = Sha256(sha256(NEWER_PDF).hexdigest())
UNINDEXED_SHA = Sha256(sha256(b"unindexed").hexdigest())
ENVIRON = {
    "DATADESK_R2_ENDPOINT_URL": "http://store.invalid:9000",
    "DATADESK_R2_ACCESS_KEY_ID": "access-key-PLANTED",
    "DATADESK_R2_SECRET_ACCESS_KEY": "secret-key-PLANTED",
    "DATADESK_R2_ARCHIVE_BUCKET": "archive",
}


class KeepingReader:
    def __init__(self, inner: PdfReader) -> None:
        self.inner = inner
        self.kept: list[Document] = []

    def page1_text(self, pdf: bytes) -> str:
        return self.inner.page1_text(pdf)

    def words(self, pdf: bytes, sha256: Sha256, pages: Sequence[int]) -> Document:
        document = self.inner.words(pdf, sha256, pages)
        self.kept.append(document)
        return document

    def render(self, pdf: bytes, page: int, dpi: int) -> bytes:
        return self.inner.render(pdf, page, dpi)

    def tool(self) -> str:
        return self.inner.tool()


def version(sha: Sha256, listed_at: str, supersedes: Sha256 | None = None) -> DocumentVersion:
    url = f"https://www.phila.gov/media/{listed_at}/report.pdf"
    return DocumentVersion(sha, EDITION, listed_at, (url,), "title", EDITION.period, supersedes)


def checkout(root: Path, *versions: DocumentVersion) -> Path:
    for path in (CATALOG_PATH, INDEX_PATH):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / CATALOG_PATH, root / CATALOG_PATH)
    (root / INDEX_PATH).write_text(render_index(ArchiveIndex(versions)), encoding="utf-8")
    return root


def store() -> DictStore:
    return DictStore({pdf_key(SHA): PDF, pdf_key(NEWER_SHA): NEWER_PDF})


def run(root: Path, reader: PdfReader, cache: LocalCache, sha: str, pages: str) -> tuple[Path, ...]:
    return fixture_command(store(), reader, cache, root, sha=sha, pages=pages)


def fixtures(root: Path) -> dict[str, bytes]:
    folder = root / FIXTURE_FOLDER
    return {path.name: path.read_bytes() for path in folder.iterdir()} if folder.exists() else {}


def test_a_second_run_writes_the_same_bytes(tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    reader = KeepingReader(PdfPlumberReader())
    cache = DirCache(tmp_path / "words")
    first = run(root, reader, cache, SHA, "35,36")
    written = fixtures(root)
    assert len(reader.kept) == 1
    for path in first:
        path.unlink()
    assert fixtures(root) == {}
    second = run(root, reader, cache, SHA, "35,36")
    assert len(reader.kept) == 1
    assert second == first
    assert fixtures(root) == written
    assert sorted(written) == ["qcmr_2022_09_30_p35.py", "qcmr_2022_09_30_p36.py"]


def test_each_fixture_runs_to_the_page_the_reader_read(tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    reader = KeepingReader(PdfPlumberReader())
    written = run(root, reader, DictCache(), SHA, "35,36")
    (kept,) = reader.kept
    for path, page in zip(written, kept.pages, strict=True):
        namespace: dict[str, Any] = {}
        exec(path.read_text(encoding="utf-8"), namespace)
        assert namespace["SHA"] == SHA
        assert namespace["PAGE"] == page
        assert [word.text for word in page.words] == ["PAGE", str(page.number)]


def test_pages_given_out_of_order_and_twice_write_each_page_once(tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    cache = DictCache()
    written = run(root, PdfPlumberReader(), cache, SHA, "36,35,35")
    folder = root / FIXTURE_FOLDER
    assert written == (folder / "qcmr_2022_09_30_p35.py", folder / "qcmr_2022_09_30_p36.py")
    assert sorted(fixtures(root)) == ["qcmr_2022_09_30_p35.py", "qcmr_2022_09_30_p36.py"]
    assert cache.keys() == {word_key(SHA, (35, 36), PdfPlumberReader().tool())}


def test_a_second_sha_of_one_edition_does_not_overwrite_the_first_ones_fixture(
    tmp_path: Path,
) -> None:
    root = checkout(
        tmp_path / "checkout",
        version(SHA, "20221116102946"),
        version(NEWER_SHA, "20221201090000", supersedes=SHA),
    )
    run(root, PdfPlumberReader(), DictCache(), SHA, "1")
    held = fixtures(root)
    reader = KeepingReader(PdfPlumberReader())
    with pytest.raises(FixtureStopped, match=f"names the sha {SHA}"):
        run(root, reader, DictCache(), NEWER_SHA, "2,1")
    assert reader.kept == []
    assert fixtures(root) == held
    assert sorted(held) == ["qcmr_2022_09_30_p1.py"]


@pytest.mark.parametrize(
    "sha",
    [
        pytest.param(SHA.upper(), id="upper_case"),
        pytest.param(SHA[:63], id="63_characters"),
        pytest.param(f"{SHA}0", id="65_characters"),
        pytest.param(f"{SHA[:63]}g", id="not_hex"),
        pytest.param(UNINDEXED_SHA, id="not_in_the_index"),
    ],
)
def test_a_sha_that_is_not_an_indexed_sha256_stops_the_command(sha: str, tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    reader = KeepingReader(PdfPlumberReader())
    with pytest.raises(FixtureStopped):
        run(root, reader, DictCache(), sha, "35")
    assert reader.kept == []
    assert fixtures(root) == {}


@pytest.mark.parametrize("pages", ["", "35,", "35,,36", "0", "-1", "35-36", "x", "٣٥", " 35"])
def test_pages_that_are_not_page_numbers_stop_the_command(pages: str, tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    reader = KeepingReader(PdfPlumberReader())
    with pytest.raises(FixtureStopped):
        run(root, reader, DictCache(), SHA, pages)
    assert reader.kept == []
    assert fixtures(root) == {}


def test_a_checkout_the_command_cannot_read_stops_it(tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    (root / INDEX_PATH).write_text("not json\n", encoding="utf-8")
    with pytest.raises(FixtureStopped, match="index_unreadable"):
        run(root, PdfPlumberReader(), DictCache(), SHA, "35")
    assert fixtures(root) == {}


def test_main_writes_the_fixtures_from_the_working_directory_and_prints_each_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    monkeypatch.setattr(cli, "s3_store", lambda settings: store())
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["fixture", SHA, "36,35"]) == 0
    out, err = capsys.readouterr()
    assert out == (
        "wrote packages/datadesk/tests/fixtures/words/qcmr_2022_09_30_p35.py\n"
        "wrote packages/datadesk/tests/fixtures/words/qcmr_2022_09_30_p36.py\n"
    )
    assert err == ""
    assert DirCache(root / ".cache" / "words").keys() == {
        word_key(SHA, (35, 36), PdfPlumberReader().tool())
    }


def test_main_prints_one_line_when_the_command_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout", version(SHA, "20221116102946"))
    monkeypatch.setattr(cli, "s3_store", lambda settings: store())
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["fixture", UNINDEXED_SHA, "35"]) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert UNINDEXED_SHA in err
    assert len(err.splitlines()) == 1
    assert fixtures(root) == {}
