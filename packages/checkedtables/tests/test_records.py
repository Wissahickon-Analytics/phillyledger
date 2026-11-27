from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from string import digits
from typing import Any

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from checkedtables.cells import Amount, Blank, Dash, NotApplicable, Reading, Text, Unreadable
from checkedtables.columns import ColumnSpec, NumberFormat
from checkedtables.kinds import DashMeaning, SourceKind, UnreadableReason, ValueKind
from checkedtables.lex import lex_cell, transliteration_ok
from checkedtables.lines import group_lines
from checkedtables.records import (
    CellRecords,
    DashRule,
    EveryRow,
    ReviewedReading,
    apply_reading,
    reading_for,
)
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.table import Finding, Severity
from checkedtables.testing import page_from_text
from checkedtables.words import Page, Word

SHA = Sha256("0123456789abcdef" * 4)
OTHER_SHA = Sha256("f" * 64)
PAGE = 4
OCR = SourceKind.OCR
TEXT_LAYER = SourceKind.TEXT_LAYER
CASH = ColumnSpec("cash", "Cash", ValueKind.MONEY, NumberFormat(decimals=1))
MONEY = ColumnSpec("money", "Money", ValueKind.MONEY, NumberFormat(decimals=None))
COUNT = ColumnSpec("general", "General", ValueKind.COUNT)
LABEL = ColumnSpec("label", "Label", ValueKind.TEXT)
BLANKS = ("", " ", "\t", "\n")
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
DASH_RULE = DashRule("d1", "cash", ("cash",), EveryRow(), DashMeaning.ZERO, "confirmed on page 2")
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


def text_word(index: int, text: str, size: float, bottom: float) -> Word:
    box = Box(12.0 * index, bottom - size, 12.0 * index + 6.0 * len(text), bottom)
    return Word(WordRef(SHA, PAGE, index), text, box, False, size, None)


def reviewed(text: str, reading: str | None, col: ColumnSpec = CASH) -> object:
    page, cell_words = cash_row(text)
    found = reading_for(cell_words, page.words, OCR, (record(text, reading, cell_words),))
    assert isinstance(found, ReviewedReading), found
    return apply_reading(lex_cell(cell_words, col, OCR), found)


def assert_finding(
    result: object, code: str, review: str = "r1", page: int = PAGE, sha: str = SHA
) -> None:
    assert isinstance(result, Finding), result
    subject = f"{sha[:8]}:reading:{review}"
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
        replace(reading, doc_sha256=OTHER_SHA),
        replace(reading, source=SourceKind.TEXT_LAYER),
        replace(reading, box=label_box),
    ):
        assert reading_for(cell_words, page.words, OCR, (other,)) is None, other
    assert reading_for(cell_words, page.words, OCR, ()) is None
    assert reading_for(cell_words, page.words, OCR, (reading,)) == reading


def test_a_box_holds_a_word_within_one_point_of_it() -> None:
    page, cell_words = cash_row("2918")
    reading = record("2918", "291.8", cell_words)
    box = reading.box
    for outside, found in ((1.0, True), (1.01, False)):
        for side in (
            replace(box, x0=box.x0 + outside),
            replace(box, x1=box.x1 - outside),
            replace(box, top=box.top + outside),
            replace(box, bottom=box.bottom - outside),
        ):
            moved = replace(reading, box=side)
            expected = moved if found else None
            assert reading_for(cell_words, page.words, OCR, (moved,)) == expected, side


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
            assert isinstance(result, Finding)
            assert result.message == "the words in the box, '7 7', are not the cell's words, '7'"


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


def test_a_reading_with_a_minus_gives_a_negative_amount() -> None:
    _, cell_words = cash_row("45")
    cell = lex_cell(cell_words, CASH, OCR)
    refs = tuple(word.ref for word in cell_words)
    expected = Amount(Decimal("-4.5"), "45", refs, OCR, Reading.REVIEWED, "r1")
    assert apply_reading(cell, record("45", "-4.5", cell_words)) == expected


