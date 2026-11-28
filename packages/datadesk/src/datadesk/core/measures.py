"""What each published column means, in the closed lists of `vocab` (design section 2.2).

A table module's `measures(era, scope)` gives each column a `MeasureSpec`. The release writes
each cell beside its column's description, and `subject_of` says which values of two editions
are about one thing, so a prior-year column meets the earlier edition's current column. Nothing
here sees a cell value.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from re import compile
from typing import assert_never

from checkedtables.table import RowKey, TableId
from datadesk.core.domain import DocumentVersion, EditionKey, Period
from datadesk.core.periods import fiscal_period, fiscal_year_of
from datadesk.core.records import EditionNote, NoteKind
from datadesk.core.vocab import Dim, How, Kind, Quantity, Version, Window

Dims = tuple[tuple[Dim, str], ...]
_CUTOFF_MONTH = compile(r"(\d{4})-(\d{2})")


class Basis(StrEnum):
    """Whether a value is an amount over its window or a level at the window's end.

    Attributes
    ----------
    FLOW
        An amount over the window, such as a year's obligations.
    POINT
        A level at the end of the window, such as a count of positions or a balance.
    """

    FLOW = "flow"
    POINT = "point"


@dataclass(frozen=True, slots=True)
class Stated:
    """A number the publisher reports, by its kind, its window and the year of the window.

    Attributes
    ----------
    year : int
        Whole years back from the edition's own window: 0 for the edition's year, -1 for the
        year before. The window says whether the year is fiscal, calendar or a tax year.
    version : Version
        Which budget a BUDGET column holds. NONE for every other kind.
    month : int or None
        The fiscal month of a month column in a grid, 1 for July to 12 for June. None for every
        other column, a column of the edition's own month among them.
    quantity : Quantity or None
        What the column counts, when that is not what the table mainly counts. None for the
        table's main quantity, which the row's line names.
    dims : Dims
        The slices the column carries, such as ``((Dim.FUND, "phl_fund_general"),)``.

    Raises
    ------
    ValueError
        When a budget has no version or another kind has one, a column whose window is not
        MONTH names a fiscal month, a fiscal month is not 1 to 12, or the year is after the
        edition's.
    """

    kind: Kind
    window: Window
    year: int = 0
    version: Version = Version.NONE
    month: int | None = None
    quantity: Quantity | None = None
    dims: Dims = ()

    def __post_init__(self) -> None:
        """Refuse a version that disagrees with the kind, a misplaced month, and a later year."""
        if (self.kind is Kind.BUDGET) != (self.version is not Version.NONE):
            raise ValueError("a budget column has a version, and only a budget column has one")
        if self.month is not None and self.window is not Window.MONTH:
            raise ValueError("only a month column names a fiscal month")
        if self.month is not None and not 1 <= self.month <= 12:
            raise ValueError(f"fiscal month {self.month} is not 1 to 12")
        if self.year > 0:
            raise ValueError("a column never reports a later year than its edition")


@dataclass(frozen=True, slots=True)
class Derived:
    """A number the publisher computed from other printed columns of the same table.

    Attributes
    ----------
    of : tuple[str, ...]
        The names of the operand columns, in the order `how` reads them. A difference takes two
        or more, the first minus each later one. A share takes one, the column that holds the
        whole. The other ways take two.
    dims : Dims
        For a share, the part of the whole that the column holds.

    Raises
    ------
    ValueError
        When `of` names another count of operands than `how` takes.
    """

    how: How
    of: tuple[str, ...]
    dims: Dims = ()

    def __post_init__(self) -> None:
        """Refuse a count of operands that `how` does not take."""
        if self.how is How.DIFFERENCE and len(self.of) < 2:
            raise ValueError(f"a difference takes two or more operands, not {self.of}")
        if self.how is How.SHARE and len(self.of) != 1:
            raise ValueError(f"a share takes one operand, not {self.of}")
        if self.how not in (How.DIFFERENCE, How.SHARE) and len(self.of) != 2:
            raise ValueError(f"a {self.how} takes two operands, not {self.of}")


@dataclass(frozen=True, slots=True)
class NotPublished:
    """A column the parser reads and the checks may use, which the release never writes.

    Attributes
    ----------
    reason : str
        Why, such as the quirk that leaves the column's meaning open (SUPOP-Q15).
    """

    reason: str


Meaning = Stated | Derived | NotPublished


@dataclass(frozen=True, slots=True)
class MeasureSpec:
    """What one column means, in what unit, at what scale and on what basis.

    Attributes
    ----------
    column : str
        The column's name in its era.
    unit : str
        What a published value counts, such as "USD", "positions" or "percent".
    scale : Decimal
        What the printed number is multiplied by to publish it, such as 1000 for a column
        printed in thousands.
    """

    column: str
    meaning: Meaning
    unit: str
    scale: Decimal
    basis: Basis


@dataclass(frozen=True, slots=True)
class RowMeasure:
    """A spec that replaces one column's spec on the rows that carry some key parts.

    Attributes
    ----------
    match : tuple[tuple[str, str], ...]
        The key parts a row must carry, such as ``(("metric", "positions"),)`` for the counts
        that O-3 prints under dollar captions.
    """

    match: tuple[tuple[str, str], ...]
    column: str
    spec: MeasureSpec


@dataclass(frozen=True, slots=True)
class MeasureSet:
    """The specs of an era's columns in print order, and the row overrides of some of them."""

    columns: tuple[MeasureSpec, ...]
    rows: tuple[RowMeasure, ...] = ()


