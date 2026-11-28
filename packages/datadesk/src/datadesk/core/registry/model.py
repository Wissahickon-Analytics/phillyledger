"""The registry's types: entities with dated names, table-scoped aliases, and relations.

A department, fund or tax spelling lives only here, as an official name with fiscal years or as
an alias that names its tables (design section 7.2). A row schema that names an entity carries
no labels, and `schema_for` fills them from the registry.
"""

from dataclasses import dataclass
from enum import StrEnum

from checkedtables.refs import Sha256


class EntityKind(StrEnum):
    """What an entity is. Each member names the TOML array of tables that holds its kind.

    Attributes
    ----------
    GROUP
        A scope that a table prints as one row and the City runs as several entities, such as
        Streets with Sanitation in Table P-1 through FY2025 (QPOS-Q12). Its `members` name them.
    """

    DEPARTMENT = "department"
    FUND = "fund"
    CLASS = "class"
    TAX = "tax"
    GROUP = "group"


@dataclass(frozen=True, slots=True)
class Dated:
    """A value that holds in a span of fiscal years, such as a name the City used for a time.

    Attributes
    ----------
    value : str
        The value, such as a name as the pages print it.
    first_fy, last_fy : int or None
        The first and the last fiscal year it holds in, both included. None leaves that end
        open. A name's span is whole fiscal years, so a spelling that changes inside a year is
        an alias with the shas of its editions.
    """

    value: str
    first_fy: int | None
    last_fy: int | None


class Residual(StrEnum):
    """Whether an entity is the rest of a split, such as the Other fund beside the General."""

    NO = "no"
    YES = "yes"


@dataclass(frozen=True, slots=True)
class Entity:
    """One department, fund, class, tax or group.

    Attributes
    ----------
    id : str
        The id that row keys and release rows name, such as "phl_dept_police". A department
        keeps the id of the old repo's ``config/entities.yml``.
    names : tuple[Dated, ...]
        Its official names, each with its fiscal years. A group has none: no page names it,
        and a table that prints it as a row reaches it through an alias.
    codes : tuple[Dated, ...]
        Its printed codes, such as department numbers, each with its fiscal years.
    parents : tuple[Dated, ...]
        The id of the entity it sits under, with the fiscal years it did (QOBL-Q15).
    members : tuple[str, ...]
        For a group, the ids of the entities it covers.
    """

    id: str
    kind: EntityKind
    names: tuple[Dated, ...]
    codes: tuple[Dated, ...] = ()
    parents: tuple[Dated, ...] = ()
    members: tuple[str, ...] = ()
    residual: Residual = Residual.NO


class RelationKind(StrEnum):
    """How one entity's figures relate to another's over a span of fiscal years."""

    MERGED_INTO = "merged_into"
    SPLIT_FROM = "split_from"
    REPORTED_UNDER = "reported_under"


@dataclass(frozen=True, slots=True)
class Relation:
    """A dated link from one entity to another, such as a department merged into another.

    Attributes
    ----------
    source, target : str
        The ids of the two entities.
    first_fy, last_fy : int, int or None
        The fiscal years the relation holds in. None leaves the last year open.
    fund : str or None
        The id of the one fund the relation holds in, or None for every fund.
    evidence : str
        Where the pages say so, such as a footnote and its edition.
    """

    kind: RelationKind
    source: str
    target: str
    first_fy: int
    last_fy: int | None
    fund: str | None
    evidence: str


@dataclass(frozen=True, slots=True)
class Alias:
    """A spelling of an entity that holds in some tables only, such as OCR damage on one file.

    Attributes
    ----------
    entity : str
        The id of the entity it spells.
    label : str
        The spelling, as the pages print it.
    tables : tuple[str, ...]
        The tables it holds in. Never empty, so no alias holds everywhere.
    first_fy, last_fy : int or None
        The fiscal years it holds in, both included. None leaves that end open.
    editions : tuple[Sha256, ...]
        The files it holds in. Empty holds in every file of its tables and years. A misprint
        or a spelling that changes inside a fiscal year names its files (QPOS-Q09).

    Raises
    ------
    ValueError
        When `tables` is empty.
    """

    entity: str
    label: str
    tables: tuple[str, ...]
    first_fy: int | None
    last_fy: int | None
    editions: tuple[Sha256, ...] = ()

    def __post_init__(self) -> None:
        """Refuse an alias that names no table."""
        if not self.tables:
            raise ValueError(f"the alias {self.label!r} of {self.entity} names no table")


@dataclass(frozen=True, slots=True)
class Registry:
    """Every entity, relation and alias of the registry's files."""

    entities: tuple[Entity, ...]
    relations: tuple[Relation, ...]
    aliases: tuple[Alias, ...]


@dataclass(frozen=True, slots=True)
class LookupScope:
    """Where a label is read: the table, the fiscal year of the edition, and its file.

    Attributes
    ----------
    fiscal_year : int
        The fiscal year of the edition's period end, so FY2026 for an edition of 2025-09-30.
    edition : Sha256
        The sha of the edition's file, which an alias with `editions` must name.
    """

    table: str
    fiscal_year: int
    edition: Sha256
