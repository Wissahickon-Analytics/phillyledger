"""A `PdfReader` adapter on pdfplumber.

`WORDS` numbers what the adapter makes of pdfplumber's output: each word's size and style, the
rules and the order. A pull request that changes any of them raises it. `OPTIONS` holds the
options that `extract_words` runs with, those of the old backend. The tool string names
`WORDS` and each option, so a change to either gives every page new word keys.
"""

from collections.abc import Callable, Iterator, Sequence
from functools import partial
from io import BytesIO
from itertools import count
from json import dumps
from re import IGNORECASE, compile
from statistics import median
from types import MappingProxyType
from typing import Any

import pdfminer
import pdfplumber
from pdfminer.pdfpage import PDFPage
from pdfplumber.page import Page as PlumberPage

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.words import Document, Page, Rule, Word, WordSource
from datadesk.shell.ports import EffectError

WORDS = 1
OPTIONS = MappingProxyType(
    {"x_tolerance": 2, "y_tolerance": 2, "use_text_flow": True, "extra_attrs": ("fontname",)}
)

_BOLD = compile(r"bold|semibold|demibold|demi|black|heavy", IGNORECASE)
_THICKEST = 3
_SHORTEST = 8


class PdfPlumberReader:
    """Read PDFs with pdfplumber, which reads a page's text layer and no image on it.

    Each method walks pdfminer's pages from page 1 and builds no page after the last one it
    needs, so a broken box on a later page does not stop it. It never reads pdfplumber's page
    list and never calls `close`, since both build every page (design section 4). Any error
    the libraries raise becomes EffectError, chained, and its message names the page, or the
    file when it cannot be opened.
    """

    def page1_text(self, pdf: bytes) -> str:
        """Return the text that pdfplumber extracts from page 1.

        Raises
        ------
        EffectError
            For any error the libraries raise, and for a file with no page.
        """
        return _guarded("page 1", _page_at(pdf, 1).extract_text)

    def words(self, pdf: bytes, sha256: Sha256, pages: Sequence[int]) -> Document:
        """Return the words and rules of `pages`, or of every page when `pages` is empty.

        A word's text is what pdfplumber returns, a font code such as ``(cid:1)`` included. Its
        index counts the words of its page from 0 in pdfplumber's order. It is bold when its
        font's name holds bold, semibold, demibold, demi, black or heavy in any case, the old
        classifier's rule. Its size is the median size of its glyphs. The pages come back
        ascending, each with pdfplumber's width, height and rotation. Words and rules sit in
        the frame of the page as shown, so a page with ``/Rotate 90`` reads upright.

        Raises
        ------
        EffectError
            When the file lacks a page in `pages`, and for any error the libraries raise on a
            page at or before the last page in `pages`. pdfminer builds the pages in turn, so a
            page it cannot build, such as one with a crop box that is one number, stops the
            read of every later page (step 4 plan, fact 10).
        """
        wanted = frozenset(pages)
        source = WordSource(SourceKind.TEXT_LAYER, self.tool())
        read = tuple(
            _guarded(f"page {page.page_number}", partial(_page, page, sha256, source))
            for page in _pages(pdf, wanted)
        )
        if missing := wanted - {page.number for page in read}:
            raise EffectError(f"the file has no page {min(missing)}")
        return Document(sha256, read)

    def render(self, pdf: bytes, page: int, dpi: int) -> bytes:
        """Return the whole page as a PNG at `dpi`, drawn by pdfplumber's `to_image`.

        The image is the page turned by its rotation, in the frame that `words` uses, at
        `dpi` / 72 pixels to the point. It keeps every color pdfium draws.

        Raises
        ------
        EffectError
            When the file lacks the page, and for any error the libraries raise.
        """
        return _guarded(f"page {page}", partial(_png, _page_at(pdf, page), dpi))

    def tool(self) -> str:
        """Return the tool string of every page that `words` reads.

        It names the versions of pdfplumber and pdfminer.six, `WORDS`, and each of `OPTIONS`
        with its value in JSON. It leaves out ``return_chars``, which adds each word's glyphs
        to what pdfplumber returns and changes no word. The size the adapter reads from those
        glyphs counts in `WORDS`.
        """
        options = ";".join(
            f"{name}={dumps(value, separators=(',', ':'))}" for name, value in OPTIONS.items()
        )
        return (
            f"pdfplumber=={pdfplumber.__version__};pdfminer.six=={pdfminer.__version__};"
            f"words={WORDS};{options}"
        )


