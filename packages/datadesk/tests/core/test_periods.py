from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from datadesk.core.domain import Period
from datadesk.core.periods import MONTHS, fiscal_period, fiscal_quarter, fiscal_year_of
from datadesk.core.vocab import Window

DAYS = st.dates(min_value=date(1900, 1, 1), max_value=date(2199, 12, 30))


def test_months_maps_each_english_month_name_to_its_number() -> None:
    assert MONTHS["january"] == 1
    assert MONTHS["september"] == 9
    assert MONTHS["december"] == 12
    assert sorted(MONTHS.values()) == list(range(1, 13))


def test_july_starts_the_next_fiscal_year() -> None:
    assert fiscal_year_of(date(2025, 6, 30)) == 2025
    assert fiscal_year_of(date(2025, 7, 1)) == 2026
    assert fiscal_year_of(date(2025, 12, 31)) == 2026
    assert fiscal_year_of(date(2026, 1, 1)) == 2026


@pytest.mark.parametrize(
    ("period_end", "quarter"),
    [
        pytest.param(date(2021, 9, 30), (2022, 1), id="september_ends_q1_of_the_next_year"),
        pytest.param(date(2021, 12, 31), (2022, 2), id="december_ends_q2_of_the_next_year"),
        pytest.param(date(2022, 3, 31), (2022, 3), id="march_ends_q3"),
        pytest.param(date(2022, 6, 30), (2022, 4), id="june_ends_q4"),
    ],
)
def test_fiscal_quarter_of_each_quarter_end(period_end: date, quarter: tuple[int, int]) -> None:
    assert fiscal_quarter(period_end) == quarter


@given(DAYS)
def test_the_fiscal_year_turns_on_july_first_alone(day: date) -> None:
    following = day + timedelta(days=1)
    turns = (following.month, following.day) == (7, 1)
    assert fiscal_year_of(following) == fiscal_year_of(day) + turns


@given(DAYS)
def test_the_fiscal_quarter_turns_on_the_first_of_january_april_july_and_october(
    day: date,
) -> None:
    following = day + timedelta(days=1)
    turns = following.day == 1 and following.month in (1, 4, 7, 10)
    assert (fiscal_quarter(following) != fiscal_quarter(day)) == turns
    assert fiscal_quarter(day)[0] == fiscal_year_of(day)


@pytest.mark.parametrize(
    ("kind", "label_year", "months", "period"),
    [
        pytest.param(
            Window.FISCAL_YTD,
            2026,
            (7, 12),
            Period(date(2025, 7, 1), date(2025, 12, 31)),
            id="july_to_december_of_fy2026_is_calendar_2025",
        ),
        pytest.param(
            Window.FISCAL_YEAR,
            2026,
            (7, 6),
            Period(date(2025, 7, 1), date(2026, 6, 30)),
            id="the_fiscal_year_runs_july_to_june",
        ),
        pytest.param(
            Window.FISCAL_YTD,
            2024,
            (7, 2),
            Period(date(2023, 7, 1), date(2024, 2, 29)),
            id="a_fiscal_year_to_date_ends_on_the_last_day_of_a_leap_february",
        ),
        pytest.param(
            Window.QUARTER,
            2026,
            (4, 6),
            Period(date(2026, 4, 1), date(2026, 6, 30)),
            id="a_quarter_takes_the_calendar_year",
        ),
        pytest.param(
            Window.CALENDAR_YTD,
            2025,
            (1, 9),
            Period(date(2025, 1, 1), date(2025, 9, 30)),
            id="the_calendar_year_to_date",
        ),
        pytest.param(
            Window.MONTH,
            2025,
            (12, 12),
            Period(date(2025, 12, 1), date(2025, 12, 31)),
            id="december_takes_the_calendar_year",
        ),
        pytest.param(
            Window.TAX_YEAR,
            2023,
            (1, 12),
            Period(date(2023, 1, 1), date(2023, 12, 31)),
            id="the_tax_year",
        ),
    ],
)
def test_fiscal_period_reads_the_label_year_in_the_basis_of_its_window(
    kind: Window, label_year: int, months: tuple[int, int], period: Period
) -> None:
    assert fiscal_period(kind, label_year, months) == period


@pytest.mark.parametrize(
    ("kind", "months", "message"),
    [
        pytest.param(Window.MONTH, (0, 1), "not 1 to 12", id="month_zero"),
        pytest.param(Window.MONTH, (12, 13), "not 1 to 12", id="month_thirteen"),
        pytest.param(Window.QUARTER, (10, 3), "ends before it starts", id="a_calendar_span_back"),
        pytest.param(Window.FISCAL_YEAR, (1, 7), "ends before it starts", id="a_fiscal_span_back"),
    ],
)
def test_fiscal_period_refuses_a_month_out_of_range_and_a_span_that_runs_back(
    kind: Window, months: tuple[int, int], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        fiscal_period(kind, 2025, months)
