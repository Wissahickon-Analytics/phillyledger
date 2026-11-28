from datetime import date

import pytest

from checkedtables.kinds import Presence
from checkedtables.refs import Sha256
from checkedtables.rows import RowDef, RowSchema, Truncation
from checkedtables.table import RowKey, RowKind, Severity
from datadesk.core.domain import DocumentVersion, EditionKey, Period
from datadesk.core.registry.load import Refused
from datadesk.core.registry.model import Alias, Dated, Entity, EntityKind, Registry
from datadesk.core.rowschemas import (
    RegistryLabels,
    RowSchemaSource,
    RowSource,
    SchemaLabels,
    load_row_schema,
    schema_for,
)

TABLE = "qcmr_positions"
FY2025_Q4 = Sha256("2" * 64)
FY2026_Q1 = Sha256("3" * 64)
REGISTRY = Registry(
    entities=(
        Entity("phl_dept_police", EntityKind.DEPARTMENT, (Dated("Police", None, None),)),
        Entity("phl_dept_streets", EntityKind.DEPARTMENT, (Dated("Streets", None, None),)),
        Entity(
            "phl_group_streets_sanitation",
            EntityKind.GROUP,
            (),
            members=("phl_dept_streets", "phl_dept_streets_sanitation"),
        ),
    ),
    relations=(),
    aliases=(Alias("phl_group_streets_sanitation", "Streets", (TABLE,), 2022, 2025),),
)
SCHEMA = """
table = "qcmr_positions"
root = "line=total_all_funds"
drop = ['^NOTE:']

[[row]]
key = "dept=phl_dept_police"
kind = "subtotal"
entity = "phl_dept_police"
forms = ["{name} - Total"]

[[row]]
key = "breakdown=civilian|dept=phl_dept_police"
kind = "breakdown"
parent = "dept=phl_dept_police"
within = "dept=phl_dept_police"
labels = ["Civilian"]

[[row]]
key = "group=streets_with_sanitation"
kind = "item"
entity = "phl_group_streets_sanitation"
periods = [["2021-07-01", "2025-06-30"]]

[[row]]
key = "dept=phl_dept_streets"
kind = "item"
entity = "phl_dept_streets"
periods = [["2025-07-01", ""]]

[[row]]
key = "line=total_all_funds"
kind = "total"
labels = ["TOTAL ALL FUNDS"]
"""
POLICE = RowKey.of(dept="phl_dept_police")
CIVILIAN = RowKey.of(breakdown="civilian", dept="phl_dept_police")
GROUP = RowKey.of(group="streets_with_sanitation")
STREETS = RowKey.of(dept="phl_dept_streets")
TOTAL = RowKey.of(line="total_all_funds")


def source(text: str = SCHEMA) -> RowSchemaSource:
    loaded = load_row_schema(TABLE, text)
    assert isinstance(loaded, RowSchemaSource), loaded
    return loaded


def version(end: date, sha: Sha256) -> DocumentVersion:
    start = date(end.year, end.month - 2, 1)
    return DocumentVersion(
        sha256=sha,
        edition=EditionKey("qcmr", Period(start, end)),
        listed_at="20251101000000",
        urls=(),
        title="Quarterly City Managers Report",
        printed_period=Period(start, end),
        supersedes=None,
    )


def codes(loaded: RowSchemaSource | Refused) -> list[tuple[str, str]]:
    assert isinstance(loaded, Refused), loaded
    assert {finding.severity for finding in loaded.findings} == {Severity.BLOCK}
    return [(finding.code, finding.subject) for finding in loaded.findings]


def row(text: str) -> str:
    return f'table = "qcmr_positions"\n\n[[row]]\n{text}\n'


