from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from checkedtables.table import Finding, Severity


class Stage(StrEnum):
    NONE = "none"
    ADOPTED = "adopted"
    PROPOSED = "proposed"


@dataclass(frozen=True, slots=True, order=True)
class Period:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(f"period ends before it starts: {self}")

    def holds(self, day: date) -> bool:
        return self.start <= day <= self.end


@dataclass(frozen=True, slots=True, order=True)
class EditionKey:
    series: str
    period: Period
    stage: Stage = Stage.NONE

    def id(self) -> str:
        return f"{self.series}:{self.period.end.isoformat()}:{self.stage}"


class Via(StrEnum):
    PUBLISHER = "publisher"
    WAYBACK = "wayback"
    MANUAL = "manual"


class Holding(StrEnum):
    WHOLE = "whole"
    EXCERPT = "excerpt"


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    sha256: str
    edition: EditionKey
    listed_at: str
    urls: tuple[str, ...]
    title: str
    printed_period: Period | None
    supersedes: str | None
    via: Via = Via.PUBLISHER
    holding: Holding = Holding.WHOLE


@dataclass(frozen=True, slots=True)
class ArchiveIndex:
    versions: tuple[DocumentVersion, ...]

    def __post_init__(self) -> None:
        if problem := index_problem(self.versions):
            raise ValueError(problem.message)

    def current(self, edition: EditionKey) -> DocumentVersion | None:
        return next((head for head in _heads(self.versions) if head.edition == edition), None)

    def by_sha(self, sha: str) -> DocumentVersion | None:
        return next((version for version in self.versions if version.sha256 == sha), None)


def sort_versions(versions: Iterable[DocumentVersion]) -> tuple[DocumentVersion, ...]:
    return tuple(sorted(versions, key=lambda v: (v.edition, v.listed_at, v.sha256)))


def index_problem(versions: tuple[DocumentVersion, ...]) -> Finding | None:
    if versions != sort_versions(versions):
        return _block("versions_out_of_order", "index", "not sorted by edition, listed_at, sha256")
    editions: dict[str, EditionKey] = {}
    for version in versions:
        if held := editions.get(version.sha256):
            message = f"{version.sha256} is indexed under {held.id()} and {version.edition.id()}"
            return _block("content_alias", version.sha256, message)
        editions[version.sha256] = version.edition
    for version in versions:
        if version.supersedes is not None and editions.get(version.supersedes) != version.edition:
            message = f"{version.sha256} supersedes {version.supersedes}, not of its edition"
            return _block("supersedes_outside_edition", version.sha256, message)
    for edition, count in Counter(head.edition for head in _heads(versions)).items():
        if count > 1:
            message = f"{edition.id()} has {count} versions that nothing supersedes"
            return _block("two_current_versions", edition.id(), message)
    return None


def _heads(versions: tuple[DocumentVersion, ...]) -> list[DocumentVersion]:
    superseded = {version.supersedes for version in versions}
    return [version for version in versions if version.sha256 not in superseded]


def _block(code: str, subject: str, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, subject, message)
