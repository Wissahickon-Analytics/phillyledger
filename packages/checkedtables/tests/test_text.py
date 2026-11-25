from re import fullmatch

from hypothesis import given
from hypothesis import strategies as st

from checkedtables.labels import Label
from checkedtables.lines import Line, group_lines, has_values
from checkedtables.refs import Sha256
from checkedtables.testing import page_from_text
from checkedtables.text import (
    normalize_label,
    normalize_space,
    parse_label,
    split_line_prefix,
    squash,
)

SHA = Sha256("a" * 64)
LINE_NUMBER = r"I|\d{1,2}"
PREFIX_PATTERNS = (LINE_NUMBER, r"\d+", r"[A-Z][a-z]+", r".*", r"x")
word_texts = st.sampled_from(("23", "I", "5", "Civilian", "Human", "(1)", "1,234", "-")) | st.text(
    alphabet="0123456789IVCivil(),.-", min_size=1, max_size=4
)


def line(text: str) -> Line:
    (only,) = group_lines(page_from_text(text, SHA, 1))
    return only


def label(text: str) -> Label:
    return parse_label((), page_from_text(text, SHA, 1).words)


def printed_text_marks(found: Label) -> tuple[str, str, tuple[str, ...]]:
    return found.printed, found.text, found.marks


def matched(text: str) -> str:
    return squash(normalize_label(text))


def test_label_mark_number_in_parentheses() -> None:
    # QPOS-Q11, ENT-Q07, BIB-Q47: config/entities.yml:935
    found = label("Human Services (1)")
    assert printed_text_marks(found) == ("Human Services (1)", "Human Services", ("(1)",))
    assert (found.norm, found.squash, found.line_no) == ("human services", "humanservices", None)


def test_label_mark_two_digit_number_in_parentheses() -> None:
    # QOBL-Q43, QOBL-Q48: tests/test_entities.py:1215-1225
    assert printed_text_marks(label("Office of Prison Oversight (10)")) == (
        "Office of Prison Oversight (10)",
        "Office of Prison Oversight",
        ("(10)",),
    )


def test_label_mark_asterisk_in_parentheses() -> None:
    # QOBL-Q24
    assert printed_text_marks(label("Full-Time Positions (*)")) == (
        "Full-Time Positions (*)",
        "Full-Time Positions",
        ("(*)",),
    )


def test_label_mark_line_formula() -> None:
    # BIB-Q38: config/resolved_assertions.yml:270 holds the normalized "23 29"
    found = label("Adjusted Fund Balance (23+29)")
    assert printed_text_marks(found) == (
        "Adjusted Fund Balance (23+29)",
        "Adjusted Fund Balance",
        ("(23+29)",),
    )
    assert found.norm == "adjusted fund balance"


def test_label_mark_two_asterisks_and_a_digit() -> None:
    # RTT-Q38, BSALES-Q27, ENT-Q07: config/entities.yml:4226
    assert printed_text_marks(label("Total RTT records **1")) == (
        "Total RTT records **1",
        "Total RTT records",
        ("**1",),
    )
    assert printed_text_marks(label("Total RTT records **12")) == (
        "Total RTT records **12",
        "Total RTT records",
        ("**12",),
    )


def test_label_mark_one_asterisk() -> None:
    # VAL-Q28
    assert printed_text_marks(label("TOTAL TAX REVENUE *")) == (
        "TOTAL TAX REVENUE *",
        "TOTAL TAX REVENUE",
        ("*",),
    )


def test_label_mark_comma_subtotal() -> None:
    # BSALES-Q27: config/entities.yml:4248
    assert printed_text_marks(label("Manufacturing, subtotal")) == (
        "Manufacturing, subtotal",
        "Manufacturing",
        (", subtotal",),
    )
    assert printed_text_marks(label("Manufacturing, SUBTOTAL")) == (
        "Manufacturing, SUBTOTAL",
        "Manufacturing",
        (", SUBTOTAL",),
    )


def test_label_mark_see_note_with_and_without_its_space() -> None:
    # WAGE-Q44: config/entities.yml:3679-3680
    spaced = label("Federal Gov't (includes US Post Office) see note")
    joined = label("Federal Gov 't (includes US Post Offic e) seenote")
    assert printed_text_marks(spaced) == (
        "Federal Gov't (includes US Post Office) see note",
        "Federal Gov't (includes US Post Office)",
        ("see note",),
    )
    assert printed_text_marks(joined) == (
        "Federal Gov 't (includes US Post Offic e) seenote",
        "Federal Gov 't (includes US Post Offic e)",
        ("seenote",),
    )
    assert spaced.squash == joined.squash == "federalgovtincludesuspostoffice"
    assert printed_text_marks(label("Federal Gov't (includes US Post Office) SEE NOTE")) == (
        "Federal Gov't (includes US Post Office) SEE NOTE",
        "Federal Gov't (includes US Post Office)",
        ("SEE NOTE",),
    )


