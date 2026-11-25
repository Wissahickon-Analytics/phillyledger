from dataclasses import replace
from datetime import date

import pytest

from checkedtables.table import Finding, Severity
from datadesk.core.domain import ArchiveIndex, DocumentVersion, EditionKey, Period
from datadesk.core.fetch import (
    Fetched,
    FetchPlan,
    Rejection,
    StoreObject,
    confirm_period,
    plan_fetch,
    qcmr_period,
)
from datadesk.core.index import render_index
from datadesk.core.records import EditionNote, NoteKind
from datadesk.core.watch import FetchRequest

Q1_PERIOD = Period(date(2021, 7, 1), date(2021, 9, 30))
Q2_PERIOD = Period(date(2021, 10, 1), date(2021, 12, 31))
FY2022_Q1 = EditionKey("qcmr", Q1_PERIOD)
FY2022_Q2 = EditionKey("qcmr", Q2_PERIOD)
FY2022_Q3 = EditionKey("qcmr", Period(date(2022, 1, 1), date(2022, 3, 31)))
FY2022_Q4 = EditionKey("qcmr", Period(date(2022, 4, 1), date(2022, 6, 30)))
Q1_SHA = "7c4a2e5abb00a5084cdb24fb35325cd1f2cdee42cfd9b30cf7c62c46c2f22918"
Q2_SHA = "401136b9ca279d46ab11e25a6d3da0980b30cbf147fc23976cc467519aa7aed7"
NEW_Q1_SHA = "f040b053395e239682f951df810d15eab029d43d92006312b23181d36ae0a1f1"
INDEX_FILE = "packages/datadesk/src/datadesk/data/index.jsonl"
EMPTY = ArchiveIndex(())
MEDIA = "https://www.phila.gov/media"
Q1_TITLE = "Quarterly City Managers Report - September 30, 2021"
Q1_URL = f"{MEDIA}/20211116102946/Quarterly-City-Managers-Report-September-30-2021.pdf"
Q1_REPOST_URL = f"{MEDIA}/20220301090000/Quarterly-City-Managers-Report-September-30-2021-1.pdf"
Q1_THIRD_URL = f"{MEDIA}/20220601090000/Quarterly-City-Managers-Report-September-30-2021-2.pdf"
Q1_EARLY_URL = f"{MEDIA}/20211101090000/Quarterly-City-Managers-Report-September-30-2021-0.pdf"
Q2_URL = f"{MEDIA}/20220217152839/Quarterly-City-Managers-Report-December-31-2021.pdf"
Q1_REQUEST = FetchRequest(FY2022_Q1, Q1_URL, Q1_TITLE, "20211116102946", "new")
Q1_REPOST = FetchRequest(FY2022_Q1, Q1_REPOST_URL, Q1_TITLE, "20220301090000", "revision")
Q1_THIRD = FetchRequest(FY2022_Q1, Q1_THIRD_URL, Q1_TITLE, "20220601090000", "revision")
Q1_EARLY = FetchRequest(FY2022_Q1, Q1_EARLY_URL, Q1_TITLE, "20211101090000", "revision")
Q2_REQUEST = FetchRequest(
    FY2022_Q2, Q2_URL, "Quarterly City Managers Report - December 31, 2021", "20220217152839", "new"
)
Q1 = DocumentVersion(Q1_SHA, FY2022_Q1, "20211116102946", (Q1_URL,), Q1_TITLE, Q1_PERIOD, None)
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
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021\nPERIOD ENDINGS",
            FY2022_Q1,
            Period(date(2021, 7, 1), date(2021, 9, 30)),
            id="a_longer_word_after_period_is_not_a_caption",
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
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021\nFOR THE PERIOD ENDING Märch 31, 2022",
            "period_unreadable",
            id="a_month_word_of_other_letters_beside_a_readable_phrase",
        ),
        pytest.param(
            "FOR THE PERIOD ENDING SEPTEMBER 30, 2021\nFOR THE PERIOD ENDING",
            "period_unreadable",
            id="a_caption_with_no_date_beside_a_readable_phrase",
        ),
        pytest.param(
            "SUBPERIOD ENDING SEPTEMBER 30, 2021",
            "period_unreadable",
            id="a_longer_word_in_place_of_the_caption",
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
        pytest.param(replace(NOTE, printed=""), id="a_blank_note"),
        pytest.param(
            replace(NOTE, printed="QUARTERLY CITY MANAGERS REPORT"),
            id="a_note_that_quotes_other_words",
        ),
        pytest.param(
            replace(NOTE, printed="FOR THE PERIOD ENDING DECEMBER 31 2021"),
            id="a_note_that_reads_as_the_period_in_words_page_1_lacks",
        ),
    ],
)
def test_a_note_that_does_not_fit_the_cover_leaves_the_mismatch(note: EditionNote) -> None:
    assert finding_code(confirm_period("qcmr", Q2_COVER, FY2022_Q1, (note,))) == "period_mismatch"


