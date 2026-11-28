from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from checkedtables.refs import Sha256
from checkedtables.table import RowKey, TableId
from datadesk.core.domain import DocumentVersion, EditionKey, Period
from datadesk.core.measures import (
    Basis,
    Derived,
    MeasureSet,
    MeasureSpec,
    NotPublished,
    RowMeasure,
    Scope,
    Stated,
    Subject,
    description,
    measure_for,
    period_of,
    scope_for,
    subject_of,
)
from datadesk.core.records import EditionNote, NoteKind
from datadesk.core.vocab import ALL, Dim, How, Kind, Quantity, Version, Window

SHA = Sha256("a" * 64)
OTHER = Sha256("b" * 64)
TABLE = TableId("qcmr_cash")
Q2_FY2024 = Period(date(2023, 10, 1), date(2023, 12, 31))
Q3_FY2024 = Period(date(2024, 1, 1), date(2024, 3, 31))
Q4_FY2024 = Period(date(2024, 4, 1), date(2024, 6, 30))
ACTUAL = Stated(Kind.ACTUAL, Window.FISCAL_YEAR)
GENERAL = ((Dim.FUND, "phl_fund_general"),)


def version(period: Period) -> DocumentVersion:
    return DocumentVersion(
        sha256=SHA,
        edition=EditionKey("qcmr", period),
        listed_at="20240801000000",
        urls=(),
        title="Quarterly City Managers Report",
        printed_period=period,
        supersedes=None,
    )


def scope(period: Period) -> Scope:
    return Scope(version(period).edition, TABLE, frozenset(), period.end)


def note(kind: NoteKind, value: str, sha: Sha256 = SHA, id: str = "n1") -> EditionNote:
    return EditionNote(id, kind, sha, 1, "Actual through April", value, "the cover says so")


def spec(column: str, meaning: Stated | Derived | NotPublished, basis: Basis) -> MeasureSpec:
    return MeasureSpec(column, meaning, "USD", Decimal(1), basis)


@pytest.mark.parametrize(
    ("meaning", "message"),
    [
        pytest.param(
            lambda: Stated(Kind.BUDGET, Window.FISCAL_YEAR),
            "a budget column has a version",
            id="a_budget_with_no_version",
        ),
        pytest.param(
            lambda: Stated(Kind.ACTUAL, Window.QUARTER, version=Version.ADOPTED),
            "only a budget column has one",
            id="an_actual_with_a_version",
        ),
        pytest.param(
            lambda: Stated(Kind.ACTUAL, Window.QUARTER, month=3),
            "only a month column names a fiscal month",
            id="a_fiscal_month_on_a_quarter",
        ),
        pytest.param(
            lambda: Stated(Kind.ACTUAL, Window.MONTH, month=13),
            "fiscal month 13",
            id="a_thirteenth_fiscal_month",
        ),
        pytest.param(
            lambda: Stated(Kind.ACTUAL, Window.MONTH, month=0),
            "fiscal month 0",
            id="a_fiscal_month_zero",
        ),
        pytest.param(
            lambda: Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=1),
            "a later year than its edition",
            id="a_year_after_the_edition",
        ),
        pytest.param(
            lambda: Derived(How.DIFFERENCE, of=("adopted",)),
            "a difference takes two or more operands",
            id="a_difference_of_one_column",
        ),
        pytest.param(
            lambda: Derived(How.SHARE, of=("part", "whole")),
            "a share takes one operand",
            id="a_share_of_two_columns",
        ),
        pytest.param(
            lambda: Derived(How.RATIO, of=("a", "b", "c")),
            "ratio takes two operands",
            id="a_ratio_of_three_columns",
        ),
    ],
)
def test_a_meaning_that_breaks_a_rule_of_its_type_is_refused(meaning: object, message: str) -> None:
    assert callable(meaning)
    with pytest.raises(ValueError, match=message):
        meaning()


