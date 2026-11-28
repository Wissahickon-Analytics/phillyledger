from dataclasses import replace
from datetime import date

import pytest

from checkedtables.kinds import SourceKind
from checkedtables.records import CellRecords, ReviewedReading
from checkedtables.refs import Box, Sha256
from checkedtables.rows import RowSchema
from checkedtables.table import Finding, Severity
from datadesk.core.context import Failed, ParseContext
from datadesk.core.domain import DocumentVersion, EditionKey, Period
from datadesk.core.records import EditionNote, NoteKind, TablePages
from datadesk.core.registry.model import Registry

SHA = Sha256("a" * 64)
OTHER = Sha256("b" * 64)
QUARTER = Period(date(2025, 7, 1), date(2025, 9, 30))
VERSION = DocumentVersion(
    sha256=SHA,
    edition=EditionKey("qcmr", QUARTER),
    listed_at="20251101000000",
    urls=(),
    title="Quarterly City Managers Report",
    printed_period=QUARTER,
    supersedes=None,
)
POSITIONS = RowSchema("qcmr_positions", ())
CONTEXT = ParseContext(
    version=VERSION,
    schemas=(POSITIONS, RowSchema("qcmr_cash", ())),
    registry=Registry((), (), ()),
    cell_records=CellRecords((), (), 95.0),
    notes=(),
    table_pages=(),
)
NOTE = EditionNote("n1", NoteKind.HEADER_ILLEGIBLE, OTHER, 36, "", "", "the header is a blur")
BOX = Box(0.0, 0.0, 1.0, 1.0)
PAGES = TablePages("tp1", OTHER, "qcmr_positions", 35, 36, "scan")


def test_a_context_names_the_period_and_fiscal_year_of_its_edition() -> None:
    assert CONTEXT.period == QUARTER
    assert CONTEXT.fiscal_year == 2026


def test_a_context_gives_the_schema_of_each_table_it_holds() -> None:
    assert CONTEXT.schema("qcmr_positions") is POSITIONS
    with pytest.raises(KeyError, match="qcmr_obligations"):
        CONTEXT.schema("qcmr_obligations")


def test_a_context_refuses_two_schemas_of_one_table() -> None:
    with pytest.raises(ValueError, match="qcmr_positions"):
        replace(CONTEXT, schemas=(POSITIONS, POSITIONS))


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"notes": (NOTE,)}, id="a_note"),
        pytest.param({"table_pages": (PAGES,)}, id="a_table_pages_record"),
        pytest.param(
            {
                "cell_records": CellRecords(
                    (
                        ReviewedReading(
                            "r1", OTHER, 36, BOX, SourceKind.TEXT_LAYER, "1", "1", "seen"
                        ),
                    ),
                    (),
                    95.0,
                )
            },
            id="a_reading",
        ),
    ],
)
def test_a_context_refuses_a_record_of_another_file(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="b" * 8):
        replace(CONTEXT, **changes)


def test_a_context_keeps_the_records_of_its_own_file() -> None:
    kept = replace(
        CONTEXT,
        notes=(replace(NOTE, doc_sha256=SHA),),
        table_pages=(replace(PAGES, doc_sha256=SHA),),
    )
    assert kept.notes[0].doc_sha256 == kept.table_pages[0].doc_sha256 == SHA


def test_a_failed_parse_needs_a_block_finding() -> None:
    warn = Finding(Severity.WARN, "commentary_page", "aaaaaaaa:qcmr_positions", "no caption", 34)
    with pytest.raises(ValueError, match="BLOCK"):
        Failed(())
    with pytest.raises(ValueError, match="BLOCK"):
        Failed((warn,))
    block = replace(warn, severity=Severity.BLOCK, code="table_not_found", page=None)
    assert Failed((warn, block)).findings == (warn, block)
