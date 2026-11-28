import re
from collections.abc import Sequence
from datetime import date
from importlib import import_module
from statistics import median

from packages.checkedtables.tests.step_2_rule import step_2_rule_lines
from packages.datadesk.tests.fixtures.p1 import RUNS, P1Run

from checkedtables.columns import lanes_from_rules
from checkedtables.lines import Line, PageLines, group_lines, page_lines
from checkedtables.pages import BodyRule
from checkedtables.pipeline import CutPages, Layout, cut_pages
from checkedtables.refs import WordRef
from checkedtables.words import Page, Word
from datadesk.core.tables.qcmr_positions import COLUMNS, ERAS, TABLE
from datadesk.shell.cli import FIXTURE_FOLDER

MARK = re.compile(r"\(\d\)")
NUMBER = re.compile(r"\(?\d[\d,]*\)?")
GROUPS = ("YEAR END ACTUAL", "ADOPTED BUDGET", "MONTH END ACTUAL", "(OVER)")
MOVED: dict[str, tuple[tuple[int, str, str], ...]] = {
    "qcmr_2021_09_30_p35": ((521, "2", "2 5 First Judicial District"),),
    "qcmr_2021_09_30_p36": ((393, "2", "2 6 Records"),),
    "qcmr_2021_12_31_p34": ((521, "2", "2 6 Fleet Services"),),
    "qcmr_2021_12_31_p35": ((393, "2", "2 7 Register of Wills"),),
    "qcmr_2022_03_31_p35": ((494, "2", "2 4 Fleet Services"),),
    "qcmr_2022_03_31_p36": ((393, "2", "2 5 Records"),),
    "qcmr_2022_06_30_p34": (
        (278, "2", "2 2 Note for FY22 Q4:"),
        (279, "2", "2 2 Note for FY22 Q4:"),
    ),
    "qcmr_2022_06_30_p35": ((494, "2", "2 3 Fleet Services"),),
    "qcmr_2022_06_30_p36": ((393, "2", "2 4 Records"),),
    "qcmr_2022_09_30_p34": (
        (290, "2", "2 4 Note for FY23 Q1:"),
        (291, "4", "2 4 Note for FY23 Q1:"),
    ),
    "qcmr_2022_09_30_p35": ((521, "2", "2 5 First Judicial District"),),
    "qcmr_2022_09_30_p36": ((393, "2", "2 6 Records"),),
    "qcmr_2022_12_31_p34": (
        (280, "2", "2 4 Note for FY23 Q2:"),
        (281, "4", "2 4 Note for FY23 Q2:"),
    ),
    "qcmr_2022_12_31_p35": ((521, "2", "2 5 First Judicial District"),),
    "qcmr_2022_12_31_p36": ((393, "2", "2 6 Records"),),
    "qcmr_2023_03_31_p33": (
        (266, "2", "2 4 Note for FY23 Q3:"),
        (267, "4", "2 4 Note for FY23 Q3:"),
    ),
    "qcmr_2023_03_31_p34": ((521, "2", "2 5 First Judicial District"),),
    "qcmr_2023_03_31_p35": ((393, "2", "2 6 Records"),),
    "qcmr_2023_09_30_p33": (
        (65, "(1)", "Aviation (1)"),
        (313, "(2)", "Human Services (2)"),
        (459, "(1)", "(1) In FY23 and prior,"),
        (477, "(2)", "(2) Positions have been transferred"),
    ),
    "qcmr_2023_12_31_p32": (
        (65, "(1)", "Aviation (1)"),
        (313, "(2)", "Human Services (2)"),
        (459, "(1)", "(1) In FY23 and prior,"),
        (477, "(2)", "(2) Positions have been transferred"),
    ),
    "qcmr_2024_03_31_p32": (
        (65, "(1)", "Aviation (1)"),
        (313, "(2)", "Human Services (2)"),
        (459, "(1)", "(1) In FY23 and prior,"),
        (477, "(2)", "(2) Positions have been transferred"),
    ),
    "qcmr_2024_06_30_p32": (
        (65, "(1)", "Aviation (1)"),
        (325, "(2)", "Human Services (2)"),
        (486, "(1)", "(1) In FY23 and prior,"),
        (504, "(2)", "(2) Positions have been transferred"),
    ),
    "qcmr_2024_09_30_p33": (
        (312, "(1)", "Human Services (1)"),
        (473, "(1)", "(1) Positions have been transferred"),
    ),
    "qcmr_2024_12_31_p34": (
        (312, "(1)", "Human Services (1)"),
        (473, "(1)", "(1) Positions have been transferred"),
    ),
    "qcmr_2025_03_31_p33": (
        (312, "(1)", "Human Services (1)"),
        (470, "(1)", "(1) Positions have been transferred"),
    ),
    "qcmr_2025_06_30_p31": (
        (312, "(1)", "Human Services (1)"),
        (470, "(1)", "(1) Positions have been transferred"),
    ),
    "qcmr_2025_09_30_p35": (
        (338, "(1)", "Human Services (1)"),
        (511, "(1)", "(1) Positions have been transferred"),
    ),
    "qcmr_2025_12_31_p36": (
        (338, "(1)", "Human Services (1)"),
        (511, "(1)", "(1) Positions have been transferred"),
    ),
    "qcmr_2026_03_31_p36": (
        (338, "(1)", "Human Services (1)"),
        (511, "(1)", "(1) Positions have been transferred"),
    ),
    "qcmr_2026_06_30_p33": (
        (338, "(1)", "Human Services (1)"),
        (511, "(1)", "(1) Positions have been transferred"),
    ),
}


