import ast
import importlib.util
from collections.abc import Iterator
from pathlib import Path

PURE_PACKAGES = ("checkedtables", "datadesk.core")
BANNED_CALLS = frozenset({"open", "print", "input", "__import__"})
BANNED_METHOD_CALLS = frozenset({"now", "today"})
BANNED_READS_ON = frozenset({"os", "time", "builtins"})
BANNED_IMPORTS = frozenset({"random", "builtins"})
BANNED_NAMES = frozenset({"random"})
MUTABLE_DISPLAYS = (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)
MUTABLE_CONSTRUCTORS = frozenset({"list", "dict", "set", "bytearray"})
NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
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
    "CACHE, SEEN = {}, set()",
    "if __debug__:\n    CACHE = {}",
    "try:\n    import tomllib\nexcept ImportError:\n    CACHE = {}",
    "match __name__:\n    case _:\n        CACHE = {}",
    "with suppress():\n    for _ in ():\n        while __debug__:\n            CACHE = {}",
)
ALLOWED_FORMS = (
    'NAMES = ("a", "b")',
    'LOOKUP = MappingProxyType({"a": 1})',
    "def collect():\n    items = []\n    return items\n",
    "if __debug__:\n    def collect():\n        items = []\n        return items\n",
)


def package_sources(name: str) -> list[Path]:
    spec = importlib.util.find_spec(name)
    assert spec is not None and spec.submodule_search_locations, name
    return sorted(
        path for folder in spec.submodule_search_locations for path in Path(folder).rglob("*.py")
    )


def effect(node: ast.expr | ast.stmt) -> str | None:
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
            banned = ", ".join(alias.name for alias in aliases if alias.name in BANNED_IMPORTS)
            return f"import {banned}" if banned else None
        case ast.ImportFrom(module=module) if module in BANNED_IMPORTS:
            return f"from {module} import"
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


def impurities(tree: ast.Module) -> list[tuple[int, str]]:
    nodes = (node for node in ast.walk(tree) if isinstance(node, ast.expr | ast.stmt))
    effects = [(node.lineno, found) for node in nodes if (found := effect(node))]
    state = [
        (statement.lineno, "mutable module state")
        for statement in module_scope(tree)
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
        module = "\n".join(("NAMES = ()", source))
        last_line = len(module.splitlines())
        assert [line for line, _ in impurities(ast.parse(module))] == [last_line], source


def test_scan_allows_immutable_constants() -> None:
    for source in ALLOWED_FORMS:
        assert impurities(ast.parse(source)) == [], source
