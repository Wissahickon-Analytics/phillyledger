"""Records that a person writes about an edition's file, such as a note on what it prints."""

from dataclasses import dataclass
from enum import StrEnum

from checkedtables.refs import Sha256


class NoteKind(StrEnum):
    """What an edition note says about its file.

    Attributes
    ----------
    PRINTED_PERIOD
        The file prints another period than the listing gave its edition.
    CUTOFF
        The last month of actual figures differs from the quarter's default.
    HEADER_MISPRINT
        A caption prints a wrong year.
    DROP_LINE
        One printed line is debris to drop.
    HEADER_ILLEGIBLE
        A scanned header cannot be read, so the page binds its columns by lane order.
    """

    PRINTED_PERIOD = "printed_period"
    CUTOFF = "cutoff"
    HEADER_MISPRINT = "header_misprint"
    DROP_LINE = "drop_line"
    HEADER_ILLEGIBLE = "header_illegible"


@dataclass(frozen=True, slots=True)
class EditionNote:
    """A person's note on what one file prints, with the words it is about and why.

    Attributes
    ----------
    doc_sha256
        The `Sha256` of the file the note is about.
    page
        The 1-based page the note is about, or None for no one page.
    printed
        The exact printed words the note is about, which the page must print.
    value
        What the note says the words mean. A PRINTED_PERIOD note gives the printed period's
        end in ISO form, such as "2014-03-31".
    """

    id: str
    kind: NoteKind
    doc_sha256: Sha256
    page: int | None
    printed: str
    value: str
    reason: str