@pytest.mark.parametrize(
    ("stated", "period", "covers"),
    [
        pytest.param(
            Stated(Kind.ACTUAL, Window.QUARTER),
            Q4_FY2024,
            Period(date(2024, 4, 1), date(2024, 6, 30)),
            id="the_quarter",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.QUARTER, year=-1),
            Q2_FY2024,
            Period(date(2022, 10, 1), date(2022, 12, 31)),
            id="the_quarter_a_year_back",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1),
            Q2_FY2024,
            Period(date(2022, 7, 1), date(2023, 6, 30)),
            id="the_fiscal_year_before",
        ),
        pytest.param(
            Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED),
            Q3_FY2024,
            Period(date(2023, 7, 1), date(2024, 6, 30)),
            id="the_fiscal_year",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.FISCAL_YTD),
            Q2_FY2024,
            Period(date(2023, 7, 1), date(2023, 12, 31)),
            id="july_to_december_of_fy2024_is_calendar_2023",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.FISCAL_YTD, year=-1),
            Q3_FY2024,
            Period(date(2022, 7, 1), date(2023, 3, 31)),
            id="the_fiscal_year_to_date_a_year_back",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.CALENDAR_YTD),
            Q4_FY2024,
            Period(date(2024, 1, 1), date(2024, 6, 30)),
            id="the_calendar_year_to_date",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.MONTH),
            Q2_FY2024,
            Period(date(2023, 12, 1), date(2023, 12, 31)),
            id="the_edition_month",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.MONTH, month=1),
            Q2_FY2024,
            Period(date(2023, 7, 1), date(2023, 7, 31)),
            id="fiscal_month_1_is_july",
        ),
        pytest.param(
            Stated(Kind.PROJECTION, Window.MONTH, month=8),
            Q2_FY2024,
            Period(date(2024, 2, 1), date(2024, 2, 29)),
            id="fiscal_month_8_is_february_of_a_leap_year",
        ),
        pytest.param(
            Stated(Kind.PROJECTION, Window.MONTH, month=12, year=-1),
            Q2_FY2024,
            Period(date(2023, 6, 1), date(2023, 6, 30)),
            id="fiscal_month_12_a_year_back",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.CALENDAR_YEAR),
            Q2_FY2024,
            Period(date(2023, 1, 1), date(2023, 12, 31)),
            id="the_calendar_year",
        ),
        pytest.param(
            Stated(Kind.ACTUAL, Window.TAX_YEAR, year=-2),
            Q4_FY2024,
            Period(date(2022, 1, 1), date(2022, 12, 31)),
            id="the_tax_year_two_back",
        ),
    ],
)
def test_each_window_covers_the_days_of_its_year_basis(
    stated: Stated, period: Period, covers: Period
) -> None:
    assert period_of(stated, scope(period)) == covers


def test_a_level_keeps_only_its_end_date_and_an_amount_keeps_its_span() -> None:
    quarter_end = spec("actual", Stated(Kind.ACTUAL, Window.QUARTER), Basis.POINT)
    year_to_date = spec("ytd", Stated(Kind.ACTUAL, Window.FISCAL_YTD), Basis.FLOW)
    assert subject_of(quarter_end, scope(Q2_FY2024)) == Subject(
        Kind.ACTUAL, Version.NONE, None, (), "USD", None, date(2023, 12, 31)
    )
    assert subject_of(year_to_date, scope(Q2_FY2024)) == Subject(
        Kind.ACTUAL, Version.NONE, None, (), "USD", date(2023, 7, 1), date(2023, 12, 31)
    )


def test_the_year_to_date_of_q4_is_one_subject_with_the_prior_year_of_the_next_q1() -> None:
    year_to_date = spec("ytd", Stated(Kind.ACTUAL, Window.FISCAL_YTD), Basis.FLOW)
    prior = spec("prior", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1), Basis.FLOW)
    q1_fy2025 = Period(date(2024, 7, 1), date(2024, 9, 30))
    assert subject_of(year_to_date, scope(Q4_FY2024)) == subject_of(prior, scope(q1_fy2025))
    assert subject_of(year_to_date, scope(Q3_FY2024)) != subject_of(prior, scope(q1_fy2025))


def test_a_computed_or_unpublished_column_has_no_subject() -> None:
    difference = spec("gap", Derived(How.DIFFERENCE, of=("a", "b")), Basis.FLOW)
    hidden = spec("famis", NotPublished("SUPOP-Q15: what the column holds is unknown"), Basis.FLOW)
    assert subject_of(difference, scope(Q2_FY2024)) is None
    assert subject_of(hidden, scope(Q2_FY2024)) is None


