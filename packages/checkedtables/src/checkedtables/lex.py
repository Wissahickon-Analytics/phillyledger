from collections.abc import Sequence
from dataclasses import replace
from decimal import Decimal
from re import compile

from checkedtables.cells import Amount, Blank, Cell, Dash, NotApplicable, Text, Unreadable
from checkedtables.columns import ColumnSpec
from checkedtables.kinds import PercentSign, SourceKind, ValueKind
from checkedtables.words import Word

_DIGITS = "0123456789"
_MINUS = "-\u2212\u2013\u2014"
_MARKS = "*\u2020\u2021\xa7#`\u2070\xb9\xb2\xb3\u2074\u2075\u2076\u2077\u2078\u2079"
_GLYPHS = f"{_DIGITS},.$%()+{_MINUS}{_MARKS}"
_DASHES = ("-", "--", "\u2013", "\u2014")
_NOT_APPLICABLE = ("N/A", "NA")
_TEXT_KINDS = (ValueKind.YEAR, ValueKind.CODE, ValueKind.TEXT)
_JOIN_KINDS = (ValueKind.MONEY, ValueKind.PERCENT)
_PERCENT_ALLOWED = (
    (PercentSign.ABSENT, False),
    (PercentSign.OPTIONAL, False),
    (PercentSign.OPTIONAL, True),
    (PercentSign.REQUIRED, True),
)
_RAISED_SIZE = 0.7
_CONFUSABLES = (
    ("B", "8"),
    ("b", "8"),
    ("D", "0"),
    ("d", "0"),
    ("O", "0"),
    ("o", "0"),
    ("Q", "0"),
    ("q", "0"),
    ("&", "6"),
)
_NUMBER = compile(
    r"(?!.*\$.*\$)\$?(?:(?P<open>\()|(?P<minus>[" + _MINUS + r"]))?\$?"
    r"(?P<digits>(?:0|[1-9][0-9]{0,2}(?:,[0-9]{3})*|[1-9][0-9]*)(?:\.[0-9]+)?)%?(?(open)\))"
)
_MARK_WORD = compile(f"[{_MARKS}]+")
_ONE_DIGIT = compile("[0-9]")
_JOINS = (
    (_ONE_DIGIT, compile("[0-9]{1,2}(?:,[0-9]{3})+")),
    (compile("[" + _MINUS + r"$]{0,2}[0-9]{1,3}(?:,[0-9]{3})*\.[0-9]+"), _ONE_DIGIT),
)
_LABEL_THEN_NUMBER = compile(r"(?<=[A-Za-z])(?=\(?\$?[0-9]{1,3}(?:,[0-9]{3})+(?![0-9]))")
_NUMBER_THEN_LABEL = compile(r"(?<![0-9,.])[0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?\)?(?=[A-Za-z])")
_AFTER_CLOSE = compile(r"(?<=[%)])(?=[0-9($])")


def _read_number(token: str) -> Decimal | None:
    found = _NUMBER.fullmatch(token)
    if found is None:
        return None
    sign = "-" if found["open"] or found["minus"] else ""
    return Decimal(sign + found["digits"].replace(",", ""))


def _is_raised_digit(words: Sequence[Word]) -> bool:
    if len(words) < 2:
        return False
    number, digit = words[-2], words[-1]
    return (
        _ONE_DIGIT.fullmatch(digit.text) is not None
        and any(glyph in _DIGITS for glyph in number.text)
        and digit.size is not None
        and number.size is not None
        and digit.size < _RAISED_SIZE * number.size
        and digit.box.bottom < number.box.bottom
    )


