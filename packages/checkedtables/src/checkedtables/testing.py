"""Build pages from monospace text, for tests of code that reads words."""

from re import compile

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.words import Document, Page, Word, WordSource

_MARKER = compile(r"(?P<open>(?<![^ ])\*\*(?=[^ *]))|(?<=[^ *])\*\*(?![^ ])")
_WORD = compile(r"[^ ]+")
_TOOL = "checkedtables.testing.page_from_text"
_COLUMN = 6.0
_ROW = 12.0


def _unmark(row: str) -> tuple[str, tuple[bool, ...]]:
    """Take the bold markers out of a row, and say which kept characters were bold."""
    unpaired: list[int] = []
    spans: list[tuple[int, int]] = []
    for found in _MARKER.finditer(row):
        if found["open"]:
            unpaired.append(found.start())
        elif unpaired:
            spans.append((unpaired.pop(), found.start()))
    markers = {at + step for span in spans for at in span for step in (0, 1)}
    kept = [index for index in range(len(row)) if index not in markers]
    bold = tuple(any(start < index < end for start, end in spans) for index in kept)
    return "".join(row[index] for index in kept), bold


def page_from_text(text: str, sha: Sha256, page: int) -> Page:
    """Lay out a monospace block of text as the words of one page.

    A word is a run of characters with no ASCII space, so a tab or a non-breaking space stays
    inside a word. Character column ``c`` of line ``r`` starts at ``x0 = 6c`` and ``top = 12r``,
    and every word is 12 points tall. A ``**`` that starts a word opens a bold span when the
    next character of the word is not ``*``. A ``**`` that ends a word closes one when the
    character before it in the word is not ``*``, and it pairs with the nearest unpaired
    opening ``**`` to its left on the same line. A pair marks the words between it as bold and
    leaves the layout before columns are counted. Every other ``**`` stays in the text, so
    ``**1`` with no closer, ``**ab**cd``, ``x**ab**`` and ``***`` are words.

    Parameters
    ----------
    text : str
        The block, one page line per text line. When its first line is ``#ocr``, that line is
        dropped and the page reads as OCR.
    sha : Sha256
        The sha256 of the file the page belongs to.
    page : int
        The 1-based page number.

    Returns
    -------
    Page
        A page as wide as its longest line and as tall as its lines, with rotation 0. Word refs
        count the words in reading order from 0. A text layer word has ``bold`` set, size 12 and
        no confidence. An OCR word has no style and confidence 100.
    """
    rows = text.split("\n")
    kind = SourceKind.OCR if rows[0] == "#ocr" else SourceKind.TEXT_LAYER
    if kind is SourceKind.OCR:
        rows = rows[1:]
    laid_out = [_unmark(row) for row in rows]
    words: list[Word] = []
    for line, (plain, bold) in enumerate(laid_out):
        for match in _WORD.finditer(plain):
            start, end = match.span()
            ref = WordRef(sha, page, len(words))
            box = Box(_COLUMN * start, _ROW * line, _COLUMN * end, _ROW * (line + 1))
            if kind is SourceKind.OCR:
                words.append(Word(ref, match.group(), box, None, None, 100.0))
            else:
                words.append(Word(ref, match.group(), box, all(bold[start:end]), _ROW, None))
    width = _COLUMN * max((len(plain) for plain, _ in laid_out), default=0)
    source = WordSource(kind, _TOOL)
    return Page(sha, page, width, _ROW * len(rows), 0, source, tuple(words))


def doc_of(*pages: Page) -> Document:
    """Gather pages of one file into a document.

    Parameters
    ----------
    *pages : Page
        The pages, in any order.

    Returns
    -------
    Document
        The document of the pages' file, with the pages sorted by number.

    Raises
    ------
    ValueError
        When no page is given, when the pages come from more than one file, or when two pages
        have the same number.
    """
    if not pages:
        raise ValueError("doc_of needs at least one page")
    shas = sorted({page.doc_sha256 for page in pages})
    if len(shas) > 1:
        raise ValueError(f"doc_of takes pages of one file, not of {shas}")
    numbers = [page.number for page in pages]
    repeated = sorted({number for number in numbers if numbers.count(number) > 1})
    if repeated:
        raise ValueError(f"doc_of got page {repeated[0]} twice")
    return Document(shas[0], tuple(sorted(pages, key=lambda page: page.number)))
