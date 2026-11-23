from dataclasses import replace
from decimal import Decimal
from string import ascii_letters, digits, punctuation

from hypothesis import example, given
from hypothesis import strategies as st

from checkedtables.cells import Amount, Blank, Cell, Dash, NotApplicable, Text, Unreadable
from checkedtables.columns import ColumnSpec, NumberFormat
from checkedtables.kinds import DashMeaning, PercentSign, SourceKind, ValueKind
from checkedtables.lex import lex_cell, split_numeric_runs, transliteration_ok
from checkedtables.lines import group_lines, has_values
from checkedtables.refs import Box, WordRef
from checkedtables.testing import page_from_text
from checkedtables.words import Word

SHA = "a" * 64
MONEY = ColumnSpec("money", "Money", ValueKind.MONEY, NumberFormat(decimals=None))
CASH = ColumnSpec("cash", "Cash", ValueKind.MONEY, NumberFormat(decimals=1))
COUNT_COLUMN = ColumnSpec("count", "Count", ValueKind.COUNT)
PERCENT = ColumnSpec(
    "percent", "Percent", ValueKind.PERCENT, NumberFormat(None, PercentSign.OPTIONAL)
)
MINUS_GLYPHS = ("-", "−", "–", "—")
DASHES = ("-", "--", "–", "—")
DOLLARS = (("", ""), ("$", ""), ("", "$"), ("$ ", ""))
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
FRAGMENTS = (
    "0",
    "7",
    "12",
    "345",
    "1,234",
    "37,332,523",
    ".5",
    ",",
    ".",
    "$",
    "%",
    "(",
    ")",
    "+",
    *MINUS_GLYPHS,
    "o",
    "B",
    "TAX",
    " ",
    "*",
    "`",
    "\xb9",
    "†",
)
values = st.builds(
    lambda number, decimals: Decimal(number).scaleb(-decimals),
    st.integers(-(10**15), 10**15),
    st.integers(0, 12),
)
word_texts = st.lists(st.sampled_from(FRAGMENTS), max_size=4).map("".join)
value_words = st.builds(
    "".join,
    st.tuples(
        st.sampled_from(("", "(", "$", "$(", "($", "-$", "$-", "+", *MINUS_GLYPHS)),
        st.sampled_from(("0", "7", "12", "1,234", "12.3", "0.05", "37,332,523", "67,215,504.0")),
        st.sampled_from(("", "%", ")", "%)", "*", "\xb9", "-", "%*", "``")),
    ),
) | st.sampled_from((*DASHES, "N/A", "NA", "−", "B", "%", "007", "1,23"))


def words(*texts: str) -> tuple[Word, ...]:
    return page_from_text(" ".join(texts), SHA, 1).words


def lexed(text: str, col: ColumnSpec = MONEY) -> Cell:
    page = page_from_text(text, SHA, 1)
    return lex_cell(page.words, col, page.source.kind)


def amount(text: str, col: ColumnSpec = MONEY) -> Amount:
    cell = lexed(text, col)
    assert isinstance(cell, Amount), (text, cell)
    return cell


def reason(text: str, col: ColumnSpec = MONEY) -> str:
    cell = lexed(text, col)
    assert isinstance(cell, Unreadable), (text, cell)
    return cell.reason


def placed(index: int, text: str, size: float, bottom: float) -> Word:
    box = Box(12.0 * index, bottom - size, 12.0 * index + 6.0 * len(text), bottom)
    return Word(WordRef(SHA, 1, index), text, box, False, size, None)


def printed(value: Decimal, grouping: str, negative: str, dollar: tuple[str, str]) -> str:
    outside, inside = dollar
    magnitude = f"{inside}{format(value.copy_abs(), f'{grouping}f')}"
    if not value.is_signed():
        return f"{outside}{magnitude}"
    if negative == "()":
        return f"{outside}({magnitude})"
    return f"{outside}{negative}{magnitude}"


def decimal_digits(text: str) -> str:
    return "".join(character for character in text if character in digits)


