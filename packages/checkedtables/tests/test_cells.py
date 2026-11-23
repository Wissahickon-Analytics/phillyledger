from decimal import Decimal

import pytest

from checkedtables.cells import Amount, Reading
from checkedtables.kinds import SourceKind
from checkedtables.refs import WordRef

REF = WordRef("a" * 64, 1, 0)


def ocr_amount(reading: Reading, review_id: str | None) -> Amount:
    return Amount(Decimal("104.0"), "1o4.o", (REF,), SourceKind.OCR, reading, review_id)


def test_amount_needs_words() -> None:
    with pytest.raises(ValueError, match="needs the words"):
        Amount(Decimal(1234), "1,234", (), SourceKind.TEXT_LAYER)
    assert Amount(Decimal(1234), "1,234", (REF,), SourceKind.TEXT_LAYER).words == (REF,)


def test_reviewed_amount_names_its_review_and_only_then() -> None:
    assert ocr_amount(Reading.REVIEWED, "qcash-fy07-q4-1").review_id == "qcash-fy07-q4-1"
    assert ocr_amount(Reading.DIRECT, None).reading is Reading.DIRECT
    for reading, review_id in ((Reading.REVIEWED, None), (Reading.DIRECT, "qcash-fy07-q4-1")):
        with pytest.raises(ValueError, match="names its review, and only then"):
            ocr_amount(reading, review_id)
