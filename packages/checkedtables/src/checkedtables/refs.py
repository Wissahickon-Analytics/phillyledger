from collections.abc import Iterable
from dataclasses import dataclass


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
        """Refuse an inverted box."""
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

        Returns
        -------
        bool
            True when every edge of `other` is within `slack` of this box or inside it.
        """
        return (
            self.x0 - slack <= other.x0
            and other.x1 <= self.x1 + slack
            and self.top - slack <= other.top
            and other.bottom <= self.bottom + slack
        )


@dataclass(frozen=True, slots=True)
class WordRef:
    """The file, page and extraction place of one word.

    Refs sort by `doc_sha256`, `page`, `index` and `child`, and a ref with no `child` sorts
    before every child of the same word.

    Attributes
    ----------
    doc_sha256 : str
        The sha256 of the publisher file.
    page : int
        The 1-based page in the publisher file, never in a cut file.
    index : int
        The extraction order on that page. It is evidence, never a record key.
    child : int or None
        Set when `split_numeric_runs` made this word from a longer one, whose box this word's
        box approximates.
    """

    doc_sha256: str
    page: int
    index: int
    child: int | None = None

    def _order(self) -> tuple[str, int, int, tuple[int, ...]]:
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
