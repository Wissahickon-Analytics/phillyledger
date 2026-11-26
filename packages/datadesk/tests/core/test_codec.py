from dataclasses import replace
from json import dumps, loads
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.words import Document, Page, Rule, Word, WordSource
from datadesk.core.codec import FORMAT, decode_document, encode_document, render_fixture

SHA = Sha256("5f238d579d4c1d7e2b3a4f5e6d7c8b9a0f1e2d3c4b5a69788796a5b4c3d2e1f0")
TOOL = "pdfplumber==0.11.10;pdfminer.six==20260107;words=1"
TEXT_PAGE = Page(
    SHA,
    35,
    792.0,
    612.0,
    90,
    WordSource(SourceKind.TEXT_LAYER, TOOL),
    (
        Word(WordRef(SHA, 35, 0), "Mural", Box(40.5, 100.25, 70.0, 108.0), True, 8.88, None),
        Word(WordRef(SHA, 35, 1, 0), "10", Box(300.0, 100.25, 309.5, 108.0), False, None, None),
    ),
    (Rule(Box(250.36, 90.0, 250.36, 500.0)),),
)
OCR_PAGE = Page(
    SHA,
    36,
    792.0,
    612.0,
    0,
    WordSource(SourceKind.OCR, "textract:AnalyzeDocument;dpi=300"),
    (Word(WordRef(SHA, 36, 0), "Arts", Box(41.0, 120.0, 60.0, 128.0), None, None, 97.5),),
)
DOC = Document(SHA, (TEXT_PAGE, OCR_PAGE))
ENCODED = encode_document(DOC)
DROP = object()
WORD = ("pages", 0, "words", 0)

finite_floats = st.floats(allow_nan=False, allow_infinity=False)
page_sizes = finite_floats | st.integers()
high_surrogates = st.characters(categories=["Cs"], max_codepoint=0xDBFF)
low_surrogates = st.characters(categories=["Cs"], min_codepoint=0xDC00)
any_text = (
    st.text()
    | st.text(high_surrogates, min_size=1)
    | st.text(low_surrogates, min_size=1)
    | st.tuples(high_surrogates, low_surrogates).map("".join)
)
sha256s = st.text("0123456789abcdef", min_size=64, max_size=64).map(Sha256)


@st.composite
def boxes(draw: st.DrawFn) -> Box:
    x0, x1 = sorted((draw(finite_floats), draw(finite_floats)))
    top, bottom = sorted((draw(finite_floats), draw(finite_floats)))
    return Box(x0, top, x1, bottom)


@st.composite
def pages(draw: st.DrawFn, sha: Sha256, number: int) -> Page:
    kind = draw(st.sampled_from(SourceKind))
    confidences = st.none() | st.floats(0, 100) if kind is SourceKind.OCR else st.none()
    places = st.tuples(st.integers(0, 40), st.none() | st.integers(0, 4))
    words = tuple(
        Word(
            WordRef(sha, number, index, child),
            draw(any_text),
            draw(boxes()),
            draw(st.none() | st.booleans()),
            draw(st.none() | finite_floats),
            draw(confidences),
        )
        for index, child in draw(st.lists(places, unique=True, max_size=5))
    )
    rules = tuple(draw(st.lists(boxes().map(Rule), max_size=3)))
    return Page(
        sha,
        number,
        draw(page_sizes),
        draw(page_sizes),
        draw(st.integers()),
        WordSource(kind, draw(any_text)),
        words,
        rules,
    )


@st.composite
def documents(draw: st.DrawFn) -> Document:
    sha = draw(sha256s)
    numbers = sorted(draw(st.sets(st.integers(1, 2_000), max_size=4)))
    return Document(sha, tuple(draw(pages(sha, number)) for number in numbers))


def edited(path: tuple[str | int, ...], value: object) -> bytes:
    fields: Any = loads(ENCODED)
    *steps, last = path
    held = fields
    for step in steps:
        held = held[step]
    if value is DROP:
        del held[last]
    else:
        held[last] = value
    return dumps(fields).encode()


@given(documents())
def test_a_document_decodes_to_an_equal_document(doc: Document) -> None:
    data = encode_document(doc)
    assert decode_document(data) == doc
    assert encode_document(decode_document(data)) == data


def test_one_document_encoded_twice_gives_the_same_bytes() -> None:
    assert encode_document(DOC) == encode_document(DOC)


def test_the_encoding_is_json_with_sorted_keys_no_spaces_and_the_format_number() -> None:
    page = replace(OCR_PAGE, words=(), rules=(Rule(Box(1.0, 2.0, 1.0, 9.5)),))
    assert encode_document(Document(SHA, (page,))) == (
        b'{"format":1,"pages":[{"doc_sha256":"' + SHA.encode() + b'","height":612.0,'
        b'"number":36,"rotation":0,"rules":[{"box":{"bottom":9.5,"top":2.0,"x0":1.0,"x1":1.0}}],'
        b'"source":{"kind":"ocr","tool":"textract:AnalyzeDocument;dpi=300"},"width":792.0,'
        b'"words":[]}],"sha256":"' + SHA.encode() + b'"}'
    )


def test_a_high_surrogate_then_a_low_one_read_back_as_two_code_points() -> None:
    word = replace(OCR_PAGE.words[0], text=chr(0xD835) + chr(0xDC00))
    doc = replace(DOC, pages=(TEXT_PAGE, replace(OCR_PAGE, words=(word,))))
    decoded = decode_document(encode_document(doc))
    assert decoded.pages[1].words[0].text == chr(0xD835) + chr(0xDC00)
    assert decoded == doc


