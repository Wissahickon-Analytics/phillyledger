import re
import tomllib
from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from functools import cache
from typing import Any

from packages.checkedtables.tests.ink import cell_refs, misplaced
from packages.datadesk.tests.fixtures.p1 import RUNS, P1Run
from tests.test_p1_pages import MARK, fixture_page, stem
from tests.test_registry_data import (
    DATA,
    FIRST,
    LAST,
    PARENTS,
    SCHEMA_FILE,
    between,
    registry,
    source,
    versions,
)

from checkedtables.cells import Amount
from checkedtables.pipeline import CutPages
from checkedtables.records import CellRecords
from checkedtables.refs import WordRef
from checkedtables.table import Row, RowKey, RowKind, Severity, Table
from checkedtables.words import Document, Page, Word
from datadesk.core.context import ParseContext, Parsed, ParseResult
from datadesk.core.rowschemas import schema_for
from datadesk.core.tables.qcmr_positions import TABLE, parse

FLOOR = 95.0
ROOT = RowKey.of(line="total_all_funds")
BY_EDITION = {run.edition: run for run in RUNS}
FOOTNOTE = re.compile(r"\(\d\) ")
NOTICE = "NOTE: The material in this report is preliminary"
DIGIT = re.compile(r"\d")
# Each department and group label that the 40 grid pages print, without its footnote mark, with
# the entity of its row. A label that names its entity in some editions only is in SCOPED with
# them: the two seams (QPOS-Q12, decision 21), and Fleet Management and Office of Arts and
# Culture with the names that replace them.
PRINTED_ENTITIES = {
    "Auditing (City Controller's Office)": "phl_dept_auditing_city_controllers_office",
    "Aviation": "phl_dept_aviation",
    "Board of Ethics": "phl_dept_board_of_ethics",
    "Board of Pensions": "phl_dept_board_of_pensions",
    "Board of Revision of Taxes": "phl_dept_board_of_revision_of_taxes",
    "Citizens Police Oversight Commission": "phl_dept_citizens_police_oversight_commission",
    "City Commissioners (Election Board)": "phl_dept_city_commissioners_election_board",
    "City Council": "phl_dept_city_council",
    "City Representative": "phl_dept_city_representative",
    "City Treasurer": "phl_dept_city_treasurer",
    "Civil Service Commission": "phl_dept_civil_service_commission",
    "District Attorney - Total": "phl_dept_district_attorney",
    "Finance": "phl_dept_finance",
    "Fire - Total": "phl_dept_fire",
    "First Judicial District": "phl_dept_first_judicial_district",
    "Free Library": "phl_dept_free_library",
    "Human Relations Commission": "phl_dept_human_relations_commission",
    "Human Services": "phl_dept_human_services",
    "L&I-Board of Building Standards": "phl_dept_l_and_i_board_of_building_standards",
    "L&I-Board of L & I Review": "phl_dept_l_and_i_board_of_l_and_i_review",
    "Labor": "phl_dept_labor_mayors_office_of",
    "Law": "phl_dept_law",
    "Licenses & Inspections": "phl_dept_licenses_and_inspections",
    "Managing Director's Office": "phl_dept_managing_directors_office",
    "Mayor's Office": "phl_dept_mayors_office",
    "Mayor's Office-Comm. Empowerment & Opp.": (
        "phl_dept_mayors_office_of_community_empowerment_and_oppo"
    ),
    "Mayor's Office-Neighborhood Comm. Act. Ctrs.": (
        "phl_dept_neighborhood_community_action_centers"
    ),
    "Mural Arts Program": "phl_dept_mural_arts_program",
    "Office of Behavioral Hlth & Intellectual disAbility": (
        "phl_dept_office_of_behavioral_health_and_intellectual_dis"
    ),
    "Office of Children and Families": "phl_dept_office_of_children_and_families",
    "Office of Education": "phl_dept_office_of_education",
    "Office of Homeless Services": "phl_dept_office_of_homeless_services",
    "Office of Human Resources": "phl_dept_office_of_human_resources",
    "Office of Innovation and Technology": "phl_dept_office_of_innovation_and_technology",
    "Office of Property Assessment": "phl_dept_office_of_property_assessment",
    "Office of Public Safety": "phl_dept_office_of_public_safety",
    "Office of Sustainability": "phl_dept_office_of_sustainability",
    "Office of the Chief Administrative Officer": (
        "phl_dept_office_of_the_chief_administrative_officer"
    ),
    "Office of the Inspector General": "phl_dept_office_of_the_inspector_general",
    "Parks and Recreation": "phl_dept_parks_and_recreation",
    "Planning & Development": "phl_dept_planning_and_development",
    "Police - Total": "phl_dept_police",
    "Prisons": "phl_dept_prisons",
    "Procurement": "phl_dept_procurement",
    "Public Health": "phl_dept_public_health",
    "Public Property": "phl_dept_public_property",
    "Records": "phl_dept_records",
    "Register of Wills": "phl_dept_register_of_wills",
    "Revenue": "phl_dept_revenue",
    "Sanitation": "phl_dept_streets_sanitation",
    "Sheriff": "phl_dept_sheriff",
    "Water": "phl_dept_water",
    "Water,Sewer & Stormwater Rate Board": "phl_dept_water_sewer_and_stormwater_rate_board",
}
SCOPED = (
    ("Streets", "phl_group_streets_sanitation", between(FIRST, "2025-06-30")),
    ("Streets", "phl_dept_streets", between("2025-09-30", LAST)),
    ("Commerce", "phl_group_commerce_aviation", between(FIRST, "2023-06-30")),
    ("Commerce", "phl_dept_commerce", between("2023-09-30", LAST)),
    ("Fleet Management", "phl_dept_fleet_management", between(FIRST, FIRST)),
    ("Fleet Services", "phl_dept_fleet_management", between("2021-12-31", LAST)),
    (
        "Office of Arts and Culture",
        "phl_dept_office_of_arts_and_culture",
        between(FIRST, "2024-12-31"),
    ),
    ("Creative Philadelphia", "phl_dept_office_of_arts_and_culture", between("2025-03-31", LAST)),
)


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