@pytest.mark.parametrize(
    "page1",
    [
        pytest.param(
            f"{Q2_COVER}SUBPERIOD ENDING DECEMBER 31 2021", id="a_word_character_before_the_quote"
        ),
        pytest.param(
            f"{Q2_COVER}PERIOD ENDING DECEMBER 31 2021S", id="a_word_character_after_the_quote"
        ),
    ],
)
def test_a_note_quoted_from_inside_a_longer_word_leaves_the_mismatch(page1: str) -> None:
    note = replace(NOTE, printed="PERIOD ENDING DECEMBER 31 2021")
    assert finding_code(confirm_period("qcmr", page1, FY2022_Q1, (note,))) == "period_mismatch"


def test_a_note_does_not_clear_a_date_that_is_not_a_quarter_end() -> None:
    page1 = "FOR THE PERIOD ENDING DECEMBER 30, 2021"
    note = replace(NOTE, printed=page1, value="2021-12-30")
    result = confirm_period("qcmr", page1, FY2022_Q1, (note,))
    assert finding_code(result) == "period_not_a_quarter_end"


REFUSED_COVERS = [
    pytest.param("", "period_unreadable", id="an_empty_page"),
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
]


@pytest.mark.parametrize(("page1", "code"), REFUSED_COVERS)
def test_qcmr_period_refuses_with_a_member_of_period_refusal(page1: str, code: str) -> None:
    from datadesk.core.fetch import PeriodRefusal

    assert qcmr_period(page1) is PeriodRefusal(code)


@pytest.mark.parametrize(("page1", "code"), REFUSED_COVERS)
def test_confirm_period_puts_the_refusal_in_the_finding_code_as_plain_text(
    page1: str, code: str
) -> None:
    finding = confirm_period("qcmr", page1, FY2022_Q1, ())
    assert isinstance(finding, Finding)
    assert (type(finding.code), finding.code) == (str, code)


def test_a_series_with_no_period_reader_is_unsupported() -> None:
    collections = EditionKey("collections_city", Period(date(2021, 9, 1), date(2021, 9, 30)))
    result = confirm_period("collections_city", "MONTH OF SEPTEMBER\nFY 2022", collections, ())
    assert finding_code(result, collections) == "period_unsupported"


def ok(request: FetchRequest, sha: str, page1: str | None = Q1_COVER) -> Fetched:
    return Fetched(request, 200, sha, 1_781_180, page1)


def pdf_key(sha: str) -> str:
    return f"pdf/{sha[:2]}/{sha}.pdf"


def written(plan: FetchPlan) -> tuple[object, ...]:
    return (plan.store, plan.index_add, plan.pull_request.files)


def listed(body: str, *words: str) -> list[str]:
    return [line for line in body.splitlines() if all(word in line for word in words)]


def test_a_confirmed_report_is_stored_once_and_indexed() -> None:
    plan = plan_fetch([ok(Q1_REQUEST, Q1_SHA)], EMPTY, ())
    assert plan.store == (StoreObject(Q1_SHA, f"pdf/7c/{Q1_SHA}.pdf"),)
    assert plan.index_add == (Q1,)
    assert plan.rejections == ()
    assert plan.pull_request.files == ((INDEX_FILE, render_index(ArchiveIndex((Q1,)))),)
    assert len(listed(plan.pull_request.body, "qcmr:2021-09-30:none", Q1_SHA, Q1_URL)) == 1


def test_a_sha_indexed_under_another_edition_is_a_content_alias() -> None:
    plan = plan_fetch([ok(Q2_REQUEST, Q1_SHA)], ArchiveIndex((Q1,)), ())
    assert plan.rejections == (Rejection(Q2_REQUEST, "content_alias"),)
    assert written(plan) == ((), (), ())
    assert len(listed(plan.pull_request.body, "qcmr:2021-12-31:none", Q2_URL, "content_alias")) == 1


