from dataclasses import replace

import pytest
from packages.checkedtables.tests.grid import ERA, ON, at, grid_page, header, values

from checkedtables.kinds import Presence
from checkedtables.lines import Line, group_lines, has_values
from checkedtables.pages import BodyRule
from checkedtables.pipeline import CutPages, Layout, cut_pages
from checkedtables.refs import Sha256
from checkedtables.rows import (
    RawRow,
    RowDef,
    RowMatch,
    RowSchema,
    Truncation,
    join_rows,
    match_rows,
    starts_known_row,
    stray_findings,
)
from checkedtables.table import RowKey, RowKind, Severity
from checkedtables.testing import page_from_text

SHA = Sha256("a" * 64)
ROOT = RowKey.of(line="total_all_funds")
TOTAL = values("TOTAL ALL FUNDS", "132", "33", "154", "44", "22")
PARKS = RowKey.of(dept="parks")
PARKS_AND_ZOO = RowKey.of(dept="parks_and_zoo")
ROADS = RowKey.of(dept="roads")
PARENTS = ("Courts", "Fire", "Police")


def dept(name: str) -> RowKey:
    return RowKey.of(dept=name.lower().replace(" ", "_"))


def breakdown(name: str, part: str) -> RowKey:
    return RowKey.of(breakdown=part, dept=name.lower().replace(" ", "_"))


def item(key: RowKey, *labels: str, presence: Presence = Presence.REQUIRED) -> RowDef:
    return RowDef(key, RowKind.ITEM, labels, presence=presence)


def schema(*rows: RowDef, truncation: Truncation = Truncation.NONE) -> RowSchema:
    grand = RowDef(ROOT, RowKind.TOTAL, ("TOTAL ALL FUNDS",))
    return RowSchema("staff", (*rows, grand), root=ROOT, truncation=truncation)


def parents_with_breakdowns() -> tuple[RowDef, ...]:
    defs: list[RowDef] = []
    for name in PARENTS:
        defs.append(RowDef(dept(name), RowKind.SUBTOTAL, (f"{name} - Total",)))
        for part in ("Civilian", "Uniform"):
            key, parent = breakdown(name, part.lower()), dept(name)
            defs.append(RowDef(key, RowKind.BREAKDOWN, (part,), parent=parent, within=parent))
    return tuple(defs)


LAYOUT = Layout(
    "staff",
    (ERA,),
    BodyRule(
        start=has_values,
        stop=lambda line: line.text.startswith("TOTAL"),
        drop=(r"^NOTE:",),
        prefix=r"\d{1,2}|I",
    ),
)


def raws(*pages: tuple[str, ...]) -> tuple[RawRow, ...]:
    laid_out = tuple(
        grid_page(number, "\n".join((header(), *rows))) for number, rows in enumerate(pages, 3)
    )
    cut = cut_pages(LAYOUT, laid_out, ON)
    assert isinstance(cut, CutPages), cut
    return cut.raws


def full(label: str) -> str:
    return values(label, "12", "3", "14", "4", "2")


def matched(defs: RowSchema, *rows: str) -> RowMatch:
    return match_rows(raws((*rows, TOTAL)), defs)


def keys(result: RowMatch) -> list[RowKey]:
    return [row.key for row in result.rows]


def codes(result: RowMatch) -> list[tuple[Severity, str, str]]:
    return [(f.severity, f.code, f.subject) for f in result.findings]


def test_each_row_matches_its_definition_and_hangs_under_its_parent_or_the_root() -> None:
    defs = schema(item(PARKS, "Parks"), *parents_with_breakdowns()[6:])
    result = matched(defs, full("Parks"), full("Police - Total"), full("Civilian"), full("Uniform"))
    assert result.findings == ()
    assert keys(result) == [
        PARKS,
        dept("Police"),
        breakdown("Police", "civilian"),
        breakdown("Police", "uniform"),
        ROOT,
    ]
    assert [row.parent for row in result.rows] == [ROOT, ROOT, dept("Police"), dept("Police"), None]
    assert [row.kind for row in result.rows] == [
        RowKind.ITEM,
        RowKind.SUBTOTAL,
        RowKind.BREAKDOWN,
        RowKind.BREAKDOWN,
        RowKind.TOTAL,
    ]
    assert [row.label.text for row in result.rows] == [
        "Parks",
        "Police - Total",
        "Civilian",
        "Uniform",
        "TOTAL ALL FUNDS",
    ]


