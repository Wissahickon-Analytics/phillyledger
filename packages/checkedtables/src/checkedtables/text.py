from collections.abc import Sequence
from dataclasses import replace
from re import compile
from typing import TYPE_CHECKING

from checkedtables.labels import Label
from checkedtables.words import Word

if TYPE_CHECKING:
    from checkedtables.lines import Line

_HYPHEN = compile("[\u2010\u2011]")
_SPACE = compile(r"\s+")
_SPACED_HYPHEN = compile(r"(?<=[^\W\d_]) ?- ?(?=[^\W\d_])")
_PUNCTUATION = compile(r"(?!(?<=\d)[.,](?=\d))[^\w\s]|_")
_TRAILING_MARK = compile(
    r"\s*(?P<mark>"
    r"\(\d+(?:\+\d+)*\)"
    r"|\(\*\)"
    r"|\*\*\d+"
    r"|\*"
    r"|,\s*(?i:subtotal)"
    r"|(?<=\s)(?i:see ?note)"
    r"|(?<=[^\W\d_]\s)\d"
    r")\s*$"
)


def normalize_space(s: str) -> str:
    """Return text with one form of space and of hyphen.

    Every Unicode space becomes a plain space and runs of spaces collapse to one. U+2010 and
    U+2011 become ``-``, and a hyphen between two letters loses the spaces around it. The ends
    are trimmed.

    Parameters
    ----------
    s : str
        The text, such as the joined words of a line.

    Returns
    -------
    str
        The text with its spaces and hyphens normalized and nothing else changed.
    """
    spaced = _SPACE.sub(" ", _HYPHEN.sub("-", s)).strip()
    return _SPACED_HYPHEN.sub("-", spaced)


def normalize_label(s: str) -> str:
    """Return the form of a label that row matching compares.

    The text is casefolded, ``&`` reads as "and", and every punctuation mark becomes a space,
    except a comma or a point between two digits. Spaces are then normalized.

    Parameters
    ----------
    s : str
        The label text, without its marks and line number.

    Returns
    -------
    str
        The normalized label, such as "delivery couriers" for "Delivery / couriers".
    """
    return normalize_space(_PUNCTUATION.sub(" ", s.casefold().replace("&", " and ")))


def squash(norm: str) -> str:
    """Return a normalized label without spaces.

    The squashed form matches labels that a kerning gap splits, such as "car and truc k rental"
    and "car and truck rental".

    Parameters
    ----------
    norm : str
        A label after `normalize_label`.

    Returns
    -------
    str
        `norm` with every space removed.
    """
    return "".join(norm.split())


def parse_label(prefix: Sequence[Word], words: Sequence[Word]) -> Label:
    """Read a row label from its words, with its marks and line number split off.

    Marks leave the end of the label one at a time until none is left. A mark is a number or a
    line formula in parentheses ("(1)", "(23+29)"), "(*)", two asterisks and a number ("**1"),
    one asterisk, ", subtotal", "see note" or "seenote", or one digit after a word ("Sheriff 2").

    Parameters
    ----------
    prefix : Sequence[Word]
        The words that `split_line_prefix` took off the line. They become the line number.
    words : Sequence[Word]
        The label words, left to right.

    Returns
    -------
    Label
        The label. `printed` keeps every word, and `marks` keeps the marks in print order.
    """
    text = " ".join(word.text for word in words)
    marks: tuple[str, ...] = ()
    while found := _TRAILING_MARK.search(text):
        marks = (found["mark"], *marks)
        text = text[: found.start()]
    norm = normalize_label(text)
    return Label(
        printed=" ".join(word.text for word in (*prefix, *words)),
        text=text,
        norm=norm,
        squash=squash(norm),
        marks=marks,
        line_no=" ".join(word.text for word in prefix) or None,
    )


def split_line_prefix(line: "Line", pattern: str) -> tuple[tuple[Word, ...], "Line"]:
    """Take the leading words that match a table's line number pattern off a line.

    Parameters
    ----------
    line : Line
        The line, before lanes are found.
    pattern : str
        A regex that a line number word fullmatches, such as ``"I|[0-9]{1,2}"``.

    Returns
    -------
    tuple[tuple[Word, ...], Line]
        Every leading word that fullmatches `pattern`, and the line without them. The line keeps
        its page and box, and has no words when every word matched.
    """
    matcher = compile(pattern)
    cut = next(
        (index for index, word in enumerate(line.words) if not matcher.fullmatch(word.text)),
        len(line.words),
    )
    return line.words[:cut], replace(line, words=line.words[cut:])