def cut_of(result: ParseResult) -> CutPages:
    assert isinstance(result, Parsed), result
    (cut,) = result.cuts
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
        cut = cut_of(result)
        assert tuple(page.number for page in cut.pages) == run.grid, run.edition
        grid = document(run, run.grid).pages
        assert misplaced(grid, cut, table, result.findings) == {}, run.edition
        pages += grid
    assert len(pages) == 40
    assert sum(len(page.words) for page in pages) == 18541


@cache
def registry_files() -> tuple[dict[str, Any], ...]:
    paths = sorted((DATA / "registry").rglob("*.toml"))
    return tuple(tomllib.loads(path.read_text(encoding="utf-8")) for path in paths)


def in_years(record: dict[str, Any], year: int) -> bool:
    return record.get("first_fy", year) <= year <= record.get("last_fy", year)


def written_spellings(entity: str, year: int, sha: str) -> set[str]:
    spellings: set[str] = set()
    for file in registry_files():
        for kind, records in file.items():
            if kind == "alias":
                spellings |= {
                    alias["label"]
                    for alias in records
                    if alias["entity"] == entity
                    and TABLE in alias["tables"]
                    and in_years(alias, year)
                    and (not alias.get("editions") or sha in alias["editions"])
                }
            elif kind != "relation":
                spellings |= {
                    name["value"]
                    for record in records
                    if record["id"] == entity
                    for name in record.get("names", [])
                    if in_years(name, year)
                }
    return spellings


def printed_entities(edition: str) -> dict[str, str]:
    scoped = {label: entity for label, entity, editions in SCOPED if edition in editions}
    return PRINTED_ENTITIES | scoped


