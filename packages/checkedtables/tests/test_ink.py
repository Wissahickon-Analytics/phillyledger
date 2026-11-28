from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st
from packages.checkedtables.tests.grid import ERA, ON, RULE_XS, header, values
from packages.checkedtables.tests.ink import misplaced

from checkedtables.assemble import assemble
from checkedtables.cells import Blank
from checkedtables.lines import page_lines
from checkedtables.pages import BodyRule
from checkedtables.pipeline import CutPages, Layout, cut_pages
from checkedtables.records import CellRecords
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.rows import RowDef, RowSchema, match_rows, starts_known_row, stray_findings
from checkedtables.table import Finding, RowKey, RowKind, Table, TableId
from checkedtables.testing import page_from_text
from checkedtables.words import Page, Rule

SHA = Sha256("a" * 64)
POLICE = RowKey.of(dept="police")
ROOT = RowKey.of(line="total_all_funds")
SCHEMA = RowSchema(
    "staff",
    (
        RowDef(RowKey.of(dept="parks"), RowKind.ITEM, ("Parks",)),
        RowDef(RowKey.of(dept="roads"), RowKind.ITEM, ("Roads",)),
        RowDef(POLICE, RowKind.SUBTOTAL, ("Police - Total",)),
        RowDef(
            RowKey.of(breakdown="civilian", dept="police"),
            RowKind.BREAKDOWN,
            ("Civilian",),
            parent=POLICE,
            within=POLICE,
        ),
        RowDef(
            RowKey.of(breakdown="uniform", dept="police"),
            RowKind.BREAKDOWN,
            ("Uniform",),
            parent=POLICE,
            within=POLICE,
        ),
        RowDef(RowKey.of(dept="harbor_fund"), RowKind.ITEM, ("Harbor Fund",)),
        RowDef(ROOT, RowKind.TOTAL, ("TOTAL ALL FUNDS",)),
    ),
    root=ROOT,
)
LAYOUT = Layout(
    "staff",
    (ERA,),
    BodyRule(
        start=starts_known_row(SCHEMA),
        stop=lambda line: line.text.startswith("TOTAL"),
        drop=(r"^NOTE:",),
        prefix=r"\d{1,2}|I",
    ),
)
TOTAL = values("TOTAL ALL FUNDS", "132", "33", "154", "44", "22")
BLOCKS = (
    ("Roads",),
    ("Police - Total", "Civilian", "Uniform"),
    ("Harbor Fund",),
    ("Zoo",),
    ("Dock",),
)
LABELS = tuple(label for block in BLOCKS for label in block)
PREFIX = st.sampled_from(("", "", "9 ", "I "))
VALUE = st.sampled_from(("", "-", "0", "7", "42", "999", "(12)"))
EXAMPLE = "\n".join(
    (
        header(),
        values("Roads", "12", "3", "14", "4", "2"),
        values("9 Parks", "1", "-", "", "4", "(12)"),
        "NOTE: see below",
        values("Zoo", "1", "2", "3", "4", "5").ljust(66) + "99 zz",
        "7",
        TOTAL,
        "NOTE: preliminary",
    )
)


def laid_out(text: str) -> Page:
    rules = tuple(Rule(Box(x, 12.0, x, 12.0 * (text.count("\n") + 1))) for x in RULE_XS)
    return replace(page_from_text(text, SHA, 3), rules=rules)


def parsed(page: Page) -> tuple[CutPages, Table, tuple[Finding, ...]]:
    cut = cut_pages(LAYOUT, (page_lines(page),), ON)
    assert isinstance(cut, CutPages), cut
    matched = match_rows(cut.raws, SCHEMA)
    built = assemble(TableId("staff"), cut, matched.rows, CellRecords((), (), 95.0))
    assert built.table is not None, built.findings
    findings = (*cut.findings, *matched.findings, *built.findings, *stray_findings(cut.raws))
    return cut, built.table, findings


@st.composite
def table_pages(draw: st.DrawFn) -> str:
    by_block = st.permutations(BLOCKS).map(lambda blocks: sum(blocks, ()))
    labels = draw(st.one_of(st.permutations(LABELS), by_block))
    opener = values("Parks", *draw(st.lists(VALUE, min_size=5, max_size=5)))
    lines = [opener] if draw(st.booleans()) else []
    count = draw(st.one_of(st.just(len(labels)), st.integers(0, len(labels))))
    for label in labels[:count]:
        if label == "Harbor Fund" and draw(st.booleans()):
            lines.append(draw(PREFIX) + "Harbor")
            label = "Fund"
        line = values(draw(PREFIX) + label, *draw(st.lists(VALUE, min_size=5, max_size=5)))
        stray = draw(st.sampled_from(("", "zz", "99 zz")))
        lines.append(f"{line.ljust(66)}{stray}" if stray else line)
        lines += draw(st.lists(st.sampled_from(("NOTE: see below", "7")), max_size=1))
    lines.append(TOTAL)
    lines += draw(st.lists(st.sampled_from(("NOTE: preliminary", "7")), max_size=2))
    source = draw(st.sampled_from(("", "#ocr\n")))
    return source + "\n".join((header(), *lines))


@given(table_pages())
def test_no_ink_is_lost_on_a_generated_table_page(text: str) -> None:
    page = laid_out(text)
    cut, table, findings = parsed(page)
    assert misplaced((page,), cut, table, findings) == {}


def test_the_ledger_finds_a_ref_taken_out() -> None:
    page = laid_out(EXAMPLE)
    cut, table, findings = parsed(page)
    assert misplaced((page,), cut, table, findings) == {}
    roads = table.rows[0]
    emptied = replace(roads, cells=(Blank(), *roads.cells[1:]))
    [twelve] = cut.raws[0].cells[0][1]
    assert misplaced((page,), cut, replace(table, rows=(emptied, *table.rows[1:])), findings) == {
        twelve.ref: 0
    }
    [stray, _] = cut.raws[2].stray
    no_stray = tuple(f for f in findings if f.code != "stray_value")
    assert misplaced((page,), cut, table, no_stray) == {stray.ref: 0}
    zoo = cut.raws[2]
    no_unknown = tuple(f for f in findings if f.code != "unknown_row")
    zoo_words = (*zoo.label_words, *(word for _, cell in zoo.cells for word in cell))
    assert misplaced((page,), cut, table, no_unknown) == {word.ref: 0 for word in zoo_words}


def test_the_ledger_finds_a_ref_counted_twice() -> None:
    page = laid_out(EXAMPLE)
    cut, table, findings = parsed(page)
    roads = table.rows[0]
    twelve = cut.raws[0].cells[0][1][0].ref
    doubled = replace(roads, label_words=(*roads.label_words, twelve))
    twice = replace(table, rows=(doubled, *table.rows[1:]))
    assert misplaced((page,), cut, twice, findings) == {twelve: 2}
    foreign = WordRef(SHA, 9, 0)
    elsewhere = replace(roads, label_words=(*roads.label_words, foreign))
    outside = replace(table, rows=(elsewhere, *table.rows[1:]))
    assert misplaced((page,), cut, outside, findings) == {foreign: 1}