def test_label_mark_see_note_with_any_one_space_between_its_words() -> None:
    # WAGE-Q44
    for space in ("\xa0", "\t", "\u2009"):
        found = label(f"Federal Government see{space}note")
        assert printed_text_marks(found) == (
            f"Federal Government see{space}note",
            "Federal Government",
            (f"see{space}note",),
        ), ascii(space)
        assert found.norm == label("Federal Government see note").norm == "federal government"
    assert printed_text_marks(label("Federal Government see\t\tnote")) == (
        "Federal Government see\t\tnote",
        "Federal Government see\t\tnote",
        (),
    )


def test_label_control_see_note_inside_a_word_keeps_every_word() -> None:
    # WAGE-Q44
    assert printed_text_marks(label("Oversee note")) == ("Oversee note", "Oversee note", ())


def test_label_mark_bare_digit_after_a_word() -> None:
    # ENT-Q07: entities.py:54-61 and tests/test_entities.py:1215-1225
    assert printed_text_marks(label("Sheriff 2")) == ("Sheriff 2", "Sheriff", ("2",))


def test_label_marks_keep_print_order() -> None:
    # ENT-Q07, WAGE-Q44
    assert printed_text_marks(label("Human Services (1) * see note")) == (
        "Human Services (1) * see note",
        "Human Services",
        ("(1)", "*", "see note"),
    )


def test_label_control_three_digit_code_keeps_every_word() -> None:
    # ENT-Q07: tests/test_entities.py:1227-1232
    assert printed_text_marks(label("CLASS 100")) == ("CLASS 100", "CLASS 100", ())


def test_label_control_leading_two_digit_code_keeps_every_word() -> None:
    # ENT-Q07: tests/test_entities.py:1227-1232
    assert printed_text_marks(label("10 COMMUNITY DEVELOPMENT")) == (
        "10 COMMUNITY DEVELOPMENT",
        "10 COMMUNITY DEVELOPMENT",
        (),
    )


def test_label_control_digit_after_a_number_or_a_mark_keeps_every_word() -> None:
    # MCITY-Q13, ENT-Q07
    assert printed_text_marks(label("Fiscal 202 4")) == ("Fiscal 202 4", "Fiscal 202 4", ())
    assert printed_text_marks(label("Total (1) 2")) == ("Total (1) 2", "Total (1) 2", ())


def test_label_control_leading_parenthesis_keeps_every_word() -> None:
    assert printed_text_marks(label("(Over) Under")) == ("(Over) Under", "(Over) Under", ())


def test_label_control_declared_prefix_becomes_the_line_number() -> None:
    # QPOS-Q08
    prefix, rest = split_line_prefix(line("5 Sheriff"), LINE_NUMBER)
    found = parse_label(prefix, rest.words)
    assert printed_text_marks(found) == ("5 Sheriff", "Sheriff", ())
    assert found.line_no == "5"
    assert printed_text_marks(label("5 Sheriff")) == ("5 Sheriff", "5 Sheriff", ())


def test_normalize_space_collapses_nonbreaking_spaces() -> None:
    # QOBL-Q02: the header qcmr.py:172-180 reads, as tests/test_qcmr.py:67 prints it
    assert normalize_space("CASH\xa0FLOW\xa0PROJECTIONS") == "CASH FLOW PROJECTIONS"
    assert normalize_space("GENERAL\xa0FUND \u2010 FY2025") == "GENERAL FUND-FY2025"


def test_normalize_space_reads_unicode_spaces_and_hyphens() -> None:
    assert normalize_space(" Debt\u2009Service\u202f \t Fund ") == "Debt Service Fund"
    assert normalize_space("Sub\u2011Total") == normalize_space("Sub - Total") == "Sub-Total"
    assert normalize_space("- 12 -") == "- 12 -"
    assert normalize_space("1 - 2") == "1 - 2"


def test_normalize_label_keeps_kerning_gaps_that_squash_joins() -> None:
    # BSALES-Q46
    gaps = ("truc k", "repai r", "T ax", "s oftware", "s tores")
    assert [normalize_label(gap) for gap in gaps] == [
        "truc k",
        "repai r",
        "t ax",
        "s oftware",
        "s tores",
    ]
    assert [matched(gap) for gap in gaps] == ["truck", "repair", "tax", "software", "stores"]


def test_normalize_label_drops_the_spacing_around_a_slash() -> None:
    # BSALES-Q47
    assert normalize_label("Delivery / couriers") == "delivery couriers"
    assert normalize_label("Delivery/couriers") == "delivery couriers"
    assert matched("Delivery / couriers") == matched("Delivery/couriers") == "deliverycouriers"


