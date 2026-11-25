"""Words, rules and pages, as one source read them from a publisher's file."""

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

    Raises
    ------
    ValueError
        When `confidence` is outside 0 to 100, or NaN.
    """

    ref: WordRef
    text: str
    box: Box
    bold: bool | None
    size: float | None
    confidence: float | None

    def __post_init__(self) -> None:
        """Refuse a confidence outside 0 to 100, NaN included."""
        if self.confidence is not None and not 0 <= self.confidence <= 100:
            raise ValueError(
                f"word {self.ref} has a confidence outside 0 to 100: {self.confidence}"
            )


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
        The sha256 of the publisher file. Never empty.
    number : int
        The 1-based page number in the publisher file.
    width, height : float
        The page size.
    rotation : int
        The page rotation in degrees.
    source : WordSource
        The tool that read every word on the page.
    words : tuple[Word, ...]
        The words, each from this file and page, each with its own ref, and none with an OCR
        confidence on a text layer page.
    rules : tuple[Rule, ...]
        The drawn lines.

    Raises
    ------
    ValueError
        When `doc_sha256` is empty, `number` is below 1, a word's ref names another file or
        another page, two words share a ref, or a word on a text layer page carries an OCR
        confidence.
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
        """Refuse an empty hash, a page below 1, and a word this page cannot hold."""
        if not self.doc_sha256:
            raise ValueError(f"page {self.number} names no file")
        if self.number < 1:
            raise ValueError(f"a page has a number below 1: {self.number}")
        seen: set[WordRef] = set()
        for word in self.words:
            if word.ref.doc_sha256 != self.doc_sha256 or word.ref.page != self.number:
                raise ValueError(f"word {word.ref} does not belong to page {self.number}")
            if word.ref in seen:
                raise ValueError(f"two words on page {self.number} share the ref {word.ref}")
            seen.add(word.ref)
            if self.source.kind is SourceKind.TEXT_LAYER and word.confidence is not None:
                raise ValueError(f"word {word.ref} has an OCR confidence on a text layer page")


@dataclass(frozen=True, slots=True)
class Document:
    """The extracted pages of one publisher file.

    Attributes
    ----------
    sha256 : str
        The sha256 of the publisher file. Never empty.
    pages : tuple[Page, ...]
        The extracted pages of this file, in strictly ascending order. They need not be
        contiguous.

    Raises
    ------
    ValueError
        When `sha256` is empty, a page is of another file, or the page numbers are not strictly
        ascending.
    """

    sha256: str
    pages: tuple[Page, ...]

    def __post_init__(self) -> None:
        """Refuse an empty hash, a page of another file, and pages out of ascending order."""
        if not self.sha256:
            raise ValueError("a document names no file")
        for page in self.pages:
            if page.doc_sha256 != self.sha256:
                raise ValueError(f"page {page.number} does not belong to document {self.sha256}")
        numbers = [page.number for page in self.pages]
        if numbers != sorted(set(numbers)):
            raise ValueError(f"page numbers are not strictly ascending: {numbers}")

    def page(self, number: int) -> Page:
        """Return the page with this number.

        Parameters
        ----------
        number : int
            The 1-based page number in the publisher file.

        Raises
        ------
        KeyError
            When the document holds no page with this number.
        """
        for page in self.pages:
            if page.number == number:
                return page
        raise KeyError(number)
