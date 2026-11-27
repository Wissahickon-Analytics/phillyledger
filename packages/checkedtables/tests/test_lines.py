from collections import Counter
from dataclasses import replace
from statistics import median

from hypothesis import example, given
from hypothesis import strategies as st
from packages.checkedtables.tests.step_2_rule import step_2_rule_lines

from checkedtables.kinds import SourceKind
from checkedtables.lines import Line, PageLines, group_lines, has_values, lines_text, page_lines
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.testing import page_from_text
from checkedtables.words import Page, Rule, Word, WordSource

SHA = Sha256("a" * 64)
OTHER_SHA = Sha256("b" * 64)
TEXT_LAYER = WordSource(SourceKind.TEXT_LAYER, "pdfplumber==0.11.4;dedupe_chars")
OCR = WordSource(SourceKind.OCR, "textract:AnalyzeDocument;dpi=300")
SOURCES = (
    TEXT_LAYER,
    WordSource(SourceKind.TEXT_LAYER, "pdfplumber==0.11.4"),
    OCR,
    WordSource(SourceKind.OCR, "textract:DetectDocumentText;dpi=200"),
)
coordinates = st.floats(min_value=0.0, max_value=100.0)
sizes = st.floats(min_value=0.0, max_value=30.0)
boxes = st.builds(
    lambda x0, top, width, height: Box(x0, top, x0 + width, top + height),
    coordinates,
    coordinates,
    sizes,
    sizes,
)
splits = st.sampled_from(((None,), (0, 1), (0, 1, 2), (None, 0, 1), (None, 0, 1, 2)))
texts = st.sampled_from(
    ("Taxes", "1,234", "-", "*", "x", "", "$", "%", "(1,234)", "N/A")
) | st.text(max_size=5)
bolds = st.sampled_from((None, True, False))
font_sizes = st.none() | st.floats()
ocr_confidences = st.none() | st.floats(min_value=0.0, max_value=100.0)
page_sizes = st.floats(min_value=0.0, exclude_min=True, allow_infinity=False)
rotations = st.sampled_from((0, 90, 180, 270))
rules = st.lists(st.builds(Rule, boxes), max_size=3).map(tuple)


def placed(
    index: int, text: str, x0: float, top: float, bottom: float, child: int | None = None
) -> Word:
    box = Box(x0, top, x0 + 6.0 * len(text), bottom)
    return Word(WordRef(SHA, 1, index, child), text, box, False, 12.0, None)


def page_of(*words: Word, source: WordSource = TEXT_LAYER) -> Page:
    return Page(SHA, 1, 612.0, 792.0, 0, source, words)


STAIRCASE = page_of(*(placed(i, f"w{i}", 6.0 * i, 3.6 * i, 3.6 * i + 12.0) for i in range(40)))
UNEVEN_HEIGHTS = page_of(
    placed(0, "Taxes", 0.0, 0.0, 12.0),
    placed(1, "1,234", 300.0, 0.0, 12.0),
    placed(2, "Fees", 0.0, 6.0, 18.0),
    placed(3, "~", 500.0, 140.0, 200.0),
)
OUT_OF_ORDER = page_of(
    placed(0, "Grants", 0.0, 20.0, 32.0),
    placed(1, "45", 50.0, 18.0, 30.0),
    placed(2, "|", 200.0, 0.0, 50.0),
)
SPLIT_WORD = page_of(
    placed(0, "12.3%", 0.0, 0.0, 12.0, child=0),
    placed(0, "45,678", 30.0, 0.0, 12.0, child=1),
)
PARENT_WITH_CHILDREN = page_of(
    placed(0, "TAX434,605,553", 0.0, 0.0, 12.0),
    placed(0, "TAX", 0.0, 0.0, 12.0, child=0),
    placed(0, "434,605,553", 18.0, 0.0, 12.0, child=1),
)
LOW_CONFIDENCE = page_of(
    Word(WordRef(SHA, 1, 0), "Taxes", Box(0.0, 0.0, 30.0, 12.0), None, None, 100.0),
    Word(WordRef(SHA, 1, 1), "85.8", Box(60.0, 0.0, 84.0, 12.0), None, None, 89.0),
    source=OCR,
)
MOVED_OPENER = page_of(
    placed(0, "a", 0.0, 80.0, 100.0),
    placed(1, "a2", 20.0, 72.0, 102.0),
    placed(2, "b", 40.0, 74.0, 114.0),
    placed(3, "c", 60.0, 76.0, 116.0),
)
PAGE_2_OF_ANOTHER_FILE = replace(
    page_from_text("Taxes $ 1,234", OTHER_SHA, 2),
    rotation=90,
    rules=(Rule(Box(0.0, 14.0, 78.0, 14.0)),),
)