def test_normalize_label_reads_a_spaced_unicode_hyphen() -> None:
    # SUPOP-Q32: tests/test_supplemental_source_acknowledgments.py:219 and 222
    spaced = "Total Locally Generated Non \u2010 Tax Revenue"
    assert normalize_label(spaced) == normalize_label("Total Locally Generated Non-Tax Revenue")
    assert normalize_label(spaced) == "total locally generated non tax revenue"
    assert normalize_space("Sub \u2010 Total") == "Sub-Total"
    assert normalize_label("Sub \u2010 Total") == "sub total"


def test_normalize_label_casefolds_and_drops_underscores() -> None:
    assert normalize_label("Stra\xdfe") == normalize_label("STRASSE") == "strasse"
    assert normalize_label("Fund_Balance") == "fund balance"


def test_normalize_label_keeps_digit_separators() -> None:
    assert normalize_label("Fund 1,234.5 & Co., Inc.") == "fund 1,234.5 and co inc"
    assert normalize_label("Adjusted Fund Balance June 30 (23+29)") == (
        "adjusted fund balance june 30 23 29"
    )


def test_squash_joins_kerning_gaps() -> None:
    # ENT-Q10
    assert matched("Car and truc k rental") == matched("Car and truck rental")
    assert matched("Car and truc k rental") == "carandtruckrental"
    assert matched("Department s tores, retail") == "departmentstoresretail"


def test_squash_joins_a_glyph_seam_in_a_year() -> None:
    # MCITY-Q13
    assert matched("Fiscal 202 4") == matched("Fiscal 2024") == "fiscal2024"


def test_squash_matches_a_spaced_label() -> None:
    # MSCH-Q20
    assert matched("LI QUOR SALES TAX") == matched("LIQUOR SALES TAX") == "liquorsalestax"


def test_squash_matches_a_label_with_no_spaces() -> None:
    # SUPOP-Q19
    assert matched("PublicHealthSub-Total") == matched("Public Health Sub-Total")
    assert matched("PublicHealthSub-Total") == "publichealthsubtotal"


def test_split_line_prefix_takes_recap_line_numbers() -> None:
    # ENT-Q08
    for text, number, rest in (
        ("24 First Judicial District", "24", "First Judicial District"),
        ("I Records", "I", "Records"),
    ):
        prefix, after = split_line_prefix(line(text), LINE_NUMBER)
        assert [word.text for word in prefix] == [number]
        assert after.text == rest
        assert parse_label(prefix, after.words).line_no == number


def test_split_line_prefix_takes_numbered_recap_labels() -> None:
    # QOBL-Q55
    for text, number in (("1 First Judicial District", "1"), ("24 First Judicial District", "24")):
        prefix, after = split_line_prefix(line(text), LINE_NUMBER)
        found = parse_label(prefix, after.words)
        assert (found.printed, found.text, found.line_no) == (
            text,
            "First Judicial District",
            number,
        )


def test_split_line_prefix_takes_ocr_prefixes() -> None:
    # QPOS-Q08: config/entities.yml:4588-4608
    labels = ("I Civilian", "23 Civilian", "24 Civilian", "26 Civilian", "I Uniform", "26 Uniform")
    for text in labels:
        number, name = text.split(" ")
        (found,) = group_lines(page_from_text(f"#ocr\n{text}", SHA, 1))
        prefix, after = split_line_prefix(found, LINE_NUMBER)
        assert [word.text for word in prefix] == [number]
        assert [word.text for word in after.words] == [name]


def test_split_line_prefix_takes_leading_numbers() -> None:
    # QPOS-Q10: config/entities.yml:2550-2551
    for number in ("1", "2", "5", "23", "24", "25", "27"):
        prefix, after = split_line_prefix(line(f"{number} Recreation"), LINE_NUMBER)
        found = parse_label(prefix, after.words)
        assert (found.text, found.line_no) == ("Recreation", number)


def test_a_line_of_only_prefix_words_keeps_no_value_word() -> None:
    # QPOS-Q08
    lines = group_lines(page_from_text("23\n24\n26", SHA, 1))
    for found, number in zip(lines, ("23", "24", "26"), strict=True):
        prefix, rest = split_line_prefix(found, LINE_NUMBER)
        assert [word.text for word in prefix] == [number]
        assert rest.words == ()
        assert rest.box == found.box
        assert not has_values(rest)


@given(st.lists(word_texts, min_size=1, max_size=8), st.sampled_from(PREFIX_PATTERNS))
def test_split_line_prefix_loses_no_word(texts: list[str], pattern: str) -> None:
    whole = line(" ".join(texts))
    prefix, rest = split_line_prefix(whole, pattern)
    assert (*prefix, *rest.words) == whole.words
    assert (rest.page, rest.box) == (whole.page, whole.box)
    assert all(fullmatch(pattern, word.text) for word in prefix)
    assert not rest.words or not fullmatch(pattern, rest.words[0].text)
