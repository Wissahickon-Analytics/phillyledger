import operator
from dataclasses import replace
from decimal import Decimal
from itertools import product

import pytest
from hypothesis import given
from hypothesis import strategies as st

from checkedtables.cells import Amount, Blank
from checkedtables.kinds import SourceKind, ValueKind
from checkedtables.labels import Label
from checkedtables.refs import Sha256, WordRef
from checkedtables.table import (
    Additivity,
    Column,
    Finding,
    Row,
    RowKey,
    RowKind,
    Severity,
    Table,
    TableId,
    additivity_of,
)

SHA = Sha256("a" * 64)
COMPARISONS = (operator.lt, operator.le, operator.gt, operator.ge)
POLICE = RowKey.of(dept="phl_dept_police")
CIVILIAN = RowKey.of(breakdown="civilian", dept="phl_dept_police")
UNIFORM = RowKey.of(breakdown="uniform", dept="phl_dept_police")
ROOT = RowKey.of(line="total_all_funds")
COLUMNS = (
    Column("actual_general", ValueKind.COUNT, "General", True),
    Column("actual_other", ValueKind.COUNT, "Other", True),
)
names = st.text(st.characters(exclude_characters="|="), min_size=1)
values = st.text(st.characters(exclude_characters="|="))
findings = st.builds(
    Finding,
    severity=st.sampled_from(Severity),
    code=st.sampled_from(("unknown_row", "style_unavailable")),
    subject=st.sampled_from(("a1b2c3d4:positions:dept=police", "a1b2c3d4:positions:dept=fire")),
    message=st.sampled_from(("", "row printed twice")),
    page=st.none() | st.integers(1, 3),
)


def page_first_key(finding: Finding) -> tuple[str, str, str, str, bool, int | None]:
    return (
        finding.severity.value,
        finding.code,
        finding.subject,
        finding.message,
        finding.page is not None,
        finding.page,
    )


@given(st.dictionaries(names, values, min_size=1))
def test_row_key_parse_inverts_str(parts: dict[str, str]) -> None:
    key = RowKey.of(**parts)
    assert key.parts == tuple(sorted(parts.items()))
    assert RowKey.parse(str(key)) == key


def test_row_key_prints_its_parts_by_name() -> None:
    key = RowKey.of(dept="phl_dept_police", breakdown="civilian")
    assert str(key) == "breakdown=civilian|dept=phl_dept_police"


def test_row_key_refuses_unsorted_names() -> None:
    for parts in (
        (("dept", "phl_dept_police"), ("breakdown", "civilian")),
        (("dept", "phl_dept_police"), ("dept", "phl_dept_fire")),
    ):
        with pytest.raises(ValueError, match="strictly ascending"):
            RowKey(parts)
    with pytest.raises(ValueError, match="strictly ascending"):
        RowKey.parse("b=1|a=2")


def test_row_key_refuses_empty_names_and_separators() -> None:
    for parts in (
        (),
        (("", "civilian"),),
        (("dept|line", "total"),),
        (("dept=line", "total"),),
        (("line", "total|grand"),),
        (("line", "total=grand"),),
    ):
        with pytest.raises(ValueError):
            RowKey(parts)
    for text in ("", "line", "line=total|", "=total"):
        with pytest.raises(ValueError):
            RowKey.parse(text)


def test_row_key_has_occurrence() -> None:
    assert RowKey.of(label="acme", occurrence="2").has_occurrence
    assert not RowKey.of(label="acme").has_occurrence
    assert not RowKey.of(label="occurrence").has_occurrence


@given(st.lists(findings))
def test_findings_sort_with_and_without_page(found: list[Finding]) -> None:
    assert sorted(found) == sorted(found, key=page_first_key)
    for a, b in product(found, repeat=2):
        for compare in COMPARISONS:
            assert compare(a, b) == compare(page_first_key(a), page_first_key(b)), (a, b)