def stem(edition: str, page: int) -> str:
    return f"qcmr_{edition.split(':')[1].replace('-', '_')}_p{page}"


def fixture_page(name: str) -> Page:
    return import_module(f"{FIXTURE_FOLDER.replace('/', '.')}.{name}").PAGE


def grid_stems(first: str, last: str) -> list[str]:
    return [
        stem(run.edition, page)
        for run in RUNS
        if first <= run.edition.split(":")[1] <= last
        for page in run.grid
    ]


def all_stems() -> list[str]:
    commentary = [stem(run.edition, run.commentary) for run in RUNS if run.commentary is not None]
    return commentary + grid_stems("2021-09-30", "2026-06-30")


def line_of(lines: Sequence[Line], word: Word) -> Line:
    (found,) = [line for line in lines if word in line.words]
    return found


def refs_without(lines: Sequence[Sequence[Word]], moved: set[WordRef]) -> set[frozenset[WordRef]]:
    return {frozenset(word.ref for word in line) - moved for line in lines} - {frozenset()}


def test_every_raised_mark_joins_its_line_on_the_grid_pages() -> None:
    marks: dict[tuple[str, int], tuple[Line, int]] = {}
    for name in grid_stems("2023-09-30", "2026-06-30"):
        page = fixture_page(name)
        for line in group_lines(page):
            for position, word in enumerate(line.words[:-1]):
                if MARK.fullmatch(word.text):
                    marks[(name, page.words.index(word))] = (line, position)
    pinned = [
        (name, index)
        for name, pins in MOVED.items()
        for index, text, _ in pins
        if MARK.fullmatch(text)
    ]
    assert sorted(marks) == sorted(pinned)
    assert len(marks) == 32
    assert len({name.rsplit("_", 1)[0] for name, _ in marks}) == 12
    assert marks[("qcmr_2026_06_30_p33", 338)][0].text.startswith("Human Services (1) ")
    for (name, index), (line, position) in marks.items():
        after = [word.text for word in line.words[position + 1 :]]
        if position == 0:
            assert not NUMBER.fullmatch(after[0]), f"{name} word {index} opens no footnote"
        else:
            assert not NUMBER.fullmatch(line.words[position - 1].text), f"{name} word {index}"
            assert len(after) == 10, f"{name} word {index} is not after its row's label"
            assert all(NUMBER.fullmatch(text) for text in after), f"{name} word {index}"
    for name in grid_stems("2021-09-30", "2026-06-30"):
        lone = [line.text for line in group_lines(fixture_page(name)) if MARK.fullmatch(line.text)]
        assert lone == [], name


def test_both_margin_digits_join_one_row_on_the_grid_pages_through_2023_03_31() -> None:
    names = grid_stems("2021-09-30", "2023-03-31")
    assert len(names) == 14
    for name in names:
        page = fixture_page(name)
        left = min(rule.box.x0 for rule in page.rules)
        margin = [word for word in page.words if word.box.x1 < left]
        assert [len(word.text) for word in margin] == [1, 1], name
        assert all(word.text.isdigit() for word in margin), name
        line = line_of(group_lines(page), margin[0])
        texts = [word.text for word in line.words]
        assert set(line.words[:2]) == set(margin), name
        assert texts[2:-10], f"{name} has no label after its margin digits"
        assert not any(NUMBER.fullmatch(text) for text in texts[2:-10]), name
        assert all(NUMBER.fullmatch(text) for text in texts[-10:]), name


