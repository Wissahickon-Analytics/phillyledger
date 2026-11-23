from collections.abc import Sequence
from dataclasses import dataclass

from checkedtables.cells import Amount, Cell, Reading, Unreadable
from checkedtables.kinds import DashMeaning, SourceKind
from checkedtables.lex import _read_number, transliteration_ok
from checkedtables.refs import Box
from checkedtables.table import Finding, RowKey, Severity
from checkedtables.words import Word

_SLACK = 1.0


@dataclass(frozen=True, slots=True)
class ReviewedReading:
    """A person's reading of one cell on the rendered page.

    A reading is keyed by file hash, page, box and the text that extraction returned in the box,
    never by word index, which shifts when the extraction library changes.

    Attributes
    ----------
    id : str
        The id of the record. Never empty, since a reviewed `Amount` names it.
    doc_sha256 : str
        The sha256 of the publisher file.
    page : int
        The 1-based page in the publisher file.
    box : Box
        Where the reviewer looked.
    source : SourceKind
        The word layer being read.
    seen : str
        What extraction returns inside the box, the word texts joined by one space, such as
        "2918" or "1o4.o".
    reading : str or None
        What a person reads on the rendered page, such as "291.8". None accepts publishing the
        cell as null.
    reason : str
        Why the reading was written.

    Raises
    ------
    ValueError
        When `id` is empty.
    """

    id: str
    doc_sha256: str
    page: int
    box: Box
    source: SourceKind
    seen: str
    reading: str | None
    reason: str

    def __post_init__(self) -> None:
        """Refuse an empty id."""
        if not self.id:
            raise ValueError("a reviewed reading needs an id")


@dataclass(frozen=True, slots=True)
class EveryRow:
    """The rows of a `DashRule` that applies to every row of its table."""


@dataclass(frozen=True, slots=True)
class DashRule:
    """A declared meaning for the dashes in some cells of one table.

    Attributes
    ----------
    id : str
        The id of the record.
    table : str
        The table the rule applies to.
    columns : tuple[str, ...]
        The names of the columns the rule applies to.
    rows : tuple[RowKey, ...] or EveryRow
        The rows the rule applies to.
    meaning : DashMeaning
        What a dash in those cells means.
    evidence : str
        Where the meaning was confirmed, such as "maintainer confirmed 2026-10-01 against page
        2".
    """

    id: str
    table: str
    columns: tuple[str, ...]
    rows: tuple[RowKey, ...] | EveryRow
    meaning: DashMeaning
    evidence: str


@dataclass(frozen=True, slots=True)
class CellRecords:
    """The records that change the cells of one document.

    Attributes
    ----------
    readings : tuple[ReviewedReading, ...]
        The reviewed readings of this document only.
    dash_rules : tuple[DashRule, ...]
        The dash rules, already narrowed to the period of this edition.
    confidence_floor : float
        An OCR word with a confidence below it needs a reading.
    """

    readings: tuple[ReviewedReading, ...]
    dash_rules: tuple[DashRule, ...]
    confidence_floor: float


def _holds(reading: ReviewedReading, word: Word) -> bool:
    return (
        word.ref.doc_sha256 == reading.doc_sha256
        and word.ref.page == reading.page
        and reading.box.contains(word.box, _SLACK)
    )


def _finding(code: str, reading: ReviewedReading, message: str) -> Finding:
    subject = f"{reading.doc_sha256[:8]}:reading:{reading.id}"
    return Finding(Severity.BLOCK, code, subject, message, reading.page)