def test_a_reading_places_the_decimal_point_it_reads() -> None:
    # VAL-Q35
    for reading, expected, exponent in (
        ("29.18", Decimal("29.18"), -2),
        ("291.8", Decimal("291.8"), -1),
    ):
        result = reviewed("2918", reading)
        assert isinstance(result, Amount), (reading, result)
        assert (result.printed, result.printed.as_tuple().exponent) == (expected, exponent), reading


def test_a_reviewed_cell_names_the_record_that_was_applied() -> None:
    # VAL-Q35
    _, cell_words = cash_row("2918")
    cell = lex_cell(cell_words, CASH, OCR)
    refs = tuple(word.ref for word in cell_words)
    for review in ("cash-fy07-q3", "cash-fy08-q1"):
        read = apply_reading(cell, record("2918", "291.8", cell_words, review))
        accepted = apply_reading(cell, record("2918", None, cell_words, review))
        assert read == Amount(Decimal("291.8"), "2918", refs, OCR, Reading.REVIEWED, review)
        assert accepted == replace(cell, accepted_by=review)


def test_a_reviewed_amount_names_the_record_that_was_applied() -> None:
    _, cell_words = cash_row("291.8")
    cell = lex_cell(cell_words, CASH, OCR)
    assert isinstance(cell, Amount), cell
    read = apply_reading(cell, record("291.8", "291.8", cell_words, "second-record"))
    accepted = apply_reading(cell, record("291.8", None, cell_words, "second-record"))
    assert read == Amount(
        Decimal("291.8"), "291.8", cell.words, OCR, Reading.REVIEWED, "second-record"
    )
    assert accepted == Unreadable(
        "291.8", cell.words, UnreadableReason.REVIEWED_NULL, "second-record"
    )


def test_a_cell_takes_the_record_boxed_on_it_and_not_the_first_record() -> None:
    page = page_from_text("#ocr\nTaxes 2918 2918", SHA, PAGE)
    left, right = page.words[1:]
    left_record = record("2918", "29.18", (left,), "left")
    right_record = record("2918", "291.8", (right,), "right")
    readings = (left_record, right_record)
    for word, expected, value in (
        (right, right_record, Decimal("291.8")),
        (left, left_record, Decimal("29.18")),
    ):
        found = reading_for((word,), page.words, OCR, readings)
        assert found == expected, (word, found)
        cell = lex_cell((word,), CASH, OCR)
        assert apply_reading(cell, found) == Amount(
            value, "2918", (word.ref,), OCR, Reading.REVIEWED, expected.id
        )


def test_a_reviewed_zero_keeps_its_sign() -> None:
    # QCASH-Q53
    result = reviewed("(0.0)", "(0.0)")
    assert isinstance(result, Amount), result
    assert result.printed.as_tuple() == Decimal("-0.0").as_tuple()


def test_a_null_reading_on_an_amount_gives_reviewed_null() -> None:
    _, cell_words = cash_row("65.8")
    cell = lex_cell(cell_words, CASH, OCR)
    assert isinstance(cell, Amount)
    expected = Unreadable("65.8", cell.words, UnreadableReason.REVIEWED_NULL, "r1")
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


def test_a_raised_footnote_digit_stays_out_of_a_reviewed_amount() -> None:
    # VAL-Q28
    cell_words = (
        text_word(0, "$", 6.0, 12.0),
        text_word(1, "2.8", 12.0, 12.0),
        text_word(2, "1", 6.0, 6.0),
    )
    cell = lex_cell(cell_words, CASH, TEXT_LAYER)
    assert isinstance(cell, Amount)
    assert (cell.text, cell.marks) == ("$ 2.8 1", ("1",))
    box = Box.around(word.box for word in cell_words)
    reading = ReviewedReading("r1", SHA, PAGE, box, TEXT_LAYER, "$ 2.8 1", "2.8", "footnote 1")
    assert reading_for(cell_words, cell_words, TEXT_LAYER, (reading,)) == reading
    expected = Amount(
        Decimal("2.8"), "$ 2.8 1", cell.words, TEXT_LAYER, Reading.REVIEWED, "r1", ("1",)
    )
    assert apply_reading(cell, reading) == expected
    assert_finding(apply_reading(cell, replace(reading, reading="2.81")), "reading_refused")


