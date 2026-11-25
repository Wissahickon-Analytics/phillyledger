from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from datadesk.core.periods import MONTHS, fiscal_quarter, fiscal_year_of

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
