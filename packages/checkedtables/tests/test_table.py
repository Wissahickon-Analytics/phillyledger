import operator
from itertools import product

import pytest
from hypothesis import given
from hypothesis import strategies as st

from checkedtables.table import Finding, RowKey, Severity

COMPARISONS = (operator.lt, operator.le, operator.gt, operator.ge)
names = st.text(st.characters(exclude_characters="|="), min_size=1)
values = st.text(st.characters(exclude_characters="|="))
findings = st.builds(
    Finding,
    severity=st.sampled_from(Severity),
    code=st.sampled_from(("unknown_row", "style_unavailable")),
    subject=st.sampled_from(("a1b2c3d4:positions:dept=police",)),
    message=st.sampled_from(("", "row printed twice")),
    page=st.none() | st.integers(1, 3),
)


def page_first_key(finding: Finding) -> tuple[str, str, str, str, int]:
    page = -1 if finding.page is None else finding.page
    return (finding.severity.value, finding.code, finding.subject, finding.message, page)


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