@given(
    values,
    st.sampled_from(("", ",")),
    st.sampled_from(("()", *MINUS_GLYPHS)),
    st.sampled_from(DOLLARS),
)
@example(Decimal("0.00001"), "", "-", ("", ""))
@example(Decimal("1234.567890"), ",", "()", ("$", ""))
@example(Decimal("-1234.567890"), "", "—", ("", "$"))
def test_lexer_round_trip(
    value: Decimal, grouping: str, negative: str, dollar: tuple[str, str]
) -> None:
    text = printed(value, grouping, negative, dollar)
    assert amount(text).printed.as_tuple() == value.as_tuple(), text


@given(
    st.lists(word_texts, min_size=1, max_size=3),
    st.sampled_from(("", "1")),
    st.sampled_from((MONEY, CASH, COUNT_COLUMN, PERCENT)),
    st.sampled_from(tuple(SourceKind)),
)
@example(["007"], "", MONEY, SourceKind.TEXT_LAYER)
@example(["1", "37,332,523"], "", MONEY, SourceKind.TEXT_LAYER)
@example(["67,215,504.0", "0"], "", MONEY, SourceKind.TEXT_LAYER)
@example(["$", "2.8"], "1", CASH, SourceKind.TEXT_LAYER)
@example(["0.05%*"], "", PERCENT, SourceKind.TEXT_LAYER)
def test_amount_digits_are_the_digits_of_its_words(
    texts: list[str], raised: str, col: ColumnSpec, source: SourceKind
) -> None:
    cell_words = [placed(index, text, 12.0, 12.0) for index, text in enumerate(texts)]
    if raised and decimal_digits(texts[-1]):
        cell_words.append(placed(len(texts), raised, 6.0, 6.0))
    cell = lex_cell(cell_words, col, source)
    if isinstance(cell, Amount):
        joined = " ".join(texts)
        fraction = joined.rpartition(".")[2] if "." in joined else ""
        assert decimal_digits(format(cell.printed.copy_abs(), "f")) == decimal_digits(joined)
        assert cell.printed.as_tuple().exponent == -len(decimal_digits(fraction))


@given(
    st.sampled_from(("", "$")),
    st.lists(value_words, min_size=1, max_size=2),
    st.sampled_from(("", "*", "`", "\xb9", "†", "**")),
)
@example("$", ["1", "37,332,523"], "*")
@example("", ["2.8"], "`")
def test_a_lexed_value_is_a_value_word(dollar: str, numbers: list[str], mark: str) -> None:
    cell_text = " ".join(text for text in (dollar, *numbers, mark) if text)
    page = page_from_text(f"Taxes {cell_text}", SHA, 1)
    (line,) = group_lines(page)
    cell = lex_cell(line.words[1:], PERCENT, page.source.kind)
    if isinstance(cell, Amount | Dash | NotApplicable):
        assert has_values(line), cell_text


def test_transliteration_refuses_a_digit_swap() -> None:
    # QCASH-Q22, MSCH-Q26
    assert transliteration_ok("1o4.o", "104.0")
    assert transliteration_ok("2918", "291.8")
    assert not transliteration_ok("65.8", "85.8")
    assert not transliteration_ok("77,500,000", "7,500,000")


def test_confusable_glyphs_are_pinned() -> None:
    confusable = dict(CONFUSABLE_GLYPHS)
    for glyph in f"{ascii_letters}{punctuation}\xb9−Ο０":
        for digit in digits:
            expected = confusable.get(glyph) == digit
            assert transliteration_ok(f"1{glyph}", f"1{digit}") is expected, (glyph, digit)


def test_transliteration_reads_every_glyph_in_order() -> None:
    assert transliteration_ok("(59.8j", "(59.8)")
    assert transliteration_ok("B&D", "860")
    assert not transliteration_ok("B&D", "806")
    assert not transliteration_ok("291.8", "2918.1")
    assert not transliteration_ok("1,185.9", "1,165.9")


def test_bare_integers_never_join() -> None:  # QPOS-Q27, VAL-Q21
    cell = lex_cell(words("12", "345"), COUNT_COLUMN, SourceKind.TEXT_LAYER)
    assert isinstance(cell, Unreadable)


def test_bare_integers_never_join_in_a_money_column() -> None:
    # VAL-Q21, QPOS-Q27
    for text in ("12 345", "1 2", "12 345 678", "12, 345"):
        assert reason(text) == "two_tokens", text


def test_two_amounts_in_one_cell_never_join() -> None:
    for text in ("4727 402.5", "1234.5 6", "12 3,456", "204,935 3,344", "746,066,499 726,847,660"):
        assert reason(text) == "two_tokens", text


