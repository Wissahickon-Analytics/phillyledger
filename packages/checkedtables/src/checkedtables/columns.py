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
        The stable name that checks and keys use.
    caption : str
        A regex searched in the lane's stacked caption.
    kind : ValueKind
        What the column holds.
    fmt : NumberFormat
        How the column prints its numbers.
    presence : Presence
        Whether the column must be printed.
    dash : DashMeaning
        What a dash in the column means.
    """

    name: str
    caption: str
    kind: ValueKind
    fmt: NumberFormat = NumberFormat()
    presence: Presence = Presence.REQUIRED
    dash: DashMeaning = DashMeaning.NO_VALUE
