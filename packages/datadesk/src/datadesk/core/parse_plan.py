"""The word key and the word job: which pages of a file to read, and where the words are cached.

`ParseJob`, `ParsePlan`, `plan_parse` and `plan_ocr` join at the steps that have tables and OCR.
"""

from dataclasses import dataclass
from hashlib import sha256
from json import dumps
from re import compile

from checkedtables.kinds import SourceKind
from checkedtables.refs import Sha256
from datadesk.core.codec import FORMAT

_WORD_KEY = compile(r"[0-9a-f]{64}")


class WordKey(str):
    """The key of one entry in the word cache, as the 64 lowercase hex characters of a sha256.

    It is not a `Sha256`: it hashes the inputs that decide a page's words, not one file's
    bytes. It equals its text, so a file name or a dictionary key takes it as text. The
    constructor is the one builder, and it checks the rule.

    Raises
    ------
    ValueError
        When the value is not a `str` of 64 lowercase hex characters.
    """

    __slots__ = ()

    def __new__(cls, text: str) -> "WordKey":  # noqa: PYI034
        """Build the key from the 64 characters the check matched, never from `str(text)`."""
        checked = _WORD_KEY.fullmatch(text) if isinstance(text, str) else None
        if checked is None:
            raise ValueError(f"word key {text!r} is not 64 lowercase hex characters")
        return super().__new__(cls, checked.group())

    def __repr__(self) -> str:
        """Return the expression that rebuilds this key, such as ``WordKey('7c4a...')``."""
        return f"WordKey({super().__repr__()})"


def word_key(doc_sha256: Sha256, pages: tuple[int, ...], tool: str) -> WordKey:
    """Return the key under which the word cache keeps these pages of a file, as read by `tool`.

    The key is the sha256 of the JSON list of the codec's `FORMAT`, the file's sha, the pages
    and the tool string, written with no spaces. A change to any of the four gives another key,
    so the cache never serves words of another file, page set, extractor or byte layout.

    Parameters
    ----------
    pages : tuple[int, ...]
        The 1-based pages asked for, as the word job holds them. Empty means every page.
    tool : str
        The extractor and its settings, as `WordSource.tool` gives them.
    """
    text = dumps([FORMAT, doc_sha256, list(pages), tool], separators=(",", ":"))
    return WordKey(sha256(text.encode("utf-8")).hexdigest())


@dataclass(frozen=True, slots=True)
class WordJob:
    """The pages of one file to read with one source, and the cache entry that holds them.

    Attributes
    ----------
    doc_sha256 : Sha256
        The sha256 of the publisher file.
    pages : tuple[int, ...]
        The 1-based pages, strictly ascending. Empty means every page.
    source : SourceKind
        The source that reads the pages.
    compare : SourceKind or None
        A second source to read the same pages with, for `compare_sources`.
    cache_key : WordKey
        The key of the cache entry that holds the words.

    Raises
    ------
    ValueError
        When a page is below 1, or the pages are not strictly ascending, as when one is asked
        for twice.
    """

    doc_sha256: Sha256
    pages: tuple[int, ...]
    source: SourceKind
    compare: SourceKind | None
    cache_key: WordKey

    def __post_init__(self) -> None:
        """Refuse a page below 1 and pages that are not strictly ascending."""
        if any(page < 1 for page in self.pages):
            raise ValueError(f"a word job asks for a page below 1: {self.pages}")
        if list(self.pages) != sorted(set(self.pages)):
            raise ValueError(f"a word job's pages are not strictly ascending: {self.pages}")
