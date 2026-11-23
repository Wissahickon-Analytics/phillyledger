from collections import Counter
from dataclasses import replace
from itertools import pairwise
from statistics import median

from hypothesis import example, given
from hypothesis import strategies as st

from checkedtables.kinds import SourceKind
from checkedtables.lines import Line, PageLines, group_lines, has_values, lines_text, page_lines
from checkedtables.refs import Box, WordRef
from checkedtables.testing import page_from_text
from checkedtables.words import Page, Word, WordSource

SHA = "a" * 64
TEXT_LAYER = WordSource(SourceKind.TEXT_LAYER, "pdfplumber==0.11.4;dedupe_chars")
OCR = WordSource(SourceKind.OCR, "textract:AnalyzeDocument;dpi=300")
coordinates = st.floats(min_value=0.0, max_value=100.0)
sizes = st.floats(min_value=0.0, max_value=30.0)
boxes = st.builds(
    lambda x0, top, width, height: Box(x0, top, x0 + width, top + height),
    coordinates,
    coordinates,
    sizes,
    sizes,
)
splits = st.sampled_from(((None,), (0, 1), (0, 1, 2)))
texts = st.sampled_from(("Taxes", "1,234", "-", "*", "x", ""))
bolds = st.sampled_from((None, True, False))
font_sizes = st.none() | st.floats()
ocr_confidences = st.none() | st.floats(min_value=0.0, max_value=100.0)


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
LOW_CONFIDENCE = page_of(
    Word(WordRef(SHA, 1, 0), "Taxes", Box(0.0, 0.0, 30.0, 12.0), None, None, 100.0),
    Word(WordRef(SHA, 1, 1), "85.8", Box(60.0, 0.0, 84.0, 12.0), None, None, 89.0),
    source=OCR,
)


@st.composite
def pages(draw: st.DrawFn) -> Page:
    source = draw(st.sampled_from((TEXT_LAYER, OCR)))
    confidences = ocr_confidences if source is OCR else st.none()
    runs = draw(st.lists(splits, max_size=12))
    refs = [WordRef(SHA, 1, index, child) for index, run in enumerate(runs) for child in run]
    words = [
        Word(ref, draw(texts), draw(boxes), draw(bolds), draw(font_sizes), draw(confidences))
        for ref in refs
    ]
    return page_of(*words, source=source)


def tolerance(page: Page) -> float:
    return 0.35 * median(word.box.bottom - word.box.top for word in page.words)


def line(text: str) -> Line:
    (only,) = group_lines(page_from_text(text, SHA, 1))
    return only


@given(pages())
@example(STAIRCASE)
@example(UNEVEN_HEIGHTS)
@example(SPLIT_WORD)
@example(LOW_CONFIDENCE)
def test_every_word_lands_in_exactly_one_line(page: Page) -> None:
    lines = group_lines(page)
    assert Counter(word for found in lines for word in found.words) == Counter(page.words)
    assert all(found.words for found in lines)


@given(pages())
@example(STAIRCASE)
@example(UNEVEN_HEIGHTS)
def test_a_line_never_spans_more_than_the_tolerance(page: Page) -> None:
    for found in group_lines(page):
        bottoms = [word.box.bottom for word in found.words]
        assert max(bottoms) - min(bottoms) <= tolerance(page)


@given(pages())
@example(STAIRCASE)
@example(UNEVEN_HEIGHTS)
def test_a_word_within_the_tolerance_never_opens_a_line(page: Page) -> None:
    openers = sorted(min(word.box.bottom for word in found.words) for found in group_lines(page))
    assert all(after - before > tolerance(page) for before, after in pairwise(openers))


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