@dataclass(frozen=True, slots=True)
class Scope:
    """What a description may depend on beside the era. It holds no cell value.

    Attributes
    ----------
    edition : EditionKey
        The edition, with its period and stage.
    table : TableId
        The table and its instance parts, such as a fund, a zone or a window.
    printed : frozenset[str]
        The names of the era's columns that the table prints.
    actual_through : date
        The last day of recorded results: the period's end, unless a CUTOFF note says otherwise.
    """

    edition: EditionKey
    table: TableId
    printed: frozenset[str]
    actual_through: date


@dataclass(frozen=True, slots=True, order=True)
class Subject:
    """What a stated value is about, apart from its edition, its table and its column's name.

    The window is left out, so a fiscal year to date that ends on June 30 and the next edition's
    prior-year actual for that fiscal year are one subject.

    Attributes
    ----------
    start : date or None
        The window's first day, or None for a level, which only its end date dates.
    end : date
        The window's last day.
    """

    kind: Kind
    version: Version
    quantity: Quantity | None
    dims: Dims
    unit: str
    start: date | None
    end: date


def scope_for(
    version: DocumentVersion,
    table: TableId,
    printed: frozenset[str],
    notes: Sequence[EditionNote],
) -> tuple[Scope, frozenset[str]]:
    """Build the scope of one parsed table, with the ids of the notes it read.

    `actual_through` is the period's end, unless a CUTOFF note of the file gives the last month
    of actual figures as ``YYYY-MM`` (QCASH-Q41). Then it is that month's last day, and the
    note's id joins the parser's used set, so a CUTOFF note that no table read stays unused.

    Parameters
    ----------
    printed : frozenset[str]
        The names of the era's columns that the table prints.
    notes : Sequence[EditionNote]
        The notes, of this file or of others.

    Raises
    ------
    ValueError
        When two CUTOFF notes are about the file, or one gives no month as ``YYYY-MM``.
    """
    match [n for n in notes if n.kind is NoteKind.CUTOFF and n.doc_sha256 == version.sha256]:
        case []:
            through, used = version.edition.period.end, frozenset[str]()
        case [note]:
            through, used = _last_day_of(note), frozenset({note.id})
        case found:
            raise ValueError(f"cutoff notes {', '.join(n.id for n in found)} name one file")
    return Scope(version.edition, table, printed, through), used


