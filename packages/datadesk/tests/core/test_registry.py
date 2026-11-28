import pytest

from checkedtables.refs import Sha256
from checkedtables.table import Severity
from datadesk.core.registry.load import Refused, load_registry
from datadesk.core.registry.model import (
    Alias,
    Dated,
    Entity,
    EntityKind,
    LookupScope,
    Registry,
    Relation,
    RelationKind,
    Residual,
)
from datadesk.core.registry.resolve import labels_for

FY2022_Q1 = Sha256("7c4a2e5abb00a5084cdb24fb35325cd1f2cdee42cfd9b30cf7c62c46c2f22918")
FY2022_Q2 = Sha256("1" * 64)
DEPARTMENTS = """
[[department]]
id = "phl_dept_fleet_management"
names = [{ value = "Fleet Services", first_fy = 2022 }]

[[department]]
id = "phl_dept_office_of_arts_and_culture"
names = [
  { value = "Office of Arts and Culture", last_fy = 2025 },
  { value = "Creative Philadelphia", first_fy = 2026 },
]

[[department]]
id = "phl_dept_streets"
names = [{ value = "Streets" }]
codes = [{ value = "13", first_fy = 2008, last_fy = 2013 }]
"""
GROUPS = """
[[group]]
id = "phl_group_streets_sanitation"
members = ["phl_dept_streets", "phl_dept_streets_sanitation"]
"""
FUNDS = """
[[fund]]
id = "phl_fund_other"
names = [{ value = "Other" }]
residual = "yes"
"""
ALIASES = f"""
[[alias]]
entity = "phl_dept_fleet_management"
label = "Fleet Management"
tables = ["qcmr_positions"]
editions = ["{FY2022_Q1}"]

[[alias]]
entity = "phl_group_streets_sanitation"
label = "Streets"
tables = ["qcmr_positions"]
first_fy = 2022
last_fy = 2025
"""
RELATIONS = """
[[relation]]
kind = "reported_under"
source = "phl_dept_aviation"
target = "phl_dept_commerce"
first_fy = 2022
last_fy = 2023
evidence = "FY2024 P-1 footnote"
"""
TEXTS = (
    ("registry/departments.toml", DEPARTMENTS),
    ("registry/groups.toml", GROUPS),
    ("registry/funds.toml", FUNDS),
    ("registry/aliases/qcmr_positions.toml", ALIASES),
    ("registry/relations.toml", RELATIONS),
)


def registry() -> Registry:
    loaded = load_registry(TEXTS)
    assert isinstance(loaded, Registry), loaded
    return loaded


def scope(fiscal_year: int, edition: Sha256 = FY2022_Q2, table: str = "qcmr_positions"):
    return LookupScope(table, fiscal_year, edition)


def codes(loaded: Registry | Refused) -> list[tuple[str, str]]:
    assert isinstance(loaded, Refused), loaded
    assert {finding.severity for finding in loaded.findings} == {Severity.BLOCK}
    return [(finding.code, finding.subject) for finding in loaded.findings]


def test_load_registry_reads_each_kind_of_entity_its_aliases_and_relations() -> None:
    assert registry() == Registry(
        entities=(
            Entity(
                "phl_dept_fleet_management",
                EntityKind.DEPARTMENT,
                (Dated("Fleet Services", 2022, None),),
            ),
            Entity(
                "phl_dept_office_of_arts_and_culture",
                EntityKind.DEPARTMENT,
                (
                    Dated("Office of Arts and Culture", None, 2025),
                    Dated("Creative Philadelphia", 2026, None),
                ),
            ),
            Entity(
                "phl_dept_streets",
                EntityKind.DEPARTMENT,
                (Dated("Streets", None, None),),
                codes=(Dated("13", 2008, 2013),),
            ),
            Entity(
                "phl_group_streets_sanitation",
                EntityKind.GROUP,
                (),
                members=("phl_dept_streets", "phl_dept_streets_sanitation"),
            ),
            Entity(
                "phl_fund_other",
                EntityKind.FUND,
                (Dated("Other", None, None),),
                residual=Residual.YES,
            ),
        ),
        relations=(
            Relation(
                RelationKind.REPORTED_UNDER,
                "phl_dept_aviation",
                "phl_dept_commerce",
                2022,
                2023,
                None,
                "FY2024 P-1 footnote",
            ),
        ),
        aliases=(
            Alias(
                "phl_dept_fleet_management",
                "Fleet Management",
                ("qcmr_positions",),
                None,
                None,
                (FY2022_Q1,),
            ),
            Alias("phl_group_streets_sanitation", "Streets", ("qcmr_positions",), 2022, 2025),
        ),
    )


def test_no_text_is_the_empty_registry() -> None:
    assert load_registry(()) == Registry((), (), ())


def test_a_name_outside_its_fiscal_years_gives_no_label() -> None:
    arts = "phl_dept_office_of_arts_and_culture"
    assert labels_for(registry(), arts, scope(2025)) == ("Office of Arts and Culture",)
    assert labels_for(registry(), arts, scope(2026)) == ("Creative Philadelphia",)
    assert labels_for(registry(), "phl_dept_fleet_management", scope(2021)) == ()
    assert labels_for(registry(), "phl_dept_streets", scope(1990)) == ("Streets",)


