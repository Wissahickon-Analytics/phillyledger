from io import BytesIO

import pdfplumber
from pdfminer.pdfpage import PDFPage
from pdfplumber.page import Page

from datadesk.shell.ports import EffectError


class PdfPlumberReader:
    def page1_text(self, pdf: bytes) -> str:
        try:
            document = pdfplumber.open(BytesIO(pdf))
            page1 = next(PDFPage.create_pages(document.doc))
            return Page(document, page1, page_number=1).extract_text()
        except Exception as error:
            raise EffectError(f"pdfplumber cannot read page 1: {error!r}") from error
