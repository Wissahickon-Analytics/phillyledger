from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from checkedtables.kinds import DashMeaning, SourceKind
from checkedtables.refs import WordRef


class Reading(StrEnum):
    """How an Amount got its value: read from its words, or supplied by a ReviewedReading."""

    DIRECT = "direct"
    REVIEWED = "reviewed"


@dataclass(frozen=True, slots=True)
class Amount:
    """A number read from the words of one cell.

    Attributes
    ----------
    printed : Decimal
        The number as printed, before any unit scale.
    text : str
        The word text joined verbatim.
    words : tuple[WordRef, ...]
        The words the number was read from. Never empty.
    source : SourceKind
        The source of the words. It decides whether a passing check can prove the number.
    reading : Reading
        How the number was read.
    review_id : str or None
        The ReviewedReading that supplied the number, set exactly when `reading` is REVIEWED,
        and never empty.
    marks : tuple[str, ...]
        Marks printed with the number, such as the "*" of "242,096*" or a superscript digit.

    Raises
    ------
    ValueError
        When `words` is empty, when `review_id` is empty, or when `review_id` is set without a
        reviewed reading or missing from one.
    """

    printed: Decimal
    text: str
    words: tuple[WordRef, ...]
    source: SourceKind
    reading: Reading = Reading.DIRECT
    review_id: str | None = None
    marks: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Refuse no words, an empty review id, or a review id the reading does not match."""
        if not self.words:
            raise ValueError("an Amount needs the words it was read from")
        if self.review_id == "":
            raise ValueError("an Amount names an empty review id")
        if (self.reading is Reading.REVIEWED) != (self.review_id is not None):
            raise ValueError("a reviewed Amount names its review, and only then")


@dataclass(frozen=True, slots=True)
class Dash:
    """A cell that prints only a dash.

    Attributes
    ----------
    text : str
        The dash as printed.
    words : tuple[WordRef, ...]
        The words of the dash. Never empty.
    meaning : DashMeaning
        What the dash means.
    rule_id : str or None
        The DashRule that set ZERO, if one did.

    Raises
    ------
    ValueError
        When `words` is empty.
    """

    text: str
    words: tuple[WordRef, ...]
    meaning: DashMeaning
    rule_id: str | None = None

    def __post_init__(self) -> None:
        """Refuse a Dash with no words."""
        if not self.words:
            raise ValueError("a Dash needs the words it was read from")


@dataclass(frozen=True, slots=True)
class NotApplicable:
    """A cell that prints a not-applicable marker, such as "N/A" or "NA"."""

    text: str
    words: tuple[WordRef, ...]


@dataclass(frozen=True, slots=True)
class Blank:
    """A cell with no words."""


@dataclass(frozen=True, slots=True)
class Unreadable:
    """A cell whose words read as no value of its column.

    Attributes
    ----------
    text : str
        The word text joined verbatim.
    words : tuple[WordRef, ...]
        The words of the cell.
    reason : str
        Why the words did not read, such as "grouping", "low_confidence" or "two_tokens".
    accepted_by : str or None
        The review id that accepts publishing the cell as null.
    """

    text: str
    words: tuple[WordRef, ...]
    reason: str
    accepted_by: str | None = None


@dataclass(frozen=True, slots=True)
class Text:
    """A cell of a text column."""

    text: str
    words: tuple[WordRef, ...]


Cell = Amount | Dash | NotApplicable | Blank | Unreadable | Text
