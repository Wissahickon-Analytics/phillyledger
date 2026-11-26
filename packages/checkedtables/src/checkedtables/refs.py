"""Boxes on a page, file hashes and word refs, which cells and checks import instead of words."""

from collections.abc import Iterable
from dataclasses import dataclass
from re import compile
from typing import Self

_SHA256 = compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class Box:
    """A rectangle on a page, with y growing down the page.

    Attributes
    ----------
    x0, x1 : float
        The left and right edges, with ``x0 <= x1``.
    top, bottom : float
        The top and bottom edges, with ``top <= bottom``.

    Raises
    ------
    ValueError
        When an edge pair is inverted or holds a NaN.
    """

    x0: float
    top: float
    x1: float
    bottom: float

    def __post_init__(self) -> None:
        """Refuse an inverted or NaN edge pair."""
        if not (self.x0 <= self.x1 and self.top <= self.bottom):
            raise ValueError(f"inverted box {self}")

    @staticmethod
    def around(boxes: Iterable["Box"]) -> "Box":
        """Return the smallest box that holds every box.

        Parameters
        ----------
        boxes : Iterable[Box]
            The boxes to hold, read once.

        Returns
        -------
        Box
            The box from the least `x0` and `top` to the greatest `x1` and `bottom`.

        Raises
        ------
        ValueError
            When `boxes` is empty.
        """
        members = tuple(boxes)
        if not members:
            raise ValueError("Box.around needs at least one box")
        return Box(
            min(box.x0 for box in members),
            min(box.top for box in members),
            max(box.x1 for box in members),
            max(box.bottom for box in members),
        )

    def contains(self, other: "Box", slack: float) -> bool:
        """Return whether `other` lies inside this box grown by `slack` on every side.

        Parameters
        ----------
        other : Box
            The box to test.
        slack : float
            How far `other` may reach past each edge of this box.
        """
        return (
            self.x0 - slack <= other.x0
            and other.x1 <= self.x1 + slack
            and self.top - slack <= other.top
            and other.bottom <= self.bottom + slack
        )


class Sha256(str):
    """The sha256 of a file's bytes, as the 64 lowercase hex characters `hexdigest()` writes.

    A `Sha256` equals its text, and a dictionary key, a path or JSON takes it as text. The
    constructor is the one builder, and it checks the rule. A slice of one is plain text.

    Raises
    ------
    ValueError
        When the value is not a `str` of 64 lowercase hex characters. A sha is never the
        publisher's data: code computes it from bytes or reads it from one of the repo's own
        files, so a bad one is a broken invariant, not a finding.
    """

    __slots__ = ()

    def __new__(cls, text: str) -> Self:
        """Build the hash from the 64 characters the check matched.

        It never reads `str(text)`, so a `str` subclass whose `__str__` gives other text, such
        as a member of a ``(str, Enum)`` class, still gives the text that was checked.
        """
        checked = _SHA256.fullmatch(text) if isinstance(text, str) else None
        if checked is None:
            raise ValueError(f"sha256 {text!r} is not 64 lowercase hex characters")
        return super().__new__(cls, checked.group())

    def __repr__(self) -> str:
        """Return the expression that rebuilds this hash, such as ``Sha256('7c4a...')``."""
        return f"Sha256({super().__repr__()})"


@dataclass(frozen=True, slots=True)
class WordRef:
    """The file, page and extraction place of one word.

    Refs sort by `doc_sha256`, `page`, `index` and `child`, and a ref with no `child` sorts
    before every child of the same word.

    Attributes
    ----------
    doc_sha256 : Sha256
        The sha256 of the publisher file.
    page : int
        The 1-based page in the publisher file, never in a cut file.
    index : int
        The extraction order on that page. It is evidence, never a record key.
    child : int or None
        Set when `split_numeric_runs` cut this word out of a longer one. Its box is then
        approximate.

    Raises
    ------
    ValueError
        When `doc_sha256` is not a `Sha256`, `page` is below 1, or `index` or `child` is below 0.
    """

    doc_sha256: Sha256
    page: int
    index: int
    child: int | None = None

    def __post_init__(self) -> None:
        """Refuse a hash that is not a `Sha256`, a page below 1, or an index or child below 0."""
        if not isinstance(self.doc_sha256, Sha256):
            raise ValueError(f"a word ref names its file by {self.doc_sha256!r}, not a Sha256")
        if self.page < 1:
            raise ValueError(f"a word ref has a page below 1: {self}")
        if self.index < 0:
            raise ValueError(f"a word ref has an index below 0: {self}")
        if self.child is not None and self.child < 0:
            raise ValueError(f"a word ref has a child below 0: {self}")

    def _order(self) -> tuple[Sha256, int, int, tuple[int, ...]]:
        return (self.doc_sha256, self.page, self.index, () if self.child is None else (self.child,))

    def __lt__(self, other: object) -> bool:
        """Return whether this ref sorts before `other`."""
        if not isinstance(other, WordRef):
            return NotImplemented
        return self._order() < other._order()

    def __le__(self, other: object) -> bool:
        """Return whether this ref sorts before `other` or equals it."""
        if not isinstance(other, WordRef):
            return NotImplemented
        return self._order() <= other._order()

    def __gt__(self, other: object) -> bool:
        """Return whether this ref sorts after `other`."""
        if not isinstance(other, WordRef):
            return NotImplemented
        return self._order() > other._order()

    def __ge__(self, other: object) -> bool:
        """Return whether this ref sorts after `other` or equals it."""
        if not isinstance(other, WordRef):
            return NotImplemented
        return self._order() >= other._order()
