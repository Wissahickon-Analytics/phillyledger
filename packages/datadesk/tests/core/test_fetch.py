from dataclasses import replace
from datetime import date

import pytest

from checkedtables.table import Finding, Severity
from datadesk.core.domain import EditionKey, Period
from datadesk.core.fetch import confirm_period
from datadesk.core.records import EditionNote, NoteKind

Q1_PERIOD = Period(date(2021, 7, 1), date(2021, 9, 30))
Q2_PERIOD = Period(date(2021, 10, 1), date(2021, 12, 31))
FY2022_Q1 = EditionKey("qcmr", Q1_PERIOD)
FY2022_Q2 = EditionKey("qcmr", Q2_PERIOD)
FY2022_Q3 = EditionKey("qcmr", Period(date(2022, 1, 1), date(2022, 3, 31)))
FY2022_Q4 = EditionKey("qcmr", Period(date(2022, 4, 1), date(2022, 6, 30)))
Q1_SHA = "7c4a2e5abb00a5084cdb24fb35325cd1f2cdee42cfd9b30cf7c62c46c2f22918"
Q2_SHA = "401136b9ca279d46ab11e25a6d3da0980b30cbf147fc23976cc467519aa7aed7"
Q1_COVER = "QUARTERLY CITY MANAGERS REPORT\nFOR THE PERIOD ENDING SEPTEMBER 30, 2021\n"
Q2_COVER = "QUARTERLY CITY MANAGERS REPORT\nFOR THE PERIOD ENDING DECEMBER 31, 2021\n"
NOTE = EditionNote(
    id="qcmr-fy2022-q1-cover",
    kind=NoteKind.PRINTED_PERIOD,
    doc_sha256=Q1_SHA,
    page=1,
    printed="FOR THE PERIOD ENDING DECEMBER 31, 2021",
    value="2021-12-31",
    reason="the cover prints the next quarter",
)


def finding_code(result: Period | Finding, edition: EditionKey = FY2022_Q1) -> str:
    assert isinstance(result, Finding), result
    assert (result.severity, result.subject) == (Severity.BLOCK, edition.id())
    return result.code


@pytest.mark.parametrize(
    ("page1", "expected", "period"),
    [
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021",
            FY2022_Q1,
            Period(date(2021, 7, 1), date(2021, 9, 30)),
            id="september_opens_the_next_fiscal_year",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING DECEMBER 31, 2021",
            FY2022_Q2,
            Period(date(2021, 10, 1), date(2021, 12, 31)),
            id="december_is_in_the_next_fiscal_year",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING MARCH 31, 2022",
            FY2022_Q3,
            Period(date(2022, 1, 1), date(2022, 3, 31)),
            id="march",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING JUNE 30, 2022",
            FY2022_Q4,
            Period(date(2022, 4, 1), date(2022, 6, 30)),
            id="june_closes_the_fiscal_year",
        ),
        pytest.param(
            "FOR THE PERIOD\nENDING SEPTEMBER\n30, 2021",
            FY2022_Q1,
            Period(date(2021, 7, 1), date(2021, 9, 30)),
            id="a_phrase_broken_across_lines",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021",
            FY2022_Q1,
            Period(date(2021, 7, 1), date(2021, 9, 30)),
            id="a_phrase_spaced_with_no_break_spaces",
        ),
        pytest.param(
            "for the period ending September 30 2021",
            FY2022_Q1,
            Period(date(2021, 7, 1), date(2021, 9, 30)),
            id="lower_case_and_no_comma",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021\nPERIOD ENDING SEPTEMBER 30, 2021",
            FY2022_Q1,
            Period(date(2021, 7, 1), date(2021, 9, 30)),
            id="the_phrase_twice_with_one_date",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021\nDECEMBER 31, 2021",
            FY2022_Q1,
            Period(date(2021, 7, 1), date(2021, 9, 30)),
            id="a_bare_date_beside_the_phrase_is_not_read",
        ),
    ],
)
def test_confirm_period_returns_the_quarter_the_cover_prints(
    page1: str, expected: EditionKey, period: Period
) -> None:
    assert confirm_period("qcmr", page1, expected, ()) == period