def test_count_and_ocr_cells_never_join() -> None:
    assert isinstance(
        lex_cell(words("1", "23,456"), COUNT_COLUMN, SourceKind.TEXT_LAYER), Unreadable
    )
    assert reason("#ocr\n67,215,504.0 0") == "two_tokens"
    assert reason("-1 37,332,523") == "two_tokens"
    assert reason("$1 37,332,523") == "two_tokens"
    assert amount("1 23,456").printed == Decimal("123456")
    assert amount("67,215,504.0 0").printed.as_tuple() == Decimal("67215504.00").as_tuple()


def test_spaces_after_commas_never_join() -> None:
    # VAL-Q33
    assert reason("10, 936, 234") == "two_tokens"
    assert reason("(1, 130, 698)") == "two_tokens"


def test_join_shapes_keep_their_token_limits() -> None:
    assert amount("(1 37,332,523)").printed == Decimal("-137332523")
    assert amount("-67,215,504.0 0").printed == Decimal("-67215504.00")
    assert amount("$67,215,504.0 0").printed == Decimal("67215504.00")
    assert amount("123.5 6").printed == Decimal("123.56")
    assert amount("1 37,332,523", PERCENT).printed == Decimal("137332523")
    for text in (
        "1 2 37,332,523",
        "12 37,332,523",
        "1 37,332,52",
        "1 2,345%",
        "1,234.5 67",
        "1,234.5 6 7",
        "12.3 4%",
        "0 37,332,523",
        "(-67,215,504.0 0)",
        "1 $ 37,332,523",
        "- 5",
        "5 %",
        "12.3 %",
    ):
        assert reason(text) == "two_tokens", text
    assert reason("67,215,504.0 0", CASH) == "decimals"


def test_a_raised_digit_after_a_small_dollar_sign_is_a_mark() -> None:
    # VAL-Q28
    cell_words = (placed(0, "$", 6.0, 12.0), placed(1, "2.8", 12.0, 12.0), placed(2, "1", 6.0, 6.0))
    cell = lex_cell(cell_words, CASH, SourceKind.TEXT_LAYER)
    assert isinstance(cell, Amount)
    assert (cell.printed, cell.marks, cell.text) == (Decimal("2.8"), ("1",), "$ 2.8 1")
    assert cell.words == tuple(word.ref for word in cell_words)


def test_a_digit_that_is_not_small_and_raised_is_no_mark() -> None:
    # VAL-Q28
    for size, bottom in ((12.0, 12.0), (6.0, 12.0), (12.0, 6.0), (9.0, 6.0)):
        cell_words = (placed(0, "2.8", 12.0, 12.0), placed(1, "1", size, bottom))
        cell = lex_cell(cell_words, MONEY, SourceKind.TEXT_LAYER)
        assert isinstance(cell, Amount)
        assert (cell.printed, cell.marks) == (Decimal("2.81"), ()), (size, bottom)
    ocr = tuple(replace(word, size=None) for word in cell_words)
    assert isinstance(lex_cell(ocr, MONEY, SourceKind.OCR), Unreadable)


def test_footnote_marks_leave_the_amount() -> None:
    # VAL-Q28
    assert amount("242,096*").marks == ("*",)
    assert amount("2.8 `", CASH).marks == ("`",)
    assert amount("1,234\xb9").marks == ("\xb9",)
    assert amount("1,234\xb9\xb2 †").marks == ("\xb9\xb2", "†")
    assert amount("(5,678)‡").printed == Decimal("-5678")
    assert amount("12.3%\xa7", PERCENT).marks == ("\xa7",)
    assert amount("1,234 # **").marks == ("#", "**")
    cell = amount("242,096*")
    assert (cell.text, cell.words) == ("242,096*", (WordRef(SHA, 1, 0),))
    assert reason("2*42,096") == "grouping"
    assert reason("*") == "not_a_number"


def test_a_double_dash_is_a_dash_with_no_value() -> None:
    # BIB-Q50
    page = page_from_text("--", SHA, 1)
    assert lex_cell(page.words, MONEY, SourceKind.TEXT_LAYER) == Dash(
        "--", (WordRef(SHA, 1, 0),), DashMeaning.NO_VALUE
    )