def test_findings_compare_only_with_findings() -> None:
    finding = Finding(Severity.BLOCK, "unknown_row", "a1b2c3d4:positions:dept=police", "")
    for compare in COMPARISONS:
        with pytest.raises(TypeError):
            compare(finding, 1)


def amount(value: str, index: int) -> Amount:
    return Amount(Decimal(value), value, (WordRef(SHA, 3, index),), SourceKind.TEXT_LAYER)


def row(key: RowKey, kind: RowKind, parent: RowKey | None, general: str, other: str) -> Row:
    label = Label(str(key), str(key), str(key), str(key), (), None)
    cells = (amount(general, 2 * len(general)), amount(other, 2 * len(other) + 1))
    return Row(key, kind, label, parent, 3, (), cells, None, None)


ROWS = (
    row(POLICE, RowKind.SUBTOTAL, ROOT, "10", "2"),
    row(CIVILIAN, RowKind.BREAKDOWN, POLICE, "4", "1"),
    row(UNIFORM, RowKind.BREAKDOWN, POLICE, "6", "1"),
    row(ROOT, RowKind.TOTAL, None, "10", "2"),
)
TABLE = Table(TableId("qcmr_positions"), SHA, "p1_ten_columns", (3,), COLUMNS, ROWS)


def test_each_row_kind_adds_up_as_its_additivity() -> None:
    assert {kind: additivity_of(kind) for kind in RowKind} == {
        RowKind.HEADING: Additivity.NONE,
        RowKind.ITEM: Additivity.ADDITIVE,
        RowKind.SUBTOTAL: Additivity.ADDITIVE,
        RowKind.TOTAL: Additivity.ADDITIVE,
        RowKind.BREAKDOWN: Additivity.COMPONENT,
        RowKind.MEMO: Additivity.NONE,
    }
    assert [each.additivity for each in ROWS] == [
        Additivity.ADDITIVE,
        Additivity.COMPONENT,
        Additivity.COMPONENT,
        Additivity.ADDITIVE,
    ]


def test_a_table_id_prints_its_name_then_its_instance_parts() -> None:
    plain = TableId("qcmr_positions")
    by_fund = TableId("supplemental_revenues", (("fund", "phl_fund_general"),))
    assert str(plain) == "qcmr_positions"
    assert str(by_fund) == "supplemental_revenues|fund=phl_fund_general"
    assert by_fund.part("fund") == "phl_fund_general"
    with pytest.raises(KeyError):
        by_fund.part("zone")
    with pytest.raises(KeyError):
        plain.part("fund")


def test_a_table_reads_a_cell_a_row_and_the_children_of_a_row() -> None:
    assert TABLE.cell(CIVILIAN, "actual_general") == ROWS[1].cells[0]
    assert TABLE.cell(UNIFORM, "actual_other") == ROWS[2].cells[1]
    assert TABLE.row(POLICE) == ROWS[0]
    assert TABLE.row(RowKey.of(dept="phl_dept_fire")) is None
    assert TABLE.children(POLICE) == (ROWS[1], ROWS[2])
    assert TABLE.children(ROOT) == (ROWS[0],)
    assert TABLE.children(CIVILIAN) == ()
    with pytest.raises(KeyError):
        TABLE.cell(RowKey.of(dept="phl_dept_fire"), "actual_general")
    with pytest.raises(KeyError):
        TABLE.cell(POLICE, "adopted_general")


def test_a_table_refuses_two_rows_of_one_key_a_ragged_row_and_a_parent_it_lacks() -> None:
    with pytest.raises(ValueError, match="duplicate row keys"):
        replace(TABLE, rows=(*ROWS, ROWS[1]))
    ragged = replace(ROWS[1], cells=(Blank(),))
    with pytest.raises(ValueError, match="ragged row"):
        replace(TABLE, rows=(ROWS[0], ragged, ROWS[2], ROWS[3]))
    with pytest.raises(ValueError, match="parent key not in table"):
        replace(TABLE, rows=ROWS[1:])
