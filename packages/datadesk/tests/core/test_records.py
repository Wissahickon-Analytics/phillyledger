from dataclasses import replace

import pytest

from checkedtables.pages import PageRun
from checkedtables.refs import Sha256
from datadesk.core.records import (
    EditionNote,
    NoteKind,
    TablePages,
    declared_run,
    illegible_pages,
)

SHA = Sha256("a" * 64)
OTHER = Sha256("b" * 64)
PAGES = TablePages("tp1", SHA, "qcmr_positions", 35, 36, "scan; no text to find the band")
ILLEGIBLE = EditionNote("n1", NoteKind.HEADER_ILLEGIBLE, SHA, 36, "", "", "the header is a blur")


def test_a_table_pages_record_declares_the_run_of_its_table() -> None:
    assert declared_run((PAGES,), "qcmr_positions") == (PageRun(35, 36), frozenset({"tp1"}))


def test_no_record_of_the_table_declares_no_run() -> None:
    assert declared_run((), "qcmr_positions") == (None, frozenset())
    assert declared_run((PAGES,), "qcmr_cash") == (None, frozenset())


def test_two_records_of_one_table_are_refused() -> None:
    with pytest.raises(ValueError, match="qcmr_positions"):
        declared_run((PAGES, replace(PAGES, id="tp2")), "qcmr_positions")


@pytest.mark.parametrize(("first", "last"), [(0, 3), (5, 4), (-1, -1)])
def test_a_table_pages_record_needs_pages_in_order_from_page_1(first: int, last: int) -> None:
    with pytest.raises(ValueError, match="tp1"):
        replace(PAGES, first=first, last=last)


def test_a_one_page_table_pages_record_is_kept() -> None:
    assert declared_run((replace(PAGES, last=35),), "qcmr_positions")[0] == PageRun(35, 35)


def test_the_illegible_pages_are_the_header_illegible_notes_of_the_file() -> None:
    notes = (
        ILLEGIBLE,
        replace(ILLEGIBLE, id="n2", page=40),
        replace(ILLEGIBLE, id="n3", kind=NoteKind.DROP_LINE, page=41),
        replace(ILLEGIBLE, id="n4", doc_sha256=OTHER, page=42),
    )
    assert illegible_pages(notes, SHA) == (frozenset({36, 40}), frozenset({"n1", "n2"}))
    assert illegible_pages(notes, OTHER) == (frozenset({42}), frozenset({"n4"}))


def test_a_header_illegible_note_on_no_page_makes_no_page_illegible() -> None:
    assert illegible_pages((replace(ILLEGIBLE, page=None),), SHA) == (frozenset(), frozenset())
