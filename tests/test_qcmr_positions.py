import re
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from functools import cache

from packages.checkedtables.tests.ink import cell_refs, misplaced
from packages.datadesk.tests.fixtures.p1 import RUNS, P1Run
from tests.test_p1_pages import fixture_page, stem
from tests.test_registry_data import PARENTS, registry, source, versions

from checkedtables.cells import Amount
from checkedtables.lines import page_lines
from checkedtables.pipeline import CutPages, cut_pages
from checkedtables.records import CellRecords
from checkedtables.refs import WordRef
from checkedtables.table import RowKey, RowKind, Severity, Table
from checkedtables.text import normalize_label
from checkedtables.words import Document, Page
from datadesk.core.context import ParseContext, Parsed, ParseResult
from datadesk.core.registry.model import LookupScope
from datadesk.core.registry.resolve import labels_for
from datadesk.core.rowschemas import RegistryLabels, schema_for
from datadesk.core.tables.qcmr_positions import TABLE, layout, parse

FLOOR = 95.0
ROOT = RowKey.of(line="total_all_funds")
BY_EDITION = {run.edition: run for run in RUNS}
FOOTNOTE = re.compile(r"\(\d\) ")
NOTICE = "NOTE: The material in this report is preliminary"
DIGIT = re.compile(r"\d")


def context(edition: str) -> ParseContext:
    version = versions()[edition]
    return ParseContext(
        version=version,
        schemas=(schema_for(source(), version, registry()),),
        registry=registry(),
        cell_records=CellRecords((), (), FLOOR),
        notes=(),
        table_pages=(),
    )


def run_pages(run: P1Run) -> tuple[int, ...]:
    return (*(() if run.commentary is None else (run.commentary,)), *run.grid)


def document(run: P1Run, numbers: Sequence[int]) -> Document:
    pages = tuple(fixture_page(stem(run.edition, number)) for number in numbers)
    return Document(versions()[run.edition].sha256, pages)


@cache
def parsed(edition: str) -> ParseResult:
    run = BY_EDITION[edition]
    return parse(document(run, run_pages(run)), context(edition))


def checked_table(result: ParseResult, run: P1Run) -> Table:
    assert isinstance(result, Parsed), f"{run.edition}: {result}"
    assert len(result.tables) == 1, run.edition
    blocks = [finding for finding in result.findings if finding.severity is Severity.BLOCK]
    assert blocks == [], run.edition
    (table,) = result.tables
    assert table.pages == run.grid, run.edition
    assert len(table.rows) == run.rows, run.edition
    return table


def table_of(edition: str) -> Table:
    return checked_table(parsed(edition), BY_EDITION[edition])


def cut_of(run: P1Run) -> CutPages:
    ctx = context(run.edition)
    pages = tuple(page_lines(page) for page in document(run, run_pages(run)).pages)
    cut = cut_pages(layout(ctx.schema(TABLE)), pages, ctx.period.end)
    assert isinstance(cut, CutPages), f"{run.edition}: {cut}"
    return cut


def placed_refs(table: Table) -> set[WordRef]:
    return {
        ref
        for row in table.rows
        for ref in (*row.label_words, *(r for c in row.cells for r in cell_refs(c)))
    }


def test_each_edition_parses_with_no_block_finding() -> None:
    assert len(RUNS) == 20
    assert sum(len(table_of(run.edition).rows) for run in RUNS) == 1174


def test_no_ink_is_lost_on_any_grid_page() -> None:
    pages: list[Page] = []
    for run in RUNS:
        result = parsed(run.edition)
        table = checked_table(result, run)
        cut = cut_of(run)
        assert tuple(page.number for page in cut.pages) == run.grid, run.edition
        grid = document(run, run.grid).pages
        assert misplaced(grid, cut, table, result.findings) == {}, run.edition
        pages += grid
    assert len(pages) == 40
    assert sum(len(page.words) for page in pages) == 18541


