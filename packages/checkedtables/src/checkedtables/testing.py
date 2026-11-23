from re import compile

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, WordRef
from checkedtables.words import Document, Page, Word, WordSource

_BOLD = compile(r"\*\*(.+?)\*\*")
_WORD = compile(r"[^ ]+")
_TOOL = "checkedtables.testing.page_from_text"
_COLUMN = 6.0
_ROW = 12.0


def _unmark(row: str) -> tuple[str, tuple[bool, ...]]:
    parts = _BOLD.split(row)
    bold = tuple(index % 2 == 1 for index, part in enumerate(parts) for _ in part)
    return "".join(parts), bold


def page_from_text(text: str, sha: str, page: int) -> Page:
    """Lay out a monospace block of text as the words of one page.

    A word is a run of characters with no space. Character column ``c`` of line ``r`` starts at
    ``x0 = 6c`` and ``top = 12r``, and every word is 12 points tall. A pair of ``**`` marks the
    text between it as bold and leaves the layout before columns are counted. A lone ``**``
    stays in the text.

    Parameters
    ----------
    text : str
        The block, one page line per text line. When its first line is ``#ocr``, that line is
        dropped and the page reads as OCR.
    sha : str
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
