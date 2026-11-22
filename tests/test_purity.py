import ast
import importlib.util
from pathlib import Path

PURE_PACKAGES = ("checkedtables", "datadesk.core")
CALLED_BUILTINS = frozenset({"open", "print", "input", "__import__"})
CLOCK_METHODS = frozenset({"now", "today"})
READ_MODULES = frozenset({"os", "time", "builtins"})
IMPORTED_MODULES = frozenset({"random", "builtins"})
MUTABLE_DISPLAYS = (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)
MUTABLE_CONSTRUCTORS = frozenset({"list", "dict", "set", "bytearray"})
BANNED_FORMS = (
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
)
ALLOWED_FORMS = (
    'NAMES = ("a", "b")',
    'LOOKUP = MappingProxyType({"a": 1})',
    "def collect():\n    items = []\n    return items\n",
)


def package_sources(name: str) -> list[Path]:
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.submodule_search_locations, name
    return sorted(
        path for folder in spec.submodule_search_locations for path in Path(folder).rglob("*.py")
    )


def effect(node: ast.expr | ast.stmt) -> str | None:
    match node:
        case ast.Call(func=ast.Name(id=name)) if name in CALLED_BUILTINS:
            return f"{name}()"
        case ast.Call(func=ast.Attribute(attr=name)) if name in CLOCK_METHODS:
            return f".{name}()"
        case ast.Attribute(value=ast.Name(id=module), attr=name) if module in READ_MODULES:
            return f"{module}.{name}"
        case ast.Name(id="random"):
            return "random"
        case ast.Import(names=aliases):
            banned = ", ".join(alias.name for alias in aliases if alias.name in IMPORTED_MODULES)
            return f"import {banned}" if banned else None
        case ast.ImportFrom(module=module) if module in IMPORTED_MODULES:
            return f"from {module} import"
    return None


def is_mutable(value: ast.expr | None) -> bool:
    match value:
        case ast.Call(func=ast.Name(id=name)):
            return name in MUTABLE_CONSTRUCTORS
    return isinstance(value, MUTABLE_DISPLAYS)


def impurities(tree: ast.Module) -> list[tuple[int, str]]:
    nodes = (node for node in ast.walk(tree) if isinstance(node, ast.expr | ast.stmt))
    effects = [(node.lineno, found) for node in nodes if (found := effect(node))]
    state = [
        (statement.lineno, "mutable module state")
        for statement in tree.body
        if isinstance(statement, ast.Assign | ast.AnnAssign) and is_mutable(statement.value)
    ]
    return sorted(effects + state)


def test_pure_packages_have_no_effects() -> None:
    hits = [
        f"{path}:{line} {found}"
        for name in PURE_PACKAGES
        for path in package_sources(name)
        for line, found in impurities(ast.parse(path.read_text(), filename=str(path)))
    ]
    assert not hits, "\n".join(hits)


def test_scan_reports_each_banned_form() -> None:
    for source in BANNED_FORMS:
        lines = [line for line, _ in impurities(ast.parse(f"\n{source}"))]
        assert lines == [2], source


def test_scan_allows_immutable_constants() -> None:
    for source in ALLOWED_FORMS:
        assert impurities(ast.parse(source)) == [], source
