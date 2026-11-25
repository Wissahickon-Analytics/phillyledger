"""Row labels, kept apart from words so that tables and checks never import them."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Label:
    """A row label, with its marks and line number split off.

    Attributes
    ----------
    printed : str
        The words joined verbatim, line number included.
    text : str
        `printed` without its marks and line number.
    norm : str
        `text` after ``normalize_label``.
    squash : str
        `norm` without spaces, so "car and truc k rental" gives "carandtruckrental".
    marks : tuple[str, ...]
        The marks, such as "(1)", "**2", "*", "see note", "(19+20)" and ", subtotal".
    line_no : str or None
        The words that ``BodyRule.prefix`` split off, such as "23", "I" or "C01234".
    """

    printed: str
    text: str
    norm: str
    squash: str
    marks: tuple[str, ...]
    line_no: str | None