def test_a_dash_in_a_count_column_means_no_count() -> None:
    # BSALES-Q38
    cell = lexed("-", COUNT_COLUMN)
    assert isinstance(cell, Dash)
    assert cell.meaning is DashMeaning.NO_VALUE


def test_a_dash_for_a_missing_count_is_a_dash() -> None:
    # RTT-Q39
    for dash in DASHES:
        assert lexed(dash, COUNT_COLUMN) == Dash(dash, (WordRef(SHA, 1, 0),), DashMeaning.NO_VALUE)


def test_a_dash_means_no_value_unless_the_column_declares_zero() -> None:
    # SUPCAP-Q28
    zero = ColumnSpec("enc", "Encumbrances", ValueKind.MONEY, dash=DashMeaning.ZERO)
    assert lexed("-") == Dash("-", (WordRef(SHA, 1, 0),), DashMeaning.NO_VALUE)
    assert lexed("-", zero) == Dash("-", (WordRef(SHA, 1, 0),), DashMeaning.ZERO)


def test_dashes_and_marks_are_never_zero() -> None:
    # QCASH-Q52
    for text in (*DASHES, "*", "---", "−", "- -"):
        cell = lexed(text, CASH)
        assert isinstance(cell, Dash | Unreadable), text


def test_not_applicable_cells_are_never_numbers() -> None:
    # MCITY-Q34
    row = page_from_text("N/A N/A NA", SHA, 1).words
    for word in row:
        cell = lex_cell((word,), MONEY, SourceKind.TEXT_LAYER)
        assert cell == NotApplicable(word.text, (word.ref,))
    assert reason("n/a") == "not_a_number"


def test_a_fund_that_prints_n_a_is_not_applicable() -> None:
    # SUPCAP-Q34
    assert lexed("N/A", CASH) == NotApplicable("N/A", (WordRef(SHA, 1, 0),))


def test_a_fused_money_lane_is_unreadable() -> None:
    # MSCH-Q29
    assert reason("1,234 5") == "two_tokens"
    assert reason("5,678,901 (12,345)") == "two_tokens"


def test_parentheses_and_a_leading_minus_are_negative() -> None:
    # MSCH-Q34
    assert amount("(5,678)").printed == Decimal("-5678")
    for minus in MINUS_GLYPHS:
        assert amount(f"{minus}5,678").printed == Decimal("-5678"), minus


def test_cash_negatives_keep_their_decimal() -> None:
    # QCASH-Q53
    assert amount("(3.0)", CASH).printed.as_tuple() == Decimal("-3.0").as_tuple()
    assert amount("-4.5", CASH).printed == Decimal("-4.5")
    assert amount("−11.0", CASH).printed.as_tuple() == Decimal("-11.0").as_tuple()
    assert reason("(3)", CASH) == "decimals"


def test_a_blank_lane_cell_is_blank() -> None:
    # QPOS-Q21
    assert lex_cell((), COUNT_COLUMN, SourceKind.TEXT_LAYER) == Blank()
    assert lex_cell((), MONEY, SourceKind.OCR) == Blank()


def test_a_percent_sign_follows_the_column_format() -> None:
    # SUPOP-Q12
    absent = ColumnSpec("rate", "Rate", ValueKind.PERCENT, NumberFormat(None, PercentSign.ABSENT))
    required = ColumnSpec("rate", "Rate", ValueKind.PERCENT, NumberFormat(2, PercentSign.REQUIRED))
    assert amount("74.98", PERCENT).printed == Decimal("74.98")
    assert amount("74.98%", PERCENT).printed == Decimal("74.98")
    assert amount("74.98", absent).printed == Decimal("74.98")
    assert reason("74.98%", absent) == "percent_sign"
    assert amount("74.98%", required).printed == Decimal("74.98")
    assert reason("74.98", required) == "percent_sign"
    assert reason("74.9%", required) == "decimals"
    assert reason("1,234%") == "percent_sign"


def test_a_dollar_sign_leaves_the_number() -> None:
    # VAL-Q09
    for text in ("$1,234", "$ 1,234"):
        cell = amount(text)
        assert (cell.printed, cell.text) == (Decimal("1234"), text)
        assert cell.words == tuple(WordRef(SHA, 1, index) for index in range(len(text.split())))
    for text in ("-$61,397,587", "$-61,397,587", "$(61,397,587)", "($61,397,587)"):
        assert amount(text).printed == Decimal("-61397587"), text
    for text in ("$$1,234", "1,234$", "$-$1,234", "1,234 $"):
        assert isinstance(lexed(text), Unreadable), text


