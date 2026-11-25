"""Row keys, and the findings that come back beside a result."""

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True, order=True)
class RowKey:
    """The identity of a row, as named parts sorted by name.

    ``str`` prints each part as ``name=value`` and joins the parts with ``|``, and `parse` reads
    that text back.

    Attributes
    ----------
    parts : tuple[tuple[str, str], ...]
        The ``(name, value)`` parts, such as
        ``(("breakdown", "civilian"), ("dept", "phl_dept_police"))``.

    Raises
    ------
    ValueError
        When there are no parts, the names are not strictly ascending, a name is empty, or a
        name or value holds ``|`` or ``=``.
    """

    parts: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        """Refuse no parts, names that are empty or not strictly ascending, and a separator."""
        names = [name for name, _ in self.parts]
        if not names:
            raise ValueError("a row key needs at least one part")
        if names != sorted(set(names)):
            raise ValueError(f"row key names are not strictly ascending: {names}")
        if not all(names):
            raise ValueError(f"a row key name is empty: {self.parts}")
        if any(separator in text for part in self.parts for text in part for separator in "|="):
            raise ValueError(f"a row key part holds | or =: {self.parts}")

    def __str__(self) -> str:
        """Return the parts as ``name=value`` joined by ``|``."""
        return "|".join(f"{name}={value}" for name, value in self.parts)

    @staticmethod
    def of(**parts: str) -> "RowKey":
        """Return the key with these parts, sorted by name.

        Parameters
        ----------
        **parts : str
            The value of each part, by name.
        """
        return RowKey(tuple(sorted(parts.items())))

    @staticmethod
    def parse(text: str) -> "RowKey":
        """Read a key from the text that ``str`` prints.

        For a key held as text, such as one in a TOML record. Code builds a key with `of`.

        Parameters
        ----------
        text : str
            Parts as ``name=value``, joined by ``|``.

        Raises
        ------
        ValueError
            When a part has no ``=``, or the parts break a rule of the key.
        """
        pieces = [part.partition("=") for part in text.split("|")]
        if not all(separator for _, separator, _ in pieces):
            raise ValueError(f"a row key part has no =: {text!r}")
        return RowKey(tuple((name, value) for name, _, value in pieces))

    @property
    def has_occurrence(self) -> bool:
        """Whether the key has the ``occurrence`` part that a list table gives a repeated key."""
        return any(name == "occurrence" for name, _ in self.parts)


class Severity(StrEnum):
    """How a finding affects the gate. A BLOCK finding fails it, and a WARN finding is listed."""

    BLOCK = "block"
    WARN = "warn"


@dataclass(frozen=True, slots=True)
class Finding:
    """A problem in the documents, returned as a value beside the result.

    Findings sort by `severity`, `code`, `subject`, `message` and `page`, and a finding with no
    page sorts before every page.

    Attributes
    ----------
    severity : Severity
        Whether the finding blocks.
    code : str
        A stable code, such as "unknown_row", "style_unavailable" or "check_not_evaluated".
    subject : str
        What the finding is about, as ``"<doc sha8>:<table>:<row key or label>"``.
    message : str
        The finding in words.
    page : int or None
        The page the finding is on, when it has one.
    """

    severity: Severity
    code: str
    subject: str
    message: str
    page: int | None = None

    def _order(self) -> tuple[str, str, str, str, tuple[int, ...]]:
        page = () if self.page is None else (self.page,)
        return (self.severity, self.code, self.subject, self.message, page)

    def __lt__(self, other: object) -> bool:
        """Return whether this finding sorts before `other`."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() < other._order()

    def __le__(self, other: object) -> bool:
        """Return whether this finding sorts before `other` or equals it."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() <= other._order()

    def __gt__(self, other: object) -> bool:
        """Return whether this finding sorts after `other`."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() > other._order()

    def __ge__(self, other: object) -> bool:
        """Return whether this finding sorts after `other` or equals it."""
        if not isinstance(other, Finding):
            return NotImplemented
        return self._order() >= other._order()
