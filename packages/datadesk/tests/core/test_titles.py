from datetime import date, timedelta

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from datadesk.core.domain import EditionKey, Period
from datadesk.core.listings.titles import TITLE_RULES, qcmr_title
from datadesk.core.periods import MONTHS, fiscal_quarter

NAMES = {number: name.capitalize() for name, number in MONTHS.items()}
DAYS = st.dates(min_value=date(2000, 1, 1), max_value=date(2100, 12, 31))
QUARTER_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))


def qcmr(start: date, end: date) -> EditionKey:
    return EditionKey("qcmr", Period(start, end))


def report_title(day: date, manager: str = "Managers", dash: str = "-") -> str:
    return f"Quarterly City {manager} Report {dash} {NAMES[day.month]} {day.day}, {day.year}"


@pytest.mark.parametrize(
    ("title", "reading"),
    [
        pytest.param(
            "Quarterly City Managers Report - March 31, 2026",
            qcmr(date(2026, 1, 1), date(2026, 3, 31)),
            id="a_report",
        ),
        pytest.param(
            "Quarterly City Manager's Report - December 31, 2022",
            qcmr(date(2022, 10, 1), date(2022, 12, 31)),
            id="managers_with_an_apostrophe",
        ),
        pytest.param(
            "Quarterly City Managers Report – March 31, 2021",
            qcmr(date(2021, 1, 1), date(2021, 3, 31)),
            id="an_en_dash_as_the_feed_prints_before_june_2021",
        ),
        pytest.param(
            "Quarterly City Managers Report Infographic - September 30, 2024",
            "infographic",
            id="an_infographic",
        ),
        pytest.param(
            "Quarterly City Managers Report Infographic – FY20Q2 General Fund",
            "infographic",
            id="an_infographic_with_no_date",
        ),
        pytest.param(
            "Executive Summary – FY18 Q1 Quarterly City Managers Report",
            "unrelated",
            id="an_executive_summary",
        ),
        pytest.param(
            "Quarterly City Managers Report Revised - June 30, 2025",
            "unrelated",
            id="words_between_report_and_the_date",
        ),
        pytest.param(
            "Quarterly City Managers Report - March 30, 2026",
            "not_a_quarter_end",
            id="a_date_that_is_not_a_quarter_end",
        ),
        pytest.param(
            "Quarterly City Managers Report - Smarch 31, 2026",
            "not_a_quarter_end",
            id="a_month_that_is_not_a_month",
        ),
    ],
)
def test_qcmr_title_reads_an_edition_or_a_skip_reason(
    title: str, reading: EditionKey | str
) -> None:
    assert qcmr_title(title) == reading


def test_title_rules_hold_the_qcmr_rule() -> None:
    assert TITLE_RULES["qcmr"] is qcmr_title


@given(DAYS, st.sampled_from(QUARTER_ENDS))
def test_a_report_title_reads_as_the_fiscal_quarter_it_ends(
    day: date, month_day: tuple[int, int]
) -> None:
    end = date(day.year, *month_day)
    edition = qcmr_title(report_title(end))
    assert isinstance(edition, EditionKey)
    assert edition.series == "qcmr"
    assert edition.period.end == end
    assert fiscal_quarter(edition.period.start) == fiscal_quarter(end)
    assert fiscal_quarter(edition.period.start - timedelta(days=1)) != fiscal_quarter(end)
    assert qcmr_title(report_title(end, manager="Manager's", dash="–")) == edition


@given(DAYS)
def test_a_report_title_dated_on_any_other_day_is_not_a_quarter_end(day: date) -> None:
    assume((day.month, day.day) not in QUARTER_ENDS)
    assert qcmr_title(report_title(day)) == "not_a_quarter_end"