def test_load_row_schema_reads_each_row_with_the_home_of_its_labels() -> None:
    open_end = Period(date(2025, 7, 1), date.max)
    assert source() == RowSchemaSource(
        table=TABLE,
        root=TOTAL,
        drop=("^NOTE:",),
        rows=(
            RowSource(
                POLICE, RowKind.SUBTOTAL, RegistryLabels("phl_dept_police", ("{name} - Total",))
            ),
            RowSource(
                CIVILIAN,
                RowKind.BREAKDOWN,
                SchemaLabels(("Civilian",)),
                parent=POLICE,
                within=POLICE,
            ),
            RowSource(
                GROUP,
                RowKind.ITEM,
                RegistryLabels("phl_group_streets_sanitation", ("{name}",)),
                periods=(Period(date(2021, 7, 1), date(2025, 6, 30)),),
            ),
            RowSource(
                STREETS,
                RowKind.ITEM,
                RegistryLabels("phl_dept_streets", ("{name}",)),
                periods=(open_end,),
            ),
            RowSource(TOTAL, RowKind.TOTAL, SchemaLabels(("TOTAL ALL FUNDS",))),
        ),
    )


def test_forms_build_the_parent_label_from_the_registry_name() -> None:
    schema = schema_for(source(), version(date(2025, 6, 30), FY2025_Q4), REGISTRY)
    (police,) = [found for found in schema.rows if found.key == POLICE]
    assert police == RowDef(POLICE, RowKind.SUBTOTAL, ("Police - Total",), entity="phl_dept_police")


def test_schema_for_narrows_the_rows_to_one_edition() -> None:
    assert schema_for(source(), version(date(2025, 6, 30), FY2025_Q4), REGISTRY) == RowSchema(
        table=TABLE,
        rows=(
            RowDef(POLICE, RowKind.SUBTOTAL, ("Police - Total",), entity="phl_dept_police"),
            RowDef(CIVILIAN, RowKind.BREAKDOWN, ("Civilian",), parent=POLICE, within=POLICE),
            RowDef(GROUP, RowKind.ITEM, ("Streets",), entity="phl_group_streets_sanitation"),
            RowDef(TOTAL, RowKind.TOTAL, ("TOTAL ALL FUNDS",)),
        ),
        root=TOTAL,
        drop=("^NOTE:",),
    )


def test_a_row_outside_its_periods_leaves_the_schema() -> None:
    def keys(end: date, sha: Sha256) -> list[RowKey]:
        return [found.key for found in schema_for(source(), version(end, sha), REGISTRY).rows]

    assert keys(date(2025, 6, 30), FY2025_Q4) == [POLICE, CIVILIAN, GROUP, TOTAL]
    assert keys(date(2025, 9, 30), FY2026_Q1) == [POLICE, CIVILIAN, STREETS, TOTAL]
    assert keys(date(2021, 6, 30), FY2025_Q4) == [POLICE, CIVILIAN, TOTAL]
    assert keys(date(2099, 6, 30), FY2025_Q4) == [POLICE, CIVILIAN, STREETS, TOTAL]


def test_a_row_leaves_the_schema_of_an_edition_it_names_absent() -> None:
    text = SCHEMA.replace(
        'labels = ["Civilian"]', f'labels = ["Civilian"]\nabsent_editions = ["{FY2026_Q1}"]'
    )
    absent = schema_for(source(text), version(date(2025, 9, 30), FY2026_Q1), REGISTRY)
    present = schema_for(source(text), version(date(2025, 9, 30), FY2025_Q4), REGISTRY)
    assert CIVILIAN not in [found.key for found in absent.rows]
    assert CIVILIAN in [found.key for found in present.rows]


def test_an_entity_with_no_label_in_the_edition_gives_a_row_with_no_label() -> None:
    schema = schema_for(source(), version(date(2026, 6, 30), FY2026_Q1), Registry((), (), ()))
    assert [found.labels for found in schema.rows] == [(), ("Civilian",), (), ("TOTAL ALL FUNDS",)]


def test_load_row_schema_reads_the_other_fields_of_a_row() -> None:
    text = (
        'table = "qcmr_positions"\ntruncation = "unique_prefix"\n\n'
        '[[row]]\nkey = "line=memo"\nkind = "memo"\nlabels = [""]\nfollows = "line=total"\n'
        'presence = "optional"\nunit = "positions"\n'
    )
    assert source(text).truncation is Truncation.UNIQUE_PREFIX
    (memo,) = schema_for(source(text), version(date(2025, 9, 30), FY2026_Q1), REGISTRY).rows
    assert memo == RowDef(
        RowKey.of(line="memo"),
        RowKind.MEMO,
        ("",),
        follows=RowKey.of(line="total"),
        presence=Presence.OPTIONAL,
        unit="positions",
    )


