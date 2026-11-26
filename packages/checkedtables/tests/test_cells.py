from decimal import Decimal

import pytest

from checkedtables.cells import Amount, Dash, Reading
from checkedtables.kinds import DashMeaning, SourceKind
from checkedtables.refs import Sha256, WordRef

REF = WordRef(Sha256("a" * 64), 1, 0)
REVIEW = "qcash-fy07-q4-1"


def ocr_amount(text: str, reading: Reading, review_id: str | None) -> Amount:
    return Amount(Decimal("104.0"), text, (REF,), SourceKind.OCR, reading, review_id)


def test_amount_needs_words() -> None:
    with pytest.raises(ValueError, match="needs the words"):
        Amount(Decimal(1234), "1,234", (), SourceKind.TEXT_LAYER)
    assert Amount(Decimal(1234), "1,234", (REF,), SourceKind.TEXT_LAYER).words == (REF,)


def test_reviewed_amount_names_its_review_and_only_then() -> None:
    assert ocr_amount("1o4.o", Reading.REVIEWED, REVIEW).review_id == REVIEW
    assert ocr_amount("104.0", Reading.DIRECT, None).reading is Reading.DIRECT
    for reading, review_id in ((Reading.REVIEWED, None), (Reading.DIRECT, REVIEW)):
        with pytest.raises(ValueError, match="names its review, and only then"):
            ocr_amount("104.0", reading, review_id)


def test_amount_refuses_an_empty_review_id() -> None:
    for reading in Reading:
        with pytest.raises(ValueError, match="empty review id"):
            ocr_amount("1o4.o", reading, "")
    assert ocr_amount("1o4.o", Reading.REVIEWED, "r").review_id == "r"
    assert ocr_amount("104.0", Reading.DIRECT, None).review_id is None


def test_dash_needs_words() -> None:
    for meaning in DashMeaning:
        with pytest.raises(ValueError, match="needs the words"):
            Dash("-", (), meaning)
        assert Dash("-", (REF,), meaning).words == (REF,)
