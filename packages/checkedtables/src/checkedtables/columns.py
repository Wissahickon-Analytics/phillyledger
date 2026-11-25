"""The columns a table declares, and how each one prints its numbers."""

from dataclasses import dataclass

from checkedtables.kinds import DashMeaning, PercentSign, Presence, ValueKind


@dataclass(frozen=True, slots=True)
class NumberFormat:
    """How a column prints its numbers.

    Attributes
    ----------
    decimals : int or None
        The printed decimals. None means as printed.
    percent : PercentSign
        Whether a cell prints a ``%`` sign.
    """

    decimals: int | None = 0
    percent: PercentSign = PercentSign.ABSENT


@dataclass(frozen=True, slots=True)
class ColumnSpec:
    """One column that a table declares.

    Attributes
    ----------
    name : str
        The stable name that checks and keys use. Never empty.
    caption : str
        A regex searched in the lane's stacked caption. Never empty, since the empty regex
        matches every caption.
    kind : ValueKind
        What the column holds.
    fmt : NumberFormat
        How the column prints its numbers.
    presence : Presence
        Whether the column must be printed.
    dash : DashMeaning
        What a dash in the column means.

    Raises
    ------
    ValueError
        When `name` or `caption` is empty.
    """

    name: str
    caption: str
    kind: ValueKind
    fmt: NumberFormat = NumberFormat()
    presence: Presence = Presence.REQUIRED
    dash: DashMeaning = DashMeaning.NO_VALUE

    def __post_init__(self) -> None:
        """Refuse a column with an empty name or an empty caption."""
        if not self.name:
            raise ValueError(f"a column has an empty name: {self}")
        if not self.caption:
            raise ValueError(f"column {self.name} has an empty caption")
