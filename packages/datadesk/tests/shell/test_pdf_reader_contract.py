from dataclasses import astuple
from importlib.metadata import version
from io import BytesIO
from math import ceil

import pytest
from packages.datadesk.tests.shell.pdfs import (
    NOT_RULES,
    RULES,
    SIDEWAYS,
    STYLED,
    drawn_pdf,
    image_pdf,
    text_pdf,
)
from PIL import Image

from checkedtables.kinds import SourceKind
from checkedtables.refs import Sha256, WordRef
from checkedtables.words import WordSource
from datadesk.shell.adapters import pdf_pdfplumber
from datadesk.shell.adapters.pdf_pdfplumber import PdfPlumberReader
from datadesk.shell.ports import EffectError

COVER = "FOR THE PERIOD ENDING SEPTEMBER 30, 2021"
SECOND_PAGE = "TABLE P-1 FULL-TIME POSITIONS"
SHA = Sha256("7c4a8d09ca3762af61e59520943dc26494f8941b7c4a8d09ca3762af61e59520")
READER = PdfPlumberReader()
TURNED = {1: "/Rotate 90"}


def test_page1_text_holds_the_words_of_page_1_alone() -> None:
    text = READER.page1_text(text_pdf(COVER, SECOND_PAGE))
    assert COVER in text
    assert SECOND_PAGE not in text


@pytest.mark.parametrize(
    "box",
    [
        pytest.param("/ArtBox [0 0]", id="a_box_with_two_numbers"),
        pytest.param("/ArtBox [0 0 612 /Wide]", id="a_box_with_a_name"),
        pytest.param("/CropBox 42", id="a_crop_box_that_is_one_number"),
    ],
)
def test_page1_text_reads_page_1_when_a_later_page_has_a_broken_box(box: str) -> None:
    text = READER.page1_text(text_pdf(COVER, SECOND_PAGE, entries={2: box}))
    assert COVER in text


def test_page1_text_of_an_image_page_is_empty() -> None:
    assert READER.page1_text(image_pdf()) == ""


@pytest.mark.parametrize(
    "pdf",
    [
        pytest.param(b"<html>Request blocked</html>", id="bytes_that_are_not_a_pdf"),
        pytest.param(text_pdf(), id="a_pdf_with_no_page"),
        pytest.param(
            text_pdf(COVER, entries={1: "/ArtBox [0 0 612 /Wide]"}),
            id="a_page_1_with_a_box_with_a_name",
        ),
        pytest.param(
            text_pdf(COVER, entries={1: "/ArtBox 42"}), id="a_page_1_with_a_box_that_is_one_number"
        ),
    ],
)
def test_page1_text_of_a_file_pdfplumber_cannot_read_is_an_effect_error(pdf: bytes) -> None:
    with pytest.raises(EffectError):
        READER.page1_text(pdf)


def test_a_text_layer_gives_each_words_text_box_style_and_size() -> None:
    page = READER.words(drawn_pdf(STYLED), SHA, (1,)).page(1)
    assert [(w.ref, w.text, w.bold, w.size, w.confidence) for w in page.words] == [
        (WordRef(SHA, 1, 0), "Total", True, 12.0, None),
        (WordRef(SHA, 1, 1), "1,234", False, 9.0, None),
    ]
    assert [astuple(w.box) for w in page.words] == [
        pytest.approx((72, 62.484, 100.668, 74.484)),
        pytest.approx((200, 64.863, 222.518, 73.863)),
    ]
    assert (page.doc_sha256, page.number, page.width, page.height, page.rotation) == (
        SHA,
        1,
        612,
        792,
        0,
    )
    assert page.source == WordSource(SourceKind.TEXT_LAYER, READER.tool())


def test_words_come_in_drawing_order_and_part_at_a_gap_of_two_and_a_half_points() -> None:
    pdf = drawn_pdf(
        "BT /F1 12 Tf 72 300 Td (LAST) Tj ET "
        "BT /F1 12 Tf 72 720 Td (12) Tj ET "
        "BT /F1 12 Tf 87.844 720 Td (34) Tj ET"
    )
    assert [w.text for w in READER.words(pdf, SHA, ()).page(1).words] == ["LAST", "12", "34"]


