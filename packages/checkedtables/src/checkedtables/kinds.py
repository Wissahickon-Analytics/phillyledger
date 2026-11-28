"""Closed lists of where words came from, how a column's cells print, and why one is unreadable."""

from enum import StrEnum


class SourceKind(StrEnum):
    """Where a page's words came from: the PDF's text layer or OCR of a rendered page."""

    TEXT_LAYER = "text_layer"
    OCR = "ocr"


class ValueKind(StrEnum):
    """What a column holds."""

    MONEY = "money"
    COUNT = "count"
    PERCENT = "percent"
    YEAR = "year"
    CODE = "code"
    TEXT = "text"


class DashMeaning(StrEnum):
    """What a dash in a cell means.

    `NO_VALUE` is the default everywhere. `ZERO` comes only from a `DashRule` or from an era
    column that declares it.
    """

    NO_VALUE = "no_value"
    ZERO = "zero"


class Presence(StrEnum):
    """Whether a declared column or row must be printed."""

    REQUIRED = "required"
    OPTIONAL = "optional"


class PercentSign(StrEnum):
    """Whether a percent cell prints its ``%`` sign."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    ABSENT = "absent"


class UnreadableReason(StrEnum):
    """Why the words of a cell give no value of its column.

    Attributes
    ----------
    NOT_A_NUMBER
        A glyph that no number, sign, mark or separator uses, or no digit.
    TWO_TOKENS
        Two or more words in no form that reads as one number.
    SIGN
        A plus sign, a minus after a digit, an unpaired or misplaced parenthesis, or two signs.
    PERCENT_SIGN
        A ``%`` that the column's format forbids, or none where it requires one.
    GROUPING
        What is left is not one strictly grouped number, a misplaced ``$``, ``%`` or mark
        included.
    DECIMALS
        A count of printed decimals other than the one the column declares.
    FONT_CODE
        A word holds ``(cid:``, a font code that extraction could not decode, which is no
        evidence of any glyph (VAL-Q05).
    REVIEWED_NULL
        A person read an `Amount` cell on the rendered page and accepted it as null. Only
        `apply_reading` gives it.
    LOW_CONFIDENCE
        An OCR word of a cell that reads as an `Amount` has a confidence under the floor of
        its records, and no reading covers the cell. Only `assemble` gives it.
    """

    NOT_A_NUMBER = "not_a_number"
    TWO_TOKENS = "two_tokens"
    SIGN = "sign"
    PERCENT_SIGN = "percent_sign"
    GROUPING = "grouping"
    DECIMALS = "decimals"
    FONT_CODE = "font_code"
    REVIEWED_NULL = "reviewed_null"
    LOW_CONFIDENCE = "low_confidence"
