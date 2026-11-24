from dataclasses import dataclass
from enum import StrEnum


class NoteKind(StrEnum):
    PRINTED_PERIOD = "printed_period"
    CUTOFF = "cutoff"
    HEADER_MISPRINT = "header_misprint"
    DROP_LINE = "drop_line"
    HEADER_ILLEGIBLE = "header_illegible"


@dataclass(frozen=True, slots=True)
class EditionNote:
    id: str
    kind: NoteKind
    doc_sha256: str
    page: int | None
    printed: str
    value: str
    reason: str
