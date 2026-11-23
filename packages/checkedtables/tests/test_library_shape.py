import builtins
import dataclasses
import importlib
import inspect
import pkgutil
from collections.abc import Iterable, Iterator, Mapping
from functools import reduce
from operator import or_
from pathlib import Path
from types import FunctionType, MethodType, ModuleType, UnionType
from typing import (
    TYPE_CHECKING,
    ForwardRef,
    Optional,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import checkedtables
from datadesk.core.tables import bib_common, collections_common, qcmr_common, supp_common

if TYPE_CHECKING:
    import _typeshed
    from _typeshed import DataclassInstance, SupportsRead

FAMILY_HELPERS = (qcmr_common, collections_common, bib_common, supp_common)
FIELD_SNAPSHOT: dict[str, tuple[str, ...]] = {
    "Box": ("x0", "top", "x1", "bottom"),
    "WordRef": ("doc_sha256", "page", "index", "child"),
    "WordSource": ("kind", "tool"),
    "Word": ("ref", "text", "box", "bold", "size", "confidence"),
    "Rule": ("box",),
    "Page": ("doc_sha256", "number", "width", "height", "rotation", "source", "words", "rules"),
    "Document": ("sha256", "pages"),
    "Line": ("page", "words", "box"),
    "PageLines": ("number", "source", "lines"),
    "Label": ("printed", "text", "norm", "squash", "marks", "line_no"),
    "Amount": ("printed", "text", "words", "source", "reading", "review_id", "marks"),
    "Dash": ("text", "words", "meaning", "rule_id"),
    "NotApplicable": ("text", "words"),
    "Blank": (),
    "Unreadable": ("text", "words", "reason", "accepted_by"),
    "Text": ("text", "words"),
    "NumberFormat": ("decimals", "percent"),
    "ColumnSpec": ("name", "caption", "kind", "fmt", "presence", "dash"),
    "RowKey": ("parts",),
    "Finding": ("severity", "code", "subject", "message", "page"),
    "ReviewedReading": ("id", "doc_sha256", "page", "box", "source", "seen", "reading", "reason"),
    "EveryRow": (),
    "DashRule": ("id", "table", "columns", "rows", "meaning", "evidence"),
    "CellRecords": ("readings", "dash_rules", "confidence_floor"),
}


def public_modules(module: ModuleType) -> list[ModuleType]:
    found = pkgutil.walk_packages(getattr(module, "__path__", ()), f"{module.__name__}.")
    names = [info.name for info in found]
    public = [name for name in names if not any(part.startswith("_") for part in name.split("."))]
    return [module, *map(importlib.import_module, public)]


def in_package(value: object, root: ModuleType) -> bool:
    module = getattr(value, "__module__", None)
    return isinstance(module, str) and (
        module == root.__name__ or module.startswith(f"{root.__name__}.")
    )


def public_objects(root: ModuleType) -> Iterable[object]:
    return {
        id(value): value
        for module in public_modules(root)
        for name, value in vars(module).items()
        if not name.startswith("_") and in_package(value, root)
    }.values()


def package_members(cls: type, root: ModuleType) -> dict[str, object]:
    defined_in = {name: owner for owner in reversed(cls.__mro__) for name in vars(owner)}
    return {
        name: vars(owner)[name] for name, owner in defined_in.items() if in_package(owner, root)
    }


def written_constructor(cls: type, members: Mapping[str, object]) -> Iterator[MethodType]:
    if "__init__" in members and not dataclasses.is_dataclass(cls):
        yield MethodType(cls.__init__, cls)


def public_methods_as_called(
    cls: type, members: Mapping[str, object]
) -> Iterator[FunctionType | MethodType]:
    for name, member in members.items():
        if name.startswith("_"):
            continue
        if isinstance(member, FunctionType):
            yield MethodType(member, cls)
        elif isinstance(member, classmethod | staticmethod):
            yield getattr(cls, name)


def public_functions(module: ModuleType) -> Iterator[FunctionType | MethodType]:
    for value in public_objects(module):
        if isinstance(value, FunctionType):
            yield value
        elif isinstance(value, type):
            members = package_members(value, module)
            yield from written_constructor(value, members)
            yield from public_methods_as_called(value, members)


class UnresolvedType(type):
    def __getattr__(cls, name: str) -> "UnresolvedType":
        return cls

    def __getitem__(cls, key: object) -> "UnresolvedType":
        return cls


class AnnotationNames(dict[str, object]):
    def __missing__(self, name: str) -> UnresolvedType:
        if name.startswith("__"):
            # pytest reads __tracebackhide__ from the locals of the eval frame on an error.
            raise KeyError(name)
        return UnresolvedType(name, (), {})


def resolved(annotation: object, names: AnnotationNames) -> object:
    if isinstance(annotation, ForwardRef):
        annotation = annotation.__forward_arg__
    if isinstance(annotation, str):
        annotation = eval(annotation, {}, names)
    if get_origin(annotation) in (Union, UnionType):
        return reduce(or_, (resolved(arg, names) for arg in get_args(annotation)))
    return annotation


def accepts_bool(annotation: object) -> bool:
    if get_origin(annotation) in (Union, UnionType):
        return bool in get_args(annotation)
    return annotation is bool


def bool_parameters(fn: FunctionType | MethodType) -> list[str]:
    # eval asks __missing__ for every name before builtins, so builtins and globals go in first.
    names = AnnotationNames({**vars(builtins), **inspect.unwrap(fn).__globals__})
    parameters = inspect.signature(fn).parameters.values()
    return [p.name for p in parameters if accepts_bool(resolved(p.annotation, names))]


def kit_dataclasses() -> list["type[DataclassInstance]"]:
    return [
        value
        for value in public_objects(checkedtables)
        if isinstance(value, type) and dataclasses.is_dataclass(value)
    ]


def field_names(cls: "type[DataclassInstance]") -> tuple[str, ...]:
    return tuple(field.name for field in dataclasses.fields(cls))


def bool_fields(classes: Iterable["type[DataclassInstance]"]) -> set[tuple[str, str]]:
    return {
        (cls.__name__, name)
        for cls in classes
        for name in field_names(cls)
        if accepts_bool(get_type_hints(cls)[name])
    }


def source_lines(package: ModuleType) -> int:
    return sum(
        1
        for folder in package.__path__
        for path in Path(folder).rglob("*.py")
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def public_names(package: ModuleType) -> list[str]:
    return [
        name
        for name, value in vars(package).items()
        if not name.startswith("_") and not isinstance(value, ModuleType)
    ]


def test_no_bool_parameters_and_at_most_four() -> None:
    for module in (checkedtables, *FAMILY_HELPERS):
        for fn in public_functions(module):
            params = list(inspect.signature(fn).parameters.values())
            assert len(params) <= 4, fn.__qualname__
            assert not bool_parameters(fn), fn.__qualname__


def test_bool_parameters_reads_each_spelling() -> None:
    def plain(flag: bool) -> None: ...
    def optional(flag: bool | None) -> None: ...
    def typing_optional(flag: Optional[bool]) -> None: ...  # noqa: UP045
    def quoted_in_optional(flag: Optional["bool"]) -> None: ...
    def keyword_only(*, flag: bool = False) -> None: ...
    def plain_string(flag: "bool") -> None: ...
    def optional_string(flag: "bool | None") -> None: ...
    def unresolved_member(flag: "bool | DataclassInstance") -> None: ...
    def unresolved_dotted(flag: "bool | _typeshed.DataclassInstance") -> None: ...
    def unresolved_subscript(flag: "bool | SupportsRead[str]") -> None: ...
    def flags(flags: tuple[bool, ...]) -> None: ...
    def count(count: int | None) -> None: ...
    def unresolved_beside(row: "DataclassInstance", flag: bool) -> "DataclassInstance":
        return row

    def unresolved_return() -> "DataclassInstance":
        raise NotImplementedError

    for fn in (
        plain,
        optional,
        typing_optional,
        quoted_in_optional,
        keyword_only,
        plain_string,
        optional_string,
        unresolved_beside,
        unresolved_member,
        unresolved_dotted,
        unresolved_subscript,
    ):
        assert bool_parameters(fn) == ["flag"], fn.__name__
    assert bool_parameters(flags) == []
    assert bool_parameters(count) == []
    assert bool_parameters(unresolved_return) == []


def test_public_functions_reaches_reexports_and_constructors() -> None:
    def parse(flag: bool) -> None: ...
    def unreached(hidden: bool) -> None: ...

    class Reader:
        def __init__(self, strict: bool) -> None: ...

    class Outside:
        def write(self, verbose: bool) -> None: ...

    class _Base:
        def __init__(self, source: bool) -> None: ...
        def read(self, lenient: bool) -> None: ...
        def close(self, force: bool) -> None: ...

    class Child(_Base, Outside):
        def close(self, force: bool, quiet: bool = False) -> None: ...

    @dataclasses.dataclass(frozen=True, slots=True)
    class Row:
        bold: bool | None

    parse.__module__ = unreached.__module__ = _Base.__module__ = "planted._impl"
    Reader.__module__ = Child.__module__ = Row.__module__ = "planted"
    Outside.__module__ = "elsewhere"
    private = ModuleType("planted._impl")
    vars(private).update(parse=parse, unreached=unreached)
    package = ModuleType("planted")
    vars(package).update(
        _impl=private, parse=parse, parse_again=parse, Reader=Reader, Child=Child, Row=Row
    )

    found = [list(inspect.signature(fn).parameters) for fn in public_functions(package)]
    assert found == [["flag"], ["strict"], ["source"], ["lenient"], ["force", "quiet"]]


def test_kit_dataclass_fields_are_pinned() -> None:
    assert {cls.__name__: field_names(cls) for cls in kit_dataclasses()} == FIELD_SNAPSHOT


def test_bool_fields_are_page_facts_only() -> None:
    assert bool_fields(kit_dataclasses()) == {("Word", "bold")}


def report_budget() -> None:
    print(
        f"checkedtables: {source_lines(checkedtables)} lines (budget 3,800), "
        f"{len(public_names(checkedtables))} public names (budget 140)"
    )


if __name__ == "__main__":
    report_budget()
