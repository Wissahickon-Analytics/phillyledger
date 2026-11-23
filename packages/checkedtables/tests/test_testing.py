import pytest

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, WordRef
from checkedtables.testing import doc_of, page_from_text
from checkedtables.words import Document

SHA = "a" * 64
OTHER_SHA = "b" * 64


def test_page_from_text_lays_out_six_by_twelve() -> None:
    page = page_from_text("Total  1,234\n\n  Net 5", SHA, 3)
    assert [(word.text, word.box) for word in page.words] == [
        ("Total", Box(0.0, 0.0, 30.0, 12.0)),
        ("1,234", Box(42.0, 0.0, 72.0, 12.0)),
        ("Net", Box(12.0, 24.0, 30.0, 36.0)),
        ("5", Box(36.0, 24.0, 42.0, 36.0)),
    ]
    assert [word.ref for word in page.words] == [WordRef(SHA, 3, index) for index in range(4)]
    assert (page.doc_sha256, page.number, page.width, page.height, page.rotation) == (
        SHA,
        3,
        72.0,
        36.0,
        0,
    )
    assert page.source.kind is SourceKind.TEXT_LAYER
    assert {(word.bold, word.size, word.confidence) for word in page.words} == {(False, 12.0, None)}


def test_double_asterisks_mark_bold_words() -> None:
    page = page_from_text("**Total Revenue** 1,234\nRefunds **12**\nTotal RTT records **1", SHA, 1)
    assert [(word.text, word.bold) for word in page.words] == [
        ("Total", True),
        ("Revenue", True),
        ("1,234", False),
        ("Refunds", False),
        ("12", True),
        ("Total", False),
        ("RTT", False),
        ("records", False),
        ("**1", False),
    ]
    assert page.words[2].box == Box(84.0, 0.0, 114.0, 12.0)
    assert page.words[4].box == Box(48.0, 12.0, 60.0, 24.0)
    assert page.width == 6.0 * len("Total RTT records **1")


def test_a_literal_mark_before_a_bold_value_stays_in_the_text() -> None:
    # RTT-Q38
    page = page_from_text("Total RTT records **1  **1,234**", SHA, 1)
    assert [(word.text, word.bold, word.box) for word in page.words[-2:]] == [
        ("**1", False, Box(108.0, 0.0, 126.0, 12.0)),
        ("1,234", True, Box(138.0, 0.0, 168.0, 12.0)),
    ]


def test_two_bold_spans_on_one_line() -> None:
    page = page_from_text("**Taxes** 12 **Fees 34**", SHA, 1)
    assert [(word.text, word.bold) for word in page.words] == [
        ("Taxes", True),
        ("12", False),
        ("Fees", True),
        ("34", True),
    ]


def test_a_literal_mark_after_a_bold_span_stays_in_the_text() -> None:
    # RTT-Q38
    page = page_from_text("**Total** 12 **1", SHA, 1)
    assert [(word.text, word.bold) for word in page.words] == [
        ("Total", True),
        ("12", False),
        ("**1", False),
    ]


def test_double_asterisks_inside_a_word_open_and_close_nothing() -> None:
    page = page_from_text("**ab**cd ef", SHA, 1)
    assert [(word.text, word.bold) for word in page.words] == [("**ab**cd", False), ("ef", False)]


def test_a_word_of_only_asterisks_stays_in_the_text() -> None:
    page = page_from_text("Total ** *** **** 12", SHA, 1)
    assert [(word.text, word.bold) for word in page.words] == [
        ("Total", False),
        ("**", False),
        ("***", False),
        ("****", False),
        ("12", False),
    ]


def test_ocr_block_has_no_style() -> None:
    page = page_from_text("#ocr\n**Total** 1,234", SHA, 1)
    assert page.source.kind is SourceKind.OCR
    assert [(word.text, word.bold, word.size, word.confidence) for word in page.words] == [
        ("Total", None, None, 100.0),
        ("1,234", None, None, 100.0),
    ]
    assert page.words[1].box == Box(36.0, 0.0, 66.0, 12.0)
    assert (page.width, page.height) == (66.0, 12.0)


def test_doc_of_refuses_two_hashes() -> None:
    with pytest.raises(ValueError, match="one file"):
        doc_of(page_from_text("a", SHA, 1), page_from_text("b", OTHER_SHA, 2))


def test_doc_of_sorts_pages_and_refuses_repeats() -> None:
    third, first = page_from_text("c", SHA, 3), page_from_text("a", SHA, 1)
    assert doc_of(third, first) == Document(SHA, (first, third))
    with pytest.raises(ValueError, match="at least one page"):
        doc_of()
    with pytest.raises(ValueError, match="page 1 twice"):
        doc_of(first, third, page_from_text("again", SHA, 1))
