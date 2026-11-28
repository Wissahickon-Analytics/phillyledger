import re
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import date
from decimal import Decimal
from functools import cache

import pytest
from tests.test_registry_data import registry, versions

from checkedtables.columns import Era
from checkedtables.kinds import Presence, ValueKind
from checkedtables.table import TableId
from datadesk.core.domain import DocumentVersion
from datadesk.core.measures import (
    Basis,
    Derived,
    Meaning,
    MeasureSet,
    MeasureSpec,
    NotPublished,
    RowMeasure,
    Scope,
    Stated,
    description,
    scope_for,
    subject_of,
)
from datadesk.core.records import EditionNote, NoteKind
from datadesk.core.registry.model import EntityKind
from datadesk.core.tables.catalog import TABLES, TableEntry, entry
from datadesk.core.vocab import ALL, DIM_VALUES, Dim, How, Kind, Version, Window

# Design section 5.1, in the order the page prints them.
POSITIONS = (
    "prior_general",
    "prior_other",
    "prior_total",
    "adopted_general",
    "adopted_other",
    "adopted_total",
    "actual_general",
    "actual_other",
    "actual_total",
    "over_under",
)
MEASURED = frozenset({ValueKind.MONEY, ValueKind.COUNT, ValueKind.PERCENT})
PERCENT_HOWS = frozenset({How.PERCENT_CHANGE, How.RATIO, How.SHARE, How.ANNUAL_GROWTH})
GENERAL = ((Dim.FUND, "phl_fund_general"),)
OTHER = ((Dim.FUND, "phl_fund_other"),)
EVERY_FUND = ((Dim.FUND, ALL),)


@cache
def fund_ids() -> frozenset[str]:
    return frozenset(item.id for item in registry().entities if item.kind is EntityKind.FUND)


def edition_versions(table: TableEntry, era: Era) -> tuple[DocumentVersion, ...]:
    first, last = era.expected
    return tuple(
        version
        for version in versions().values()
        if version.edition.series == table.series
        and first <= version.edition.period.end <= (last or date.max)
    )


def cutoff(version: DocumentVersion, months: int) -> EditionNote:
    end = version.edition.period.end
    year, month = divmod(end.year * 12 + end.month - 1 + months, 12)
    value = f"{year:04d}-{month + 1:02d}"
    return EditionNote("cutoff", NoteKind.CUTOFF, version.sha256, 1, "", value, "a run's scope")


def scopes(table: TableEntry, era: Era) -> Iterator[Scope]:
    every = frozenset(column.name for column in era.columns)
    optional = [column.name for column in era.columns if column.presence is Presence.OPTIONAL]
    printed_sets = (every, *(every - {name} for name in optional))
    for version in edition_versions(table, era):
        for notes in ((), (cutoff(version, -1),), (cutoff(version, 1),)):
            for printed in printed_sets:
                yield scope_for(version, TableId(table.name), printed, notes)[0]


def scope_of(table: TableEntry, end: str) -> Scope:
    version = versions()[f"{table.series}:{end}:none"]
    (era,) = table.eras
    return scope_for(version, TableId(table.name), frozenset(c.name for c in era.columns), ())[0]


def regex_problems(era: Era) -> Iterator[str]:
    columns = [(f"{era.name}.{c.name}", c.caption, c.group) for c in era.columns]
    patterns = [
        *((f"{era.name} signature", p) for p in era.signature),
        *((f"{era.name} excludes", p) for p in era.excludes),
        *((f"{name} caption", caption) for name, caption, _ in columns),
        *((f"{name} group", group) for name, _, group in columns if group is not None),
    ]
    for where, pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as error:
            yield f"{where} {pattern!r} does not compile: {error}"
    for column in era.columns:
        if column.fmt.decimals is not None and column.fmt.decimals < 0:
            yield f"{era.name}.{column.name} prints {column.fmt.decimals} decimals"


def dims_of(meaning: Meaning) -> tuple[tuple[Dim, str], ...]:
    match meaning:
        case Stated() | Derived():
            return meaning.dims
        case NotPublished():
            return ()


