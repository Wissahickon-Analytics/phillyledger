from hashlib import sha256
from re import escape
from typing import Any

import pytest

from checkedtables.kinds import SourceKind
from checkedtables.refs import Sha256
from datadesk.core import parse_plan
from datadesk.core.parse_plan import WordJob, WordKey, word_key

SHA = Sha256("5f238d579d4c1d7e2b3a4f5e6d7c8b9a0f1e2d3c4b5a69788796a5b4c3d2e1f0")
OTHER_SHA = Sha256("cbddaf2f9d4c1d7e2b3a4f5e6d7c8b9a0f1e2d3c4b5a69788796a5b4c3d2e1f0")
TOOL = "pdfplumber==0.11.10;pdfminer.six==20260107;words=1"
KEY = word_key(SHA, (35, 36), TOOL)


def test_a_word_key_is_the_sha256_of_the_format_the_sha_the_pages_and_the_tool() -> None:
    text = f'[1,"{SHA}",[35,36],"{TOOL}"]'
    assert sha256(text.encode()).hexdigest() == KEY
    assert type(KEY) is WordKey


@pytest.mark.parametrize(
    ("doc_sha256", "pages", "tool"),
    [
        pytest.param(OTHER_SHA, (35, 36), TOOL, id="another_sha"),
        pytest.param(SHA, (35,), TOOL, id="fewer_pages"),
        pytest.param(SHA, (34, 35), TOOL, id="other_pages"),
        pytest.param(SHA, (), TOOL, id="every_page"),
        pytest.param(SHA, (35, 36), TOOL.replace("words=1", "words=2"), id="another_tool"),
    ],
)
def test_a_word_key_changes_with_each_input(
    doc_sha256: Sha256, pages: tuple[int, ...], tool: str
) -> None:
    assert word_key(doc_sha256, pages, tool) != KEY


def test_a_word_key_changes_with_the_format_number(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(parse_plan, "FORMAT", parse_plan.FORMAT + 1)
    assert word_key(SHA, (35, 36), TOOL) != KEY


def test_a_word_key_equals_its_text_and_shows_its_type() -> None:
    text = "ab" * 32
    assert WordKey(text) == text
    assert repr(WordKey(text)) == f"WordKey('{text}')"


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("AB" * 32, id="upper_case"),
        pytest.param("a" * 63, id="63_characters"),
        pytest.param("a" * 65, id="65_characters"),
        pytest.param("g" * 64, id="not_hex"),
        pytest.param(f"{'a' * 64}\n", id="a_trailing_newline"),
        pytest.param(b"a" * 64, id="bytes"),
        pytest.param(None, id="none"),
    ],
)
def test_a_word_key_refuses_what_is_not_64_lowercase_hex_characters(text: Any) -> None:
    with pytest.raises(ValueError, match="not 64 lowercase hex"):
        WordKey(text)


def test_a_word_job_takes_ascending_pages_and_an_empty_tuple_for_every_page() -> None:
    assert WordJob(SHA, (1, 35, 36), SourceKind.TEXT_LAYER, None, KEY).pages == (1, 35, 36)
    assert WordJob(SHA, (), SourceKind.OCR, SourceKind.TEXT_LAYER, KEY).pages == ()


@pytest.mark.parametrize(
    "pages",
    [
        pytest.param((35, 35), id="a_page_twice"),
        pytest.param((36, 35), id="pages_out_of_order"),
        pytest.param((0, 35), id="a_page_below_1"),
        pytest.param((-2,), id="a_negative_page"),
    ],
)
def test_a_word_job_refuses_pages_that_are_not_strictly_ascending_from_1(
    pages: tuple[int, ...],
) -> None:
    with pytest.raises(ValueError, match=escape(str(pages))):
        WordJob(SHA, pages, SourceKind.TEXT_LAYER, None, KEY)
