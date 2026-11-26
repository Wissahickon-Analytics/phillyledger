"""Encode a `Document` as the bytes the word cache keeps, and read those bytes back.

`FORMAT` numbers the layout of the bytes. A change to the layout raises it, and every word key
holds it, so the cache never serves bytes of another layout.
"""

from dataclasses import asdict
from json import dumps, loads
from typing import Any, Never

from checkedtables.kinds import SourceKind
from checkedtables.refs import Box, Sha256, WordRef
from checkedtables.words import Document, Page, Rule, Word, WordSource

FORMAT = 1

_NULL = type(None)
_INT = (int,)
_NUMBER = (int, float)
_STR = (str,)
_OBJECT = (dict,)
_LIST = (list,)
_INT_OR_NULL = (int, _NULL)
_BOOL_OR_NULL = (bool, _NULL)
_NUMBER_OR_NULL = (int, float, _NULL)


def encode_document(doc: Document) -> bytes:
    """Write a document as the bytes the word cache keeps.

    The bytes are one JSON object: the document as `dataclasses.asdict` gives it, keyed by the
    dataclasses' own field names, with the key ``"format"`` set to `FORMAT`. Keys are sorted at
    every level, no space separates them, and every character past ASCII is escaped, so any
    `str` encodes, a lone surrogate included. JSON reads the escapes of a high surrogate
    followed by a low one as the one character the pair stands for, so only such text reads
    back changed. JSON writes a float by its `repr`, so it reads back as the same float. One
    document always gives the same bytes. Two equal documents may not, since ``0.0 == -0.0``
    and the two are written apart.

    Raises
    ------
    ValueError
        When a float is NaN or infinite, which JSON cannot hold.
    """
    fields = asdict(doc) | {"format": FORMAT}
    return dumps(fields, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def decode_document(data: bytes) -> Document:
    """Read back the document that `encode_document` wrote.

    Each sha is built with `Sha256`, each value with its kit constructor, every sequence as a
    tuple and each source kind as its `SourceKind` member. A number keeps the JSON kind it was
    written with, so the document encodes to the same bytes again. A key the document does not
    read is passed over.

    Raises
    ------
    ValueError
        For bytes that are not UTF-8 JSON, a NaN or an infinity, a format that is not the
        integer `FORMAT` (``true`` and ``1.0`` are refused), a missing key, a value of the wrong
        JSON kind, and a value that a kit constructor refuses.
    """
    fields = _checked(loads(data.decode("utf-8"), parse_constant=_refuse), _OBJECT, "the bytes")
    if (number := _field(fields, "format", _INT)) != FORMAT:
        raise ValueError(f"the bytes are of format {number}, not {FORMAT}")
    pages = tuple(_page(page) for page in _items(fields, "pages"))
    return Document(Sha256(_field(fields, "sha256", _STR)), pages)


def _page(fields: dict[str, Any]) -> Page:
    source = _field(fields, "source", _OBJECT)
    return Page(
        doc_sha256=Sha256(_field(fields, "doc_sha256", _STR)),
        number=_field(fields, "number", _INT),
        width=_field(fields, "width", _NUMBER),
        height=_field(fields, "height", _NUMBER),
        rotation=_field(fields, "rotation", _INT),
        source=WordSource(SourceKind(_field(source, "kind", _STR)), _field(source, "tool", _STR)),
        words=tuple(_word(word) for word in _items(fields, "words")),
        rules=tuple(Rule(_box(_field(rule, "box", _OBJECT))) for rule in _items(fields, "rules")),
    )


def _word(fields: dict[str, Any]) -> Word:
    ref = _field(fields, "ref", _OBJECT)
    return Word(
        ref=WordRef(
            doc_sha256=Sha256(_field(ref, "doc_sha256", _STR)),
            page=_field(ref, "page", _INT),
            index=_field(ref, "index", _INT),
            child=_field(ref, "child", _INT_OR_NULL),
        ),
        text=_field(fields, "text", _STR),
        box=_box(_field(fields, "box", _OBJECT)),
        bold=_field(fields, "bold", _BOOL_OR_NULL),
        size=_field(fields, "size", _NUMBER_OR_NULL),
        confidence=_field(fields, "confidence", _NUMBER_OR_NULL),
    )


def _box(fields: dict[str, Any]) -> Box:
    return Box(
        x0=_field(fields, "x0", _NUMBER),
        top=_field(fields, "top", _NUMBER),
        x1=_field(fields, "x1", _NUMBER),
        bottom=_field(fields, "bottom", _NUMBER),
    )


def _items(fields: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [_checked(item, _OBJECT, f"an item of {key!r}") for item in _field(fields, key, _LIST)]


def _field(fields: dict[str, Any], key: str, kinds: tuple[type, ...]) -> Any:
    if key not in fields:
        raise ValueError(f"the key {key!r} is missing")
    return _checked(fields[key], kinds, f"the key {key!r}")


def _checked(value: Any, kinds: tuple[type, ...], where: str) -> Any:
    """Return `value` when its type is one of `kinds`.

    The test is on the exact type, so a JSON ``true`` is not an `int` and ``1`` is not a `bool`.
    """
    if type(value) not in kinds:
        names = " or ".join(kind.__name__ for kind in kinds)
        raise ValueError(f"{where} holds a {type(value).__name__}, not a {names}")
    return value


def _refuse(constant: str) -> Never:
    """Refuse the NaN and infinities that `json.loads` reads by default and JSON lacks."""
    raise ValueError(f"{constant} is not a number JSON can hold")
