"""datadesk/core/measures.py: what a published column means. Pure; no cell values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import StrEnum

from vocab import Dim, How, Kind, Quantity, Version, Window

Dims = tuple[tuple[Dim, str], ...]


class Basis(StrEnum):
    FLOW = "flow"      # amount over the window
    POINT = "point"    # level at the end of the window (positions, balances)


@dataclass(frozen=True, slots=True, order=True)
class Period:
    start: date
    end: date


@dataclass(frozen=True, slots=True)
class Stated:
    """A number the publisher reports."""

    kind: Kind
    window: Window
    year: int = 0                      # whole years back from the edition's own window: 0, -1, -2, -3
    version: Version = Version.NONE
    month: int | None = None           # fiscal month 1 to 12 (July is 1), for a month column of a grid
    quantity: Quantity | None = None   # None: the row says what is counted
    dims: Dims = ()

    def __post_init__(self) -> None:
        if (self.kind is Kind.BUDGET) != (self.version is not Version.NONE):
            raise ValueError("a budget column has a version, and only a budget column has one")
        if self.month is not None and self.window is not Window.MONTH:
            raise ValueError("only a month column names a fiscal month")
        if self.month is not None and not 1 <= self.month <= 12:
            raise ValueError("fiscal month out of range")
        if self.year > 0:
            raise ValueError("a column never reports a later year than its edition")


@dataclass(frozen=True, slots=True)
class Derived:
    """A number the publisher computed from other printed columns of the same row or table."""

    how: How
    of: tuple[str, ...]                # operand columns, in the order `how` reads them
    dims: Dims = ()

    def __post_init__(self) -> None:
        n = len(self.of)
        if self.how is How.SHARE and n != 1:
            raise ValueError("a share names one operand, the whole")
        if self.how is How.DIFFERENCE and n < 2:
            raise ValueError("a difference names at least two operands")
        if self.how not in (How.SHARE, How.DIFFERENCE) and n != 2:
            raise ValueError(f"{self.how} names two operands")


@dataclass(frozen=True, slots=True)
class NotPublished:
    """A column the parser reads and the checks may use, and the release does not write."""

    reason: str


Meaning = Stated | Derived | NotPublished


@dataclass(frozen=True, slots=True)
class MeasureSpec:
    column: str
    meaning: Meaning
    unit: str             # "USD", "positions", "fte", "transactions", "accounts", "percent"
    scale: Decimal        # published value = printed x scale (1, 1000, 1000000)
    basis: Basis


@dataclass(frozen=True, slots=True)
class RowMeasure:
    match: tuple[tuple[str, str], ...]   # key parts a row must carry, e.g. (("metric", "positions"),)
    column: str
    spec: MeasureSpec                    # replaces the column's spec on every matching row


@dataclass(frozen=True, slots=True)
class MeasureSet:
    columns: tuple[MeasureSpec, ...]
    rows: tuple[RowMeasure, ...] = ()


@dataclass(frozen=True, slots=True)
class Scope:
    """What a description may depend on besides the era. It never holds a cell value."""

    period: Period                     # EditionKey.period in the design
    stage: str                         # EditionKey.stage: none, adopted, proposed
    instance: tuple[tuple[str, str], ...]   # TableId.instance: fund, zone, window
    printed: frozenset[str]            # names of the era's columns printed in this table
    actual_through: date               # last day of recorded results; the period end unless a CUTOFF note says so

    def part(self, name: str) -> str:
        return dict(self.instance)[name]


@dataclass(frozen=True, slots=True, order=True)
class Subject:
    """What a stated value is about, apart from its edition, its table and its column name."""

    kind: Kind
    version: Version
    quantity: Quantity | None
    dims: Dims
    unit: str
    start: date | None                 # None for a point value: only the date matters
    end: date


def fiscal_year_of(day: date) -> int:
    return day.year + 1 if day.month >= 7 else day.year


def _month_end(year: int, month: int) -> date:
    nxt = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return nxt - timedelta(days=1)


def fiscal_month(fiscal_year: int, month: int) -> Period:
    cal_month = (month + 5) % 12 + 1               # fiscal month 1 is July
    cal_year = fiscal_year - 1 if cal_month >= 7 else fiscal_year
    return Period(date(cal_year, cal_month, 1), _month_end(cal_year, cal_month))


def _shift(day: date, years: int) -> date:
    if day.month == 2 and day.day == 29:
        return _month_end(day.year + years, 2)
    if day.month == 2 and day.day == 28:
        return _month_end(day.year + years, 2)
    return day.replace(year=day.year + years)


def period_of(stated: Stated, scope: Scope) -> Period:
    """The dates a stated column covers. One place for every window's year basis."""
    end = scope.period.end
    fy = fiscal_year_of(end) + stated.year
    match stated.window:
        case Window.MONTH:
            if stated.month is not None:
                return fiscal_month(fy, stated.month)
            e = _shift(end, stated.year)
            return Period(date(e.year, e.month, 1), e)
        case Window.QUARTER:
            e = _shift(end, stated.year)
            first = e.month - 2
            return Period(date(e.year, first, 1), e)
        case Window.FISCAL_YTD:
            return Period(date(fy - 1, 7, 1), _shift(end, stated.year))
        case Window.CALENDAR_YTD:
            e = _shift(end, stated.year)
            return Period(date(e.year, 1, 1), e)
        case Window.FISCAL_YEAR:
            return Period(date(fy - 1, 7, 1), date(fy, 6, 30))
        case Window.CALENDAR_YEAR | Window.TAX_YEAR:
            y = end.year + stated.year
            return Period(date(y, 1, 1), date(y, 12, 31))
    raise AssertionError(stated.window)


def subject_of(spec: MeasureSpec, scope: Scope) -> Subject | None:
    """The matching key for restatements and cross-edition checks. Derived columns have none."""
    m = spec.meaning
    if not isinstance(m, Stated):
        return None
    p = period_of(m, scope)
    start = None if spec.basis is Basis.POINT else p.start
    return Subject(m.kind, m.version, m.quantity, m.dims, spec.unit, start, p.end)


def describe(meaning: Meaning) -> tuple[object, ...]:
    """The comparable form used by the uniqueness test."""
    match meaning:
        case Stated():
            return ("stated", meaning.kind, meaning.version, meaning.window, meaning.year,
                    meaning.month, meaning.quantity, meaning.dims)
        case Derived():
            return ("derived", meaning.how, meaning.of, meaning.dims)
        case NotPublished():
            return ("not_published", meaning.reason)
    raise AssertionError(meaning)


def measure_for(ms: MeasureSet, row: tuple[tuple[str, str], ...], column: str) -> MeasureSpec:
    """The spec for one cell: a matching row override, else the column's spec."""
    parts = set(row)
    hits = [r.spec for r in ms.rows if r.column == column and set(r.match) <= parts]
    if len(hits) > 1:
        raise ValueError(f"two row overrides match {row} in {column}")
    if hits:
        return hits[0]
    return next(c for c in ms.columns if c.column == column)