def test_each_department_label_is_a_registry_label() -> None:
    forms = {
        row.labels.entity: row.labels.forms
        for row in source().rows
        if isinstance(row.labels, RegistryLabels)
    }
    resolved = 0
    for run in RUNS:
        table = table_of(run.edition)
        ctx = context(run.edition)
        scope = LookupScope(TABLE, ctx.fiscal_year, ctx.version.sha256)
        for row in table.rows:
            where = f"{run.edition} {row.label.printed!r}"
            if row.entity is None:
                if row.key == ROOT:
                    assert (row.kind, row.parent) == (RowKind.TOTAL, None), where
                else:
                    assert row.kind is RowKind.BREAKDOWN, where
                    parent = table.row(row.parent) if row.parent is not None else None
                    assert parent is not None and parent.entity is not None, where
                continue
            names = labels_for(registry(), row.entity, scope)
            allowed = {
                normalize_label(form.replace("{name}", name))
                for name in names
                for form in forms[row.entity]
            }
            assert row.label.norm in allowed, where
            resolved += 1
        kinds = {row.kind for row in table.rows if row.entity is None}
        assert kinds <= {RowKind.BREAKDOWN, RowKind.TOTAL}, run.edition
    assert resolved == 1174 - 20 - 6 * 20


def seam_row(edition: str, page: int, label: str) -> tuple[RowKey, str | None]:
    run = BY_EDITION[edition]
    table = checked_table(parse(document(run, run.grid), context(edition)), run)
    (row,) = [row for row in table.rows if row.label.text == label]
    assert row.page == page, edition
    return row.key, row.entity


def test_streets_is_two_entities_across_fy2026() -> None:
    before = seam_row("qcmr:2025-06-30:none", 32, "Streets")
    after = seam_row("qcmr:2025-09-30:none", 36, "Streets")
    assert before == (RowKey.of(group="streets_with_sanitation"), "phl_group_streets_sanitation")
    assert after == (RowKey.of(dept="phl_dept_streets"), "phl_dept_streets")


def test_commerce_is_two_entities_across_fy2024() -> None:
    before = seam_row("qcmr:2023-06-30:none", 32, "Commerce")
    after = seam_row("qcmr:2023-09-30:none", 33, "Commerce")
    assert before == (RowKey.of(group="commerce_with_aviation"), "phl_group_commerce_aviation")
    assert after == (RowKey.of(dept="phl_dept_commerce"), "phl_dept_commerce")


def test_a_commentary_page_is_reported_and_not_parsed() -> None:
    reported = 0
    for run in RUNS:
        result = parsed(run.edition)
        table = checked_table(result, run)
        found = [finding for finding in result.findings if finding.code == "commentary_page"]
        if run.commentary is None:
            assert found == [], run.edition
            continue
        sha8 = versions()[run.edition].sha256[:8]
        assert [(f.severity, f.subject, f.page) for f in found] == [
            (Severity.WARN, f"{sha8}:{TABLE}", run.commentary)
        ], run.edition
        words = {word.ref for word in fixture_page(stem(run.edition, run.commentary)).words}
        assert not words & placed_refs(table), run.edition
        reported += 1
    assert reported == 16


def test_both_margin_digits_are_the_prefix_of_their_row_through_2023_03_31() -> None:
    rows = 0
    for run in RUNS:
        table = table_of(run.edition)
        numbered = [row for row in table.rows if row.label.line_no is not None]
        if run.edition > "qcmr:2023-03-31:none":
            assert numbered == [], run.edition
            continue
        assert sorted(row.page for row in numbered) == list(run.grid), run.edition
        for row in numbered:
            page = fixture_page(stem(run.edition, row.page))
            left = min(rule.box.x0 for rule in page.rules)
            margin = {word.ref for word in page.words if word.box.x1 < left}
            assert len(margin) == 2 and set(row.label_words[:2]) == margin, run.edition
            assert re.fullmatch(r"\d \d", row.label.line_no or ""), run.edition
            assert not DIGIT.search(row.label.text), run.edition
            rows += 1
    assert rows == 14