def test_a_decoded_page_names_its_source_by_the_enum_member() -> None:
    kinds = [page.source.kind for page in decode_document(ENCODED).pages]
    assert kinds[0] is SourceKind.TEXT_LAYER
    assert kinds[1] is SourceKind.OCR


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_encode_refuses_a_float_json_cannot_hold(bad: float) -> None:
    word = replace(TEXT_PAGE.words[0], size=bad)
    doc = replace(DOC, pages=(replace(TEXT_PAGE, words=(word,)), OCR_PAGE))
    with pytest.raises(ValueError, match="JSON compliant"):
        encode_document(doc)


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"", id="no_bytes"),
        pytest.param(ENCODED[:-1], id="bytes_cut_at_the_end"),
        pytest.param(ENCODED[: len(ENCODED) // 2], id="bytes_cut_in_half"),
        pytest.param(b"\xff" + ENCODED, id="bytes_that_are_not_utf_8"),
        pytest.param(ENCODED.decode().encode("utf-16"), id="json_in_utf_16"),
        pytest.param(b"[]", id="a_json_list"),
        pytest.param(ENCODED.replace(b'"size":8.88', b'"size":NaN'), id="a_nan"),
        pytest.param(ENCODED.replace(b'"size":8.88', b'"size":Infinity'), id="an_infinity"),
    ],
)
def test_decode_refuses_bytes_that_are_not_an_encoded_document(data: bytes) -> None:
    with pytest.raises(ValueError):
        decode_document(data)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param(("format",), FORMAT + 1, id="another_format_number"),
        pytest.param(("format",), True, id="a_format_of_true"),
        pytest.param(("format",), float(FORMAT), id="a_format_that_is_a_float"),
        pytest.param(("format",), DROP, id="no_format"),
        pytest.param(("sha256",), SHA.upper(), id="a_sha_in_upper_case"),
        pytest.param(("pages", 0, "doc_sha256"), SHA[:63], id="a_page_sha_of_63_characters"),
        pytest.param((*WORD, "ref", "doc_sha256"), None, id="a_word_sha_that_is_null"),
        pytest.param(("pages", 0, "rules"), DROP, id="a_missing_key"),
        pytest.param((*WORD, "box", "x0"), "40.5", id="a_number_as_text"),
        pytest.param((*WORD, "bold"), 1, id="a_number_for_a_bool"),
        pytest.param((*WORD, "text"), 7, id="a_number_for_text"),
        pytest.param(("pages", 0, "number"), 35.0, id="a_float_for_an_int"),
        pytest.param(("pages", 0, "rotation"), False, id="a_bool_for_an_int"),
        pytest.param(("pages", 0), [], id="a_page_that_is_a_list"),
        pytest.param(("pages",), {}, id="pages_that_are_an_object"),
        pytest.param((*WORD, "box"), [40.5, 100.25, 70.0, 108.0], id="a_box_that_is_a_list"),
        pytest.param(("pages", 0, "source", "kind"), "scan", id="an_unknown_source"),
        pytest.param((*WORD, "box", "x1"), 1.0, id="an_inverted_box"),
        pytest.param(("pages", 1, "words", 0, "confidence"), 101, id="a_confidence_over_100"),
        pytest.param((*WORD, "confidence"), 50, id="a_confidence_on_a_text_layer"),
        pytest.param(("pages", 1, "number"), 35, id="a_page_number_twice"),
    ],
)
def test_decode_refuses_json_this_codec_did_not_write(
    path: tuple[str | int, ...], value: object
) -> None:
    with pytest.raises(ValueError):
        decode_document(edited(path, value))


@given(st.tuples(sha256s, st.integers(1, 2_000)).flatmap(lambda drawn: pages(*drawn)))
def test_a_rendered_fixture_runs_to_an_equal_page_and_renders_the_same_text(page: Page) -> None:
    text = render_fixture(page)
    namespace: dict[str, Any] = {}
    exec(text, namespace)
    assert namespace["PAGE"] == page
    assert repr(namespace["PAGE"]) == repr(page)
    assert render_fixture(namespace["PAGE"]) == text


def test_a_rendered_fixture_binds_the_sha_once_and_prints_one_word_or_rule_on_a_line() -> None:
    page = replace(TEXT_PAGE, width=792)
    text = render_fixture(page)
    assert text.count(SHA) == 1
    assert f"SHA = Sha256({str(SHA)!r})\n" in text
    assert "    width=792,\n" in text
    assert (
        "        Word(WordRef(SHA, 35, 0, None), 'Mural', Box(40.5, 100.25, 70.0, 108.0), "
        "True, 8.88, None),\n"
    ) in text
    assert "        Rule(Box(250.36, 90.0, 250.36, 500.0)),\n" in text
    assert "SourceKind.TEXT_LAYER" in text


def test_a_word_whose_text_holds_the_sha_is_printed_as_its_text() -> None:
    word = replace(TEXT_PAGE.words[0], text=f"see {SHA}")
    namespace: dict[str, Any] = {}
    exec(render_fixture(replace(TEXT_PAGE, words=(word,))), namespace)
    assert namespace["PAGE"].words[0].text == f"see {SHA}"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_render_fixture_refuses_a_float_a_module_cannot_hold(bad: float) -> None:
    word = replace(TEXT_PAGE.words[0], size=bad)
    with pytest.raises(ValueError, match="literal"):
        render_fixture(replace(TEXT_PAGE, words=(word,)))
