import shutil
from collections.abc import Sequence
from datetime import date
from hashlib import sha256
from io import BytesIO
from math import ceil, floor
from pathlib import Path

import pytest
from packages.datadesk.tests.shell.fakes import DictCache, DictStore
from packages.datadesk.tests.shell.pdfs import drawn_pdf
from PIL import Image, ImageChops

from checkedtables.lines import Line
from checkedtables.refs import Box, Sha256
from checkedtables.testing import page_from_text
from checkedtables.words import Document
from datadesk.core.domain import ArchiveIndex, DocumentVersion, EditionKey, Period
from datadesk.core.fetch import INDEX_PATH, pdf_key
from datadesk.core.index import render_index
from datadesk.shell import cli
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.cli import CropsStopped, crops_command, main
from datadesk.shell.gather import CATALOG_PATH
from datadesk.shell.report import (
    ROW_PAD,
    CropRow,
    NoLine,
    RowEnd,
    TwoLines,
    read_crop_rows,
    row_band,
    row_line,
)

REPO = Path(__file__).parents[4]
DPI = 200
SCALE = DPI / 72
EDITION = EditionKey("qcmr", Period(date(2022, 7, 1), date(2022, 9, 30)))
ROWS = ("Auditing 1 2 3", "Mural Arts Program 8 0 8", "Mural Arts Fund 4 5 6")
HEADER = "edition\tsha256\tpage\trow\tpage_label\tcrop_label\tvalues\tread_by\n"
ENVIRON = {
    "DATADESK_R2_ENDPOINT_URL": "http://store.invalid:9000",
    "DATADESK_R2_ACCESS_KEY_ID": "access-key-PLANTED",
    "DATADESK_R2_SECRET_ACCESS_KEY": "secret-key-PLANTED",
    "DATADESK_R2_ARCHIVE_BUCKET": "archive",
}


def upright(rows: Sequence[str]) -> str:
    return " ".join(
        f"BT /F1 7.44 Tf 72 {692 - 9.6 * number:.2f} Td ({text}) Tj ET"
        for number, text in enumerate(rows)
    )


def turned(rows: Sequence[str]) -> str:
    return " ".join(
        f"BT /F1 7.44 Tf 0 1 -1 0 {100 + 9.6 * number:.2f} 72 Tm ({text}) Tj ET"
        for number, text in enumerate(rows)
    )


PDF = drawn_pdf(upright(ROWS), turned(ROWS), entries={2: "/Rotate 90"})
SHA = Sha256(sha256(PDF).hexdigest())
UNINDEXED_SHA = Sha256(sha256(b"unindexed").hexdigest())
SIZES = {1: (1700, 2200), 2: (2200, 1700)}


class ReadingStore(DictStore):
    def __init__(self) -> None:
        super().__init__({pdf_key(SHA): PDF})
        self.gets: list[str] = []

    def get(self, key: str) -> bytes:
        self.gets.append(key)
        return super().get(key)


class KeepingReader:
    def __init__(self) -> None:
        self.inner = PdfPlumberReader()
        self.calls: list[str] = []

    def page1_text(self, pdf: bytes) -> str:
        return self.inner.page1_text(pdf)

    def words(self, pdf: bytes, sha256: Sha256, pages: Sequence[int]) -> Document:
        self.calls.append(f"words {list(pages)}")
        return self.inner.words(pdf, sha256, pages)

    def render(self, pdf: bytes, page: int, dpi: int) -> bytes:
        self.calls.append(f"render {page} at {dpi}")
        return self.inner.render(pdf, page, dpi)

    def tool(self) -> str:
        return self.inner.tool()


def checkout(root: Path) -> Path:
    for path in (CATALOG_PATH, INDEX_PATH):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / CATALOG_PATH, root / CATALOG_PATH)
    version = DocumentVersion(
        SHA,
        EDITION,
        "20221116102946",
        ("https://www.phila.gov/media/20221116102946/report.pdf",),
        "title",
        EDITION.period,
        None,
    )
    (root / INDEX_PATH).write_text(render_index(ArchiveIndex((version,))), encoding="utf-8")
    return root


def row(
    page: int,
    end: str,
    label: str = "",
    reading: tuple[str, str] = ("", ""),
    edition: str = "qcmr:2022-09-30:none",
    sha: str = SHA,
) -> tuple[str, ...]:
    return (edition, sha, str(page), end, label, *reading, "a reader" if any(reading) else "")


def tsv_file(folder: Path, *rows: tuple[str, ...]) -> Path:
    path = folder / "crops.tsv"
    path.write_text(HEADER + "".join("\t".join(fields) + "\n" for fields in rows), encoding="utf-8")
    return path