def test_a_words_size_is_the_median_size_of_its_glyphs() -> None:
    pdf = drawn_pdf("BT /F1 12 Tf 72 720 Td (AB) Tj /F1 11 Tf (C) Tj ET")
    assert [(w.text, w.size) for w in READER.words(pdf, SHA, ()).page(1).words] == [("ABC", 12.0)]


def test_every_value_has_the_type_the_kit_declares() -> None:
    pdf = drawn_pdf(f"{STYLED} {RULES}", SIDEWAYS, entries={2: "/Rotate 90"})
    pages = READER.words(pdf, SHA, ()).pages
    assert len(pages) == 2
    for page in pages:
        assert (type(page.number), type(page.rotation)) == (int, int)
        assert (type(page.width), type(page.height)) == (float, float)
        assert page.words
        assert page.rules
        for word in page.words:
            assert (type(word.ref.index), type(word.size)) == (int, float)
            assert {type(value) for value in astuple(word.box)} == {float}
        assert {type(value) for rule in page.rules for value in astuple(rule.box)} == {float}


def test_a_page_turned_by_rotate_90_reads_upright() -> None:
    page = READER.words(drawn_pdf(SIDEWAYS, entries=TURNED), SHA, ()).page(1)
    assert (page.width, page.height, page.rotation) == (792, 612, 90)
    assert [(w.text, astuple(w.box)) for w in page.words] == [
        ("TABLE", pytest.approx((72, 290.484, 110.016, 302.484))),
        ("P-1", pytest.approx((113.352, 290.484, 132.024, 302.484))),
    ]
    assert [astuple(rule.box) for rule in page.rules] == [pytest.approx((100.72, 400, 100.72, 600))]


def test_no_pages_asked_for_means_every_page() -> None:
    document = READER.words(text_pdf("ONE", "TWO"), SHA, ())
    assert document.sha256 == SHA
    assert [(p.number, [w.text for w in p.words]) for p in document.pages] == [
        (1, ["ONE"]),
        (2, ["TWO"]),
    ]


@pytest.mark.parametrize("pages", [(1, 3), (3, 1)])
def test_a_subset_of_pages_comes_back_ascending(pages: tuple[int, ...]) -> None:
    document = READER.words(text_pdf("ONE", "TWO", "THREE"), SHA, pages)
    assert [(p.number, [w.text for w in p.words]) for p in document.pages] == [
        (1, ["ONE"]),
        (3, ["THREE"]),
    ]


def test_one_pdf_read_twice_gives_equal_documents() -> None:
    pdf = drawn_pdf(STYLED, RULES, SIDEWAYS, entries={3: "/Rotate 90"})
    assert READER.words(pdf, SHA, ()) == READER.words(pdf, SHA, ())


def test_line_objects_and_thin_rects_give_rules_on_their_centerlines() -> None:
    page = READER.words(drawn_pdf(RULES), SHA, ()).page(1)
    assert [astuple(rule.box) for rule in page.rules] == [
        pytest.approx((100, 392, 300, 392)),
        pytest.approx((100, 442, 100, 492)),
        pytest.approx((72, 91.64, 472, 91.64)),
        pytest.approx((72, 191.64, 472, 191.64)),
        pytest.approx((72.36, 91.28, 72.36, 192)),
        pytest.approx((471.72, 91.28, 471.72, 192)),
    ]


def test_a_thick_rect_a_short_one_and_a_slanted_line_give_no_rule() -> None:
    assert READER.words(drawn_pdf(NOT_RULES), SHA, ()).page(1).rules == ()


def test_a_font_code_comes_back_as_pdfminer_writes_it() -> None:
    page = READER.words(text_pdf(r"1\0012"), SHA, ()).page(1)
    assert [w.text for w in page.words] == ["1(cid:1)2"]


def test_a_broken_box_after_the_last_page_asked_for_does_not_stop_the_read() -> None:
    document = READER.words(text_pdf("WANTED", "BAD", entries={2: "/CropBox 42"}), SHA, (1,))
    assert [w.text for w in document.page(1).words] == ["WANTED"]


@pytest.mark.parametrize("box", ["/ArtBox [0 0]", "/ArtBox [0 0 612 /Wide]", "/ArtBox 42"])
def test_a_box_only_pdfplumber_reads_on_a_page_not_asked_for_does_not_stop_the_read(
    box: str,
) -> None:
    document = READER.words(text_pdf("ONE", "SKIPPED", "THREE", entries={2: box}), SHA, (1, 3))
    assert [p.number for p in document.pages] == [1, 3]