def test_a_label_that_matches_no_definition_is_an_unknown_row() -> None:
    result = matched(schema(item(PARKS, "Parks")), full("Parks"), full("Zoo"))
    assert keys(result) == [PARKS, ROOT]
    [unknown] = result.findings
    assert (unknown.severity, unknown.code, unknown.subject, unknown.page) == (
        Severity.BLOCK,
        "unknown_row",
        "aaaaaaaa:staff:Zoo",
        3,
    )


def test_a_label_that_two_definitions_hold_at_one_stage_is_an_ambiguous_row() -> None:
    defs = schema(item(PARKS, "Parks"), item(PARKS_AND_ZOO, "PARKS"))
    result = matched(defs, full("Parks"))
    assert keys(result) == [ROOT]
    assert codes(result)[0] == (Severity.BLOCK, "ambiguous_row", "aaaaaaaa:staff:Parks")
    assert "dept=parks" in result.findings[0].message
    assert "dept=parks_and_zoo" in result.findings[0].message


def test_two_rows_that_get_one_key_are_a_duplicate_row() -> None:
    result = matched(schema(item(PARKS, "Parks")), full("Parks"), full("Parks"))
    assert keys(result) == [PARKS, PARKS, ROOT]
    assert codes(result) == [(Severity.BLOCK, "duplicate_row", "aaaaaaaa:staff:dept=parks")]


def test_a_required_row_that_no_line_prints_is_a_missing_row() -> None:
    optional = item(ROADS, "Roads", presence=Presence.OPTIONAL)
    result = matched(schema(item(PARKS, "Parks"), optional), full("Roads"))
    assert keys(result) == [ROADS, ROOT]
    [missing] = result.findings
    assert (missing.severity, missing.code, missing.subject, missing.page) == (
        Severity.BLOCK,
        "missing_row",
        "aaaaaaaa:staff:dept=parks",
        None,
    )
    assert matched(schema(item(PARKS, "Parks"), optional), full("Parks")).findings == ()


def test_civilian_under_three_parents_matches_inside_each_block_and_gets_three_keys() -> None:
    lines = [full(line) for name in PARENTS for line in (f"{name} - Total", "Civilian", "Uniform")]
    result = matched(schema(*parents_with_breakdowns()), *lines)
    assert result.findings == ()
    civilian = [row for row in result.rows if row.label.text == "Civilian"]
    assert [row.key for row in civilian] == [breakdown(name, "civilian") for name in PARENTS]
    assert [row.parent for row in civilian] == [dept(name) for name in PARENTS]


def test_a_breakdown_after_its_parent_block_closes_is_an_unknown_row() -> None:
    defs = schema(item(PARKS, "Parks"), *parents_with_breakdowns()[6:])
    result = matched(defs, full("Police - Total"), full("Parks"), full("Civilian"))
    assert keys(result) == [dept("Police"), PARKS, ROOT]
    assert [(f.code, f.subject) for f in result.findings] == [
        ("unknown_row", "aaaaaaaa:staff:Civilian"),
        ("missing_row", "aaaaaaaa:staff:breakdown=civilian|dept=police"),
        ("missing_row", "aaaaaaaa:staff:breakdown=uniform|dept=police"),
    ]


def test_an_unknown_row_inside_a_block_leaves_the_block_open() -> None:
    defs = schema(*parents_with_breakdowns()[6:])
    result = matched(defs, full("Police - Total"), full("Zoo"), full("Civilian"), full("Uniform"))
    assert keys(result) == [
        dept("Police"),
        breakdown("Police", "civilian"),
        breakdown("Police", "uniform"),
        ROOT,
    ]
    assert codes(result) == [(Severity.BLOCK, "unknown_row", "aaaaaaaa:staff:Zoo")]


