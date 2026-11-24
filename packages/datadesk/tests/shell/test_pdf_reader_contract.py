import pytest
from packages.datadesk.tests.shell.pdfs import image_pdf, text_pdf

from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.ports import EffectError

COVER = "FOR THE PERIOD ENDING SEPTEMBER 30, 2021"
SECOND_PAGE = "TABLE P-1 FULL-TIME POSITIONS"


def test_page1_text_holds_the_words_of_page_1_alone() -> None:
    text = PdfPlumberReader().page1_text(text_pdf(COVER, SECOND_PAGE))
    assert COVER in text
    assert SECOND_PAGE not in text


def test_page1_text_of_an_image_page_is_empty() -> None:
    assert PdfPlumberReader().page1_text(image_pdf()) == ""


@pytest.mark.parametrize(
    "pdf",
    [
        pytest.param(b"<html>Request blocked</html>", id="bytes_that_are_not_a_pdf"),
        pytest.param(text_pdf(), id="a_pdf_with_no_page"),
    ],
)
def test_page1_text_of_a_file_pdfplumber_cannot_read_is_an_effect_error(pdf: bytes) -> None:
    with pytest.raises(EffectError):
        PdfPlumberReader().page1_text(pdf)