def test_an_entity_row_with_labels_is_refused() -> None:
    text = row(
        'key = "dept=phl_dept_police"\nkind = "item"\nentity = "phl_dept_police"\nlabels = ["Police"]'
    )
    assert codes(load_row_schema(TABLE, text)) == [("rowschema_entity_with_labels", f"{TABLE}:row 1")]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("[[row]\n", [("rowschema_not_toml", TABLE)], id="not_toml"),
        pytest.param(
            'table = "qcmr_obligations"\n', [("rowschema_wrong_table", TABLE)], id="other_table"
        ),
        pytest.param("", [("rowschema_missing_field", TABLE)], id="no_table"),
        pytest.param(
            'table = "qcmr_positions"\nrows = []\n',
            [("rowschema_unknown_field", TABLE)],
            id="unknown_key",
        ),
        pytest.param(
            'table = "qcmr_positions"\nroot = "total_all_funds"\n',
            [("rowschema_bad_value", TABLE)],
            id="root_not_a_key",
        ),
        pytest.param(
            'table = "qcmr_positions"\nrow = "line=total"\n',
            [("rowschema_wrong_type", TABLE)],
            id="rows_not_an_array",
        ),
        pytest.param(
            row('key = "dept=phl_dept_police"\nkind = "item"'),
            [("rowschema_missing_field", f"{TABLE}:row 1")],
            id="no_entity_and_no_labels",
        ),
        pytest.param(
            row('key = "line=total"\nkind = "total"\nlabels = ["TOTAL"]\nforms = ["{name}"]'),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="forms_without_an_entity",
        ),
        pytest.param(
            row(
                'key = "dept=phl_dept_police"\nkind = "item"\nentity = "phl_dept_police"\nforms = ["Total"]'
            ),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="form_without_the_name",
        ),
        pytest.param(
            row(
                'key = "dept=phl_dept_police"\nkind = "item"\nentity = "phl_dept_police"\nforms = ["{name} {year}"]'
            ),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="form_with_another_field",
        ),
        pytest.param(
            row('key = "dept=police"\nkind = "department"\nlabels = ["Police"]'),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="kind_not_a_member",
        ),
        pytest.param(
            row('key = "dept"\nkind = "item"\nlabels = ["Police"]'),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="key_with_no_part",
        ),
        pytest.param(
            row('key = "line=x"\nkind = "item"\nlabels = ["X"]\nperiods = [["2025-07-01"]]'),
            [("rowschema_wrong_type", f"{TABLE}:row 1")],
            id="period_with_one_end",
        ),
        pytest.param(
            row(
                'key = "line=x"\nkind = "item"\nlabels = ["X"]\nperiods = [["2025-07-01", "FY26"]]'
            ),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="period_end_not_a_date",
        ),
        pytest.param(
            row(
                'key = "line=x"\nkind = "item"\nlabels = ["X"]\nperiods = [["2025-07-01", "2025-06-30"]]'
            ),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="period_that_ends_before_it_starts",
        ),
        pytest.param(
            row('key = "line=x"\nkind = "item"\nlabels = ["X"]\nabsent_editions = ["FY2026 Q1"]'),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="absent_edition_not_a_sha",
        ),
        pytest.param(
            row('key = "line=x"\nkind = "item"\nlabels = ["X"]\nfollows = "line=total"'),
            [("rowschema_bad_value", f"{TABLE}:row 1")],
            id="follows_on_a_row_with_a_label",
        ),
        pytest.param(
            row('key = "line=x"\nkind = "item"\nlabel = "X"'),
            [("rowschema_unknown_field", f"{TABLE}:row 1")],
            id="unknown_field",
        ),
        pytest.param(
            row('key = "line=x"\nkind = "item"\nlabels = ["X"]')
            + '\n[[row]]\nkey = "line=x"\nkind = "item"\nlabels = ["Y"]\n',
            [("rowschema_duplicate_key", f"{TABLE}:line=x")],
            id="one_key_twice",
        ),
    ],
)
def test_load_row_schema_refuses_text_that_breaks_a_rule(
    text: str, expected: list[tuple[str, str]]
) -> None:
    assert codes(load_row_schema(TABLE, text)) == expected