def test_a_parent_block_stays_open_across_a_page_break() -> None:
    defs = schema(*parents_with_breakdowns()[6:])
    result = match_rows(
        raws((full("Police - Total"), full("Civilian")), (full("Uniform"), TOTAL)), defs
    )
    assert result.findings == ()
    assert [(row.key, row.raw.page) for row in result.rows] == [
        (dept("Police"), 3),
        (breakdown("Police", "civilian"), 3),
        (breakdown("Police", "uniform"), 4),
        (ROOT, 4),
    ]


def test_a_label_matches_by_its_squashed_form_when_no_normalized_form_matches() -> None:
    result = matched(schema(item(PARKS, "Truck Rental")), full("Truc k Rental"))
    assert keys(result) == [PARKS, ROOT]
    assert result.findings == ()


def test_an_exact_match_beats_a_prefix_and_a_unique_prefix_matches_with_a_warning() -> None:
    defs = schema(
        item(PARKS, "Parks"),
        item(PARKS_AND_ZOO, "Parks and Zoo"),
        truncation=Truncation.UNIQUE_PREFIX,
    )
    exact = matched(defs, full("Parks"), full("Parks and Zoo"))
    assert keys(exact) == [PARKS, PARKS_AND_ZOO, ROOT]
    assert exact.findings == ()
    truncated = matched(defs, full("Parks"), full("Parks and Z"))
    assert keys(truncated) == [PARKS, PARKS_AND_ZOO, ROOT]
    [warning] = truncated.findings
    assert (warning.severity, warning.code, warning.subject) == (
        Severity.WARN,
        "truncated_label",
        "aaaaaaaa:staff:dept=parks_and_zoo",
    )
    assert "'Parks and Zoo'" in warning.message
    plain = matched(replace(defs, truncation=Truncation.NONE), full("Parks"), full("Parks and Z"))
    assert keys(plain) == [PARKS, ROOT]
    assert codes(plain)[0] == (Severity.BLOCK, "unknown_row", "aaaaaaaa:staff:Parks and Z")


def test_a_prefix_of_two_labels_is_an_ambiguous_row() -> None:
    defs = schema(
        item(PARKS, "Parks Department"),
        item(PARKS_AND_ZOO, "Parks and Zoo"),
        truncation=Truncation.UNIQUE_PREFIX,
    )
    result = matched(defs, full("Parks"))
    assert codes(result)[0] == (Severity.BLOCK, "ambiguous_row", "aaaaaaaa:staff:Parks")


def test_an_unlabeled_row_matches_only_the_valued_line_right_after_the_row_it_follows() -> None:
    appropriation = RowKey.of(line="current_year_appropriation")
    defs = schema(
        item(PARKS, "Parks"),
        item(ROADS, "Roads", presence=Presence.OPTIONAL),
        RowDef(appropriation, RowKind.SUBTOTAL, ("",), follows=PARKS),
    )
    unlabeled = values("", "120", "30", "140", "40", "20")
    after = matched(defs, full("Parks"), unlabeled)
    assert keys(after) == [PARKS, appropriation, ROOT]
    assert after.findings == ()
    elsewhere = matched(defs, full("Parks"), full("Roads"), unlabeled)
    assert keys(elsewhere) == [PARKS, ROADS, ROOT]
    assert codes(elsewhere) == [
        (Severity.BLOCK, "unknown_row", "aaaaaaaa:staff:"),
        (Severity.BLOCK, "missing_row", "aaaaaaaa:staff:line=current_year_appropriation"),
    ]


def test_a_label_only_line_joins_the_next_row_when_that_gives_one_candidate() -> None:
    defs = schema(item(PARKS_AND_ZOO, "Parks and Zoo"), item(ROADS, "Roads"))
    wrapped = matched(defs, full("Roads"), "Parks and", full("Zoo"))
    assert wrapped.findings == ()
    joined = wrapped.rows[1]
    assert (joined.key, joined.label.text) == (PARKS_AND_ZOO, "Parks and Zoo")
    assert [word.text for word in joined.raw.label_words] == ["Parks", "and", "Zoo"]
    assert [len(words) for _, words in joined.raw.cells] == [1] * 5
    orphan = matched(defs, full("Roads"), "Heading", full("Parks and Zoo"))
    assert keys(orphan) == [ROADS, PARKS_AND_ZOO, ROOT]
    assert codes(orphan) == [(Severity.BLOCK, "unknown_row", "aaaaaaaa:staff:Heading")]


