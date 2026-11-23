from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from string import digits

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from checkedtables.cells import Amount, Blank, Dash, NotApplicable, Reading, Text, Unreadable
from checkedtables.columns import ColumnSpec, NumberFormat
from checkedtables.kinds import DashMeaning, SourceKind, ValueKind
from checkedtables.lex import lex_cell, transliteration_ok
from checkedtables.records import ReviewedReading, apply_reading, reading_for
from checkedtables.refs import Box
from checkedtables.table import Finding, Severity
from checkedtables.testing import page_from_text
from checkedtables.words import Page, Word

SHA = "0123456789abcdef" * 4
PAGE = 4
OCR = SourceKind.OCR
CASH = ColumnSpec("cash", "Cash", ValueKind.MONEY, NumberFormat(decimals=1))
MONEY = ColumnSpec("money", "Money", ValueKind.MONEY, NumberFormat(decimals=None))
CONFUSABLE_GLYPHS = (
    ("B", "8"),
    ("b", "8"),
    ("D", "0"),
    ("d", "0"),
    ("O", "0"),
    ("o", "0"),
    ("Q", "0"),
    ("q", "0"),
    ("&", "6"),
)
SEEN_SEPARATORS = ("", " ", ",", ".", ": ")
SIGNED = ("{}", "({})", "-{}", "−{}", "–{}", "${}", "$({})", "(${})", "$-{}")
seen_parts = st.lists(
    st.tuples(
        st.sampled_from(SEEN_SEPARATORS),
        st.text(digits + "".join(glyph for glyph, _ in CONFUSABLE_GLYPHS), min_size=1, max_size=4),
    ),
    min_size=1,
    max_size=4,
)


def cash_row(cell: str, page: int = PAGE) -> tuple[Page, tuple[Word, ...]]:
    laid_out = page_from_text(f"#ocr\nTaxes {cell}", SHA, page)
    return laid_out, laid_out.words[1:]


def record(
    seen: str, reading: str | None, held: Sequence[Word], review: str = "r1"
) -> ReviewedReading:
    box = Box.around(word.box for word in held)
    return ReviewedReading(review, SHA, PAGE, box, OCR, seen, reading, "read on the rendered page")


def reviewed(text: str, reading: str | None, col: ColumnSpec = CASH) -> object:
    page, cell_words = cash_row(text)
    found = reading_for(cell_words, page.words, OCR, (record(text, reading, cell_words),))
    assert isinstance(found, ReviewedReading), found
    return apply_reading(lex_cell(cell_words, col, OCR), found)


def assert_finding(result: object, code: str, review: str = "r1", page: int = PAGE) -> None:
    assert isinstance(result, Finding), result
    subject = f"01234567:reading:{review}"
    assert (result.severity, result.code, result.subject, result.page) == (
        Severity.BLOCK,
        code,
        subject,
        page,
    )


def transliterated(seen: str) -> str:
    confusable = dict(CONFUSABLE_GLYPHS)
    return "".join(glyph if glyph in digits else confusable.get(glyph, "") for glyph in seen)


def test_a_reading_restores_a_lost_separator() -> None:
    # VAL-Q35
    page, cell_words = cash_row("2918")
    cell = lex_cell(cell_words, CASH, OCR)
    assert isinstance(cell, Unreadable)
    reading = record("2918", "291.8", cell_words)
    assert reading_for(cell_words, page.words, OCR, (reading,)) == reading
    refs = tuple(word.ref for word in cell_words)
    expected = Amount(Decimal("291.8"), "2918", refs, OCR, Reading.REVIEWED, "r1")
    assert apply_reading(cell, reading) == expected


def test_a_reading_replaces_letters_with_digits() -> None:
    # VAL-Q36
    result = reviewed("1o4.o", "104.0")
    assert isinstance(result, Amount)
    assert str(result.printed) == "104.0"
    assert (result.text, result.source, result.reading, result.review_id) == (
        "1o4.o",
        OCR,
        Reading.REVIEWED,
        "r1",
    )


def test_a_reading_cannot_change_a_digit() -> None:
    # QCASH-Q22, MSCH-Q26
    assert_finding(reviewed("65.8", "85.8"), "reading_refused")
    assert_finding(reviewed("77,500,000", "7,500,000", MONEY), "reading_refused")


def test_moved_text_makes_a_reading_stale() -> None:
    _, before = cash_row("2918")
    reading = record("2918", "291.8", before)
    for after in ("2913", "29 18"):
        page, cell_words = cash_row(after)
        assert_finding(reading_for(cell_words, page.words, OCR, (reading,)), "stale_reading")


def test_a_box_that_holds_part_of_a_cell_is_stale() -> None:
    page, cell_words = cash_row("(29 1)")
    reading = record("1)", "(29.1)", cell_words[1:])
    assert_finding(reading_for(cell_words, page.words, OCR, (reading,)), "stale_reading")


def test_two_readings_for_one_cell_is_a_finding() -> None:
    page, cell_words = cash_row("2918")
    cell_box = record("2918", "291.8", cell_words, "r2")
    row_box = record("Taxes 2918", None, page.words, "r1")
    result = reading_for(cell_words, page.words, OCR, (cell_box, row_box))
    assert_finding(result, "duplicate_reading")
    assert isinstance(result, Finding)
    assert "r1" in result.message and "r2" in result.message


def test_a_reading_on_another_page_or_source_is_no_candidate() -> None:
    page, cell_words = cash_row("2918")
    reading = record("2918", "291.8", cell_words)
    label_box = Box.around(word.box for word in page.words[:1])
    for other in (
        replace(reading, page=PAGE + 1),
        replace(reading, doc_sha256="f" * 64),
        replace(reading, source=SourceKind.TEXT_LAYER),
        replace(reading, box=label_box),
    ):
        assert reading_for(cell_words, page.words, OCR, (other,)) is None, other
    assert reading_for(cell_words, page.words, OCR, ()) is None
    assert reading_for(cell_words, page.words, OCR, (reading,)) == reading