def test_one_sha_fetched_for_two_editions_in_one_batch_is_a_content_alias() -> None:
    plan = plan_fetch([ok(Q1_REQUEST, Q1_SHA), ok(Q2_REQUEST, Q1_SHA)], EMPTY, ())
    assert plan.store == (StoreObject(Q1_SHA, pdf_key(Q1_SHA)),)
    assert plan.index_add == (Q1,)
    assert plan.rejections == (Rejection(Q2_REQUEST, "content_alias"),)


@pytest.mark.parametrize(("status", "reason"), [(404, "http_404"), (503, "http_503")])
def test_a_status_other_than_200_is_a_rejection(status: int, reason: str) -> None:
    plan = plan_fetch([Fetched(Q1_REQUEST, status, None, 0, None)], EMPTY, ())
    assert plan.rejections == (Rejection(Q1_REQUEST, reason),)
    assert written(plan) == ((), (), ())


@pytest.mark.parametrize(
    ("revision", "listed_at", "url"),
    [
        pytest.param(Q1_REPOST, "20220301090000", Q1_REPOST_URL, id="a_later_listing"),
        pytest.param(
            replace(Q1_REQUEST, reason="revision"),
            "20211116102946",
            Q1_URL,
            id="new_bytes_behind_the_same_listing",
        ),
    ],
)
def test_new_bytes_of_an_indexed_edition_supersede_its_current_version(
    revision: FetchRequest, listed_at: str, url: str
) -> None:
    plan = plan_fetch([ok(revision, NEW_Q1_SHA)], ArchiveIndex((Q1,)), ())
    new = DocumentVersion(NEW_Q1_SHA, FY2022_Q1, listed_at, (url,), Q1_TITLE, Q1_PERIOD, Q1_SHA)
    assert plan.store == (StoreObject(NEW_Q1_SHA, pdf_key(NEW_Q1_SHA)),)
    assert plan.index_add == (new,)
    assert plan.rejections == ()
    assert plan.pull_request.files == ((INDEX_FILE, render_index(ArchiveIndex((Q1, new)))),)


def test_plan_fetch_adds_nothing_for_an_indexed_sha() -> None:
    plan = plan_fetch([ok(Q1_REQUEST, Q1_SHA)], ArchiveIndex((Q1,)), ())
    assert plan.rejections == ()
    assert written(plan) == ((), (), ())


def test_the_current_sha_at_a_new_url_adds_the_url_and_stores_nothing() -> None:
    plan = plan_fetch([ok(Q1_REPOST, Q1_SHA)], ArchiveIndex((Q1,)), ())
    assert plan.store == ()
    assert plan.index_add == (replace(Q1, urls=(Q1_REPOST_URL,), listed_at="20220301090000"),)
    assert plan.rejections == ()
    merged = replace(Q1, urls=(Q1_URL, Q1_REPOST_URL), listed_at="20220301090000")
    assert plan.pull_request.files == ((INDEX_FILE, render_index(ArchiveIndex((merged,)))),)


def test_the_current_sha_at_a_new_url_listed_earlier_keeps_the_later_stamp() -> None:
    plan = plan_fetch([ok(Q1_EARLY, Q1_SHA)], ArchiveIndex((Q1,)), ())
    assert plan.index_add == (replace(Q1, urls=(Q1_EARLY_URL,), listed_at="20211101090000"),)
    merged = replace(Q1, urls=(Q1_URL, Q1_EARLY_URL))
    assert plan.pull_request.files == ((INDEX_FILE, render_index(ArchiveIndex((merged,)))),)


def test_older_bytes_after_a_repost_of_the_current_sha_are_listed_before_current() -> None:
    plan = plan_fetch([ok(Q1_THIRD, Q1_SHA), ok(Q1_REPOST, NEW_Q1_SHA)], ArchiveIndex((Q1,)), ())
    assert plan.rejections == (Rejection(Q1_REPOST, "listed_before_current"),)
    assert plan.store == ()
    assert plan.index_add == (replace(Q1, urls=(Q1_THIRD_URL,), listed_at="20220601090000"),)
    june = replace(Q1, urls=(Q1_URL, Q1_THIRD_URL), listed_at="20220601090000")
    assert plan.pull_request.files == ((INDEX_FILE, render_index(ArchiveIndex((june,)))),)


