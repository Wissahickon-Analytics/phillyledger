"""The QCMR positions table, P-1 (design section 5.1). Whole QCMR PDF in, one Table out.

The table prints ten count columns: General, Other and Total under each of three group
captions, then the variance (QPOS-Q01). The captions are written as the archived reports of
FY2022 to FY2026 print them, in capitals. Each fund column binds by its own caption inside the
rule band of its group, never by its place in the row (QPOS-Q02). The tenth column prints
"MONTH END", "ACTUAL (OVER)" and "UNDER BUDGET" on three header lines and has no group, so its
caption regex starts at "MONTH" to caption the column with all three.

The rows are the closed schema of ``datadesk/data/rows/qcmr_positions.toml``, and the registry
spells every department (design section 7.2).
"""

from datetime import date
from re import compile
from typing import assert_never

from checkedtables.assemble import assemble
from checkedtables.columns import ColumnSpec, Era, NumberFormat
from checkedtables.kinds import ValueKind
from checkedtables.lines import Line, page_lines
from checkedtables.pages import BodyRule, PageRun, find_runs, only_run
from checkedtables.pipeline import CutPages, Layout, cut_pages
from checkedtables.rows import RowSchema, match_rows, starts_known_row, stray_findings
from checkedtables.table import Finding, TableId
from checkedtables.words import Document
from datadesk.core.context import Failed, ParseContext, Parsed, ParseResult
from datadesk.core.records import declared_run, illegible_pages

TABLE = "qcmr_positions"
_COUNT = NumberFormat(decimals=0)
_GROUPS = (
    ("prior", r"YEAR\s+END\s+ACTUAL"),
    ("adopted", r"ADOPTED\s+BUDGET"),
    ("actual", r"MONTH\s+END\s+ACTUAL"),
)
_FUNDS = (("general", "General"), ("other", "Other"), ("total", "Total"))
_OVER = r"\(OVER\)"

COLUMNS: tuple[ColumnSpec, ...] = (
    *(
        ColumnSpec(f"{group}_{fund}", caption, ValueKind.COUNT, _COUNT, group=printed)
        for group, printed in _GROUPS
        for fund, caption in _FUNDS
    ),
    ColumnSpec("over_under", rf"MONTH\s+END\s+ACTUAL\s+{_OVER}\s*UNDER", ValueKind.COUNT, _COUNT),
)
ERAS = (
    Era(
        "p1_ten_columns",
        signature=(*(printed for _, printed in _GROUPS), _OVER),
        columns=COLUMNS,
        expected=(date(2007, 7, 1), None),
    ),
)

# "23 Civilian" and "I Uniform" on the scans (QPOS-Q08), and the two digits of the sideways
# page number that join a row in FY2022 Q1 to FY2023 Q3 (QPOS-Q10).
_LINE_NO = r"(?:\d{1,2}|I)"
_COUNT_WORD = compile(r"\(?\d[\d,]*\)?")


def _layout(schema: RowSchema) -> Layout:
    """Return how `parse` cuts the pages of one edition, whose rows `schema` holds.

    The body starts at the first line that opens with a label of the schema or ends with a
    count for each column. It stops at TOTAL ALL FUNDS. The schema's ``drop`` makes the
    footnotes and the notice under the rows of the first grid page furniture, and a line of
    line number words alone, such as the page number at the foot, is furniture too.

    Parameters
    ----------
    schema : RowSchema
        The positions rows of the edition, from `schema_for`.
    """
    known = starts_known_row(schema)

    def starts(line: Line) -> bool:
        return known(line) or _ends_with_counts(line)

    body = BodyRule(start=starts, stop=_is_grand_total, drop=schema.drop, prefix=_LINE_NO)
    return Layout(TABLE, ERAS, body)


def parse(doc: Document, ctx: ParseContext) -> ParseResult:
    """Read Table P-1 from the words of a whole QCMR report.

    The run is the pages that a `TablePages` record names, or else the one run of pages whose
    two-line band prints TABLE P-1. A page before the grid that prints no caption of the era's
    signature, such as the commentary page of 16 of the 20 editions of FY2022 to FY2026, is a
    WARN ``commentary_page`` finding and is not cut. The rows match the
    edition's schema, and a page that a HEADER_ILLEGIBLE note names binds its columns by
    position.

    Returns
    -------
    ParseResult
        `Parsed` with the table, the cut it was assembled from, every finding of the cut, the
        match, the assembly and the strays, sorted, and the ids of the records used. `Failed`
        with the one finding when no run, or more than one, prints the band, or when the cut
        stops, and with every finding when the assembly builds no table.
    """
    schema = ctx.schema(TABLE)
    pages = tuple(page_lines(page) for page in doc.pages)
    declared, pages_used = declared_run(ctx.table_pages, TABLE)
    run = declared or only_run(find_runs(pages, _is_p1), f"{doc.sha256[:8]}:{TABLE}")
    match run:
        case PageRun():
            pass
        case Finding():
            return Failed((run,))
        case _:
            assert_never(run)
    positional, notes_used = illegible_pages(ctx.notes, doc.sha256)
    cut = cut_pages(_layout(schema), run.take(pages), ctx.period.end, positional)
    match cut:
        case CutPages():
            pass
        case Finding():
            return Failed((cut,))
        case _:
            assert_never(cut)
    matched = match_rows(cut.raws, schema)
    built = assemble(TableId(TABLE), cut, matched.rows, ctx.cell_records)
    findings = (*cut.findings, *matched.findings, *built.findings, *stray_findings(cut.raws))
    if built.table is None:
        return Failed(tuple(sorted(findings)))
    used = built.used | notes_used | pages_used
    return Parsed((built.table,), (cut,), tuple(sorted(findings)), used)


def _is_p1(band: str) -> bool:
    return "TABLE P-1" in band.upper()


def _is_grand_total(line: Line) -> bool:
    return "TOTAL ALL FUNDS" in line.text.upper()


def _ends_with_counts(line: Line) -> bool:
    """Return whether a line has a word before a count word for each column, as a row has."""
    tail = line.words[-len(COLUMNS) :]
    return len(line.words) > len(COLUMNS) and all(_COUNT_WORD.fullmatch(w.text) for w in tail)
