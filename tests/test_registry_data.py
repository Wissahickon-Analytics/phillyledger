import tomllib
from functools import cache
from pathlib import Path

from packages.datadesk.tests.fixtures.p1 import RUNS
from tests.test_p1_pages import grid_of

from checkedtables.rows import RowSchema, match_rows
from checkedtables.table import RowKey, RowKind
from checkedtables.text import parse_label
from datadesk.core.domain import DocumentVersion
from datadesk.core.fetch import INDEX_PATH
from datadesk.core.index import parse_index
from datadesk.core.registry.load import load_registry
from datadesk.core.registry.model import Registry
from datadesk.core.rowschemas import (
    RegistryLabels,
    RowSchemaSource,
    SchemaLabels,
    load_row_schema,
    schema_for,
)
from datadesk.core.tables.qcmr_positions import TABLE

REPO = Path(__file__).parents[1]
DATA = REPO / "packages/datadesk/src/datadesk/data"
SCHEMA_FILE = DATA / "rows" / f"{TABLE}.toml"
SCHEMA_LABELS = {"Civilian", "Uniform", "TOTAL ALL FUNDS"}
FORMS = {"{name}", "{name} - Total"}
PARENTS = {
    "phl_dept_district_attorney": "District Attorney - Total",
    "phl_dept_fire": "Fire - Total",
    "phl_dept_police": "Police - Total",
}
EDITIONS = [run.edition for run in RUNS]
FIRST, LAST = "2021-09-30", "2026-06-30"


def between(first: str, last: str) -> set[str]:
    return {edition for edition in EDITIONS if first <= edition.split(":")[1] <= last}


def edition(end: str) -> str:
    return f"qcmr:{end}:none"


FACT_12 = {
    "Fleet Management": between(FIRST, FIRST),
    "Fleet Services": between("2021-12-31", LAST),
    "City Representative": between(FIRST, LAST)
    - between("2022-03-31", "2022-06-30")
    - between("2023-09-30", "2024-03-31")
    - between("2024-09-30", "2025-06-30"),
    "Office of Arts and Culture": between(FIRST, "2024-12-31")
    - between("2022-03-31", "2022-06-30")
    - between("2023-09-30", "2024-03-31"),
    "Creative Philadelphia": between("2025-03-31", LAST),
    "Office of Children and Families": between(FIRST, "2024-06-30"),
    "Office of Education": between("2024-09-30", LAST),
    "Aviation": between("2023-09-30", LAST),
    "Citizens Police Oversight Commission": between("2025-09-30", LAST),
    "Mayor's Office-Neighborhood Comm. Act. Ctrs.": between("2025-09-30", LAST),
    "Office of Public Safety": between("2025-09-30", LAST),
    "Sanitation": between("2025-09-30", LAST),
}
WHOLE_YEAR_NAMES = {
    ("Fleet Services", edition(FIRST)),
    ("Office of Arts and Culture", edition("2025-03-31")),
    ("Office of Arts and Culture", edition("2025-06-30")),
}
SEAMS = (
    (
        "Streets",
        (
            edition("2025-06-30"),
            RowKey.of(group="streets_with_sanitation"),
            "phl_group_streets_sanitation",
        ),
        (edition("2025-09-30"), RowKey.of(dept="phl_dept_streets"), "phl_dept_streets"),
    ),
    (
        "Commerce",
        (
            edition("2023-06-30"),
            RowKey.of(group="commerce_with_aviation"),
            "phl_group_commerce_aviation",
        ),
        (edition("2023-09-30"), RowKey.of(dept="phl_dept_commerce"), "phl_dept_commerce"),
    ),
)


@cache
def registry() -> Registry:
    files = sorted((DATA / "registry").rglob("*.toml"))
    loaded = load_registry(
        [(str(path.relative_to(DATA)), path.read_text(encoding="utf-8")) for path in files]
    )
    assert isinstance(loaded, Registry), loaded
    return loaded


@cache
def source() -> RowSchemaSource:
    loaded = load_row_schema(TABLE, SCHEMA_FILE.read_text(encoding="utf-8"))
    assert isinstance(loaded, RowSchemaSource), loaded
    return loaded


@cache
def versions() -> dict[str, DocumentVersion]:
    index = parse_index((REPO / INDEX_PATH).read_text(encoding="utf-8"))
    return {version.edition.id(): version for version in index.versions}


@cache
def schemas() -> dict[str, RowSchema]:
    return {name: schema_for(source(), versions()[name], registry()) for name in EDITIONS}


def department_spellings(text: str) -> list[str]:
    problems: list[str] = []
    for row in tomllib.loads(text).get("row", []):
        key = row.get("key")
        if "entity" in row and "labels" in row:
            problems.append(f"{key} names an entity and has labels")
        problems += [
            f"{key} prints {label!r}"
            for label in row.get("labels", ())
            if label not in SCHEMA_LABELS
        ]
        problems += [
            f"{key} has the form {form!r}" for form in row.get("forms", ()) if form not in FORMS
        ]
    return problems


def test_the_positions_schema_spells_no_department() -> None:
    text = SCHEMA_FILE.read_text(encoding="utf-8")
    assert isinstance(load_row_schema(TABLE, text), RowSchemaSource)
    assert department_spellings(text) == []


