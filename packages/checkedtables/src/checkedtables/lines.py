from collections.abc import Sequence
from dataclasses import dataclass
from re import compile
from statistics import median

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box
from checkedtables.text import normalize_space
from checkedtables.words import Page, Word

_TOLERANCE = 0.35
_MARKS = "*\u2020\u2021\xa7#`\u2070\xb9\xb2\xb3\u2074-\u2079"
_VALUE_GLYPHS = r"\d,.$%()\-\u2212\u2013\u2014"
_MARK_WORD = compile(f"[{_MARKS}]+")
_VALUE_WORD = compile(
    rf"N/A|NA|-|--|\u2013|\u2014|[{_VALUE_GLYPHS}]*\d[{_VALUE_GLYPHS}]*[{_MARKS}]*"
)


@dataclass(frozen=True, slots=True)
class Line:
    """The words of one printed line of a page.

    Attributes
    ----------
    page : int
        The 1-based page number.
    words : tuple[Word, ...]
        The words, left to right.
    box : Box
        The box around the words that `group_lines` found on the line.
    """

    page: int
    words: tuple[Word, ...]
    box: Box

    @property
    def text(self) -> str:
        """Return the words joined by spaces, after `normalize_space`."""
        return normalize_space(" ".join(word.text for word in self.words))


@dataclass(frozen=True, slots=True)
class PageLines:
    """The lines of one page, with the source of its words.

    Attributes
    ----------
    number : int
        The 1-based page number.
    source : SourceKind
        The text layer or OCR.
    lines : tuple[Line, ...]
        The lines, top to bottom.
    """

    number: int
    source: SourceKind
    lines: tuple[Line, ...]


def _line(page: int, words: Sequence[Word]) -> Line:
    ordered = tuple(sorted(words, key=lambda word: word.box.x0))
    return Line(page, ordered, Box.around(word.box for word in ordered))


def group_lines(page: Page) -> tuple[Line, ...]:
    """Group a page's words into lines by their bottoms.

    The words are taken by bottom, then `x0`, then ref. The first word opens a line. A later
    word joins the open line when its bottom is within 0.35 of the page's median word height
    of the bottom of the word that opened the line, and opens a new line otherwise. So lines
    never chain, and a tall word cannot bridge two lines.

    Parameters
    ----------
    page : Page
        The page.

    Returns
    -------
    tuple[Line, ...]
        The lines sorted by top, each with its words sorted by `x0`. Every word of the page is
        in exactly one line.
    """
    if not page.words:
        return ()
    tolerance = _TOLERANCE * median(word.box.bottom - word.box.top for word in page.words)
    groups: list[list[Word]] = []
    for word in sorted(page.words, key=lambda word: (word.box.bottom, word.box.x0, word.ref)):
        if groups and word.box.bottom - groups[-1][0].box.bottom <= tolerance:
            groups[-1].append(word)
        else:
            groups.append([word])
    lines = (_line(page.number, group) for group in groups)
    return tuple(sorted(lines, key=lambda line: line.box.top))


def page_lines(page: Page) -> PageLines:
    """Return a page's lines with its number and the source of its words.

    Parameters
    ----------
    page : Page
        The page.

    Returns
    -------
    PageLines
        The lines that `group_lines` finds.
    """
    return PageLines(page.number, page.source.kind, group_lines(page))


def has_values(line: Line) -> bool:
    """Return whether a line ends in a value word.

    The last word that is not a mark word decides. A mark word holds only ``*``, ``†``, ``‡``,
    ``§``, ``#``, a backtick and superscript digits. A value word is ``N/A``, ``NA``, a dash
    placeholder (``-``, ``--``, an en dash or an em dash), or a digit with nothing else but
    ``,``, ``.``, ``$``, ``%``, parentheses, minus glyphs and trailing marks.

    Parameters
    ----------
    line : Line
        The line.

    Returns
    -------
    bool
        True when the line ends in a value word, so "Class 100 Total" has no values.
    """
    for word in reversed(line.words):
        if not _MARK_WORD.fullmatch(word.text):
            return _VALUE_WORD.fullmatch(word.text) is not None
    return False


def lines_text(lines: Sequence[Line]) -> str:
    """Return the text of each line, joined with a newline.

    Parameters
    ----------
    lines : Sequence[Line]
        The lines.

    Returns
    -------
    str
        The `Line.text` of each line in order, one per text line.
    """
    return "\n".join(line.text for line in lines)
