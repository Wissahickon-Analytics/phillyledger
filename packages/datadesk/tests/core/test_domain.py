from dataclasses import replace
from datetime import date

import pytest

from checkedtables.table import Severity
from datadesk.core.domain import (
    ArchiveIndex,
    DocumentVersion,
    EditionKey,
    Period,
    Stage,
    index_problem,
)

FY2026_Q3 = EditionKey("qcmr", Period(date(2026, 1, 1), date(2026, 3, 31)))
FY2026_Q4 = EditionKey("qcmr", Period(date(2026, 4, 1), date(2026, 6, 30)))
Q3_SHA = "032c5cfddfb77c50b270d5f0954d73674b5ec1c92c5d3fdee4b60e53efd82827"
Q4_SHA = "48fd9aa936df05a28bb7f37083720afac85d1ee2a2c9a70be832382f0dc55020"
REVISED_Q4_SHA = "1c0d5e7f9a2b4c6d8e0f1a3b5c7d9e1f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d"
LATER_Q4_SHA = "9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e8d"


def version(
    sha: str, edition: EditionKey, listed_at: str, supersedes: str | None = None
) -> DocumentVersion:
    end = edition.period.end
    return DocumentVersion(
        sha256=sha,
        edition=edition,
        listed_at=listed_at,
        urls=(f"https://www.phila.gov/media/{listed_at}/Quarterly-City-Managers-Report.pdf",),
        title=f"Quarterly City Managers Report - {end:%B} {end.day}, {end:%Y}",
        printed_period=edition.period,
        supersedes=supersedes,
    )


Q3 = version(Q3_SHA, FY2026_Q3, "20260515154446")
Q4 = version(Q4_SHA, FY2026_Q4, "20260817162758")
REVISED_Q4 = version(REVISED_Q4_SHA, FY2026_Q4, "20260817162758", supersedes=Q4_SHA)
LATER_Q4 = version(LATER_Q4_SHA, FY2026_Q4, "20261116120000", supersedes=REVISED_Q4_SHA)


def test_edition_id_names_the_series_the_period_end_and_the_stage() -> None:
    assert FY2026_Q4.id() == "qcmr:2026-06-30:none"
    budget = EditionKey("bib", Period(date(2026, 7, 1), date(2027, 6, 30)), Stage.PROPOSED)
    assert budget.id() == "bib:2027-06-30:proposed"


def test_period_holds_its_own_days_and_refuses_an_end_before_its_start() -> None:
    assert FY2026_Q4.period.holds(date(2026, 4, 1))
    assert FY2026_Q4.period.holds(date(2026, 6, 30))
    assert not FY2026_Q4.period.holds(date(2026, 7, 1))
    assert Period(date(2026, 6, 30), date(2026, 6, 30)).holds(date(2026, 6, 30))
    with pytest.raises(ValueError, match="ends before it starts"):
        Period(date(2026, 6, 30), date(2026, 4, 1))


def test_index_refuses_one_sha_twice() -> None:
    assert ArchiveIndex((Q3, Q4)).versions == (Q3, Q4)
    with pytest.raises(ValueError, match=Q4_SHA):
        ArchiveIndex((version(Q4_SHA, FY2026_Q3, "20260515154446"), Q4))


@pytest.mark.parametrize(
    "versions",
    [
        pytest.param((Q4, Q3), id="out_of_order"),
        pytest.param(
            (Q4, version(LATER_Q4_SHA, FY2026_Q4, "20261116120000")),
            id="two_versions_that_nothing_supersedes",
        ),
        pytest.param(
            (Q3, version(LATER_Q4_SHA, FY2026_Q4, "20261116120000", supersedes=Q3_SHA)),
            id="supersedes_a_version_of_another_edition",
        ),
        pytest.param(
            (version(LATER_Q4_SHA, FY2026_Q4, "20261116120000", supersedes=Q4_SHA),),
            id="supersedes_a_sha_not_indexed",
        ),
    ],
)
def test_index_refuses_versions_that_break_a_rule(versions: tuple[DocumentVersion, ...]) -> None:
    with pytest.raises(ValueError):
        ArchiveIndex(versions)


@pytest.mark.parametrize(
    ("broken", "chain"),
    [
        pytest.param(
            (replace(Q4, supersedes=Q4_SHA),), (Q4,), id="a_version_that_supersedes_itself"
        ),
        pytest.param(
            (replace(REVISED_Q4, supersedes=LATER_Q4_SHA), Q4, LATER_Q4),
            (REVISED_Q4, Q4, LATER_Q4),
            id="two_versions_that_supersede_each_other_beside_a_third",
        ),
        pytest.param(
            (
                REVISED_Q4,
                replace(Q4, supersedes=REVISED_Q4_SHA),
                replace(LATER_Q4, supersedes=Q4_SHA),
            ),
            (REVISED_Q4, Q4, LATER_Q4),
            id="a_chain_that_runs_into_a_cycle",
        ),
    ],
)
def test_index_refuses_an_edition_whose_versions_are_not_one_chain(
    broken: tuple[DocumentVersion, ...], chain: tuple[DocumentVersion, ...]
) -> None:
    assert ArchiveIndex(chain).versions == chain
    problem = index_problem(broken)
    assert problem is not None
    assert (problem.severity, problem.code, problem.subject) == (
        Severity.BLOCK,
        "broken_chain",
        "qcmr:2026-06-30:none",
    )
    with pytest.raises(ValueError, match="qcmr:2026-06-30:none"):
        ArchiveIndex(broken)


def test_index_orders_versions_of_one_edition_by_listed_at_then_sha() -> None:
    later = version(LATER_Q4_SHA, FY2026_Q4, "20261116120000", supersedes=Q4_SHA)
    revised = version(REVISED_Q4_SHA, FY2026_Q4, "20260817162758", supersedes=Q4_SHA)
    assert ArchiveIndex((Q3, Q4, later)).versions == (Q3, Q4, later)
    assert ArchiveIndex((Q3, revised, Q4)).versions == (Q3, revised, Q4)
    with pytest.raises(ValueError):
        ArchiveIndex((Q3, Q4, revised))


def test_current_is_the_version_that_nothing_supersedes() -> None:
    revised = version(REVISED_Q4_SHA, FY2026_Q4, "20260817162758", supersedes=Q4_SHA)
    later = version(LATER_Q4_SHA, FY2026_Q4, "20261116120000", supersedes=REVISED_Q4_SHA)
    assert ArchiveIndex((Q3, Q4)).current(FY2026_Q4) == Q4
    assert ArchiveIndex((Q3, revised, Q4)).current(FY2026_Q4) == revised
    chain = ArchiveIndex((Q3, revised, Q4, later))
    assert chain.current(FY2026_Q4) == later
    assert chain.current(FY2026_Q3) == Q3
    assert chain.current(EditionKey("qcmr", Period(date(2025, 10, 1), date(2025, 12, 31)))) is None


def test_by_sha_finds_the_version_with_those_bytes() -> None:
    index = ArchiveIndex((Q3, Q4))
    assert index.by_sha(Q4_SHA) == Q4
    assert index.by_sha(Q3_SHA) == Q3
    assert index.by_sha(REVISED_Q4_SHA) is None
