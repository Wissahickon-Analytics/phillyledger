"""A checked table's rows and columns, the keys of its rows, and the findings beside it."""

from dataclasses import dataclass
from enum import StrEnum
from typing import assert_never

from checkedtables.cells import Cell
from checkedtables.kinds import ValueKind
from checkedtables.labels import Label
from checkedtables.refs import Sha256, WordRef


class RowKind(StrEnum):
    """What a row is in its table, which decides how a check adds it up.

    Attributes
    ----------
    HEADING
        A label that heads the rows under it and holds no value to add.
    ITEM
        A row that adds into its parent.
    SUBTOTAL
        A row that adds the rows under it, and adds into its own parent.
    TOTAL
        A row that adds the rows under it, such as the grand total of the table.
    BREAKDOWN
        A part of a parent that is already counted, such as Civilian under Police - Total.
    MEMO
        A comparator or memo line, published and never added.
    """

    HEADING = "heading"
    ITEM = "item"
    SUBTOTAL = "subtotal"
    TOTAL = "total"
    BREAKDOWN = "breakdown"
    MEMO = "memo"


class Additivity(StrEnum):
    """How a row's values add into its parent.

    Attributes
    ----------
    ADDITIVE
        The row adds into its parent.
    COMPONENT
        The row splits a parent that is already counted, so it never adds a second time.
    NONE
        The row adds into nothing.
    """

    ADDITIVE = "additive"
    COMPONENT = "component"
    NONE = "none"


def additivity_of(kind: RowKind) -> Additivity:
    """Return how a row of this kind adds into its parent.

    An item, a subtotal and a total are additive, a breakdown is a component, and a memo and a
    heading add into nothing. Additivity comes only from the kind, so an additive memo row
    cannot be built.

    Parameters
    ----------
    kind : RowKind
        The row's kind.
    """
    match kind:
        case RowKind.ITEM | RowKind.SUBTOTAL | RowKind.TOTAL:
            return Additivity.ADDITIVE
        case RowKind.BREAKDOWN:
            return Additivity.COMPONENT
        case RowKind.MEMO | RowKind.HEADING:
            return Additivity.NONE
        case _:
            assert_never(kind)


@dataclass(frozen=True, slots=True, order=True)
class RowKey:
    """The identity of a row, as named parts sorted by name.

    ``str`` prints each part as ``name=value`` and joins the parts with ``|``, and `parse` reads
    that text back.

    Attributes
    ----------
    parts : tuple[tuple[str, str], ...]
        The ``(name, value)`` parts, such as
        ``(("breakdown", "civilian"), ("dept", "phl_dept_police"))``.

    Raises
    ------
    ValueError
        When there are no parts, the names are not strictly ascending, a name is empty, or a
        name or value holds ``|`` or ``=``.
    """

    parts: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        """Refuse no parts, names that are empty or not strictly ascending, and a separator."""
        names = [name for name, _ in self.parts]
        if not names:
            raise ValueError("a row key needs at least one part")
        if names != sorted(set(names)):
            raise ValueError(f"row key names are not strictly ascending: {names}")
        if not all(names):
            raise ValueError(f"a row key name is empty: {self.parts}")
        if any(separator in text for part in self.parts for text in part for separator in "|="):
            raise ValueError(f"a row key part holds | or =: {self.parts}")

    def __str__(self) -> str:
        """Return the parts as ``name=value`` joined by ``|``."""
        return "|".join(f"{name}={value}" for name, value in self.parts)

    @staticmethod
    def of(**parts: str) -> "RowKey":
        """Return the key with these parts, sorted by name.

        Parameters
        ----------
        **parts : str
            The value of each part, by name.
        """
        return RowKey(tuple(sorted(parts.items())))

    @staticmethod
    def parse(text: str) -> "RowKey":
        """Read a key from the text that ``str`` prints.

        For a key held as text, such as one in a TOML record. Code builds a key with `of`.

        Parameters
        ----------
        text : str
            Parts as ``name=value``, joined by ``|``.

        Raises
        ------
        ValueError
            When a part has no ``=``, or the parts break a rule of the key.
        """
        pieces = [part.partition("=") for part in text.split("|")]
        if not all(separator for _, separator, _ in pieces):
            raise ValueError(f"a row key part has no =: {text!r}")
        return RowKey(tuple((name, value) for name, _, value in pieces))

    @property
    def has_occurrence(self) -> bool:
        """Whether the key has the ``occurrence`` part that a list table gives a repeated key."""
        return any(name == "occurrence" for name, _ in self.parts)


class Severity(StrEnum):
    """How a finding affects the gate. A BLOCK finding fails it, and a WARN finding is listed."""

    BLOCK = "block"
    WARN = "warn"


@dataclass(frozen=True, slots=True)
class Finding:
    """A problem in the documents, returned as a value beside the result.

    Findings sort by `severity`, `code`, `subject`, `message` and `page`, and a finding with no
    page sorts before every page.

    Attributes
    ----------
    severity : Severity
        Whether the finding blocks.
    code : str
        A stable code, such as "unknown_row", "style_unavailable" or "check_not_evaluated".
    subject : str
        What the finding is about, as ``"<doc sha8>:<table>:<row key or label>"``.
    message : str
        The finding in words.
    page : int or None
        The page the finding is on, when it has one.
    """

    severity: Severity
    code: str
    subject: str
    message: str
    page: int | None = None

    def _order(self) -> tuple[str, str, str, str, tuple[int, ...]]:
        page = () if self.page is None else (self.page,)
        return (self.severity, self.code, self.subject, self.message, page)

    def __lt__(self, other: object) -> bool:
        """Return whether this finding sorts before `other`."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() < other._order()

    def __le__(self, other: object) -> bool:
        """Return whether this finding sorts before `other` or equals it."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() <= other._order()

    def __gt__(self, other: object) -> bool:
        """Return whether this finding sorts after `other`."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() > other._order()

    def __ge__(self, other: object) -> bool:
        """Return whether this finding sorts after `other` or equals it."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() >= other._order()


