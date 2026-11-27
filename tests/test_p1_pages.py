import re
from collections.abc import Sequence
from importlib import import_module

from packages.checkedtables.tests.step_2_rule import step_2_rule_lines
from packages.datadesk.tests.fixtures.p1 import RUNS

from checkedtables.lines import Line, group_lines
from checkedtables.refs import WordRef
from checkedtables.words import Page, Word
from datadesk.shell.cli import FIXTURE_FOLDER

MARK = re.compile(r"\(\d\)")
NUMBER = re.compile(r"\(?\d[\d,]*\)?")
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
