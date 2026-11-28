import ast
import importlib.util
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import ModuleType

import pytest

PURE_PACKAGES = ("checkedtables", "datadesk.core")
PURE_IMPORTS: dict[str, tuple[str, ...]] = {
    "checkedtables": (
        "collections.abc.Callable",
        "collections.abc.Iterable",
        "collections.abc.Sequence",
        "dataclasses.dataclass",
        "dataclasses.replace",
        "datetime.date",
        "decimal.Decimal",
        "enum.StrEnum",
        "re.compile",
        "statistics.median",
        "typing.Self",
        "typing.TYPE_CHECKING",
        "typing.assert_never",
    ),
    "datadesk.core": (
        "collections.Counter",
        "collections.abc.Callable",
        "collections.abc.Iterable",
        "collections.abc.Sequence",
        "dataclasses.asdict",
        "dataclasses.dataclass",
        "dataclasses.replace",
        "datetime.date",
        "datetime.timedelta",
        "decimal.Decimal",
        "enum.StrEnum",
        "hashlib.sha256",
        "json.dumps",
        "json.loads",
        "re.compile",
        "re.escape",
        "tomllib.TOMLDecodeError",
        "tomllib.loads",
        "types.MappingProxyType",
        "typing.Any",
        "typing.Never",
        "typing.assert_never",
    ),
}
INSIDE = {
    "checkedtables": ("checkedtables",),
    "datadesk.core": ("datadesk.core", "checkedtables"),
}
BANNED_CALLS = frozenset({"open", "print", "input", "__import__"})
BANNED_METHOD_CALLS = frozenset({"now", "today"})
BANNED_READS_ON = frozenset({"os", "time", "builtins"})
BANNED_NAMES = frozenset({"random"})
MUTABLE_DISPLAYS = (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)
MUTABLE_CONSTRUCTORS = frozenset({"list", "dict", "set", "bytearray"})
NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
KIT_MODULE = "checkedtables.words"
CORE_MODULE = "datadesk.core.tables.birt"
BANNED_FORMS = {
    KIT_MODULE: (
        'open("x")',
        "print(1)",
        "input()",
        "datetime.now()",
        "date.today()",
        "os.getcwd()",
        "import random",
        "from random import choice",
        "random.random()",
        "time.time()",
        "import builtins",
        "from builtins import open",
        'builtins.open("x")',
        '__import__("boto3")',
        "CACHE: dict[str, str] = {}",
        "ITEMS = []",
        "SEEN = set()",
        "CACHE, SEEN = {}, set()",
        "if __debug__:\n    CACHE = {}",
        "try:\n    pass\nexcept ImportError:\n    CACHE = {}",
        "match __name__:\n    case _:\n        CACHE = {}",
        "with suppress():\n    for _ in ():\n        while __debug__:\n            CACHE = {}",
        "import sys",
        "import os.path as p",
        "import dataclasses",
        "from io import FileIO",
        "from collections import defaultdict",
        "from dataclasses import sys",
        "from re import *",
        "def make():\n    from uuid import uuid4",
        "if TYPE_CHECKING:\n    from pathlib import Path",
        "from . import refs",
        '__package__ = "email.mime"\nfrom . import text',
    ),
    CORE_MODULE: (
        "from . import catalog",
        "from ... import core",
        "from ... import shell",
        "from ...shell import run",
        "from datadesk import shell",
        "import datadesk.core.tables",
    ),
}
ALLOWED_FORMS = {
    KIT_MODULE: (
        'NAMES = ("a", "b")',
        'LOOKUP = MappingProxyType({"a": 1})',
        "def collect():\n    items = []\n    return items\n",
        "if __debug__:\n    def collect():\n        items = []\n        return items\n",
        "from checkedtables.refs import Box",
        "import checkedtables.lines",
        "from checkedtables.lines import *",
    ),
    CORE_MODULE: (
        "from checkedtables.refs import Box",
        "import datadesk.core.tables as tables",
        "from datadesk import core",
    ),
}
GBK_FILE_HIDING_IMPORT = b'# coding: gbk\nX = "\xe3\x81\x81\\"; import sys #\'"\n'


def package_sources(name: str) -> list[tuple[str, Path]]:
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.submodule_search_locations, name
    return sorted(
        (".".join((name, *path.relative_to(folder).with_suffix("").parts)), path)
        for folder in map(Path, spec.submodule_search_locations)
        for path in folder.rglob("*.py")
    )


def parse_file(path: Path) -> ast.Module:
    return ast.parse(path.read_bytes(), filename=str(path))


def pure_package(module: str) -> str:
    (package,) = (name for name in PURE_PACKAGES if is_at_or_under(module, name))
    return package


def is_at_or_under(name: str, root: str) -> bool:
    return name == root or name.startswith(f"{root}.")


def is_inside(name: str, package: str) -> bool:
    return any(is_at_or_under(name, root) for root in INSIDE[package])


def bound_module(alias: ast.alias) -> str:
    return alias.name if alias.asname else alias.name.partition(".")[0]


def outside_imports(tree: ast.Module, module: str) -> list[tuple[int, str]]:
    package = pure_package(module)
    pairs = (
        (node.lineno, f"{node.module}.{alias.name}")
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and not node.level
        for alias in node.names
    )
    return [(line, pair) for line, pair in pairs if not is_inside(pair, package)]


def module_valued(pairs: Iterable[str]) -> list[str]:
    return [pair for pair in pairs if not names_a_value(pair)]