def test_a_trailing_minus_or_a_plus_sign_is_unreadable() -> None:
    # VAL-Q26
    for text in ("123-", "+12.3%", "+5", "1,234−", "(5,678", "5,678)", "-(5,678)", "--5"):
        assert reason(text, PERCENT) == "sign", text


def test_a_percent_reads_as_printed() -> None:
    # VAL-Q27
    assert amount("12.3%", PERCENT).printed.as_tuple() == Decimal("12.3").as_tuple()
    assert amount("12.30%", PERCENT).printed.as_tuple() == Decimal("12.30").as_tuple()
    assert amount("(12.3%)", PERCENT).printed == Decimal("-12.3")
    assert reason("(12.3)%", PERCENT) == "grouping"


def test_strict_grouping() -> None:
    for text in ("007", "0,123", "1,23", "1234,567", "12,3456", ".5", "5.", "1..2", "1.2.3"):
        assert reason(text) == "grouping", text
    for text in ("0", "0.5", "1234567", "1,234,567", "999"):
        assert amount(text).printed == Decimal(text.replace(",", "")), text


def test_digits_that_are_not_ascii_never_read() -> None:
    for text in ("１,234", "١٢", "1\xa0234", "1o4.o"):
        assert reason(text) == "not_a_number", text


def test_text_columns_give_text() -> None:
    for kind in (ValueKind.YEAR, ValueKind.CODE, ValueKind.TEXT):
        column = ColumnSpec("code", "Code", kind)
        assert lexed("FY2016 1,234", column) == Text(
            "FY2016 1,234", (WordRef(SHA, 1, 0), WordRef(SHA, 1, 1))
        )


def test_a_percent_and_a_tax_cell_fused_split_apart() -> None:
    # BSALES-Q36
    (word,) = words("12.3%45,678")
    assert [child.text for child in split_numeric_runs(word)] == ["12.3%", "45,678"]


def test_two_percents_in_one_cell_split_apart() -> None:
    # RTT-Q22
    (word,) = words("12.3%4.5%")
    assert [child.text for child in split_numeric_runs(word)] == ["12.3%", "4.5%"]


def test_split_children_carry_their_parent_and_a_cut_box() -> None:
    # VAL-Q08
    (word,) = page_from_text("    TAX434,605,553", SHA, 2).words
    first, second = split_numeric_runs(word)
    assert (first.ref, second.ref) == (WordRef(SHA, 2, 0, 0), WordRef(SHA, 2, 0, 1))
    assert (first.box, second.box) == (Box(24.0, 0.0, 42.0, 12.0), Box(42.0, 0.0, 108.0, 12.0))
    assert (first.bold, first.size, first.confidence) == (word.bold, word.size, word.confidence)


def test_two_amounts_in_one_word_split_apart() -> None:
    # VAL-Q33
    (word,) = words("(1,234)(5,678)")
    assert [child.text for child in split_numeric_runs(word)] == ["(1,234)", "(5,678)"]
    (word,) = words("1,234)$5")
    assert [child.text for child in split_numeric_runs(word)] == ["1,234)", "$5"]


def test_an_amount_fused_to_a_label_splits_on_either_side() -> None:
    # VAL-Q34
    cases = {
        "TAX434,605,553": ["TAX", "434,605,553"],
        "TAX(434,605.5)": ["TAX", "(434,605.5)"],
        "TAX$434,605": ["TAX", "$434,605"],
        "408,491,218NET": ["408,491,218", "NET"],
        "(408,491.2)NET": ["(408,491.2)", "NET"],
        "A1,234B": ["A", "1,234", "B"],
    }
    for text, children in cases.items():
        (word,) = words(text)
        assert [child.text for child in split_numeric_runs(word)] == children, text


def test_a_word_with_one_run_comes_back_unchanged() -> None:
    for text in (
        "FY2016",
        "1,234",
        "TAX",
        "12.3%",
        "TAX1234,567",
        "TAX12,34",
        "(1,234)",
        "12.3%TAX",
    ):
        (word,) = words(text)
        assert split_numeric_runs(word) == (word,), text