def test_a_reviewed_amount_keeps_the_marks_of_its_cell() -> None:
    # VAL-Q28
    for text, col, reading, marks in (
        ("242,096*", MONEY, "242096", ("*",)),
        ("2.8 `", CASH, "2.8", ("`",)),
        ("65.8", CASH, "65.8", ()),
    ):
        result = reviewed(text, reading, col)
        assert isinstance(result, Amount), (text, result)
        assert (result.printed, result.marks) == (Decimal(reading), marks), text


def test_a_reading_joins_the_cell_words_in_the_order_given() -> None:
    page, (seven, eight) = cash_row("7 8")
    page = replace(
        page,
        words=(
            replace(seven, box=Box(36.0, 1.0, 42.0, 13.0)),
            replace(eight, box=Box(36.0, 0.0, 42.0, 12.0)),
        ),
    )
    (line,) = group_lines(page)
    cell = lex_cell(line.words, CASH, OCR)
    assert isinstance(cell, Unreadable)
    assert cell.text == "8 7"
    accepted = record("8 7", None, line.words)
    assert reading_for(line.words, page.words, OCR, (accepted,)) == accepted
    assert apply_reading(cell, accepted) == replace(cell, accepted_by="r1")
    stale = record("7 8", None, line.words)
    assert_finding(reading_for(line.words, page.words, OCR, (stale,)), "stale_reading")


def test_a_word_given_twice_is_not_the_cell() -> None:
    page, (word,) = cash_row("7")
    reading = record("7", None, (word,))
    assert reading_for((word,), page.words, OCR, (reading,)) == reading
    assert_finding(reading_for((word, word), page.words, OCR, (reading,)), "stale_reading")
    assert_finding(reading_for((word,), (*page.words, word), OCR, (reading,)), "stale_reading")


def test_a_word_given_twice_cannot_stand_for_another_word() -> None:
    page, (seven, eight) = cash_row("7 8")
    reading = record("7 7", "77", (seven, eight))
    assert_finding(reading_for((seven, seven), page.words, OCR, (reading,)), "stale_reading")
    printed = replace(reading, seen="7 8")
    assert reading_for((seven, eight), page.words, OCR, (printed,)) == printed


def test_a_reading_cannot_drop_or_add_a_digit_of_another_script() -> None:
    for seen, reading in (
        ("１,234", "234"),
        ("1234", "１２３４"),
        ("１２３４", "１２３４"),
    ):
        assert_finding(reviewed(seen, reading, MONEY), "reading_refused")


def test_a_null_reading_of_other_text_is_stale() -> None:
    _, cell_words = cash_row("65.8")
    cell = lex_cell(cell_words, CASH, OCR)
    assert_finding(apply_reading(cell, record("85.8", None, cell_words)), "stale_reading")


def test_a_reading_of_another_file_is_stale() -> None:
    _, cell_words = cash_row("65.8")
    cell = lex_cell(cell_words, CASH, OCR)
    elsewhere = replace(record("65.8", "65.8", cell_words), doc_sha256=OTHER_SHA)
    assert_finding(apply_reading(cell, elsewhere), "stale_reading", sha=OTHER_SHA)


def test_a_cell_with_a_word_on_another_page_is_stale() -> None:
    _, here = cash_row("(29 1)")
    _, there = cash_row("(29 1)", PAGE + 1)
    cell = lex_cell((here[0], there[1]), CASH, OCR)
    for page in (PAGE, PAGE + 1):
        reading = replace(record("(29 1)", "(29.1)", here), page=page)
        assert_finding(apply_reading(cell, reading), "stale_reading", page=page)