def names_a_value(pair: str) -> bool:
    owner, _, name = pair.rpartition(".")
    if name == "*":
        return False
    try:
        value = getattr(importlib.import_module(owner), name)
    except (ImportError, AttributeError):
        return False
    return not isinstance(value, ModuleType)


def effect(node: ast.expr | ast.stmt, package: str) -> str | None:
    match node:
        case ast.Call(func=ast.Name(id=name)) if name in BANNED_CALLS:
            return f"{name}()"
        case ast.Call(func=ast.Attribute(attr=name)) if name in BANNED_METHOD_CALLS:
            return f".{name}()"
        case ast.Attribute(value=ast.Name(id=owner), attr=name) if owner in BANNED_READS_ON:
            return f"{owner}.{name}"
        case ast.Name(id=name) if name in BANNED_NAMES:
            return name
        case ast.ImportFrom(level=level, module=name) if level:
            return f"relative import from {'.' * level}{name or ''}"
        case ast.Import(names=aliases):
            names = (alias.name for alias in aliases if not is_inside(bound_module(alias), package))
            outside = ", ".join(names)
            return f"import {outside}" if outside else None
    return None


def is_mutable(value: ast.expr | None) -> bool:
    match value:
        case ast.Call(func=ast.Name(id=name)):
            return name in MUTABLE_CONSTRUCTORS
        case ast.Tuple(elts=elements):
            return any(is_mutable(element) for element in elements)
    return isinstance(value, MUTABLE_DISPLAYS)


def module_scope(node: ast.AST) -> Iterator[ast.AST]:
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, NESTED_SCOPES):
            yield child
            yield from module_scope(child)


def impurities(tree: ast.Module, module: str) -> list[tuple[int, str]]:
    package = pure_package(module)
    nodes = (node for node in ast.walk(tree) if isinstance(node, ast.expr | ast.stmt))
    effects = [(node.lineno, found) for node in nodes if (found := effect(node, package))]
    unpinned = [
        (line, "from {} import {}".format(*pair.rsplit(".", 1)))
        for line, pair in outside_imports(tree, module)
        if pair.endswith(".*") or pair not in PURE_IMPORTS[package]
    ]
    state = [
        (statement.lineno, "mutable module state")
        for statement in module_scope(tree)
        if isinstance(statement, ast.Assign | ast.AnnAssign) and is_mutable(statement.value)
    ]
    return sorted(effects + unpinned + state)


def test_pure_packages_have_no_effects() -> None:
    hits = [
        f"{path}:{line} {found}"
        for name in PURE_PACKAGES
        for module, path in package_sources(name)
        for line, found in impurities(parse_file(path), module)
    ]
    assert not hits, "\n".join(hits)


def test_pure_imports_are_pinned() -> None:
    for name in PURE_PACKAGES:
        pairs = {
            pair
            for module, path in package_sources(name)
            for _, pair in outside_imports(parse_file(path), module)
        }
        assert tuple(sorted(pairs)) == PURE_IMPORTS[name], name


def test_scan_reads_a_file_as_the_importer_does(tmp_path: Path) -> None:
    path = tmp_path / "words.py"
    path.write_bytes(GBK_FILE_HIDING_IMPORT)
    assert impurities(ast.parse(GBK_FILE_HIDING_IMPORT.decode()), KIT_MODULE) == []
    assert impurities(parse_file(path), KIT_MODULE) == [(2, "import sys")]


def test_pinned_imports_are_not_modules() -> None:
    probes = ("dataclasses.sys", "dataclasses.dataclass", "statistics.random", "re.no_such_name")
    assert module_valued(probes) == ["dataclasses.sys", "statistics.random", "re.no_such_name"]
    assert module_valued(pair for pairs in PURE_IMPORTS.values() for pair in pairs) == []


def test_star_import_from_outside_fails_whatever_the_pin_holds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answers_every_name = ModuleType("example_units")
    answers_every_name.__getattr__ = lambda name: None
    monkeypatch.setitem(sys.modules, answers_every_name.__name__, answers_every_name)
    monkeypatch.setitem(PURE_IMPORTS, "checkedtables", ("example_units.*",))
    star = "from example_units import *"
    assert impurities(ast.parse(star), KIT_MODULE) == [(1, star)]
    assert module_valued(PURE_IMPORTS["checkedtables"]) == ["example_units.*"]


def test_scan_passes_a_name_its_own_package_pins(monkeypatch: pytest.MonkeyPatch) -> None:
    tree = ast.parse("from decimal import Decimal")
    monkeypatch.setitem(PURE_IMPORTS, "checkedtables", ("decimal.Decimal",))
    assert impurities(tree, KIT_MODULE) == []
    monkeypatch.setitem(PURE_IMPORTS, "checkedtables", ())
    monkeypatch.setitem(PURE_IMPORTS, "datadesk.core", ("decimal.Decimal",))
    assert impurities(tree, KIT_MODULE) == [(1, "from decimal import Decimal")]


def test_scan_reports_each_banned_form() -> None:
    for module, sources in BANNED_FORMS.items():
        for source in sources:
            text = "\n".join(("NAMES = ()", source))
            last_line = len(text.splitlines())
            assert [line for line, _ in impurities(ast.parse(text), module)] == [last_line], source


def test_scan_allows_immutable_constants() -> None:
    for module, sources in ALLOWED_FORMS.items():
        for source in sources:
            assert impurities(ast.parse(source), module) == [], source
