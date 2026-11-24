from io import BytesIO

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

from datadesk.shell.ports import EffectError


class PdfPlumberReader:
    def page1_text(self, pdf: bytes) -> str:
        try:
            with pdfplumber.open(BytesIO(pdf)) as document:
                return document.pages[0].extract_text()
        except (IndexError, PdfminerException) as error:
            raise EffectError(f"pdfplumber cannot read page 1: {error}") from error
