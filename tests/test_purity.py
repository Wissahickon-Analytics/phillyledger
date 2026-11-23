import ast
import importlib.util
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import ModuleType

PURE_PACKAGES = ("checkedtables", "datadesk.core")
PURE_IMPORTS: dict[str, tuple[str, ...]] = {
    "checkedtables": ("collections.abc.Iterable", "dataclasses.dataclass"),
    "datadesk.core": (),
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
    ),
    CORE_MODULE: (
        "from ... import shell",
        "from ...shell import run",
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
        "from . import refs",
    ),
    CORE_MODULE: (
        "from . import catalog",
        "from checkedtables.refs import Box",
        "import datadesk.core.tables as tables",
    ),
}


def package_sources(name: str) -> list[tuple[str, Path]]:
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.submodule_search_locations, name
    return sorted(
        (".".join((name, *path.relative_to(folder).with_suffix("").parts)), path)
        for folder in map(Path, spec.submodule_search_locations)
        for path in folder.rglob("*.py")
    )


def pure_package(module: str) -> str:
    (package,) = (name for name in PURE_PACKAGES if is_at_or_under(module, name))
    return package


def is_at_or_under(name: str, root: str) -> bool:
    return name == root or name.startswith(f"{root}.")


def is_inside(name: str, package: str) -> bool:
    return any(is_at_or_under(name, root) for root in INSIDE[package])


def imported_module(node: ast.ImportFrom, module: str) -> str:
    relative = "." * node.level + (node.module or "")
    return importlib.util.resolve_name(relative, module.rpartition(".")[0])


def bound_module(alias: ast.alias) -> str:
    return alias.name if alias.asname else alias.name.partition(".")[0]


def outside_imports(tree: ast.Module, module: str) -> list[tuple[int, str]]:
    package = pure_package(module)
    sources = (
        (node, imported_module(node, module))
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    return [
        (node.lineno, f"{source}.{alias.name}")
        for node, source in sources
        if not is_inside(source, package)
        for alias in node.names
    ]


def module_valued(pairs: Iterable[str]) -> list[str]:
    found = []
    for pair in pairs:
        owner, _, name = pair.rpartition(".")
        try:
            value = getattr(importlib.import_module(owner), name)
        except (ImportError, AttributeError):
            found.append(pair)
        else:
            if isinstance(value, ModuleType):
                found.append(pair)
    return found


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
        if pair not in PURE_IMPORTS[package]
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
        for line, found in impurities(ast.parse(path.read_text(), filename=str(path)), module)
    ]
    assert not hits, "\n".join(hits)


def test_pure_imports_are_pinned() -> None:
    for name in PURE_PACKAGES:
        pairs = {
            pair
            for module, path in package_sources(name)
            for _, pair in outside_imports(ast.parse(path.read_text(), filename=str(path)), module)
        }
        assert tuple(sorted(pairs)) == PURE_IMPORTS[name], name


def test_pinned_imports_are_not_modules() -> None:
    probes = ("dataclasses.sys", "dataclasses.dataclass", "statistics.random", "re.no_such_name")
    assert module_valued(probes) == ["dataclasses.sys", "statistics.random", "re.no_such_name"]
    assert module_valued(pair for pairs in PURE_IMPORTS.values() for pair in pairs) == []


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
