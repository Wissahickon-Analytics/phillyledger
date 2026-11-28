from collections import Counter
from collections.abc import Sequence
from typing import assert_never

from checkedtables.cells import Amount, Blank, Cell, Dash, NotApplicable, Text, Unreadable
from checkedtables.pipeline import CutPages
from checkedtables.refs import WordRef
from checkedtables.rows import RawRow
from checkedtables.table import Finding, Table
from checkedtables.words import Page

STRAY_CODES = ("stray_value", "stray_word")
NOT_A_ROW_CODES = ("unknown_row", "ambiguous_row")


def cell_refs(cell: Cell) -> tuple[WordRef, ...]:
    match cell:
        case Blank():
            return ()
        case Amount() | Dash() | NotApplicable() | Unreadable() | Text():
            return cell.words
        case _:
            assert_never(cell)


def row_refs(raw: RawRow) -> tuple[WordRef, ...]:
    words = (*raw.prefix, *raw.label_words, *(word for _, cell in raw.cells for word in cell))
    return tuple(word.ref for word in words)


def misplaced(
    pages: Sequence[Page], cut: CutPages, table: Table, findings: Sequence[Finding]
) -> dict[WordRef, int]:
    """Count the places each word of the pages ends up in, and return the words not in one.

    A word's places are a header or furniture line of the cut, the label or a cell of a row of
    the table, a stray that a stray finding names, and a raw row that an unknown or ambiguous
    row finding names, if no row of the table holds a word of it. A finding fits a stray or a
    raw row when it is on the row's page, its subject is ``"<doc sha8>:<part>:<printed label>"``
    with the sha8 of the row's words and the row's printed label, and, for a stray, its message
    quotes the word's text. Each finding names one stray or one raw row that it fits
    (`_named`). The result maps each word of the pages that is in no place or in two or more,
    and each placed word that is on none of the pages, to its count of places. It is empty
    when no ink is lost.
    """
    placed: list[WordRef] = []
    for page in cut.pages:
        placed += [word.ref for line in (*page.header, *page.furniture) for word in line.words]
    for row in table.rows:
        placed += [*row.label_words, *(ref for cell in row.cells for ref in cell_refs(cell))]
    in_rows = set(placed)
    strays = [(raw, repr(word.text), (word.ref,)) for raw in cut.raws for word in raw.stray]
    not_rows = [
        (raw, "", row_refs(raw))
        for raw in cut.raws
        if row_refs(raw) and not in_rows.intersection(row_refs(raw))
    ]
    placed += _named(findings, STRAY_CODES, strays)
    placed += _named(findings, NOT_A_ROW_CODES, not_rows)
    counts = Counter(placed)
    on_pages = {word.ref for page in pages for word in page.words}
    return {
        ref: counts[ref]
        for ref in on_pages | set(counts)
        if counts[ref] != 1 or ref not in on_pages
    }


def _named(
    findings: Sequence[Finding],
    codes: tuple[str, ...],
    places: Sequence[tuple[RawRow, str, tuple[WordRef, ...]]],
) -> list[WordRef]:
    """Return the refs of the places that the findings of `codes` name, one place per finding.

    A place is a raw row, the text a finding's message must quote, and the refs it holds. A
    finding names the first place it fits that no earlier finding names, or the first it fits
    when every one is named, so a finding given twice counts its place twice.
    """
    named: list[int] = []
    for finding in findings:
        if finding.code not in codes:
            continue
        parts = finding.subject.split(":", 2)
        fits = [
            index
            for index, (raw, quote, _) in enumerate(places)
            if finding.page == raw.page
            and len(parts) == 3
            and (parts[0], parts[2]) == (_sha8(raw), _printed(raw))
            and quote in finding.message
        ]
        fresh = [index for index in fits if index not in named]
        named += (fresh or fits)[:1]
    return [ref for index in named for ref in places[index][2]]


def _printed(raw: RawRow) -> str:
    return " ".join(word.text for word in (*raw.prefix, *raw.label_words))


def _sha8(raw: RawRow) -> str:
    cells = (word for _, cell in raw.cells for word in cell)
    return next(
        word.ref.doc_sha256[:8] for word in (*raw.prefix, *raw.label_words, *cells, *raw.stray)
    )
