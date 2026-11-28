from dataclasses import replace
from decimal import Decimal

from packages.checkedtables.tests.grid import (
    ERA,
    FIRST,
    NAMES,
    ON,
    OPTIONAL_OVER,
    RULE_XS,
    SECOND,
    header,
    values,
)

from checkedtables.assemble import Assembly, assemble
from checkedtables.cells import Amount, Blank, Dash, Reading, Unreadable
from checkedtables.columns import Era
from checkedtables.kinds import DashMeaning, SourceKind, UnreadableReason, ValueKind
from checkedtables.lines import has_values, page_lines
from checkedtables.pages import BodyRule
from checkedtables.pipeline import CutPages, Layout, cut_pages
from checkedtables.records import CellRecords, DashRule, EveryRow, ReviewedReading
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.rows import RowDef, RowSchema, match_rows
from checkedtables.table import Column, RowKey, RowKind, Severity, TableId
from checkedtables.testing import page_from_text
from checkedtables.words import Rule, Word

SHA = Sha256("a" * 64)
STAFF = TableId("staff")
ROOT = RowKey.of(line="total_all_funds")
PARKS = RowKey.of(dept="parks")
ROADS = RowKey.of(dept="roads")
SCHEMA = RowSchema(
    "staff",
    (
        RowDef(PARKS, RowKind.ITEM, ("Parks",)),
        RowDef(ROADS, RowKind.ITEM, ("Roads",)),
        RowDef(ROOT, RowKind.TOTAL, ("TOTAL ALL FUNDS",)),
    ),
    root=ROOT,
)
BODY = BodyRule(
    start=has_values, stop=lambda line: line.text.startswith("TOTAL"), prefix=r"\d{1,2}|I"
)
TOTAL = values("TOTAL ALL FUNDS", "132", "33", "154", "44", "22")
NO_RECORDS = CellRecords((), (), 95.0)
FLOOR = 95.0


def cut_of(*rows: str, confidence: dict[str, float] | None = None, era: Era = ERA) -> CutPages:
    text = "\n".join((header(), *rows, TOTAL))
    built = page_from_text(f"#ocr\n{text}" if confidence is not None else text, SHA, 3)
    lowered = tuple(
        replace(word, confidence=(confidence or {}).get(word.text, word.confidence))
        for word in built.words
    )
    rules = tuple(Rule(Box(x, 12.0, x, 12.0 * (text.count("\n") + 1))) for x in RULE_XS)
    lines = page_lines(replace(built, words=lowered, rules=rules))
    cut = cut_pages(Layout("staff", (era,), BODY), (lines,), ON)
    assert isinstance(cut, CutPages), cut
    return cut


def refs(cut: CutPages, row: int, column: int) -> tuple[WordRef, ...]:
    return tuple(word.ref for word in cut.raws[row].cells[column][1])


def assembled(cut: CutPages, records: CellRecords = NO_RECORDS) -> Assembly:
    return assemble(STAFF, cut, match_rows(cut.raws, SCHEMA).rows, records)


def words_of(cut: CutPages, text: str) -> tuple[Word, ...]:
    return tuple(
        word
        for raw in cut.raws
        for word in (*raw.label_words, *(w for _, cell in raw.cells for w in cell))
        if word.text == text
    )


def reading(
    cut: CutPages, *texts: str, seen: str, read: str | None, source: SourceKind
) -> ReviewedReading:
    held = [word for text in texts for word in words_of(cut, text)]
    box = Box.around(word.box for word in held)
    return ReviewedReading("r1", SHA, 3, box, source, seen, read, "read on the rendered page")


def test_assembly_lexes_each_cell_and_builds_the_table_of_the_cut() -> None:
    cut = cut_of(
        values("12 Parks", "12", "3", "14", "4", "2"), values("Roads", "-", "", "1", "", "")
    )
    built = assembled(cut)
    assert built.findings == ()
    assert built.used == frozenset()
    table = built.table
    assert table is not None
    assert (table.id, table.doc_sha256, table.era, table.pages) == (STAFF, SHA, "x1_five", (3,))
    assert [(c.name, c.kind, c.printed) for c in table.columns] == [
        (name, ValueKind.COUNT, True) for name in NAMES
    ]
    assert [row.key for row in table.rows] == [PARKS, ROADS, ROOT]
    assert [row.parent for row in table.rows] == [ROOT, ROOT, None]
    parks, roads, total = table.rows
    assert [cell.printed for cell in parks.cells if isinstance(cell, Amount)] == [
        Decimal(text) for text in ("12", "3", "14", "4", "2")
    ]
    assert roads.cells[0] == Dash("-", refs(cut, 1, 0), DashMeaning.NO_VALUE)
    assert [type(cell) for cell in roads.cells[1:]] == [Blank, Amount, Blank, Blank]
    assert (parks.page, parks.label.line_no, parks.label.text) == (3, "12", "Parks")
    parks_raw = cut.raws[0]
    assert parks.label_words == tuple(w.ref for w in (*parks_raw.prefix, *parks_raw.label_words))
    assert total.kind is RowKind.TOTAL