@st.composite
def pages(draw: st.DrawFn) -> Page:
    sha = draw(st.sampled_from((SHA, OTHER_SHA)))
    number = draw(st.integers(min_value=1, max_value=3))
    source = draw(st.sampled_from(SOURCES))
    confidences = ocr_confidences if source.kind is SourceKind.OCR else st.none()
    runs = draw(st.lists(splits, max_size=12))
    refs = [WordRef(sha, number, index, child) for index, run in enumerate(runs) for child in run]
    words = tuple(
        Word(ref, draw(texts), draw(boxes), draw(bolds), draw(font_sizes), draw(confidences))
        for ref in refs
    )
    return Page(
        sha, number, draw(page_sizes), draw(page_sizes), draw(rotations), source, words, draw(rules)
    )


def tolerance(page: Page) -> float:
    return 0.35 * median(word.box.bottom - word.box.top for word in page.words)


def height(word: Word) -> float:
    return word.box.bottom - word.box.top


def unmoved(page: Page) -> set[WordRef]:
    lines = step_2_rule_lines(page)
    boxes = [Box.around(word.box for word in found) for found in lines]
    medians = [median(height(word) for word in found) for found in lines]
    return {
        word.ref
        for own, found in enumerate(lines)
        for word in found
        if own
        == min(
            (
                index
                for index, box in enumerate(boxes)
                if box.top < word.box.bottom <= box.bottom and height(word) < 0.7 * medians[index]
            ),
            key=lambda index: boxes[index].bottom,
            default=own,
        )
    }


def line(text: str) -> Line:
    (only,) = group_lines(page_from_text(text, SHA, 1))
    return only


@given(pages())
@example(STAIRCASE)
@example(UNEVEN_HEIGHTS)
@example(SPLIT_WORD)
@example(PARENT_WITH_CHILDREN)
@example(LOW_CONFIDENCE)
@example(PAGE_2_OF_ANOTHER_FILE)
def test_every_word_lands_in_exactly_one_line(page: Page) -> None:
    lines = group_lines(page)
    assert Counter(word for found in lines for word in found.words) == Counter(page.words)
    assert all(found.words for found in lines)
    assert all(found.page == page.number for found in lines)


@given(pages())
@example(STAIRCASE)
@example(UNEVEN_HEIGHTS)
@example(MOVED_OPENER)
def test_the_unmoved_words_of_a_line_never_span_more_than_the_tolerance(page: Page) -> None:
    kept = unmoved(page)
    for found in group_lines(page):
        bottoms = [word.box.bottom for word in found.words if word.ref in kept]
        assert not bottoms or max(bottoms) - min(bottoms) <= tolerance(page)


@given(pages())
@example(STAIRCASE)
@example(UNEVEN_HEIGHTS)
@example(MOVED_OPENER)
def test_the_unmoved_words_keep_the_lines_the_step_2_rule_gives_them(page: Page) -> None:
    kept = unmoved(page)
    after = {frozenset(word.ref for word in found.words) & kept for found in group_lines(page)}
    before = {frozenset(word.ref for word in found) & kept for found in step_2_rule_lines(page)}
    assert after - {frozenset()} == before - {frozenset()}


@given(st.data())
def test_group_lines_ignores_word_order(data: st.DataObject) -> None:
    page = data.draw(pages())
    shuffled = tuple(data.draw(st.permutations(page.words)))
    assert group_lines(replace(page, words=shuffled)) == group_lines(page)
    assert group_lines(replace(page, words=page.words[::-1])) == group_lines(page)


@given(pages())
@example(OUT_OF_ORDER)
def test_lines_read_left_to_right_and_top_down(page: Page) -> None:
    lines = group_lines(page)
    assert [found.box.top for found in lines] == sorted(found.box.top for found in lines)
    for found in lines:
        assert [word.box.x0 for word in found.words] == sorted(word.box.x0 for word in found.words)
        assert found.box == Box.around(word.box for word in found.words)
        assert found.page == page.number