@pytest.mark.parametrize(
    ("page1", "code"),
    [
        pytest.param(
            "QUARTERLY CITY MANAGERS REPORT\nSEPTEMBER 30, 2021",
            "period_unreadable",
            id="a_bare_date_and_no_phrase",
        ),
        pytest.param("(cid:38)(cid:51)(cid:52)(cid:3)", "period_unreadable", id="no_readable_text"),
        pytest.param("", "period_unreadable", id="an_empty_page"),
        pytest.param(
            "FOR THE PERIOD ENDING SMARCH 31, 2022",
            "period_unreadable",
            id="a_month_word_that_names_no_month",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 31, 2021",
            "period_unreadable",
            id="a_day_the_month_lacks",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 20211",
            "period_unreadable",
            id="a_year_run_on_into_another_digit",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021\nFOR THE PERIOD ENDING SMARCH 31, 2022",
            "period_unreadable",
            id="an_unreadable_phrase_beside_a_readable_one",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021\nFOR THE PERIOD ENDING DECEMBER 31, 2021",
            "period_ambiguous",
            id="two_phrases_with_two_dates",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 29, 2021",
            "period_not_a_quarter_end",
            id="a_date_that_is_not_a_quarter_end",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING JUNE 30, 2021",
            "period_mismatch",
            id="the_quarter_before",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2022",
            "period_mismatch",
            id="the_same_quarter_a_year_later",
        ),
    ],
)
def test_confirm_period_returns_a_finding_for_a_cover_it_cannot_confirm(
    page1: str, code: str
) -> None:
    assert finding_code(confirm_period("qcmr", page1, FY2022_Q1, ())) == code


@pytest.mark.parametrize(
    ("page1", "note"),
    [
        pytest.param(Q2_COVER, NOTE, id="a_note_on_page_1"),
        pytest.param(Q2_COVER, replace(NOTE, page=None), id="a_note_with_no_page"),
        pytest.param(
            "FOR THE PERIOD ENDING DECEMBER\n31, 2021",
            NOTE,
            id="a_page_that_spaces_the_text_another_way",
        ),
    ],
)
def test_a_printed_period_note_clears_a_mismatch(page1: str, note: EditionNote) -> None:
    assert confirm_period("qcmr", page1, FY2022_Q1, (note,)) == Period(
        date(2021, 10, 1), date(2021, 12, 31)
    )


@pytest.mark.parametrize(
    "note",
    [
        pytest.param(
            replace(NOTE, printed="FOR THE PERIOD ENDING DECEMBER 31, 2012"),
            id="a_note_whose_text_page_1_lacks",
        ),
        pytest.param(replace(NOTE, kind=NoteKind.CUTOFF), id="a_note_of_another_kind"),
        pytest.param(replace(NOTE, value="2021-09-30"), id="a_note_whose_value_is_not_printed"),
        pytest.param(replace(NOTE, page=2), id="a_note_on_another_page"),
    ],
)
def test_a_note_that_does_not_fit_the_cover_leaves_the_mismatch(note: EditionNote) -> None:
    assert finding_code(confirm_period("qcmr", Q2_COVER, FY2022_Q1, (note,))) == "period_mismatch"


def test_a_note_does_not_clear_a_date_that_is_not_a_quarter_end() -> None:
    page1 = "FOR THE PERIOD ENDING DECEMBER 30, 2021"
    note = replace(NOTE, printed=page1, value="2021-12-30")
    result = confirm_period("qcmr", page1, FY2022_Q1, (note,))
    assert finding_code(result) == "period_not_a_quarter_end"


def test_a_series_with_no_period_reader_is_unsupported() -> None:
    collections = EditionKey("collections_city", Period(date(2021, 9, 1), date(2021, 9, 30)))
    result = confirm_period("collections_city", "MONTH OF SEPTEMBER\nFY 2022", collections, ())
    assert finding_code(result, collections) == "period_unsupported"