def test_a_column_the_page_does_not_print_is_a_column_not_printed() -> None:
    era = replace(OPTIONAL_OVER, signature=(FIRST, SECOND))
    narrow = header().replace("(OVER)", "      ").replace("UNDER", "     ")
    text = "\n".join(
        (
            narrow,
            values("Parks", "12", "3", "14", "4"),
            values("TOTAL ALL FUNDS", "1", "2", "3", "4"),
        )
    )
    rules = tuple(Rule(Box(x, 12.0, x, 12.0 * (text.count("\n") + 1))) for x in RULE_XS)
    lines = page_lines(replace(page_from_text(text, SHA, 3), rules=rules))
    cut = cut_pages(Layout("staff", (era,), BODY), (lines,), ON)
    assert isinstance(cut, CutPages), cut
    table = assembled(cut).table
    assert table is not None
    over = table.columns[-1]
    assert (over.name, over.caption, over.printed) == ("over_under", "", False)
    assert all(column.printed for column in table.columns[:-1])
    assert [row.cells[-1] for row in table.rows] == [Blank(), Blank()]


def test_a_dash_rule_changes_a_dash_and_is_named_in_used() -> None:
    cut = cut_of(
        values("Parks", "-", "3", "14", "4", "2"), values("Roads", "-", "3", "14", "4", "2")
    )
    zero = DashRule("zero_parks", "staff", ("first_general",), (PARKS,), DashMeaning.ZERO, "page 3")
    idle = DashRule("idle", "staff", ("first_general",), (ROADS,), DashMeaning.NO_VALUE, "page 3")
    other = DashRule("other", "rates", ("first_general",), EveryRow(), DashMeaning.ZERO, "page 3")
    built = assembled(cut, CellRecords((), (zero, idle, other), FLOOR))
    assert built.findings == ()
    assert built.used == frozenset({"zero_parks"})
    assert built.table is not None
    parks, roads, _ = built.table.rows
    assert parks.cells[0] == Dash("-", refs(cut, 0, 0), DashMeaning.ZERO, "zero_parks")
    assert roads.cells[0] == Dash("-", refs(cut, 1, 0), DashMeaning.NO_VALUE)


def test_a_rule_that_sets_no_value_names_no_rule_on_its_dash() -> None:
    era = replace(ERA, columns=(replace(ERA.columns[0], dash=DashMeaning.ZERO), *ERA.columns[1:]))
    cut = cut_of(values("Parks", "-", "3", "14", "4", "2"), era=era)
    rule = DashRule("none", "staff", ("first_general",), EveryRow(), DashMeaning.NO_VALUE, "p 3")
    built = assembled(cut, CellRecords((), (rule,), FLOOR))
    assert built.used == frozenset({"none"})
    assert built.table is not None
    assert built.table.rows[0].cells[0] == Dash("-", refs(cut, 0, 0), DashMeaning.NO_VALUE)
    unruled = assembled(cut).table
    assert unruled is not None
    assert unruled.rows[0].cells[0] == Dash("-", refs(cut, 0, 0), DashMeaning.ZERO)


def test_two_dash_rules_on_one_dash_block_and_change_nothing() -> None:
    cut = cut_of(values("Parks", "-", "3", "14", "4", "2"))
    first = DashRule("d1", "staff", ("first_general",), (PARKS,), DashMeaning.ZERO, "page 3")
    second = DashRule("d2", "staff", ("first_general",), EveryRow(), DashMeaning.ZERO, "page 3")
    built = assembled(cut, CellRecords((), (second, first), FLOOR))
    assert [(f.severity, f.code, f.subject, f.page) for f in built.findings] == [
        (Severity.BLOCK, "duplicate_dash_rule", "aaaaaaaa:staff:dept=parks", 3)
    ]
    assert "d1, d2" in built.findings[0].message
    assert built.used == frozenset()
    assert built.table is not None
    assert built.table.rows[0].cells[0] == Dash("-", refs(cut, 0, 0), DashMeaning.NO_VALUE)


