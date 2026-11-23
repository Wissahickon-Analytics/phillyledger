from checkedtables.cells import Amount, Blank, Cell, Dash, NotApplicable, Text, Unreadable
from checkedtables.columns import ColumnSpec, NumberFormat
from checkedtables.kinds import PercentSign, ValueKind
from checkedtables.lex import lex_cell, split_numeric_runs
from checkedtables.testing import page_from_text

SHA = "a" * 64
COLUMNS = {
    "M": ColumnSpec("money", "Money", ValueKind.MONEY, NumberFormat(decimals=None)),
    "M1": ColumnSpec("cash", "Cash", ValueKind.MONEY, NumberFormat(decimals=1)),
    "C": ColumnSpec("count", "Count", ValueKind.COUNT),
    "P": ColumnSpec(
        "percent", "Percent", ValueKind.PERCENT, NumberFormat(None, PercentSign.OPTIONAL)
    ),
}
PROBES = (
    ("12 345", "C", "12345.0", "12345", "Unreadable two_tokens"),  # QPOS-Q27
    ("1 2", "C", "12.0", "12", "Unreadable two_tokens"),  # QPOS-Q27
    ("12 345 678", "C", "12345678.0", "12345678", "Unreadable two_tokens"),  # QPOS-Q27
    ("12, 345", "M", "12345.0", "12345", "Unreadable two_tokens"),  # VAL-Q21
    ("-$61,397,587", "M", "None", "-61397587", "Amount -61397587"),  # VAL-Q22
    ("-", "M", "0.0", "None", "Dash no_value"),
    ("--", "M", "0.0", "None", "Dash no_value"),  # BIB-Q50
    ("\u2014", "M", "0.0", "None", "Dash no_value"),
    ("---", "M", "None", "None", "Unreadable not_a_number"),
    ("- 0", "M", "-0.0", "-0", "Unreadable two_tokens"),
    ("(12.3%)", "P", "-12.3", "-12.3", "Amount -12.3"),  # VAL-Q27
    ("+12.3%", "P", "None", "None", "Unreadable sign"),  # VAL-Q26
    ("123-", "M", "None", "None", "Unreadable sign"),  # VAL-Q26
    (".5", "M", "None", "None", "Unreadable grouping"),
    ("$(1,234)", "M", "None", "None", "Amount -1234"),
    ("1,234 5", "M", "None", "None", "Unreadable two_tokens"),  # MSCH-Q29
    ("1,234,567", "M", "1234567.0", "1234567", "Amount 1234567"),
    ("11.6", "M1", "11.6", "11.6", "Amount 11.6"),
    ("(3.0)", "M1", "-3.0", "-3.0", "Amount -3.0"),  # QCASH-Q53
    ("828,904.89", "M", "828904.89", "828904.89", "Amount 828904.89"),
    ("44,646,313", "M", "44646313.0", "44646313", "Amount 44646313"),
    ("(5,678)", "M", "-5678.0", "-5678", "Amount -5678"),  # MSCH-Q34
    ("-4.5", "M1", "-4.5", "-4.5", "Amount -4.5"),  # QCASH-Q53
    ("\u20137", "M", "-7.0", "-7", "Amount -7"),
    ("-11.0", "M1", "-11.0", "-11.0", "Amount -11.0"),  # QCASH-Q53
    ("$-61,397,587", "M", "-61397587.0", "-61397587", "Amount -61397587"),  # VAL-Q22
    ("\u2013", "M", "0.0", "None", "Dash no_value"),
    ("N/A", "M", "None", "None", "NotApplicable"),  # MCITY-Q34
    ("12.3%", "P", "12.3", "12.3", "Amount 12.3"),  # VAL-Q27
    ("69%", "P", "69.0", "69", "Amount 69"),  # VAL-Q27
    ("26.6%", "P", "26.6", "26.6", "Amount 26.6"),  # VAL-Q27
    ("74.98", "P", "74.98", "74.98", "Amount 74.98"),  # SUPOP-Q12
    ("242,096*", "M", "242096.0", "242096", "Amount 242096 marks *"),  # VAL-Q28
    ("2.8 `", "M1", "2.8", "2.8", "Amount 2.8 marks `"),  # VAL-Q28
    ("TOTAL TAX REVENUE *", "M", "None", "None", "Unreadable not_a_number"),
    ("1 37,332,523", "M", "137332523.0", "137332523", "Amount 137332523"),
    ("67,215,504.0 0", "M", "67215504.0", "67215504.00", "Amount 67215504.00"),
    ("10, 936, 234 (1, 130, 698)", "M", "None", "None", "Unreadable two_tokens"),  # VAL-Q33
    ("TAX434,605,553", "M", "None", "None", "Unreadable not_a_number"),  # VAL-Q34
    ("408,491,218 NET PROFITS TAX", "M", "None", "None", "Unreadable not_a_number"),
    ("2100", "M1", "2100.0", "2100", "Unreadable decimals"),  # QCASH-Q21
    ("266 1", "M1", "2661.0", "2661", "Unreadable two_tokens"),  # QCASH-Q21
    ("69,2", "M1", "None", "None", "Unreadable grouping"),  # QCASH-Q21
    ("67: 3", "M1", "None", "None", "Unreadable not_a_number"),  # QCASH-Q21
    ("B", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    ("O", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    ("Q", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    ("D", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    ("&", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    ("(59.8j", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    (":", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    ("1,234\xb9", "M", "None", "None", "Amount 1234 marks \xb9"),  # VAL-Q28
    ("(29 1)", "M1", "-291.0", "-291", "Unreadable two_tokens"),  # QCASH-Q21
    ("1o4.o", "M1", "None", "None", "Unreadable not_a_number"),  # VAL-Q36
    ("110,626,142.01 92.31", "M", "None", "None", "Unreadable two_tokens"),  # VAL-Q15
)


def describe(cell: Cell) -> str:
    match cell:
        case Amount(printed=printed, marks=()):
            return f"Amount {printed}"
        case Amount(printed=printed, marks=marks):
            return f"Amount {printed} marks {' '.join(marks)}"
        case Dash(meaning=meaning):
            return f"Dash {meaning}"
        case NotApplicable():
            return "NotApplicable"
        case Unreadable(reason=reason):
            return f"Unreadable {reason}"
        case Blank():
            return "Blank"
        case Text(text=text):
            return f"Text {text}"


def test_val_probe_inputs_give_documented_results() -> None:
    assert len(PROBES) == 55
    for text, key, _, _, new in PROBES:
        page = page_from_text(text, SHA, 1)
        assert describe(lex_cell(page.words, COLUMNS[key], page.source.kind)) == new, text
    fused, *_ = PROBES[38]
    (word,) = page_from_text(fused, SHA, 1).words
    assert [child.text for child in split_numeric_runs(word)] == ["TAX", "434,605,553"]