def test_a_reading_needs_an_id() -> None:
    _, cell_words = cash_row("2918")
    for blank in BLANKS:
        with pytest.raises(ValueError, match="id"):
            record("2918", "291.8", cell_words, blank)


@pytest.mark.parametrize(
    "sha",
    [
        pytest.param("0123456789abcdef" * 4, id="64_hex_characters_of_plain_text"),
        pytest.param("", id="empty"),
        pytest.param(None, id="none"),
    ],
)
def test_reviewed_reading_refuses_a_sha_that_is_not_a_sha256(sha: Any) -> None:
    box = Box(0.0, 0.0, 10.0, 10.0)
    with pytest.raises(ValueError, match="not a Sha256"):
        ReviewedReading("r1", sha, PAGE, box, OCR, "1", "1", "read on the rendered page")
    reading = ReviewedReading("r1", SHA, PAGE, box, OCR, "1", "1", "read on the rendered page")
    assert reading.doc_sha256 == SHA


def test_a_reading_needs_a_reason() -> None:
    _, cell_words = cash_row("2918")
    for blank in (*BLANKS, " \t "):
        with pytest.raises(ValueError, match="reason"):
            replace(record("2918", "291.8", cell_words), reason=blank)


def test_a_dash_rule_needs_an_id() -> None:
    for blank in BLANKS:
        with pytest.raises(ValueError, match="id"):
            replace(DASH_RULE, id=blank)


def test_one_id_names_one_record() -> None:
    _, cell_words = cash_row("2918")
    reading = record("2918", "291.8", cell_words)
    CellRecords(
        (reading, replace(reading, id="r2")), (DASH_RULE, replace(DASH_RULE, id="d2")), 90.0
    )
    with pytest.raises(ValueError, match="r1"):
        CellRecords((reading, replace(reading, reading="29.18")), (), 90.0)
    with pytest.raises(ValueError, match="d1"):
        CellRecords((), (DASH_RULE, replace(DASH_RULE, columns=("other",))), 90.0)


def test_a_reading_and_a_dash_rule_never_share_an_id() -> None:
    _, cell_words = cash_row("2918")
    reading = record("2918", "291.8", cell_words, DASH_RULE.id)
    with pytest.raises(ValueError, match="d1"):
        CellRecords((reading,), (DASH_RULE,), 90.0)


def test_a_font_code_never_becomes_a_reviewed_number() -> None:
    # VAL-Q05
    page = page_from_text("10(cid:28)", SHA, PAGE)
    refs = tuple(word.ref for word in page.words)
    for column in (COUNT, LABEL):
        cell = lex_cell(page.words, column, TEXT_LAYER)
        assert cell == Unreadable("10(cid:28)", refs, UnreadableReason.FONT_CODE), column.kind
        for value in ("109", "10028", None):
            reading = replace(record("10(cid:28)", value, page.words), source=TEXT_LAYER)
            assert reading_for(page.words, page.words, TEXT_LAYER, (reading,)) == reading
            result = apply_reading(cell, reading)
            if value is None:
                expected = Unreadable("10(cid:28)", refs, UnreadableReason.FONT_CODE, "r1")
                assert result == expected, column.kind
            else:
                assert_finding(result, "reading_refused")


def test_a_reviewed_amount_keeps_a_raised_digit_and_a_mark_after_it() -> None:
    # VAL-Q28
    cell_words = (
        text_word(0, "2.8", 12.0, 12.0),
        text_word(1, "1", 6.0, 6.0),
        text_word(2, "*", 12.0, 12.0),
    )
    cell = lex_cell(cell_words, CASH, TEXT_LAYER)
    assert isinstance(cell, Amount)
    assert (cell.printed, cell.text, cell.marks) == (Decimal("2.8"), "2.8 1 *", ("1", "*"))
    box = Box.around(word.box for word in cell_words)
    reading = ReviewedReading("r1", SHA, PAGE, box, TEXT_LAYER, "2.8 1 *", "2.8", "footnote 1")
    assert reading_for(cell_words, cell_words, TEXT_LAYER, (reading,)) == reading
    result = apply_reading(cell, reading)
    assert isinstance(result, Amount), result
    assert (result.printed, result.marks) == (Decimal("2.8"), ("1", "*"))
    assert_finding(apply_reading(cell, replace(reading, reading="2.81")), "reading_refused")


