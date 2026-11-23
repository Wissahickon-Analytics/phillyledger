import math
import operator
from itertools import product

import pytest
from checkedtables.refs import Box, WordRef
from hypothesis import given
from hypothesis import strategies as st

COMPARISONS = (operator.lt, operator.le, operator.gt, operator.ge)
coordinates = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False)


@st.composite
def boxes(draw: st.DrawFn) -> Box:
    x0, x1 = sorted((draw(coordinates), draw(coordinates)))
    top, bottom = sorted((draw(coordinates), draw(coordinates)))
    return Box(x0, top, x1, bottom)


word_refs = st.builds(
    WordRef,
    doc_sha256=st.sampled_from(("a" * 64, "b" * 64)),
    page=st.integers(1, 3),
    index=st.integers(0, 3),
    child=st.none() | st.integers(0, 3),
)


def child_first_key(ref: WordRef) -> tuple[str, int, int, int]:
    return (ref.doc_sha256, ref.page, ref.index, -1 if ref.child is None else ref.child)


def test_inverted_box_raises() -> None:
    for x0, top, x1, bottom in ((2.0, 0.0, 1.0, 1.0), (0.0, 2.0, 1.0, 1.0), (math.nan, 0, 1, 1)):
        with pytest.raises(ValueError, match="inverted box"):
            Box(x0, top, x1, bottom)
    assert Box(1.0, 1.0, 1.0, 1.0).x1 == 1.0


@given(st.lists(boxes(), min_size=1))
def test_box_around_holds_every_box(members: list[Box]) -> None:
    around = Box.around(iter(members))
    assert all(around.contains(box, 0.0) for box in members)
    assert around == Box(
        min(box.x0 for box in members),
        min(box.top for box in members),
        max(box.x1 for box in members),
        max(box.bottom for box in members),
    )


def test_box_around_nothing_raises() -> None:
    with pytest.raises(ValueError):
        Box.around(())
    with pytest.raises(ValueError):
        Box.around(iter(()))


def test_box_contains_with_slack() -> None:
    cell = Box(10.0, 10.0, 20.0, 20.0)
    word = Box(9.5, 10.0, 20.0, 20.5)
    assert not cell.contains(word, 0.0)
    assert cell.contains(word, 0.5)
    assert not cell.contains(Box(21.0, 10.0, 22.0, 20.0), 0.5)


@given(st.lists(word_refs))
def test_word_refs_sort_with_and_without_child(refs: list[WordRef]) -> None:
    assert sorted(refs) == sorted(refs, key=child_first_key)
    for a, b in product(refs, repeat=2):
        for compare in COMPARISONS:
            assert compare(a, b) == compare(child_first_key(a), child_first_key(b)), (a, b)
