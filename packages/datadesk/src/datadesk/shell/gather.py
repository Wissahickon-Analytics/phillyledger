"""Read the checkout's files once, and hand their text to the pure loaders."""

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
    """What a command reads from the checkout: the source catalog and the archive index."""

    catalog: SourceCatalog
    index: ArchiveIndex


def gather_repo(root: Path) -> RepoSnapshot | tuple[Finding, ...]:
    """Read the catalog and the index from the checkout at `root`.

    Every problem comes back as a BLOCK finding: catalog_unreadable or index_unreadable for a
    file that cannot be read or is not UTF-8, each finding of `load_catalog`, and
    index_unreadable for an index that `parse_index` refuses.
    """
    catalog_text = _read(root, CATALOG_PATH, "catalog_unreadable")
    index_text = _read(root, INDEX_PATH, "index_unreadable")
    catalog = load_catalog(catalog_text) if isinstance(catalog_text, str) else (catalog_text,)
    index = _read_index(index_text) if isinstance(index_text, str) else index_text
    match catalog, index:
        case SourceCatalog(), ArchiveIndex():
            return RepoSnapshot(catalog, index)
        case SourceCatalog(), Finding():
            return (index,)
        case tuple(), Finding():
            return (*catalog, index)
        case tuple(), ArchiveIndex():
            return catalog


def _read(root: Path, path: str, code: str) -> str | Finding:
    try:
        return (root / path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return _unreadable(code, path, error)


def _read_index(text: str) -> ArchiveIndex | Finding:
    try:
        return parse_index(text)
    except (KeyError, TypeError, ValueError) as error:
        return _unreadable("index_unreadable", INDEX_PATH, error)


def _unreadable(code: str, path: str, error: Exception) -> Finding:
    return Finding(Severity.BLOCK, code, path, f"{type(error).__name__}: {error}")
