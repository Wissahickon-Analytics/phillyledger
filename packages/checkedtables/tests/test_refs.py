import math
import operator
from enum import Enum
from itertools import product
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from checkedtables.refs import Box, Sha256, WordRef

COMPARISONS = (operator.lt, operator.le, operator.gt, operator.ge)
HEX = "7c4a2e5abb00a5084cdb24fb35325cd1f2cdee42cfd9b30cf7c62c46c2f22918"
SHA = Sha256("a" * 64)
coordinates = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False)


@st.composite
def boxes(draw: st.DrawFn) -> Box:
    x0, x1 = sorted((draw(coordinates), draw(coordinates)))
    top, bottom = sorted((draw(coordinates), draw(coordinates)))
    return Box(x0, top, x1, bottom)


word_refs = st.builds(
    WordRef,
    doc_sha256=st.sampled_from(("a" * 64, "b" * 64)).map(Sha256),
    page=st.integers(1, 3),
    index=st.integers(0, 3),
    child=st.none() | st.integers(0, 3),
)


def child_first_key(ref: WordRef) -> tuple[str, int, int, bool, int | None]:
    return (ref.doc_sha256, ref.page, ref.index, ref.child is not None, ref.child)


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
    with pytest.raises(ValueError, match="needs at least one box"):
        Box.around(())
    with pytest.raises(ValueError, match="needs at least one box"):
        Box.around(iter(()))


def test_box_contains_with_slack() -> None:
    cell = Box(10.0, 10.0, 20.0, 20.0)
    for slack in (0.0, 0.5):
        assert cell.contains(Box(12.0, 12.0, 18.0, 18.0), slack)
    for reach in (0.25, 1.0):
        for word in (
            Box(10.0 - reach, 12.0, 18.0, 18.0),
            Box(12.0, 10.0 - reach, 18.0, 18.0),
            Box(12.0, 12.0, 20.0 + reach, 18.0),
            Box(12.0, 12.0, 18.0, 20.0 + reach),
        ):
            for slack, contained in ((0.0, False), (reach / 2, False), (reach, True)):
                assert cell.contains(word, slack) is contained, (word, slack)


def test_word_ref_cites_a_file_and_a_page() -> None:
    nameless: Any = ""
    for doc_sha256, page, index, child, message in (
        (nameless, 1, 0, None, "not a Sha256"),
        (SHA, 0, 0, None, "page below 1"),
        (SHA, 1, -1, None, "index below 0"),
        (SHA, 1, 0, -1, "child below 0"),
    ):
        with pytest.raises(ValueError, match=message):
            WordRef(doc_sha256, page, index, child)
    assert WordRef(SHA, 1, 0, 0).child == 0


@given(st.lists(word_refs))
def test_word_refs_sort_with_and_without_child(refs: list[WordRef]) -> None:
    assert sorted(refs) == sorted(refs, key=child_first_key)
    for a, b in product(refs, repeat=2):
        for compare in COMPARISONS:
            assert compare(a, b) == compare(child_first_key(a), child_first_key(b)), (a, b)


def test_word_refs_compare_only_with_word_refs() -> None:
    for compare in COMPARISONS:
        with pytest.raises(TypeError):
            compare(WordRef(SHA, 1, 0), 1)


class OtherText(str):
    def __str__(self) -> str:
        return "other text"


class Digest(str, Enum):  # noqa: UP042
    SAMPLE = HEX


@given(st.text("0123456789abcdef", min_size=64, max_size=64))
def test_sha256_holds_64_lowercase_hex_characters_and_equals_its_text(text: str) -> None:
    sha = Sha256(text)
    assert type(sha) is Sha256
    assert sha == text
    assert hash(sha) == hash(text)
    assert (type(str(sha)), str(sha)) == (str, text)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param("", id="empty"),
        pytest.param(HEX.replace("c", "C", 1), id="an_uppercase_digit"),
        pytest.param(HEX[:63], id="63_characters"),
        pytest.param(f"{HEX}0", id="65_characters"),
        pytest.param(f"{HEX}\n", id="a_trailing_newline"),
        pytest.param(f"{HEX[:63]}g", id="a_letter_that_is_not_hex"),
        pytest.param(f"\N{FULLWIDTH DIGIT ZERO}{HEX[1:]}", id="a_decimal_digit_that_is_not_ascii"),
        pytest.param(None, id="none"),
        pytest.param(int(HEX, 16), id="a_number"),
        pytest.param(HEX.encode(), id="bytes"),
        pytest.param([HEX], id="a_list"),
    ],
)
def test_sha256_refuses_any_other_value(value: Any) -> None:
    with pytest.raises(ValueError, match="is not 64 lowercase hex characters"):
        Sha256(value)


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(OtherText(HEX), id="a_str_subclass_with_its_own_str"),
        pytest.param(Digest.SAMPLE, id="a_member_of_a_str_enum"),
    ],
)
def test_sha256_of_a_str_subclass_holds_the_text_it_checked(text: str) -> None:
    assert str(text) != HEX
    sha = Sha256(text)
    assert (type(sha), str(sha), len(sha)) == (Sha256, HEX, 64)


def test_the_repr_of_a_word_ref_rebuilds_its_sha256() -> None:
    ref = WordRef(Sha256(HEX), 2, 5, 1)
    names = {"Sha256": Sha256, "WordRef": WordRef}
    assert repr(Sha256(HEX)) == f"Sha256({HEX!r})"
    rebuilt = eval(repr(ref), names)
    assert rebuilt == ref
    assert type(rebuilt.doc_sha256) is Sha256


@pytest.mark.parametrize(
    "sha",
    [
        pytest.param(HEX, id="64_hex_characters_of_plain_text"),
        pytest.param("", id="empty"),
        pytest.param(None, id="none"),
    ],
)
def test_word_ref_refuses_a_sha_that_is_not_a_sha256(sha: Any) -> None:
    with pytest.raises(ValueError, match="not a Sha256"):
        WordRef(sha, 1, 0)
    assert WordRef(Sha256(HEX), 1, 0).doc_sha256 == HEX