def _pages(pdf: bytes, wanted: frozenset[int]) -> Iterator[PlumberPage]:
    """Yield pdfplumber's page for each page in `wanted`, or for every page when it is empty.

    It stops after the last page in `wanted` and passes over a page the file lacks, which the
    caller reports.
    """
    document = _guarded("the file", partial(pdfplumber.open, BytesIO(pdf)))
    objects = PDFPage.create_pages(document.doc)
    last = max(wanted, default=0)
    for number in count(1):
        built = _guarded(f"page {number}", partial(next, objects, None))
        if built is None:
            return
        if not wanted or number in wanted:
            yield _guarded(
                f"page {number}", partial(PlumberPage, document, built, page_number=number)
            )
        if number == last:
            return


def _page_at(pdf: bytes, number: int) -> PlumberPage:
    page = next(_pages(pdf, frozenset((number,))), None)
    if page is None:
        raise EffectError(f"the file has no page {number}")
    return page


def _page(page: PlumberPage, sha256: Sha256, source: WordSource) -> Page:
    """Build the kit's page from pdfplumber's, each value of the type the kit declares.

    pdfplumber gives a whole-number width or height, such as 792, as an `int`, and the page
    holds it as a `float`. pdfplumber also gives the number the page's ``/Rotate`` holds, while
    pdfminer lays the page out by that number read as an integer, and as 0 when it is not one.
    So a rotation that is not an `int`, such as ``90.0``, would put the words in another frame
    than the page's width and height, and it raises ValueError.
    """
    if not isinstance(page.rotation, int):
        raise ValueError(f"the page's rotation {page.rotation!r} is not an integer")
    number = page.page_number
    words = tuple(
        Word(
            ref=WordRef(sha256, number, index),
            text=word["text"],
            box=_box(word),
            bold=_BOLD.search(word["fontname"]) is not None,
            size=float(median(char["size"] for char in word["chars"])),
            confidence=None,
        )
        for index, word in enumerate(page.extract_words(**OPTIONS, return_chars=True))
    )
    rules = tuple(
        rule for shape in (*page.lines, *page.rects) if (rule := _rule(_box(shape))) is not None
    )
    return Page(
        sha256, number, float(page.width), float(page.height), page.rotation, source, words, rules
    )


def _box(shape: dict[str, Any]) -> Box:
    return Box(float(shape["x0"]), float(shape["top"]), float(shape["x1"]), float(shape["bottom"]))


def _rule(box: Box) -> Rule | None:
    """Return the rule that a drawn line or rect with this box makes, or None when it makes none.

    A shape at most `_THICKEST` points across and at least `_SHORTEST` long is a rule, as in the
    old `rule_from_box`. Thicker is shading and shorter is a tick. The rule lies on the shape's
    centerline: an upright one is a box of no width at its middle x, so the kit reads it as
    vertical whatever the stroke's width, and a level one a box of no height at its middle y.
    A line object takes the same test as a rect, as in the old code, so a slanted line makes a
    rule only when its box is that thin one way and that long the other.
    """
    width, height = box.x1 - box.x0, box.bottom - box.top
    if width <= _THICKEST and height >= _SHORTEST:
        middle = (box.x0 + box.x1) / 2
        return Rule(Box(middle, box.top, middle, box.bottom))
    if height <= _THICKEST and width >= _SHORTEST:
        middle = (box.top + box.bottom) / 2
        return Rule(Box(box.x0, middle, box.x1, middle))
    return None


def _png(page: PlumberPage, dpi: int) -> bytes:
    image = BytesIO()
    page.to_image(resolution=dpi).save(image, format="PNG", quantize=False)
    return image.getvalue()


def _guarded[T](what: str, read: Callable[[], T]) -> T:
    """Run `read`, and turn any error it raises into EffectError, chained, naming `what`."""
    try:
        return read()
    except Exception as error:
        raise EffectError(f"pdfplumber cannot read {what}: {error!r}") from error
