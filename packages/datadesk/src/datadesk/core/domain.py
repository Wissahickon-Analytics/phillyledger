"""The archive's identities: editions, the versions of their files, and the index."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from checkedtables.refs import Sha256
from checkedtables.table import Finding, Severity


class Stage(StrEnum):
    """Which budget an edition belongs to: proposed, adopted, or NONE for a series without one."""

    NONE = "none"
    ADOPTED = "adopted"
    PROPOSED = "proposed"


@dataclass(frozen=True, slots=True, order=True)
class Period:
    """A span of days from `start` to `end`, both included, such as an edition's quarter."""

    start: date
    end: date

    def __post_init__(self) -> None:
        """Raise ValueError when the period ends before it starts."""
        if self.start > self.end:
            raise ValueError(f"period ends before it starts: {self}")

    def holds(self, day: date) -> bool:
        """Whether `day` falls in the period, both ends included."""
        return self.start <= day <= self.end


@dataclass(frozen=True, slots=True, order=True)
class EditionKey:
    """One edition of a series: the period it reports and its budget stage.

    A QCMR edition's period runs from the first day of its fiscal quarter to the date that the
    listing's title gives, so FY2026 Q4 is 2026-04-01 to 2026-06-30. The period that the cover
    prints is `DocumentVersion.printed_period`. At fetch the two are equal unless a
    PRINTED_PERIOD note confirms another period that the cover prints (`confirm_period`).
    """

    series: str
    period: Period
    stage: Stage = Stage.NONE

    def id(self) -> str:
        """Name the edition by series, period end and stage, as "qcmr:2023-06-30:none".

        The id leaves out the period's start, so the index file writes the whole key instead.
        """
        return f"{self.series}:{self.period.end.isoformat()}:{self.stage}"


class Via(StrEnum):
    """How the archive got a file: from the publisher's listing, a Wayback capture, or by hand."""

    PUBLISHER = "publisher"
    WAYBACK = "wayback"
    MANUAL = "manual"


class Holding(StrEnum):
    """Whether the archive holds the publisher's whole file or a section cut from it by hand."""

    WHOLE = "whole"
    EXCERPT = "excerpt"


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    """One version of an edition's file, as one line of the archive index.

    Attributes
    ----------
    sha256
        The sha256 of the file's bytes.
    listed_at
        A stamp that sorts in listing order. For a document-finder listing it is the 14-digit
        upload stamp in the URL's path, the latest of the stamps at which each of `urls` joined
        the line.
    urls
        Every URL that served these bytes, on the canonical host.
    title
        The listing's title for the file, as printed.
    printed_period
        The period that page 1 prints, as `confirm_period` confirmed it at fetch.
    supersedes
        The sha256 of the version of the same edition that this one replaces, or None for the
        first. Its listed_at may equal this one's, when new bytes sit behind an unchanged URL.
    """

    sha256: Sha256
    edition: EditionKey
    listed_at: str
    urls: tuple[str, ...]
    title: str
    printed_period: Period | None
    supersedes: Sha256 | None
    via: Via = Via.PUBLISHER
    holding: Holding = Holding.WHOLE


@dataclass(frozen=True, slots=True)
class ArchiveIndex:
    """Every archived version, sorted by edition, listed_at and sha256.

    Building one whose versions break a rule of `index_problem` raises ValueError.
    """

    versions: tuple[DocumentVersion, ...]

    def __post_init__(self) -> None:
        """Raise ValueError with the message of the rule `index_problem` finds broken."""
        if problem := index_problem(self.versions):
            raise ValueError(problem.message)

    def current(self, edition: EditionKey) -> DocumentVersion | None:
        """Return the edition's version that no other version supersedes, or None."""
        return next((head for head in _heads(self.versions) if head.edition == edition), None)

    def by_sha(self, sha: Sha256) -> DocumentVersion | None:
        """Return the version whose bytes have this sha256, or None."""
        return next((version for version in self.versions if version.sha256 == sha), None)


def sort_versions(versions: Iterable[DocumentVersion]) -> tuple[DocumentVersion, ...]:
    """Sort versions in index order: by edition, then listed_at, then sha256."""
    return tuple(sorted(versions, key=lambda v: (v.edition, v.listed_at, v.sha256)))


def index_problem(versions: tuple[DocumentVersion, ...]) -> Finding | None:
    """Return the first rule of the index that the versions break, or None.

    Each rule broken is a BLOCK finding with its code. The versions are sorted as `sort_versions`
    sorts them (versions_out_of_order). A sha sits on one line (content_alias). `supersedes` names
    a version of the same edition (supersedes_outside_edition). One version of each edition is
    superseded by nothing (two_current_versions). Following `supersedes` from that version reaches
    every version of its edition once and then ends, so a version that supersedes itself, or a
    cycle of versions, is refused (broken_chain).
    """
    if versions != sort_versions(versions):
        return _block("versions_out_of_order", "index", "not sorted by edition, listed_at, sha256")
    editions: dict[Sha256, EditionKey] = {}
    for version in versions:
        if held := editions.get(version.sha256):
            message = f"{version.sha256} is indexed under {held.id()} and {version.edition.id()}"
            return _block("content_alias", version.sha256, message)
        editions[version.sha256] = version.edition
    for version in versions:
        if version.supersedes is not None and editions.get(version.supersedes) != version.edition:
            message = f"{version.sha256} supersedes {version.supersedes}, not of its edition"
            return _block("supersedes_outside_edition", version.sha256, message)
    heads = _heads(versions)
    for edition, count in Counter(head.edition for head in heads).items():
        if count > 1:
            message = f"{edition.id()} has {count} versions that nothing supersedes"
            return _block("two_current_versions", edition.id(), message)
    current = {head.edition: head.sha256 for head in heads}
    older = {version.sha256: version.supersedes for version in versions}
    for edition, size in Counter(version.edition for version in versions).items():
        chain: list[Sha256] = []
        sha = current.get(edition)
        while sha is not None and sha not in chain:
            chain.append(sha)
            sha = older[sha]
        if sha is not None or len(chain) != size:
            message = f"{edition.id()} has {size} versions that do not form one chain"
            return _block("broken_chain", edition.id(), message)
    return None


def _heads(versions: tuple[DocumentVersion, ...]) -> list[DocumentVersion]:
    superseded = {version.supersedes for version in versions}
    return [version for version in versions if version.sha256 not in superseded]


def _block(code: str, subject: str, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message)