def test_the_description_tells_apart_every_field_but_nothing_else() -> None:
    general = replace(ACTUAL, dims=GENERAL)
    assert description(general) == description(
        Stated(Kind.ACTUAL, Window.FISCAL_YEAR, dims=GENERAL)
    )
    others = (
        ACTUAL,
        replace(general, dims=((Dim.FUND, ALL),)),
        replace(general, year=-1),
        replace(general, window=Window.FISCAL_YTD),
        replace(general, kind=Kind.PROJECTION),
        replace(general, quantity=Quantity.CASH),
        Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED, dims=GENERAL),
        Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.TARGET, dims=GENERAL),
        Stated(Kind.ACTUAL, Window.MONTH, month=2, dims=GENERAL),
        Stated(Kind.ACTUAL, Window.MONTH, month=3, dims=GENERAL),
        Derived(How.DIFFERENCE, of=("adopted", "actual")),
        Derived(How.DIFFERENCE, of=("target", "actual")),
        NotPublished("one reason"),
        NotPublished("another reason"),
    )
    descriptions = [description(meaning) for meaning in (general, *others)]
    assert len(set(descriptions)) == len(descriptions)


def test_a_row_override_replaces_the_column_spec_on_the_rows_that_carry_its_parts() -> None:
    adopted = spec(
        "adopted", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED), Basis.FLOW
    )
    positions = replace(adopted, unit="positions", basis=Basis.POINT)
    measures = MeasureSet(
        (adopted,), (RowMeasure((("metric", "positions"),), "adopted", positions),)
    )
    counted = RowKey.of(metric="positions", section="phl_dept_police")
    paid = RowKey.of(metric="class_100", section="phl_dept_police")
    assert measure_for(measures, counted, "adopted") == positions
    assert measure_for(measures, paid, "adopted") == adopted


def test_two_overrides_that_match_one_row_are_refused() -> None:
    adopted = spec(
        "adopted", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED), Basis.FLOW
    )
    positions = replace(adopted, unit="positions", basis=Basis.POINT)
    measures = MeasureSet(
        (adopted,),
        (
            RowMeasure((("metric", "positions"),), "adopted", positions),
            RowMeasure((("section", "phl_dept_police"),), "adopted", positions),
        ),
    )
    with pytest.raises(ValueError, match="two overrides of adopted"):
        measure_for(measures, RowKey.of(metric="positions", section="phl_dept_police"), "adopted")


def test_a_column_with_no_spec_is_a_key_error() -> None:
    with pytest.raises(KeyError, match="remaining"):
        measure_for(MeasureSet(()), RowKey.of(line="total"), "remaining")


def test_the_scope_of_an_edition_with_no_cutoff_is_actual_through_its_period_end() -> None:
    printed = frozenset({"adopted", "actual"})
    notes = (
        note(NoteKind.CUTOFF, "2024-04", sha=OTHER),
        note(NoteKind.PRINTED_PERIOD, "2024-06-30"),
    )
    assert scope_for(version(Q4_FY2024), TABLE, printed, notes) == (
        Scope(version(Q4_FY2024).edition, TABLE, printed, date(2024, 6, 30)),
        frozenset(),
    )


def test_a_cutoff_note_of_the_file_sets_the_last_actual_day_and_is_used() -> None:
    scope_of, used = scope_for(
        version(Q4_FY2024), TABLE, frozenset(), (note(NoteKind.CUTOFF, "2024-04", id="cut"),)
    )
    assert scope_of.actual_through == date(2024, 4, 30)
    assert used == frozenset({"cut"})


@pytest.mark.parametrize("value", ["2024-4", "2024-13", "April 2024", "2024-04-30"])
def test_a_cutoff_that_names_no_month_is_refused(value: str) -> None:
    with pytest.raises(ValueError, match="cutoff"):
        scope_for(version(Q4_FY2024), TABLE, frozenset(), (note(NoteKind.CUTOFF, value),))


def test_two_cutoff_notes_of_one_file_are_refused() -> None:
    notes = (note(NoteKind.CUTOFF, "2024-04"), note(NoteKind.CUTOFF, "2024-05", id="n2"))
    with pytest.raises(ValueError, match="n1, n2"):
        scope_for(version(Q4_FY2024), TABLE, frozenset(), notes)
