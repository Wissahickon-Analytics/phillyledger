from checkedtables.lines import Line, PageLines, page_lines
from checkedtables.pages import BodyRule, PageRun, find_runs, header_band, only_run, slice_body
from checkedtables.refs import Sha256
from checkedtables.table import Finding, Severity
from checkedtables.testing import page_from_text

SHA = Sha256("a" * 64)
CONTENTS = "CONTENTS\nForeword\nTable X-1 Staff by office 3"
GRID = "TABLE X-1\nSTAFF BY OFFICE\nOffice Budget\nParks 12"
PROSE = "A REPORT\nForeword\nThe year went well."


def lines_of(number: int, text: str) -> PageLines:
    return page_lines(page_from_text(text, SHA, number))


def is_x1(band: str) -> bool:
    return "TABLE X-1" in band.upper()


def texts(lines: tuple[Line, ...]) -> list[str]:
    return [line.text for line in lines]


def test_the_header_band_is_the_text_of_the_first_lines() -> None:
    lines = lines_of(1, CONTENTS).lines
    assert header_band(lines, 2) == "CONTENTS\nForeword"
    assert header_band(lines, 5) == "CONTENTS\nForeword\nTable X-1 Staff by office 3"


def test_find_runs_takes_each_run_of_consecutive_pages_whose_band_matches() -> None:
    pages = (
        lines_of(2, CONTENTS),
        lines_of(3, GRID),
        lines_of(4, GRID),
        lines_of(5, PROSE),
        lines_of(6, GRID),
        lines_of(8, GRID),
    )
    assert find_runs(pages, is_x1) == (PageRun(3, 4), PageRun(6, 6), PageRun(8, 8))
    assert find_runs(pages[:1], is_x1) == ()


def test_only_run_takes_one_run_and_refuses_none_or_two() -> None:
    assert only_run((PageRun(3, 4),), "aaaaaaaa:staff") == PageRun(3, 4)
    none = only_run((), "aaaaaaaa:staff")
    two = only_run((PageRun(3, 4), PageRun(6, 6)), "aaaaaaaa:staff")
    assert isinstance(none, Finding)
    assert (none.severity, none.code, none.subject) == (
        Severity.BLOCK,
        "table_not_found",
        "aaaaaaaa:staff",
    )
    assert isinstance(two, Finding)
    assert (two.severity, two.code, two.subject) == (
        Severity.BLOCK,
        "several_runs",
        "aaaaaaaa:staff",
    )


def test_a_run_takes_its_pages_in_order() -> None:
    pages = tuple(lines_of(number, GRID) for number in (2, 3, 4, 5))
    run = PageRun(3, 4)
    assert run.pages == range(3, 5)
    assert [page.number for page in run.take(pages)] == [3, 4]


def test_slice_body_splits_header_body_and_furniture() -> None:
    page = lines_of(
        1,
        "TABLE X-1\n"
        "Office Budget\n"
        "Parks 12\n"
        "(1) Parks moved\n"
        "7 Roads 14\n"
        "23\n"
        "TOTAL 26\n"
        "NOTE: preliminary\n"
        "24",
    )
    rule = BodyRule(
        start=lambda line: line.text == "Parks 12",
        stop=lambda line: line.text.startswith("TOTAL"),
        drop=(r"^\(\d+\)\s",),
        prefix=r"\d{1,2}",
    )
    header, body, furniture = slice_body(page.lines, rule)
    assert texts(header) == ["TABLE X-1", "Office Budget"]
    assert texts(body) == ["Parks 12", "7 Roads 14", "TOTAL 26"]
    assert texts(furniture) == ["(1) Parks moved", "23", "NOTE: preliminary", "24"]


def test_slice_body_runs_to_the_page_end_with_no_stop() -> None:
    page = lines_of(1, "Office Budget\nParks 12\nRoads 14\n23")
    rule = BodyRule(start=lambda line: line.text.startswith("Parks"), stop=None)
    header, body, furniture = slice_body(page.lines, rule)
    assert texts(header) == ["Office Budget"]
    assert texts(body) == ["Parks 12", "Roads 14", "23"]
    assert furniture == ()


def test_slice_body_with_no_start_is_all_header() -> None:
    page = lines_of(1, PROSE)
    rule = BodyRule(start=lambda line: line.text.startswith("Parks"), stop=None)
    assert slice_body(page.lines, rule) == (page.lines, (), ())
