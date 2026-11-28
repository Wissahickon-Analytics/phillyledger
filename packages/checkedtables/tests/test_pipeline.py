from dataclasses import replace

from packages.checkedtables.tests.grid import (
    BODY,
    COLUMNS,
    ERA,
    FIRST,
    NAMES,
    ON,
    OPTIONAL_OVER,
    SECOND,
    grid_page,
    header,
    values,
)

from checkedtables.columns import Era
from checkedtables.lines import Line, PageLines, has_values
from checkedtables.pages import BodyRule
from checkedtables.pipeline import CutPages, Layout, cut_pages
from checkedtables.table import Finding, Severity

BODY_RULE = BodyRule(
    start=has_values, stop=lambda line: line.text.startswith("TOTAL"), drop=(r"^NOTE:",)
)
LAYOUT = Layout("staff", (ERA,), BODY_RULE)
TOTAL = values("TOTAL", "132", "33", "154", "44", "22")
COMMENTARY = "TABLE X-1\nABOUT THIS TABLE:\nStaff rose in the first year and fell in the second."


def page(number: int, text: str) -> PageLines:
    return grid_page(number, text)


def texts(lines: tuple[Line, ...]) -> list[str]:
    return [line.text for line in lines]


def cut_of(result: CutPages | Finding) -> CutPages:
    assert isinstance(result, CutPages), result
    return result


def stop_of(result: CutPages | Finding) -> Finding:
    assert isinstance(result, Finding), result
    assert result.severity is Severity.BLOCK
    return result


def test_two_pages_cut_into_rows_under_one_binding() -> None:
    first = page(3, f"{header()}\n{BODY}\nNOTE: preliminary")
    second = page(4, f"{header()}\n{TOTAL}\nNOTE: preliminary\n12")
    cut = cut_of(cut_pages(LAYOUT, (first, second), ON))
    assert cut.era == ERA
    assert cut.findings == ()
    assert [spec.name for spec, _ in cut.binding.columns] == list(NAMES)
    assert [each.number for each in cut.pages] == [3, 4]
    assert [len(each.header) for each in cut.pages] == [4, 4]
    assert [texts(each.furniture) for each in cut.pages] == [
        ["NOTE: preliminary"],
        ["NOTE: preliminary", "12"],
    ]
    assert [(raw.page, [word.text for word in raw.label_words]) for raw in cut.raws] == [
        (3, ["Parks"]),
        (3, ["Roads"]),
        (4, ["TOTAL"]),
    ]
    assert [[len(words) for _, words in raw.cells] for raw in cut.raws] == [[1] * 5] * 3


def test_a_missing_required_caption_is_a_binding_finding() -> None:
    lost = page(1, f"{header(other='')}\n{BODY}")
    found = stop_of(cut_pages(LAYOUT, (lost,), ON))
    assert (found.code, found.subject, found.page) == ("column_unbound", "aaaaaaaa:staff", 1)


def test_a_commentary_page_first_gives_one_warning_and_is_not_cut() -> None:
    commentary = page(2, COMMENTARY)
    cut = cut_of(cut_pages(LAYOUT, (commentary, page(3, f"{header()}\n{BODY}")), ON))
    assert [(f.severity, f.code, f.page) for f in cut.findings] == [
        (Severity.WARN, "commentary_page", 2)
    ]
    assert [each.number for each in cut.pages] == [3]


def test_a_first_grid_page_that_lost_a_signature_caption_stops_the_table() -> None:
    damaged = page(3, f"{header(groups=('FIRST YEAR', 'SECOND'))}\n{BODY}")
    intact = page(4, f"{header()}\n{TOTAL}")
    found = stop_of(cut_pages(LAYOUT, (damaged, intact), ON))
    assert (found.code, found.page) == ("era_not_found", 3)


def test_a_commentary_page_after_a_grid_page_stops_the_table() -> None:
    pages = (page(3, f"{header()}\n{BODY}"), page(4, COMMENTARY))
    found = stop_of(cut_pages(LAYOUT, pages, ON))
    assert (found.code, found.page) == ("commentary_after_grid", 4)


def test_a_run_of_commentary_alone_has_no_grid_page() -> None:
    found = stop_of(cut_pages(LAYOUT, (page(2, COMMENTARY),), ON))
    assert found.code == "no_grid_page"


def test_a_page_that_binds_other_columns_than_the_first_stops_the_table() -> None:
    era = replace(OPTIONAL_OVER, signature=(FIRST, SECOND))
    narrow = header().replace("(OVER)", "      ").replace("UNDER", "     ")
    pages = (
        page(3, f"{header()}\n{BODY}"),
        page(4, f"{narrow}\n{values('TOTAL', '132', '33', '154', '44')}"),
    )
    found = stop_of(cut_pages(replace(LAYOUT, eras=(era,)), pages, ON))
    assert (found.code, found.page) == ("columns_differ_by_page", 4)


def test_a_page_that_names_another_era_stops_the_table() -> None:
    third = Era("x1_third", (r"THIRD\s+YEAR",), COLUMNS, ERA.expected)
    pages = (
        page(3, f"{header()}\n{BODY}"),
        page(4, f"{header(groups=('FIRST YEAR', 'THIRD YEAR'))}\n{TOTAL}"),
    )
    found = stop_of(cut_pages(replace(LAYOUT, eras=(ERA, third)), pages, ON))
    assert (found.code, found.page) == ("eras_differ_by_page", 4)


def test_bind_by_position_binds_only_a_page_that_the_caller_names() -> None:
    blurred = header().replace("General", "#######").replace("Other", "#####")
    pages = (page(3, f"{header()}\n{BODY}"), page(4, f"{blurred}\n{TOTAL}"))
    found = stop_of(cut_pages(LAYOUT, pages, ON))
    assert (found.code, found.page) == ("column_unbound", 4)
    cut = cut_of(cut_pages(LAYOUT, pages, ON, frozenset({4})))
    by_caption, by_position = (each.binding for each in cut.pages)
    assert [spec.name for spec, _ in by_position.columns] == list(NAMES)
    assert all(lane and lane.caption for _, lane in by_caption.columns)
    assert all(lane and not lane.caption for _, lane in by_position.columns)