def test_a_department_spelled_in_a_form_fails_the_schema_test() -> None:
    text = SCHEMA_FILE.read_text(encoding="utf-8")
    police = 'entity = "phl_dept_police"\nforms = ["{name} - Total"]'
    assert text.count(police) == 1
    planted = text.replace(police, police.replace("]", ', "{name} Police"]'))
    assert department_spellings(planted) == ["dept=phl_dept_police has the form '{name} Police'"]


def test_a_department_spelled_in_a_drop_pattern_fails_the_schema_test() -> None:
    text = SCHEMA_FILE.read_text(encoding="utf-8")
    drop = "drop = ['"
    assert text.count(drop) == 1
    finance = r"^Finance\b"
    planted = text.replace(drop, f"{drop}{finance}', '")
    assert isinstance(load_row_schema(TABLE, planted), RowSchemaSource)
    assert department_spellings(planted) == [f"drop has the pattern {finance!r}"]


def test_a_field_the_schema_test_does_not_read_fails_it() -> None:
    text = SCHEMA_FILE.read_text(encoding="utf-8")
    table = f'table = "{TABLE}"\n'
    police = 'entity = "phl_dept_police"\n'
    assert text.count(table) == text.count(police) == 1
    planted = text.replace(table, f"{table}keep = ['^Finance']\n").replace(
        police, f'{police}label_editions = ["Finance"]\n'
    )
    assert department_spellings(planted) == [
        "the file has the field 'keep'",
        "dept=phl_dept_police has the field 'label_editions'",
    ]


def test_every_entity_that_a_row_or_an_alias_names_is_in_the_registry() -> None:
    reg = registry()
    ids = [entity.id for entity in reg.entities]
    rows = {row.labels.entity for row in source().rows if isinstance(row.labels, RegistryLabels)}
    members = {member for entity in reg.entities for member in entity.members}
    named = rows | members | {alias.entity for alias in reg.aliases}
    assert named | {"phl_fund_general", "phl_fund_other"} <= set(ids)


def test_each_edition_has_a_schema_row_for_each_row_its_grid_pages_print() -> None:
    for run in RUNS:
        rows = schemas()[run.edition].rows
        assert len(rows) == run.rows, run.edition
        parents = {(row.key, row.labels) for row in rows if row.kind is RowKind.SUBTOTAL}
        assert parents == {(RowKey.of(dept=dept), (label,)) for dept, label in PARENTS.items()}
        breakdowns = {(row.labels, row.parent) for row in rows if row.kind is RowKind.BREAKDOWN}
        assert breakdowns == {
            ((label,), RowKey.of(dept=dept))
            for label in ("Civilian", "Uniform")
            for dept in PARENTS
        }, run.edition


def test_each_label_that_changes_is_a_label_of_the_editions_that_print_it() -> None:
    assert len(FACT_12["City Representative"]) == 11
    assert len(FACT_12["Office of Arts and Culture"]) == 9
    for label, printed in FACT_12.items():
        holding = {
            name
            for name, schema in schemas().items()
            if any(label in row.labels for row in schema.rows)
        }
        whole_year = {name for spelled, name in WHOLE_YEAR_NAMES if spelled == label}
        assert holding == printed | whole_year, label
    for label, name in WHOLE_YEAR_NAMES:
        (row,) = [row for row in schemas()[name].rows if label in row.labels]
        assert [text for text in row.labels if name in FACT_12.get(text, ())] != [], (label, name)


def test_the_two_edition_aliases_hold_in_their_editions_alone() -> None:
    by_sha = {version.sha256: name for name, version in versions().items()}
    held = {
        alias.label: {by_sha[sha] for sha in alias.editions}
        for alias in registry().aliases
        if alias.editions
    }
    assert held == {
        "Fleet Management": {edition(FIRST)},
        "Creative Philadelphia": {edition("2025-03-31"), edition("2025-06-30")},
    }


def test_streets_and_commerce_are_two_entities_across_their_seams() -> None:
    for label, before, after in SEAMS:
        for (name, key, entity), (_, other, _) in ((before, after), (after, before)):
            rows = schemas()[name].rows
            assert [(row.key, row.entity) for row in rows if label in row.labels] == [(key, entity)]
            assert other not in [row.key for row in rows], (label, name)


def test_every_cut_row_of_the_40_grid_pages_matches_one_schema_row() -> None:
    for run in RUNS:
        _, cut = grid_of(run)
        matched = match_rows(cut.raws, schemas()[run.edition])
        assert matched.findings == (), run.edition
        assert len(matched.rows) == len(cut.raws) == run.rows, run.edition


def test_every_spelling_the_positions_rows_take_from_the_files_is_printed_on_a_grid_page() -> None:
    printed: set[str] = set()
    for run in RUNS:
        _, cut = grid_of(run)
        printed |= {parse_label(raw.prefix, raw.label_words).text for raw in cut.raws}
    forms = {
        row.labels.entity: row.labels.forms
        for row in source().rows
        if isinstance(row.labels, RegistryLabels)
    }
    spelled = {
        form.replace("{name}", name.value)
        for entity in registry().entities
        if entity.id in forms
        for name in entity.names
        for form in forms[entity.id]
    }
    aliases = {alias.label for alias in registry().aliases if TABLE in alias.tables}
    labels = {
        text
        for row in source().rows
        if isinstance(row.labels, SchemaLabels)
        for text in row.labels.labels
    }
    assert len(printed) == 62
    assert spelled | aliases | labels == printed