def measure_problems(era: Era, measures: MeasureSet, funds: frozenset[str]) -> Iterator[str]:
    names = [column.name for column in era.columns if column.kind in MEASURED]
    described = [spec.column for spec in measures.columns]
    if described != names:
        yield f"{era.name}: the measures describe {described}, not the columns {names}"
    published = {s.column: s for s in measures.columns if not isinstance(s.meaning, NotPublished)}
    first_of: dict[tuple[object, ...], str] = {}
    for spec in published.values():
        key = description(spec.meaning)
        if key in first_of:
            yield f"{era.name}: {first_of[key]} and {spec.column} have one description"
        first_of.setdefault(key, spec.column)
    for spec in published.values():
        if isinstance(spec.meaning, Derived):
            for operand in spec.meaning.of:
                if operand not in published:
                    yield f"{era.name}: {spec.column} reads {operand}, which is no published column"
            if spec.meaning.how in PERCENT_HOWS and spec.unit != "percent":
                yield f"{era.name}: {spec.column} is a {spec.meaning.how} in {spec.unit}"
    for spec in (*measures.columns, *(row.spec for row in measures.rows)):
        for dim, value in dims_of(spec.meaning):
            if dim is Dim.FUND and value != ALL and value not in funds:
                yield f"{era.name}: {spec.column} names the fund {value}, which the registry lacks"
            if dim is not Dim.FUND and value not in DIM_VALUES[dim]:
                yield f"{era.name}: {spec.column} names the {dim} {value}, which is no value of it"
    for index, row in enumerate(measures.rows):
        if row.column not in names:
            yield f"{era.name}: an override names {row.column}, which is no column"
        for other in measures.rows[index + 1 :]:
            parts = dict(other.match)
            agree = all(parts.get(name, value) == value for name, value in row.match)
            if other.column == row.column and agree:
                yield f"{era.name}: two overrides of {row.column} match one row"


def catalog_problems(table: TableEntry, funds: frozenset[str]) -> list[str]:
    problems = set()
    for era in table.eras:
        problems.update(regex_problems(era))
        for scope in scopes(table, era):
            problems.update(measure_problems(era, table.measures(era, scope), funds))
    return sorted(problems)


def positions_with(column: str, change: Callable[[MeasureSpec], MeasureSpec]) -> TableEntry:
    table = entry("qcmr_positions")

    def measures(era: Era, scope: Scope) -> MeasureSet:
        got = table.measures(era, scope)
        specs = tuple(change(spec) if spec.column == column else spec for spec in got.columns)
        return replace(got, columns=specs)

    return replace(table, measures=measures)


def by_name(table: TableEntry, end: str) -> dict[str, MeasureSpec]:
    (era,) = table.eras
    return {spec.column: spec for spec in table.measures(era, scope_of(table, end)).columns}


def test_the_ten_positions_columns_have_ten_descriptions() -> None:
    table = entry("qcmr_positions")
    (era,) = table.eras
    seen = 0
    for scope in scopes(table, era):
        specs = table.measures(era, scope).columns
        assert [spec.column for spec in specs] == list(POSITIONS)
        assert [s.column for s in specs if isinstance(s.meaning, NotPublished)] == []
        assert len({description(spec.meaning) for spec in specs}) == len(POSITIONS)
        seen += 1
    assert seen == 60


def test_two_equal_descriptions_fail_the_catalog_rules() -> None:
    general = by_name(entry("qcmr_positions"), "2026-06-30")["adopted_general"]
    copy = positions_with("adopted_other", lambda spec: replace(spec, meaning=general.meaning))
    assert catalog_problems(copy, fund_ids()) == [
        "p1_ten_columns: adopted_general and adopted_other have one description"
    ]


def test_every_table_of_the_catalog_keeps_the_catalog_rules() -> None:
    assert [table.name for table in TABLES] == ["qcmr_positions"]
    for table in TABLES:
        assert catalog_problems(table, fund_ids()) == [], table.name


def test_each_positions_column_means_what_the_page_prints_over_it() -> None:
    prior = Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1)
    adopted = Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED)
    actual = Stated(Kind.ACTUAL, Window.QUARTER)
    meanings: dict[str, Meaning] = {
        f"{group}_{fund}": replace(meaning, dims=dims)
        for group, meaning in (("prior", prior), ("adopted", adopted), ("actual", actual))
        for fund, dims in (("general", GENERAL), ("other", OTHER), ("total", EVERY_FUND))
    }
    meanings["over_under"] = Derived(How.DIFFERENCE, of=("adopted_total", "actual_total"))
    expected = {
        name: MeasureSpec(name, meaning, "positions", Decimal(1), Basis.POINT)
        for name, meaning in meanings.items()
    }
    assert by_name(entry("qcmr_positions"), "2026-06-30") == expected


def test_a_positions_budget_with_no_version_and_an_actual_with_one_are_refused() -> None:
    specs = by_name(entry("qcmr_positions"), "2026-06-30")
    budget, actual = specs["adopted_general"].meaning, specs["actual_total"].meaning
    assert isinstance(budget, Stated) and isinstance(actual, Stated)
    with pytest.raises(ValueError, match="a budget column has a version"):
        replace(budget, version=Version.NONE)
    with pytest.raises(ValueError, match="only a budget column has one"):
        replace(actual, version=Version.ADOPTED)


