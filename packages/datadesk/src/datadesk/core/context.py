"""What a table parser reads beside the words of one file, and what it gives back.

The shell builds a `ParseContext` from the index entry, the row schemas, the registry and the
records of one file, and a table's `parse` returns `Parsed` or `Failed` (design section 2.2).
"""

from dataclasses import dataclass

from checkedtables.records import CellRecords
from checkedtables.rows import RowSchema
from checkedtables.table import Finding, Severity, Table
from datadesk.core.domain import DocumentVersion, Period
from datadesk.core.periods import fiscal_year_of
from datadesk.core.records import EditionNote, TablePages
from datadesk.core.registry.model import Registry


@dataclass(frozen=True, slots=True)
class ParseContext:
    """Everything a table parser reads about one file but its words.

    Attributes
    ----------
    version : DocumentVersion
        The file's index entry, with its edition and period.
    schemas : tuple[RowSchema, ...]
        The row schemas of the file's closed tables, each narrowed to this edition by
        `schema_for`, one for each table.
    registry : Registry
        The registry, for a table that resolves labels itself.
    cell_records : CellRecords
        The readings of this file and the dash rules of its period.
    notes : tuple[EditionNote, ...]
        The notes on this file.
    table_pages : tuple[TablePages, ...]
        The records of the pages that hold a table in this file.

    Raises
    ------
    ValueError
        When two schemas are of one table, or a note, a `TablePages` record or a reading is
        about another file.
    """

    version: DocumentVersion
    schemas: tuple[RowSchema, ...]
    registry: Registry
    cell_records: CellRecords
    notes: tuple[EditionNote, ...]
    table_pages: tuple[TablePages, ...]

    def __post_init__(self) -> None:
        """Refuse two schemas of one table and a record of another file."""
        tables = [schema.table for schema in self.schemas]
        if repeated := sorted({table for table in tables if tables.count(table) > 1}):
            raise ValueError(f"two row schemas of {', '.join(repeated)}")
        shas = {
            *(note.doc_sha256 for note in self.notes),
            *(pages.doc_sha256 for pages in self.table_pages),
            *(reading.doc_sha256 for reading in self.cell_records.readings),
        }
        if others := sorted(shas - {self.version.sha256}):
            named = ", ".join(sha[:8] for sha in others)
            raise ValueError(f"records of {named} in the context of {self.version.sha256[:8]}")

    @property
    def period(self) -> Period:
        """The period the edition reports, such as 2025-07-01 to 2025-09-30 for FY2026 Q1."""
        return self.version.edition.period

    @property
    def fiscal_year(self) -> int:
        """The City's fiscal year of the period's end, which starts on July 1."""
        return fiscal_year_of(self.period.end)

    def schema(self, table: str) -> RowSchema:
        """Return the row schema of a table.

        Raises
        ------
        KeyError
            When the context holds no schema of the table, which is a bug of its builder.
        """
        for schema in self.schemas:
            if schema.table == table:
                return schema
        raise KeyError(table)


@dataclass(frozen=True, slots=True)
class Parsed:
    """The tables a parser read from one file, with its findings.

    Attributes
    ----------
    tables : tuple[Table, ...]
        The tables, in the order the parser built them.
    findings : tuple[Finding, ...]
        Every finding, sorted. A BLOCK finding beside a table fails the gate, as an unknown
        row does.
    used : frozenset[str]
        The ids of the records that changed a cell or chose a page, so that a record passed in
        and not used becomes an ``unused_record`` finding.
    """

    tables: tuple[Table, ...]
    findings: tuple[Finding, ...]
    used: frozenset[str]


@dataclass(frozen=True, slots=True)
class Failed:
    """A file whose table a parser could not build, with the findings that say why.

    Raises
    ------
    ValueError
        When no finding is BLOCK, since a parse that fails has a problem that stops it.
    """

    findings: tuple[Finding, ...]

    def __post_init__(self) -> None:
        """Refuse a failure with no BLOCK finding."""
        if not any(finding.severity is Severity.BLOCK for finding in self.findings):
            raise ValueError("a failed parse needs a BLOCK finding")


ParseResult = Parsed | Failed