def test_a_superseded_sha_listed_again_is_rejected_and_the_newer_bytes_stay_current() -> None:
    plan = plan_fetch(
        [ok(Q1_REQUEST, Q1_SHA), ok(Q1_REPOST, NEW_Q1_SHA), ok(Q1_THIRD, Q1_SHA)], EMPTY, ()
    )
    new = DocumentVersion(
        NEW_Q1_SHA, FY2022_Q1, "20220301090000", (Q1_REPOST_URL,), Q1_TITLE, Q1_PERIOD, Q1_SHA
    )
    assert plan.rejections == (Rejection(Q1_THIRD, "superseded_sha_relisted"),)
    assert plan.index_add == (Q1, new)
    assert plan.store == (
        StoreObject(Q1_SHA, pdf_key(Q1_SHA)),
        StoreObject(NEW_Q1_SHA, pdf_key(NEW_Q1_SHA)),
    )
    assert plan.pull_request.files == ((INDEX_FILE, render_index(ArchiveIndex((Q1, new)))),)


def test_new_bytes_listed_before_the_current_version_are_rejected() -> None:
    plan = plan_fetch([ok(Q1_EARLY, NEW_Q1_SHA)], ArchiveIndex((Q1,)), ())
    assert plan.rejections == (Rejection(Q1_EARLY, "listed_before_current"),)
    assert written(plan) == ((), (), ())


@pytest.mark.parametrize(
    ("page1", "reason"),
    [
        pytest.param(Q2_COVER, "period_mismatch", id="a_cover_of_another_quarter"),
        pytest.param("(cid:38)(cid:51)(cid:52)(cid:3)", "period_unreadable", id="no_readable_text"),
        pytest.param(None, "period_unreadable", id="no_page_1_text"),
    ],
)
def test_a_cover_that_confirm_period_refuses_stores_nothing(page1: str | None, reason: str) -> None:
    plan = plan_fetch([ok(Q1_REQUEST, Q1_SHA, page1)], EMPTY, ())
    assert plan.rejections == (Rejection(Q1_REQUEST, reason),)
    assert written(plan) == ((), (), ())


def test_plan_fetch_clears_a_mismatch_only_with_a_note_for_the_fetched_sha() -> None:
    cleared = plan_fetch([ok(Q1_REQUEST, Q1_SHA, Q2_COVER)], EMPTY, (NOTE,))
    assert cleared.index_add == (replace(Q1, printed_period=Q2_PERIOD),)
    other = plan_fetch(
        [ok(Q1_REQUEST, Q1_SHA, Q2_COVER)], EMPTY, (replace(NOTE, doc_sha256=Q2_SHA),)
    )
    assert other.rejections == (Rejection(Q1_REQUEST, "period_mismatch"),)
    assert written(other) == ((), (), ())


def test_the_body_of_the_fetch_pull_request_is_exact() -> None:
    added = plan_fetch([ok(Q1_REQUEST, Q1_SHA)], EMPTY, ())
    refused = plan_fetch([ok(Q1_REQUEST, Q1_SHA, "")], EMPTY, ())
    unchanged = plan_fetch([ok(Q1_REQUEST, Q1_SHA)], ArchiveIndex((Q1,)), ())
    assert added.pull_request.body == (
        "Index lines added:\n"
        "- qcmr:2021-09-30:none "
        "7c4a2e5abb00a5084cdb24fb35325cd1f2cdee42cfd9b30cf7c62c46c2f22918 "
        "https://www.phila.gov/media/20211116102946/"
        "Quarterly-City-Managers-Report-September-30-2021.pdf\n"
        "\n"
        "Rejected:\n"
        "- none\n"
    )
    assert [(type(item.dest_key), item.dest_key) for item in added.store] == [
        (
            str,
            "pdf/7c/7c4a2e5abb00a5084cdb24fb35325cd1f2cdee42cfd9b30cf7c62c46c2f22918.pdf",
        )
    ]
    assert refused.pull_request.body == (
        "Index lines added:\n"
        "- none\n"
        "\n"
        "Rejected:\n"
        "- qcmr:2021-09-30:none "
        "https://www.phila.gov/media/20211116102946/"
        "Quarterly-City-Managers-Report-September-30-2021.pdf period_unreadable\n"
    )
    assert unchanged.pull_request.body == "Index lines added:\n- none\n\nRejected:\n- none\n"
    bodies = (added, refused, unchanged)
    assert [type(plan.pull_request.body) for plan in bodies] == [str, str, str]