def test_words_at_one_place_keep_ref_order() -> None:
    words = tuple(placed(index, "8", 0.0, 0.0, 12.0) for index in range(3))
    (found,) = group_lines(page_of(*words[::-1]))
    assert found.words == words


def test_debris_between_two_rows_joins_neither() -> None:
    # QCASH-Q16, VAL-Q13
    page = page_of(
        placed(0, "Long-Term", 0.0, 100.0, 112.0),
        placed(1, "Debt", 60.0, 100.0, 112.0),
        placed(2, "12.3", 300.0, 100.0, 112.0),
        placed(3, "co", 330.0, 104.0, 118.0),
        placed(4, "~", 348.0, 108.0, 118.0),
        placed(5, "Interfund", 0.0, 112.0, 124.0),
        placed(6, "Charges", 60.0, 112.0, 124.0),
        placed(7, "45.6", 300.0, 112.0, 124.0),
    )
    assert [found.text for found in group_lines(page)] == [
        "Long-Term Debt 12.3",
        "co ~",
        "Interfund Charges 45.6",
    ]


def row_with(*extra: Word) -> Page:
    return page_of(
        placed(0, "Human", 0.0, 88.0, 100.0),
        placed(1, "Services", 36.0, 88.0, 100.0),
        placed(2, "1,428", 300.0, 88.0, 100.0),
        *extra,
    )


def line_texts(page: Page) -> list[str]:
    return [found.text for found in group_lines(page)]


def test_a_line_holds_a_word_whose_bottom_is_below_its_top_and_not_below_its_bottom() -> None:
    # QPOS-Q11
    assert line_texts(row_with(placed(3, "(1)", 90.0, 83.0, 88.0))) == [
        "(1)",
        "Human Services 1,428",
    ]
    assert line_texts(row_with(placed(3, "(1)", 90.0, 83.5, 88.5))) == ["Human Services (1) 1,428"]
    assert line_texts(row_with(placed(3, "(1)", 90.0, 95.0, 100.0))) == ["Human Services (1) 1,428"]
    assert line_texts(row_with(placed(3, "(1)", 90.0, 100.0, 105.0))) == [
        "Human Services 1,428",
        "(1)",
    ]


def test_a_word_moves_only_when_under_0_7_of_the_line_median() -> None:
    def page(mark_top: float) -> Page:
        return page_of(
            placed(0, "Aviation", 0.0, 90.0, 100.0),
            placed(1, "840", 300.0, 90.0, 100.0),
            placed(2, "639", 340.0, 90.0, 100.0),
            placed(3, "(1)", 60.0, mark_top, 93.0),
        )

    assert line_texts(page(86.0)) == ["(1)", "Aviation 840 639"]
    assert line_texts(page(86.1)) == ["Aviation (1) 840 639"]


def test_the_size_of_a_word_is_measured_against_its_line_and_not_the_page() -> None:
    title = tuple(placed(4 + index, "TITLE", 60.0 * index, 20.0, 40.0) for index in range(5))
    small_row = page_of(
        placed(0, "Aviation", 0.0, 90.0, 100.0),
        placed(1, "840", 300.0, 90.0, 100.0),
        placed(2, "639", 340.0, 90.0, 100.0),
        placed(3, "(1)", 60.0, 84.0, 92.0),
        *title,
    )
    assert line_texts(small_row)[1:] == ["(1)", "Aviation 840 639"]
    notes = tuple(placed(4 + index, "note", 30.0 * index, 195.0, 200.0) for index in range(6))
    tall_row = page_of(
        placed(0, "Aviation", 0.0, 80.0, 100.0),
        placed(1, "840", 300.0, 80.0, 100.0),
        placed(2, "639", 340.0, 80.0, 100.0),
        placed(3, "(1)", 60.0, 84.0, 90.0),
        *notes,
    )
    assert line_texts(tall_row)[0] == "Aviation (1) 840 639"


