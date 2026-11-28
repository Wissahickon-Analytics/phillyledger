"""Build a table from its cut pages and matched rows, lexing each cell and applying its records."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import assert_never

from checkedtables.cells import Amount, Blank, Cell, Dash, NotApplicable, Text, Unreadable
from checkedtables.kinds import DashMeaning, UnreadableReason
from checkedtables.lex import lex_cell
from checkedtables.pipeline import CutPage, CutPages
from checkedtables.records import (
    CellRecords,
    DashRule,
    EveryRow,
    ReviewedReading,
    apply_reading,
    reading_for,
)
from checkedtables.rows import KeyedRow, _words
from checkedtables.table import Column, Finding, Row, RowKey, Severity, Table, TableId
from checkedtables.words import Word


@dataclass(frozen=True, slots=True)
class Assembly:
    """A table built from its rows, or the findings that make it impossible to build.

    Attributes
    ----------
    table : Table or None
        The table. None when two rows share a key or a row's parent is the key of no row.
    findings : tuple[Finding, ...]
        The findings of the cells and of the table, as `assemble` gives them.
    used : frozenset[str]
        The ids of the readings and dash rules that changed a cell.
    """

    table: Table | None
    findings: tuple[Finding, ...]
    used: frozenset[str]


@dataclass(frozen=True, slots=True)
class _Step:
    """A cell after one step of `assemble`, the findings of the step, and the records it used."""

    cell: Cell
    findings: tuple[Finding, ...] = ()
    used: tuple[str, ...] = ()


def assemble(
    table_id: TableId, cut: CutPages, rows: Sequence[KeyedRow], records: CellRecords
) -> Assembly:
    """Build a table from the rows of its cut pages, reading each cell from its words.

    Each cell is lexed with `lex_cell` and the source of its page. A dash rule of the table
    that names the cell's column and row then gives a `Dash` the rule's meaning, and names
    itself on the dash when that meaning is ZERO. Then `reading_for` looks for a reading of
    the cell among the words of its cut page, and `apply_reading` applies the one it finds. A
    cell that no reading covers, that reads as an `Amount`, and that holds an OCR word whose
    confidence is under the records' floor is `Unreadable` with "low_confidence": OCR words
    under the floor need a reading before they read as a number (design section 8.3). The
    floor reads no other cell, since `apply_reading` takes no `Dash` and no `NotApplicable`.

    Parameters
    ----------
    table_id : TableId
        The table and its instance. A dash rule applies when its table is the id's name.
    cut : CutPages
        The table's cut pages, from `cut_pages`.
    rows : Sequence[KeyedRow]
        The matched rows, in print order, from `match_rows` or `read_grammar`.
    records : CellRecords
        The readings and dash rules of this document, and its confidence floor.

    Returns
    -------
    Assembly
        The table, with a column for each column of the first page's binding, in its declared
        order, with the caption it prints there, and a row for each keyed row. A row's
        `label_words` are its prefix words, then its label words. A record is in `used` when it
        changed a cell. The findings come cell by cell, then for the table. The findings of
        `reading_for` and `apply_reading` keep their own subjects. The others are BLOCK, with
        the subject
        ``"<doc sha8>:<table id>:<row key>"``: ``duplicate_dash_rule`` on the row's page for a
        dash that two or more rules name, which keeps its meaning, ``unreadable_cell`` on the
        row's page for an `Unreadable` cell that no reading accepts, and then, on no page,
        ``duplicate_key`` for each key that two or more rows hold and ``dangling_parent`` for
        each row whose parent no row holds. Either of the last two leaves no table.
    """
    page_words = {page.number: _page_words(page) for page in cut.pages}
    sha = next(word.ref.doc_sha256 for words in page_words.values() for word in words)
    subject = f"{sha[:8]}:{table_id}"
    specs = {spec.name: spec for spec, _ in cut.binding.columns}
    pages = {page.number: page for page in cut.pages}
    rules = tuple(rule for rule in records.dash_rules if rule.table == table_id.name)
    findings: list[Finding] = []
    used: set[str] = set()
    built: list[Row] = []
    for keyed in rows:
        raw, source = keyed.raw, pages[keyed.raw.page].source
        where = f"{subject}:{keyed.key}"
        cells: list[Cell] = []
        for name, words in raw.cells:
            ruled = tuple(rule for rule in rules if _covers(rule, name, keyed.key))
            dashed = _dashed(lex_cell(words, specs[name], source), ruled, where, raw.page)
            found = reading_for(words, page_words[raw.page], source, records.readings)
            read = _read(dashed.cell, words, found, records.confidence_floor)
            findings += (*dashed.findings, *read.findings)
            findings += _unaccepted(read.cell, name, where, raw.page)
            used.update((*dashed.used, *read.used))
            cells.append(read.cell)
        label = tuple(word.ref for word in (*raw.prefix, *raw.label_words))
        built.append(
            Row(
                keyed.key,
                keyed.kind,
                keyed.label,
                keyed.parent,
                raw.page,
                label,
                tuple(cells),
                keyed.entity,
                keyed.unit,
            )
        )
    stops = _stops(built, subject)
    if stops:
        return Assembly(None, (*findings, *stops), frozenset(used))
    captions = dict(cut.binding.captions)
    columns = tuple(
        Column(spec.name, spec.kind, captions.get(spec.name, ""), lane is not None)
        for spec, lane in cut.binding.columns
    )
    numbers = tuple(page.number for page in cut.pages)
    table = Table(table_id, sha, cut.era.name, numbers, columns, tuple(built))
    return Assembly(table, tuple(findings), frozenset(used))


def _page_words(page: CutPage) -> tuple[Word, ...]:
    """Return every word of a cut page: its header, its rows and its furniture."""
    lines = (*page.header, *page.furniture)
    return (
        *(word for line in lines for word in line.words),
        *(word for raw in page.raws for word in _words(raw)),
    )


def _covers(rule: DashRule, column: str, key: RowKey) -> bool:
    """Return whether a dash rule names this column and this row."""
    match rule.rows:
        case EveryRow():
            return column in rule.columns
        case tuple():
            return column in rule.columns and key in rule.rows
        case _:
            assert_never(rule.rows)


def _dashed(cell: Cell, rules: Sequence[DashRule], subject: str, page: int) -> _Step:
    """Give a dash the meaning of the one dash rule that names it."""
    if not isinstance(cell, Dash) or not rules:
        return _Step(cell)
    if len(rules) > 1:
        ids = ", ".join(sorted(rule.id for rule in rules))
        message = f"dash rules {ids} each name the dash {cell.text!r}"
        return _Step(
            cell, (Finding(Severity.BLOCK, "duplicate_dash_rule", subject, message, page),)
        )
    [rule] = rules
    named = rule.id if rule.meaning is DashMeaning.ZERO else None
    ruled = Dash(cell.text, cell.words, rule.meaning, named)
    return _Step(ruled, used=() if ruled == cell else (rule.id,))


def _read(
    cell: Cell, words: Sequence[Word], found: ReviewedReading | Finding | None, floor: float
) -> _Step:
    """Apply the reading that `reading_for` found, or with none, the OCR confidence floor."""
    match found:
        case None:
            low = any(word.confidence is not None and word.confidence < floor for word in words)
            if isinstance(cell, Amount) and low:
                return _Step(Unreadable(cell.text, cell.words, UnreadableReason.LOW_CONFIDENCE))
            return _Step(cell)
        case Finding():
            return _Step(cell, (found,))
        case ReviewedReading():
            applied = apply_reading(cell, found)
            match applied:
                case Finding():
                    return _Step(cell, (applied,))
                case Amount() | Dash() | NotApplicable() | Blank() | Unreadable() | Text():
                    return _Step(applied, used=(found.id,))
                case _:
                    assert_never(applied)
        case _:
            assert_never(found)


def _unaccepted(cell: Cell, column: str, subject: str, page: int) -> tuple[Finding, ...]:
    """Return the finding for an `Unreadable` cell that no reading accepts, if the cell is one."""
    if not isinstance(cell, Unreadable) or cell.accepted_by is not None:
        return ()
    message = f"{column}: {cell.text!r} reads as no value ({cell.reason})"
    return (Finding(Severity.BLOCK, "unreadable_cell", subject, message, page),)


def _stops(rows: Sequence[Row], subject: str) -> tuple[Finding, ...]:
    """Return the findings that leave no table: two rows of one key, and a missing parent."""
    keys = [row.key for row in rows]
    repeated = [key for key in dict.fromkeys(keys) if keys.count(key) > 1]
    dangling = [row for row in rows if row.parent is not None and row.parent not in keys]
    return (
        *(
            _stop("duplicate_key", f"{subject}:{key}", f"{keys.count(key)} rows hold the key")
            for key in repeated
        ),
        *(
            _stop(
                "dangling_parent", f"{subject}:{row.key}", f"no row holds its parent {row.parent}"
            )
            for row in dangling
        ),
    )


def _stop(code: str, subject: str, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message)
