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
    row finding names. A stray finding names a stray word when it is on the word's page and
    its message quotes the word's text. A row finding names a raw row that no row of the table
    holds a word of when it is on the row's page and its subject ends with the row's printed
    label. Each finding names one word or one row. The result maps each word of the pages
    that is in no place or in two or more, and each placed word that is on none of the pages,
    to its count of places. It is empty when no ink is lost.
    """
    placed: list[WordRef] = []
    for page in cut.pages:
        placed += [word.ref for line in (*page.header, *page.furniture) for word in line.words]
    for row in table.rows:
        placed += [*row.label_words, *(ref for cell in row.cells for ref in cell_refs(cell))]
    in_rows = set(placed)
    unused = list(findings)
    for raw in cut.raws:
        for word in raw.stray:
            stray = next(
                (
                    finding
                    for finding in unused
                    if finding.code in STRAY_CODES
                    and finding.page == word.ref.page
                    and repr(word.text) in finding.message
                ),
                None,
            )
            if stray is not None:
                unused.remove(stray)
                placed.append(word.ref)
        own = row_refs(raw)
        if not own or in_rows.intersection(own):
            continue
        printed = " ".join(word.text for word in (*raw.prefix, *raw.label_words))
        unknown = next(
            (
                finding
                for finding in unused
                if finding.code in NOT_A_ROW_CODES
                and finding.page == raw.page
                and finding.subject.endswith(f":{printed}")
            ),
            None,
        )
        if unknown is not None:
            unused.remove(unknown)
            placed += own
    counts = Counter(placed)
    on_pages = {word.ref for page in pages for word in page.words}
    return {
        ref: counts[ref]
        for ref in on_pages | set(counts)
        if counts[ref] != 1 or ref not in on_pages
    }