@cache
def page_words(edition: str, number: int) -> tuple[float, dict[WordRef, Word]]:
    page = fixture_page(stem(edition, number))
    return min(rule.box.x0 for rule in page.rules), {word.ref: word for word in page.words}


def printed_label(edition: str, row: Row) -> str:
    left, words = page_words(edition, row.page)
    kept = [words[ref] for ref in row.label_words]
    return " ".join(w.text for w in kept if w.box.x1 >= left and not MARK.fullmatch(w.text))


def test_each_department_label_is_a_registry_label() -> None:
    schema_file = tomllib.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    forms = {
        row["entity"]: row.get("forms", ["{name}"]) for row in schema_file["row"] if "entity" in row
    }
    printed: set[tuple[str, str]] = set()
    resolved = 0
    for run in RUNS:
        table = table_of(run.edition)
        version = versions()[run.edition]
        end = version.edition.period.end
        year = end.year + (end.month >= 7)
        entities = printed_entities(run.edition)
        for row in table.rows:
            if row.entity is None:
                where = f"{run.edition} {row.key}"
                if row.key == ROOT:
                    assert (row.kind, row.parent) == (RowKind.TOTAL, None), where
                else:
                    assert row.kind is RowKind.BREAKDOWN, where
                    parent = table.row(row.parent) if row.parent is not None else None
                    assert parent is not None and parent.entity is not None, where
                continue
            label = printed_label(run.edition, row)
            assert entities.get(label) == row.entity, (run.edition, label)
            spellings = {
                form.replace("{name}", name)
                for name in written_spellings(row.entity, year, version.sha256)
                for form in forms[row.entity]
            }
            assert label in spellings, (run.edition, label, row.entity)
            printed.add((label, row.entity))
            resolved += 1
        kinds = {row.kind for row in table.rows if row.entity is None}
        assert kinds <= {RowKind.BREAKDOWN, RowKind.TOTAL}, run.edition
    assert resolved == 1174 - 20 - 6 * 20
    assert printed == {*PRINTED_ENTITIES.items(), *((label, e) for label, e, _ in SCOPED)}


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
        first, second = cut_of(parsed(run.edition)).pages
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
    cut = cut_of(result)
    assert [len(page.header) for page in cut.pages] == [9, 9]
    assert misplaced(doc.pages, cut, result.tables[0], result.findings) == {}


def findings_on_page_33(words: Sequence[Word]) -> list[tuple[Severity, str, str, int | None]]:
    edition = "qcmr:2026-06-30:none"
    first = fixture_page(stem(edition, 33))
    pages = (replace(first, words=tuple(words)), fixture_page(stem(edition, 34)))
    result = parse(Document(first.doc_sha256, pages), context(edition))
    assert isinstance(result, Parsed)
    return [(f.severity, f.code, f.subject, f.page) for f in result.findings]


def test_parse_returns_the_finding_of_a_cell_that_assembly_cannot_read() -> None:
    first = fixture_page(stem("qcmr:2026-06-30:none", 33))
    finance, count = first.words[240:242]
    assert (finance.text, count.text) == ("Finance", "126")
    words = [replace(word, text="(cid:5)") if word is count else word for word in first.words]
    sha8 = first.doc_sha256[:8]
    assert findings_on_page_33(words) == [
        (Severity.BLOCK, "unreadable_cell", f"{sha8}:{TABLE}:dept=phl_dept_finance", 33)
    ]


def test_parse_returns_the_finding_of_a_stray_word_on_a_row() -> None:
    first = fixture_page(stem("qcmr:2026-06-30:none", 33))
    finance, last = first.words[240], first.words[250]
    assert (finance.text, last.text) == ("Finance", "14")
    box = replace(last.box, x0=last.box.x1 + 10, x1=last.box.x1 + 16)
    stray = replace(last, ref=replace(last.ref, index=len(first.words)), text="x", box=box)
    sha8 = first.doc_sha256[:8]
    assert findings_on_page_33([*first.words, stray]) == [
        (Severity.WARN, "stray_word", f"{sha8}:stray:Finance", 33)
    ]
