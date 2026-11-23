import pytest

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, WordRef
from checkedtables.words import Document, Page, Word, WordSource

SHA = "a" * 64
OTHER_SHA = "b" * 64
TEXT_LAYER = WordSource(SourceKind.TEXT_LAYER, "pdfplumber==0.11.4;dedupe_chars")


def word(sha: str, page: int, index: int) -> Word:
    return Word(WordRef(sha, page, index), "1,234", Box(0.0, 0.0, 10.0, 10.0), None, None, None)


def page(number: int, words: tuple[Word, ...]) -> Page:
    return Page(SHA, number, 612.0, 792.0, 0, TEXT_LAYER, words)


def test_page_refuses_a_word_from_another_page() -> None:
    with pytest.raises(ValueError, match="does not belong to page 1"):
        page(1, (word(SHA, 1, 0), word(SHA, 2, 0)))
    assert page(2, (word(SHA, 2, 0),)).words == (word(SHA, 2, 0),)


def test_page_refuses_a_word_from_another_document() -> None:
    with pytest.raises(ValueError, match="does not belong to page 1"):
        page(1, (word(OTHER_SHA, 1, 0),))


def test_document_page_returns_the_page() -> None:
    first, third = page(1, (word(SHA, 1, 0),)), page(3, ())
    document = Document(SHA, (first, third))
    assert document.page(1) is first
    assert document.page(3) is third
    with pytest.raises(KeyError):
        document.page(2)


def test_word_source_keeps_the_tool_string() -> None:
    # VAL-Q07: OCR output depends on the render dpi and the API, so the tool string names both.
    tool = "textract:AnalyzeDocument;dpi=300"
    source = WordSource(SourceKind.OCR, tool)
    assert source.tool == tool
    assert source != WordSource(SourceKind.OCR, "textract:AnalyzeDocument;dpi=200")
