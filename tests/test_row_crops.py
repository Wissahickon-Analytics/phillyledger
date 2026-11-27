from collections import Counter
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import assert_never

import pytest

from checkedtables.lines import Line
from datadesk.shell.cli import FIXTURE_FOLDER
from datadesk.shell.report import CropRow, NoLine, RowEnd, TwoLines, read_crop_rows, row_line

REPO = Path(__file__).parents[1]
CROPS = REPO / "docs" / "evidence" / "crops" / "qcmr_positions.tsv"
ROWS = read_crop_rows(CROPS.read_text(encoding="utf-8"))
GRID_PAGES = {
    "qcmr:2022-09-30:none": (35, 36),
    "qcmr:2022-12-31:none": (35, 36),
    "qcmr:2023-03-31:none": (34, 35),
    "qcmr:2023-06-30:none": (32, 33),
    "qcmr:2023-09-30:none": (33, 34),
    "qcmr:2023-12-31:none": (32, 33),
    "qcmr:2024-03-31:none": (32, 33),
    "qcmr:2024-06-30:none": (32, 33),
    "qcmr:2024-09-30:none": (33, 34),
    "qcmr:2024-12-31:none": (34, 35),
}


def name(row: CropRow) -> str:
    return f"{row.edition}-p{row.page}-{row.row}"


def fixture(edition: str, page: int) -> ModuleType:
    series, end, stage = edition.split(":")
    stem = "_".join([series, end.replace("-", "_"), *([] if stage == "none" else [stage])])
    return import_module(f"{FIXTURE_FOLDER.replace('/', '.')}.{stem}_p{page}")


@pytest.mark.parametrize("row", ROWS, ids=name)
def test_each_row_read_from_a_crop_matches_the_extracted_words(row: CropRow) -> None:
    module = fixture(row.edition, row.page)
    assert (module.SHA, module.PAGE.number) == (row.sha256, row.page), name(row)
    assert row.page_label, f"{name(row)} has no page_label typed from the page image"
    found = row_line(module.PAGE, row.page_label)
    match found:
        case Line():
            pass
        case NoLine():
            pytest.fail(f"{name(row)}: no line begins with {row.page_label!r}")
        case TwoLines():
            pytest.fail(f"{name(row)}: {len(found.lines)} lines begin with {row.page_label!r}")
        case _:
            assert_never(found)
    extracted = [word.text for word in found.words]
    read = [*row.crop_label.split(), *row.values.split()]
    assert extracted == read, f"{name(row)}: the words are {extracted}, the crop reads {read}"
    assert row.crop_label == row.page_label, name(row)


def test_each_page_has_one_first_and_one_last_row() -> None:
    counts = Counter((row.edition, row.page, row.row) for row in ROWS)
    assert dict(counts) == {
        (edition, page, end): 1
        for edition, pages in GRID_PAGES.items()
        for page in pages
        for end in RowEnd
    }
    labels = {(row.edition, row.page, row.row): row.page_label for row in ROWS}
    for edition, pages in GRID_PAGES.items():
        for page in pages:
            module = fixture(edition, page)
            first = row_line(module.PAGE, labels[edition, page, RowEnd.FIRST])
            last = row_line(module.PAGE, labels[edition, page, RowEnd.LAST])
            assert isinstance(first, Line), f"{edition} page {page} first"
            assert isinstance(last, Line), f"{edition} page {page} last"
            assert first.box.bottom < last.box.top, (
                f"{edition} page {page}: the first row {first.text!r} is not above "
                f"the last row {last.text!r}"
            )