def run(tmp_path: Path, *rows: tuple[str, ...]) -> tuple[Path, ...]:
    root = checkout(tmp_path / "checkout")
    tsv = tsv_file(tmp_path, *rows)
    return crops_command(
        ReadingStore(), PdfPlumberReader(), DictCache(), root, tsv=tsv, folder=tmp_path / "crops"
    )


def gray(path: Path) -> Image.Image:
    return Image.open(path).convert("L")


def ink(image: Image.Image, left: float, top: float, right: float, bottom: float) -> int:
    darkest, _ = image.crop((floor(left), floor(top), ceil(right), ceil(bottom))).getextrema()
    assert isinstance(darkest, int)
    return darkest


def files(folder: Path) -> list[str]:
    return sorted(str(path.relative_to(folder)) for path in folder.rglob("*") if path.is_file())


@pytest.mark.parametrize("page", [1, 2], ids=["upright", "turned"])
def test_each_page_is_written_at_200_dpi_whether_or_not_a_row_has_a_label(
    page: int, tmp_path: Path
) -> None:
    written = run(tmp_path, row(page, "first"), row(page, "last"))
    image = Image.open(tmp_path / "crops" / "pages" / f"qcmr_2022_09_30_p{page}.png")
    assert (image.format, image.size) == ("PNG", SIZES[page])
    assert written == (tmp_path / "crops" / "pages" / f"qcmr_2022_09_30_p{page}.png",)
    assert files(tmp_path / "crops") == [f"pages/qcmr_2022_09_30_p{page}.png"]


def test_the_pages_of_a_sha_are_read_once_through_the_word_cache(tmp_path: Path) -> None:
    root = checkout(tmp_path / "checkout")
    tsv = tsv_file(tmp_path, row(2, "first"), row(1, "last"), row(1, "first"))
    reader, cache = KeepingReader(), DictCache()
    crops_command(ReadingStore(), reader, cache, root, tsv=tsv, folder=tmp_path / "one")
    crops_command(ReadingStore(), reader, cache, root, tsv=tsv, folder=tmp_path / "two")
    assert reader.calls == [
        "words [1, 2]",
        "render 1 at 200",
        "render 2 at 200",
        "render 1 at 200",
        "render 2 at 200",
    ]
    assert files(tmp_path / "one") == files(tmp_path / "two")


@pytest.mark.parametrize("page", [1, 2], ids=["upright", "turned"])
def test_a_labelled_row_gets_a_band_across_the_page_with_ink_where_its_words_are(
    page: int, tmp_path: Path
) -> None:
    written = run(tmp_path, row(page, "first", "Auditing"), row(page, "last", "Mural Arts Program"))
    rows = tmp_path / "crops" / "rows"
    assert written[1:] == (
        rows / f"qcmr_2022_09_30_p{page}_first.png",
        rows / f"qcmr_2022_09_30_p{page}_last.png",
    )
    line = row_line(PdfPlumberReader().words(PDF, SHA, (page,)).page(page), "Mural Arts Program")
    assert isinstance(line, Line)
    band = gray(rows / f"qcmr_2022_09_30_p{page}_last.png")
    width, height = band.size
    assert width == SIZES[page][0]
    assert height >= (line.box.bottom - line.box.top + 2 * ROW_PAD) * SCALE
    assert height < (line.box.bottom - line.box.top + 2 * ROW_PAD) * SCALE + 2
    for word in line.words:
        assert ink(band, word.box.x0 * SCALE, 0, word.box.x1 * SCALE, height) < 128
    assert ink(band, 0, 0, width, 1) == 255
    assert ink(band, 0, height - 1, width, height) == 255
    assert ink(band, line.box.x1 * SCALE + 2, 0, width, height) == 255


@pytest.mark.parametrize("page", [1, 2], ids=["upright", "turned"])
def test_a_band_of_an_empty_stretch_holds_no_ink(page: int) -> None:
    png = PdfPlumberReader().render(PDF, page, DPI)
    band = Image.open(BytesIO(row_band(png, Line(page, (), Box(72, 300, 400, 307.44)), DPI)))
    assert band.width == SIZES[page][0]
    assert 0 <= band.height - (7.44 + 2 * ROW_PAD) * SCALE < 2
    assert band.convert("L").getextrema() == (255, 255)


@pytest.mark.parametrize("page", [1, 2], ids=["upright", "turned"])
def test_a_band_at_the_edge_of_the_page_stays_inside_the_image(page: int) -> None:
    png = PdfPlumberReader().render(PDF, page, DPI)
    bottom = SIZES[page][1] / SCALE
    for box in (Box(72, 0, 400, 7.44), Box(72, bottom - 7.44, 400, bottom)):
        band = Image.open(BytesIO(row_band(png, Line(page, (), box), DPI)))
        assert band.width == SIZES[page][0]
        assert band.height < (7.44 + ROW_PAD) * SCALE + 2
        assert band.convert("L").getextrema() == (255, 255)


