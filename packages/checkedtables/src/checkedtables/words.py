from dataclasses import dataclass

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, WordRef


@dataclass(frozen=True, slots=True)
class WordSource:
    """The tool that read a page's words.

    Attributes
    ----------
    kind : SourceKind
        The text layer or OCR.
    tool : str
        The tool and its settings, such as ``"pdfplumber==0.11.4;dedupe_chars"`` or
        ``"textract:AnalyzeDocument;dpi=300"``.
    """

    kind: SourceKind
    tool: str


@dataclass(frozen=True, slots=True)
class Word:
    """One word as the source read it.

    Attributes
    ----------
    ref : WordRef
        The file, page and extraction place of the word.
    text : str
        The text verbatim, before any cleaning.
    box : Box
        Where the word sits on the page.
    bold : bool or None
        None when the source carries no style, as for every OCR word.
    size : float or None
        The font size, when the source gives one.
    confidence : float or None
        The OCR confidence from 0 to 100. None for a text layer.
    """

    ref: WordRef
    text: str
    box: Box
    bold: bool | None
    size: float | None
    confidence: float | None


@dataclass(frozen=True, slots=True)
class Rule:
    """A line drawn on the page. It is vertical when its box is less than 1 pt wide."""

    box: Box


@dataclass(frozen=True, slots=True)
class Page:
    """One page of a publisher file, with words from one source.

    Attributes
    ----------
    doc_sha256 : str
        The sha256 of the publisher file.
    number : int
        The 1-based page number in the publisher file.
    width, height : float
        The page size.
    rotation : int
        The page rotation in degrees.
    source : WordSource
        The tool that read every word on the page.
    words : tuple[Word, ...]
        The words, each from this file and page.
    rules : tuple[Rule, ...]
        The drawn lines.

    Raises
    ------
    ValueError
        When a word's ref names another file or another page.
    """

    doc_sha256: str
    number: int
    width: float
    height: float
    rotation: int
    source: WordSource
    words: tuple[Word, ...]
    rules: tuple[Rule, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a word of another file or another page."""
        for word in self.words:
            if word.ref.doc_sha256 != self.doc_sha256 or word.ref.page != self.number:
                raise ValueError(f"word {word.ref} does not belong to page {self.number}")


@dataclass(frozen=True, slots=True)
class Document:
    """The extracted pages of one publisher file.

    Attributes
    ----------
    sha256 : str
        The sha256 of the publisher file.
    pages : tuple[Page, ...]
        The extracted pages in ascending order. They need not be contiguous.
    """

    sha256: str
    pages: tuple[Page, ...]

    def page(self, number: int) -> Page:
        """Return the page with this number.

        Parameters
        ----------
        number : int
            The 1-based page number in the publisher file.

        Returns
        -------
        Page
            The extracted page.

        Raises
        ------
        KeyError
            When the document holds no page with this number.
        """
        for page in self.pages:
            if page.number == number:
                return page
        raise KeyError(number)
