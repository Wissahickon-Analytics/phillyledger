from dataclasses import replace
from datetime import date

import pytest
from packages.checkedtables.tests.grid import (
    BODY,
    COLUMNS,
    ERA,
    NAMES,
    SHA,
    grid_page,
    header,
)

from checkedtables.columns import (
    Binding,
    ColumnSpec,
    Era,
    Lane,
    bind_by_position,
    bind_columns,
    choose_era,
    cut_line,
    lanes_from_rules,
    lanes_from_values,
)
from checkedtables.kinds import Presence, ValueKind
from checkedtables.lines import Line, PageLines, page_lines
from checkedtables.refs import Box
from checkedtables.table import Finding
from checkedtables.testing import page_from_text
from checkedtables.text import split_line_prefix
from checkedtables.words import Rule

BUDGET = ColumnSpec("budget", "Budget", ValueKind.MONEY)
ACTUAL = ColumnSpec("actual", "Actual", ValueKind.MONEY)
TWO = Era("two", ("Budget",), (BUDGET, ACTUAL), (date(2020, 7, 1), None))


def text_lines(text: str) -> tuple[Line, ...]:
    return page_lines(page_from_text(text, SHA, 1)).lines


def bind(page: PageLines, era: Era = ERA) -> Binding | Finding:
    head, body = page.lines[:4], page.lines[4:]
    bands = lanes_from_rules(page.rules, head[-1].box)
    return bind_columns(era, head, lanes_from_values(body), bands)


def finding_code(result: object) -> str:
    assert isinstance(result, Finding), result
    return result.code


def test_column_spec_needs_a_name_a_caption_and_no_empty_group() -> None:
    for name, caption, message in (("", "Budget", "empty name"), ("budget", "", "empty caption")):
        with pytest.raises(ValueError, match=message):
            ColumnSpec(name, caption, ValueKind.MONEY)
    with pytest.raises(ValueError, match="empty group"):
        ColumnSpec("budget", "Budget", ValueKind.MONEY, group="")
    assert ColumnSpec("b", "B", ValueKind.MONEY).caption == "B"


def test_an_era_needs_a_signature_distinct_names_and_a_required_column() -> None:
    start = (date(2020, 7, 1), None)
    with pytest.raises(ValueError, match="no signature"):
        Era("none", (), (BUDGET,), start)
    with pytest.raises(ValueError, match="duplicate column names"):
        Era("twice", ("Budget",), (BUDGET, BUDGET), start)
    with pytest.raises(ValueError, match="no required column"):
        Era("loose", ("Budget",), (replace(BUDGET, presence=Presence.OPTIONAL),), start)


def test_choose_era_takes_the_one_era_whose_signature_the_header_prints() -> None:
    old = Era("old", ("Budget",), (BUDGET,), (date(2007, 7, 1), date(2019, 6, 30)), ("Actual",))
    assert choose_era((old, TWO), "Office Budget Actual", date(2024, 6, 30)) == TWO
    assert finding_code(choose_era((old, TWO), "Office Spent", date(2024, 6, 30))) == (
        "era_not_found"
    )
    assert finding_code(
        choose_era((TWO, replace(TWO, name="copy")), "Budget", date(2024, 6, 30))
    ) == ("several_eras")
    assert finding_code(choose_era((old,), "Office Budget", date(2024, 6, 30))) == (
        "era_out_of_range"
    )
    assert choose_era((old,), "Office Budget", date(2019, 6, 30)) == old


def test_right_edges_cluster_into_lanes_that_meet() -> None:
    lanes = lanes_from_values(grid_page(1, BODY).lines)
    assert lanes == (
        Lane(114.0, 132.0, ""),
        Lane(132.0, 192.0, ""),
        Lane(192.0, 264.0, ""),
        Lane(264.0, 324.0, ""),
        Lane(324.0, 384.0, ""),
    )


def test_a_mark_beside_a_label_seeds_no_lane() -> None:
    lines = text_lines("Human Services (1)    12     34\nParks                 10     20")
    lanes = lanes_from_values(lines)
    assert [lane.x1 for lane in lanes] == [144.0, 186.0]
    binding = bind_columns(TWO, text_lines("Office                Budget Actual"), lanes, ())
    assert isinstance(binding, Binding)
    row = cut_line(lines[0], binding, ())
    assert [word.text for word in row.label_words] == ["Human", "Services", "(1)"]
    assert [(name, [word.text for word in words]) for name, words in row.cells] == [
        ("budget", ["12"]),
        ("actual", ["34"]),
    ]
    spaced = lanes_from_values(text_lines("Ward  7    12     34"))
    assert [lane.x1 for lane in spaced] == [42.0, 78.0, 120.0]
    assert lanes_from_values(text_lines("Class 100 Total")) == ()


def test_touching_pieces_of_a_rule_count_as_one_rule() -> None:
    rules = (
        Rule(Box(10.0, 0.0, 10.0, 50.0)),
        Rule(Box(10.0, 50.0, 10.0, 100.0)),
        Rule(Box(60.0, 0.0, 60.0, 100.0)),
        Rule(Box(110.0, 0.0, 110.0, 45.0)),
        Rule(Box(110.0, 47.0, 110.0, 100.0)),
        Rule(Box(0.0, 30.0, 200.0, 30.0)),
    )
    assert lanes_from_rules(rules, Box(0.0, 40.0, 200.0, 60.0)) == (Lane(10.0, 60.0, ""),)
    assert lanes_from_rules(rules, Box(0.0, 60.0, 200.0, 90.0)) == (
        Lane(10.0, 60.0, ""),
        Lane(60.0, 110.0, ""),
    )