@pytest.mark.parametrize(
    ("label", "found"),
    [
        pytest.param("Streets", "no line", id="no_line"),
        pytest.param("Mural Arts", "2 lines", id="two_lines"),
    ],
)
def test_a_label_that_begins_no_line_or_two_lines_stops_before_any_row_file(
    label: str, found: str, tmp_path: Path
) -> None:
    reading = ("Auditing", "1 2 3")
    with pytest.raises(CropsStopped) as stopped:
        run(tmp_path, row(1, "first", "Auditing", reading), row(1, "last", label, reading))
    message = str(stopped.value)
    assert f"qcmr:2022-09-30:none page 1 last {label!r}: {found}" in message
    assert "'Auditing'" not in message
    assert files(tmp_path / "crops") == ["pages/qcmr_2022_09_30_p1.png"]


def test_every_row_whose_label_finds_no_one_line_is_named(tmp_path: Path) -> None:
    with pytest.raises(CropsStopped) as stopped:
        run(tmp_path, row(1, "first", "Streets"), row(2, "last", "Mural Arts"))
    message = str(stopped.value)
    assert "qcmr:2022-09-30:none page 1 first 'Streets': no line" in message
    assert "qcmr:2022-09-30:none page 2 last 'Mural Arts': 2 lines" in message


def test_the_sheet_waits_for_every_row_to_have_a_crop_label_and_values(tmp_path: Path) -> None:
    typed = row(1, "first", "Auditing", ("Auditing", "1 2 3"))
    untyped = row(2, "last", "Mural Arts Program", ("Mural Arts Program", ""))
    written = run(tmp_path, typed, untyped)
    assert [path.name for path in written] == [
        "qcmr_2022_09_30_p1.png",
        "qcmr_2022_09_30_p2.png",
        "qcmr_2022_09_30_p1_first.png",
        "qcmr_2022_09_30_p2_last.png",
    ]
    assert not (tmp_path / "crops" / "sheet.png").exists()


def test_the_sheet_stacks_every_crop_with_its_reading_printed_under_it(tmp_path: Path) -> None:
    sheets = []
    for values in ("1 2 3", "1 2 4"):
        (folder := tmp_path / values.replace(" ", "")).mkdir()
        written = run(
            folder,
            row(1, "first", "Auditing", ("Auditing", values)),
            row(2, "first", "Auditing", ("Auditing", "1 2 3")),
            row(2, "last", "Mural Arts Program", ("Mural Arts Program", "8 0 8")),
        )
        assert written[-1] == folder / "crops" / "sheet.png"
        sheets.append(Image.open(written[-1]))
    crops = [Image.open(path) for path in written[2:-1]]
    first, second = sheets
    assert first.format == "PNG"
    assert first.width == max(crop.width for crop in crops) == 2200
    assert first.height > sum(crop.height for crop in crops)
    changed = ImageChops.difference(first.convert("RGB"), second.convert("RGB")).getbbox()
    assert changed is not None
    _, top, _, bottom = changed
    assert crops[0].height <= top
    assert bottom <= first.height - crops[1].height - crops[2].height


@pytest.mark.parametrize(
    "rows",
    [
        pytest.param(None, id="no_file"),
        pytest.param("edition\tsha256\tpage\trow\n", id="a_bad_header"),
        pytest.param(HEADER + "\t".join(row(1, "first"))[:-1] + "\n", id="a_short_row"),
        pytest.param(row(1, "first", sha=UNINDEXED_SHA), id="a_sha_the_index_lacks"),
        pytest.param(row(1, "first", edition="qcmr:2022-12-31:none"), id="another_edition"),
    ],
)
def test_a_crop_file_the_command_cannot_use_stops_it_before_any_pdf_is_read(
    rows: str | tuple[str, ...] | None, tmp_path: Path
) -> None:
    root = checkout(tmp_path / "checkout")
    tsv = tmp_path / "crops.tsv"
    match rows:
        case None:
            pass
        case str():
            tsv.write_text(rows, encoding="utf-8")
        case tuple():
            tsv_file(tmp_path, row(1, "first"), rows)
    store, reader = ReadingStore(), KeepingReader()
    with pytest.raises(CropsStopped):
        crops_command(store, reader, DictCache(), root, tsv=tsv, folder=tmp_path / "crops")
    assert (store.gets, reader.calls) == ([], [])
    assert not (tmp_path / "crops").exists()


