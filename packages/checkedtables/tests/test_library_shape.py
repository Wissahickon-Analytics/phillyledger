import dataclasses
import importlib
import inspect
import pkgutil
from collections.abc import Iterable, Iterator
from pathlib import Path
from types import FunctionType, MethodType, ModuleType, UnionType
from typing import TYPE_CHECKING, Optional, Union, get_args, get_origin, get_type_hints

import checkedtables
from datadesk.core.tables import bib_common, collections_common, qcmr_common, supp_common

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

FAMILY_HELPERS = (qcmr_common, collections_common, bib_common, supp_common)
FIELD_SNAPSHOT: dict[str, tuple[str, ...]] = {}


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


def written_constructor(cls: type) -> Iterator[MethodType]:
    if "__init__" in vars(cls) and not dataclasses.is_dataclass(cls):
        yield MethodType(vars(cls)["__init__"], cls)


def public_methods_as_called(cls: type) -> Iterator[FunctionType | MethodType]:
    for name, member in vars(cls).items():
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
            yield from written_constructor(value)
            yield from public_methods_as_called(value)


def accepts_bool(annotation: object) -> bool:
    if get_origin(annotation) in (Union, UnionType):
        return bool in get_args(annotation)
    return annotation is bool


def bool_parameters(fn: FunctionType | MethodType) -> list[str]:
    parameters = inspect.signature(fn, eval_str=True).parameters.values()
    return [parameter.name for parameter in parameters if accepts_bool(parameter.annotation)]


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
    def keyword_only(*, flag: bool = False) -> None: ...
    def plain_string(flag: "bool") -> None: ...
    def optional_string(flag: "bool | None") -> None: ...
    def flags(flags: tuple[bool, ...]) -> None: ...
    def count(count: int | None) -> None: ...

    for fn in (plain, optional, typing_optional, keyword_only, plain_string, optional_string):
        assert bool_parameters(fn) == ["flag"], fn.__name__
    assert bool_parameters(flags) == []
    assert bool_parameters(count) == []


def test_public_functions_reaches_reexports_and_constructors() -> None:
    def parse(flag: bool) -> None: ...
    def unreached(hidden: bool) -> None: ...

    class Reader:
        def __init__(self, strict: bool) -> None: ...

    @dataclasses.dataclass(frozen=True, slots=True)
    class Row:
        bold: bool | None

    parse.__module__ = unreached.__module__ = "planted._impl"
    Reader.__module__ = Row.__module__ = "planted"
    private = ModuleType("planted._impl")
    vars(private).update(parse=parse, unreached=unreached)
    package = ModuleType("planted")
    vars(package).update(_impl=private, parse=parse, parse_again=parse, Reader=Reader, Row=Row)

    found = public_functions(package)
    assert [list(inspect.signature(fn).parameters) for fn in found] == [["flag"], ["strict"]]


def test_kit_dataclass_fields_are_pinned() -> None:
    assert {cls.__name__: field_names(cls) for cls in kit_dataclasses()} == FIELD_SNAPSHOT


def test_bool_fields_are_page_facts_only() -> None:
    assert bool_fields(kit_dataclasses()) == set()


def report_budget() -> None:
    print(
        f"checkedtables: {source_lines(checkedtables)} lines (budget 3,800), "
        f"{len(public_names(checkedtables))} public names (budget 140)"
    )


if __name__ == "__main__":
    report_budget()
