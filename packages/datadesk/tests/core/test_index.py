from dataclasses import replace
from datetime import date

from hypothesis import given
from hypothesis import strategies as st

from checkedtables.table import Finding, Severity
from datadesk.core.domain import (
    ArchiveIndex,
    DocumentVersion,
    EditionKey,
    Holding,
    Period,
    Stage,
    Via,
)
from datadesk.core.index import add_versions, parse_index, render_index

FY2026_Q3 = EditionKey("qcmr", Period(date(2026, 1, 1), date(2026, 3, 31)))
FY2026_Q4 = EditionKey("qcmr", Period(date(2026, 4, 1), date(2026, 6, 30)))
Q3_SHA = "032c5cfddfb77c50b270d5f0954d73674b5ec1c92c5d3fdee4b60e53efd82827"
Q4_SHA = "48fd9aa936df05a28bb7f37083720afac85d1ee2a2c9a70be832382f0dc55020"
REVISED_Q4_SHA = "1c0d5e7f9a2b4c6d8e0f1a3b5c7d9e1f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d"
LATER_Q4_SHA = "9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d"
MEDIA = "https://www.phila.gov/media"
Q3_URL = f"{MEDIA}/20260515154446/Quarterly-City-Managers-Report-March-30-2026R.pdf"
Q4_URL = f"{MEDIA}/20260817162758/Quarterly-City-Managers-Report-June-30-2026.pdf"
Q4_REPOST_URL = f"{MEDIA}/20261116120000/Quarterly-City-Managers-Report-June-30-2026-1.pdf"
Q3_TITLE = "Quarterly City Managers Report - March 31, 2026"
Q4_TITLE = "Quarterly City Managers Report - June 30, 2026"

Q3 = DocumentVersion(
    Q3_SHA, FY2026_Q3, "20260515154446", (Q3_URL,), Q3_TITLE, FY2026_Q3.period, None
)
Q4 = DocumentVersion(
    Q4_SHA, FY2026_Q4, "20260817162758", (Q4_URL,), Q4_TITLE, FY2026_Q4.period, None
)
REVISED_Q4 = DocumentVersion(
    REVISED_Q4_SHA, FY2026_Q4, "20260817162758", (Q4_URL,), Q4_TITLE, None, Q4_SHA
)
LATER_Q4 = DocumentVersion(
    LATER_Q4_SHA, FY2026_Q4, "20261116120000", (Q4_REPOST_URL,), Q4_TITLE, None, None
)
TEXT = (
    '{"edition": {"period": {"end": "2026-03-31", "start": "2026-01-01"}, "series": "qcmr", '
    '"stage": "none"}, "holding": "whole", "listed_at": "20260515154446", '
    '"printed_period": {"end": "2026-03-31", "start": "2026-01-01"}, '
    '"sha256": "032c5cfddfb77c50b270d5f0954d73674b5ec1c92c5d3fdee4b60e53efd82827", '
    '"supersedes": null, "title": "Quarterly City Managers Report - March 31, 2026", '
    '"urls": ["https://www.phila.gov/media/20260515154446/'
    'Quarterly-City-Managers-Report-March-30-2026R.pdf"], "via": "publisher"}\n'
    '{"edition": {"period": {"end": "2026-06-30", "start": "2026-04-01"}, "series": "qcmr", '
    '"stage": "none"}, "holding": "whole", "listed_at": "20260817162758", '
    '"printed_period": null, '
    '"sha256": "1c0d5e7f9a2b4c6d8e0f1a3b5c7d9e1f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d", '
    '"supersedes": "48fd9aa936df05a28bb7f37083720afac85d1ee2a2c9a70be832382f0dc55020", '
    '"title": "Quarterly City Managers Report - June 30, 2026", '
    '"urls": ["https://www.phila.gov/media/20260817162758/'
    'Quarterly-City-Managers-Report-June-30-2026.pdf"], "via": "publisher"}\n'
    '{"edition": {"period": {"end": "2026-06-30", "start": "2026-04-01"}, "series": "qcmr", '
    '"stage": "none"}, "holding": "whole", "listed_at": "20260817162758", '
    '"printed_period": {"end": "2026-06-30", "start": "2026-04-01"}, '
    '"sha256": "48fd9aa936df05a28bb7f37083720afac85d1ee2a2c9a70be832382f0dc55020", '
    '"supersedes": null, "title": "Quarterly City Managers Report - June 30, 2026", '
    '"urls": ["https://www.phila.gov/media/20260817162758/'
    'Quarterly-City-Managers-Report-June-30-2026.pdf"], "via": "publisher"}\n'
)

sha256s = st.text("0123456789abcdef", min_size=64, max_size=64)
periods = st.tuples(st.dates(), st.dates()).map(lambda days: Period(*sorted(days)))
editions = st.builds(EditionKey, st.text(), periods, st.sampled_from(Stage))


