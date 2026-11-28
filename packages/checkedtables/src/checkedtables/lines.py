"""Group a page's words into printed lines."""

from collections.abc import Sequence
from dataclasses import dataclass
from re import compile
from statistics import median

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box
from checkedtables.text import normalize_space
from checkedtables.words import Page, Rule, Word

_TOLERANCE = 0.35
_RAISED_SIZE = 0.7
_DIGITS = "0123456789"
_MARKS = "*\u2020\u2021\xa7#`\u2070\xb9\xb2\xb3\u2074-\u2079"
_VALUE_GLYPHS = r"\d,.$%()\-\u2212\u2013\u2014"
_MARK_WORD = compile(f"[{_MARKS}]+")
_FOOTNOTE = compile(f"[0-9][{_MARKS}]*")
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
    """The lines of one page, with the source of its words and the rules drawn on it.

    Attributes
    ----------
    number : int
        The 1-based page number.
    source : SourceKind
        The text layer or OCR.
    lines : tuple[Line, ...]
        The lines, top to bottom.
    rules : tuple[Rule, ...]
        The page's drawn lines, as the `Page` holds them. `cut_pages` finds the bands of a
        table's group captions between them.
    """

    number: int
    source: SourceKind
    lines: tuple[Line, ...]
    rules: tuple[Rule, ...] = ()


def _line(page: int, words: Sequence[Word]) -> Line:
    ordered = tuple(sorted(words, key=lambda word: word.box.x0))
    return Line(page, ordered, Box.around(word.box for word in ordered))


def _height(word: Word) -> float:
    return word.box.bottom - word.box.top


def _holder(word: Word, own: int, lines: Sequence[Line], medians: Sequence[float]) -> int:
    """Return the index of the nearest line that holds a word small for it, else `own`."""
    holders = [
        index
        for index, line in enumerate(lines)
        if line.box.top < word.box.bottom <= line.box.bottom
        and _height(word) < _RAISED_SIZE * medians[index]
    ]
    return min(holders, key=lambda index: lines[index].box.bottom, default=own)


def group_lines(page: Page) -> tuple[Line, ...]:
    """Group a page's words into lines by their bottoms, then move each small raised word.

    The words are taken by bottom, then `x0`, then ref. The first word opens a line. A later
    word joins the open line when its bottom is within 0.35 of the page's median word height
    of the bottom of the word that opened the line, and opens a new line otherwise. So lines
    never chain, and a tall word cannot bridge two lines.

    Then a line holds a word when the line's top is above the word's bottom, the line's bottom
    is at or below it, and the word's height is under 0.7 of the line's median word height,
    the ratio of the lexer's raised-digit rule (decision 14). Heights are box heights, in the
    page's units. Every line keeps the box and the median it had before any word moved, so
    moves never chain. Of the lines that hold a word, its own among them, it joins the one
    with the nearest bottom. No two lines share a bottom, so no tie can occur. A
    line that loses all its words is gone. QPOS-Q11: from FY2024 Q1, the bottom of the "(1)"
    after "Human Services" in Table P-1 is about 4.2 points above the label's, past the
    tolerance of 2.60, and this puts the mark back on its row.

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
    tolerance = _TOLERANCE * median(_height(word) for word in page.words)
    groups: list[list[Word]] = []
    for word in sorted(page.words, key=lambda word: (word.box.bottom, word.box.x0, word.ref)):
        if groups and word.box.bottom - groups[-1][0].box.bottom <= tolerance:
            groups[-1].append(word)
        else:
            groups.append([word])
    clusters = [_line(page.number, group) for group in groups]
    medians = [median(_height(word) for word in cluster.words) for cluster in clusters]
    members: list[list[Word]] = [[] for _ in clusters]
    for own, cluster in enumerate(clusters):
        for word in cluster.words:
            members[_holder(word, own, clusters, medians)].append(word)
    lines = (_line(page.number, words) for words in members if words)
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
        The lines that `group_lines` finds, and the page's rules.
    """
    return PageLines(page.number, page.source.kind, group_lines(page), page.rules)


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
    return bool(_value_words(line.words))


def _value_words(words: Sequence[Word]) -> tuple[Word, ...]:
    """Return the value words that end a line, left to right, without its mark words.

    A value word joins only while no word right of it is neither a value word nor a mark word.
    """
    found: list[Word] = []
    for word in reversed(words):
        if _MARK_WORD.fullmatch(word.text):
            continue
        if not _VALUE_WORD.fullmatch(word.text):
            break
        found.append(word)
    return tuple(reversed(found))


def _is_raised_digit(words: Sequence[Word]) -> bool:
    """Return whether the last word is a raised digit after a number, which is its mark.

    The last word is one digit, alone or with mark glyphs after it, under 0.7 of the size of
    the word before it, which holds a digit, and its bottom is above that word's bottom
    (VAL-Q28). `lex_cell` reads it as a mark, and `lanes_from_values` lets it join the cell of
    its number.
    """
    if len(words) < 2:
        return False
    number, digit = words[-2], words[-1]
    return (
        _FOOTNOTE.fullmatch(digit.text) is not None
        and any(glyph in _DIGITS for glyph in number.text)
        and digit.size is not None
        and number.size is not None
        and digit.size < _RAISED_SIZE * number.size
        and digit.box.bottom < number.box.bottom
    )


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