def test_a_label_only_line_never_joins_a_row_on_the_next_page() -> None:
    defs = schema(item(PARKS_AND_ZOO, "Parks and Zoo"), item(ROADS, "Roads"))
    result = match_rows(raws((full("Roads"), "Parks and"), (full("Zoo"), TOTAL)), defs)
    assert keys(result) == [ROADS, ROOT]
    assert [(f.code, f.subject) for f in result.findings] == [
        ("unknown_row", "aaaaaaaa:staff:Parks and"),
        ("unknown_row", "aaaaaaaa:staff:Zoo"),
        ("missing_row", "aaaaaaaa:staff:dept=parks_and_zoo"),
    ]


def test_a_row_keeps_its_line_number_and_marks_on_its_label() -> None:
    defs = schema(item(PARKS, "Parks"), item(ROADS, "Roads"))
    result = matched(defs, full("12 Parks"), full("Roads (1)"))
    assert result.findings == ()
    parks, roads, _ = result.rows
    assert (parks.label.text, parks.label.line_no, parks.label.printed) == (
        "Parks",
        "12",
        "12 Parks",
    )
    assert (roads.label.text, roads.label.marks) == ("Roads", ("(1)",))


def test_join_rows_puts_the_words_of_two_rows_in_one() -> None:
    _, upper, lower, _ = raws((full("Roads"), "**Parks and**", full("I Zoo"), TOTAL))
    assert not upper.has_values()
    assert (upper.bold, lower.bold) == (True, False)
    joined = join_rows(upper, lower)
    assert joined.page == upper.page
    assert joined.prefix == lower.prefix
    assert joined.label_words == (*upper.label_words, *lower.label_words)
    assert joined.cells == lower.cells
    assert joined.stray == lower.stray
    assert joined.x0 == min(upper.x0, lower.x0)
    assert joined.bold is False


def test_starts_known_row_takes_a_line_that_opens_with_a_label_of_the_schema() -> None:
    known = starts_known_row(schema(item(PARKS, "Parks and Recreation"), item(ROADS, "")))

    def line(text: str) -> Line:
        (only,) = group_lines(page_from_text(text, SHA, 1))
        return only

    assert known(line("Parks and Recreation 12 14"))
    assert known(line("PARKS & RECREATION"))
    assert known(line("TOTAL ALL FUNDS 12"))
    assert not known(line("Parks and Recreational Programs 12"))
    assert not known(line("Office General Other"))
    assert not known(line("12 14"))


def test_a_stray_value_blocks_and_a_stray_word_warns() -> None:
    stray_row = at((0, full("Parks")), (66, "99"), (70, "zz"))
    found = stray_findings(raws((full("Roads"), stray_row, TOTAL)))
    assert [(f.severity, f.code, f.subject, f.page) for f in found] == [
        (Severity.BLOCK, "stray_value", "aaaaaaaa:stray:Parks", 3),
        (Severity.WARN, "stray_word", "aaaaaaaa:stray:Parks", 3),
    ]
    assert ["'99'" in found[0].message, "'zz'" in found[1].message] == [True, True]
    assert stray_findings(raws((full("Parks"), TOTAL))) == ()


def test_a_raw_row_has_values_when_a_lane_holds_a_word() -> None:
    (label, value) = group_lines(page_from_text("Taxes 12", SHA, 1))[0].words
    with_value = RawRow(1, (), (label,), (("budget", (value,)), ("actual", ())), (), False, 0.0)
    assert with_value.has_values()
    heading = RawRow(1, (), (label,), (("budget", ()), ("actual", ())), (value,), False, 0.0)
    assert not heading.has_values()


def test_follows_needs_an_unlabeled_row_and_a_schema_refuses_two_rows_of_one_key() -> None:
    with pytest.raises(ValueError, match="only an unlabeled row may use follows"):
        RowDef(ROADS, RowKind.ITEM, ("Roads",), follows=PARKS)
    with pytest.raises(ValueError, match="duplicate RowDef key"):
        RowSchema("staff", (item(PARKS, "Parks"), item(PARKS, "Parks and Zoo")))