def test_a_box_holds_a_word_within_one_point_of_it() -> None:
    page, cell_words = cash_row("2918")
    reading = record("2918", "291.8", cell_words)
    for shift, found in ((0.5, True), (-0.5, True), (2.0, False), (-2.0, False)):
        box = reading.box
        moved = replace(
            reading, box=Box(box.x0 + shift, box.top + shift, box.x1 + shift, box.bottom + shift)
        )
        expected = moved if found else None
        assert reading_for(cell_words, page.words, OCR, (moved,)) == expected, shift


def test_a_null_reading_accepts_an_unreadable_cell() -> None:
    # VAL-Q36
    _, cell_words = cash_row("B")
    cell = lex_cell(cell_words, CASH, OCR)
    assert isinstance(cell, Unreadable)
    assert apply_reading(cell, record("B", None, cell_words)) == replace(cell, accepted_by="r1")


def test_a_box_that_holds_two_cells_is_stale() -> None:
    page = page_from_text("#ocr\nTaxes 7 7", SHA, PAGE)
    first, second = page.words[1:]
    for seen in ("7", "7 7"):
        reading = record(seen, seen, (first, second))
        for cell_words in ((first,), (second,)):
            result = reading_for(cell_words, page.words, OCR, (reading,))
            assert_finding(result, "stale_reading")


def test_a_reading_never_lends_its_value_to_another_cell() -> None:
    _, cell_words = cash_row("65.8")
    cell = lex_cell(cell_words, CASH, OCR)
    assert_finding(apply_reading(cell, record("85.8", "85.8", cell_words)), "stale_reading")
    elsewhere = replace(record("65.8", "65.8", cell_words), page=PAGE + 1)
    assert_finding(apply_reading(cell, elsewhere), "stale_reading", page=PAGE + 1)


def test_a_negative_reading_is_read() -> None:
    # VAL-Q35
    page, cell_words = cash_row("(29 1)")
    cell = lex_cell(cell_words, CASH, OCR)
    assert isinstance(cell, Unreadable)
    reading = record("(29 1)", "(29.1)", cell_words)
    assert reading_for(cell_words, page.words[::-1], OCR, (reading,)) == reading
    result = apply_reading(cell, reading)
    assert isinstance(result, Amount)
    assert str(result.printed) == "-29.1"


def test_a_null_reading_on_an_amount_gives_reviewed_null() -> None:
    _, cell_words = cash_row("65.8")
    cell = lex_cell(cell_words, CASH, OCR)
    assert isinstance(cell, Amount)
    expected = Unreadable("65.8", cell.words, "reviewed_null", "r1")
    assert apply_reading(cell, record("65.8", None, cell_words)) == expected


def test_only_an_amount_or_an_unreadable_cell_takes_a_reading() -> None:
    _, cell_words = cash_row("2918")
    refs = tuple(word.ref for word in cell_words)
    for seen, cell in (
        ("", Blank()),
        ("-", Dash("-", refs, DashMeaning.NO_VALUE)),
        ("N/A", NotApplicable("N/A", refs)),
        ("2918", Text("2918", refs)),
    ):
        assert_finding(apply_reading(cell, record(seen, None, cell_words)), "reading_refused")
    text_cell = Text("2918", refs)
    assert_finding(apply_reading(text_cell, record("2918", "291.8", cell_words)), "reading_refused")


def test_a_reading_that_is_not_one_signed_number_is_refused() -> None:
    _, cell_words = cash_row("2918")
    cell = lex_cell(cell_words, CASH, OCR)
    for reading in ("29,18", "+291.8", "291.8-", "2 91.8", "((291.8))", "2.9.18", "291.8 B"):
        assert transliteration_ok("2918", reading), reading
        result = apply_reading(cell, record("2918", reading, cell_words))
        assert_finding(result, "reading_refused")


def test_a_reading_needs_an_id() -> None:
    _, cell_words = cash_row("2918")
    with pytest.raises(ValueError, match="id"):
        record("2918", "291.8", cell_words, "")


@given(seen_parts, st.integers(1, 16), st.sampled_from(("", ",")), st.sampled_from(SIGNED))
@example([("", "2918")], 3, "", "{}")
@example([("", "29"), (" ", "1")], 2, "", "({})")
@example([("", "69"), (",", "2")], 2, ",", "{}")
@example([("", "67"), (": ", "3")], 2, "", "-{}")
@example([("", "1o4.o")], 3, "", "{}")
@example([("", "0o7")], 3, ",", "$({})")
def test_a_reviewed_amount_keeps_the_digits_seen(
    parts: list[tuple[str, str]], point: int, grouping: str, sign: str
) -> None:
    seen = parts[0][1] + "".join(separator + chunk for separator, chunk in parts[1:])
    seen_digits = transliterated(seen)
    whole = 1 if seen_digits[0] == "0" else min(point, len(seen_digits))
    number = format(int(seen_digits[:whole]), grouping)
    fraction = seen_digits[whole:]
    reading = sign.format(f"{number}.{fraction}" if fraction else number)
    page, cell_words = cash_row(seen)
    found = reading_for(cell_words, page.words, OCR, (record(seen, reading, cell_words),))
    assert isinstance(found, ReviewedReading), (seen, found)
    result = apply_reading(lex_cell(cell_words, CASH, OCR), found)
    assert isinstance(result, Amount), (seen, reading, result)
    assert transliterated(format(result.printed.copy_abs(), "f")) == seen_digits, (seen, reading)
