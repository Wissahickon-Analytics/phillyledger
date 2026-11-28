import re
import tomllib
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from typing import Any

from packages.datadesk.tests.fixtures.p1 import RUNS
from tests.test_p1_pages import grid_of

from checkedtables.rows import RowSchema, match_rows
from checkedtables.table import RowKey, RowKind
from checkedtables.text import normalize_label, parse_label, squash
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
ESCAPE = re.compile(r"\\.")
# Design section 5.1 gives the Streets group row its key, and shape 15 of docs/plans/step-05.md
# the Commerce one. Each key holds the words of the departments its group joins.
GROUP_KEYS = {
    "phl_group_streets_sanitation": "group=streets_with_sanitation",
    "phl_group_commerce_aviation": "group=commerce_with_aviation",
}
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


def parsed() -> dict[str, Any]:
    return tomllib.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


def row_index(file: dict[str, Any], key: str) -> int:
    (index,) = [index for index, row in enumerate(file["row"]) if row["key"] == key]
    return index


def strings(value: object, path: str) -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for name, item in value.items():
            yield path, name
            yield from strings(item, f"{path}.{name}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from strings(item, f"{path}[{index}]")


@cache
def spellings() -> dict[str, str]:
    reg = registry()
    printed = [name.value for entity in reg.entities for name in entity.names]
    printed += [alias.label for alias in reg.aliases]
    return {squash(normalize_label(text)): text for text in printed}


@cache
def entity_ids() -> re.Pattern[str]:
    return re.compile("|".join(rf"\b{re.escape(entity.id)}\b" for entity in registry().entities))


# A string holds a spelling when a run of its words, normalized as match_rows normalizes a label,
# squashes to the spelling squashed. Each regex escape and each registry id is cut first, so
# r"^Fleet\s+Management" holds a spelling and "dept=phl_dept_finance" holds none.
def held(text: str) -> list[str]:
    words = normalize_label(entity_ids().sub(" ", ESCAPE.sub(" ", text))).split()
    runs = {"".join(words[i:j]) for i in range(len(words)) for j in range(i + 1, len(words) + 1)}
    return sorted(spelling for run, spelling in spellings().items() if run in runs)


def schema_problems(file: dict[str, Any]) -> list[str]:
    rows = file.get("row", [])
    designed = {
        f"{TABLE}.row[{index}].key"
        for index, row in enumerate(rows)
        if "entity" in row and row.get("key") == GROUP_KEYS.get(row["entity"])
    }
    problems = [
        f"{path} holds {spelling!r}"
        for path, text in strings(file, TABLE)
        if path not in designed
        for spelling in held(text)
    ]
    for row in rows:
        key = row.get("key")
        if "entity" in row:
            entity = row["entity"]
            if "labels" in row:
                problems.append(f"{key} names an entity and has labels")
            if key != GROUP_KEYS.get(entity, f"dept={entity}"):
                problems.append(f"{key} is not the key of {entity}")
        if row.get("kind") == "breakdown" and not (
            set(RowKey.parse(row["parent"]).parts) <= set(RowKey.parse(key).parts)
        ):
            problems.append(f"{key} does not hold its parent {row['parent']}")
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
    assert isinstance(
        load_row_schema(TABLE, SCHEMA_FILE.read_text(encoding="utf-8")), RowSchemaSource
    )
    assert schema_problems(parsed()) == []


def test_a_department_spelled_in_a_form_fails_the_schema_test() -> None:
    file = parsed()
    police = row_index(file, "dept=phl_dept_police")
    file["row"][police]["forms"].append("{name} Police")
    assert schema_problems(file) == [
        f"{TABLE}.row[{police}].forms[1] holds 'Police'",
        "dept=phl_dept_police has the form '{name} Police'",
    ]


def test_a_department_spelled_in_a_drop_pattern_fails_the_schema_test() -> None:
    file = parsed()
    file["drop"].insert(0, r"^Finance\b")
    assert schema_problems(file) == [
        f"{TABLE}.drop[0] holds 'Finance'",
        f"drop is {file['drop']!r}, not the two patterns of shape 10",
    ]


def test_a_drop_pattern_outside_shape_10_fails_the_schema_test() -> None:
    file = parsed()
    file["drop"].append(r"^Fin\w+")
    assert schema_problems(file) == [f"drop is {file['drop']!r}, not the two patterns of shape 10"]


def test_a_department_spelled_in_a_row_key_fails_the_schema_test() -> None:
    file = parsed()
    fleet = row_index(file, "dept=phl_dept_fleet_management")
    file["row"][fleet]["key"] = "dept=Fleet Management"
    assert schema_problems(file) == [
        f"{TABLE}.row[{fleet}].key holds 'Fleet Management'",
        "dept=Fleet Management is not the key of phl_dept_fleet_management",
    ]


def test_a_department_spelled_in_a_field_the_loader_does_not_know_fails_the_schema_test() -> None:
    file = parsed()
    police = row_index(file, "dept=phl_dept_police")
    file["row"][police]["label_editions"] = ["Law"]
    file["keep"] = {"Sheriff": [r"^Fleet\s+Services"]}
    assert schema_problems(file) == [
        f"{TABLE}.row[{police}].label_editions[0] holds 'Law'",
        f"{TABLE}.keep holds 'Sheriff'",
        f"{TABLE}.keep.Sheriff[0] holds 'Fleet Services'",
    ]


def test_a_row_unit_passes_the_schema_test() -> None:
    file = parsed()
    file["row"][row_index(file, "dept=phl_dept_finance")]["unit"] = "positions"
    assert schema_problems(file) == []


def test_a_row_key_of_another_entity_or_parent_fails_the_schema_test() -> None:
    file = parsed()
    civilian = row_index(file, "breakdown=civilian|dept=phl_dept_fire")
    law = row_index(file, "dept=phl_dept_law")
    file["row"][civilian]["parent"] = "dept=phl_dept_police"
    file["row"][law]["entity"] = "phl_dept_labor_mayors_office_of"
    assert schema_problems(file) == [
        "breakdown=civilian|dept=phl_dept_fire does not hold its parent dept=phl_dept_police",
        "dept=phl_dept_law is not the key of phl_dept_labor_mayors_office_of",
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