def test_an_alias_holds_only_in_its_editions() -> None:
    fleet = "phl_dept_fleet_management"
    assert labels_for(registry(), fleet, scope(2022, FY2022_Q1)) == (
        "Fleet Services",
        "Fleet Management",
    )
    assert labels_for(registry(), fleet, scope(2022, FY2022_Q2)) == ("Fleet Services",)


def test_an_alias_holds_only_in_its_tables_and_its_years() -> None:
    group = "phl_group_streets_sanitation"
    assert labels_for(registry(), group, scope(2022)) == ("Streets",)
    assert labels_for(registry(), group, scope(2025)) == ("Streets",)
    assert labels_for(registry(), group, scope(2021)) == ()
    assert labels_for(registry(), group, scope(2026)) == ()
    assert labels_for(registry(), group, scope(2025, table="qcmr_obligations")) == ()
    fleet = scope(2022, FY2022_Q1, table="qcmr_obligations")
    assert labels_for(registry(), "phl_dept_fleet_management", fleet) == ("Fleet Services",)


def test_an_entity_the_registry_lacks_has_no_label() -> None:
    assert labels_for(registry(), "phl_dept_aviation", scope(2024)) == ()


def test_an_alias_needs_a_table() -> None:
    with pytest.raises(ValueError, match="Streets"):
        Alias("phl_group_streets_sanitation", "Streets", (), None, None)


@pytest.mark.parametrize(
    ("texts", "expected"),
    [
        pytest.param(
            (("departments.toml", "[[department]\n"),),
            [("registry_not_toml", "departments.toml")],
            id="not_toml",
        ),
        pytest.param(
            (("departments.toml", '[[departmnet]]\nid = "phl_dept_law"\n'),),
            [("registry_unknown_field", "departments.toml")],
            id="unknown_array",
        ),
        pytest.param(
            (("departments.toml", 'department = "phl_dept_law"\n'),),
            [("registry_wrong_type", "departments.toml:department")],
            id="not_an_array_of_tables",
        ),
        pytest.param(
            (("departments.toml", '[[department]]\nnames = [{ value = "Law" }]\n'),),
            [("registry_missing_field", "departments.toml:department 1")],
            id="no_id",
        ),
        pytest.param(
            (("departments.toml", '[[department]]\nid = "phl_dept_law"\nname = "Law"\n'),),
            [("registry_unknown_field", "departments.toml:department 1")],
            id="unknown_field",
        ),
        pytest.param(
            (("departments.toml", '[[department]]\nid = "phl_dept_law"\nnames = ["Law"]\n'),),
            [("registry_wrong_type", "departments.toml:department 1")],
            id="name_not_a_table",
        ),
        pytest.param(
            (("groups.toml", '[[group]]\nid = "phl_group_x"\nmembers = ["phl_dept_law", 7]\n'),),
            [("registry_wrong_type", "groups.toml:group 1")],
            id="member_not_a_string",
        ),
        pytest.param(
            (("departments.toml", "[[department]]\nid = 7\n"),),
            [("registry_wrong_type", "departments.toml:department 1")],
            id="id_not_a_string",
        ),
        pytest.param(
            (
                (
                    "departments.toml",
                    '[[department]]\nid = "phl_dept_law"\nnames = [{ value = "Law", '
                    "first_fy = true }]\n",
                ),
            ),
            [("registry_wrong_type", "departments.toml:department 1")],
            id="year_not_an_integer",
        ),
        pytest.param(
            (("funds.toml", '[[fund]]\nid = "phl_fund_other"\nresidual = "maybe"\n'),),
            [("registry_bad_value", "funds.toml:fund 1")],
            id="residual_not_a_member",
        ),
        pytest.param(
            (("aliases.toml", ALIASES.replace(FY2022_Q1, "FY2022 Q1")),),
            [("registry_bad_value", "aliases.toml:alias 1")],
            id="edition_not_a_sha",
        ),
        pytest.param(
            (("aliases.toml", ALIASES.replace(FY2022_Q1, FY2022_Q1.upper())),),
            [("registry_bad_value", "aliases.toml:alias 1")],
            id="edition_in_capitals",
        ),
        pytest.param(
            (("aliases.toml", ALIASES.replace('tables = ["qcmr_positions"]', "tables = []", 1)),),
            [("registry_bad_value", "aliases.toml:alias 1")],
            id="alias_with_no_table",
        ),
        pytest.param(
            (("relations.toml", RELATIONS.replace("reported_under", "renamed")),),
            [("registry_bad_value", "relations.toml:relation 1")],
            id="relation_kind_not_a_member",
        ),
        pytest.param(
            (("a.toml", DEPARTMENTS), ("b.toml", DEPARTMENTS.split("\n\n")[0])),
            [("registry_duplicate_id", "phl_dept_fleet_management")],
            id="one_id_twice",
        ),
        pytest.param(
            (("departments.toml", "[[department]\n"), ("aliases.toml", "[[alias]]\n")),
            [
                ("registry_not_toml", "departments.toml"),
                ("registry_missing_field", "aliases.toml:alias 1"),
            ],
            id="every_file_is_read",
        ),
    ],
)
def test_load_registry_refuses_text_that_breaks_a_rule(
    texts: tuple[tuple[str, str], ...], expected: list[tuple[str, str]]
) -> None:
    assert codes(load_registry(texts)) == expected


def test_refused_needs_a_finding() -> None:
    with pytest.raises(ValueError, match="finding"):
        Refused(())