def test_only_the_mark_words_that_end_a_cell_leave_its_digits() -> None:
    # VAL-Q28
    for texts, accepted, refused in (
        (("1", "1"), "1", "11"),
        (("$", "1", "1"), "1", "11"),
        (("$", "10", "1"), "10", "101"),
    ):
        *number, mark = texts
        cell_words = (
            *(text_word(index, text, 12.0, 12.0) for index, text in enumerate(number)),
            text_word(len(number), mark, 6.0, 6.0),
        )
        cell = lex_cell(cell_words, MONEY, TEXT_LAYER)
        assert isinstance(cell, Amount), texts
        assert cell.marks == (mark,), texts
        seen = " ".join(texts)
        box = Box.around(word.box for word in cell_words)
        reading = ReviewedReading("r1", SHA, PAGE, box, TEXT_LAYER, seen, accepted, "footnote")
        result = apply_reading(cell, reading)
        assert isinstance(result, Amount), (texts, result)
        assert (result.printed, result.marks) == (Decimal(accepted), (mark,)), texts
        assert_finding(apply_reading(cell, replace(reading, reading=refused)), "reading_refused")


def test_a_box_over_a_word_of_the_next_line_is_stale() -> None:
    first, second = text_word(0, "29", 12.0, 12.0), text_word(1, "1", 12.0, 12.0)
    below = replace(text_word(2, "7", 12.0, 26.0), box=Box(0.0, 14.0, 6.0, 26.0))
    box = Box.around((first.box, below.box))
    assert not box.contains(second.box, 1.0)
    reading = ReviewedReading("r1", SHA, PAGE, box, TEXT_LAYER, "29 1", "29.1", "lost point")
    result = reading_for((first, second), (first, second, below), TEXT_LAYER, (reading,))
    assert_finding(result, "stale_reading")


def test_a_reading_joins_the_cell_words_as_given_and_not_by_left_edge() -> None:
    left, right = text_word(0, "7", 12.0, 12.0), text_word(1, "8", 12.0, 12.0)
    cell_words = (right, left)
    box = Box.around(word.box for word in cell_words)
    accepted = ReviewedReading("r1", SHA, PAGE, box, TEXT_LAYER, "8 7", None, "printed 8 7")
    assert reading_for(cell_words, cell_words, TEXT_LAYER, (accepted,)) == accepted
    stale = replace(accepted, seen="7 8")
    assert_finding(reading_for(cell_words, cell_words, TEXT_LAYER, (stale,)), "stale_reading")


@given(seen_parts, st.integers(1, 16), st.sampled_from(("", ",")), st.sampled_from(SIGNED))
@example([("", "2918")], 3, "", "{}")
@example([("", "2918")], 2, "", "{}")
@example([("", "29"), (" ", "1")], 2, "", "({})")
@example([("", "69"), (",", "2")], 2, ",", "{}")
@example([("", "67"), (": ", "3")], 2, "", "-{}")
@example([("", "1o4.o")], 3, "", "{}")
@example([("", "0o7")], 3, ",", "$({})")
@example([("", "0"), (".", "0")], 1, "", "({})")
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
    minus = "" if sign in ("{}", "${}") else "-"
    expected = Decimal(minus + seen_digits[:whole] + (f".{fraction}" if fraction else ""))
    assert (result.printed, result.printed.as_tuple()) == (expected, expected.as_tuple()), (
        seen,
        reading,
    )