def test_columns_bind_by_caption_inside_the_band_of_their_group() -> None:
    binding = bind(grid_page(1, f"{header()}\n{BODY}"))
    assert isinstance(binding, Binding)
    assert [spec.name for spec, _ in binding.columns] == list(NAMES)
    assert [(lane.x0, lane.x1, lane.caption) for _, lane in binding.columns if lane] == [
        (114.0, 132.0, "FIRST General"),
        (132.0, 192.0, "FIRST YEAR Other"),
        (192.0, 264.0, "SECOND General"),
        (264.0, 324.0, "SECOND YEAR Other"),
        (324.0, 384.0, "(OVER) UNDER"),
    ]
    assert binding.label_right == 114.0


def test_two_groups_that_trade_places_bind_to_no_wrong_name() -> None:
    swapped = grid_page(1, f"{header(groups=('SECOND YEAR', 'FIRST YEAR'))}\n{BODY}")
    assert finding_code(bind(swapped)) == "columns_out_of_order"
    as_printed = replace(ERA, columns=(*COLUMNS[2:4], *COLUMNS[:2], COLUMNS[4]))
    binding = bind(swapped, as_printed)
    assert isinstance(binding, Binding)
    assert [spec.name for spec, lane in binding.columns if lane] == [
        "second_general",
        "second_other",
        "first_general",
        "first_other",
        "over_under",
    ]


def test_a_spec_with_a_group_binds_nothing_without_a_band() -> None:
    page = grid_page(1, f"{header()}\n{BODY}")
    found = bind_columns(ERA, page.lines[:4], lanes_from_values(page.lines[4:]), ())
    assert finding_code(found) == "column_unbound"


def test_the_longest_caption_match_takes_the_lane() -> None:
    lines = text_lines(
        "Office    Prior\n          Year\n          Actual    Actual\nParks        120       130"
    )
    prior = ColumnSpec("prior", r"Prior\s+Year\s+Actual", ValueKind.MONEY)
    era = Era("prior", ("Actual",), (prior, ACTUAL), (date(2020, 7, 1), None))
    binding = bind_columns(era, lines[:3], lanes_from_values(lines[3:]), ())
    assert isinstance(binding, Binding)
    assert [(spec.name, lane.caption) for spec, lane in binding.columns if lane] == [
        ("prior", "Prior Year Actual"),
        ("actual", "Actual"),
    ]


def test_an_unclaimed_lane_and_a_tie_are_findings() -> None:
    extra = text_lines("Office   Budget   Actual   Notes\nParks        12       13       9")
    assert finding_code(bind_columns(TWO, extra[:1], lanes_from_values(extra[1:]), ())) == (
        "lane_unclaimed"
    )
    stacked = text_lines("Office   Budget\n         Actual\nParks        12")
    loose = replace(TWO, columns=(BUDGET, replace(ACTUAL, presence=Presence.OPTIONAL)))
    assert finding_code(bind_columns(loose, stacked[:2], lanes_from_values(stacked[2:]), ())) == (
        "columns_tie"
    )


def test_bind_by_position_needs_one_lane_for_each_column() -> None:
    lanes = lanes_from_values(grid_page(1, BODY).lines)
    binding = bind_by_position(ERA, lanes)
    assert isinstance(binding, Binding)
    assert [(spec.name, lane) for spec, lane in binding.columns] == list(
        zip(NAMES, lanes, strict=True)
    )
    assert binding.label_right == 114.0
    assert finding_code(bind_by_position(ERA, lanes[:4])) == "lane_count_differs"


def test_cut_line_puts_each_word_in_one_place() -> None:
    lanes = (Lane(90.0, 108.0, ""), Lane(108.0, 150.0, ""))
    binding = Binding("two", ((BUDGET, lanes[0]), (ACTUAL, lanes[1])), 90.0)
    line = text_lines("7 **Parks** **Dept**    12     34   x")[0]
    prefix, rest = split_line_prefix(line, r"\d{1,2}")
    row = cut_line(rest, binding, prefix)
    assert [word.text for word in row.prefix] == ["7"]
    assert [word.text for word in row.label_words] == ["Parks", "Dept"]
    assert [(name, [word.text for word in words]) for name, words in row.cells] == [
        ("budget", ["12"]),
        ("actual", ["34"]),
    ]
    assert [word.text for word in row.stray] == ["x"]
    assert (row.page, row.bold, row.x0) == (1, True, 12.0)
    plain = cut_line(text_lines("Parks           12     34")[0], binding, ())
    assert (plain.bold, plain.stray) == (False, ())
    ocr = page_lines(page_from_text("#ocr\nParks           12     34", SHA, 1)).lines[0]
    assert cut_line(ocr, binding, ()).bold is None
    missing = Binding("two", ((BUDGET, lanes[0]), (ACTUAL, None)), 90.0)
    row = cut_line(text_lines("Parks           12     34")[0], missing, ())
    assert [(name, len(words)) for name, words in row.cells] == [("budget", 1), ("actual", 0)]
    assert [word.text for word in row.stray] == ["34"]