def test_read_crop_rows_reads_each_field() -> None:
    text = HEADER + "\t".join(row(35, "last", "Mural Arts", ("Mural Arts", "8 0 8"))) + "\n"
    assert read_crop_rows(text) == (
        CropRow(
            "qcmr:2022-09-30:none",
            SHA,
            35,
            RowEnd.LAST,
            "Mural Arts",
            "Mural Arts",
            "8 0 8",
            "a reader",
        ),
    )
    assert read_crop_rows(HEADER) == ()


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param("", "line 1", id="no_header"),
        pytest.param(HEADER.replace("values", "digits"), "line 1", id="another_header"),
        pytest.param(HEADER[:-1], "line 1", id="no_last_newline"),
        pytest.param(HEADER + "\t".join(row(35, "first")) + "\textra\n", "line 2", id="nine"),
        pytest.param(
            HEADER + "\t".join(row(35, "first", sha=SHA.upper())) + "\n", "line 2", id="sha"
        ),
        pytest.param(HEADER + "\t".join(row(0, "first")) + "\n", "line 2", id="page_0"),
        pytest.param(
            HEADER + "\t".join(row(35, "first")).replace("\t35\t", "\t+3\t") + "\n",
            "line 2",
            id="page_sign",
        ),
        pytest.param(HEADER + "\t".join(row(35, "middle")) + "\n", "line 2", id="middle"),
        pytest.param(
            HEADER + "\t".join(row(35, "first")) + "\n" + "\t".join(row(35, "First")) + "\n",
            "line 3",
            id="third_line",
        ),
    ],
)
def test_read_crop_rows_refuses_a_line_it_cannot_read_and_names_it(text: str, line: str) -> None:
    with pytest.raises(ValueError, match=f"{line}\\b"):
        read_crop_rows(text)


ROW_PAGE = page_from_text(
    "Auditing 1 2 3\nMural Arts Program 8 0 8\nMural Arts Fund 4 5 6\nTotal Arts 9", SHA, 1
)


def test_row_line_gives_the_one_line_that_begins_with_the_label() -> None:
    found = row_line(ROW_PAGE, "Mural  Arts Program")
    assert isinstance(found, Line)
    assert [word.text for word in found.words] == ["Mural", "Arts", "Program", "8", "0", "8"]


@pytest.mark.parametrize("label", ["Streets", "Arts", "Auditing 1 2 3 4", "auditing", "", " "])
def test_row_line_gives_no_line_for_a_label_that_begins_none(label: str) -> None:
    assert row_line(ROW_PAGE, label) == NoLine(label)


def test_row_line_gives_both_lines_when_two_begin_with_the_label() -> None:
    found = row_line(ROW_PAGE, "Mural Arts")
    assert isinstance(found, TwoLines)
    assert found.label == "Mural Arts"
    assert [line.text for line in found.lines] == [
        "Mural Arts Program 8 0 8",
        "Mural Arts Fund 4 5 6",
    ]


def test_main_writes_the_files_and_prints_each_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout")
    tsv_file(root, row(1, "first", "Auditing"))
    monkeypatch.setattr(cli, "s3_store", lambda settings: ReadingStore())
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["crops", "crops.tsv", ".cache/crops"]) == 0
    out, err = capsys.readouterr()
    assert out == (
        "wrote .cache/crops/pages/qcmr_2022_09_30_p1.png\n"
        "wrote .cache/crops/rows/qcmr_2022_09_30_p1_first.png\n"
    )
    assert err == ""
    assert len(list((root / ".cache" / "words").iterdir())) == 1


def test_main_prints_neither_r2_key_on_the_line_a_stop_prints(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = checkout(tmp_path / "checkout")
    keys = (ENVIRON["DATADESK_R2_ACCESS_KEY_ID"], ENVIRON["DATADESK_R2_SECRET_ACCESS_KEY"])
    monkeypatch.setattr(cli, "s3_store", lambda settings: ReadingStore())
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    assert main(["crops", f"{keys[0]}-{keys[1]}.tsv", ".cache/crops"]) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert len(err.splitlines()) == 1
    assert err.startswith("datadesk: ")
    assert "$DATADESK_R2_ACCESS_KEY_ID-$DATADESK_R2_SECRET_ACCESS_KEY.tsv" in err
    assert not [key for key in keys if key in out + err]


def test_main_prints_a_traceback_when_the_working_directory_is_gone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name, value in ENVIRON.items():
        monkeypatch.setenv(name, value)
    gone = tmp_path / "gone"
    gone.mkdir()
    monkeypatch.chdir(gone)
    gone.rmdir()
    assert main(["crops", "crops.tsv", ".cache/crops"]) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert "Traceback" in err
    assert "FileNotFoundError" in err