@pytest.mark.parametrize(
    ("pdf", "pages", "named"),
    [
        pytest.param(
            text_pdf("BAD", "WANTED", entries={1: "/CropBox 42"}),
            (2,),
            1,
            id="a_crop_box_that_is_one_number_before_the_page_asked_for",
        ),
        pytest.param(
            text_pdf("ONE", "BAD", entries={2: "/ArtBox [0 0 612 /Wide]"}),
            (2,),
            2,
            id="a_box_with_a_name_on_the_page_asked_for",
        ),
        pytest.param(
            text_pdf("ONE", entries={1: "/Rotate 90.0"}),
            (),
            1,
            id="a_rotation_that_is_not_an_integer",
        ),
        pytest.param(
            text_pdf("ONE", entries={1: "/Rotate /East"}),
            (),
            1,
            id="a_rotation_that_is_a_name",
        ),
    ],
)
def test_a_page_the_libraries_cannot_read_is_an_effect_error_that_names_it(
    pdf: bytes, pages: tuple[int, ...], named: int
) -> None:
    with pytest.raises(EffectError, match=rf"\bpage {named}\b") as raised:
        READER.words(pdf, SHA, pages)
    assert isinstance(raised.value.__cause__, Exception)


def test_a_page_the_file_lacks_is_an_effect_error_that_names_it() -> None:
    with pytest.raises(EffectError, match=r"\bpage 3\b"):
        READER.words(text_pdf("ONE", "TWO"), SHA, (1, 3))


def test_bytes_that_are_not_a_pdf_are_an_effect_error() -> None:
    with pytest.raises(EffectError) as raised:
        READER.words(b"<html>Request blocked</html>", SHA, ())
    assert isinstance(raised.value.__cause__, Exception)


def test_the_tool_string_names_both_libraries_the_adapter_number_and_each_option() -> None:
    assert READER.tool() == (
        f"pdfplumber=={version('pdfplumber')};pdfminer.six=={version('pdfminer.six')};words=1;"
        'x_tolerance=2;y_tolerance=2;use_text_flow=true;extra_attrs=["fontname"]'
    )


def test_the_tool_string_changes_with_the_adapter_number(monkeypatch: pytest.MonkeyPatch) -> None:
    first = READER.tool()
    monkeypatch.setattr(pdf_pdfplumber, "WORDS", 2)
    assert READER.tool() == first.replace(";words=1;", ";words=2;")


@pytest.mark.parametrize(
    ("pdf", "dpi", "size"),
    [
        pytest.param(text_pdf("TOTAL"), 144, (1224, 1584), id="upright"),
        pytest.param(drawn_pdf(SIDEWAYS, entries=TURNED), 72, (792, 612), id="turned"),
    ],
)
def test_render_gives_the_page_at_the_dpi_with_ink_where_a_word_is(
    pdf: bytes, dpi: int, size: tuple[int, int]
) -> None:
    image = Image.open(BytesIO(READER.render(pdf, 1, dpi)))
    assert (image.format, image.size) == ("PNG", size)
    scale = dpi / 72
    box = READER.words(pdf, SHA, ()).page(1).words[0].box
    gray = image.convert("L")
    word = (
        int(box.x0 * scale),
        int(box.top * scale),
        ceil(box.x1 * scale),
        ceil(box.bottom * scale),
    )
    assert gray.crop(word).getextrema() == (0, 255)
    assert gray.crop((0, 0, 40, 40)).getextrema() == (255, 255)


@pytest.mark.parametrize(
    ("pdf", "page"),
    [
        pytest.param(text_pdf("ONE"), 2, id="a_page_the_file_lacks"),
        pytest.param(b"<html>Request blocked</html>", 1, id="bytes_that_are_not_a_pdf"),
        pytest.param(text_pdf("ONE", entries={1: "/CropBox 42"}), 1, id="a_broken_box"),
    ],
)
def test_render_of_a_page_it_cannot_read_is_an_effect_error(pdf: bytes, page: int) -> None:
    with pytest.raises(EffectError):
        READER.render(pdf, page, 72)
