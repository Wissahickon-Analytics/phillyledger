"""A `PdfReader` adapter on pdfplumber."""

from io import BytesIO

import pdfplumber
from pdfminer.pdfpage import PDFPage
from pdfplumber.page import Page

from datadesk.shell.ports import EffectError


class PdfPlumberReader:
    """Read PDFs with pdfplumber, which reads a page's text layer and no image on it."""

    def page1_text(self, pdf: bytes) -> str:
        """Return the text that pdfplumber extracts from page 1.

        It builds page 1 alone, so a broken box on a later page does not stop it.

        Raises
        ------
        EffectError
            For any error pdfplumber raises.
        """
        try:
            document = pdfplumber.open(BytesIO(pdf))
            page1 = next(PDFPage.create_pages(document.doc))
            return Page(document, page1, page_number=1).extract_text()
        except Exception as error:
            raise EffectError(f"pdfplumber cannot read page 1: {error!r}") from error