def test_a_word_two_lines_hold_joins_the_one_with_the_nearer_bottom() -> None:
    mark = placed(4, "(1)", 40.0, 87.0, 92.0)
    both_hold = page_of(
        placed(0, "Alpha", 0.0, 80.0, 100.0),
        placed(1, "12", 300.0, 80.0, 100.0),
        placed(2, "Beta", 0.0, 90.0, 110.0),
        placed(3, "34", 300.0, 90.0, 110.0),
        mark,
    )
    assert line_texts(both_hold) == ["Alpha (1) 12", "Beta 34"]
    mark_not_small_for_the_nearer = page_of(
        placed(0, "Alpha", 0.0, 80.0, 100.0),
        placed(1, "1", 300.0, 94.0, 100.0),
        placed(5, "2", 320.0, 94.0, 100.0),
        placed(2, "Beta", 0.0, 90.0, 110.0),
        placed(3, "34", 300.0, 102.0, 110.0),
        placed(6, "56", 340.0, 102.0, 110.0),
        mark,
    )
    assert line_texts(mark_not_small_for_the_nearer) == ["Alpha 1 2", "Beta (1) 34 56"]


def test_a_word_its_own_line_holds_stays_though_a_farther_line_also_holds_it() -> None:
    page = page_of(
        placed(0, "a", 0.0, 99.0, 100.0),
        placed(1, "a2", 20.0, 90.5, 102.5),
        placed(2, "b", 40.0, 84.0, 104.0),
        placed(3, "c", 60.0, 98.0, 106.0),
    )
    assert line_texts(page) == ["b c", "a a2"]


def test_two_rows_with_one_bottom_are_one_line_so_a_word_never_ties() -> None:
    page = page_of(
        placed(0, "Alpha", 0.0, 70.0, 100.0),
        placed(1, "12", 300.0, 90.0, 100.0),
        placed(2, "(1)", 40.0, 87.0, 92.0),
    )
    assert line_texts(page) == ["Alpha (1) 12"]


def test_a_full_size_word_inside_a_line_span_stays_on_its_own_line() -> None:
    assert line_texts(row_with(placed(3, "Note", 90.0, 83.0, 95.0))) == [
        "Note",
        "Human Services 1,428",
    ]


def test_a_label_that_ends_in_text_has_no_values() -> None:
    assert not has_values(line("Class 100 Total"))
    assert has_values(line("Class 100 Total 1,234"))


def test_a_row_that_ends_in_a_dash_has_values() -> None:
    for dash in ("-", "--", "\u2013", "\u2014"):
        assert has_values(line(f"Grants {dash}")), dash
    assert not has_values(line("Grants ---"))


def test_a_row_that_ends_in_a_mark_word_has_values() -> None:
    assert has_values(line("Debt Service 2.8 `"))
    superscripts = ("\xb9", "\xb2\xb3", "\u2070", "\u2074", "\u2079")
    for mark in ("*", "\u2020", "\u2021", "\xa7", "#", "`", "**", *superscripts):
        assert has_values(line(f"Debt Service 2.8 {mark}")), mark
        assert not has_values(line(f"Debt Service {mark}")), mark


def test_value_words_end_a_row_with_values() -> None:
    values = (
        "N/A",
        "NA",
        "1,234",
        "(1,234)",
        "$1,234",
        "$(1,234)",
        "12.3%",
        "-4.5",
        "\u22125",
        "\u20137",
        "\u20147",
        "242,096*",
        "1,234\xb9",
        "1,234\u2070",
        "1,234\u2079",
    )
    for value in values:
        assert has_values(line(f"Taxes {value}")), value
    for text in ("Total", "$", "%", "()", "N/A.", "na", "TAX434,605,553", "*242", "1o4.o"):
        assert not has_values(line(f"Taxes {text}")), text


def test_page_lines_carry_the_source_and_the_text() -> None:
    page = page_from_text("#ocr\nCASH\xa0FLOW  PROJECTIONS\n\nNon \u2010 Tax 1,234", SHA, 2)
    found = page_lines(page)
    assert found == PageLines(2, SourceKind.OCR, group_lines(page))
    assert [each.text for each in found.lines] == ["CASH FLOW PROJECTIONS", "Non-Tax 1,234"]
    assert lines_text(found.lines) == "CASH FLOW PROJECTIONS\nNon-Tax 1,234"
    assert lines_text(()) == ""
    assert group_lines(page_of()) == ()