@st.composite
def archive_indexes(draw: st.DrawFn) -> ArchiveIndex:
    chains = draw(st.lists(st.tuples(editions, st.integers(1, 3)), unique_by=lambda c: c[0]))
    count = sum(length for _, length in chains)
    shas = iter(draw(st.lists(sha256s, min_size=count, max_size=count, unique=True)))
    versions = []
    for edition, length in chains:
        older = None
        for _ in range(length):
            version = DocumentVersion(
                sha256=next(shas),
                edition=edition,
                listed_at=draw(st.text()),
                urls=tuple(draw(st.lists(st.text(), max_size=3))),
                title=draw(st.text()),
                printed_period=draw(st.none() | periods),
                supersedes=older,
                via=draw(st.sampled_from(Via)),
                holding=draw(st.sampled_from(Holding)),
            )
            versions.append(version)
            older = version.sha256
    return ArchiveIndex(tuple(sorted(versions, key=lambda v: (v.edition, v.listed_at, v.sha256))))


def test_parse_index_reads_one_version_from_each_line() -> None:
    assert parse_index(TEXT) == ArchiveIndex((Q3, REVISED_Q4, Q4))


def test_render_index_writes_one_line_for_each_version_with_sorted_keys() -> None:
    assert render_index(ArchiveIndex((Q3, REVISED_Q4, Q4))) == TEXT


def test_render_index_gives_back_the_sorted_text_it_parsed() -> None:
    assert render_index(parse_index(TEXT)) == TEXT


def test_parse_index_sorts_the_lines() -> None:
    shuffled = "".join(reversed(TEXT.splitlines(keepends=True)))
    assert shuffled != TEXT
    assert parse_index(shuffled) == ArchiveIndex((Q3, REVISED_Q4, Q4))


def test_the_empty_text_is_the_empty_index() -> None:
    assert parse_index("") == ArchiveIndex(())
    assert render_index(ArchiveIndex(())) == ""


@given(archive_indexes())
def test_parse_index_reads_back_what_render_index_writes(index: ArchiveIndex) -> None:
    assert parse_index(render_index(index)) == index


def test_a_version_listed_at_the_stamp_of_the_one_it_supersedes_round_trips() -> None:
    index = ArchiveIndex((REVISED_Q4, Q4))
    read = parse_index(render_index(index))
    assert read == index
    assert read.current(FY2026_Q4) == REVISED_Q4


def test_add_versions_merges_a_new_url_into_the_line_of_the_same_sha_and_edition() -> None:
    relisted = replace(
        Q4,
        listed_at="20261116120000",
        urls=(Q4_REPOST_URL, Q4_URL),
        title="Quarterly City Manager's Report - June 30, 2026",
    )
    merged = replace(Q4, urls=(Q4_URL, Q4_REPOST_URL))
    assert add_versions(ArchiveIndex((Q3, Q4)), [relisted]) == ArchiveIndex((Q3, merged))


def test_add_versions_adds_nothing_for_an_indexed_sha_at_an_indexed_url() -> None:
    index = ArchiveIndex((Q3, Q4))
    assert add_versions(index, [Q4]) == index
    assert add_versions(index, [replace(Q4, listed_at="20261116120000")]) == index
    assert add_versions(ArchiveIndex((Q4,)), [Q3]) == index


def test_add_versions_refuses_a_sha_indexed_under_another_edition() -> None:
    found = add_versions(ArchiveIndex((Q4,)), [replace(Q3, sha256=Q4_SHA)])
    assert isinstance(found, Finding)
    assert (found.severity, found.code, found.subject) == (Severity.BLOCK, "content_alias", Q4_SHA)
    assert add_versions(ArchiveIndex((Q4,)), [Q3]) == ArchiveIndex((Q3, Q4))


def test_add_versions_refuses_an_edition_left_with_two_versions_that_nothing_supersedes() -> None:
    found = add_versions(ArchiveIndex((Q3, Q4)), [LATER_Q4])
    assert isinstance(found, Finding)
    assert (found.severity, found.code, found.subject) == (
        Severity.BLOCK,
        "two_current_versions",
        "qcmr:2026-06-30:none",
    )
    revision = replace(LATER_Q4, supersedes=Q4_SHA)
    assert add_versions(ArchiveIndex((Q3, Q4)), [revision]) == ArchiveIndex((Q3, Q4, revision))


def test_add_versions_refuses_a_version_that_supersedes_itself() -> None:
    found = add_versions(ArchiveIndex((Q3,)), [replace(Q4, supersedes=Q4_SHA)])
    assert isinstance(found, Finding)
    assert (found.severity, found.code, found.subject) == (
        Severity.BLOCK,
        "broken_chain",
        "qcmr:2026-06-30:none",
    )
    assert add_versions(ArchiveIndex((Q3,)), [Q4]) == ArchiveIndex((Q3, Q4))


def test_add_versions_refuses_two_versions_that_supersede_each_other_beside_a_third() -> None:
    cycle = [
        replace(REVISED_Q4, supersedes=LATER_Q4_SHA),
        replace(LATER_Q4, supersedes=REVISED_Q4_SHA),
    ]
    found = add_versions(ArchiveIndex((Q3, Q4)), cycle)
    assert isinstance(found, Finding)
    assert (found.severity, found.code, found.subject) == (
        Severity.BLOCK,
        "broken_chain",
        "qcmr:2026-06-30:none",
    )
    later = replace(LATER_Q4, supersedes=REVISED_Q4_SHA)
    chain = add_versions(ArchiveIndex((Q3, Q4)), [REVISED_Q4, later])
    assert chain == ArchiveIndex((Q3, REVISED_Q4, Q4, later))