def test_the_q4_fy2024_quarter_end_count_is_the_fy2025_q1_prior_year_count() -> None:
    table = entry("qcmr_positions")
    q4_fy2024, q1_fy2025 = by_name(table, "2024-06-30"), by_name(table, "2024-09-30")
    q2_fy2024 = by_name(table, "2023-12-31")
    for fund in ("general", "other", "total"):
        quarter_end = subject_of(q4_fy2024[f"actual_{fund}"], scope_of(table, "2024-06-30"))
        prior_year = subject_of(q1_fy2025[f"prior_{fund}"], scope_of(table, "2024-09-30"))
        mid_year = subject_of(q2_fy2024[f"actual_{fund}"], scope_of(table, "2023-12-31"))
        assert quarter_end is not None and quarter_end.end == date(2024, 6, 30)
        assert quarter_end == prior_year
        assert mid_year != prior_year


def test_an_operand_that_is_not_a_column_fails_the_catalog_rules() -> None:
    misread = Derived(How.DIFFERENCE, of=("adopted_total", "actual_totl"))
    copy = positions_with("over_under", lambda spec: replace(spec, meaning=misread))
    assert catalog_problems(copy, fund_ids()) == [
        "p1_ten_columns: over_under reads actual_totl, which is no published column"
    ]


def test_an_operand_that_is_not_published_fails_the_catalog_rules() -> None:
    copy = positions_with("actual_total", lambda spec: replace(spec, meaning=NotPublished("x")))
    assert catalog_problems(copy, fund_ids()) == [
        "p1_ten_columns: over_under reads actual_total, which is no published column"
    ]


def test_a_fund_id_that_the_registry_lacks_fails_the_catalog_rules() -> None:
    assert fund_ids() == {"phl_fund_general", "phl_fund_other"}
    assert catalog_problems(entry("qcmr_positions"), fund_ids() - {"phl_fund_other"}) == [
        f"p1_ten_columns: {group}_other names the fund phl_fund_other, which the registry lacks"
        for group in ("actual", "adopted", "prior")
    ]


def test_a_column_with_no_measure_fails_the_catalog_rules() -> None:
    table = entry("qcmr_positions")

    def measures(era: Era, scope: Scope) -> MeasureSet:
        got = table.measures(era, scope)
        return replace(got, columns=got.columns[:-1])

    assert catalog_problems(replace(table, measures=measures), fund_ids()) == [
        f"p1_ten_columns: the measures describe {list(POSITIONS[:-1])}, not the columns "
        f"{list(POSITIONS)}"
    ]


def test_a_percent_derived_in_positions_fails_the_catalog_rules() -> None:
    ratio = Derived(How.RATIO, of=("actual_total", "adopted_total"))
    copy = positions_with("over_under", lambda spec: replace(spec, meaning=ratio))
    assert catalog_problems(copy, fund_ids()) == [
        "p1_ten_columns: over_under is a ratio in positions"
    ]


def test_an_override_of_no_column_and_two_overrides_of_one_row_fail_the_catalog_rules() -> None:
    table = entry("qcmr_positions")
    spec = by_name(table, "2026-06-30")["actual_total"]
    rows = (
        RowMeasure((("dept", "phl_dept_police"),), "actual_total", spec),
        RowMeasure((("breakdown", "civilian"),), "actual_total", spec),
        RowMeasure((("dept", "phl_dept_fire"),), "actual_totl", spec),
    )

    def measures(era: Era, scope: Scope) -> MeasureSet:
        return replace(table.measures(era, scope), rows=rows)

    assert catalog_problems(replace(table, measures=measures), fund_ids()) == [
        "p1_ten_columns: an override names actual_totl, which is no column",
        "p1_ten_columns: two overrides of actual_total match one row",
    ]


def test_a_caption_that_does_not_compile_and_negative_decimals_fail_the_catalog_rules() -> None:
    table = entry("qcmr_positions")
    (era,) = table.eras
    first, second, *rest = era.columns
    broken = (
        replace(first, caption="General ("),
        replace(second, fmt=replace(second.fmt, decimals=-1)),
        *rest,
    )
    problems = catalog_problems(replace(table, eras=(replace(era, columns=broken),)), fund_ids())
    assert [problem.split(" ")[0] for problem in problems] == [
        "p1_ten_columns.prior_general",
        "p1_ten_columns.prior_other",
    ]
    assert "does not compile" in problems[0]
    assert problems[1] == "p1_ten_columns.prior_other prints -1 decimals"


def test_a_signature_that_does_not_compile_fails_the_catalog_rules() -> None:
    table = entry("qcmr_positions")
    (era,) = table.eras
    damaged = replace(era, signature=(*era.signature, r"(OVER"))
    (problem,) = catalog_problems(replace(table, eras=(damaged,)), fund_ids())
    assert problem.startswith("p1_ten_columns signature '(OVER' does not compile")


def test_entry_names_the_table_it_has_no_entry_for() -> None:
    with pytest.raises(KeyError, match="qcmr_cash"):
        entry("qcmr_cash")
