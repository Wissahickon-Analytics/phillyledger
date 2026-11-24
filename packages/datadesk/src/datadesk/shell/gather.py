from dataclasses import dataclass
from pathlib import Path

from checkedtables.table import Finding, Severity
from datadesk.core.catalog import SourceCatalog, load_catalog
from datadesk.core.domain import ArchiveIndex
from datadesk.core.fetch import INDEX_PATH
from datadesk.core.index import parse_index

CATALOG_PATH = "packages/datadesk/src/datadesk/data/catalog.toml"


@dataclass(frozen=True, slots=True)
class RepoSnapshot:
    catalog: SourceCatalog
    index: ArchiveIndex


def gather_repo(root: Path) -> RepoSnapshot | tuple[Finding, ...]:
    catalog = load_catalog((root / CATALOG_PATH).read_text(encoding="utf-8"))
    index = _read_index((root / INDEX_PATH).read_text(encoding="utf-8"))
    match catalog, index:
        case SourceCatalog(), ArchiveIndex():
            return RepoSnapshot(catalog, index)
        case SourceCatalog(), Finding():
            return (index,)
        case tuple(), Finding():
            return (*catalog, index)
        case tuple(), ArchiveIndex():
            return catalog


def _read_index(text: str) -> ArchiveIndex | Finding:
    try:
        return parse_index(text)
    except (KeyError, TypeError, ValueError) as error:
        message = f"{type(error).__name__}: {error}"
        return Finding(Severity.BLOCK, "index_unreadable", INDEX_PATH, message)
