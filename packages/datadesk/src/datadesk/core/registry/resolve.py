"""Find the spellings that the registry allows for an entity in one table, year and file.

Step 5 builds `labels_for` alone. `resolve`, `resolve_fund` and `normalize_printed_code` join
with the first grammar table, at step 8 (design section 15).
"""

from datadesk.core.registry.model import LookupScope, Registry


def labels_for(reg: Registry, entity: str, scope: LookupScope) -> tuple[str, ...]:
    """Return every spelling that the registry allows for an entity where `scope` reads it.

    Parameters
    ----------
    reg : Registry
        The registry.
    entity : str
        The entity's id.
    scope : LookupScope
        The table, the fiscal year and the file.

    Returns
    -------
    tuple[str, ...]
        The entity's official names whose fiscal years hold the year, in registry order, then
        each alias of the entity whose tables hold the table, whose fiscal years hold the year
        and whose editions, when it names any, hold the file. Each spelling once. Empty for an
        id that the registry lacks.
    """
    names = (
        name.value
        for found in reg.entities
        if found.id == entity
        for name in found.names
        if _holds(name.first_fy, name.last_fy, scope.fiscal_year)
    )
    aliases = (
        alias.label
        for alias in reg.aliases
        if alias.entity == entity
        and scope.table in alias.tables
        and _holds(alias.first_fy, alias.last_fy, scope.fiscal_year)
        and (not alias.editions or scope.edition in alias.editions)
    )
    return tuple(dict.fromkeys((*names, *aliases)))


def _holds(first_fy: int | None, last_fy: int | None, fiscal_year: int) -> bool:
    """Return whether a span of fiscal years, with None for an open end, holds the year."""
    return (first_fy is None or first_fy <= fiscal_year) and (
        last_fy is None or fiscal_year <= last_fy
    )