@dataclass(frozen=True, slots=True, order=True)
class TableId:
    """The name of a table, and the parts that tell its instances in one document apart.

    ``str`` prints the name, then each instance part as ``name=value``, joined by ``|``, as
    "supplemental_revenues|fund=phl_fund_general".

    Attributes
    ----------
    name : str
        The table's name, such as "qcmr_positions".
    instance : tuple[tuple[str, str], ...]
        The ``(name, value)`` parts of one instance, such as ``(("fund", "phl_fund_general"),)``
        for a table that a report prints once for each fund. Empty for a table printed once.
    """

    name: str
    instance: tuple[tuple[str, str], ...] = ()

    def part(self, name: str) -> str:
        """Return the value of the instance part called `name`.

        Raises
        ------
        KeyError
            When the instance has no part of that name.
        """
        for part, value in self.instance:
            if part == name:
                return value
        raise KeyError(name)

    def __str__(self) -> str:
        """Return the name, then each instance part as ``name=value``, joined by ``|``."""
        return "|".join((self.name, *(f"{part}={value}" for part, value in self.instance)))


@dataclass(frozen=True, slots=True)
class Column:
    """One column of a checked table, as the page printed it.

    Attributes
    ----------
    name : str
        The stable name that checks and keys use.
    kind : ValueKind
        What the column holds.
    caption : str
        The words that bound the column on the first page, for the release: the words its group
        regex found, then the words its caption regex found (`Binding.captions`). Empty for a
        column the page did not print, or one bound by position.
    printed : bool
        A fact read from the page: False for an optional column that the page did not print.
    """

    name: str
    kind: ValueKind
    caption: str
    printed: bool


@dataclass(frozen=True, slots=True)
class Row:
    """One row of a checked table: its key, its label as printed, and a cell for each column.

    Attributes
    ----------
    key : RowKey
        The row's identity, which the row schema or grammar gave it.
    kind : RowKind
        What the row is in the table.
    label : Label
        The label as the page printed it, with its marks and line number split off.
    parent : RowKey or None
        The key of the row it adds into, or None for the table's root.
    page : int
        The 1-based page in the publisher file.
    label_words : tuple[WordRef, ...]
        The words of ``label.printed``: the line number words, then the label words.
    cells : tuple[Cell, ...]
        One cell for each column of the table, in the table's column order.
    entity : str or None
        The registry entity the row names, if any.
    unit : str or None
        A unit that holds for this row alone.
    """

    key: RowKey
    kind: RowKind
    label: Label
    parent: RowKey | None
    page: int
    label_words: tuple[WordRef, ...]
    cells: tuple[Cell, ...]
    entity: str | None
    unit: str | None

    @property
    def additivity(self) -> Additivity:
        """How the row adds into its parent, from its kind (`additivity_of`)."""
        return additivity_of(self.kind)


@dataclass(frozen=True, slots=True)
class Table:
    """One table of one document, its rows keyed and its cells typed.

    `assemble` builds it, after it has turned two rows of one key and a parent that no row
    holds into findings. So reaching a `ValueError` here is a bug (design section 9).

    Attributes
    ----------
    id : TableId
        The table and its instance.
    doc_sha256 : Sha256
        The sha256 of the publisher file.
    era : str
        The name of the era its pages print.
    pages : tuple[int, ...]
        The 1-based pages it was read from, in order.
    columns : tuple[Column, ...]
        Its columns, left to right in the era's declared order.
    rows : tuple[Row, ...]
        Its rows, in print order.

    Raises
    ------
    ValueError
        When two rows share a key, a row has not one cell for each column, or a row's parent is
        the key of no row.
    """

    id: TableId
    doc_sha256: Sha256
    era: str
    pages: tuple[int, ...]
    columns: tuple[Column, ...]
    rows: tuple[Row, ...]

    def __post_init__(self) -> None:
        """Refuse two rows of one key, a ragged row, and a parent that no row holds."""
        keys = [row.key for row in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{self.id}: duplicate row keys")
        if any(len(row.cells) != len(self.columns) for row in self.rows):
            raise ValueError(f"{self.id}: ragged row")
        known = set(keys)
        if any(row.parent is not None and row.parent not in known for row in self.rows):
            raise ValueError(f"{self.id}: parent key not in table")

    def cell(self, key: RowKey, column: str) -> Cell:
        """Return the cell of the row of `key` under the column called `column`.

        Raises
        ------
        KeyError
            When no row has the key, or no column has the name.
        """
        row = self.row(key)
        if row is None:
            raise KeyError(key)
        names = [each.name for each in self.columns]
        if column not in names:
            raise KeyError(column)
        return row.cells[names.index(column)]

    def row(self, key: RowKey) -> Row | None:
        """Return the row of `key`, or None when the table has none."""
        return next((row for row in self.rows if row.key == key), None)

    def children(self, key: RowKey) -> tuple[Row, ...]:
        """Return the rows whose parent is `key`, in print order."""
        return tuple(row for row in self.rows if row.parent == key)