def test_only_the_54_pinned_words_leave_the_lines_of_the_step_2_rule() -> None:
    names = all_stems()
    assert len(names) == 56
    assert set(MOVED) <= set(names)
    assert sum(len(pins) for pins in MOVED.values()) == 54
    for name in names:
        page = fixture_page(name)
        pins = MOVED.get(name, ())
        moved = {page.words[index].ref for index, _, _ in pins}
        before = step_2_rule_lines(page)
        after = group_lines(page)
        assert refs_without([line.words for line in after], moved) == refs_without(before, moved), (
            f"{name}: a word that is not pinned left the line the step 2 rule gives it"
        )
        for index, text, line_start in pins:
            word = page.words[index]
            assert word.text == text, f"{name} word {index}"
            line = line_of(after, word)
            assert f"{line.text} ".startswith(f"{line_start} "), f"{name} word {index}"
            (old,) = [found for found in before if word in found]
            stayed = {other.ref for other in old} - moved
            joined = {other.ref for other in line.words} - moved
            assert joined, f"{name} word {index} joined no line of the step 2 rule"
            assert not joined & stayed, (
                f"{name} word {index} kept the line the step 2 rule gives it"
            )


def is_row(line: Line) -> bool:
    return len(line.words) > 10 and all(NUMBER.fullmatch(word.text) for word in line.words[-10:])


GRID_BODY = BodyRule(
    start=is_row,
    stop=lambda line: line.text.startswith("TOTAL ALL FUNDS"),
    drop=(r"^\(\d+\)\s", r"^NOTE:"),
    prefix=r"\d{1,2}",
)


def grid_of(run: P1Run) -> tuple[tuple[PageLines, ...], CutPages]:
    pages = tuple(page_lines(fixture_page(stem(run.edition, number))) for number in run.grid)
    on = date.fromisoformat(run.edition.split(":")[1])
    cut = cut_pages(Layout(TABLE, ERAS, GRID_BODY), pages, on)
    assert isinstance(cut, CutPages), f"{run.edition}: {cut}"
    return pages, cut


def band_text(lines: Sequence[Line], x0: float, x1: float) -> str:
    centered = (w for line in lines for w in line.words if x0 <= (w.box.x0 + w.box.x1) / 2 < x1)
    return " ".join(word.text for word in centered)


def test_the_ten_columns_bind_left_to_right_under_the_group_each_band_prints() -> None:
    names = [column.name for column in COLUMNS]
    for run in RUNS:
        pages, cut = grid_of(run)
        assert cut.findings == (), run.edition
        for page, cut_page in zip(pages, cut.pages, strict=True):
            columns = cut_page.binding.columns
            lanes = [lane for _, lane in columns if lane is not None]
            assert [spec.name for spec, _ in columns] == names, page.number
            assert len(lanes) == 10, f"{run.edition} page {page.number}"
            assert [lane.x1 for lane in lanes] == sorted(lane.x1 for lane in lanes)
            assert len(cut_page.header) == 9, f"{run.edition} page {page.number}"
            last = cut_page.header[-1]
            assert last.text == "General Other Total " * 3 + "UNDER BUDGET"
            bands = lanes_from_rules(page.rules, last.box)
            assert len(bands) == 5, f"{run.edition} page {page.number}"
            holders = [
                next(index for index, band in enumerate(bands) if band.x0 < lane.x1 <= band.x1)
                for lane in lanes
            ]
            assert holders == [1, 1, 1, 2, 2, 2, 3, 3, 3, 4], f"{run.edition} page {page.number}"
            for band, group in zip(bands[1:], GROUPS, strict=True):
                assert group in band_text(cut_page.header[5:], band.x0, band.x1), (
                    f"{run.edition} page {page.number} band {band}"
                )
            assert cut_page.binding.label_right == lanes[0].x0 > bands[0].x0


def test_each_body_row_cuts_to_a_label_and_ten_cells_of_one_word() -> None:
    for run in RUNS:
        _, cut = grid_of(run)
        assert len(cut.raws) == run.rows, run.edition
        for raw in cut.raws:
            where = f"{run.edition} page {raw.page} {[word.text for word in raw.label_words]}"
            assert raw.label_words, where
            assert [len(words) for _, words in raw.cells] == [1] * 10, where
            assert raw.stray == (), where
            numbers = [word.text for word in raw.label_words if NUMBER.fullmatch(word.text)]
            assert all(MARK.fullmatch(text) for text in numbers), where
            words = [*raw.label_words, *(word for _, cell in raw.cells for word in cell)]
            height = median(word.box.bottom - word.box.top for word in words)
            assert raw.cells[0][1][0].box.x0 - raw.label_words[-1].box.x1 > height, where
