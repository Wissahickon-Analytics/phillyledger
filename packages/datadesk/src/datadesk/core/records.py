"""Records that a person writes about an edition's file, such as a note on what it prints.

Step 5 builds the notes, `TablePages`, `declared_run` and `illegible_pages`, which the parsers
call. No record exists for the editions that step 5 parses, so each record's loader lands with
its first record (design section 4.2).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from checkedtables.pages import PageRun
from checkedtables.refs import Sha256


class NoteKind(StrEnum):
    """What an edition note says about its file.

    Attributes
    ----------
    PRINTED_PERIOD
        The file prints another period than the listing gave its edition.
    CUTOFF
        The last month of actual figures differs from the quarter's default.
    HEADER_MISPRINT
        A caption prints a wrong year.
    DROP_LINE
        One printed line is debris to drop.
    HEADER_ILLEGIBLE
        A scanned header cannot be read, so the page binds its columns by lane order.
    """

    PRINTED_PERIOD = "printed_period"
    CUTOFF = "cutoff"
    HEADER_MISPRINT = "header_misprint"
    DROP_LINE = "drop_line"
    HEADER_ILLEGIBLE = "header_illegible"


@dataclass(frozen=True, slots=True)
class EditionNote:
    """A person's note on what one file prints, with the words it is about and why.

    Attributes
    ----------
    doc_sha256
        The `Sha256` of the file the note is about.
    page
        The 1-based page the note is about, or None for no one page.
    printed
        The exact printed words the note is about, which the page must print.
    value
        What the note says the words mean. A PRINTED_PERIOD note gives the printed period's
        end in ISO form, such as "2014-03-31".
    """

    id: str
    kind: NoteKind
    doc_sha256: Sha256
    page: int | None
    printed: str
    value: str
    reason: str


@dataclass(frozen=True, slots=True)
class TablePages:
    """A person's record of the pages that hold a table in one file, which code cannot find.

    It is for an older report, above all a scan, whose header band holds no text that
    `find_runs` can read (design section 2.2, decision 1). The parser then takes these pages
    and does not search.

    Attributes
    ----------
    doc_sha256
        The `Sha256` of the file the record is about.
    table
        The table's name, such as "qcmr_positions".
    first, last
        The first and the last page of the table, both included, 1-based in the whole report.
    reason
        Why code cannot find the pages, such as "scan; no text to find the TABLE P-1 band".

    Raises
    ------
    ValueError
        When `first` is under 1 or `last` is before `first`.
    """

    id: str
    doc_sha256: Sha256
    table: str
    first: int
    last: int
    reason: str

    def __post_init__(self) -> None:
        """Refuse pages that start before page 1 or end before they start."""
        if not 1 <= self.first <= self.last:
            raise ValueError(f"{self.id}: pages {self.first} to {self.last} are not a run")


def declared_run(
    records: Sequence[TablePages], table: str
) -> tuple[PageRun | None, frozenset[str]]:
    """Return the run of pages that a record names for a table, and the record's id.

    Parameters
    ----------
    records : Sequence[TablePages]
        The records of one file.
    table : str
        The table's name.

    Returns
    -------
    tuple[PageRun | None, frozenset[str]]
        The run and the id, for the parser's used set. None and no id when no record names the
        table, so the parser finds the run itself.

    Raises
    ------
    ValueError
        When two records name the table, since one file prints a table on one run of pages.
    """
    match [record for record in records if record.table == table]:
        case []:
            return None, frozenset()
        case [record]:
            return PageRun(record.first, record.last), frozenset({record.id})
        case found:
            ids = ", ".join(record.id for record in found)
            raise ValueError(f"records {ids} each name the pages of {table}")


def illegible_pages(
    notes: Sequence[EditionNote], sha: Sha256
) -> tuple[frozenset[int], frozenset[str]]:
    """Return the pages of a file whose header a person recorded as illegible, and the note ids.

    A HEADER_ILLEGIBLE note names a scanned page whose captions cannot be read, so the parser
    binds that page's columns by lane order (`bind_by_position`). A note on no one page names no
    page here, so it stays unused.

    Parameters
    ----------
    notes : Sequence[EditionNote]
        The notes, of this file or of others.
    sha : Sha256
        The file.

    Returns
    -------
    tuple[frozenset[int], frozenset[str]]
        The 1-based pages, and the ids of the notes that name them, for the parser's used set.
    """
    pages = {
        note.id: page
        for note in notes
        if note.kind is NoteKind.HEADER_ILLEGIBLE
        and note.doc_sha256 == sha
        and (page := note.page) is not None
    }
    return frozenset(pages.values()), frozenset(pages)