def measure_for(measures: MeasureSet, row: RowKey, column: str) -> MeasureSpec:
    """Return the spec of one cell: the override whose key parts the row carries, or the column's.

    Raises
    ------
    ValueError
        When two overrides of the column match the row.
    KeyError
        When the set holds no spec of the column.
    """
    parts = set(row.parts)
    match [r.spec for r in measures.rows if r.column == column and set(r.match) <= parts]:
        case []:
            for spec in measures.columns:
                if spec.column == column:
                    return spec
            raise KeyError(column)
        case [spec]:
            return spec
        case _:
            raise ValueError(f"two overrides of {column} match the row {row}")


def period_of(stated: Stated, scope: Scope) -> Period:
    """Return the days that a stated column covers in its edition, through `fiscal_period`.

    A quarter is the fiscal quarter that holds the last month of the edition's period, and a
    month column of a grid covers its fiscal month of the edition's fiscal year, each
    `stated.year` years back.
    """
    end = scope.edition.period.end
    calendar_year = end.year + stated.year
    fiscal_year = fiscal_year_of(end) + stated.year
    match stated.window:
        case Window.MONTH if stated.month is not None:
            month = (stated.month + 5) % 12 + 1
            return fiscal_period(Window.FISCAL_YEAR, fiscal_year, (month, month))
        case Window.MONTH:
            return fiscal_period(Window.MONTH, calendar_year, (end.month, end.month))
        case Window.QUARTER:
            first = (end.month - 1) // 3 * 3 + 1
            return fiscal_period(Window.QUARTER, calendar_year, (first, first + 2))
        case Window.FISCAL_YTD:
            return fiscal_period(Window.FISCAL_YTD, fiscal_year, (7, end.month))
        case Window.CALENDAR_YTD:
            return fiscal_period(Window.CALENDAR_YTD, calendar_year, (1, end.month))
        case Window.FISCAL_YEAR:
            return fiscal_period(Window.FISCAL_YEAR, fiscal_year, (7, 6))
        case Window.CALENDAR_YEAR | Window.TAX_YEAR:
            return fiscal_period(stated.window, calendar_year, (1, 12))
        case _:
            assert_never(stated.window)


def subject_of(spec: MeasureSpec, scope: Scope) -> Subject | None:
    """Return what a column's values are about in one edition, to match them across editions.

    Returns
    -------
    Subject or None
        None for a `Derived` or `NotPublished` column, since a computed column is never
        matched across editions.
    """
    match spec.meaning:
        case Stated() as stated:
            period = period_of(stated, scope)
            start = None if spec.basis is Basis.POINT else period.start
            return Subject(
                stated.kind,
                stated.version,
                stated.quantity,
                stated.dims,
                spec.unit,
                start,
                period.end,
            )
        case Derived() | NotPublished():
            return None
        case _:
            assert_never(spec.meaning)


def description(meaning: Meaning) -> tuple[object, ...]:
    """Return a meaning in the form the catalog rules compare, so no two columns share one."""
    match meaning:
        case Stated():
            return (
                "stated",
                meaning.kind,
                meaning.version,
                meaning.window,
                meaning.year,
                meaning.month,
                meaning.quantity,
                meaning.dims,
            )
        case Derived():
            return ("derived", meaning.how, meaning.of, meaning.dims)
        case NotPublished():
            return ("not_published", meaning.reason)
        case _:
            assert_never(meaning)


def _last_day_of(note: EditionNote) -> date:
    """Read the last day of the month that a CUTOFF note's ``YYYY-MM`` names."""
    if (found := _CUTOFF_MONTH.fullmatch(note.value)) and 1 <= int(found[2]) <= 12:
        year, month = int(found[1]), int(found[2])
        return fiscal_period(Window.MONTH, year, (month, month)).end
    raise ValueError(f"the cutoff note {note.id} names no month as YYYY-MM: {note.value!r}")