def test_every_cell_is_a_count_and_the_one_in_parentheses_of_2025_06_30_is_minus_one() -> None:
    cells = []
    for run in RUNS:
        table = table_of(run.edition)
        names = [column.name for column in table.columns]
        cells += [
            (name, cell) for row in table.rows for name, cell in zip(names, row.cells, strict=True)
        ]
    assert len(cells) == 11740
    assert all(isinstance(cell, Amount) for _, cell in cells)
    negatives = [name for name, cell in cells if isinstance(cell, Amount) and cell.printed < 0]
    assert negatives == ["over_under"] * 47
    table = table_of("qcmr:2025-06-30:none")
    key = RowKey.of(dept="phl_dept_water_sewer_and_stormwater_rate_board")
    cell = table.cell(key, "over_under")
    assert isinstance(cell, Amount)
    assert (cell.printed, cell.text, cell.marks) == (Decimal(-1), "(1)", ())
    row = table.row(key)
    assert row is not None and row.label.marks == ()


def test_each_parent_holds_its_two_breakdown_rows_and_every_other_row_hangs_under_the_total() -> (
    None
):
    for run in RUNS:
        table = table_of(run.edition)
        for dept, label in PARENTS.items():
            parent = RowKey.of(dept=dept)
            row = table.row(parent)
            assert row is not None and (row.kind, row.label.text) == (RowKind.SUBTOTAL, label)
            assert row.parent == ROOT, run.edition
            assert [(child.kind, child.label.text) for child in table.children(parent)] == [
                (RowKind.BREAKDOWN, "Civilian"),
                (RowKind.BREAKDOWN, "Uniform"),
            ], (run.edition, dept)
        root = table.row(ROOT)
        assert root is not None and (root.kind, root.parent) == (RowKind.TOTAL, None)
        under_root = [row for row in table.rows if row.kind is not RowKind.BREAKDOWN]
        assert [row.parent for row in under_root[:-1]] == [ROOT] * (run.rows - 7), run.edition
        assert under_root[-1] is root, run.edition


def test_the_footnotes_and_the_notice_are_furniture_and_no_finding_names_them() -> None:
    for run in RUNS:
        first, second = cut_of(run).pages
        texts = [line.text for line in first.furniture]
        footnotes = [text for text in texts if FOOTNOTE.match(text)]
        two = "qcmr:2023-09-30:none" <= run.edition <= "qcmr:2024-06-30:none"
        assert len(footnotes) == (2 if two else 1), run.edition
        for page in (first, second):
            notices = [line for line in page.furniture if line.text.startswith(NOTICE)]
            assert len(notices) == 1, (run.edition, page.number)
        codes = {finding.code for finding in parsed(run.edition).findings}
        assert codes <= {"commentary_page"}, run.edition


def test_a_first_row_that_the_schema_lacks_is_an_unknown_row_and_never_header() -> None:
    run = BY_EDITION["qcmr:2026-06-30:none"]
    first = fixture_page(stem(run.edition, 33))
    auditing = first.words[50]
    assert auditing.text == "Auditing"
    words = tuple(replace(word, text="Zoo") if word is auditing else word for word in first.words)
    doc = Document(
        first.doc_sha256, (replace(first, words=words), fixture_page(stem(run.edition, 34)))
    )
    ctx = context(run.edition)
    result = parse(doc, ctx)
    assert isinstance(result, Parsed)
    sha8 = first.doc_sha256[:8]
    blocks = [(f.code, f.subject, f.page) for f in result.findings if f.severity is Severity.BLOCK]
    assert blocks == [
        ("missing_row", f"{sha8}:{TABLE}:dept=phl_dept_auditing_city_controllers_office", None),
        ("unknown_row", f"{sha8}:{TABLE}:Zoo (City Controller's Office)", 33),
    ]
    lines = tuple(page_lines(page) for page in doc.pages)
    cut = cut_pages(layout(ctx.schema(TABLE)), lines, ctx.period.end)
    assert isinstance(cut, CutPages)
    assert [len(page.header) for page in cut.pages] == [9, 9]
    assert misplaced(doc.pages, cut, result.tables[0], result.findings) == {}