def reading_for(
    cell_words: Sequence[Word],
    page_words: Sequence[Word],
    source: SourceKind,
    readings: Sequence[ReviewedReading],
) -> ReviewedReading | Finding | None:
    """Find the one reviewed reading of a cell, and check that its box still holds the cell.

    A reading is a candidate when its source is `source` and its box, grown by 1.0 point on
    every side, holds a word of the cell on the reading's file and page. The words of
    `page_words` that the box holds must be exactly the words of the cell, and their texts,
    left to right and joined by one space, must equal the reading's `seen`. So a box that holds
    part of a cell, or two cells, is stale for each of them.

    Parameters
    ----------
    cell_words : Sequence[Word]
        The words of the cell.
    page_words : Sequence[Word]
        Every word of the page, as the cells were cut from them.
    source : SourceKind
        The source of the page's words.
    readings : Sequence[ReviewedReading]
        The readings of the document.

    Returns
    -------
    ReviewedReading or Finding or None
        None when no reading is a candidate. The reading when exactly one is and its box holds
        exactly the cell's words, which join to `seen`. Otherwise a BLOCK finding on the
        reading's page with the subject ``"<doc sha8>:reading:<reading id>"``:
        "duplicate_reading" for two or more candidates, named by the least id, or
        "stale_reading" for one whose box holds other words.
    """
    candidates = sorted(
        (
            reading
            for reading in readings
            if reading.source is source and any(_holds(reading, word) for word in cell_words)
        ),
        key=lambda reading: reading.id,
    )
    if not candidates:
        return None
    reading = candidates[0]
    if len(candidates) > 1:
        ids = ", ".join(candidate.id for candidate in candidates)
        return _finding("duplicate_reading", reading, f"readings {ids} each hold a word of a cell")
    held = sorted(
        (word for word in page_words if _holds(reading, word)),
        key=lambda word: (word.box.x0, word.ref),
    )
    joined = " ".join(word.text for word in held)
    if set(held) != set(cell_words) or joined != reading.seen:
        message = f"the box holds {joined!r}, not the cell's words that read {reading.seen!r}"
        return _finding("stale_reading", reading, message)
    return reading


def apply_reading(cell: Cell, reading: ReviewedReading) -> Cell | Finding:
    """Apply a reviewed reading to the cell it was written for.

    Only an `Amount` or an `Unreadable` takes a reading. The cell's words must lie on the
    reading's file and page, and its text must equal the reading's `seen`, because
    `transliteration_ok` reads both of its texts from the record. A reading may add or drop a
    sign, a separator or a point, and may read an OCR confusable letter as its digit. It never
    changes, adds or drops a digit.

    Parameters
    ----------
    cell : Cell
        The cell as lexed from its words.
    reading : ReviewedReading
        The reading that `reading_for` found for the cell.

    Returns
    -------
    Cell or Finding
        For a reading of None, an `Unreadable` accepted by the reading's id. It keeps the
        reason of an `Unreadable` cell and gives an `Amount` the reason "reviewed_null". For
        any other reading, a reviewed `Amount` of the cell's text and words, the reading's
        source and the reading's id. Its number is the reading, read as one signed number by
        the reader of `lex_cell`. A BLOCK finding on the reading's page, with the subject
        ``"<doc sha8>:reading:<reading id>"``, takes the place of the cell in two cases.
        "stale_reading" means the cell is not the one the reading was written for.
        "reading_refused" means the cell takes no reading, or the reading changes, adds or
        drops a digit of `seen`, or is not one number.
    """
    if not isinstance(cell, Amount | Unreadable):
        return _finding("reading_refused", reading, f"a {type(cell).__name__} takes no reading")
    if {(ref.doc_sha256, ref.page) for ref in cell.words} != {(reading.doc_sha256, reading.page)}:
        return _finding("stale_reading", reading, "the cell's words are not on the reading's page")
    if cell.text != reading.seen:
        message = f"the cell prints {cell.text!r} where the reading saw {reading.seen!r}"
        return _finding("stale_reading", reading, message)
    if reading.reading is None:
        reason = cell.reason if isinstance(cell, Unreadable) else "reviewed_null"
        return Unreadable(cell.text, cell.words, reason, reading.id)
    number = _read_number(reading.reading)
    if number is None or not transliteration_ok(reading.seen, reading.reading):
        message = f"{reading.reading!r} is not one number with the digits of {reading.seen!r}"
        return _finding("reading_refused", reading, message)
    return Amount(number, cell.text, cell.words, reading.source, Reading.REVIEWED, reading.id)