def _tokens_and_marks(words: Sequence[Word]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    kept = list(words)
    marks: list[str] = []
    # VAL-Q28: footnote marks, superscript digits and a small raised digit end the cell.
    while kept and (_MARK_WORD.fullmatch(kept[-1].text) or _is_raised_digit(kept)):
        marks.insert(0, kept.pop().text)
    tokens = [word.text for word in kept]
    if tokens and (number := tokens[-1].rstrip(_MARKS)) != tokens[-1]:
        marks.insert(0, tokens[-1][len(number) :])
        tokens[-1] = number
    # VAL-Q09: a "$" set as its own word before the number.
    if tokens[:1] == ["$"]:
        tokens = tokens[1:]
    return tuple(tokens), tuple(marks)


def _joined(tokens: Sequence[str], col: ColumnSpec, source: SourceKind) -> str | None:
    if len(tokens) != 2 or col.kind not in _JOIN_KINDS or source is not SourceKind.TEXT_LAYER:
        return None
    wrapped = tokens[0].startswith("(") and tokens[1].endswith(")")
    opening, closing = ("(", ")") if wrapped else ("", "")
    head, tail = tokens[0].removeprefix(opening), tokens[1].removesuffix(closing)
    for head_shape, tail_shape in _JOINS:
        if head_shape.fullmatch(head) and tail_shape.fullmatch(tail):
            joined = f"{opening}{head}{tail}{closing}"
            return joined if _read_number(joined) is not None else None
    return None


def _sign_trouble(token: str) -> bool:
    start = next((index for index, glyph in enumerate(token) if glyph in _DIGITS), len(token))
    lead, rest = token[:start], token[start:]
    opens = token.count("(")
    return (
        "+" in token
        or any(glyph in rest for glyph in _MINUS)
        or opens != token.count(")")
        or "(" in rest
        or ")" in lead
        or opens + sum(lead.count(glyph) for glyph in _MINUS) > 1
    )


def _read_cell(tokens: Sequence[str], col: ColumnSpec, source: SourceKind) -> Decimal | str:
    glyphs = "".join(tokens)
    if not any(glyph in _DIGITS for glyph in glyphs) or any(g not in _GLYPHS for g in glyphs):
        return "not_a_number"
    token = tokens[0] if len(tokens) == 1 else _joined(tokens, col, source)
    if token is None:
        return "two_tokens"
    if _sign_trouble(token):
        return "sign"
    if (col.fmt.percent, "%" in token) not in _PERCENT_ALLOWED:
        return "percent_sign"
    number = _read_number(token)
    if number is None:
        return "grouping"
    if col.fmt.decimals is not None and len(f"{number:f}".partition(".")[2]) != col.fmt.decimals:
        return "decimals"
    return number


def split_numeric_runs(word: Word) -> tuple[Word, ...]:
    """Cut a word where a label and a number, or two numbers, were printed with no space.

    A cut falls between an ASCII letter and a comma-grouped number on either side, so ``FY2016``
    stays one word. Before the number a ``(`` or ``$`` may follow the letter, as in
    "TAX$434,605", and after it a decimal part and a ``)`` may come before the letter, as in
    "(408,491.2)NET". A cut also falls after a ``%`` or a ``)`` that a digit, a ``(`` or a
    ``$`` follows.

    Parameters
    ----------
    word : Word
        The word as the source read it.

    Returns
    -------
    tuple[Word, ...]
        The word itself when it holds one run. Otherwise one child per run, left to right, such
        as "TAX" and "434,605,553" for "TAX434,605,553" or "12.3%" and "45,678" for
        "12.3%45,678". Child ``k`` has ``ref.child == k`` and the part of the word's box that its
        characters take, in proportion to the character count, so its box is approximate.
    """
    text = word.text
    cuts = sorted(
        {found.start() for found in _LABEL_THEN_NUMBER.finditer(text)}
        | {found.end() for found in _NUMBER_THEN_LABEL.finditer(text)}
        | {found.start() for found in _AFTER_CLOSE.finditer(text)}
    )
    if not cuts:
        return (word,)
    width = word.box.x1 - word.box.x0
    return tuple(
        replace(
            word,
            ref=replace(word.ref, child=child),
            text=text[start:end],
            box=replace(
                word.box,
                x0=word.box.x0 + width * start / len(text),
                x1=word.box.x0 + width * end / len(text),
            ),
        )
        for child, (start, end) in enumerate(zip((0, *cuts), (*cuts, len(text)), strict=True))
    )


def lex_cell(words: Sequence[Word], col: ColumnSpec, source: SourceKind) -> Cell:
    """Read the words of one cell as a typed cell, only from what the words print.

    The rules apply in order. No words give `Blank`, and a year, code or text column gives
    `Text`. The text "N/A" or "NA" gives `NotApplicable`, and "-", "--", an en dash or an em
    dash gives a `Dash` with the column's meaning. A number may end in marks, which the
    `Amount` keeps apart from its value: the glyphs ``*``, ``†``, ``‡``, ``§``, ``#``, a
    backtick and superscript digits, and a last one-digit word under 0.7 of the size of the
    number word just before it whose bottom is above that word's bottom. A ``$`` word may stand
    first in the cell.

    A word reads as a number when paired parentheses around it or one leading minus glyph
    (``-``, U+2212, an en dash or an em dash) give its sign, a ``$`` stands at most once before
    the digits on either side of that sign, the digits are ASCII, 1 to 3 then comma groups of
    3, or plain, then an optional point and digits, with a leading zero only as the whole
    integer part, and a ``%``, if any, follows the digits inside the parentheses. Two words
    read as one number only in a money or percent column on a text layer, in two printed forms,
    each of which may sit inside one pair of parentheses: one bare digit, then 1 or 2 digits
    and comma groups ("1 37,332,523"), or a number with a point whose integer part is 1 to 3
    digits or comma-grouped, with an optional ``$`` and minus glyph, then one digit
    ("67,215,504.0 0"). Whether a ``%`` may or must be printed follows ``col.fmt.percent``,
    and the printed decimals must equal ``col.fmt.decimals`` unless it is None.

    Parameters
    ----------
    words : Sequence[Word]
        The words of the cell, left to right.
    col : ColumnSpec
        The column the cell sits in.
    source : SourceKind
        The source of the page's words.

    Returns
    -------
    Cell
        An `Amount` whose `printed` is a Decimal built from the printed digits, sign and point,
        with its marks. A cell of a number column that is not blank, N/A or a dash and does not
        read as a number is `Unreadable`, with the first reason that applies of
        "not_a_number" (a character that no number, sign, mark or separator uses, or no
        digit), "two_tokens" (two or more words in no form that reads as one number), "sign" (a
        plus sign, a minus after a digit, an unpaired or misplaced parenthesis, or two signs),
        "percent_sign", "grouping" (what is left is not one strictly grouped number, a
        misplaced ``$`` or ``%`` included) and "decimals". An `Amount` and an `Unreadable` keep
        the word texts joined by one space and the ref of every word, the ``$`` and mark words
        included.
    """
    if not words:
        return Blank()
    text = " ".join(word.text for word in words)
    refs = tuple(word.ref for word in words)
    if col.kind in _TEXT_KINDS:
        return Text(text, refs)
    if text in _NOT_APPLICABLE:
        return NotApplicable(text, refs)
    if text in _DASHES:
        return Dash(text, refs, col.dash)
    tokens, marks = _tokens_and_marks(words)
    number = _read_cell(tokens, col, source)
    if isinstance(number, str):
        return Unreadable(text, refs, number)
    return Amount(number, text, refs, source, marks=marks)


def transliteration_ok(seen: str, reading: str) -> bool:
    """Return whether a reading keeps every digit that extraction saw, in order.

    Each glyph of `seen` counts as its digit when it is an ASCII digit or one of the OCR
    confusables ``B`` and ``b`` for 8, ``D``, ``d``, ``O``, ``o``, ``Q`` and ``q`` for 0, and
    ``&`` for 6. Every other glyph of either text counts as nothing. So a reading may add or
    drop any glyph that is not a digit, such as a point or a sign, and may never change, drop
    or add a digit.

    Parameters
    ----------
    seen : str
        What extraction returns inside the reviewed box, such as "1o4.o".
    reading : str
        What a person reads on the rendered page, such as "104.0".

    Returns
    -------
    bool
        True when the digits of `reading` equal the digits and confusables of `seen`, so
        "2918" to "291.8" passes and "65.8" to "85.8" fails.
    """
    read = "".join(glyph for glyph in reading if glyph in _DIGITS)
    return "".join(_transliterated(glyph) for glyph in seen) == read


def _transliterated(glyph: str) -> str:
    if glyph in _DIGITS:
        return glyph
    return next((digit for confusable, digit in _CONFUSABLES if confusable == glyph), "")
