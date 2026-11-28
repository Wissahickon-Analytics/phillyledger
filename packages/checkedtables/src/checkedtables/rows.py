"""Match a table's rows to its declared row schema, and report stray words."""

from dataclasses import dataclass

from checkedtables.words import Word


@dataclass(frozen=True, slots=True)
class RawRow:
    """One body line of a page, cut into its label, its cells and the words in neither.

    `cut_line` builds it. Every word of the line is in exactly one of `prefix`, `label_words`,
    `cells` and `stray`.

    Attributes
    ----------
    page : int
        The 1-based page number.
    prefix : tuple[Word, ...]
        The leading words that ``BodyRule.prefix`` split off, such as a printed line number.
    label_words : tuple[Word, ...]
        The words left of the binding's ``label_right``, a mark beside the label included.
    cells : tuple[tuple[str, tuple[Word, ...]], ...]
        Each column of the binding, in its declared order, with the words whose right edge is
        in its lane. A column that the page does not print has no words.
    stray : tuple[Word, ...]
        The words right of the label area that are in no lane.
    bold : bool or None
        Whether every label word is bold. None when a label word carries no style, as on an
        OCR page, or when the row has no label word.
    x0 : float
        The left edge of the row's first word after its prefix.
    """

    page: int
    prefix: tuple[Word, ...]
    label_words: tuple[Word, ...]
    cells: tuple[tuple[str, tuple[Word, ...]], ...]
    stray: tuple[Word, ...]
    bold: bool | None
    x0: float

    def has_values(self) -> bool:
        """Return whether a lane holds a word of the row."""
        return any(words for _, words in self.cells)