def test_a_reading_changes_a_cell_and_is_named_in_used() -> None:
    cut = cut_of(values("Parks", "1o4", "3", "14", "4", "2"))
    record = reading(cut, "1o4", seen="1o4", read="104", source=SourceKind.TEXT_LAYER)
    built = assembled(cut, CellRecords((record,), (), FLOOR))
    assert built.findings == ()
    assert built.used == frozenset({"r1"})
    assert built.table is not None
    cell = built.table.rows[0].cells[0]
    assert isinstance(cell, Amount)
    assert (cell.printed, cell.reading, cell.review_id) == (Decimal(104), Reading.REVIEWED, "r1")


def test_a_reading_whose_box_holds_another_word_of_the_page_is_stale() -> None:
    cut = cut_of(values("Parks", "1o4", "3", "14", "4", "2"))
    record = reading(cut, "Parks", "1o4", seen="1o4", read="104", source=SourceKind.TEXT_LAYER)
    built = assembled(cut, CellRecords((record,), (), FLOOR))
    assert [f.code for f in built.findings] == ["stale_reading", "unreadable_cell"]
    assert built.used == frozenset()


def test_an_unreadable_cell_with_no_reading_blocks_and_an_accepting_reading_clears_it() -> None:
    cut = cut_of(values("Parks", "1o4", "3", "14", "4", "2"))
    built = assembled(cut)
    [blocked] = built.findings
    assert (blocked.severity, blocked.code, blocked.subject, blocked.page) == (
        Severity.BLOCK,
        "unreadable_cell",
        "aaaaaaaa:staff:dept=parks",
        3,
    )
    assert "first_general" in blocked.message
    assert built.table is not None
    assert built.table.rows[0].cells[0] == Unreadable(
        "1o4", refs(cut, 0, 0), UnreadableReason.NOT_A_NUMBER
    )
    record = reading(cut, "1o4", seen="1o4", read=None, source=SourceKind.TEXT_LAYER)
    accepted = assembled(cut, CellRecords((record,), (), FLOOR))
    assert accepted.findings == ()
    assert accepted.used == frozenset({"r1"})
    assert accepted.table is not None
    cell = accepted.table.rows[0].cells[0]
    assert isinstance(cell, Unreadable)
    assert (cell.reason, cell.accepted_by) == (UnreadableReason.NOT_A_NUMBER, "r1")


def test_an_ocr_number_under_the_confidence_floor_is_low_confidence_until_a_reading_reads_it() -> (
    None
):
    cut = cut_of(values("Parks", "12", "3", "14", "4", "2"), confidence={"12": 94.9, "14": 95.0})
    built = assembled(cut)
    [blocked] = built.findings
    assert (blocked.code, blocked.subject) == ("unreadable_cell", "aaaaaaaa:staff:dept=parks")
    assert built.table is not None
    parks = built.table.rows[0]
    assert parks.cells[0] == Unreadable("12", refs(cut, 0, 0), UnreadableReason.LOW_CONFIDENCE)
    assert isinstance(parks.cells[2], Amount)
    assert parks.cells[2].source is SourceKind.OCR
    record = reading(cut, "12", seen="12", read="12", source=SourceKind.OCR)
    read = assembled(cut, CellRecords((record,), (), FLOOR))
    assert read.findings == ()
    assert read.used == frozenset({"r1"})
    assert read.table is not None
    cell = read.table.rows[0].cells[0]
    assert isinstance(cell, Amount)
    assert (cell.printed, cell.reading) == (Decimal(12), Reading.REVIEWED)


def test_two_rows_of_one_key_give_no_table() -> None:
    cut = cut_of(
        values("Parks", "12", "3", "14", "4", "2"), values("Parks", "1", "3", "1", "4", "2")
    )
    built = assembled(cut)
    assert built.table is None
    assert [(f.severity, f.code, f.subject) for f in built.findings] == [
        (Severity.BLOCK, "duplicate_key", "aaaaaaaa:staff:dept=parks")
    ]


def test_a_row_whose_parent_is_not_in_the_table_gives_no_table() -> None:
    cut = cut_of(values("Parks", "12", "3", "14", "4", "2"))
    rows = tuple(row for row in match_rows(cut.raws, SCHEMA).rows if row.key != ROOT)
    built = assemble(STAFF, cut, rows, NO_RECORDS)
    assert built.table is None
    assert [(f.severity, f.code, f.subject) for f in built.findings] == [
        (Severity.BLOCK, "dangling_parent", "aaaaaaaa:staff:dept=parks")
    ]


def test_the_columns_of_the_table_follow_the_binding_of_the_cut() -> None:
    cut = cut_of(values("Parks", "12", "3", "14", "4", "2"))
    table = assembled(cut).table
    assert table is not None
    assert table.columns == tuple(
        Column(spec.name, spec.kind, lane.caption, True)
        for spec, lane in cut.binding.columns
        if lane is not None
    )
