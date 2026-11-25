import math
from dataclasses import replace
from typing import Any

import pytest

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, WordRef
from checkedtables.words import Document, Page, Word, WordSource

SHA = "a" * 64
OTHER_SHA = "b" * 64
TEXT_LAYER = WordSource(SourceKind.TEXT_LAYER, "pdfplumber==0.11.4;dedupe_chars")
OCR = WordSource(SourceKind.OCR, "textract:AnalyzeDocument;dpi=300")


def word(sha: str, page: int, index: int) -> Word:
    return Word(WordRef(sha, page, index), "1,234", Box(0.0, 0.0, 10.0, 10.0), None, None, None)


def page(number: int, words: tuple[Word, ...]) -> Page:
    return Page(SHA, number, 612.0, 792.0, 0, TEXT_LAYER, words)


def test_page_refuses_a_word_from_another_page() -> None:
    with pytest.raises(ValueError, match="does not belong to page 1"):
        page(1, (word(SHA, 1, 0), word(SHA, 2, 0)))
    with pytest.raises(ValueError, match="does not belong to page 2"):
        page(2, (word(SHA, 1, 0),))
    assert page(2, (word(SHA, 2, 0),)).words == (word(SHA, 2, 0),)


def test_page_refuses_a_word_from_another_document() -> None:
    with pytest.raises(ValueError, match="does not belong to page 1"):
        page(1, (word(OTHER_SHA, 1, 0),))


def test_text_layer_page_refuses_an_ocr_confidence() -> None:
    # QCASH-Q22: the text layer prints 85.8 where Textract read 65.8.
    ocr_word = replace(word(SHA, 1, 1), text="65.8", confidence=99.0)
    with pytest.raises(ValueError, match="OCR confidence on a text layer page"):
        page(1, (replace(word(SHA, 1, 0), text="85.8"), ocr_word))
    assert Page(SHA, 1, 612.0, 792.0, 0, OCR, (ocr_word,)).words == (ocr_word,)


def test_page_refuses_two_words_with_one_ref() -> None:
    first = word(SHA, 1, 0)
    with pytest.raises(ValueError, match="share the ref"):
        page(1, (first, replace(first, text="92.0", box=Box(20.0, 0.0, 30.0, 10.0))))
    children = tuple(replace(first, ref=WordRef(SHA, 1, 0, child)) for child in (0, 1))
    assert page(1, (first, *children)).words == (first, *children)


def test_word_refuses_a_confidence_outside_0_to_100() -> None:
    ocr_word = replace(word(SHA, 1, 0), confidence=99.0)
    below, above = math.nextafter(0.0, -math.inf), math.nextafter(100.0, math.inf)
    for confidence in (math.nan, below, above, 101.0):
        with pytest.raises(ValueError, match="confidence outside 0 to 100"):
            replace(ocr_word, confidence=confidence)
    for confidence in (0.0, 100.0, None):
        assert replace(ocr_word, confidence=confidence).confidence == confidence


def test_page_cites_a_file_and_a_page() -> None:
    for sha, number, message in (("", 1, "names no file"), (SHA, 0, "number below 1")):
        with pytest.raises(ValueError, match=message):
            Page(sha, number, 612.0, 792.0, 0, OCR, ())
    assert Page(SHA, 1, 612.0, 792.0, 0, OCR, ()).number == 1


def test_document_cites_a_file() -> None:
    with pytest.raises(ValueError, match="names no file"):
        Document("", ())
    assert Document(SHA, ()).sha256 == SHA


NOT_A_SHA256 = [
    pytest.param("a" * 64, id="64_hex_characters_of_plain_text"),
    pytest.param("", id="empty"),
]


@pytest.mark.parametrize("sha", NOT_A_SHA256)
def test_page_refuses_a_sha_that_is_not_a_sha256(sha: Any) -> None:
    from checkedtables.refs import Sha256

    with pytest.raises(ValueError, match="not a Sha256"):
        Page(sha, 1, 612.0, 792.0, 0, OCR, ())
    assert Page(Sha256(SHA), 1, 612.0, 792.0, 0, OCR, ()).doc_sha256 == SHA


@pytest.mark.parametrize("sha", NOT_A_SHA256)
def test_document_refuses_a_sha_that_is_not_a_sha256(sha: Any) -> None:
    from checkedtables.refs import Sha256

    with pytest.raises(ValueError, match="not a Sha256"):
        Document(sha, ())
    assert Document(Sha256(SHA), ()).sha256 == SHA


def test_document_page_returns_the_page() -> None:
    first, third = page(1, (word(SHA, 1, 0),)), page(3, ())
    document = Document(SHA, (first, third))
    assert document.page(1) is first
    assert document.page(3) is third
    with pytest.raises(KeyError):
        document.page(2)


def test_document_refuses_a_page_of_another_file() -> None:
    with pytest.raises(ValueError, match="does not belong to document"):
        Document(OTHER_SHA, (page(1, (word(SHA, 1, 0),)),))


def test_document_refuses_pages_out_of_order() -> None:
    first, third = page(1, ()), page(3, ())
    for pages in ((third, first), (first, first)):
        with pytest.raises(ValueError, match="strictly ascending"):
            Document(SHA, pages)


def test_word_source_keeps_the_tool_string() -> None:
    # VAL-Q07: OCR output depends on the render dpi and the API, so the tool string names both.
    tool = "textract:AnalyzeDocument;dpi=300"
    source = WordSource(SourceKind.OCR, tool)
    assert source.tool == tool
    assert source != WordSource(SourceKind.OCR, "textract:AnalyzeDocument;dpi=200")
