"""Closed lists that say where words came from and how a column's cells print."""

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
