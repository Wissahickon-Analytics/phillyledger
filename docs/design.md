# Final design: small typed parsers over a checked-table kit

Written November 22, 2026. This is design C with the 21 required changes in `CHANGES.md` applied.
It also takes the named parts of designs A and B, and answers every finding of the three reviews.
No part of it has been run against a PDF. Every claim about a document comes from a dossier and
carries its quirk id. Section 17 lists what is still open and what is not verified.

## 1. The design on one page

### 1.1 Why this shape

Each table gets a short Python module that calls a small kit of pure functions. The reviewers
compared this with design A, where a table is a specification read by one interpreter. A's
specification language started at 36 types and 88 fields, and the held-out QSMR needed four more
constructs. A specification language grows a field for every odd page, which is how the old
layout language reached 40 options. Plain typed parsers put an odd page's logic in that page's
module, where the type checker and unit tests see it. The kit stays small because a test pins its
shape (section 11.4), so any growth is a reviewed change.

### 1.2 Data flow

```text
publisher listings --watch--> WatchPlan --exec--> pull request (index lines, gaps)
        |                                              | merged
        v                                              v
   fetch: FetchPlan --exec--> object store (PDF by sha256) + pull request (index lines)
        |
        v
   words: WordJob --exec--> pdf adapter or archived Textract response --> Document (cached)
        |                     (Textract itself runs only in `datadesk ocr --spend`)
        v
   parse (pure): TABLES[name].parse(Document, ParseContext) --> Parsed | Failed
        |
        v
   check (pure): run_checks(tables, CheckSets) --> CheckReport (results and coverage findings)
                 match_acknowledgments(report, acks, scope) --> Gate, one per (dataset, edition)
        |
        v
   release (pure): plan_release(ReleaseInputs) --> ReleasePlan (files by sha) + blobs by sha
        |
        v
   exec: stage blobs --> verify hashes --> move latest.json
        |
        v
   reader: plan_load(manifest, request, cache keys) --> LoadPlan --exec--> path or Arrow table
```

### 1.3 Core types, by package

| Package | Core types |
|---|---|
| `checkedtables` | `Box`, `WordRef`, `Word`, `WordSource`, `Page`, `Document`, `Line`, `PageLines`, `PageRun`, `BodyRule`, `ColumnSpec`, `Era`, `Lane`, `Binding`, `Layout`, `CutPage`, `CutPages`, `Cell` (`Amount`, `Dash`, `NotApplicable`, `Blank`, `Unreadable`, `Text`), `Label`, `RawRow`, `RowKey`, `RowDef`, `RowSchema`, `RowRule`, `RowGrammar`, `KeyedRow`, `RowMatch`, `Table`, `Finding`, `ReviewedReading`, `DashRule`, `CellRecords`, the `Check` union, `CheckSet`, `Tolerance`, `RowSel`, `Result`, `CheckReport`, `FailureKey`, `ExpectedFailure`, `Acknowledgment`, `Gate` |
| `datadesk.core` | `EditionKey`, `Period`, `DocumentVersion`, `ArchiveIndex`, `Listing`, `WatchPlan`, `FetchPlan`, `WordSourcePlan`, `EditionNote`, `Kind`, `Version`, `Window`, `How`, `Dim`, `Quantity`, `Stated`, `Derived`, `NotPublished`, `MeasureSpec`, `RowMeasure`, `MeasureSet`, `Scope`, `Subject`, `ParseContext`, `Parsed`, `Failed`, `TableEntry`, `Registry`, `Entity`, `Alias`, `Resolution`, `VintagePolicy`, `ParsePlan`, `OcrPlan`, `ReleaseRow`, `ReleasePlan` |
| `phillyledger` | `Manifest`, `DatasetEntry`, `FileEntry`, `LoadRequest`, `LoadPlan` |

### 1.4 Where every effect lives

| Effect | Port (Protocol) | Adapter | Called from |
|---|---|---|---|
| HTTP to phila.gov, philasd.org and the Wayback CDX | `Http` | `datadesk.shell.adapters.http_httpx` | `watch` and `fetch` executors |
| Object store (public PDFs, private Textract JSON, releases) | `ObjectStore` | `datadesk.shell.adapters.s3` | `fetch`, `ocr`, `words` and `release` executors |
| Textract | `OcrService` | `datadesk.shell.adapters.textract` | the `ocr` executor only, and only with `--spend` |
| PDF words, rules and page-1 text | `PdfReader` | `datadesk.shell.adapters.pdf_pdfplumber` | `fetch` and `words` executors |
| Local content-addressed cache | `LocalCache` | `datadesk.shell.adapters.cache_dir`, `phillyledger._shell.cache_dir` | executors, reader |
| Git and pull requests | `GitHost` | `datadesk.shell.adapters.github` | `watch` and `fetch` executors |
| Clock | none; `cli.main` reads the time once and passes a `date` and a `datetime` down | `datadesk.shell.cli` | CLI entry only |
| Environment | none; `load_settings(environ)` returns a frozen `Settings` once | `datadesk.shell.settings` | CLI entry only |
| Repository files (TOML records, index, schemas) | none; `gather_repo` reads text once into a `RepoSnapshot` | `datadesk.shell.gather` | CLI entry only |
| Logging and progress | none; findings are values | `datadesk.shell.report` | executors |

## 2. Domain model

All types are frozen dataclasses with `slots=True` unless noted. Collections are tuples, sorted
where order carries no meaning. No frozen type holds a `Mapping` or a `list`. Money and counts are
`Decimal`. Floats appear only in geometry and OCR confidence.

A kit dataclass holds no switch. A field that changes behaviour is an enum or a union case. The
only `bool` fields are facts read from the page: `Word.bold` and `Column.printed`. The shape test
in section 11.4 enforces both rules.

### 2.1 `checkedtables` types

The checks a kit type makes at construction are the ones its block below shows, and no others.
They guard what enters the kit from outside: an adapter's words, pages and documents, a record
file's ids and reasons, and a table module's columns. Each raises `ValueError`. A relation
between two fields that one kit function computes has no check at construction. `parse_label`
keeps `Label.norm`, `Label.squash` and `Label.text`, and `lex_cell` and `apply_reading` keep
`Amount.printed` and each cell's `text`, and their tests prove it. A pull request that adds a
check shows it in the block.

```python
# checkedtables/refs.py: Box and WordRef. Cells and checks import this module, never words.
@dataclass(frozen=True, slots=True)
class Box:
    x0: float
    top: float
    x1: float
    bottom: float

    def __post_init__(self) -> None:
        if not (self.x0 <= self.x1 and self.top <= self.bottom):
            raise ValueError(f"inverted box {self}")

    @staticmethod
    def around(boxes: Iterable["Box"]) -> "Box": ...        # smallest box holding all; ValueError if none

    def contains(self, other: "Box", slack: float) -> bool: ...


@dataclass(frozen=True, slots=True)
class WordRef:
    doc_sha256: str
    page: int                  # 1-based page in the publisher file, never a cut file
    index: int                 # extraction order on that page; evidence only, never a record key
    child: int | None = None   # set when split_numeric_runs made this word; its box is approximate

    def __post_init__(self) -> None: ...    # ValueError: an empty doc_sha256, a page below 1,
                                            # or an index or a child below 0

    # __lt__, __le__, __gt__, __ge__: by the four fields, a None child before every int child.
    # order=True would raise TypeError comparing a word with its child (None against int).


# checkedtables/kinds.py
class SourceKind(StrEnum):
    TEXT_LAYER = "text_layer"
    OCR = "ocr"


class ValueKind(StrEnum):
    MONEY = "money"
    COUNT = "count"
    PERCENT = "percent"
    YEAR = "year"
    CODE = "code"
    TEXT = "text"


class DashMeaning(StrEnum):
    NO_VALUE = "no_value"      # the default everywhere
    ZERO = "zero"              # only from a DashRule or an era column that declares it


class Presence(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"


class PercentSign(StrEnum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    ABSENT = "absent"
```

```python
# checkedtables/words.py
@dataclass(frozen=True, slots=True)
class WordSource:
    kind: SourceKind
    tool: str                  # "pdfplumber==0.11.4;dedupe_chars" or "textract:AnalyzeDocument;dpi=300"


@dataclass(frozen=True, slots=True)
class Word:
    ref: WordRef
    text: str                  # verbatim, before any cleaning
    box: Box
    bold: bool | None          # None: the source carries no style (every OCR word)
    size: float | None
    confidence: float | None   # OCR only, 0 to 100

    def __post_init__(self) -> None: ...    # ValueError: a confidence outside 0 to 100 or NaN


@dataclass(frozen=True, slots=True)
class Rule:
    box: Box                   # a drawn line; vertical when width < 1 pt


@dataclass(frozen=True, slots=True)
class Page:
    doc_sha256: str
    number: int
    width: float
    height: float
    rotation: int
    source: WordSource
    words: tuple[Word, ...]
    rules: tuple[Rule, ...] = ()

    def __post_init__(self) -> None:
        if not self.doc_sha256:
            raise ValueError(f"page {self.number} names no file")
        if self.number < 1:
            raise ValueError(f"a page has a number below 1: {self.number}")
        seen: set[WordRef] = set()
        for w in self.words:
            if w.ref.doc_sha256 != self.doc_sha256 or w.ref.page != self.number:
                raise ValueError(f"word {w.ref} does not belong to page {self.number}")
            if w.ref in seen:
                raise ValueError(f"two words on page {self.number} share the ref {w.ref}")
            seen.add(w.ref)
            if self.source.kind is SourceKind.TEXT_LAYER and w.confidence is not None:
                raise ValueError(f"word {w.ref} has an OCR confidence on a text layer page")


@dataclass(frozen=True, slots=True)
class Document:
    sha256: str
    pages: tuple[Page, ...]    # pages extracted, ascending; need not be contiguous

    def __post_init__(self) -> None: ...    # ValueError: an empty sha256, a page whose
                                            # doc_sha256 is not sha256, or page numbers that are
                                            # not strictly ascending

    def page(self, number: int) -> Page: ...
```

What these make impossible:

- a word without its file hash and page;
- a page with two word sources;
- a page number that refers to a cut file, because no type stands for a cut file;
- "not bold" and "style unknown" as one state.

```python
# checkedtables/lines.py
@dataclass(frozen=True, slots=True)
class Line:
    page: int
    words: tuple[Word, ...]    # left to right
    box: Box

    @property
    def text(self) -> str: ...  # normalize_space(" ".join(w.text for w in words))


@dataclass(frozen=True, slots=True)
class PageLines:
    number: int
    source: SourceKind
    lines: tuple[Line, ...]


# checkedtables/pages.py
@dataclass(frozen=True, slots=True)
class PageRun:
    first: int
    last: int

    @property
    def pages(self) -> range: ...

    def take(self, pages: Sequence[PageLines]) -> tuple[PageLines, ...]: ...


@dataclass(frozen=True, slots=True)
class BodyRule:
    start: Callable[[Line], bool]            # first body line; everything above is header
    stop: Callable[[Line], bool] | None      # last body line, inclusive; None runs to page end
    drop: tuple[str, ...] = ()               # regexes searched in each body line; a hit is furniture
    prefix: str | None = None                # regex for a leading line-number word (QPOS-Q08)
```

```python
# checkedtables/labels.py: Label alone, so tables and checks never import words
@dataclass(frozen=True, slots=True)
class Label:
    printed: str               # verbatim joined words, line number included
    text: str                  # printed minus marks and line number
    norm: str                  # normalize_label(text)
    squash: str                # norm without spaces: "car and truc k rental" -> "carandtruckrental"
    marks: tuple[str, ...]     # "(1)", "**2", "*", "see note", "(19+20)", ", subtotal"
    line_no: str | None        # "23", "I", "C01234": the words BodyRule.prefix split off
```

```python
# checkedtables/columns.py
@dataclass(frozen=True, slots=True)
class NumberFormat:
    decimals: int | None = 0                 # printed decimals; None means "as printed"
    percent: PercentSign = PercentSign.ABSENT


@dataclass(frozen=True, slots=True)
class ColumnSpec:
    name: str                                # stable name used in checks and keys
    caption: str                             # regex searched in the lane's stacked caption
    kind: ValueKind
    fmt: NumberFormat = NumberFormat()
    presence: Presence = Presence.REQUIRED
    dash: DashMeaning = DashMeaning.NO_VALUE

    def __post_init__(self) -> None: ...     # ValueError: an empty name or an empty caption


@dataclass(frozen=True, slots=True)
class Era:
    name: str
    signature: tuple[str, ...]               # caption regexes that must all appear in the header
    columns: tuple[ColumnSpec, ...]          # left to right
    expected: tuple[date, date | None]       # cross-check only; a mismatch is a BLOCK finding
    excludes: tuple[str, ...] = ()           # caption regexes that must not appear

    def __post_init__(self) -> None:
        names = [c.name for c in self.columns]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate column names in era {self.name}")
        if all(c.presence is Presence.OPTIONAL for c in self.columns):
            raise ValueError(f"era {self.name} has no required column")


@dataclass(frozen=True, slots=True)
class Lane:
    x0: float
    x1: float
    caption: str               # header words over the lane, top to bottom


@dataclass(frozen=True, slots=True)
class Binding:
    era: str
    columns: tuple[tuple[ColumnSpec, Lane | None], ...]   # None: optional column not printed
    label_right: float                                    # x where the label area ends
```

What these make impossible:

- a column without a name and a caption;
- an era with duplicate column names;
- mapping a column by its count from the right, because no type carries a right-to-left index;
- a silent decimal repair, because no format says "insert a decimal point".

```python
# checkedtables/pipeline.py
@dataclass(frozen=True, slots=True)
class Layout:
    eras: tuple[Era, ...]
    body: BodyRule


@dataclass(frozen=True, slots=True)
class CutPage:
    number: int
    source: SourceKind
    header: tuple[Line, ...]
    binding: Binding
    raws: tuple["RawRow", ...]
    furniture: tuple[Line, ...]        # lines a drop pattern removed; kept for the ink ledger


@dataclass(frozen=True, slots=True)
class CutPages:
    era: Era
    binding: Binding                   # the first page's binding; every page binds the same columns
    pages: tuple[CutPage, ...]         # at least one
    findings: tuple["Finding", ...]

    @property
    def raws(self) -> tuple["RawRow", ...]: ...
```

`CutPages` always holds a `Binding`. A parser never carries `Binding | None` into `assemble`
(R1, R2, R3 type finding).

```python
# checkedtables/cells.py
class Reading(StrEnum):
    DIRECT = "direct"
    REVIEWED = "reviewed"          # a ReviewedReading supplied the value


@dataclass(frozen=True, slots=True)
class Amount:
    printed: Decimal               # the number as printed, before unit scale
    text: str                      # verbatim joined word text
    words: tuple[WordRef, ...]
    source: SourceKind             # decides whether a passing check can prove it (section 8.3)
    reading: Reading = Reading.DIRECT
    review_id: str | None = None
    marks: tuple[str, ...] = ()    # "*" on "242,096*", a superscript digit

    def __post_init__(self) -> None:
        if not self.words:
            raise ValueError("an Amount needs the words it was read from")
        if self.review_id == "":
            raise ValueError("an Amount names an empty review id")
        if (self.reading is Reading.REVIEWED) != (self.review_id is not None):
            raise ValueError("a reviewed Amount names its review, and only then")


@dataclass(frozen=True, slots=True)
class Dash:
    text: str
    words: tuple[WordRef, ...]
    meaning: DashMeaning
    rule_id: str | None = None     # the DashRule that set ZERO, if any

    def __post_init__(self) -> None:
        if not self.words:
            raise ValueError("a Dash needs the words it was read from")


@dataclass(frozen=True, slots=True)
class NotApplicable:
    text: str                      # "N/A", "NA"
    words: tuple[WordRef, ...]


@dataclass(frozen=True, slots=True)
class Blank:
    pass


@dataclass(frozen=True, slots=True)
class Unreadable:
    text: str
    words: tuple[WordRef, ...]
    reason: str                    # "grouping", "low_confidence", "two_tokens", ...
    accepted_by: str | None = None # review id that accepts publishing null


@dataclass(frozen=True, slots=True)
class Text:
    text: str
    words: tuple[WordRef, ...]


Cell = Amount | Dash | NotApplicable | Blank | Unreadable | Text
```

What this makes impossible:

- a number without words;
- a dash that is silently zero, because its meaning comes from a declared rule that is named;
- "blank" and "dash" as two flags on one field;
- an OCR number that hides its source.

```python
# checkedtables/table.py
class RowKind(StrEnum):
    HEADING = "heading"
    ITEM = "item"
    SUBTOTAL = "subtotal"
    TOTAL = "total"
    BREAKDOWN = "breakdown"    # inside a parent already counted (Civilian under Police Total)
    MEMO = "memo"              # comparator or memo; published, never summed


class Additivity(StrEnum):
    ADDITIVE = "additive"
    COMPONENT = "component"
    NONE = "none"


def additivity_of(kind: RowKind) -> Additivity: ...
    # ITEM, SUBTOTAL, TOTAL -> ADDITIVE; BREAKDOWN -> COMPONENT; MEMO, HEADING -> NONE


@dataclass(frozen=True, slots=True, order=True)
class RowKey:
    parts: tuple[tuple[str, str], ...]      # sorted by name: (("breakdown", "civilian"), ("dept", ...))

    def __post_init__(self) -> None: ...    # ValueError: no parts, names not strictly ascending,
                                            # an empty name, or "|" or "=" in a name or value

    def __str__(self) -> str: ...           # "breakdown=civilian|dept=phl_dept_police"

    @staticmethod
    def of(**parts: str) -> "RowKey": ...   # sorts the parts by name

    @staticmethod
    def parse(text: str) -> "RowKey": ...   # inverse of str; TOML records only; code uses RowKey.of
                                            # ValueError: a part with no "="

    @property
    def has_occurrence(self) -> bool: ...   # an "occurrence" part from a list table


class Severity(StrEnum):
    BLOCK = "block"
    WARN = "warn"


@dataclass(frozen=True, slots=True)
class Finding:
    severity: Severity
    code: str                  # "unknown_row", "style_unavailable", "check_not_evaluated", ...
    subject: str               # "<doc sha8>:<table>:<row key or label>"
    message: str
    page: int | None = None

    # __lt__, __le__, __gt__, __ge__: by the five fields, a None page before every int page,
    # as WordRef does for child.


@dataclass(frozen=True, slots=True, order=True)
class TableId:
    name: str
    instance: tuple[tuple[str, str], ...] = ()   # (("fund", "phl_fund_general"),) or (("zone", "location"),)

    def part(self, name: str) -> str: ...        # KeyError when the part is absent

    def __str__(self) -> str: ...                # "supplemental_revenues|fund=phl_fund_general"


@dataclass(frozen=True, slots=True)
class Column:
    name: str
    kind: ValueKind
    caption: str               # printed caption text, for the release
    printed: bool              # a fact read from the page: False when an optional column was absent


@dataclass(frozen=True, slots=True)
class Row:
    key: RowKey
    kind: RowKind
    label: Label
    parent: RowKey | None
    page: int
    label_words: tuple[WordRef, ...]
    cells: tuple[Cell, ...]    # aligned with Table.columns
    entity: str | None
    unit: str | None

    @property
    def additivity(self) -> Additivity: ...      # additivity_of(self.kind)


@dataclass(frozen=True, slots=True)
class Table:
    id: TableId
    doc_sha256: str
    era: str
    pages: tuple[int, ...]
    columns: tuple[Column, ...]
    rows: tuple[Row, ...]

    def __post_init__(self) -> None:
        keys = [r.key for r in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{self.id}: duplicate row keys")
        if any(len(r.cells) != len(self.columns) for r in self.rows):
            raise ValueError(f"{self.id}: ragged row")
        known = set(keys)
        if any(r.parent is not None and r.parent not in known for r in self.rows):
            raise ValueError(f"{self.id}: parent key not in table")

    def cell(self, key: RowKey, column: str) -> Cell: ...
    def row(self, key: RowKey) -> Row | None: ...
    def children(self, key: RowKey) -> tuple[Row, ...]: ...
```

Additivity is derived from the row kind. A `MEMO` row that is `ADDITIVE` cannot be built (R3).
`Table.__post_init__` raises because `assemble` has already turned duplicate keys and dangling
parents into findings. Reaching the raise is a bug (section 9).

```python
# checkedtables/rows.py
@dataclass(frozen=True, slots=True)
class RawRow:
    page: int
    prefix: tuple[Word, ...]                          # words BodyRule.prefix split off
    label_words: tuple[Word, ...]
    cells: tuple[tuple[str, tuple[Word, ...]], ...]   # column name -> words in that lane
    stray: tuple[Word, ...]                           # in no lane, right of the label area
    bold: bool | None                                 # all label words bold; None if style unknown
    x0: float

    def has_values(self) -> bool: ...


class Truncation(StrEnum):
    NONE = "none"
    UNIQUE_PREFIX = "unique_prefix"    # a printed prefix of exactly one label matches (MCITY-Q21)


@dataclass(frozen=True, slots=True)
class RowDef:
    key: RowKey
    kind: RowKind
    labels: tuple[str, ...]            # filled by schema_for: schema labels, or registry names
    parent: RowKey | None = None       # None: the schema root, if the schema has one
    within: RowKey | None = None       # block that must be open for this row to match
    follows: RowKey | None = None      # unlabeled rows only: matches the line right after this row
    presence: Presence = Presence.REQUIRED
    entity: str | None = None          # registry link; such a row's labels come from the registry
    unit: str | None = None            # row-level unit (O-3 positions rows)

    def __post_init__(self) -> None:
        if self.follows is not None and self.labels != ("",):
            raise ValueError(f"{self.key}: only an unlabeled row may use follows")


@dataclass(frozen=True, slots=True)
class RowSchema:
    table: str
    rows: tuple[RowDef, ...]           # already narrowed to one edition
    root: RowKey | None = None         # the grand total; rows with no parent hang under it
    drop: tuple[str, ...] = ()
    truncation: Truncation = Truncation.NONE

    def __post_init__(self) -> None:
        keys = [r.key for r in self.rows]
        if len(keys) != len(set(keys)):
            raise ValueError(f"duplicate RowDef key in {self.table}")


@dataclass(frozen=True, slots=True)
class KeyedRow:
    raw: RawRow
    label: Label
    key: RowKey
    kind: RowKind
    parent: RowKey | None
    entity: str | None = None
    unit: str | None = None


@dataclass(frozen=True, slots=True)
class RowMatch:
    rows: tuple[KeyedRow, ...]
    findings: tuple[Finding, ...]
```

```python
# checkedtables/grammar.py
class Values(StrEnum):
    ANY = "any"
    PRESENT = "present"        # the row has at least one value word in a lane
    ABSENT = "absent"


class Style(StrEnum):
    ANY = "any"
    BOLD = "bold"
    NOT_BOLD = "not_bold"      # either one on a row with bold=None is a style_unavailable finding


@dataclass(frozen=True, slots=True)
class AllSlots:
    pass                       # a grand total closes every open level, root included


@dataclass(frozen=True, slots=True)
class RowRule:
    name: str
    kind: RowKind
    pattern: str                             # regex matched at the start of Label.text, ignoring case
    values: Values = Values.ANY
    style: Style = Style.ANY
    opens: str | None = None                 # slot this row opens with its label
    closes: tuple[str, ...] | AllSlots = ()  # slots this row closes; their rows get it as parent
    key: tuple[str, ...] = ()                # slot names and "label", in order
    fixed: tuple[tuple[str, str], ...] = ()  # constant key parts, e.g. (("line", "total"),)


@dataclass(frozen=True, slots=True)
class Unique:
    pass                                     # a repeated key is a duplicate_row finding


@dataclass(frozen=True, slots=True)
class Occurrences:
    block: str                               # slot name, or "root"; repeated keys are numbered in it


Repeats = Unique | Occurrences


@dataclass(frozen=True, slots=True)
class RowGrammar:
    table: str
    slots: tuple[str, ...]                   # outer to inner; "root" is implicit and always open
    rules: tuple[RowRule, ...]               # tried in order; the first match wins
    drop: tuple[str, ...] = ()
    repeats: Repeats = Unique()

    def __post_init__(self) -> None:
        for rule in self.rules:
            unknown = [k for k in rule.key if k != "label" and k not in self.slots]
            if unknown or (rule.opens is not None and rule.opens not in self.slots):
                raise ValueError(f"{self.table}.{rule.name}: unknown slot {unknown or rule.opens}")
```

What these make impossible:

- a row without a key;
- a schema with two rows of one key;
- a breakdown row that matches outside its parent block (`within`);
- an unlabeled row that claims any orphan amount line (`follows`, QCASH-Q27);
- a rule that tests bold and silently matches nothing on a scan (`Style` plus `style_unavailable`);
- a key part named after a slot that does not exist;
- a repeated label in a table that did not declare itself a list.

```python
# checkedtables/records.py: the two record types the kit applies to cells
@dataclass(frozen=True, slots=True)
class ReviewedReading:
    id: str                    # never blank: a reviewed Amount names it
    doc_sha256: str
    page: int
    box: Box                   # where the reviewer looked
    source: SourceKind         # the word layer being read
    seen: str                  # what extraction returns inside the box, joined: "2918" or "1o4.o"
    reading: str | None        # what a person reads on the rendered page; None accepts null
    reason: str                # never blank: a human reading is a record with a page and a reason

    def __post_init__(self) -> None: ...   # ValueError: an id or a reason empty after strip()


@dataclass(frozen=True, slots=True)
class EveryRow:
    pass


@dataclass(frozen=True, slots=True)
class DashRule:
    id: str                    # never blank: a Dash the rule sets to ZERO names it
    table: str
    columns: tuple[str, ...]
    rows: tuple[RowKey, ...] | EveryRow
    meaning: DashMeaning
    evidence: str              # "maintainer confirmed 2026-10-01 against page 2"

    def __post_init__(self) -> None: ...   # ValueError: an id empty after strip()


@dataclass(frozen=True, slots=True)
class CellRecords:
    readings: tuple[ReviewedReading, ...]   # for this document only
    dash_rules: tuple[DashRule, ...]        # already narrowed to this edition's period
    confidence_floor: float                 # OCR words below it need a reading (change 4)

    def __post_init__(self) -> None: ...    # ValueError: an id that two records share, two
                                            # readings, two dash rules, or one of each, since
                                            # Assembly.used names a record by its id alone
```

A reading is keyed by file hash, page, box and the text the extraction returned. It is never
keyed by word index, which shifts when the extraction library changes. If the words inside the
box stop joining to `seen`, the reading is stale and blocks. A reading whose digits are not a
transliteration of `seen`, less the mark words that end an `Amount`, is refused
(`transliteration_ok`, MSCH-Q26, VAL-Q28).

```python
# checkedtables/assemble.py
@dataclass(frozen=True, slots=True)
class Assembly:
    table: Table | None            # None when blocking findings make a table impossible
    findings: tuple[Finding, ...]
    used: frozenset[str]           # ids of readings and dash rules that changed a cell
```

```python
# checkedtables/checks/dsl.py
@dataclass(frozen=True, slots=True)
class Exact:
    pass


@dataclass(frozen=True, slots=True)
class PerOperand:
    increment: Decimal             # bound = increment x (1 + n) / 2, strict (tables/checks.py:80-100)


@dataclass(frozen=True, slots=True)
class Absolute:
    bound: Decimal


Tolerance = Exact | PerOperand | Absolute
EXACT = Exact()


def bound_of(tolerance: Tolerance, n_parts: int) -> Decimal:
    match tolerance:
        case Exact():
            return Decimal(0)
        case PerOperand(increment=i):
            return i * (1 + n_parts) / 2
        case Absolute(bound=b):
            return b
        case _:
            assert_never(tolerance)


# Row selectors: a closed union, no flags.
@dataclass(frozen=True, slots=True)
class AllRows:
    pass


@dataclass(frozen=True, slots=True)
class Keys:
    keys: tuple[RowKey, ...]


@dataclass(frozen=True, slots=True)
class Kinds:
    kinds: tuple[RowKind, ...]


@dataclass(frozen=True, slots=True)
class AdditiveRows:
    pass                           # rows whose additivity is ADDITIVE


@dataclass(frozen=True, slots=True)
class Has:
    column: str                    # rows where this cell is printed (from A)


@dataclass(frozen=True, slots=True)
class Except:
    base: "RowSel"
    keys: tuple[RowKey, ...]       # e.g. the reporting-year row (SUPCAP-Q29)


RowSel = AllRows | Keys | Kinds | AdditiveRows | Has | Except


@dataclass(frozen=True, slots=True)
class FirstPresent:
    columns: tuple[str, ...]       # the first printed one; the last must be a required column (from B)


ColumnRef = str | FirstPresent


@dataclass(frozen=True, slots=True)
class CellSel:
    table: TableId
    row: RowKey
    column: str


# Terms of a column sum: a closed union.
@dataclass(frozen=True, slots=True)
class Plus:
    rows: RowSel


@dataclass(frozen=True, slots=True)
class Minus:
    rows: RowSel


@dataclass(frozen=True, slots=True)
class PlusIfPrinted:
    rows: RowSel                   # a missing operand is dropped, never a failure (TRANS)


Term = Plus | Minus | PlusIfPrinted


# The six relations. One class each; the shape test pins every field list.
@dataclass(frozen=True, slots=True)
class RowSum:
    id: str
    total: ColumnRef
    parts: tuple[ColumnRef, ...]
    rows: RowSel = AllRows()
    tolerance: Tolerance | None = None     # None: the CheckSet default
    severity: Severity = Severity.BLOCK


@dataclass(frozen=True, slots=True)
class RowDifference:
    id: str
    minuend: ColumnRef
    subtrahend: ColumnRef
    result: ColumnRef
    rows: RowSel = AllRows()
    tolerance: Tolerance | None = None
    severity: Severity = Severity.BLOCK


@dataclass(frozen=True, slots=True)
class ColumnSum:
    id: str
    total: RowKey
    terms: tuple[Term, ...]
    columns: tuple[str, ...]
    na_excluded: tuple[RowKey, ...] = ()
    tolerance: Tolerance | None = None
    severity: Severity = Severity.BLOCK


@dataclass(frozen=True, slots=True)
class ChildrenSum:
    id: str
    parents: RowSel
    columns: tuple[str, ...]
    na_excluded: tuple[RowKey, ...] = ()
    tolerance: Tolerance | None = None
    severity: Severity = Severity.BLOCK


@dataclass(frozen=True, slots=True)
class Ratio:
    id: str
    numerator: ColumnRef
    denominator: ColumnRef
    result: ColumnRef
    scale: Decimal = Decimal(100)
    rows: RowSel = AllRows()
    severity: Severity = Severity.BLOCK


@dataclass(frozen=True, slots=True)
class CellsEqual:
    id: str
    left: tuple[CellSel, ...]
    right: tuple[CellSel, ...]
    tolerance: Tolerance | None = None
    severity: Severity = Severity.BLOCK


Check = RowSum | RowDifference | ColumnSum | ChildrenSum | Ratio | CellsEqual


@dataclass(frozen=True, slots=True)
class CheckSet:
    table: str
    checks: tuple[Check, ...]
    default_tolerance: Tolerance

    def __post_init__(self) -> None:
        ids = [c.id for c in self.checks if not isinstance(c, CellsEqual)]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.table}: duplicate check id")

    def add(self, check: Check) -> "CheckSet": ...    # chained; fills tolerance=None from the default


def declare(table: str, tolerance: Tolerance) -> CheckSet: ...
```

A check that names both a column and a row set, or neither, cannot be built. Each relation is
its own class, so a field that does not apply to it does not exist on it (R1, R2, R3).

```python
# checkedtables/checks/engine.py
class Outcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"                     # all operands numeric, |residual| >= bound (> 0 for Exact)
    MISSING_TOTAL = "missing_total"   # total not numeric while parts are numeric and non-zero
    MISSING_OPERAND = "missing_operand"


class Evidence(StrEnum):
    TEXT_LAYER = "text_layer"
    OCR = "ocr"                       # OCR words with no reviewed reading
    REVIEWED = "reviewed"


@dataclass(frozen=True, slots=True, order=True)
class FailureKey:
    doc_sha256: str
    check_id: str
    table: TableId                    # with its instance part (from A)
    row: RowKey | None                # the total's row
    column: str | None                # the total's column


@dataclass(frozen=True, slots=True)
class Operand:
    table: TableId
    row: RowKey
    column: str
    page: int
    value: Decimal | None             # printed value; None when not numeric
    cell: str                         # "amount", "dash", "na", "blank", "unreadable", "text"
    evidence: Evidence | None         # None when the cell has no words


@dataclass(frozen=True, slots=True)
class Result:
    key: FailureKey
    outcome: Outcome
    residual: Decimal | None          # total minus the signed sum of parts, exact
    bound: Decimal
    total: Operand
    parts: tuple[Operand, ...]
    severity: Severity


@dataclass(frozen=True, slots=True)
class CheckReport:
    results: tuple[Result, ...]       # sorted by key
    findings: tuple[Finding, ...]     # coverage: check_not_evaluated, total_without_parts, ...

    def failures(self) -> tuple[Result, ...]: ...   # FAIL and MISSING_TOTAL
```

`CheckReport.skipped` is gone. A declared check that produces no evaluation is a blocking finding
(change 1, section 8.2).

```python
# checkedtables/checks/acks.py
class AckKind(StrEnum):
    SOURCE_ARITHMETIC = "source_arithmetic"   # printed parts do not add to the printed total
    SOURCE_TYPO = "source_typo"               # one printed cell blank, repeated or misplaced
    SOURCE_OMISSION = "source_omission"       # the total leaves out a printed row
    LAYOUT_EXCEPTION = "layout_exception"     # the relation does not hold by design in this edition


@dataclass(frozen=True, slots=True)
class ExpectedFailure:
    key: FailureKey
    residual: Decimal | None        # None only for MISSING_TOTAL
    page: int                       # page of the total operand
    operands: tuple[tuple[str, str, str], ...]   # (row key, column, signed printed value), sorted;
                                                 # total first. No coordinates, so a moved line still
                                                 # matches and a changed operand reopens the failure


@dataclass(frozen=True, slots=True)
class Acknowledgment:
    id: str
    kind: AckKind
    expects: tuple[ExpectedFailure, ...]
    reason: str
    reviewed_by: str
    reviewed_on: date
    root: str | None = None         # groups one defect repeated across editions

    def __post_init__(self) -> None:
        if not self.expects:
            raise ValueError(f"{self.id}: an acknowledgment must name what it covers")


@dataclass(frozen=True, slots=True)
class Gate:
    covered: tuple[tuple[Result, str], ...]          # (failure, acknowledgment id)
    blocking: tuple[Result, ...]                     # BLOCK failures with no acknowledgment
    findings: tuple[Finding, ...]                    # BLOCK findings in scope (parse, coverage)
    unused: tuple[tuple[str, ExpectedFailure], ...]
    mismatched: tuple[tuple[str, ExpectedFailure, Result], ...]
    double_covered: tuple[Result, ...]
    refused: tuple[tuple[str, ExpectedFailure], ...] # expectations on occurrence-numbered keys

    @property
    def passed(self) -> bool:
        return not (self.blocking or self.findings or self.unused or self.mismatched
                    or self.double_covered or self.refused)
```

There is no `AckKind` for extraction errors. An extraction error is fixed by a word source or a
reviewed reading, never by acknowledging arithmetic (MSCH-Q27, MSCH-Q28).

### 2.2 `datadesk.core` types

```python
# datadesk/core/domain.py
class Stage(StrEnum):
    NONE = "none"
    ADOPTED = "adopted"
    PROPOSED = "proposed"


@dataclass(frozen=True, slots=True, order=True)
class Period:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(f"period ends before it starts: {self}")

    def holds(self, day: date) -> bool:
        return self.start <= day <= self.end


@dataclass(frozen=True, slots=True, order=True)
class EditionKey:
    series: str                # "qcmr", "collections_city", "birt_sector", "qsmr", ...
    period: Period             # the period the edition reports; BIRT: its coverage of tax years;
                               # QCMR: its fiscal quarter, from the quarter's first day to the
                               # printed end, so FY2026 Q4 is 2026-04-01 to 2026-06-30
    stage: Stage = Stage.NONE

    def id(self) -> str: ...   # "qcmr:2023-06-30:none"


class Via(StrEnum):
    PUBLISHER = "publisher"
    WAYBACK = "wayback"
    MANUAL = "manual"          # hand-entered URL (QSMR-Q01) or a held excerpt


class Holding(StrEnum):
    WHOLE = "whole"            # the publisher's file, byte for byte
    EXCERPT = "excerpt"        # a hand-cut section; only for an edition with no full document (section 16)


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    sha256: str
    edition: EditionKey
    listed_at: str             # sortable: upload stamp or "<listing date>#<position>";
                               # document-finder: the 14-digit upload stamp in the URL path
    urls: tuple[str, ...]      # every URL that served these bytes, canonical host
    title: str                 # listing title, verbatim
    printed_period: Period | None
    supersedes: str | None     # sha of the earlier version of the same edition; its listed_at
                               # may equal this one's (new bytes behind an unchanged URL)
    via: Via = Via.PUBLISHER
    holding: Holding = Holding.WHOLE


@dataclass(frozen=True, slots=True)
class ArchiveIndex:
    versions: tuple[DocumentVersion, ...]   # sorted by (edition, listed_at, sha256)

    def __post_init__(self) -> None:
        if problem := index_problem(self.versions):
            raise ValueError(problem.message)

    def current(self, edition: EditionKey) -> DocumentVersion | None: ...
        # the edition's version that no other version supersedes
    def by_sha(self, sha: str) -> DocumentVersion | None: ...


def sort_versions(versions: Iterable[DocumentVersion]) -> tuple[DocumentVersion, ...]: ...
def index_problem(versions: tuple[DocumentVersion, ...]) -> Finding | None: ...
    # the rules an index never breaks, each a BLOCK finding: versions sorted by
    # (edition, listed_at, sha256); one sha on one line (content_alias); supersedes names a
    # version of the same edition (supersedes_outside_edition); one version per edition that
    # nothing supersedes (two_current_versions); following supersedes from that version reaches
    # every version of its edition once and then ends, so a version that supersedes itself or a
    # cycle of versions is refused (broken_chain)
```

What this makes impossible:

- identity from a file path (BSALES-Q04, SUPCAP-Q03);
- two editions sharing one set of bytes without a rejection (MSCH-Q01);
- a revision that silently replaces bytes (RTT-Q07);
- an edition whose versions are not one chain from one current version.

```python
# datadesk/core/records.py   (all loaded from TOML text by pure functions)
@dataclass(frozen=True, slots=True)
class WordSourcePlan:
    id: str
    doc_sha256: str
    pages: tuple[int, ...]           # empty means every page
    source: SourceKind
    compare: SourceKind | None       # also extract this source for these pages and compare digits
    reason: str


class NoteKind(StrEnum):
    PRINTED_PERIOD = "printed_period"     # the file prints another period (QCMR FY14 Q2)
    CUTOFF = "cutoff"                     # last actual month differs from the quarter default
    HEADER_MISPRINT = "header_misprint"   # a caption prints a wrong year (wage 2023_12)
    DROP_LINE = "drop_line"               # one printed line is debris (City 2023-07 orphan)
    HEADER_ILLEGIBLE = "header_illegible" # scan header unreadable; bind by lane order on this page


@dataclass(frozen=True, slots=True)
class EditionNote:
    id: str
    kind: NoteKind
    doc_sha256: str
    page: int | None
    printed: str        # the exact printed text the note is about; must be found or the note fails
    value: str          # "2014-03-31", "2009-04", "Oct-Dec 2023"
    reason: str


@dataclass(frozen=True, slots=True)
class TablePages:
    id: str
    doc_sha256: str
    table: str
    first: int                       # 1-based page numbers in the whole report
    last: int
    reason: str                      # "scan; no text to find the TABLE P-1 band"


@dataclass(frozen=True, slots=True)
class EditionRecords:
    word_sources: tuple[WordSourcePlan, ...]
    readings: tuple[ReviewedReading, ...]
    dash_rules: tuple[DashRule, ...]
    notes: tuple[EditionNote, ...]
    table_pages: tuple[TablePages, ...]
    acks: tuple[Acknowledgment, ...]
```

`TablePages` exists because of decision 1 (section 16). The archive holds whole reports only. The
code that finds a table's pages by its header band must work on the FY2022-on QCMR reports, which
have a text layer. For older reports, above all the scans, a record names the pages instead. The
parser then skips the search, and `plan_ocr` sends only those pages to Textract. A wrong range
is caught by the row schema and the checks, as any other misread would be. An unused record
blocks, like every record.

`ERA_OVERRIDE` from design C is gone. A date outside an era's expected range is fixed by widening
the range in code, which is a reviewed change (R1, R3 regrowth finding).

#### Column vocabulary

The old repo described columns with a short flat list of roles in `config/semantics.yml`. A
printed column the list had no word for was filed under the nearest role. QCMR O-2 has three
printed columns under `budget_estimate` (QOBL-Q34). Budget in Brief has two or three change
columns under `increase_decrease` (BIB-Q33). All eight BIRT columns were `year_actual`, and the
year was overwritten afterwards (BSALES-Q24). Period windows went into table names: five wage
subsets and twelve realty transfer subsets (WAGE-Q27, RTT-Q46).

The first version of this design gave each column a name, unit, scale and year, and left
`measure` as a free string. The sketches in section 5 set it to the column name. That left three
defects:

- Nothing said what kind of number a column holds in words that mean the same in every table.
- Section 6.4 picked the canonical value as "the newest edition that prints this (row key,
  measure, value period)". With the measure equal to the column name, a prior-year column never
  matched the earlier edition's current column, so the rule could not work as written. The
  cross-edition checks had the same problem.
- `qcmr_cash.mark_actuals` computed which cash months are actual, and no field of the release row
  carried the answer. `WindowKind` and `MeasureSet` were used in signatures and defined nowhere.

A column is now described by parts drawn from closed lists.

| Part | Question it answers | Values |
|---|---|---|
| kind | What sort of number is it? | actual, budget, projection |
| version | Which budget? | adopted, revised, proposed, target |
| window | What span does it cover? | month, quarter, fiscal year to date, calendar year to date, fiscal year, calendar year, tax year |
| year, month | Which one? | whole years back from the edition; a fiscal month for a column of a month grid |
| quantity | What does it count, if not what the table mainly counts? | 14 values, such as encumbrances, accruals, transactions |
| dims | Which slice does the column carry? | fund, residency, tax base |
| how, of | For a column the publisher computed: how, and from which columns? | difference, percent change, ratio, share, annual growth |

"As of a date" is not a window. `Basis` already says whether a value is a flow or a level, and a
level is read at the end of its window. A second way to say it would allow contradicting pairs.
`Offset` and `Calendar` are gone for the same reason: the window says whether a year is fiscal,
calendar or a tax year, so `year` is a plain count of years back.

```python
# datadesk/core/vocab.py: the closed lists. No table logic.
class Kind(StrEnum):
    ACTUAL = "actual"            # a recorded result
    BUDGET = "budget"            # an authorized or planned amount; always has a Version
    PROJECTION = "projection"    # the publisher's forecast for a window that has not closed


class Version(StrEnum):
    NONE = "none"                # every column that is not a budget
    ADOPTED = "adopted"          # as first enacted: "Adopted", "Original"
    REVISED = "revised"          # as changed after adoption, at the edition's date: "Final", "Revised"
    PROPOSED = "proposed"        # the Mayor's proposal, before Council acts
    TARGET = "target"            # the administration's target: "Target Budget", "YTD Target Plan"


class Window(StrEnum):
    MONTH = "month"
    QUARTER = "quarter"
    FISCAL_YTD = "fiscal_ytd"        # July 1 to the end of the edition's period
    CALENDAR_YTD = "calendar_ytd"    # January 1 to the end of the edition's period
    FISCAL_YEAR = "fiscal_year"
    CALENDAR_YEAR = "calendar_year"
    TAX_YEAR = "tax_year"            # BIRT


class How(StrEnum):
    DIFFERENCE = "difference"            # of[0] minus each later operand
    PERCENT_CHANGE = "percent_change"    # 100 x (of[0] - of[1]) / of[1]
    RATIO = "ratio"                      # 100 x of[0] / of[1]
    SHARE = "share"                      # 100 x part / whole; of[0] is the column that holds the whole
    ANNUAL_GROWTH = "annual_growth"      # compound yearly rate from of[1] to of[0]


class Dim(StrEnum):
    FUND = "fund"                # a registry fund id, or ALL
    RESIDENCY = "residency"      # resident, nonresident, ALL
    TAX_BASE = "tax_base"        # net_income, gross_receipts, ALL


class Quantity(StrEnum):         # set on a column that counts something other than its table's main quantity
    OBLIGATIONS = "obligations"                  # expenditures plus encumbrances (capital tables)
    EXPENDITURES = "expenditures"
    ENCUMBRANCES = "encumbrances"
    NOT_FINANCED = "not_financed"                # capital authorizations with no financing yet
    ENCUMBERED_AUTHORIZATIONS = "encumbered_authorizations"
    AUTHORIZATIONS_MERGED = "authorizations_merged"
    CASH = "cash"                                # cash received, before accruals (collections June close)
    BUDGET_BASIS = "budget_basis"                # the amount as the budget counts it: cash plus accruals
    ACCRUALS = "accruals"                        # accrued to the year, not yet cash
    NOT_ACCRUED = "not_accrued"                  # QCMR cash, FY2017 on
    VOUCHERS_PAYABLE = "vouchers_payable"
    MERGERS = "mergers"                          # QCMR cash expense grid, FY2007 to FY2010
    TRANSACTIONS = "transactions"                # recorded deed transfers ("Records")
    ACCOUNTS = "accounts"                        # taxpayer accounts or filers


ALL = "all"
DIM_VALUES: Mapping[Dim, tuple[str, ...]]        # RESIDENCY and TAX_BASE; FUND is checked against the registry
DEFINITIONS: Mapping[str, str]                   # "kind.actual" -> one line, for the release manifest
```

```python
# datadesk/core/measures.py
class Basis(StrEnum):
    FLOW = "flow"      # amount over the window
    POINT = "point"    # level at the end of the window (positions, balances)


Dims = tuple[tuple[Dim, str], ...]


@dataclass(frozen=True, slots=True)
class Stated:                          # a number the publisher reports
    kind: Kind
    window: Window
    year: int = 0                      # whole years back from the edition's own window: 0, -1, -2, -3
    version: Version = Version.NONE
    month: int | None = None           # fiscal month 1 to 12 (July is 1), for a month column of a grid
    quantity: Quantity | None = None   # None: the table's main quantity; the row says which line
    dims: Dims = ()

    def __post_init__(self) -> None:
        if (self.kind is Kind.BUDGET) != (self.version is not Version.NONE):
            raise ValueError("a budget column has a version, and only a budget column has one")
        if self.month is not None and self.window is not Window.MONTH:
            raise ValueError("only a month column names a fiscal month")
        if self.year > 0:
            raise ValueError("a column never reports a later year than its edition")


@dataclass(frozen=True, slots=True)
class Derived:                         # a number the publisher computed from other printed columns
    how: How
    of: tuple[str, ...]                # operand columns of the same table, in the order `how` reads them;
                                       # a difference takes two or more: of[0] minus each later one
    dims: Dims = ()                    # for a share: which part of the whole


@dataclass(frozen=True, slots=True)
class NotPublished:                    # read and checked, never written to a release
    reason: str


Meaning = Stated | Derived | NotPublished


@dataclass(frozen=True, slots=True)
class MeasureSpec:
    column: str
    meaning: Meaning
    unit: str             # "USD", "positions", "fte", "transactions", "accounts", "percent"
    scale: Decimal        # published value = printed x scale (1, 1000, 1000000)
    basis: Basis


@dataclass(frozen=True, slots=True)
class RowMeasure:
    match: tuple[tuple[str, str], ...]   # key parts a row must carry: (("metric", "positions"),)
    column: str
    spec: MeasureSpec                    # replaces the column's spec on every matching row (change 12)


@dataclass(frozen=True, slots=True)
class MeasureSet:
    columns: tuple[MeasureSpec, ...]
    rows: tuple[RowMeasure, ...] = ()


@dataclass(frozen=True, slots=True)
class Scope:                           # what a description may depend on besides the era; no cell values
    edition: EditionKey                # period and stage
    table: TableId                     # instance parts: fund, zone, window, tax year
    printed: frozenset[str]            # names of the era's columns printed in this table
    actual_through: date               # last day of recorded results: the period end unless a CUTOFF note says so


@dataclass(frozen=True, slots=True, order=True)
class Subject:                         # what a stated value is about, apart from edition, table and column name
    kind: Kind
    version: Version
    quantity: Quantity | None
    dims: Dims
    unit: str                          # added after the Codex review: counts never meet dollars
    start: date | None                 # None for a point value: only the date matters
    end: date
```

What these make impossible:

- a budget column with no version, or a version on a column that is not a budget;
- a derived column that does not name what it was computed from;
- a published column with no description: the only other choice is `NotPublished`, which carries
  a reason and produces no release rows;
- a description that depends on a cell value, because `Scope` holds none.

A table module's `measures(era, scope)` returns a `MeasureSet`. Most tables ignore the scope.
Five need one fact from it:

| Table | What the description depends on | Scope field |
|---|---|---|
| Budget in Brief | the Budget column is adopted in an adopted book and proposed in a proposed one | `edition.stage` |
| Wage by industry | the window the table title names | `table` |
| BIRT | the page's leading tax year | `table` |
| QCMR cash | months through the cutoff are actual, later months are projections (QCASH-Q41) | `actual_through` |
| Collections | remaining and percent collected use the revised budget when the edition prints it (MSCH-Q32) | `printed` |

`scope_for` builds the scope once per parsed table from the document version, the table id, the
printed-column flags and the edition's notes. It replaces `qcmr_cash.mark_actuals`. It returns the
ids of the notes it used, and they join the parser's used set, so an unused `CUTOFF` note still
blocks.

The cash 13th column is the annual sum on flow rows. Opening Balance and CLOSING BALANCE are
levels in every column (QCASH-Q37, Codex review). A month's opening balance is dated at the end of
the month before, so it matches that month's close, and July's is last June's close. Row
overrides on `line=opening_balance` and `line=closing_balance` say so. O-3 does the same for its
`metric=positions` rows, which print counts under dollar headers. Two overrides of one column
must disagree on some key part, so no cell matches two.

`subject_of` turns a stated column and a scope into a `Subject`: kind, version, quantity,
dimensions and dates. The window is left out, so a fiscal year to date that ends June 30 and a
prior-year actual for the same fiscal year are one subject. A point value keeps only its end
date, so a quarter-end count on June 30 and next year's "Year-End Actual" are one subject.
`select_canonical` and the cross-edition checks group by subject (section 6.4).

The lists and types above were written as running Python in `final/vocab/`, and every in-scope
column was declared with them: 272 columns in 23 column sets and 40 layouts, evaluated for 72
sample editions (`final/vocab/COLUMNS.md` lists each one). The tests of section 11.2 pass on
them. Four deliberate mistakes fail: Target Budget described like Adopted Budget, two Budget in
Brief change columns with the same operands, an operand that is not a column, and a budget with
no version. The 35 QSMR columns declared from the two editions read needed no new list member.

Limits of that run. The column lists come from the dossiers, not from the PDFs. 47 of the 272
descriptions are provisional (section 17.3). The Codex review found five descriptions wrong
against the printed pages (section 18.1), which shows the tests check consistency and not print. Two columns are `NotPublished`. Six captions are a
judgment between two readings (section 16, decision 11).

```python
# datadesk/core/context.py
@dataclass(frozen=True, slots=True)
class ParseContext:
    version: DocumentVersion
    period: Period                         # version.edition.period, named once
    fiscal_year: int
    schemas: tuple[RowSchema, ...]         # narrowed to this edition by schema_for()
    registry: Registry
    cell_records: CellRecords
    notes: tuple[EditionNote, ...]         # for this sha only
    table_pages: tuple[TablePages, ...]    # for this sha only

    def schema(self, table: str) -> RowSchema: ...


@dataclass(frozen=True, slots=True)
class Parsed:
    tables: tuple[Table, ...]
    findings: tuple[Finding, ...]
    used: frozenset[str]                   # record ids that changed a cell or a line


@dataclass(frozen=True, slots=True)
class Failed:
    findings: tuple[Finding, ...]


ParseResult = Parsed | Failed
```

A record that was passed in and not used becomes a BLOCK finding `unused_record`. This is one
rule for every record type (from A). It is the lesson of the retired 2022-07 acknowledgment
(MCITY-Q47).

```python
# datadesk/core/tables/catalog.py: the one static list of tables (change 14)
@dataclass(frozen=True, slots=True)
class TableEntry:
    name: str                                            # "qcmr_positions"
    dataset: str                                         # release dataset it feeds
    series: str                                          # EditionKey.series of its documents
    parse: Callable[[Document, ParseContext], ParseResult]
    checks_for: Callable[[str, Period], CheckSet]        # (era name, period): never the parsed table
    eras: tuple[Era, ...]
    measures: Callable[[Era, Scope], MeasureSet]         # column descriptions and row overrides


TABLES: tuple[TableEntry, ...] = (
    TableEntry("qcmr_positions", "qcmr_positions", "qcmr", qcmr_positions.parse,
               qcmr_positions.checks_for, qcmr_positions.ERAS, qcmr_positions.measures),
    # ... one entry per published table; QSMR entries are added in the last build step
)


def entry(name: str) -> TableEntry: ...       # linear search; KeyError names the table
```

`TABLES` is a tuple literal. Importing the module runs no code beyond building it. There is no
dispatch by module-name string and no `PARSER_REVISION`.

```python
# datadesk/core/registry/model.py
class EntityKind(StrEnum):
    DEPARTMENT = "department"
    FUND = "fund"
    CLASS = "class"
    TAX = "tax"
    GROUP = "group"


@dataclass(frozen=True, slots=True)
class Dated:
    value: str
    first_fy: int | None
    last_fy: int | None


class Residual(StrEnum):
    NO = "no"
    YES = "yes"           # "All Other Sectors", "Unclassified", "Other Funds"


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    kind: EntityKind
    names: tuple[Dated, ...]          # official names with fiscal-year ranges
    codes: tuple[Dated, ...] = ()     # department numbers, fund codes, class codes
    parents: tuple[Dated, ...] = ()   # parent id with a year range (QOBL-Q15: Sanitation)
    members: tuple[str, ...] = ()     # GROUP only: "City Rep. / Commerce"
    residual: Residual = Residual.NO


class RelationKind(StrEnum):
    MERGED_INTO = "merged_into"
    SPLIT_FROM = "split_from"
    REPORTED_UNDER = "reported_under"


@dataclass(frozen=True, slots=True)
class Relation:
    kind: RelationKind
    source: str
    target: str
    first_fy: int
    last_fy: int | None
    fund: str | None
    evidence: str


@dataclass(frozen=True, slots=True)
class Alias:
    entity: str
    label: str                        # printed form
    tables: tuple[str, ...]           # never empty: an alias always has a table scope
    first_fy: int | None
    last_fy: int | None
    editions: tuple[str, ...] = ()    # doc shas; required for OCR damage and one-edition misprints


@dataclass(frozen=True, slots=True)
class Registry:
    entities: tuple[Entity, ...]
    relations: tuple[Relation, ...]
    aliases: tuple[Alias, ...]


@dataclass(frozen=True, slots=True)
class Resolved:
    entity_id: str
    via: str                          # "name", "alias", "code"
    conflict: str | None = None       # fund banner name and code disagree (name wins)


@dataclass(frozen=True, slots=True)
class Unknown:
    label: str


@dataclass(frozen=True, slots=True)
class Ambiguous:
    label: str
    candidates: tuple[str, ...]


Resolution = Resolved | Unknown | Ambiguous
```

What this makes impossible:

- a global alias, because an `Alias` always names its tables;
- an OCR misprint that captures rows in other editions, because it names its editions;
- a null id that looks like a match;
- a department that is a parent in one year and a division in another without a dated record.

```python
# datadesk/core/vintage.py
class VintagePolicy(StrEnum):
    ALL_VINTAGES = "all_vintages"          # QCMR, collections, BiB, supplemental, QSMR
    NEWEST_COVERING = "newest_covering"    # BIRT, wage residency
    CURRENT_COLUMN = "current_column"      # sales, RTT, wage by industry
```

```python
# datadesk/core/release/rows.py
class Proof(StrEnum):
    ARITHMETIC = "arithmetic"          # text-layer or reviewed cell in a PASS; says nothing about binding
    OCR_ARITHMETIC = "ocr_arithmetic"  # OCR cell in a PASS: totals tie, digits not proven (change 4)
    ACKNOWLEDGED = "acknowledged"      # in a covered failure; wins over a PASS on the same cell
    UNCHECKED = "unchecked"


class BoundBy(StrEnum):
    CAPTION = "caption"                # the lane's printed caption matched the column spec
    POSITION = "position"              # HEADER_ILLEGIBLE note: lane order only
    DECLARED = "declared"              # TablePages record chose the pages


@dataclass(frozen=True, slots=True)
class ReleaseRow:
    dataset: str
    edition_id: str
    doc_sha256: str
    table: str
    table_instance: str            # "fund=phl_fund_general"
    row_key: str
    row_kind: str
    label_printed: str
    marks: str
    entity_id: str | None
    entity_status: str             # linked, unknown, none
    column: str
    caption_printed: str
    kind: str                      # actual, budget, projection, derived
    version: str                   # adopted, revised, proposed, target; "none" unless kind is budget
    window: str                    # month, quarter, fiscal_ytd, calendar_ytd, fiscal_year, calendar_year, tax_year
    quantity: str | None           # set when the column counts something other than the table's main quantity
    dims: str                      # "fund=phl_fund_general", sorted and joined; empty when the column carries none
    how: str | None                # derived columns: difference, percent_change, ratio, share, annual_growth
    derived_from: str | None       # derived columns: the operand columns, "actual,prior_actual"
    value: Decimal | None          # after scale; None unless the cell is an Amount
    printed: str | None            # verbatim cell text
    mark_meaning: str | None       # "zero", "no_value", "not_applicable"
    unit: str
    scale: Decimal
    value_year: int
    period_start: date
    period_end: date
    basis: str
    reading: str                   # direct, reviewed
    review_id: str | None
    page: int
    box: str                       # "x0,top,x1,bottom" rounded to 0.01 pt
    word_source: str
    proof: Proof
    bound_by: BoundBy
    check_ids: str                 # sorted, joined
    ack_ids: str
    is_canonical: bool
```

The row carries what a reader needs to open the page and see the number (VAL section 6.1). That
is the file hash, page, box, source, method and proof. It also carries the column's description
in the vocabulary of section 2.2, so a reader filters on `kind`, `version` and `window` and never
on a column name. A derived column takes `window`, `value_year` and the period from its first
operand. `NotPublished` columns produce no rows.

## 3. The functional core

The core never opens a file, a socket or a process. It never reads the clock, the environment or
a random source. It holds no module-level mutable state and fills no registry at import time.
Module constants are tuples, frozen dataclasses or `MappingProxyType`. It does no logging; it
returns findings. Every function below is pure and deterministic, and sorts any collection before
returning it.

### 3.1 `checkedtables`

```python
# checkedtables/text.py
def normalize_space(s: str) -> str: ...
    # NBSP, thin spaces, U+2010 and U+2011 hyphens, spaced hyphens -> one form; collapse runs.
    # Every Unicode space is a plain space, U+2010 and U+2011 are "-", a hyphen between two
    # letters loses the spaces around it, and the ends are trimmed.
def normalize_label(s: str) -> str: ...
    # casefold, & -> and, punctuation -> a space except a comma or point between two digits,
    # normalize_space ("Delivery/couriers" -> "delivery couriers", as entities.py:95 did)
def squash(norm: str) -> str: ...
    # remove spaces; matches kerning gaps such as "truc k" and "LI QUOR"
def parse_label(prefix: Sequence[Word], words: Sequence[Word]) -> Label: ...
    # Decision 17 (section 16) narrows the bare digit at step 5: a mark only when small and
    # raised, or when the row schema says the pages use digit footnotes. As built:
    # splits trailing marks until none is left, kept in print order: "(N)", "(*)", "**N", "*",
    # "see note" with any one space or none between its words, ", subtotal", "(19+20)" forms,
    # and one bare digit after a word ("Sheriff 2", ENT-Q07; "CLASS 100" keeps its number);
    # prefix words become line_no; printed keeps every word
def split_line_prefix(line: Line, pattern: str) -> tuple[tuple[Word, ...], Line]: ...
    # leading words that fullmatch `pattern` leave the line before lanes are found, so a column
    # of "23", "24", "26" prefixes can never form a lane (QPOS-Q08, ENT-Q08, QSMR-Q04).
    # The line keeps its box. A line of only prefix words comes back with no words, so no
    # value word is left to seed a lane. text.py names Line only under TYPE_CHECKING and
    # builds the line with dataclasses.replace, because lines.py imports normalize_space.


# checkedtables/lines.py
def group_lines(page: Page) -> tuple[Line, ...]: ...
    # Decision 14 (section 16) adds at step 5: a small word joins the line whose vertical span
    # holds its bottom edge. As built:
    # cluster by word bottom; a word joins a line only if its bottom is within 0.35 x median
    # word height of the line's first word. Never chains: a tall word cannot bridge two lines.
    # Words are taken by bottom, then x0, then ref. The first word opens a line, and a word
    # that does not join the open line opens the next. A line's words sort by x0, lines by top.
def page_lines(page: Page) -> PageLines: ...
def has_values(line: Line) -> bool: ...                  # a value word, as lanes_from_values defines it
    # Decision 15 (section 16) adds value words at step 5: N/A and NA in any case, U+2010
    # alone or as a minus sign, #DIV/0!.
    # The last word that is not a mark word decides. A mark word holds only *, †, ‡, §, #,
    # a backtick and superscript digits. A value word is N/A, NA, a dash placeholder (-, --,
    # an en dash, an em dash), or a digit with nothing else but , . $ % ( ), minus glyphs and
    # trailing marks. "Class 100 Total" has no values; "2.8" then a backtick word has.
def lines_text(lines: Sequence[Line]) -> str: ...
    # each line's text, joined with a newline


# checkedtables/pages.py
def header_band(lines: Sequence[Line], n: int) -> str: ...
def find_runs(pages: Sequence[PageLines], matches: Callable[[str], bool]) -> tuple[PageRun, ...]: ...
    # every maximal run of consecutive pages whose two-line header band matches (change 7)
def only_run(runs: Sequence[PageRun], subject: str) -> PageRun | Finding: ...
    # zero runs: table_not_found; two or more: several_runs. A module that expects a table to
    # break around an inserted page joins runs with its own named rule and says why.
def slice_body(lines: Sequence[Line], body: BodyRule
               ) -> tuple[tuple[Line, ...], tuple[Line, ...], tuple[Line, ...]]: ...
    # (header, body, furniture). Header: lines above the first start match. Body: from it to
    # the first stop match inclusive, or the page end. Furniture: body lines a drop regex matched.


# checkedtables/columns.py
def choose_era(eras: Sequence[Era], header_text: str, on: date) -> Era | Finding: ...
    # exactly one era whose signature regexes all match and whose excludes all miss; then the
    # expected range must contain `on`. Zero or two candidates, or a date outside: a Finding.
def lanes_from_values(body: Sequence[Line]) -> tuple[Lane, ...]: ...
    # Decision 15 (section 16) adds value words at step 5, as at has_values. As built:
    # cluster right edges of value words. A value word is a numeric word with no non-numeric
    # word to its right on its line, so "Class 100 Total" never seeds a lane.
def lanes_from_rules(rules: Sequence[Rule], region: Box) -> tuple[Lane, ...]: ...
    # lanes between consecutive vertical rules that span the region (BiB, supplemental)
def bind_columns(era: Era, header: Sequence[Line], lanes: Sequence[Lane]) -> Binding | Finding: ...
    # 1. Lane caption: header words that overlap the lane horizontally, top to bottom. A group
    #    caption spanning three lanes lands in all three; captions that share one printed line
    #    each land over their own lanes (from B, MCITY-Q12).
    # 2. Add an empty lane for a required caption printed over no values (QCASH-Q35).
    # 3. Each lane's candidates are the specs whose caption regex it contains. The longest
    #    match wins and a spec binds once, so "Prior Year Actual" never binds to "Actual".
    #    Specs with identical captions bind in declared left-to-right order.
    # 4. An unclaimed lane, an unbound required spec, a tie or an out-of-order binding: Finding.
def bind_by_position(era: Era, lanes: Sequence[Lane]) -> Binding | Finding: ...
    # only for pages a HEADER_ILLEGIBLE note names; lane count must equal the era's column count
def cut_line(line: Line, binding: Binding, prefix: tuple[Word, ...]) -> RawRow: ...
    # label words: left of label_right; lane words by right-edge overlap; the rest is stray


# checkedtables/pipeline.py
def cut_pages(layout: Layout, pages: Sequence[PageLines], on: date,
              positional: frozenset[int] = frozenset()) -> CutPages | Finding: ...
    # For each page: split_line_prefix on every body line, slice_body, lanes_from_values (or
    # lanes_from_rules when the page has vertical rules), bind_columns, cut_line. The era is
    # chosen once from the first page's header. Every page must bind the same column names,
    # else a page-level Finding `columns_differ_by_page` (from B). A page-level failure stops
    # the table; line-level problems travel in the result (change 19).


# checkedtables/lex.py
def split_numeric_runs(word: Word) -> tuple[Word, ...]: ...
    # "TAX434,605,553" -> ("TAX", "434,605,553"); "12.3%45,678" -> ("12.3%", "45,678");
    # children get WordRef.child and a box cut in proportion to characters. A cut falls between
    # a letter and a comma-grouped number on either side, so "FY2016" stays whole, and after a
    # "%" or ")" that a digit, "(" or "$" follows. A word with one run comes back unchanged, and
    # so does a word that still holds "(cid:", whose ")" ends a font code (VAL-Q05).
def lex_cell(words: Sequence[Word], col: ColumnSpec, source: SourceKind) -> Cell: ...
    # Decisions 15 and 16 (section 16) change at step 5 which forms are not applicable, a dash
    # or a minus glyph, and when a leading digit joins a grouped number. As built:
    # In order: no words -> Blank; YEAR, CODE and TEXT columns -> Text; one word "N/A" or "NA"
    # -> NotApplicable; one word "-", "--", en or em dash, alone or after one "$" word ("$ -",
    # RTT-Q39) -> Dash(col.dash), so one word that holds a space, such as "$ -", is neither.
    # Marks then leave the end of the cell into Amount.marks: *, †, ‡, §, #, a backtick,
    # Unicode superscript digits, and a last word of one digit, alone or with those glyphs after
    # it ("1*"), under 0.7 of the size of the number word just before it whose bottom sits above
    # that word's bottom (VAL-Q28). That word is one mark as it prints. Not small and raised,
    # such a word reads only alone or after one "$" word, so "1*" is 1 with the mark "*" and
    # "2.8 1*" is Unreadable two_tokens. A "$" word that opens the cell leaves its tokens for
    # the join and comes back in front of the number they give, so "$ $1,234" prints two "$".
    # One token reads through one private reader, which apply_reading also calls. Paired
    # parentheses or one leading minus glyph (-, U+2212, en dash, em dash) is negative, a "$"
    # stands at most once before the digits on either side of that sign, and the digits are
    # [0-9]{1,3}(,[0-9]{3})* or [0-9]+, then an optional .[0-9]+, ASCII only, with a leading
    # zero only as the whole integer part. The Decimal is built from the text, so no decimal
    # point is ever inserted and no float is used.
    # Two tokens join only in a MONEY or PERCENT column on a text layer, after a pair of
    # parentheses around the whole cell leaves, and only when the joined text reads as one
    # number. Shape 1: a bare digit, then 1 or 2 digits and comma groups ("1 37,332,523").
    # Shape 2: a number with a point whose integer part is 1 to 3 digits or comma-grouped, which
    # may carry a "$" and a minus glyph, then one digit ("67,215,504.0 0"). So two bare integers
    # never join (QPOS-Q27), and neither do "1234.5 6", "$1 37,332,523", a detached minus or %,
    # or tokens that end in a comma ("10, 936, 234", decision 12). Parentheses after a "$" word
    # do not wrap the whole cell, so "$ (1 23,456)" and "$ (1.2 3)" do not join, and neither
    # old reader joins them. No shape joins a cell that both old readers refuse, compared on the
    # cell without its marks.
    # A "%" follows col.fmt.percent, and printed decimals equal col.fmt.decimals unless None.
    # Anything else -> Unreadable with the first reason that applies: not_a_number (a glyph no
    # number, sign, mark or separator uses, or no digit), two_tokens (tokens that fit no join
    # shape), sign (a plus, a minus after a digit, an unpaired or misplaced parenthesis such as
    # the ")" of "(1).23", two signs), percent_sign, grouping (what is left is not one strictly
    # grouped number, a misplaced "$", "%" or mark included), decimals.
    # Amount and Unreadable keep the word texts joined by one space and the ref of every word.
def transliteration_ok(seen: str, reading: str) -> bool: ...
    # Decision 13 (section 16.2) tightens this rule at step 5. As built:
    # the digits of `reading`, in order, equal the digit-or-OCR-confusable glyphs of `seen`;
    # B and b read as 8, D, d, O, o, Q and q as 0, & as 6, and every other glyph as nothing,
    # except that a decimal digit that is not ASCII (str.isdecimal, so not a superscript) in
    # either text fails ("1o4.o" -> "104.0" passes; "2918" -> "291.8" passes; "65.8" -> "85.8"
    # fails; "77,500,000" -> "7,500,000" fails; "７7,500,000" -> "7,500,000" fails). A `seen`
    # that holds "(cid:" fails against every reading, since a font code that extraction could
    # not decode is no evidence of any digit ("10(cid:28)" -> "10028" and -> "109" fail, VAL-Q05)


# checkedtables/records.py
def reading_for(cell_words: Sequence[Word], page_words: Sequence[Word], source: SourceKind,
                readings: Sequence[ReviewedReading]) -> ReviewedReading | Finding | None: ...
    # Decision 13 (section 16.2, clause 7) adds at step 5: the two number words of a reading
    # stand within the gap limit of decision 16. As built:
    # A reading is a candidate when its source is `source` and its box, with 1.0 pt of slack,
    # holds a cell word of its file and page. None: no candidate. duplicate_reading: two or
    # more, named by the least id. The page words the box holds must be exactly the cell's
    # words, each as many times, and the cell's words joined by one space in the order given,
    # the order lex_cell joins them in, must equal `seen`, else stale_reading. So a box that
    # holds part of a cell or two cells is stale for each, and a cell whose words share a left
    # edge reads as group_lines ordered them.
    # page_words takes the place of a page number, which every word's ref carries: without
    # them a word that moved into the box could not be seen. The caller passes the words the
    # cells were cut from.
def apply_reading(cell: Cell, reading: ReviewedReading) -> Cell | Finding: ...
    # Decision 13 (section 16.2, clauses 6 and 8) adds at step 5 a test of the source and the
    # confirmation of an Amount. As built:
    # 1. Only an Amount or an Unreadable takes a reading, else reading_refused.
    # 2. The cell's words lie on the reading's file and page and its text equals `seen`, else
    #    stale_reading. transliteration_ok reads both texts from the record, so without this
    #    test a reading could put its value on another cell's words.
    # 3. A None reading gives Unreadable(accepted_by=id). An Unreadable keeps its reason, and
    #    an Amount gets "reviewed_null".
    # 4. Any other reading must pass transliteration_ok(kept, reading), where kept is the
    #    cell's text less the mark words that end an Amount (the whole-word marks, such as a
    #    small raised digit, are the last words of the text, VAL-Q28), and read as one signed
    #    number through the private reader of lex_cell, else reading_refused. So the mark "1"
    #    of "$ 2.8 1" never enters the number, which reads as "2.8" and not "2.81".
    #    No column format applies, so "29.18" reads in a one-decimal column. Then Amount(the
    #    reading's number, the cell's text and words, the reading's source, REVIEWED, the
    #    reading's id, the cell's marks); an Unreadable has none.
    # Every finding of both functions is BLOCK, on the reading's page, with the subject
    # "<doc sha8>:reading:<reading id>". They have no table name for the form of Finding.subject.


# checkedtables/rows.py
def join_rows(upper: RawRow, lower: RawRow) -> RawRow: ...
def starts_known_row(schema: RowSchema) -> Callable[[Line], bool]: ...
def match_rows(raws: Sequence[RawRow], schema: RowSchema) -> RowMatch: ...
    # Walks rows in print order with a stack of open blocks; a row that has children in the
    # schema opens one. Candidates: label matches by norm, then squash, then (with
    # Truncation.UNIQUE_PREFIX) a unique prefix; the first stage with candidates decides, so an
    # exact match always beats a prefix. `within` must be the open block. `follows` must be the
    # row just matched. Exactly one candidate or a Finding. A label-only row with no candidate
    # joins the next row when that gives exactly one candidate (a wrapped label).
    # Parent: the RowDef's parent, else the schema root; the root row itself has none. After the walk: duplicate_row,
    # missing_row for an unmatched REQUIRED RowDef, unknown_row for an unmatched raw row.
    # A truncated match adds a WARN finding naming the full label. No row is ever guessed.
def stray_findings(raws: Sequence[RawRow]) -> tuple[Finding, ...]: ...
    # a numeric stray word is BLOCK (a value outside every lane); other strays are WARN


# checkedtables/grammar.py
def read_grammar(raws: Sequence[RawRow], grammar: RowGrammar,
                 initial: tuple[tuple[str, str], ...] = ()) -> RowMatch: ...
    # See section 3.1.1.


# checkedtables/assemble.py
def assemble(table_id: TableId, cut: CutPages, rows: Sequence[KeyedRow],
             records: CellRecords) -> Assembly: ...
    # lexes every cell with lex_cell and the page's source; applies dash rules, then readings;
    # an OCR value word under the confidence floor with no reading becomes
    # Unreadable("low_confidence"); an Unreadable cell without an accepting reading is a BLOCK
    # finding; duplicate keys or dangling parents give table=None with findings.


# checkedtables/checks/engine.py
def run_checks(tables: Sequence[Table], checks: Sequence[CheckSet]) -> CheckReport: ...
def evaluate(check: Check, tables: Sequence[Table]) -> tuple[Result, ...]: ...
    # expands a check into instances, reads operands, computes the residual exactly in Decimal,
    # compares with the bound. No operand value is ever changed.


# checkedtables/checks/coverage.py
def check_coverage(tables: Sequence[Table], checks: Sequence[CheckSet],
                   results: Sequence[Result]) -> tuple[Finding, ...]: ...
    # check_not_evaluated (BLOCK): a declared check with no result for a table in its scope.
    # check_all_missing (BLOCK): every result of a check on one table is MISSING_OPERAND.
    # total_without_parts (BLOCK): a TOTAL or SUBTOTAL row with an Amount, no children, and no
    # declared ColumnSum or CellsEqual that names it as total (change 2).


# checkedtables/checks/acks.py
def match_acknowledgments(report: CheckReport, acks: Sequence[Acknowledgment],
                          scope: frozenset[str]) -> Gate: ...
    # scope: doc shas this gate decides; expectations for other docs are out of scope


# checkedtables/checks/report.py
def report_rows(report: CheckReport, gate: Gate) -> tuple[tuple[str, ...], ...]: ...
def render_text(report: CheckReport, gate: Gate) -> str: ...


# checkedtables/suggest.py
@dataclass(frozen=True, slots=True)
class Suggestion:
    check: Check
    holds_in: int
    fails_in: int
def suggest_checks(tables: Sequence[Table], tolerance: Tolerance) -> tuple[Suggestion, ...]: ...
    # tries only the six relation classes: adjacent-column row sums and differences, children
    # sums from parent links, column sums into each TOTAL row. Prints chained Python, runs nothing.
def promotions(report: CheckReport, warn_ids: Sequence[str]) -> tuple[Suggestion, ...]: ...
    # WARN checks that passed in every edition of the corpus (change 16)
def render_chain(suggestions: Sequence[Suggestion]) -> str: ...


# checkedtables/testing.py (shipped in the wheel, from B)
def page_from_text(text: str, sha: str, page: int) -> Page: ...
    # lays out a monospace block as Words: one character is 6 pt wide, one line is 12 pt;
    # "**text**" marks bold words; returns style None when the block starts with "#ocr".
    # A word is a run of characters with no ASCII space, so a tab or a non-breaking space
    # stays inside it. A ** that starts a word opens a bold span when the word's next
    # character is not *, and a ** that ends a word closes one when the character before it
    # is not *. Each closer pairs with the nearest unpaired opener to its left on the same
    # line. Every other ** stays in the text, so "**1  **1,234**" gives "**1" and a bold
    # "1,234" (RTT-Q38).
def doc_of(*pages: Page) -> Document: ...
    # pages sorted by number; ValueError for no pages, two files or a repeated page number
```

The kit holds no Philadelphia fact. It knows no fiscal year: `choose_era` and `cut_pages` take a
date, and a measure's year lives in `datadesk`.

#### 3.1.1 `read_grammar`, stated in full

`read_grammar` reads open tables. It walks rows in print order with an implicit `root` level
and the grammar's slots below it. Every level keeps a list of pending rows.

1. A row takes the first rule whose pattern, `values` and `style` match. If a rule needs a style
   and the row's `bold` is `None`, the row gets a BLOCK `style_unavailable` finding and matches
   nothing (change 5).
2. `opens=X`. If X is open with the same normalized label, the slot continues. A continuation
   page that reprints its banners keeps one block (SUPOP-Q20, from A). If X is open with another
   label, X and every deeper slot close without a closing row; their pending rows move up one
   level. Then X opens. A valued opener (a bold department line in FY2010 Water) owns its slot.
3. `closes=(X, ...)`. The rows pending in X and its deeper slots get this row as parent. Those
   slots close. If the slot had a valued owner, the owner is not overridden by a later closer.
   The closing row joins the pending list of the level above.
4. `closes=AllSlots()`. Every level closes, root included. Root's pending rows get this row as
   parent. Root reopens at once, empty, and the closing row joins it (from A's `Grand`).
5. An item, breakdown or memo row joins the pending list of the innermost open level.
6. A heading row has no parent and joins no pending list.
7. A row no rule matches gets a BLOCK `unknown_row` finding and joins nothing.
8. Keys come from slot values, the normalized label and `fixed`. Under `Unique()`, a repeated key
   is `duplicate_row`. Under `Occurrences(block)`, every key that repeats inside one value of the
   block slot gets an `("occurrence", n)` part in print order. A key that does not repeat gets
   none (change 6).
9. `initial` opens slots before the first row. The supplemental activity tables use it to seed
   the agency slot from a single-agency fund banner (ENT-Q32, SUPOP-Q07).

Rule 3 gives every category total its children, and rule 4 gives the grand total the category
totals. Design C's grand total had no children because the category total had already cleared
the slot (R1).

### 3.2 `datadesk.core`

```python
# datadesk/core/periods.py
MONTHS: MappingProxyType[str, int]                            # "january" -> 1
def fiscal_year_of(d: date) -> int: ...                       # July starts the next FY
def fiscal_quarter(period_end: date) -> tuple[int, int]: ...  # Sep 30 -> (FY+1, 1); any other
                                                              # date gives the quarter it is in
def fiscal_period(kind: Window, label_year: int, months: tuple[int, int]) -> Period: ...
    # one place for "FY2026 July to December is calendar 2025" (WAGE-Q07) and for the year
    # basis of each window: month, quarter and calendar year use calendar years; FYTD and
    # fiscal year use July to June (RTT-Q41, WAGE-Q34)
def match_month(token: str) -> int | None: ...                # one-edit match, unique only


# datadesk/core/catalog.py
# datadesk/data/catalog.toml holds one [[source]] table for each listing, with the six fields of
# SourceEntry. Later steps add the lag, the recheck interval, missing_ok, slug exceptions and
# DatasetSpec.
class ListingShape(StrEnum):
    DOCUMENT_FINDER = "document_finder"
    PHILA_DOCUMENTS = "phila_documents"
    MANUAL = "manual"
@dataclass(frozen=True, slots=True)
class SourceEntry:
    id: str                  # "qcmr"
    series: str              # the series of its editions, and the key of its title rule
    shape: ListingShape
    listing_url: str
    category: str            # document-finder: the category whose documents are read
    first_period_end: date   # an edition that ends earlier is never fetched
@dataclass(frozen=True, slots=True)
class SourceCatalog:
    entries: tuple[SourceEntry, ...]           # an id repeated raises ValueError
    def entry(self, id: str) -> SourceEntry: ...   # KeyError for an id it lacks
def load_catalog(text: str) -> SourceCatalog | tuple[Finding, ...]: ...
    # pure; every problem is a BLOCK finding: catalog_not_toml, catalog_unknown_field,
    # catalog_missing_field, catalog_wrong_type (a date and time is not a date),
    # catalog_unknown_shape, catalog_duplicate_id


# datadesk/core/listings/*.py   (one module per publisher page shape)
@dataclass(frozen=True, slots=True)
class ListedLink:
    url: str               # canonical host (admin and www are one asset, QCASH-Q04)
    title: str             # titled anchor wins over the icon anchor (WAGE-Q03)
    position: int          # from 0, in page order
    edition: EditionKey | None
    skip_reason: str | None   # "infographic", "unrelated", "not_a_quarter_end", "unstaged";
                              # a link has an edition or a skip reason, never both or neither
    listed_at: str         # from the shape's parser; document-finder: the upload stamp
@dataclass(frozen=True, slots=True)
class Listing:
    source: str
    url: str
    html_sha256: str       # sha256 of html encoded as UTF-8
    links: tuple[ListedLink, ...]
def parse_listing(source: SourceEntry, url: str, html: str) -> Listing | Finding: ...
    # dispatches on SourceEntry.shape, a closed enum, to document_finder.parse,
    # phila_documents.parse or manual.parse (QSMR: URLs typed into the catalog, QSMR-Q01).
    # A shape parser returns the page's links as PageLink(title, url, listed_at), or a finding.
    # parse_listing reads each title with TITLE_RULES[source.series] and puts each URL on the
    # canonical host. BLOCK findings: listing_unsupported for a shape with no parser yet or a
    # series with no title rule, listing_unreadable from the shape parser.

# datadesk/core/listings/document_finder.py
def parse(source: SourceEntry, text: str) -> tuple[PageLink, ...] | Finding: ...
    # the feed is a JSON list of categories, each with a title and its documents. It reads the
    # documents of the categories titled source.category, in feed order, and nothing else.
    # listed_at is the 14-digit upload stamp in the URL path. Text that is not JSON, no such
    # category, a document with no title or URL, and a URL with no stamp are listing_unreadable.

# datadesk/core/listings/titles.py
TITLE_RULES: MappingProxyType[str, Callable[[str], EditionKey | str]]   # series -> its rule
def qcmr_title(title: str) -> EditionKey | str: ...
    # "infographic" anywhere in the title: "infographic". "Quarterly City Managers Report" or
    # "Quarterly City Manager's Report", a hyphen or an en dash, then "<Month> <D>, <YYYY>" and
    # nothing more: the edition Period(first day of the fiscal quarter, that date) when the date
    # is a quarter end, else "not_a_quarter_end". Any other title: "unrelated". The edition comes
    # from the title alone, never from the URL.


# datadesk/core/watch.py
@dataclass(frozen=True, slots=True)
class ListingFetch:
    source: str
    url: str
    missing_ok: bool       # a fact from the catalog: the current fiscal year's page may 404
@dataclass(frozen=True, slots=True)
class FetchRequest:
    edition: EditionKey
    url: str
    title: str
    listed_at: str
    reason: str            # "new", "revision", "url_reused", "wayback"
@dataclass(frozen=True, slots=True)
class WaybackLookup:
    url: str
    edition: EditionKey
@dataclass(frozen=True, slots=True)
class Gap:
    series: str
    edition: EditionKey
    note: str
@dataclass(frozen=True, slots=True)
class WatchPlan:
    fetch: tuple[FetchRequest, ...]
    wayback: tuple[WaybackLookup, ...]
    gaps: tuple[Gap, ...]
    findings: tuple[Finding, ...]
@dataclass(frozen=True, slots=True)
class PullRequestPlan:
    files: tuple[tuple[str, str], ...]   # (path in the checkout, the file's whole text)
    branch: str
    title: str
    body: str
def plan_listing_fetches(catalog: SourceCatalog, today: date) -> tuple[ListingFetch, ...]: ...
def judge_listing_responses(fetches: Sequence[ListingFetch],
                            statuses: Sequence[int]) -> tuple[Finding, ...]: ...
    # a 404 on a page the catalog marks missing_ok is no finding; any other non-200 is BLOCK
def plan_watch(catalog: SourceCatalog, listings: Sequence[Listing], index: ArchiveIndex,
               today: date) -> WatchPlan: ...
    # Last link per edition wins: the greatest listed_at, and on equal ones the earliest
    # position, since the feed lists its quarters newest first. An edition that ends before its
    # entry's first_period_end is dropped. A kept link is requested unless an indexed version of
    # its own edition holds its URL, with reason "new" when the edition has no version and
    # "revision" when it has one. A URL that another edition holds is still requested, so
    # plan_fetch sees the bytes and rejects them as content_alias. Each link skipped as
    # not_a_quarter_end is a WARN finding with that code. An earlier sha stays as a superseded
    # version (plan_fetch). Step 3 builds the rules above, and step 13 the rules below. A URL
    # whose sha changed under an older listing becomes url_reused plus a WaybackLookup
    # (WAGE-Q10, Q11).
    # Expected editions from the catalog minus indexed ones become gaps, after the declared lag.
    # Indexed URLs not fetched within the catalog's recheck interval become `recheck` requests:
    # the executor downloads and hashes them, and a new sha behind an unchanged listing goes
    # into the pull request as a replaced document (Codex review).
def pick_capture(cdx_rows: Sequence[tuple[str, str, str]], lookup: WaybackLookup) -> FetchRequest | Finding: ...
def with_captures(plan: WatchPlan, picks: Sequence[FetchRequest | Finding]) -> WatchPlan: ...
def plan_pull_request(plan: WatchPlan, today: date) -> PullRequestPlan: ...


# datadesk/core/fetch.py
@dataclass(frozen=True, slots=True)
class Fetched:
    request: FetchRequest
    status: int
    sha256: str | None
    size: int
    page1_text: str | None          # from PdfReader, before any decision
@dataclass(frozen=True, slots=True)
class StoreObject:
    sha256: str
    dest_key: str                   # "pdf/<sha[:2]>/<sha>.pdf"
@dataclass(frozen=True, slots=True)
class Rejection:
    request: FetchRequest
    reason: str                     # "period_mismatch", "content_alias", "http_404", ...
@dataclass(frozen=True, slots=True)
class FetchPlan:
    store: tuple[StoreObject, ...]
    index_add: tuple[DocumentVersion, ...]
    rejections: tuple[Rejection, ...]
    pull_request: PullRequestPlan   # the new index lines, for review
def confirm_period(series: str, page1_text: str, expected: EditionKey,
                   notes: Sequence[EditionNote]) -> Period | Finding: ...
    # per-series title readers: "MONTH OF <month>" plus one "FY YYYY" (MCITY-Q04 to Q07),
    # "PERIOD ENDING" (QCASH-Q05), "Fiscal Year YYYY Collections" (BSALES-Q11), wage months and
    # FY (WAGE-Q14), "Quarterly School Manager Report" and its period ending date (QSMR).
    # A PRINTED_PERIOD note is the only way a mismatch is accepted.
def plan_fetch(fetched: Sequence[Fetched], index: ArchiveIndex,
               notes: Sequence[EditionNote]) -> FetchPlan: ...
    # a sha already indexed under another edition is a content_alias rejection (MSCH-Q01)


# datadesk/core/index.py
# The index file is packages/datadesk/src/datadesk/data/index.jsonl. Each line is one
# DocumentVersion as a JSON object: its keys sorted at every level (section 10), the edition as
# series, period start, period end and stage (never the id alone, which drops the start), dates
# in ISO form, printed_period an object or null, and a newline after every line. The empty
# index is "".
def parse_index(jsonl: str) -> ArchiveIndex: ...         # splits on "\n" alone, then sorts
def render_index(index: ArchiveIndex) -> str: ...        # sorted, one JSON object per line
def add_versions(index: ArchiveIndex, new: Sequence[DocumentVersion]) -> ArchiveIndex | Finding: ...
    # a new version whose sha and edition are indexed adds its URLs to that line, after the
    # URLs it holds, and changes nothing else; the result must pass index_problem, so a sha
    # under another edition is a content_alias finding


# datadesk/core/records.py
def load_records(texts: Sequence[tuple[str, str]]) -> RepoRecords | tuple[Finding, ...]: ...
    # TOML text in. Refuses an acknowledgment whose expectation names an occurrence-numbered
    # row key (change 6) and a reading whose digits fail transliteration_ok.
def records_for(records: RepoRecords, sha: str, period: Period) -> EditionRecords: ...
def unused_records(records: EditionRecords, used: frozenset[str]) -> tuple[Finding, ...]: ...
def drop_noted_lines(lines: Sequence[Line], notes: Sequence[EditionNote],
                     page: int) -> tuple[tuple[Line, ...], frozenset[str]]: ...
    # removes a line whose text equals a DROP_LINE note's printed text on that page
def illegible_pages(notes: Sequence[EditionNote], sha: str) -> tuple[frozenset[int], frozenset[str]]: ...
def declared_run(records: Sequence[TablePages], table: str) -> tuple[PageRun | None, frozenset[str]]: ...
    # the run a TablePages record names for this table, and its id for the used set


# datadesk/core/registry/resolve.py
def resolve(reg: Registry, kind: EntityKind, label: Label, scope: LookupScope) -> Resolution: ...
    # LookupScope(table, fiscal_year, edition). Candidates: official names valid in that FY,
    # plus aliases whose tables include `table`, whose FY range holds it and whose editions,
    # if any, include `edition`. Exact on norm, then on squash. No prefix or fuzzy rule.
def resolve_fund(reg: Registry, banner: str, code: str | None, fiscal_year: int) -> Resolution: ...
def labels_for(reg: Registry, entity: str, scope: LookupScope) -> tuple[str, ...]: ...
    # every printed form the registry allows for this entity in this table, year and edition
def normalize_printed_code(code: str) -> str: ...      # "010" -> "01", "01-011" kept
def lint_registry(reg: Registry, schemas: Sequence[RowSchemaSource]) -> tuple[Finding, ...]: ...


# datadesk/core/rowschemas.py
def load_row_schema(table: str, toml_text: str) -> RowSchemaSource | tuple[Finding, ...]: ...
    # a [[row]] with `entity` and `labels` is refused: one home per spelling (change 11)
def schema_for(source: RowSchemaSource, version: DocumentVersion, reg: Registry) -> RowSchema: ...
    # keeps RowDefs whose periods hold the edition and whose `absent_editions` do not name its
    # sha (MSCH-Q23); fills an entity row's labels from labels_for() and the row's `forms`
    # templates ("{name} Total", "{name} - Total", QPOS-Q37)


# datadesk/core/measures.py
def scope_for(version: DocumentVersion, table: TableId, printed: frozenset[str],
              notes: Sequence[EditionNote]) -> tuple[Scope, frozenset[str]]: ...
    # actual_through is the period end, or the value of a CUTOFF note for this sha (QCASH-Q41);
    # returns the note ids used, which join the parser's used set. It never sees a cell.
def measure_for(measures: MeasureSet, row: RowKey, column: str) -> MeasureSpec: ...
def period_of(stated: Stated, scope: Scope) -> Period: ...
    # the dates a stated column covers, through periods.fiscal_period
def subject_of(spec: MeasureSpec, scope: Scope) -> Subject | None: ...
    # None for Derived and NotPublished: computed columns are never matched across editions
def description(meaning: Meaning) -> tuple[object, ...]: ...   # the comparable form the catalog test uses


# datadesk/core/words_audit.py
def compare_sources(primary: Page, other: Page, tolerance_pt: float) -> tuple[Finding, ...]: ...
    # signed numeric tokens at overlapping boxes that differ in any character, including a sign
    # or decimal point, and numeric tokens one source has and the other does not; each is a
    # BLOCK finding `source_disagreement` naming the box and both texts. A ReviewedReading clears
    # it, and may accept the other source's token at that box (Codex review)


# datadesk/core/parse_plan.py
@dataclass(frozen=True, slots=True)
class WordJob:
    doc_sha256: str
    pages: tuple[int, ...]               # empty means every page
    source: SourceKind
    compare: SourceKind | None           # change 3: also extract this source for these pages
    cache_key: str
@dataclass(frozen=True, slots=True)
class ParseJob:
    doc_sha256: str
    table: str                           # a TABLES entry name, looked up in a static tuple
    word_keys: tuple[str, ...]
    compare_keys: tuple[str, ...]
    cache_key: str                       # sha256(word keys, code tree sha, record and registry shas)
@dataclass(frozen=True, slots=True)
class ParsePlan:
    extract: tuple[WordJob, ...]         # word jobs not in the cache, text layer only
    ocr_missing: tuple[WordJob, ...]     # OCR pages with no archived Textract response
    parse: tuple[ParseJob, ...]          # parse jobs not in the parse cache
    reuse: tuple[ParseJob, ...]          # parse results served from the cache
def plan_parse(snapshot: ParseSnapshot) -> ParsePlan: ...
def plan_ocr(missing: Sequence[WordJob], config: str) -> OcrPlan: ...
    # pages, Textract config and the archive key for each response; printed with a page count
def parse_context(job: ParseJob, repo: RepoSnapshot) -> ParseContext: ...
def run_parse_job(job: ParseJob, doc: Document, compare: Document | None,
                  ctx: ParseContext) -> ParseResult: ...
    # TABLES lookup, then entry.parse; when `compare` is given, compare_sources runs on each
    # compared page and its findings join the result; readings that settle a disagreement
    # count as used


# datadesk/core/ocr.py
def textract_to_document(responses: Sequence[tuple[int, bytes]], sha: str, tool: str) -> Document: ...


# datadesk/core/codec.py
def encode_document(doc: Document) -> bytes: ...
def decode_document(data: bytes) -> Document: ...
def encode_parse_result(result: ParseResult) -> bytes: ...
def decode_parse_result(data: bytes) -> ParseResult: ...


# datadesk/core/checks/series.py
def cross_edition_checks(dataset: str, tables: Sequence[tuple[DocumentVersion, Table]]) -> CheckSet: ...
    # WARN severity. One generic relation, same_subject_agrees: two editions that print the same
    # (table, instance, row key, Subject) should print the same value. It covers prior columns
    # against earlier editions, the adopted budget across a year's quarters, and Q4 against the
    # next FY-1 actual. Declared beside it: FYTD deltas, and the occurrence counts of a list
    # table's labels between editions
def checks_for_document(entry: TableEntry, tables: Sequence[Table], period: Period) -> tuple[CheckSet, ...]: ...
    # entry.checks_for(table.era, period) for each table, plus the family's cross-table checks


# datadesk/core/vintage.py
def select_canonical(policy: VintagePolicy, rows: Sequence[ReleaseRow]) -> tuple[ReleaseRow, ...]: ...
    # groups rows by (table, instance, row key, window, Subject), never by column name


# datadesk/core/tables/<table>.py: the interface every table module has (section 5)
ERAS: tuple[Era, ...]
def measures(era: Era, scope: Scope) -> MeasureSet: ...
def parse(doc: Document, ctx: ParseContext) -> ParseResult: ...
def checks_for(era: str, period: Period) -> CheckSet: ...


# datadesk/core/tables/collections_common.py
def dedupe_overprint(page: Page) -> Page: ...           # removes words, never creates them (5.3)
def attach_stacked_labels(raws: Sequence[RawRow]) -> tuple[RawRow, ...]: ...
def caption_year_findings(binding: Binding, header: Sequence[Line], period: Period,
                          notes: Sequence[EditionNote]) -> tuple[tuple[Finding, ...], frozenset[str]]: ...
def money_measures(era: Era, scope: Scope) -> MeasureSet: ...
    # remaining and percent collected name revised_budget when scope.printed holds it, else budget


# datadesk/core/tables/qcmr_cash.py
def split_grids(lines: Sequence[Line]) -> tuple[tuple[Line, ...], tuple[Line, ...]] | Finding: ...
    # cut page 1 at "REVENUES" and "E(X|(cid:N)| )PENSES AND|ANO OBLIGATIONS"; both required
def month_kind(scope: Scope, month: int) -> Kind: ...
    # ACTUAL when the fiscal month ended on or before scope.actual_through, else PROJECTION
def find_balance_page(pages: Sequence[PageLines], run: PageRun) -> PageLines | Finding: ...
    # section 6.2


# datadesk/core/tables/rtt.py
def split_zones(lines: Sequence[Line]) -> tuple[tuple[str, tuple[Line, ...]], ...] | Finding: ...
def cross_checks(tables: Sequence[Table]) -> CheckSet: ...   # property total = location total


# datadesk/core/tables/wage_industry.py
def period_kind(title: str, header: str, version: DocumentVersion,
                notes: Sequence[EditionNote]) -> tuple[Window, Period] | Finding: ...


# datadesk/core/tables/bib_revenue_schedule.py
def grammar_for(version: DocumentVersion, sources: Sequence[SourceKind]) -> RowGrammar: ...
    # TEXT_GRAMMAR when every schedule page has a text layer, SCAN_GRAMMAR otherwise (6.1)


# datadesk/core/release/*.py
def to_release_rows(dataset: DatasetSpec, version: DocumentVersion, table: Table,
                    measures: MeasureSet, proof: ProofMap) -> tuple[ReleaseRow, ...]: ...
    # DatasetSpec.withheld lists row keys parsed and checked but not written (BSALES-Q32)
def proof_of(report: CheckReport, gate: Gate, tables: Sequence[Table]) -> ProofMap: ...
def verify_cell_provenance(table: Table, doc: Document, cut_formats: Sequence[ColumnSpec],
                           readings: Sequence[ReviewedReading]) -> tuple[Finding, ...]: ...
def encode_parquet(rows: Sequence[ReleaseRow]) -> bytes: ...   # fixed schema, no timestamps
def encode_csv(rows: Sequence[ReleaseRow]) -> bytes: ...
def diff_rows(previous: Sequence[ReleaseRow], current: Sequence[ReleaseRow]) -> RowDiff: ...
    # keyed by (dataset, edition_id, table, table_instance, row_key, column): added, removed,
    # value_changed, entity_changed, key_changed for a document present in both releases
def plan_release(inputs: ReleaseInputs) -> ReleasePlanned | ReleaseBlocked: ...
    # ReleaseInputs: checked datasets with one Gate per (dataset, edition), the previous
    # manifest and its rows, release id, created_at, and the accepted diff sha if any
```

`encode_parquet` imports `pyarrow`. That is computation over values, so it sits in the core. A
test asserts byte-identical output for identical input (section 10).

### 3.3 `phillyledger`

```python
# phillyledger/manifest.py
def parse_manifest(text: str) -> Manifest: ...
def render_manifest(m: Manifest) -> str: ...      # sorted keys, stable


# phillyledger/plan.py
def plan_load(manifest: Manifest, request: LoadRequest, cached: frozenset[str]) -> LoadPlan: ...
def cite(manifest: Manifest, row: Mapping[str, object]) -> str: ...


# phillyledger/lineage.py (moved as is from gov_budget_data/lineage.py)
def predecessor_spans(registry_rows: Sequence[Mapping[str, object]], entity: str) -> tuple[Span, ...]: ...
```

## 4. The imperative shell

Every effect sits behind one `typing.Protocol` with one real adapter and one fake. There are six
ports. The `Clock` port is gone: `cli.main` reads the time once and passes values down (change 20).

```python
# datadesk/shell/ports.py
class Http(Protocol):
    def get(self, url: str) -> HttpResponse: ...     # any status is a result; transport errors raise


@dataclass(frozen=True, slots=True)
class CreateOnly:
    pass                               # S3 PutObject with If-None-Match: *


@dataclass(frozen=True, slots=True)
class IfMatch:
    etag: str | None                   # None: the key must not exist yet


Condition = CreateOnly | IfMatch


class PreconditionFailed(Exception): ...


class ObjectStore(Protocol):
    def put(self, key: str, data: bytes, public: bool, condition: Condition) -> str: ...  # new etag
    def head(self, key: str) -> str | None: ...                                          # etag
    def get(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def list(self, prefix: str) -> tuple[str, ...]: ...   # one caller: archived OCR keys for plan_parse


class OcrService(Protocol):
    def analyze(self, page_png: bytes, config: str) -> bytes: ...   # raw Textract JSON


class PdfReader(Protocol):
    def words(self, pdf: bytes, sha256: str, pages: Sequence[int]) -> Document: ...
    def page1_text(self, pdf: bytes) -> str: ...
    def render(self, pdf: bytes, page: int, dpi: int) -> bytes: ...  # for OCR and review images


class LocalCache(Protocol):
    def get(self, key: str) -> bytes | None: ...
    def put(self, key: str, data: bytes) -> None: ...
    def keys(self) -> frozenset[str]: ...


class GitHost(Protocol):
    def open_pull_request(self, plan: PullRequestPlan) -> str: ...  # files, branch, title, body
```

`textract_to_document` is a pure function in `datadesk.core.ocr`; only the call to Textract is an
effect. Archived responses live privately at `ocr/<sha>/<page>/<config-hash>.json` (VAL-Q07).

The shell reads repository files once. `gather_repo(root)` returns a `RepoSnapshot` of text:
TOML records, row schemas, the registry, the catalog and the archive index. Pure loaders turn the
text into values. An executor then holds the snapshot and the plan, and passes both to pure
functions only (R3 purity finding).

### 4.1 `watch`

```python
# datadesk/shell/run_watch.py
def run_watch(deps: Deps, repo: RepoSnapshot, today: date) -> str | None:
    catalog, index = repo.catalog, repo.index
    fetches = plan_listing_fetches(catalog, today)                          # pure
    responses = [deps.http.get(f.url) for f in fetches]                     # effect
    problems = judge_listing_responses(fetches, [r.status for r in responses])   # pure
    listings = [parse_listing(catalog.entry(f.source), f.url, r.text)      # pure per response
                for f, r in zip(fetches, responses) if r.status == 200]
    plan = plan_watch(catalog, listings, index, today)                      # pure
    picks = [pick_capture(parse_cdx(deps.http.get(cdx_url(w.url)).text), w)  # effect, then pure
             for w in plan.wayback]
    plan = with_captures(plan, picks)                                       # pure
    pr = plan_pull_request(replace(plan, findings=(*plan.findings, *problems)), today)  # pure
    return deps.git.open_pull_request(pr) if pr.files else None
```

The pull request carries `watch/plan-<date>.json` (the plan itself) and a readable summary.
`watch` downloads no PDF and parses nothing. The executor branches only on HTTP status, which is
the effect's outcome. Whether a 404 matters is decided by `judge_listing_responses` from the
catalog's `missing_ok` fact (R2: the port has no `accept_404` flag).

### 4.2 `fetch`

```python
# datadesk/shell/run_fetch.py
def run_fetch(deps: Deps, plan: WatchPlan, repo: RepoSnapshot) -> FetchPlan:
    held: dict[str, bytes] = {}                                   # bytes by sha, in memory
    fetched: list[Fetched] = []
    for req in plan.fetch:
        r = deps.http.get(req.url)
        if r.status != 200:
            fetched.append(Fetched(req, r.status, None, 0, None))
            continue
        sha = sha256(r.body).hexdigest()
        held[sha] = r.body
        fetched.append(Fetched(req, 200, sha, len(r.body), deps.pdf.page1_text(r.body)))
    result = plan_fetch(fetched, repo.index, repo.records.notes)  # pure: every decision
    for obj in result.store:
        deps.store.put(obj.dest_key, held[obj.sha256], public=True)
    deps.git.open_pull_request(result.pull_request)
    return result
```

Download, hash and decide is a loop of small plans, as the principles allow. Bytes stay in memory
keyed by hash until `plan_fetch` decides; nothing is staged and copied (R2). A watch pull request
adds a handful of PDFs, so memory is not a concern. The index change goes through a pull request,
so `GitHost` needs one method.

### 4.3 `ocr`

```python
# datadesk/shell/run_ocr.py
def run_ocr(deps: Deps, plan: OcrPlan) -> tuple[str, ...]:
    written: list[str] = []
    for item in plan.items:
        pdf = deps.store.get(item.pdf_key)
        image = deps.pdf.render(pdf, item.page, item.dpi)
        deps.store.put(item.archive_key, deps.ocr.analyze(image, item.config), public=False)
        written.append(item.archive_key)
    return tuple(written)


# datadesk/shell/cli.py (excerpt)
def ocr_command(deps: Deps, repo: RepoSnapshot, spend: bool) -> int:
    plan = plan_ocr(plan_parse(parse_snapshot(deps, repo)).ocr_missing, TEXTRACT_CONFIG)
    print(render_ocr_plan(plan))                     # pages, documents and the page count to pay for
    if not spend:
        return 0
    run_ocr(deps, plan)
    return 0
```

Textract runs only here. No other command calls `OcrService`, so `watch`, `parse` and `release`
can never spend money (change 15). The CLI flag decides whether to spend.
No executor branches on data to decide it.

### 4.4 `parse`

```python
# datadesk/shell/run_parse.py
def run_parse(deps: Deps, repo: RepoSnapshot) -> ParseOutcome | OcrNeeded:
    plan = plan_parse(parse_snapshot(deps, repo))                       # pure
    if plan.ocr_missing:
        return OcrNeeded(plan.ocr_missing)
    for job in plan.extract:                                            # only what the plan lists
        pdf = deps.store.get(pdf_key(job.doc_sha256))
        deps.cache.put(job.cache_key, encode_document(deps.pdf.words(pdf, job.doc_sha256, job.pages)))
    results: dict[str, ParseResult] = {}
    for job in plan.reuse:
        results[job.cache_key] = decode_parse_result(need_bytes(deps.cache.get(job.cache_key)))
    for job in plan.parse:
        doc = merged_document(deps.cache, job.word_keys)                # decode and join pages
        other = merged_document(deps.cache, job.compare_keys) if job.compare_keys else None
        result = run_parse_job(job, doc, other, parse_context(job, repo))   # pure
        deps.cache.put(job.cache_key, encode_parse_result(result))
        results[job.cache_key] = result
    return ParseOutcome(plan, results)
```

`plan_parse` decides which words to extract, which OCR responses exist and which parse results are
cached. The executor does not re-read the cache to decide again (R1, R2). `merged_document` builds
one `Document` whose pages each come from the declared source. A page never appears twice.

### 4.5 `release`

```python
# datadesk/shell/run_release.py
def run_release(deps: Deps, planned: ReleasePlanned) -> Released:
    plan, blobs = planned.plan, planned.blobs                 # plan lists files by sha only
    prefix = f"releases/{plan.release_id}"
    for f in plan.files:
        put_immutable(deps.store, f"{prefix}/staged/{f.path}", blobs[f.sha256], f.sha256, public=False)
    for f in plan.files:                                      # gate step 2: what was staged
        if sha256(deps.store.get(f"{prefix}/staged/{f.path}")).hexdigest() != f.sha256:
            raise StagingCorrupted(f.path)
    for f in plan.files:
        put_immutable(deps.store, f"{prefix}/{f.path}", blobs[f.sha256], f.sha256, public=True)
    deps.store.put("releases/latest.json", blobs[plan.pointer.new_sha256], public=True,
                   condition=IfMatch(plan.pointer.previous_etag))   # PreconditionFailed: replan
    return Released(plan.manifest)


def put_immutable(store: ObjectStore, key: str, data: bytes, sha: str, public: bool) -> None:
    try:
        store.put(key, data, public, condition=CreateOnly())
    except PreconditionFailed:                                # a retry or a racing run wrote it
        if sha256(store.get(key)).hexdigest() != sha:
            raise


# datadesk/shell/cli.py (excerpt)
def release_command(deps: Deps, repo: RepoSnapshot, release_id: str, now: datetime,
                    accepted_diff: str | None) -> int:
    parsed = run_parse(deps, repo)                            # editions that need OCR come back
    report_ocr_needed(parsed.ocr_needed)                      # as withheld, not as a stop
    checked = check_all(parsed, repo)                         # pure: checks, coverage, gates
    previous = load_previous_release(deps.store)              # effect: manifest, rows, pointer etag
    outcome = plan_release(ReleaseInputs(checked, previous, release_id, now, accepted_diff))
    if isinstance(outcome, ReleaseBlocked):
        return report_blocked(outcome)
    run_release(deps, outcome)
    return 0
```

`ReleasePlan` holds `files` (path, sha, size), `manifest`, `diff`, `withheld` and `pointer`. The
bytes travel beside it in `ReleasePlanned.blobs`, keyed by sha. A dry run prints the plan without
megabytes of Parquet (change 13). The release executor runs no parse. The CLI composes parse,
check and release, and each step is a value the next one reads (R1, R2).

Gating is per (dataset, edition) (change 17). `plan_release` withholds a blocked edition, keeps
the previous release's rows for it, and lists it in the release notes. An edition that still needs
OCR is withheld the same way and the others release. A `Withdrawal` record (section 18) stops the
carry-forward: rows it names are removed and the release notes point to the correction. The
pointer moves only if its etag is the one read when the release was planned, so a slower run
cannot undo a newer release. A key change or an entity change in a
document present in both releases blocks unless `--accept-diff <sha>` names the sha of the
reviewed diff (from A).

### 4.6 The reader's `load`

```python
# phillyledger/api.py
def load(dataset: str, release: str | None = None, cache_dir: Path | None = None) -> pa.Table:
    shell = default_shell(cache_dir)                            # http and cache adapters
    manifest = parse_manifest(shell.http.get(manifest_url(release)).text)
    plan = plan_load(manifest, LoadRequest(dataset, "parquet"), shell.cache.keys())   # pure
    for d in plan.downloads:
        body = shell.http.get(d.url).body
        if sha256(body).hexdigest() != d.sha256:
            raise IntegrityError(d.url)
        shell.cache.put(d.sha256, body)
    body = need_bytes(shell.cache.get(plan.open_sha256))
    if sha256(body).hexdigest() != plan.open_sha256:                # verify on use, not only on download
        raise IntegrityError(plan.open_sha256)
    return pq.read_table(pa.BufferReader(body))
```

`path`, `datasets` and `cite` follow the same shape. Pinning is a `release` argument plus a
`phillyledger.lock` file read by the shell. The reader's cache port has the same three methods
as the desk's, so `load` uses `keys()` (R2).

## 5. How a table parser is written

A table module has five parts, always in this order: column eras, `measures`, the row schema or
grammar, `parse`, and `checks_for(era, period)`. It imports `checkedtables`, its family helper and
`datadesk.core` values. It imports nothing from the shell and no other table module.

`parse` follows one path of about eight calls: `find_runs` and `only_run`, `cut_pages`,
`match_rows` or `read_grammar`, `assemble`, then findings. `cut_pages` holds the per-page loop
that design C repeated in every module (R2 counted about 500 copied lines).

`checks_for` takes the era name and the period and never the parsed table. So a check cannot
choose its members from the values it is about to judge (R3). Section 11.3 tests this.

The examples below are complete modules. They have not been run. Line counts exclude the
docstring and blank lines.

### 5.1 QCMR positions (Table P-1)

Closed row schema, one era, exact counts, rows from two or three pages (QPOS section 11).

```python
# datadesk/core/tables/qcmr_positions.py
"""QCMR Table P-1: full-time positions by department. Whole QCMR PDF in, one Table out."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal

from checkedtables.assemble import assemble
from checkedtables.checks.dsl import (EXACT, CheckSet, ChildrenSum, Kinds, RowDifference,
                                      RowSum, declare)
from checkedtables.columns import ColumnSpec, Era, NumberFormat
from checkedtables.kinds import ValueKind
from checkedtables.lines import Line, page_lines
from checkedtables.pages import BodyRule, find_runs, only_run
from checkedtables.pipeline import Layout, cut_pages
from checkedtables.rows import match_rows, starts_known_row, stray_findings
from checkedtables.table import Finding, RowKind, TableId
from checkedtables.words import Document

from datadesk.core.context import Failed, ParseContext, Parsed, ParseResult
from datadesk.core.domain import Period
from datadesk.core.measures import (Basis, Derived, Meaning, MeasureSet, MeasureSpec, Scope,
                                    Stated)
from datadesk.core.records import declared_run, illegible_pages
from datadesk.core.vocab import ALL, Dim, How, Kind, Version, Window

TABLE = "qcmr_positions"
_COUNT = NumberFormat(decimals=0)
_GROUPS = (("prior", r"Year.?End\s+Actual"), ("adopted", r"Adopted"),
           ("actual", r"Month.?End\s+Actual"))
_FUNDS = (("general", r"General"), ("other", r"Other"), ("total", r"Total"))

COLUMNS: tuple[ColumnSpec, ...] = (
    *(ColumnSpec(f"{g}_{f}", rf"{gcap}.*{fcap}", ValueKind.COUNT, _COUNT)
      for g, gcap in _GROUPS for f, fcap in _FUNDS),
    ColumnSpec("over_under", r"\(Over\)\s*Under", ValueKind.COUNT, _COUNT),
)
_FUND_COLUMNS = tuple(c.name for c in COLUMNS if c.name != "over_under")
_ALL_COLUMNS = tuple(c.name for c in COLUMNS)
ERAS = (Era("p1_ten_columns", signature=(r"Adopted", r"\(Over\)\s*Under"), columns=COLUMNS,
            expected=(date(2007, 7, 1), None)),)

_FURNITURE = (r"^TABLE\s+P-1", r"^FULL.TIME\s+POSITIONS", r"^\(\d+\)\s", r"^Notes?:")
_LINE_NO = r"(?:\d{1,2}|I)"          # "23 Civilian", "I Uniform" (QPOS-Q08)


_FUND_IDS = {"general": "phl_fund_general", "other": "phl_fund_other", "total": ALL}
_GROUP_MEANING = {
    "prior": Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1),       # the level when last year ended
    "adopted": Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED),
    "actual": Stated(Kind.ACTUAL, Window.QUARTER),                   # the level when the quarter ended
}


def measures(era: Era, scope: Scope) -> MeasureSet:
    def count(column: str, meaning: Meaning) -> MeasureSpec:
        return MeasureSpec(column, meaning, unit="positions", scale=Decimal(1), basis=Basis.POINT)

    by_fund = tuple(
        count(f"{g}_{f}", replace(_GROUP_MEANING[g], dims=((Dim.FUND, _FUND_IDS[f]),)))
        for g in _GROUP_MEANING for f in _FUND_IDS)
    variance = count("over_under", Derived(How.DIFFERENCE, of=("adopted_total", "actual_total")))
    return MeasureSet((*by_fund, variance))


def _is_p1(band: str) -> bool:
    return "TABLE P-1" in band.upper()


def _is_grand_total(line: Line) -> bool:
    return "TOTAL ALL FUNDS" in line.text.upper()


def parse(doc: Document, ctx: ParseContext) -> ParseResult:
    schema = ctx.schema(TABLE)
    pages = tuple(page_lines(p) for p in doc.pages)
    declared, pages_used = declared_run(ctx.table_pages, TABLE)          # older reports only
    run = declared or only_run(find_runs(pages, _is_p1), f"{doc.sha256[:8]}:{TABLE}")
    if isinstance(run, Finding):
        return Failed((run,))
    body = BodyRule(start=starts_known_row(schema), stop=_is_grand_total,
                    drop=_FURNITURE, prefix=_LINE_NO)
    positional, notes_used = illegible_pages(ctx.notes, doc.sha256)   # scans, with a note only
    cut = cut_pages(Layout(ERAS, body), run.take(pages), ctx.period.end, positional)
    if isinstance(cut, Finding):
        return Failed((cut,))
    matched = match_rows(cut.raws, schema)
    built = assemble(TableId(TABLE), cut, matched.rows, ctx.cell_records)
    findings = tuple(sorted((*cut.findings, *matched.findings, *built.findings,
                             *stray_findings(cut.raws))))
    if built.table is None:
        return Failed(findings)
    return Parsed((built.table,), findings, built.used | notes_used | pages_used)


def checks_for(era: str, period: Period) -> CheckSet:
    return (
        declare(TABLE, tolerance=EXACT)
        .add(RowSum("fund_split_prior", total="prior_total",
                    parts=("prior_general", "prior_other")))
        .add(RowSum("fund_split_adopted", total="adopted_total",
                    parts=("adopted_general", "adopted_other")))
        .add(RowSum("fund_split_actual", total="actual_total",
                    parts=("actual_general", "actual_other")))
        .add(RowDifference("variance", minuend="adopted_total", subtrahend="actual_total",
                           result="over_under"))
        .add(ChildrenSum("civilian_plus_uniform", parents=Kinds((RowKind.SUBTOTAL,)),
                         columns=_ALL_COLUMNS))
        .add(ChildrenSum("all_funds_total", parents=Kinds((RowKind.TOTAL,)),
                         columns=_FUND_COLUMNS))
    )
```

95 lines. The row schema is data. Department spellings are not in it (change 11):

```toml
# datadesk/data/rows/qcmr_positions.toml
table = "qcmr_positions"
root = "line=total_all_funds"     # every department hangs under the grand total (change 2)
drop = ['^\(\d+\)\s']

[[row]]
key = "dept=phl_dept_police"
kind = "subtotal"
entity = "phl_dept_police"
forms = ["{name} Total", "{name} - Total"]    # QPOS-Q37; "Police" itself lives in the registry

[[row]]
key = "breakdown=civilian|dept=phl_dept_police"
kind = "breakdown"
parent = "dept=phl_dept_police"
within = "dept=phl_dept_police"
labels = ["Civilian"]

[[row]]
key = "dept=phl_dept_streets"
kind = "item"
entity = "phl_dept_streets"
periods = [["2007-07-01", "2013-06-30"], ["2025-07-01", ""]]

[[row]]
key = "group=streets_with_sanitation"
kind = "item"
entity = "phl_group_streets_sanitation"
periods = [["2017-07-01", "2025-06-30"]]

[[row]]
key = "line=total_all_funds"
kind = "total"
labels = ["TOTAL ALL FUNDS"]
```

```toml
# datadesk/data/registry/aliases/qcmr_positions.toml
[[alias]]
entity = "phl_dept_finance"
label = "Binance"                           # OCR damage, bound to one file (QPOS-Q09)
tables = ["qcmr_positions"]
editions = ["<sha of FY2012 Q3>"]           # the old continuity test pins FY2012 Q3

[[alias]]
entity = "phl_group_streets_sanitation"
label = "Streets"                           # P-1 only, FY2018 to FY2025 (QPOS-Q12, ENT-Q02)
tables = ["qcmr_positions"]
first_fy = 2018
last_fy = 2025
```

What the module shows:

- Columns bind by caption. A lost column on a scan is a binding finding, never a shifted role.
  The unsure QPOS-Q02 is settled on the first run.
- The `prefix` rule takes "23" and "I" off a line before lanes are found. A column of OCR
  prefixes cannot form a lane (R3, QPOS-Q08).
- Civilian and Uniform match only inside their parent's block. Indentation is never read
  (QPOS-Q07).
- `all_funds_total` is a children sum under the schema root. The engine never counts a total
  among its own parts, and Civilian is Police's child, so nothing is counted twice (R1, R2).
- The FY2010 blank variance cells lex to `Blank`. `variance` then reports `MISSING_OPERAND`,
  which never blocks (QPOS-Q21, Q22).
- The seven acknowledgments key on `all_funds_total` or `civilian_plus_uniform`, the row key and
  the column name. Their pages are whole-report pages (QPOS-Q31 is gone).

### 5.2 Supplemental revenues (the hardest supplemental table)

`supplemental_revenues` has the deepest hierarchy, multi-page parent sections, the offset
Sub-Total label and 21 of the family's 26 acknowledgments (SUPOP section 11). It is an open
table, so it uses a grammar.

```python
# datadesk/core/tables/supp_revenues.py
"""Supplemental Report, Statement of Net Revenue(s): one table per fund, often several pages."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from checkedtables.assemble import assemble
from checkedtables.checks.dsl import (EXACT, CheckSet, ChildrenSum, Kinds, Ratio,
                                      RowDifference, declare)
from checkedtables.columns import ColumnSpec, Era, NumberFormat
from checkedtables.grammar import AllSlots, RowGrammar, RowRule, Style, Values, read_grammar
from checkedtables.kinds import PercentSign, ValueKind
from checkedtables.pages import BodyRule
from checkedtables.pipeline import Layout, cut_pages
from checkedtables.rows import stray_findings
from checkedtables.table import Finding, RowKind, Severity, Table, TableId
from checkedtables.words import Document

from datadesk.core.context import Failed, ParseContext, Parsed, ParseResult
from datadesk.core.domain import Period
from datadesk.core.measures import (Basis, Derived, Meaning, MeasureSet, MeasureSpec, Scope,
                                    Stated)
from datadesk.core.registry import Resolved, resolve_fund
from datadesk.core.tables.supp_common import (Statement, body_start, department_banner,
                                               join_wrapped_labels, lift_subtotal_labels,
                                               link_departments, split_statements)
from datadesk.core.vocab import How, Kind, Version, Window

TABLE = "supplemental_revenues"
TITLE = r"^Statement\s+of\s+Net\s+Revenues?$"     # the "by Major Source" title does not match
WATER_FY2010 = (2010, "phl_fund_water")            # hierarchy shown only by bold (SUPOP-Q21)

_CENTS = NumberFormat(decimals=2)
COLUMNS = (
    ColumnSpec("original", r"Original", ValueKind.MONEY, _CENTS),
    ColumnSpec("final", r"Final", ValueKind.MONEY, _CENTS),
    ColumnSpec("actual", r"Actual", ValueKind.MONEY, _CENTS),
    ColumnSpec("percent", r"Percent|Collected", ValueKind.PERCENT,
               NumberFormat(decimals=None, percent=PercentSign.OPTIONAL)),
    ColumnSpec("prior_actual", r"Prior\s+Year(\s+Actual)?", ValueKind.MONEY, _CENTS),
    ColumnSpec("increase", r"Increase|\(Decrease\)", ValueKind.MONEY, _CENTS),
)
ERAS = (Era("net_revenue", signature=(r"Original", r"Prior\s+Year", r"Increase"),
            columns=COLUMNS, expected=(date(2002, 7, 1), None)),)
_MONEY = tuple(c.name for c in COLUMNS if c.kind is ValueKind.MONEY)

_CATEGORY = (r"(Taxes|Locally\s+Generated\s+Non\s?-?\s?Tax\s+Revenues?"
             r"|Revenues?\s+from\s+Other\s+(Governments|Funds)(\s+of\s+the\s+City)?)$")
_RULES = (
    RowRule("grand_total", RowKind.TOTAL, r"Total\s+Net\s+Revenues?$", values=Values.PRESENT,
            closes=AllSlots(), fixed=(("line", "total_net_revenue"),)),
    RowRule("category_total", RowKind.TOTAL, r"Total\s+(?!Net\b)", values=Values.PRESENT,
            closes=("category",), key=("category",), fixed=(("line", "total"),)),
    RowRule("subtotal", RowKind.SUBTOTAL, r"Sub\s*-?\s*Total$", values=Values.PRESENT,
            closes=("department",), key=("category", "department"),
            fixed=(("line", "subtotal"),)),
    RowRule("category", RowKind.HEADING, _CATEGORY, values=Values.ABSENT, opens="category"),
    RowRule("department", RowKind.HEADING, r".+", values=Values.ABSENT, opens="department"),
    RowRule("source", RowKind.ITEM, r".+", values=Values.PRESENT,
            key=("category", "department", "label")),
)
_BOLD_PARENT = RowRule("bold_department", RowKind.SUBTOTAL, r".+", values=Values.PRESENT,
                       style=Style.BOLD, opens="department", key=("category", "label"),
                       fixed=(("line", "department_total"),))
_DROP = (r"-\s*\d+\s*-$", r"\(?Continued\)?$")
GRAMMAR = RowGrammar(TABLE, slots=("category", "department"), rules=_RULES, drop=_DROP)
GRAMMAR_WATER_FY2010 = RowGrammar(TABLE, slots=("category", "department"), drop=_DROP,
                                  rules=(*_RULES[:4], _BOLD_PARENT, *_RULES[4:]))


_FY = Window.FISCAL_YEAR
_MEANING: dict[str, Meaning] = {
    "original": Stated(Kind.BUDGET, _FY, version=Version.ADOPTED),
    "final": Stated(Kind.BUDGET, _FY, version=Version.REVISED),
    "actual": Stated(Kind.ACTUAL, _FY),
    "percent": Derived(How.RATIO, of=("actual", "final")),
    "prior_actual": Stated(Kind.ACTUAL, _FY, year=-1),
    "increase": Derived(How.DIFFERENCE, of=("actual", "prior_actual")),
}


def measures(era: Era, scope: Scope) -> MeasureSet:
    return MeasureSet(tuple(
        MeasureSpec(c.name, _MEANING[c.name],
                    unit="percent" if c.kind is ValueKind.PERCENT else "USD",
                    scale=Decimal(1), basis=Basis.FLOW)
        for c in era.columns))


def parse(doc: Document, ctx: ParseContext) -> ParseResult:
    statements, findings = split_statements(doc, TITLE)
    tables: list[Table] = []
    used: frozenset[str] = frozenset()
    for statement in statements:
        result = _one_statement(statement, ctx)
        findings = (*findings, *result.findings)
        if isinstance(result, Parsed):
            tables.extend(result.tables)
            used |= result.used
    if not tables:
        missing = Finding(Severity.BLOCK, "no_table", f"{doc.sha256[:8]}:{TABLE}",
                          "no revenue statement could be read")
        return Failed(tuple(sorted((*findings, missing))))
    return Parsed(tuple(tables), tuple(sorted(findings)), used)


def _one_statement(st: Statement, ctx: ParseContext) -> ParseResult:
    fund = resolve_fund(ctx.registry, st.fund_banner, st.fund_code, ctx.fiscal_year)
    if not isinstance(fund, Resolved):
        return Failed((st.finding("unknown_fund", repr(fund)),))
    layout = Layout(ERAS, BodyRule(start=body_start, stop=None, drop=_DROP))
    cut = cut_pages(layout, st.pages, ctx.period.end)
    if isinstance(cut, Finding):
        return Failed((cut,))
    raws, joined = join_wrapped_labels(lift_subtotal_labels(cut.raws),
                                       department_banner(ctx, TABLE, _CATEGORY))
    wet = (ctx.fiscal_year, fund.entity_id) == WATER_FY2010
    matched = read_grammar(raws, GRAMMAR_WATER_FY2010 if wet else GRAMMAR)
    rows, unlinked = link_departments(matched.rows, ctx, "department", TABLE)
    built = assemble(TableId(TABLE, (("fund", fund.entity_id),)), cut, rows, ctx.cell_records)
    findings = (*cut.findings, *joined, *matched.findings, *unlinked, *built.findings,
                *stray_findings(raws))
    if fund.conflict is not None:
        findings = (*findings, st.finding("fund_banner_conflict", fund.conflict, Severity.WARN))
    if built.table is None:
        return Failed(tuple(sorted(findings)))
    return Parsed((built.table,), tuple(sorted(findings)), built.used)


def checks_for(era: str, period: Period) -> CheckSet:
    return (
        declare(TABLE, tolerance=EXACT)
        .add(ChildrenSum("sections_add_up", parents=Kinds((RowKind.SUBTOTAL, RowKind.TOTAL)),
                         columns=_MONEY))
        .add(RowDifference("increase_is_actual_less_prior", minuend="actual",
                           subtrahend="prior_actual", result="increase"))
        .add(Ratio("percent_collected", numerator="actual", denominator="final",
                   result="percent", severity=Severity.WARN))     # never checked before (SUPOP 6)
    )
```

124 lines. The family helper does the work that is the same for the six operating tables:

```python
# datadesk/core/tables/supp_common.py (signatures)
@dataclass(frozen=True, slots=True)
class Statement:
    title: str
    fund_banner: str
    fund_code: str | None
    schedule: str | None           # evidence only; letters move between editions (SUPOP-Q09)
    pages: tuple[PageLines, ...]   # one per page; lines from the title to the next title or note

    def finding(self, code: str, message: str, severity: Severity = Severity.BLOCK) -> Finding: ...


def split_statements(doc: Document, title: str) -> tuple[tuple[Statement, ...], tuple[Finding, ...]]: ...
    # every line matching any of the family's statement titles starts a zone, its own title
    # included, so two statements stacked on one page stay apart (SUPOP-Q03, SUPCAP-Q10).
    # Zones whose title matches `title` and whose fund banner is equal on consecutive pages form
    # one Statement. Unpublished titles (encumbrances, NOTE blocks) end a zone (SUPOP-Q04, Q05).
def body_start(line: Line) -> bool: ...
    # the first line below the caption block: a category heading or a line with values
def lift_subtotal_labels(raws: Sequence[RawRow]) -> tuple[RawRow, ...]: ...
    # a "Sub-Total" word group printed right of an item label on the same baseline moves to the
    # next row when that row has values and no label (SUPOP-Q18)
def department_banner(ctx: ParseContext, table: str, category: str) -> Callable[[str], bool]: ...
    # true for a value-less label that is a category heading, or that resolves to a department
    # in the registry for this table, year and edition
def join_wrapped_labels(raws: Sequence[RawRow], is_banner: Callable[[str], bool]
                        ) -> tuple[tuple[RawRow, ...], tuple[Finding, ...]]: ...
    # a value-less line that is not a banner joins the valued line below it; each join is a WARN
    # finding `joined_label`, so a wrapped source label never opens a phantom department (R1)
def link_departments(rows: Sequence[KeyedRow], ctx: ParseContext, slot: str,
                     table: str) -> tuple[tuple[KeyedRow, ...], tuple[Finding, ...]]: ...
    # resolves each distinct slot value once; Unknown -> WARN; Ambiguous -> BLOCK
```

What the module shows:

- A continuation page reprints the category and department banners. Opening a slot with the
  label it already holds changes nothing, so one Sub-Total closes the whole department
  (SUPOP-Q20).
- Parents come from `closes`. Sources hang under their Sub-Total, Sub-Totals under the category
  total, and category totals under the grand total through `AllSlots` (change 2). One
  `ChildrenSum` checks every level.
- A Sub-Total printed as a dash under valued sources is `MISSING_TOTAL`, a failure that needs an
  acknowledgment (SUPOP-Q24, Q28). An all-dash Sub-Total with no children produces no instance
  and is no coverage finding, because it holds no Amount (SUPOP-Q23).
- The FY2010 Water statement uses a grammar with a bold rule. Every other statement has no style
  rule. If FY2010 Water arrives as a scan, the bold rule yields `style_unavailable` and blocks.
- Whether the FY2010 Water bold line prints above or below its children is not verified. The
  grammar assumes above, as the old "bold parent" code did. If that is wrong, `sections_add_up`
  fails on the first run and the rule changes to a closer.
- "Prior Year Actual" binds to `prior_actual` by the longest-match rule, never to `actual` (R1).
- `percent_collected` starts at WARN. It becomes BLOCK only after a `suggest` run shows it holds
  over the corpus (change 16).
- The 17 change-column records become acknowledgments on `increase_is_actual_less_prior`, keyed
  by fund, category, department, label and column.

### 5.3 Monthly City collections

Closed schema with blocks, optional columns, a June close era, caption-year checks, overprint
and stacked labels, and era-dependent checks.

```python
# datadesk/core/tables/collections_city.py
"""Monthly City revenue collections: one statement over four pages, ten to thirteen columns."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from checkedtables.assemble import assemble
from checkedtables.checks.dsl import (AllRows, CheckSet, ChildrenSum, ColumnSum, Except,
                                      FirstPresent, Keys, Kinds, Minus, PerOperand, Plus, Ratio,
                                      RowDifference, RowSum, declare)
from checkedtables.columns import ColumnSpec, Era, NumberFormat
from checkedtables.kinds import PercentSign, Presence, ValueKind
from checkedtables.lines import PageLines, group_lines
from checkedtables.pages import BodyRule
from checkedtables.pipeline import Layout, cut_pages
from checkedtables.rows import match_rows, starts_known_row, stray_findings
from checkedtables.table import Finding, RowKey, RowKind, Severity, TableId
from checkedtables.words import Document

from datadesk.core.context import Failed, ParseContext, Parsed, ParseResult
from datadesk.core.domain import Period
from datadesk.core.measures import MeasureSet, Scope
from datadesk.core.records import drop_noted_lines
from datadesk.core.tables.collections_common import (attach_stacked_labels, caption_year_findings,
                                                     dedupe_overprint, money_measures)

TABLE = "collections_city"
STACKED_LABELS = Period(date(2014, 7, 1), date(2015, 11, 30))   # MCITY-Q20: this window only
_USD = NumberFormat(decimals=0)


def _usd(name: str, caption: str, presence: Presence = Presence.REQUIRED) -> ColumnSpec:
    return ColumnSpec(name, caption, ValueKind.MONEY, _USD, presence=presence)


_OPT = Presence.OPTIONAL
_HEAD = (_usd("prior_year_final", r"FINAL", _OPT), _usd("prior_year_budget", r"PRIOR.*BUDGET", _OPT),
         _usd("budget", r"BUDGET\s+ESTIMATE"), _usd("current_estimate", r"CURRENT\s+ESTIMATE", _OPT),
         _usd("revised_budget", r"REVISED", _OPT),
         _usd("month", r"MONTH\s+OF"), _usd("month_prior", r"MONTH\s+OF"))
_TAIL = (_usd("increase", r"INCREASE"), _usd("remaining", r"NECESSARY"),
         ColumnSpec("pct", r"PERCENT|PCT", ValueKind.PERCENT,
                    NumberFormat(decimals=None, percent=PercentSign.OPTIONAL)))
ERAS = (
    Era("ordinary", signature=(r"NECESSARY",), excludes=(r"NET\s+ACCRUALS",),
        expected=(date(2014, 7, 1), None),
        columns=(*_HEAD, _usd("fytd", r"JULY"), _usd("fytd_prior", r"JULY"), *_TAIL)),
    Era("june_close", signature=(r"NECESSARY", r"NET\s+ACCRUALS"),
        expected=(date(2015, 6, 1), None),
        columns=(*_HEAD, _usd("fytd_pre_accrual", r"BEFORE"),
                 _usd("net_accrual", r"NET\s+ACCRUALS"), _usd("fytd", r"JULY"),
                 _usd("fytd_prior_pre_accrual", r"BEFORE"),
                 _usd("net_accrual_prior", r"NET\s+ACCRUALS"), _usd("fytd_prior", r"JULY"),
                 *_TAIL)),
)
_FURNITURE = (r"COMPARATIVE\s+STATEMENT", r"^CITY\s+OF\s+PHILADELPHIA", r"^Page\s+\d+")
_GF_PARKING = (RowKey.of(block="other_taxes", tax="parking_lot"),
               RowKey.of(block="other_taxes", tax="valet_parking"))
_DEDICATED_PARKING = (RowKey.of(block="dedicated_funds", tax="parking"),)
_PICA_PARTS = tuple(RowKey.of(tax=t, scope="pica", line="total")
                    for t in ("wage", "earnings", "net_profits"))
_LESS_PICA = RowKey.of(line="less_pica")
_GFP = RowKey.of(line="total_general_fund_and_pica")
_TGF = RowKey.of(line="total_general_fund")


def measures(era: Era, scope: Scope) -> MeasureSet:
    return money_measures(era, scope)


def parse(doc: Document, ctx: ParseContext) -> ParseResult:
    schema = ctx.schema(TABLE)
    pages: list[PageLines] = []
    used: frozenset[str] = frozenset()
    for page in doc.pages:
        lines, dropped = drop_noted_lines(group_lines(dedupe_overprint(page)), ctx.notes,
                                          page.number)                       # MCITY-Q18, Q29
        pages.append(PageLines(page.number, page.source.kind, lines))
        used |= dropped
    body = BodyRule(start=starts_known_row(schema), stop=None, drop=_FURNITURE)
    cut = cut_pages(Layout(ERAS, body), pages, ctx.period.end)
    if isinstance(cut, Finding):
        return Failed((cut,))
    findings: tuple[Finding, ...] = cut.findings
    for page in cut.pages:                                    # every page's captions, not one
        more, applied = caption_year_findings(page.binding, page.header, ctx.period, ctx.notes)
        findings = (*findings, *more)
        used |= applied
    raws = cut.raws
    if STACKED_LABELS.holds(ctx.period.end):
        raws = attach_stacked_labels(raws)
    matched = match_rows(raws, schema)
    built = assemble(TableId(TABLE), cut, matched.rows, ctx.cell_records)
    findings = tuple(sorted((*findings, *matched.findings, *built.findings,
                             *stray_findings(raws))))
    if built.table is None:
        return Failed(findings)
    return Parsed((built.table,), findings, built.used | used)


def checks_for(era: str, period: Period) -> CheckSet:
    money = tuple(c.name for e in ERAS if e.name == era for c in e.columns
                  if c.kind is ValueKind.MONEY)
    na_ok = _GF_PARKING if period.end >= date(2023, 7, 31) else ()      # MCITY-Q27, FY2024 on
    base = FirstPresent(("revised_budget", "budget"))                  # MSCH-Q32 rule
    checks = (
        declare(TABLE, tolerance=PerOperand(Decimal(1)))
        .add(ChildrenSum("parts_add_to_totals", parents=Kinds((RowKind.SUBTOTAL, RowKind.TOTAL)),
                         columns=money, na_excluded=na_ok))
        .add(ColumnSum("less_pica_restates_pica", total=_LESS_PICA,
                       terms=(Plus(Keys(_PICA_PARTS)),), columns=money))
        .add(ColumnSum("general_fund_is_gfp_less_pica", total=_TGF,
                       terms=(Plus(Keys((_GFP,))), Minus(Keys((_LESS_PICA,)))), columns=money))
        .add(RowDifference("fytd_increase", minuend="fytd", subtrahend="fytd_prior",
                           result="increase"))
        .add(RowDifference("remaining_parking", minuend=base, subtrahend="fytd",
                           result="remaining", rows=Keys(_DEDICATED_PARKING)))      # MCITY-Q26
        .add(RowDifference("remaining_budget", minuend=base, subtrahend="fytd",
                           result="remaining", rows=Except(AllRows(), _DEDICATED_PARKING),
                           severity=Severity.WARN))                                  # change 16
        .add(Ratio("percent_collected", numerator="fytd", denominator=base, result="pct",
                   severity=Severity.WARN))                                          # change 16
    )
    if period.start.month == 7:
        checks = checks.add(RowSum("july_month_is_fytd", total="fytd", parts=("month",)))
    if era == "june_close":
        checks = (checks
                  .add(RowSum("accruals", total="fytd", parts=("fytd_pre_accrual", "net_accrual")))
                  .add(RowSum("accruals_prior", total="fytd_prior",
                              parts=("fytd_prior_pre_accrual", "net_accrual_prior"))))
    return checks
```

116 lines. The June close column order follows the dossier's description. MCITY section 3 does not
list it left to right, so it must be confirmed on one June page before the first release.

What the module shows:

- Eras are chosen by captions. `excludes` keeps the ordinary era from claiming a close page. The
  optional columns bind only when their caption is printed (MCITY-Q14, Q15).
- `month` and `month_prior` share a caption pattern and bind in declared order. Then
  `caption_year_findings` checks the printed years on every page against the calendar basis
  before FY2022 and the fiscal basis after (MCITY-Q11, MCITY-Q12).
- Stacked labels are joined only inside the 2014 window. Outside it, a heading followed by an
  amount-only line is an orphan finding (change 18).
- `dedupe_overprint` removes, and never creates, words. It drops three shapes, each only when the
  boxes overlap. One is a twin with the same text or the same digits without commas. Another is
  a welded copy whose squashed text equals the squashed join of the words it covers
  ("PICAWAGETAX" over "PICA", "WAGE", "TAX"). The third is an amount inside a label span whose
  digits equal a lane value on the same line (MCITY-Q18).
- `FirstPresent` picks revised budget when the edition prints it, else budget. A printed but
  unusable revised cell does not fall back; the check reports `MISSING_OPERAND`.
- Remaining budget is BLOCK only on the Dedicated Parking row, where it is declared today. On
  every other row it and percent collected start at WARN (MCITY section 5, A11 and A12).
- N/A parking cells leave the operands of `parts_add_to_totals` only from FY2024 and only for the
  two General Fund keys. Everywhere else N/A is a missing operand.
- The 52 GFP acknowledgments key on `parts_add_to_totals`, row `line=total_general_fund_and_pica`
  and the column name. A column that moves when the optional estimate prints does not move the
  key (MCITY-Q51 is gone).

### 5.4 Budget in Brief cross-table check

The relations are fixed by the book. The instances depend on which funds and schedules the book
prints. So the relation is code, and the instances come from table keys, never from values.

```python
# datadesk/core/tables/bib_cross.py
"""Budget in Brief relations across tables of one adopted book (BIB-Q40, Q41, Q43, Q56, Q57)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from checkedtables.checks.dsl import CellSel, CellsEqual, CheckSet, PerOperand, declare
from checkedtables.table import Finding, RowKey, Severity, Table

MEASURES = ("actual", "original_budget", "current_estimate", "budget")
GRAND = RowKey.of(line="total")    # the key the schedule grammar's AllSlots rule gives
# The All Funds statement prints some lines as siblings that a fund statement prints as one row
# (BIB-Q41). Pairs of (fund-statement key, All Funds keys), from bib_fund_summary.toml.
ALL_FUNDS_SPLITS: tuple[tuple[RowKey, tuple[RowKey, ...]], ...] = (
    (RowKey.of(line="advances_misc"), (RowKey.of(line="advances"), RowKey.of(line="misc_payments"))),
)


def cross_checks(tables: Sequence[Table]) -> tuple[CheckSet, tuple[Finding, ...]]:
    summaries = tuple(t for t in tables if t.id.name == "bib_fund_summary")
    schedules = tuple(t for t in tables if t.id.name == "bib_revenue_schedule")
    checks = declare("bib_cross", tolerance=PerOperand(Decimal(1)))     # thousands
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for sched in schedules:                     # a schedule's grand total feeds its fund line
        fund, category = sched.id.part("fund"), sched.id.part("category")
        summary = _fund(summaries, fund)
        line = RowKey.of(line=category)         # one key for both spellings (BIB-Q40)
        if (fund, category) in seen:
            findings.append(_finding("two_schedules_one_line", sched,
                                     "two schedules feed one fund summary line"))
            continue
        seen.add((fund, category))
        if summary is None or summary.row(line) is None or sched.row(GRAND) is None:
            findings.append(_finding("cross_table_unmatched", sched,
                                     "revenue schedule has no fund summary line to feed"))
            continue
        for col in MEASURES:
            checks = checks.add(CellsEqual("schedule_feeds_summary",
                                           left=(CellSel(summary.id, line, col),),
                                           right=(CellSel(sched.id, GRAND, col),)))
    all_funds = _fund(summaries, "all")
    if all_funds is None:                       # FY2006 to FY2008 excerpts print no summaries
        return checks, tuple(findings)
    funds = tuple(t for t in summaries if t.id.part("fund") != "all")
    for fund_key, printed in _all_funds_lines(all_funds):
        for col in MEASURES:
            checks = checks.add(CellsEqual(
                "funds_sum_to_all_funds",
                left=tuple(CellSel(all_funds.id, k, col) for k in printed),
                right=tuple(CellSel(f.id, fund_key, col) for f in funds
                            if f.row(fund_key) is not None)))
    return checks, tuple(findings)


def _fund(summaries: Sequence[Table], fund: str) -> Table | None:
    found = [t for t in summaries if t.id.part("fund") == fund]
    return found[0] if len(found) == 1 else None


def _all_funds_lines(all_funds: Table) -> tuple[tuple[RowKey, tuple[RowKey, ...]], ...]:
    whole_of = {part: whole for whole, parts in ALL_FUNDS_SPLITS for part in parts}
    grouped: dict[RowKey, list[RowKey]] = {}
    for row in all_funds.rows:
        if row.cells and row.label.text:
            grouped.setdefault(whole_of.get(row.key, row.key), []).append(row.key)
    return tuple(sorted((k, tuple(v)) for k, v in grouped.items()))


def _finding(code: str, table: Table, message: str) -> Finding:
    return Finding(Severity.BLOCK, code, f"{table.doc_sha256[:8]}:{table.id}", message)
```

59 lines. The schedule's grand total is found by its key, which the grammar's `AllSlots` rule
gives. Design C took the last TOTAL row by position (R2). Two schedules for one fund line are a
finding, because R1 could not verify that a category has one schedule per fund.

`cross_checks` reads keys and the set of printed tables. It never reads a value, and section
11.3 tests that. The eight `resolved_assertions.yml` records become acknowledgments on
`schedule_feeds_summary` and `funds_sum_to_all_funds`. They key on the summary's table instance,
row key and column, plus the document sha they never had (VAL-Q48).

### 5.5 The held-out case: QSMR CF-3 vendor payments, a list table

CF-3 prints an open list of vendors over $100,000 across 6 to 14 pages. Names are cut at about 30
characters and a vendor can repeat (QSMR-Q11). The 2016 layout prints a vendor number; the 2023
layout prints two vendors to a line (QSMR-Q10). This module uses the list-table rule of change 6
and no other kit change.

```python
# datadesk/core/tables/qsmr_vendor_payments.py
"""QSMR CF-3 Vendor Payments over $100,000: a list table (QSMR-Q10, Q11)."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from decimal import Decimal

from checkedtables.assemble import assemble
from checkedtables.checks.dsl import EXACT, CheckSet, ChildrenSum, Kinds, declare
from checkedtables.columns import ColumnSpec, Era, NumberFormat
from checkedtables.grammar import AllSlots, Occurrences, RowGrammar, RowRule, Values, read_grammar
from checkedtables.kinds import ValueKind
from checkedtables.lines import Line, PageLines, page_lines
from checkedtables.pages import BodyRule, find_runs, only_run
from checkedtables.pipeline import Layout, cut_pages
from checkedtables.refs import Box
from checkedtables.rows import RawRow, stray_findings
from checkedtables.table import Finding, RowKind, Severity, TableId
from checkedtables.words import Document, Word

from datadesk.core.context import Failed, ParseContext, Parsed, ParseResult
from datadesk.core.domain import Period
from datadesk.core.measures import Basis, MeasureSet, MeasureSpec, Scope, Stated
from datadesk.core.vocab import Kind, Window

TABLE = "qsmr_vendor_payments"
_AMOUNT = (ColumnSpec("amount", r"AMOUNT", ValueKind.MONEY, NumberFormat(decimals=0)),)
# Era boundary unknown: both read editions are inside these ranges. Narrow after the first run.
ERAS = (
    Era("one_up", signature=(r"VENDOR\s+(NO|NUMBER|#)", r"AMOUNT"), columns=_AMOUNT,
        expected=(date(2015, 7, 1), None)),
    Era("two_up", signature=(r"VENDOR", r"AMOUNT"), excludes=(r"VENDOR\s+(NO|NUMBER|#)",),
        columns=_AMOUNT, expected=(date(2015, 7, 1), None)),
)
_VENDOR_NO = r"C?\d{4,8}"          # 2016 vendor numbers become Label.line_no, never a lane
GRAMMAR = RowGrammar(
    TABLE, slots=(), drop=(r"Page\s+\d+",), repeats=Occurrences(block="root"),
    rules=(
        RowRule("grand_total", RowKind.TOTAL, r"(Grand\s+)?Total\b", values=Values.PRESENT,
                closes=AllSlots(), fixed=(("line", "total"),)),
        RowRule("subtotal", RowKind.SUBTOTAL, r"Sub\s*-?\s*Total\b", values=Values.PRESENT,
                closes=AllSlots(), fixed=(("line", "subtotal"),)),
        RowRule("other", RowKind.ITEM, r"(All\s+)?Other\s+Payments\b", values=Values.PRESENT,
                fixed=(("line", "other_payments"),)),
        RowRule("void", RowKind.MEMO, r".*\bVOID\b", key=("label",), fixed=(("status", "void"),)),
        RowRule("vendor", RowKind.ITEM, r".+", values=Values.PRESENT, key=("label",)),
    ),
)


def measures(era: Era, scope: Scope) -> MeasureSet:
    return MeasureSet((MeasureSpec("amount", Stated(Kind.ACTUAL, Window.FISCAL_YTD), unit="USD",
                                   scale=Decimal(1), basis=Basis.FLOW),))


def parse(doc: Document, ctx: ParseContext) -> ParseResult:
    pages = tuple(page_lines(p) for p in doc.pages)
    run = only_run(find_runs(pages, _is_cf3), f"{doc.sha256[:8]}:{TABLE}")
    if isinstance(run, Finding):
        return Failed((run,))
    halves = tuple(half for pl in run.take(pages) for half in _halves(pl))    # QSMR-Q10
    body = BodyRule(start=_ends_in_amount, stop=_is_grand_total, drop=GRAMMAR.drop,
                    prefix=_VENDOR_NO)
    cut = cut_pages(Layout(ERAS, body), halves, ctx.period.end)
    if isinstance(cut, Finding):
        return Failed((cut,))
    raws = tuple(_void_to_label(r) for r in cut.raws)
    matched = read_grammar(raws, GRAMMAR)                      # repeated names get occurrences
    built = assemble(TableId(TABLE), cut, matched.rows, ctx.cell_records)
    findings = tuple(sorted((*cut.findings, *matched.findings, *built.findings,
                             *stray_findings(raws))))
    if built.table is None:
        return Failed(findings)
    return Parsed((built.table,), findings, built.used)


def _is_cf3(band: str) -> bool:
    return "CF-3" in band.upper()


def _ends_in_amount(line: Line) -> bool:
    return bool(line.words) and line.words[-1].text.replace(",", "").replace("$", "").isdigit()


def _is_grand_total(line: Line) -> bool:
    return re.match(r"(GRAND\s+)?TOTAL\b", line.text, re.IGNORECASE) is not None


def _halves(pl: PageLines) -> tuple[PageLines, ...]:
    """2023 prints two vendors to a line. Cut just right of the first AMOUNT caption; the right
    half then reads like a one-vendor page, and the left half comes first in print order."""
    for line in pl.lines:
        amounts = [w for w in line.words if w.text.upper() == "AMOUNT"]
        if len(amounts) >= 2:
            gutter = amounts[0].box.x1 + 1.0
            return (_keep(pl, lambda w: w.box.x1 <= gutter), _keep(pl, lambda w: w.box.x0 > gutter))
    return (pl,)


def _keep(pl: PageLines, keep: Callable[[Word], bool]) -> PageLines:
    lines: list[Line] = []
    for line in pl.lines:
        words = tuple(w for w in line.words if keep(w))
        if words:
            lines.append(Line(line.page, words, Box.around(w.box for w in words)))
    return PageLines(pl.number, pl.source, tuple(lines))


def _void_to_label(raw: RawRow) -> RawRow:
    """A "VOID" word in the amount lane would lex as Unreadable and block every edition. It moves
    into the label, where the void rule makes the row a memo that no sum counts."""
    moved = tuple(w for _, ws in raw.cells for w in ws if w.text.upper() == "VOID")
    if not moved:
        return raw
    cells = tuple((name, tuple(w for w in ws if w.text.upper() != "VOID")) for name, ws in raw.cells)
    return replace(raw, label_words=(*raw.label_words, *moved), cells=cells)


def checks_for(era: str, period: Period) -> CheckSet:
    return (
        declare(TABLE, tolerance=EXACT)
        .add(ChildrenSum("subtotal_and_other_make_total", parents=Kinds((RowKind.TOTAL,)),
                         columns=("amount",)))                      # QSMR section 5
        .add(ChildrenSum("vendors_make_subtotal", parents=Kinds((RowKind.SUBTOTAL,)),
                         columns=("amount",), severity=Severity.WARN))   # inferred, not stated
    )
```

106 lines. What the module shows about the held-out test:

- A repeated truncated name gets `occurrence=1`, `occurrence=2` within the table. A name that
  prints once gets no occurrence part.
- No acknowledgment may target an occurrence-numbered key. `load_records` refuses one and the
  gate lists it as `refused`. Failures here sit on the Subtotal and Total rows, whose keys are
  fixed, so nothing needs to.
- A re-parse of the same document may change the occurrence count of a name. The row diff then
  reports `key_changed`, and the release blocks until `--accept-diff` names the reviewed diff.
  Between editions a changed count is a WARN in `cross_edition_checks`, because vendor lists
  change every quarter.
- The two-up layout becomes two half pages before `cut_pages`. Each half binds one `amount`
  column, so no table carries an empty right-hand column.
- The 2016 vendor number is split off by `BodyRule.prefix` and published as `Label.line_no`.
  A 2023 name that starts with a 4 to 8 digit token would lose it to `line_no`. Its printed
  label still carries every word.
- Where VOID prints (name or amount) is not known. The rule handles both and is not verified.
- Kit changes made for the QSMR: the list-table rule and the "NA" token. Both went into the kit
  before the first QSMR parse. Everything in this module is `datadesk` code. Section 15 step 14
  is the test that the kit then stays unchanged for the remaining QSMR tables.

## 6. Format eras, editions and restatements

### 6.1 Where eras live

There are four kinds of era, and each lives in one place.

| Kind of era | Lives in | Chosen by | Cross-check |
|---|---|---|---|
| Column layout | `ERAS` tuple in the table module | printed captions: `signature` all present, `excludes` all absent | `expected` date range; a mismatch is a BLOCK finding, fixed by widening the range in code |
| Row set and labels | `periods`, `absent_editions` and `label_editions` in `datadesk/data/rows/<table>.toml`; entity spellings in the registry | the edition's period and sha, in `schema_for` | `match_rows` fails on unknown, missing and duplicate rows |
| Line repairs and style rules | a named `Period` or a (fiscal year, fund) constant in the table module | the edition's period | a repair outside its window does not run |
| Word source | `WordSourcePlan` records | the document sha and page | `compare_sources` where a record asks for it |

A one-edition exception is an `EditionNote`, never a copied profile (WAGE-Q32 and MCITY-Q36 are
artifacts that cannot recur). An unused note is a blocking finding.

A repair that is tied to neither an era window nor an edition record does not exist (change 18):

| Repair or style rule | Window | Dossier |
|---|---|---|
| `attach_stacked_labels` (City) | `STACKED_LABELS`, 2014-07 to 2015-11 | MCITY-Q20 |
| `attach_stacked_labels` (School) | `STACKED_LABELS`, 2014-07 to 2015-11, bounds to confirm on the first run | MSCH-Q30 |
| Bold department parent (supplemental revenues) | FY2010, Water fund only | SUPOP-Q21 |
| Bold owner banners (BiB revenue schedules) | text-layer books; FY2011 to FY2015 scans use the scan grammar | BIB-Q21 |
| `dedupe_overprint` | every City edition; it only removes overlapping duplicates, so it cannot change a clean page | MCITY-Q18 |
| `lift_subtotal_labels` | every supplemental revenues edition; it moves only a "Sub-Total" word group | SUPOP-Q18 |

Budget in Brief revenue schedules have two grammars. `bib_revenue_schedule.grammar_for(version, sources)`
picks one from the word source of the schedule pages:

- Text layer: owner banners are value-less bold lines (`Style.BOLD`); refining sub-banners are
  value-less lines that are not bold (`Style.NOT_BOLD`).
- FY2011 to FY2015 scans (BIB-Q36): no style rule. `SCAN_SUB_BANNERS` is a closed regex list:
  "Federal:", "State:", "Other Governments", "Licenses & Permits" and the rest the first run finds.
  A value-less line on that list refines; any other value-less line is an owner banner.

A text-era grammar on a scan page yields `style_unavailable` and blocks. It can never match
nothing in silence (change 5, R1, R2).

Column eras per table, as they will be declared:

| Table | Eras (signature tokens) | Optional columns | Dossier |
|---|---|---|---|
| QCMR cash revenue grid | `legacy` ("Under", "Budget Revenues"), `middle` ("Estimated Revenues", excludes "Not Accrued"), `modern` ("Not Accrued") | none; an empty printed column binds Blank | QCASH-Q32, Q34, Q35 |
| QCMR cash expense grid | `with_mergers` ("Mergers" or "mergere"), `no_mergers` (excludes it) | none | QCASH-Q26, Q33 |
| QCMR cash page 2 | `fund_balances` (twelve month captions) | none | QCASH-Q38 |
| QCMR O-2 | `nine` ("YTD", "Target", "Projection"), `year_end` (excludes "YTD"; six columns, seen in FY2026 Q4); captions accept "Original" or "Adopted" | none | QOBL section 2, Codex review |
| QCMR O-3 | `in_year` ("YTD"), `year_end` (excludes "YTD") | FY-3 and FY-2 actuals | QOBL-Q28, Q31 |
| QCMR P-1 | `p1_ten_columns` | none | QPOS-Q01 |
| Collections, City and School | `ordinary`, `june_close` ("NET ACCRUALS") | final, prior budget, current estimate, revised | MCITY-Q14 to Q16, MSCH-Q09 to Q13 |
| Wage by industry | `nine` | none; the period kind comes from the title | WAGE-Q19, Q23 |
| Wage residency | `first` (10 and 16 columns), `rolling` (17 and 18), `summary_only` (17, no detail page) | none | WAGE-Q52, Q54 |
| BIRT | `two_halves` (8 columns) | none | BSALES-Q23 |
| Sales | `three` and `eleven` (growth captions) | none | BSALES-Q35 |
| RTT | `monthly_grid`, `monthly_comparison` (14), `quarter`, `fytd`, `fiscal_year`, `calendar_year` | percent pair | RTT-Q19, Q20 |
| BiB obligation history | `five`, `six` ("Prior Adopted"), `seven` ("Prior Increase") | none | BIB-Q32 |
| BiB fund summary and schedules | `ruled`, with LINE NO. as a CODE column and the schedule reference as TEXT | percent | BIB-Q26, Q29, Q30 |
| Supplemental activity | `seven`, with FAMIS and "Fd BAL/AP Adjs" optional | FAMIS, adjustments | SUPOP-Q15 (unsure) |
| Supplemental capital activity | `nine` and `ten` (leading numeric column) | none | SUPCAP-Q14 |
| QSMR CF-3 | `one_up`, `two_up` | none | QSMR-Q10 |

### 6.2 Three table rules the reviews found unwritten

QCMR cash page 2 (QCASH-Q38). Its caption is damaged or missing in some editions, so a header
band cannot find it. `qcmr_cash.find_balance_page(pages, run)` takes the page right after the
page-1 run. It accepts that page only if its header binds the `fund_balances` era. Its rows must
also match the page-2 schema, from General down to TOTAL FUND EQUITY. Otherwise it returns a
`balance_page_not_found` finding. The caption is evidence when present and never required.

QCMR O-3 footnotes and the citywide box (QOBL-Q19, Q20). The body cannot end at a stateless first
match, because the three metric labels repeat in every section. Two functions in the O-3 module
replace the stop predicate:

```python
# datadesk/core/tables/qcmr_personal_services.py (two functions)
_METRICS = (r"Full.Time\s+Positions", r"Class\s+100\s+Total", r"Class\s+100\s+Overtime")
_NOTE_START = re.compile(r"^(\(\d+\)|\*+|\d+\s*/|Note[s]?:)\s*")


def citywide_end(lines: Sequence[Line]) -> int | Finding:
    """Index of the last body line: the third metric line after the value-less TOTAL GENERAL
    FUND line. Lines between, such as footnotes, are dropped by drop_footnotes."""
    for i, line in enumerate(lines):
        if line.text.upper().startswith("TOTAL GENERAL FUND") and not has_values(line):
            found = [j for j in range(i + 1, len(lines))
                     if any(re.match(m, lines[j].text, re.IGNORECASE) for m in _METRICS)]
            if len(found) >= 3:
                return found[2]
            return Finding(Severity.BLOCK, "citywide_block_short", "qcmr_o3",
                           f"{len(found)} metric lines after TOTAL GENERAL FUND")
    return Finding(Severity.BLOCK, "citywide_block_missing", "qcmr_o3",
                   "no value-less TOTAL GENERAL FUND line")


def drop_footnotes(lines: Sequence[Line], is_row: Callable[[Line], bool]
                   ) -> tuple[tuple[Line, ...], tuple[Line, ...]]:
    """A footnote opens with a mark and runs over its wrapped lines until a line that has
    values or is a known section or metric row. Returns (kept, footnote lines)."""
    kept: list[Line] = []
    notes: list[Line] = []
    in_note = False
    for line in lines:
        if _NOTE_START.match(line.text) and not has_values(line):
            in_note = True
        elif in_note and (has_values(line) or is_row(line)):
            in_note = False
        (notes if in_note else kept).append(line)
    return tuple(kept), tuple(notes)
```

The O-3 module applies `drop_footnotes` to each page's lines, then cuts the last page's body at
`citywide_end`. Footnote lines are returned as furniture, so the ink ledger (section 11.2) still
accounts for every word. The sub-department sections that print beside their parents are
`BREAKDOWN` rows listed per era in the O-3 row schema (QOBL-Q14). A department that is a parent
in one span and a division in another has a dated parent in the registry (QOBL-Q15). Whether a
parent block equals the sum of its sub-blocks is not verified, so `parent_is_sub_blocks` starts
at WARN (change 16).

Unlabeled subtotal on QCMR cash (QCASH-Q27). Current Year Appropriation prints amounts and no
label. Its `RowDef` has `labels = [""]` and `follows` set to the last expense line item. It can
match only the unlabeled valued line right after that row. Any other unlabeled valued line is an
`unknown_row` finding (R3).

### 6.3 Editions

An edition is what the publisher reports for one period: `EditionKey(series, period, stage)`. A
document is bytes: `DocumentVersion`, keyed by sha. One edition can have several versions. They
form one chain through `supersedes`, and `current` is the one version that nothing supersedes. A
QCMR edition's period is its fiscal quarter, `Period(first day of the quarter, printed end)`, so
editions never overlap and FY2026 Q4 is `qcmr:2026-06-30:none`.

| Case | Rule | Where |
|---|---|---|
| Revised attachment listed after the original (QPOS-Q32, RTT-Q06, MCITY-Q02) | Later `listed_at` wins, and on equal ones the link listed first; the earlier version stays in the index with `supersedes` pointing at it | `plan_watch` |
| Same bytes under two periods (MSCH-Q01, MCITY-Q08) | Rejected as `content_alias`; the missing period is reported as a gap | `plan_fetch`, `plan_watch`, `add_versions` |
| Same bytes of the same edition at a new URL | The URL joins that version's `urls`, after the ones it holds; nothing else changes | `add_versions` |
| A URL whose bytes changed, old pages pointing at new bytes (WAGE-Q10) | The index keys by sha, so the change is visible; `url_reused` plus a Wayback lookup for the old period | `plan_watch`, `pick_capture` |
| Printed period disagrees with the listing (QOBL-Q06, QCASH-Q07) | Rejected unless a `PRINTED_PERIOD` note names the sha and the printed text | `confirm_period` |
| BIRT same-coverage revision (BSALES-Q04) | A new sha for the same `EditionKey` is a new version; nothing is keyed by path | `plan_watch` |
| Stale link must not overwrite a good file (MCITY-Q09) | Nothing is overwritten; versions are added only after `confirm_period` | `plan_fetch` |
| No listing page (QSMR-Q01) | Catalog entries with shape `manual` hold the URLs; `Via.MANUAL` in the index | `parse_listing`, index |
| Old editions once held only as cut sections or excerpts (QCMR before FY2022, BiB FY2006 to FY2008 and proposed) | The whole documents are indexed from the owner's copies (section 16, decision 1). Where code cannot find a table's pages, a `TablePages` record names them. An edition with no full document is a `Gap` in the watch pull request, decided then | index, `declared_run` |
| Missing editions (QCASH-Q08, SUPCAP-Q02, SUPOP-Q38) | The catalog declares expected editions and lag; the difference is a `Gap` in the watch pull request | `plan_watch` |

### 6.4 Restatements

Every observation is published with its edition. No value is dropped because a later edition
prints the same period. `select_canonical` sets `is_canonical` per dataset policy.

| Policy | Rule for `is_canonical` | Datasets |
|---|---|---|
| `ALL_VINTAGES` | the newest edition that prints this (table, instance, row key, window, `Subject`) | QCMR four tables, collections City and School, Budget in Brief, supplemental, QSMR |
| `NEWEST_COVERING` | the newest version by upload stamp whose coverage holds the year | BIRT (BSALES-Q01, Q03), wage residency (WAGE-Q49, Q55) |
| `CURRENT_COLUMN` | the edition whose own window is the period; if none, the newest edition that prints it | sales (BSALES-Q13: FY2019 from FY2020's prior column), RTT (RTT-Q48), wage by industry (WAGE-Q47) |

The policy is computed once, in code, from the index. It is never typed again as data
(BSALES-Q05 is gone). Rows are grouped by `Subject` (section 2.2), never by column name. A
prior-year column and the earlier edition's current column have different names and the same
subject, so they land in one group. `is_canonical` is chosen inside one window: a quarter and a
year to date that cover the same months stay two series.

Cross-edition relations run in `datadesk.core.checks.series.cross_edition_checks`. Four of the
six relations first listed here are one statement, `same_subject_agrees`: two editions that print
the same row and the same subject should print the same value. It compares by span alone, so a
fiscal year to date at June 30 is checked against next year's prior-year actual.

- `same_subject_agrees` covers the adopted budget across a fiscal year's QCMR quarters, Q4
  against the next year's prior-year actual, sales and RTT prior columns against earlier
  editions, and supplemental prior actual against the previous edition's actual;
- FYTD deltas for collections stay declared (MCITY A13 to A15), since they relate two subjects;
- a list table's occurrence count per label between editions stays declared.

They are WARN because restatement is expected. Whether any of them should ever block is an
owner decision (section 16, decision 2). Promotion is a one-word severity change in code.

## 7. Row identity and the entity registry

Row identity is decided while parsing, by the table's own schema or grammar. The registry holds
what several families share and has official names or codes. It is the only home of their
spellings (change 11).

### 7.1 Row keys by table

| Table | Schema form | `RowKey` parts | Shared parts resolved in the registry |
|---|---|---|---|
| QCMR P-1 | closed, by period, root `line=total_all_funds` | `dept` or `group`, `breakdown` for Civilian and Uniform, `line` for the grand total | department (labels from the registry) |
| QCMR O-2 | grammar | `dept` (normalized label), `line` (printed label when two lines share a department, QOBL-Q54) | department via table-scoped aliases |
| QCMR O-3 | grammar plus a per-era sub-block list | `section`, `metric` (positions, class_100, overtime) | department |
| QCMR cash | closed, by period, with `within` blocks | `grid` (revenue, expense, lifecycle, balances), `line`, `memo` | tax concept (link only) |
| Collections City | closed, with blocks | `block` (fund scope), `tax` or `line`, `cohort` (current, prior) | tax concept (link only) |
| Collections School | closed, with blocks | `tax`, `cohort` | none; School entities are table-local (MSCH-Q35) |
| Wage industry and residency | closed | `industry`, `sub_industry`, `line` | none (ENT-Q51) |
| BIRT | closed | `sector`, `sub_sector`, `line` | none |
| Sales | closed, by period | `sector`, `store_type`, `line` | none |
| RTT | closed per zone | zone in the table instance; `section`, `class`, `line` | none |
| BiB obligation history | grammar | `dept` (from the running section), `class` | department, class |
| BiB fund summary | closed, by period | fund in the table instance; `line` | fund |
| BiB revenue schedule | grammar, text or scan | fund, schedule and category in the instance; `agency`, `refine`, `label` | fund, department |
| Supplemental activity tables | grammar | fund in the instance; `agency`, `class` or `label` | fund, department, class |
| Supplemental revenues | grammar | fund in the instance; `category`, `department`, `label` | fund, department |
| Supplemental capital | grammar | `agency`, `category`, `project` (label as printed); summary: `budget_year` | department |
| QSMR CF-3 | list grammar | `label`, `occurrence` when a label repeats; `line` for Subtotal, Other Payments, Total | none |

The printed label is published beside the key, always (ENT section 11, step 6).

### 7.2 The registry

```text
datadesk/data/registry/
  departments.toml     ~110 entities: names and codes with FY ranges, dated parents, residual
  groups.toml          combined scopes: City Rep. / Commerce, Streets including Sanitation
  funds.toml           17 City funds with dated codes; scopes ("All Funds", "Operating Funds")
  school_funds.toml    QSMR funds under their own ids; none is a City fund (QSMR section 6)
  classes.toml         major classes 100 to 900 with dated labels
  taxes.toml           ~25 tax concepts (link targets only, never series keys)
  relations.toml       merged_into, split_from, reported_under (fund and FY scope)
  aliases/<table>.toml table-scoped aliases with FY range and, for misprints, edition shas
```

One home for each spelling (change 11):

- A department, fund or tax spelling lives only in the registry: an official name with a year
  range, or a table-scoped alias.
- A row definition that names an entity carries no labels. `schema_for` fills them from
  `labels_for` and the row's `forms` templates. `load_row_schema` refuses an entity row with
  labels, and the lint repeats the check in CI.
- An OCR misspelling or a one-edition misprint is an alias with an `editions` list of file
  hashes. It matches in that file only (QPOS-Q09, SUPOP-Q34).
- Lines that belong to one table (cohorts, cash lines, collection lines, industries, RTT
  classes) keep their labels in that table's row schema. Putting them in a shared registry is
  what made one label claim several ids (ENT-Q01).

`lint_registry` runs in CI and in `datadesk check`, and blocks on:

1. One normalized or squashed label claimed by two entities, or by two `RowDef`s, whose (table,
   period, block) overlap. This catches the "retail" defect (ENT-Q11) and the two Streets
   meanings.
2. An alias with no table scope, or an OCR or misprint alias with no edition list.
3. An alias equal to its entity's own name after normalization (66 cases, ENT-Q63).
4. Overlapping date ranges for one code, one name or one parent.
5. A relation that names an unknown id or a year outside both entities' ranges.
6. A schema row with both `entity` and `labels`.
7. A gate year outside the edition range it governs (ENT-Q57).

The registry is published as its own dataset `registry` in every release, so gov-budget-data can
read department ids without owning a copy (ENT-Q65).

### 7.3 What happens when identity is unclear

| Situation | Closed table | Grammar table | List table |
|---|---|---|---|
| Label matches no `RowDef` or rule | BLOCK `unknown_row` | BLOCK `unknown_row` | BLOCK `unknown_row` |
| Label matches two `RowDef`s at one match stage | BLOCK `ambiguous_row` | not possible: the first rule wins, tested per rule | same |
| Two rows get one key | BLOCK `duplicate_row` (MDO-Base against the MDO block, ENT-Q61) | BLOCK `duplicate_row` | numbered `occurrence` parts |
| A required row is missing | BLOCK `missing_row` | not applicable | not applicable |
| Registry `Unknown` for a shared part | not applicable: labels come from the registry | WARN; `entity_status="unknown"`; a dataset can declare `identity_required` to block | not applicable |
| Registry `Ambiguous` | not applicable | BLOCK | not applicable |
| Entity of a key changes between releases | row diff `entity_changed`; blocks without `--accept-diff` (Codex review) | same | same |
| A key disappears and another appears in one document between releases | row diff `key_changed`; blocks without `--accept-diff` | same | same |

## 8. Checks and acknowledgments

### 8.1 Declaration

Checks are declared in each table module's `checks_for(era, period)` with `declare(...).add(...)`
chains over the six relation classes of section 2.1. A check has a stable id written by a person.
`suggest` may print candidate chains. It never runs at publish time and never adds a check.

Cross-table checks are built by code from the set of parsed tables and their keys:

- `bib_cross.cross_checks` for Budget in Brief (section 5.4);
- `rtt.cross_checks`, property total against location total;
- `qcmr_cash.cross_checks`, page 1 CLOSING BALANCE against page 2 General, at WARN until confirmed;
- `qsmr_cross.cross_checks`, OF-3 section totals against OF-1 rows (added with the QSMR).

Cross-edition checks are built in `checks.series`.

Checks that start at WARN, because no corpus run has shown they hold (change 16):

| Check | Table | Why WARN |
|---|---|---|
| `remaining_budget` outside Dedicated Parking | collections City | A11 is declared for Dedicated Parking only (MCITY section 5) |
| `percent_collected` | collections City | A12 was never declared for the City |
| `percent_collected` | supplemental revenues | never checked by the old code (SUPOP section 6) |
| `parent_is_sub_blocks` | QCMR O-3 | not verified (R1 section 7.4) |
| every cross-edition check | all | restatement is expected |
| `vendors_make_subtotal` | QSMR CF-3 | inferred; the dossier does not state it |

`datadesk suggest --promote` runs `promotions` over the corpus report and prints the WARN checks
that passed in every edition. The owner promotes one by changing its severity in code.

### 8.2 Engine semantics

1. Expansion. Each relation runs a fixed set of instances.
   - `RowSum`, `RowDifference`, `Ratio`: once per selected row.
   - `ColumnSum`: once per named column.
   - `ChildrenSum`: once per (selected parent that has at least one child, column).
   - `CellsEqual`: once per check value.
2. A total row is never one of its own parts, whatever the selector says. A test asserts it for
   every selector (change 1, R1, R2).
3. Operands. `Amount` gives its printed value. `Dash(ZERO)` gives 0. Everything else gives no
   value. An N/A operand whose row key is in `na_excluded` is dropped. A `PlusIfPrinted` operand
   with no value is dropped. `ChildrenSum` sums children whose additivity is `ADDITIVE` or
   `COMPONENT`; `AdditiveRows` selects `ADDITIVE` only.
4. `FirstPresent` resolves once per table: the first listed column the table printed. Its last
   column must be required, so it always resolves.
5. Outcome, in this order:
   - the total and every part have no value: no instance (an empty Sub-Total, SUPOP-Q23);
   - a required part has no value: `MISSING_OPERAND`, never a failure, never zero;
   - the total has no value in a row relation: `MISSING_OPERAND`;
   - the total has no value in a `ColumnSum`, `ChildrenSum` or `CellsEqual` and the parts sum to
     non-zero: `MISSING_TOTAL`. A total printed as a dash or left blank under valued parts is a
     source fault (SUPOP-Q24, BIB-Q51);
   - otherwise the residual is the total minus the signed sum of parts, exact in `Decimal`.
     `PASS` when `|residual| < bound` (strict, VAL-Q49), or `residual == 0` for `Exact`. Else
     `FAIL`.
6. Bound. `PerOperand(i)` gives `i x (1 + n) / 2` with n parts, the old bound at
   `tables/checks.py:80-100`. `Ratio` uses half the printed increment of the result cell.
7. Coverage (change 1). For every table in a check's scope, a declared check must return at
   least one result, else BLOCK `check_not_evaluated`. A check whose every result on a table is
   `MISSING_OPERAND` gives BLOCK `check_all_missing` (changed after the Codex review: evidence
   that disappears must not pass). A TOTAL or SUBTOTAL row with an Amount and
   no children gives BLOCK `total_without_parts` (change 2). The exception is a row that a
   declared `ColumnSum` or `CellsEqual` names as its total. This closes the silent loss of MSCH-Q14.
8. The engine reads `Table` values only. It cannot import words, lines or the lexer, and it
   never writes to a cell.

### 8.3 Report and proof

`CheckReport.results` holds every instance with outcome, residual, bound and operands, each with
its page and evidence. `report_rows` flattens it for the release (`checks.parquet`) and
`render_text` prints the open items grouped by document and check. Cell proof for the release:

| Proof | Meaning |
|---|---|
| `arithmetic` | the cell is a text-layer or reviewed value, and the total or a part in at least one `PASS`. It says the sums tie. It does not say the number sits under the right row or column: swapping two funds or two departments preserves every sum (Codex review, problem 1). |
| `ocr_arithmetic` | the cell is an OCR value with no reviewed reading, in at least one `PASS`. The totals tie, and a tie does not prove digits (change 4, R3 case F4). |
| `acknowledged` | the cell is in a covered failure and in no open failure. It wins over a `PASS` on the same cell. |
| `unchecked` | the cell is in no evaluated instance, or only in `MISSING_OPERAND` instances |

Binding is shown separately in `bound_by`. Evidence that a number is under the right name comes
from three places, none of them arithmetic: caption binding on every page, labeled page fixtures
per layout that tie a number to its row label and column caption, and the cell-by-cell
comparison with a pinned earlier release before a table first publishes (section 15, step 6).

OCR words below the confidence floor need a reviewed reading before they lex as a number. The
floor is a catalog value per series (section 16, decision 8).

### 8.4 Acknowledgments

One TOML file per edition: `datadesk/data/acks/<dataset>/<edition id>.toml`.

```toml
[[acknowledgment]]
id = "qcmr-positions-fy2011-q2-opa-omitted"
kind = "source_omission"
root = "opa-left-out-of-citywide-totals"
reason = """TOTAL ALL FUNDS leaves out OPA's 134 current positions. The (Over) Under column
on the same row proves the omission."""
reviewed_by = "owner"
reviewed_on = 2026-07-30

  [[acknowledgment.expects]]
  doc_sha256 = "<64 hex>"
  check = "all_funds_total"
  table = "qcmr_positions"
  row = "line=total_all_funds"
  column = "actual_total"
  residual = "-134"
  page = 37
```

Matching, in `match_acknowledgments`:

1. Index failures (`FAIL`, `MISSING_TOTAL`) by `FailureKey`.
2. An expectation whose row key has an occurrence part is `refused` (change 6).
3. For each other expectation in scope, find the failure with that key. None found gives `unused`.
   A different residual or total page gives `mismatched`. Otherwise the failure is covered.
4. A failure claimed by two expectations gives `double_covered`.
5. A `BLOCK` failure with no expectation is `blocking`.
6. BLOCK findings in scope (parse, coverage, unused records) are carried as `findings`.
7. `Gate.passed` only when all six lists are empty. One gate is computed per (dataset, edition),
   with `scope` set to that edition's document shas (change 17).

Why the key does not shift. Every part of `FailureKey` comes from something printed or declared:

- the file hash;
- a check id written by a person;
- a table instance from a printed banner;
- a row key from the schema or grammar, never from print order outside a list table;
- a column name from the era.

A re-extraction that moves rows, a new extraction tool version or a change to lane geometry
leaves the key alone (QCASH-Q48, SUPOP-Q41, VAL-Q44). A change that alters the value alters the
residual, and the acknowledgment stops matching (QCASH-Q47, MCITY-Q47). A property test adds
unrelated rows above a failing row and asserts the gate is unchanged (from B).

Moving the 215 old records. `datadesk acks migrate` runs the new parser on each edition, then
calls the pure function below. The owner reviews the proposals in a pull request.

```python
def propose_rekey(old: LegacyAck, report: CheckReport, index: ArchiveIndex,
                  page_map: Sequence[tuple[str, int, int]]) -> tuple[ProposedAck, ...]: ...
    # matches each old record by document, label pattern and residual (old floats rounded to
    # the printed precision) and translates cut-file pages through page_map
```

Old fingerprints and ordinals are not read, so the 102 inert records migrate like the rest
(VAL-Q43). The 63 August 2026 dash records do not migrate: they become one `DashRule`
(VAL-Q47). The 34 decimal repairs (33 FY07 Q3 cells and FY08 Q1 "69,2") become `ReviewedReading`
records, since no format inserts a decimal point (QCASH-Q21).

## 9. Errors

A problem in the documents is a returned value. An exception means a bug or a failed effect.

| Situation | Kind | Who handles it |
|---|---|---|
| Table pages not found, two page runs, era not chosen, a page that binds no columns or other columns than page 1 | `Failed` with findings; the table stops | gate; the owner fixes a band rule, an era or a note |
| Unknown, ambiguous, duplicate or missing row | `Finding` (BLOCK); the parse continues | gate; the owner adds a label, a schema row or a registry alias |
| A rule needs bold on a page without style | `Finding` (BLOCK) `style_unavailable` | the owner scopes the rule by era |
| Unreadable cell, or an OCR value under the confidence floor, without a reading | `Finding` (BLOCK) | the owner writes a `ReviewedReading` or a `WordSourcePlan` |
| Stale reading (the text in its box changed) | `Finding` (BLOCK) | the owner re-reviews |
| Two word sources disagree on a digit | `Finding` (BLOCK) `source_disagreement` | a `ReviewedReading` on the primary source |
| Unused record of any kind | `Finding` (BLOCK) `unused_record` | the owner removes or fixes it |
| Declared check with no evaluation, or a total with an Amount and no parts | `Finding` (BLOCK) | the owner fixes the declaration or the schema |
| Arithmetic failure | `Result` in the report; blocks its edition through `Gate` | the owner acknowledges after reading the page |
| `MISSING_OPERAND` | `Result`; never blocks; a check that is all missing on a table is a BLOCK (Codex review) | listed; cells stay `unchecked` |
| Registry `Unknown` in a grammar table | `Finding` (WARN) | listed |
| Printed period mismatch at fetch | `Rejection` in the plan | the watch or fetch pull request shows it |
| Key or entity change between releases | `RowDiff.key_changed` or `entity_changed`; blocks without `--accept-diff` | the owner reviews the diff |
| `Table` or `RowSchema` invariant violated in `__post_init__` | `ValueError` | a bug: a loader or `assemble` should have produced a finding |
| HTTP, S3 or Textract error | exception from the adapter | the executor retries the same plan item up to three times, then stops; index and pointer are written last, so nothing is half committed |
| Hash mismatch on staged or downloaded bytes | `StagingCorrupted`, `IntegrityError` | stop; never retried silently |

Findings are collected per line (change 19). A page-level failure stops its table, because
nothing below it can be read. A line-level problem becomes a finding and the parse continues, so
one run shows every problem in an edition.

The shell is the only place that catches exceptions, and only effect exceptions. A `ValueError`
from the core propagates and fails the command, because it is a bug.

## 10. Caching and determinism

Words are cached because extraction is slow and OCR costs money. Parse results are cached under
a key that covers every input, so a stale parse cannot be served (change 14). There is no
staleness graph.

| Cache | Key | Value | Where |
|---|---|---|---|
| Words, text layer | `sha256(doc sha, page set, tool string)` | encoded `Document` | `LocalCache`; optional shared copy in the object store |
| Words, OCR | `sha256(doc sha, page, Textract config)` | raw Textract JSON | private object store, permanent (it costs money) |
| Parse results | `sha256(word keys, code tree sha, record slice sha, registry sha, schema sha)` | encoded `ParseResult` | `LocalCache` |
| PDFs | doc sha | bytes | public object store; git-ignored local copy |
| Reader downloads | file sha | bytes | `phillyledger` cache dir |

The code tree sha is the SHA-256 of every source file under `checkedtables/` and
`datadesk/core/`, sorted by path (from B). `gather_repo` computes it and passes it in as a value.
It is coarse on purpose. Any code change re-parses every table, which takes minutes from cached
words. A per-module key would need an import graph, which is the staleness machinery the old
system grew. The tool string carries the extraction library version and options, so the cache
cannot serve words from another extractor.

Determinism rules:

- Every tuple a core function returns is sorted by a declared key. Findings sort by `Finding`
  order, results by `FailureKey`, rows by table then key.
- Money and counts are `Decimal`, from text. No float reaches a value, a residual or a bound.
  Residuals in TOML are decimal strings.
- `release_id` and `created_at` are arguments. They appear only in the manifest.
- Parquet is written with a fixed Arrow schema, dictionary encoding off, a pinned writer version
  and no timestamps in metadata. CSV uses `\n`, UTF-8, quoting only when needed, rows in key
  order.
- JSON (index, manifest, plans) is rendered with sorted keys and no whitespace variation.
- A test runs `plan_release` twice on the same inputs and compares plans and blobs byte for byte.

## 11. Tests

### 11.1 Layers

| Layer | What | Needs | Runs |
|---|---|---|---|
| `checkedtables` unit | every pure function, on pages built by `testing.page_from_text` | nothing | every commit |
| `checkedtables` property | lexer, line grouping, ink ledger, engine, matcher invariants (Hypothesis) | nothing | every commit |
| `checkedtables` shape | parameter rules, field snapshots, relation and note lists, size budget | nothing | every commit |
| `datadesk.core` unit | listing parsers, period readers, `plan_watch`, `plan_fetch`, `plan_parse`, registry lint, vintage, release plan | literal strings and values | every commit |
| Table fixtures | each table parser on frozen word fixtures of real pages | fixture modules (Python values) | every commit |
| Records | every TOML record loads, every ack and reading is used, lint passes | the data directory, read by a shell-side conftest | every commit |
| Adapter contracts | each port's fake and real adapter pass the same tests | network or MinIO for the real ones | nightly and before release |
| Corpus | every archived edition parses and its gate passes | the archive | before release |
| Canary | one full run from bytes to a staged release | fakes plus two archived PDFs | every commit |
| Purity | AST scan of `checkedtables` and `datadesk.core` for `open`, `print`, `input`, `.now()`, `.today()`, `os.`, `random`, `time.`, `builtins`, `__import__`, and mutable module state: a module-level assignment of a list, dict or set display, a comprehension of one, or a call to `list`, `dict`, `set` or `bytearray`. The scan also fails every relative import, and every import from outside the package that the import pin below does not hold | nothing | every commit |

The core suites run under `pytest-socket` with sockets disabled and an empty temporary directory
as the working directory (from A). Word fixtures of real pages are generated once by
`datadesk fixture <sha> <pages>` into `tests/fixtures/words/<series>_<edition>_p<n>.py` as Python
literals, so importing them is not I/O.

pytest-socket replaces only the names `socket.socket`, `socket.getaddrinfo` and
`socket.gethostbyname` and lifts its block before fixture finalizers run, so an audit hook in the
root `conftest.py` also refuses the `socket.__new__` and resolver audit events unless the running
test carries the `enable_socket` marker. Each core test module also starts in its own empty
folder, so a module-scoped fixture never sees the checkout.

The pure packages import from outside themselves only by name. `tests/test_purity.py` pins, for
each pure package, every `module.name` pair that it imports, and the test fails when the pairs in
the source differ from the pin in either direction. The scan reads each file as the importer
does, coding cookie included. An import statement that binds an outside module, a star import
from outside, and a pinned name that is itself a module all fail, so no import, read as written,
gives pure code a module object from outside. A star import from outside fails whatever the pin
holds. `checkedtables` counts its own modules as inside. `datadesk.core` counts its own modules and
`checkedtables` as inside. A name taken from an outside module counts as inside when its full name
is at or under an inside name, as `from datadesk import core` is. A relative import fails, inside or
out. Python resolves it through the module global `__package__`, which source can rebind, so pure
code imports by absolute name. The scan reads source as written. Source that changes a module global
at run time, such as `__path__`, can still make an absolute import bind another module, and a static
scan cannot see that change. The note "The pure packages can still reach effects the gates do not
name" in `docs/plan-notes.md` lists the routes found, and review reads for them. The modules each
package imports from are a closed list, given below. A pull request that imports from a module
outside the list changes the list and the pin together.

| Package | Outside modules it imports from |
|---|---|
| `checkedtables` | `collections.abc`, `dataclasses`, `decimal`, `enum`, `re`, `statistics`, `typing` |
| `datadesk.core` | `collections`, `collections.abc`, `dataclasses`, `datetime`, `enum`, `hashlib`, `json`, `re`, `tomllib`, `types`, `typing` |

### 11.2 Property tests

- Lexer round trip: any `Decimal` with k decimals, printed with commas, parentheses, a leading
  minus or a dollar sign, lexes back to itself.
- An `Amount`'s digits are the digits of its words, always.
- Every word lands in exactly one line.
- No ink lost (from A). On any generated table page, every word ends in exactly one place. That
  is a cell, a label, a prefix, declared furniture, or a stray-word or unknown-row finding.
- A total row is never one of its own parts, for every `RowSel` case.
- Every TOTAL or SUBTOTAL row in an assembled table has children or holds no Amount. The one
  exception is a row that a declared `ColumnSum` or `CellsEqual` names as total.
- Adding unrelated rows above a failing row leaves the gate unchanged (from B). This is the shift
  that broke ordinal keys.
- Permuting acknowledgments or results leaves the gate unchanged.
- `read_grammar` keys are unique, and every parent exists, for any row sequence under `Unique()`.
- Under `Occurrences`, numbering depends only on labels in print order inside the block.
- `checks_for` and `cross_checks` give the same `CheckSet` when every `Amount` in the input
  tables is replaced by another value (section 5 rule; R3).
- Catalog test, for every table in `TABLES`, every era, and every scope the era allows (each
  stage, each window, a cutoff before and after the period end, optional columns printed and
  absent):
  - every money, count and percent column has exactly one `MeasureSpec`, and every `RowMeasure`
    names a declared row and column, so the two lists cannot drift (R3);
  - no two published columns of one table have the same `description`. This is the test the old
    repo would have failed for O-2's three columns under `budget_estimate` (QOBL-Q34);
  - every operand in a `Derived.of` is a published column of the same table, and where a
    `RowDifference` or `Ratio` check names the column as its `result`, the check's operands are
    the same columns;
  - every `Dim.FUND` value is a registry fund id or `ALL`, and other dimension values come from
    `DIM_VALUES`;
  - every list member has a line in `DEFINITIONS`, and every `Quantity` member is used by at
    least one table.

### 11.3 Example tests

```python
def test_bare_integers_never_join() -> None:                       # QPOS-Q27, VAL-Q21
    cell = lex_cell(words("12", "345"), COUNT_COLUMN, SourceKind.TEXT_LAYER)
    assert isinstance(cell, Unreadable)


def test_transliteration_refuses_a_digit_swap() -> None:           # H1, QCASH-Q22
    assert transliteration_ok("1o4.o", "104.0")
    assert transliteration_ok("2918", "291.8")
    assert not transliteration_ok("65.8", "85.8")
    assert not transliteration_ok("77,500,000", "7,500,000")


def test_police_lesson_missing_column_is_a_binding_finding() -> None:   # SUPOP-Q14
    page = page_from_text(REVENUES_PAGE_WITHOUT_PERCENT, sha=SHA, page=1)
    cut = cut_pages(Layout(supp_revenues.ERAS, BODY), (page_lines(page),), date(2021, 6, 30))
    assert isinstance(cut, Finding) and cut.code == "column_unbound"


def test_unevaluated_check_blocks() -> None:                       # MSCH-Q14, change 1
    report = run_checks([table_without_column("remaining")], [checks_naming("remaining")])
    assert [f.code for f in report.findings] == ["check_not_evaluated"]


def test_grand_total_has_category_totals_as_children() -> None:    # change 2, R1
    rows = read_grammar(cut_rows(REVENUES_TWO_CATEGORIES), supp_revenues.GRAMMAR).rows
    grand = next(r for r in rows if r.key == RowKey.of(line="total_net_revenue"))
    assert {r.key for r in rows if r.parent == grand.key} == {TAXES_TOTAL, NON_TAX_TOTAL}


def test_bold_rule_on_a_scan_blocks() -> None:                     # change 5, BIB-Q21
    matched = read_grammar(cut_rows(page_from_text("#ocr\n" + SCHEDULE, sha=SHA, page=1)),
                           bib_revenue_schedule.TEXT_GRAMMAR)
    assert "style_unavailable" in {f.code for f in matched.findings}


def test_fy07_q4_text_layer_disagrees_with_textract() -> None:     # change 3, QCASH-Q23
    result = run_parse_job(FY07_Q4_JOB, FY07_Q4_TEXT, FY07_Q4_OCR, context(FY07_Q4))
    flagged = {f.message for f in result.findings if f.code == "source_disagreement"}
    assert flagged == {"85.8 / 65.8", "109.7 / 108.7", "1,185.9 / 1,165.9"}


def test_ack_on_an_occurrence_key_is_refused() -> None:            # change 6
    gate = match_acknowledgments(REPORT, [ack(row=RowKey.of(label="acme", occurrence="2"))], SCOPE)
    assert gate.refused and not gate.passed


def test_positions_fy2011_q2_fails_on_opa() -> None:               # QPOS-Q18, real-word fixture
    parsed = qcmr_positions.parse(FY2011_Q2_P1, context(FY2011_Q2))
    assert isinstance(parsed, Parsed)
    report = run_checks(parsed.tables, [qcmr_positions.checks_for("p1_ten_columns", FY2011_Q2.period)])
    [failure] = [r for r in report.failures()
                 if r.key.check_id == "all_funds_total" and r.key.column == "actual_total"]
    assert failure.residual == Decimal("-134")


def test_plan_watch_is_idempotent() -> None:
    plan = plan_watch(CATALOG, LISTINGS, INDEX, date(2026, 11, 22))
    after = add_versions(INDEX, versions_for(plan))
    assert isinstance(after, ArchiveIndex)
    assert plan_watch(CATALOG, LISTINGS, after, date(2026, 11, 22)).fetch == ()


def test_release_bytes_are_deterministic() -> None:
    a = plan_release(RELEASE_INPUTS)
    b = plan_release(RELEASE_INPUTS)
    assert isinstance(a, ReleasePlanned) and a == b and a.blobs == b.blobs
```

### 11.4 Library shape tests (from B)

These are the guard against regrowth. A change to the kit's shape fails a test, so it is a
visible and reviewed act (change 10).

```python
# checkedtables/tests/test_library_shape.py
def test_no_bool_parameters_and_at_most_four() -> None:
    for fn in public_functions(checkedtables):
        params = list(inspect.signature(fn).parameters.values())
        assert len(params) <= 4, fn.__qualname__
        assert not bool_parameters(fn), fn.__qualname__


def test_kit_dataclass_fields_are_pinned() -> None:
    assert {cls.__name__: field_names(cls) for cls in kit_dataclasses()} == FIELD_SNAPSHOT


def test_bool_fields_are_page_facts_only() -> None:
    assert bool_fields(kit_dataclasses()) == {("Word", "bold"), ("Column", "printed")}


def test_closed_lists_are_pinned() -> None:
    assert [c.__name__ for c in get_args(Check)] == ["RowSum", "RowDifference", "ColumnSum",
                                                     "ChildrenSum", "Ratio", "CellsEqual"]
    assert [c.__name__ for c in get_args(RowSel)] == ["AllRows", "Keys", "Kinds", "AdditiveRows",
                                                      "Has", "Except"]
    assert [k.value for k in NoteKind] == ["printed_period", "cutoff", "header_misprint",
                                           "drop_line", "header_illegible"]
    assert [k.value for k in Kind] == ["actual", "budget", "projection"]
    assert [v.value for v in Version] == ["none", "adopted", "revised", "proposed", "target"]
    assert [w.value for w in Window] == ["month", "quarter", "fiscal_ytd", "calendar_ytd",
                                         "fiscal_year", "calendar_year", "tax_year"]
    assert [h.value for h in How] == ["difference", "percent_change", "ratio", "share",
                                      "annual_growth"]
    assert [d.value for d in Dim] == ["fund", "residency", "tax_base"]
    assert len(Quantity) == 14


def report_budget() -> None:                    # printed in CI and in the PR; never fails the build
    print(f"checkedtables: {source_lines(checkedtables)} lines (budget 3,800), "
          f"{len(public_names(checkedtables))} public names (budget 140)")
```

`bool_parameters` names each parameter whose annotation is `bool` or a union with `bool` as a
member, so `flag: bool | None` and `flag: Optional[bool]` fail as `flag: bool` does. It
evaluates each parameter's annotation in the function's module, a quoted one and a quoted member
such as `Optional["bool"]` included, and never the return type. A name that does not resolve at
run time, such as one imported only under `TYPE_CHECKING`, stands for an unknown type, so it
raises nothing and a `bool` beside it in a union still counts. A `bool` inside another type, such
as `tuple[bool, ...]`, does not count. A method's bound first parameter does not count toward the
four. `public_functions` reads each function and class, once, that a public name in a public
module reaches, when its `__module__` is the scanned module or a module under it, private modules
included. A public class's methods, and its `__init__` when it is not a dataclass, include those
it inherits from a base class in the scanned package, private or not, each read once as the class
resolves it, without `self`. A base outside the package, such as `object`, `Enum` or `Exception`,
adds nothing. A dataclass's generated constructor stays out, because the two field tests pin its
fields and allow the `bool` fields `Word.bold` and `Column.printed`.

`NoteKind` lives in `datadesk`, but its list is pinned in the same test file. A new kind of
per-edition switch is then as visible as a new kit field (R1). The six vocabulary lists are pinned
the same way, so a new word for a column is a reviewed change with a definition, never a string
typed into one table module. The `*_common` family modules in
`datadesk` run the first test too.

### 11.5 Contract tests

One suite per port, run against the fake and the real adapter:

| Port | Fake | Real |
|---|---|---|
| `ObjectStore` | dict store | S3 API via MinIO |
| `Http` | replays recorded responses | one phila.gov listing, nightly |
| `PdfReader` | none needed | two committed tiny PDFs: a text layer with a drawn grid and bold words, and an image page |
| `OcrService` | returns archived responses | one page against Textract, by hand, with `--spend` |
| `GitHost` | records the plan | a sandbox repository, before release |
| `LocalCache` | dict | temp directory |

The canary runs `fetch` of two pinned PDFs from the fake HTTP; from build step 13 it begins with
`watch` on a recorded listing. It then runs `parse`, `check` and `release` into a
fake store and compares the manifest with a golden file.

## 12. Module layout

Three packages in one uv workspace. Estimates are lines of Python without tests or data. They are
estimates; nothing has been written.

### 12.1 `packages/checkedtables` (on PyPI)

| Module | Job | Lines |
|---|---|---:|
| `__init__.py` | public re-exports, nothing else | 30 |
| `refs.py` | `Box`, `WordRef` | 60 |
| `kinds.py` | `SourceKind`, `ValueKind`, `DashMeaning`, `Presence`, `PercentSign` | 40 |
| `words.py` | `WordSource`, `Word`, `Rule`, `Page`, `Document` | 90 |
| `labels.py` | `Label`, kept apart so tables and checks never import words | 30 |
| `text.py` | `normalize_space`, `normalize_label`, `squash`, `parse_label`, `split_line_prefix` | 150 |
| `lines.py` | `Line`, `PageLines`, `group_lines`, `page_lines`, `has_values`, `lines_text` | 120 |
| `pages.py` | `PageRun`, `BodyRule`, `header_band`, `find_runs`, `only_run`, `slice_body` | 130 |
| `columns.py` | `NumberFormat`, `ColumnSpec`, `Era`, `Lane`, `Binding`, `choose_era`, lanes, `bind_columns`, `bind_by_position`, `cut_line` | 330 |
| `pipeline.py` | `Layout`, `CutPage`, `CutPages`, `cut_pages` with the page agreement check | 130 |
| `cells.py` | the `Cell` union and `Reading` | 90 |
| `lex.py` | `split_numeric_runs`, `lex_cell`, `transliteration_ok` | 230 |
| `records.py` | `ReviewedReading`, `DashRule`, `CellRecords`, `reading_for`, `apply_reading` | 140 |
| `table.py` | `RowKind`, `Additivity`, `RowKey`, `Finding`, `TableId`, `Column`, `Row`, `Table` | 190 |
| `rows.py` | `RawRow`, `RowDef`, `RowSchema`, `KeyedRow`, `RowMatch`, `match_rows`, `join_rows`, `starts_known_row`, `stray_findings` | 290 |
| `grammar.py` | `Values`, `Style`, `AllSlots`, `RowRule`, `Unique`, `Occurrences`, `RowGrammar`, `read_grammar` | 260 |
| `assemble.py` | `Assembly`, `assemble` | 140 |
| `checks/dsl.py` | tolerance, selector and term unions, the six relations, `CheckSet`, `declare` | 280 |
| `checks/engine.py` | `Outcome`, `Evidence`, `FailureKey`, `Operand`, `Result`, `CheckReport`, `run_checks`, `evaluate` | 270 |
| `checks/coverage.py` | `check_coverage`: unevaluated checks, totals without parts | 90 |
| `checks/acks.py` | `AckKind`, `ExpectedFailure`, `Acknowledgment`, `Gate`, `match_acknowledgments` | 190 |
| `checks/report.py` | `report_rows`, `render_text` | 100 |
| `suggest.py` | `Suggestion`, `suggest_checks`, `promotions`, `render_chain` | 210 |
| `testing.py` | `page_from_text`, `doc_of`, shipped for users' tests (from B) | 90 |
| **total** | 24 modules | **3,680** |

### 12.2 `packages/phillyledger` (on PyPI, the reader)

| Module | Job | Lines |
|---|---|---:|
| `__init__.py` | public re-exports | 20 |
| `manifest.py` | release format schema, the `vocabulary` block, `parse_manifest`, `render_manifest`; rejects a file whose `kind`, `version`, `window`, `quantity`, `how` or dimension name is not in its manifest | 240 |
| `plan.py` | `LoadRequest`, `LoadPlan`, `plan_load`, `cite` | 130 |
| `api.py` | `load`, `path`, `datasets`, `cite`: thin shell | 170 |
| `pin.py` | `phillyledger.lock` model | 60 |
| `lineage.py` | `predecessor_spans`, moved as is | 90 |
| `_shell/http.py` | HTTP adapter | 60 |
| `_shell/cache_dir.py` | content-addressed cache adapter | 70 |
| **total** | 8 modules | **840** |

### 12.3 `packages/datadesk` (never published)

| Module | Job | Lines |
|---|---|---:|
| `core/domain.py` | `Stage`, `Period`, `EditionKey`, `Via`, `Holding`, `DocumentVersion`, `ArchiveIndex`, `sort_versions`, `index_problem` | 150 |
| `core/vocab.py` | `Kind`, `Version`, `Window`, `How`, `Dim`, `Quantity`, `DIM_VALUES`, `DEFINITIONS` | 120 |
| `core/measures.py` | `Basis`, `Stated`, `Derived`, `NotPublished`, `MeasureSpec`, `RowMeasure`, `MeasureSet`, `Scope`, `Subject`, `scope_for`, `measure_for`, `period_of`, `subject_of`, `description` | 230 |
| `core/context.py` | `ParseContext`, `Parsed`, `Failed` | 80 |
| `core/periods.py` | fiscal mapping, month matching, window year basis | 200 |
| `core/catalog.py` | `SourceCatalog`, `SourceEntry`, `DatasetSpec` and their TOML loaders | 160 |
| `core/listings/document_finder.py` | listing parser for document-finder posts | 160 |
| `core/listings/phila_documents.py` | listing parser for phila.gov document pages | 170 |
| `core/listings/manual.py` | catalog-typed URLs for sources with no listing (QSMR) | 40 |
| `core/listings/titles.py` | per-series title rules: stage, period, infographics | 190 |
| `core/watch.py` | `plan_listing_fetches`, `judge_listing_responses`, `plan_watch`, `pick_capture`, `plan_pull_request` | 320 |
| `core/fetch.py` | `confirm_period`, `plan_fetch` | 230 |
| `core/index.py` | archive index parse, render, add | 100 |
| `core/records.py` | record types, TOML loaders, `records_for`, `unused_records`, `drop_noted_lines`, `illegible_pages`, `declared_run` | 370 |
| `core/rowschemas.py` | `load_row_schema`, `schema_for` with registry labels and forms | 200 |
| `core/registry/model.py` | entity, alias, relation and resolution types | 120 |
| `core/registry/load.py` | TOML loaders | 110 |
| `core/registry/resolve.py` | `resolve`, `resolve_fund`, `labels_for`, `normalize_printed_code` | 190 |
| `core/registry/lint.py` | `lint_registry` | 170 |
| `core/ocr.py` | `textract_to_document` | 90 |
| `core/codec.py` | encode and decode `Document` and `ParseResult` | 220 |
| `core/words_audit.py` | `compare_sources` | 90 |
| `core/parse_plan.py` | `WordJob`, `ParseJob`, `ParsePlan`, `OcrPlan`, `plan_parse`, `plan_ocr`, `parse_context`, `run_parse_job` | 215 |
| `core/vintage.py` | `VintagePolicy`, `select_canonical` by `Subject` | 100 |
| `core/checks/series.py` | `cross_edition_checks`, `same_subject_agrees` | 200 |
| `core/checks/run.py` | `checks_for_document`, `check_all`: checks, coverage, one gate per edition | 150 |
| `core/acks_migrate.py` | `propose_rekey` for the 215 old records | 140 |
| `core/release/rows.py` | `ReleaseRow`, `Proof`, `to_release_rows` | 180 |
| `core/release/proof.py` | `proof_of` | 110 |
| `core/release/provenance.py` | `verify_cell_provenance` | 90 |
| `core/release/encode.py` | `encode_parquet`, `encode_csv` | 130 |
| `core/release/diff.py` | `diff_rows`, `RowDiff` | 150 |
| `core/release/plan.py` | `ReleaseInputs`, `ReleasePlan`, `plan_release`, per-edition withholding | 210 |
| `core/articles.py` | `ArticleFigure` records and `recompute_figures` against a pinned release (section 18) | 80 |
| `core/tables/catalog.py` | `TableEntry`, `TABLES`, `entry` | 90 |
| `core/tables/qcmr_common.py` | QCMR band test and quarter helpers | 60 |
| `core/tables/qcmr_cash.py` | cash page 1 grids, `split_grids`, `month_kind`, `find_balance_page`, page 2 | 225 |
| `core/tables/qcmr_obligations.py` | O-2 | 120 |
| `core/tables/qcmr_personal_services.py` | O-3, `citywide_end`, `drop_footnotes` | 170 |
| `core/tables/qcmr_positions.py` | P-1 (section 5.1) | 90 |
| `core/tables/collections_common.py` | `dedupe_overprint`, `attach_stacked_labels`, `caption_year_findings`, `money_measures` | 170 |
| `core/tables/collections_city.py` | City (section 5.3) | 130 |
| `core/tables/collections_school.py` | School | 120 |
| `core/tables/wage_industry.py` | wage by industry, `period_kind` | 130 |
| `core/tables/wage_residency.py` | wage by resident status | 110 |
| `core/tables/birt.py` | BIRT by sector, two tax years per page | 110 |
| `core/tables/sales.py` | sales tax by sector | 100 |
| `core/tables/rtt.py` | realty transfer tax, `split_zones`, `cross_checks` | 150 |
| `core/tables/bib_common.py` | Budget in Brief page and banner helpers | 60 |
| `core/tables/bib_history.py` | general fund obligation history | 100 |
| `core/tables/bib_fund_summary.py` | operating fund summary | 100 |
| `core/tables/bib_revenue_schedule.py` | revenue schedules, `grammar_for`, `SCAN_SUB_BANNERS` | 140 |
| `core/tables/bib_cross.py` | cross-table checks (section 5.4) | 60 |
| `core/tables/supp_common.py` | `Statement`, `split_statements`, `lift_subtotal_labels`, `join_wrapped_labels`, `link_departments` | 180 |
| `core/tables/supp_activity.py` | agency by class, fund by class | 120 |
| `core/tables/supp_revenues.py` | Statement of Net Revenues (section 5.2) | 125 |
| `core/tables/supp_by_source.py` | revenues by major source | 90 |
| `core/tables/supp_summaries.py` | summary activity, summary revenues | 110 |
| `core/tables/supp_capital.py` | capital activity, prior, summary | 140 |
| `shell/ports.py` | the six protocols | 80 |
| `shell/settings.py` | `Settings`, `load_settings(environ)` | 50 |
| `shell/gather.py` | `gather_repo`, `RepoSnapshot`, code tree sha | 110 |
| `shell/adapters/http_httpx.py` | `Http` adapter | 60 |
| `shell/adapters/s3.py` | `ObjectStore` adapter | 140 |
| `shell/adapters/textract.py` | `OcrService` adapter | 80 |
| `shell/adapters/pdf_pdfplumber.py` | `PdfReader` adapter | 210 |
| `shell/adapters/cache_dir.py` | `LocalCache` adapter | 60 |
| `shell/adapters/github.py` | `GitHost` adapter | 110 |
| `shell/run_watch.py` | watch executor | 85 |
| `shell/run_fetch.py` | fetch executor | 60 |
| `shell/run_ocr.py` | OCR executor, only behind `--spend` | 50 |
| `shell/run_parse.py` | parse executor | 90 |
| `shell/run_release.py` | release executor | 75 |
| `shell/report.py` | printing findings, plans and gates | 140 |
| `shell/cli.py` | `datadesk` commands; reads the clock once | 240 |
| **total** | 75 modules | **10,105** |

`datadesk/data/` holds data, not code: `catalog.toml`, `rows/*.toml` (one per table),
`registry/`, `acks/` and `records/`. It is not in the line counts.

### 12.4 Totals

| Package | Modules | Lines |
|---|---:|---:|
| `checkedtables` | 24 | 3,680 |
| `phillyledger` | 8 | 840 |
| `datadesk` (core 8,465, shell 1,640) | 75 | 10,105 |
| **Grand total** | **107** | **14,625** |
| QSMR, added in build step 14 | 13 | 1,290 |
| Grand total with the QSMR | 120 | 15,915 |

QSMR modules, for the last build step:

| Module | Job | Lines |
|---|---|---:|
| `core/tables/qsmr_common.py` | QSMR band test, period reader, `caption_lanes` | 80 |
| `core/tables/qsmr_vendor_payments.py` | CF-3 (section 5.5) | 110 |
| `core/tables/qsmr_*.py, 10 more` | OF-1 to OF-3, CF-1, CF-2, P-1, P-2, SM-1, SM-4a, SM-5 | 1,050 |
| `core/tables/qsmr_cross.py` | OF-3 section totals against OF-1 | 50 |
| **total** | 13 modules | **1,290** |

This is about 3,500 lines more than design C's 11,100. The difference is in parts the reviews
asked for or C left uncounted, plus the column vocabulary added after the reviews:

| Part | Lines |
|---|---:|
| parse cache codec (`core/codec.py`) | 220 |
| `cut_pages` pipeline, which removes about 25 copied lines from each table module | 130 |
| check coverage, `check_all` and per-edition gates | 240 |
| kit record types and `testing.py` | 230 |
| `acks_migrate.py` and `gather.py`, not counted in C | 250 |
| closed unions in the check DSL, era-scoped grammars, O-3 and cash page-2 rules | about 600 |
| the remaining tables, re-estimated after writing section 5 | about 800 |
| the column vocabulary: `vocab.py`, the larger `measures.py`, the manifest block, and about 10 lines of column descriptions in each table module | 555 |
| declared table pages for old reports, and the supplemental title rule (decisions 1 and 4) | 60 |
| changes from the Codex review (section 18.5) | 405 |

The table modules shrink with `cut_pages`, but the estimates above do not count that saving
twice. The QSMR estimate comes from R3's three parsers, about 100 lines each, and the eight
smaller tables.

### 12.5 Import rules

Inside `checkedtables` the dependency order is `refs` and `kinds`, then `labels`, `cells`, `table`
and `checks`. Separately `words`, `lines`, `text`, `pages`, `columns`, `pipeline`, `lex`,
`records`, `rows`, `grammar`, `assemble` and `suggest` sit above `table`. `checks` imports none of
them, so arithmetic can never reach a word.

```toml
[tool.importlinter]
root_packages = ["checkedtables", "phillyledger", "datadesk"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "checkedtables holds no I/O and no Philadelphia"
type = "forbidden"
source_modules = ["checkedtables"]
forbidden_modules = ["phillyledger", "datadesk", "pdfplumber", "pypdfium2", "fitz", "boto3",
                     "botocore", "httpx", "requests", "urllib", "http", "pyarrow", "logging",
                     "subprocess", "socket", "asyncio", "threading", "os", "pathlib", "time",
                     "random", "tempfile", "shutil", "pytest", "hypothesis", "importlib"]

[[tool.importlinter.contracts]]
name = "arithmetic never sees words"
type = "forbidden"
source_modules = ["checkedtables.checks"]
forbidden_modules = ["checkedtables.words", "checkedtables.lines", "checkedtables.text",
                     "checkedtables.pages", "checkedtables.columns", "checkedtables.pipeline",
                     "checkedtables.lex", "checkedtables.records", "checkedtables.rows",
                     "checkedtables.grammar", "checkedtables.assemble", "checkedtables.suggest",
                     "checkedtables.testing"]

[[tool.importlinter.contracts]]
name = "the reader stands alone"
type = "forbidden"
source_modules = ["phillyledger"]
forbidden_modules = ["datadesk", "checkedtables", "pdfplumber", "boto3", "botocore", "logging",
                     "subprocess"]

[[tool.importlinter.contracts]]
name = "the reader's core is pure"
type = "forbidden"
source_modules = ["phillyledger.manifest", "phillyledger.plan", "phillyledger.pin",
                  "phillyledger.lineage"]
forbidden_modules = ["phillyledger.api", "phillyledger._shell", "httpx", "urllib", "http", "os",
                     "pathlib", "socket", "time", "random", "logging"]

[[tool.importlinter.contracts]]
name = "datadesk core is pure"
type = "forbidden"
source_modules = ["datadesk.core"]
forbidden_modules = ["datadesk.shell", "pdfplumber", "pypdfium2", "fitz", "boto3", "botocore",
                     "httpx", "requests", "urllib", "http", "logging", "subprocess", "socket",
                     "asyncio", "threading", "os", "pathlib", "time", "random", "tempfile",
                     "shutil", "importlib"]

[[tool.importlinter.contracts]]
name = "shell over core"
type = "layers"
layers = ["datadesk.shell", "datadesk.core"]

[[tool.importlinter.contracts]]
name = "table modules do not import each other"
type = "independence"
modules = ["datadesk.core.tables.qcmr_cash", "datadesk.core.tables.qcmr_obligations",
           "datadesk.core.tables.qcmr_personal_services", "datadesk.core.tables.qcmr_positions",
           "datadesk.core.tables.collections_city", "datadesk.core.tables.collections_school",
           "datadesk.core.tables.wage_industry", "datadesk.core.tables.wage_residency",
           "datadesk.core.tables.birt", "datadesk.core.tables.sales", "datadesk.core.tables.rtt",
           "datadesk.core.tables.bib_history", "datadesk.core.tables.bib_fund_summary",
           "datadesk.core.tables.bib_revenue_schedule", "datadesk.core.tables.bib_cross",
           "datadesk.core.tables.supp_activity", "datadesk.core.tables.supp_revenues",
           "datadesk.core.tables.supp_by_source", "datadesk.core.tables.supp_summaries",
           "datadesk.core.tables.supp_capital"]

[[tool.importlinter.contracts]]
name = "family helpers do not import table modules"
type = "forbidden"
source_modules = ["datadesk.core.tables.qcmr_common", "datadesk.core.tables.collections_common",
                  "datadesk.core.tables.bib_common", "datadesk.core.tables.supp_common"]
forbidden_modules = ["datadesk.core.tables.catalog", "datadesk.core.tables.qcmr_cash",
                     "datadesk.core.tables.qcmr_obligations",
                     "datadesk.core.tables.qcmr_personal_services",
                     "datadesk.core.tables.qcmr_positions", "datadesk.core.tables.collections_city",
                     "datadesk.core.tables.collections_school",
                     "datadesk.core.tables.wage_industry", "datadesk.core.tables.wage_residency",
                     "datadesk.core.tables.birt", "datadesk.core.tables.sales",
                     "datadesk.core.tables.rtt", "datadesk.core.tables.bib_history",
                     "datadesk.core.tables.bib_fund_summary",
                     "datadesk.core.tables.bib_revenue_schedule", "datadesk.core.tables.bib_cross",
                     "datadesk.core.tables.supp_activity", "datadesk.core.tables.supp_revenues",
                     "datadesk.core.tables.supp_by_source", "datadesk.core.tables.supp_summaries",
                     "datadesk.core.tables.supp_capital"]
```

The QSMR table modules join the independence list and the forbidden list of the helper contract
in build step 14, and `qsmr_common` joins the helper contract's sources. Ruff's
`flake8-tidy-imports.banned-api` bans `datetime.datetime.now`, `datetime.date.today` and
`tomllib.load` (only `tomllib.loads` on text) under `checkedtables/` and `datadesk/core/`. The
purity test of section 11.1 catches builtins that neither tool can ban. import-linter skips a
folder with no `__init__.py`, and `test_source_folders_are_packages` fails such a folder under
the three `packages/*/src` trees.

import-linter 2.16 treats a listed standard-library module as an external package and fails the
contract. Build step 1 planted `import os`, `from pathlib import Path`, `import logging`,
`import time` and `import random` in `datadesk.core`, one at a time, and each broke
`datadesk core is pure`. Design C left `os`, `pathlib`, `time` and `random` out of its lists (R2).

## 13. Quirk coverage

`/home/claude/scratch/v2/final/coverage.tsv` has one row for each of the 437 inherent quirks. New
in this version, it also has one row for each of the 87 unsure quirks, as R2 asked.
It starts from design C's file. Every renamed mechanism and every quirk whose handling changed
was updated. Of the 437 inherent rows, 85 changed, 50 of them to a new mechanism, and three
mechanism names changed module. Mechanisms over the inherent
quirks, with the number each carries:

| Mechanism | Quirks | By dossier |
|---|---:|---|
| `DATA:RowSchema` | 42 | BIB 3, BSALES 4, ENT 10, MCITY 5, MSCH 1, QCASH 7, QOBL 2, QPOS 3, RTT 4, WAGE 3 |
| `DATA:Acknowledgment` | 33 | BIB 4, BSALES 2, MCITY 7, QCASH 1, QOBL 1, QPOS 3, RTT 3, SUPCAP 1, SUPOP 5, VAL 2, WAGE 4 |
| `datadesk.core.listings.parse_listing` | 24 | BIB 4, BSALES 3, MCITY 1, MSCH 1, QCASH 2, QOBL 1, QPOS 1, RTT 3, WAGE 8 |
| `DATA:Registry` | 23 | BIB 3, ENT 10, QOBL 6, QPOS 2, SUPOP 2 |
| `checkedtables.grammar.read_grammar` | 17 | BIB 4, ENT 4, SUPCAP 4, SUPOP 5 |
| `checkedtables.rows.match_rows` | 17 | BSALES 1, ENT 6, MCITY 1, MSCH 4, QCASH 1, QPOS 2, RTT 1, WAGE 1 |
| `checkedtables.checks.dsl.CheckSet` | 16 | BSALES 2, MCITY 3, QCASH 3, QOBL 2, QPOS 1, RTT 1, SUPCAP 1, SUPOP 1, VAL 2 |
| `checkedtables.lex.lex_cell` | 14 | BIB 1, BSALES 1, MCITY 1, MSCH 1, QCASH 2, QPOS 1, RTT 1, SUPCAP 2, SUPOP 1, VAL 3 |
| `checkedtables.columns.bind_columns` | 13 | BIB 1, MCITY 3, MSCH 3, QCASH 3, QOBL 2, SUPOP 1 |
| `datadesk.core.tables.supp_common.split_statements` | 13 | SUPCAP 5, SUPOP 8 |
| `checkedtables.columns.choose_era` | 10 | BIB 1, BSALES 1, MCITY 1, MSCH 2, QCASH 2, QOBL 1, SUPCAP 1, WAGE 1 |
| `datadesk.core.watch.plan_watch` | 10 | MCITY 3, MSCH 1, QCASH 1, QPOS 1, RTT 2, WAGE 2 |
| `DATA:Era` | 9 | BIB 2, QCASH 1, QOBL 1, QPOS 1, RTT 2, SUPCAP 1, VAL 1 |
| `checkedtables.checks.dsl.Tolerance` | 9 | BSALES 1, MCITY 1, QCASH 2, QOBL 1, QPOS 1, RTT 2, VAL 1 |
| `checkedtables.text.parse_label` | 9 | BIB 2, BSALES 1, ENT 1, QOBL 2, QPOS 1, RTT 1, WAGE 1 |
| `checkedtables.pages.slice_body` | 8 | BIB 1, BSALES 1, QOBL 1, SUPCAP 1, SUPOP 2, VAL 1, WAGE 1 |
| `datadesk.core.fetch.confirm_period` | 8 | MCITY 4, MSCH 2, QCASH 1, WAGE 1 |
| `DATA:MeasureSpec` | 7 | BIB 1, MSCH 1, QCASH 1, QOBL 1, QPOS 1, SUPOP 1, VAL 1 |
| `DATA:WordSourcePlan` | 7 | BIB 1, MSCH 1, QCASH 1, SUPCAP 1, VAL 3 |
| `checkedtables.table.Additivity` | 7 | BSALES 1, ENT 1, QCASH 1, QPOS 1, RTT 1, WAGE 2 |
| `datadesk.core.vintage.select_canonical` | 7 | BSALES 2, QCASH 1, QOBL 1, RTT 1, WAGE 2 |
| `checkedtables.checks.engine.run_checks` | 6 | BIB 1, MCITY 1, MSCH 1, QOBL 1, SUPOP 1, VAL 1 |
| `datadesk.core.tables.qcmr_personal_services.parse` | 6 | ENT 2, QOBL 3, VAL 1 |
| `datadesk.core.tables.wage_industry.period_kind` | 6 | WAGE 6 |
| `DATA:EditionNote` | 5 | MCITY 1, QCASH 1, RTT 1, VAL 1, WAGE 1 |
| `DATA:SourceCatalog` | 5 | RTT 1, SUPCAP 2, SUPOP 1, WAGE 1 |
| `checkedtables.pages.find_runs` | 5 | BIB 2, QCASH 2, QOBL 1 |
| `datadesk.core.periods.fiscal_period` | 5 | QOBL 1, QPOS 1, RTT 1, WAGE 2 |
| `datadesk.core.registry.resolve_fund` | 5 | BIB 2, ENT 3 |
| `checkedtables.lex.split_numeric_runs` | 4 | BSALES 1, VAL 3 |
| `datadesk.core.tables.bib_cross.cross_checks` | 4 | BIB 4 |
| `datadesk.core.tables.bib_fund_summary.parse` | 4 | BIB 4 |
| `datadesk.core.tables.birt.parse` | 4 | BSALES 4 |
| `datadesk.core.tables.collections_common.attach_stacked_labels` | 4 | ENT 1, MCITY 1, MSCH 1, VAL 1 |
| `datadesk.core.tables.qcmr_cash.split_grids` | 4 | QCASH 2, VAL 2 |
| `datadesk.core.tables.supp_capital.parse` | 4 | SUPCAP 4 |
| `DATA:DashRule` | 3 | MCITY 1, MSCH 1, VAL 1 |
| `DATA:ReviewedReading` | 3 | MSCH 1, QCASH 2 |
| `checkedtables.text.normalize_label` | 3 | BSALES 2, SUPOP 1 |
| `datadesk.core.tables.bib_revenue_schedule.parse` | 3 | BIB 3 |
| `datadesk.core.tables.rtt.split_zones` | 3 | ENT 1, RTT 2 |
| `datadesk.core.tables.sales.parse` | 3 | BSALES 3 |
| `checkedtables.checks.acks.match_acknowledgments` | 2 | QCASH 1, VAL 1 |
| `checkedtables.records.apply_reading` | 2 | VAL 2 |
| `checkedtables.text.split_line_prefix` | 2 | ENT 1, QPOS 1 |
| `datadesk.core.fetch.plan_fetch` | 2 | MCITY 1, QOBL 1 |
| `datadesk.core.tables.bib_revenue_schedule.grammar_for` | 2 | BIB 1, ENT 1 |
| `datadesk.core.tables.collections_city.parse` | 2 | MCITY 2 |
| `datadesk.core.tables.qcmr_obligations.parse` | 2 | QOBL 2 |
| `datadesk.core.tables.qcmr_personal_services.citywide_end` | 2 | QOBL 2 |
| `datadesk.core.tables.rtt.parse` | 2 | RTT 2 |
| `datadesk.core.tables.wage_residency.parse` | 2 | WAGE 2 |
| `NOT_HANDLED` | 1 | SUPOP 1 |
| `checkedtables.checks.coverage.check_coverage` | 1 | SUPOP 1 |
| `checkedtables.checks.dsl.FirstPresent` | 1 | MSCH 1 |
| `checkedtables.columns.lanes_from_rules` | 1 | VAL 1 |
| `checkedtables.lines.group_lines` | 1 | QCASH 1 |
| `checkedtables.rows.Truncation` | 1 | MCITY 1 |
| `checkedtables.rows.join_rows` | 1 | BIB 1 |
| `checkedtables.words.WordSource` | 1 | VAL 1 |
| `datadesk.core.checks.series.cross_edition_checks` | 1 | WAGE 1 |
| `datadesk.core.measures.measure_for` | 1 | QCASH 1 |
| `datadesk.core.registry.resolve` | 1 | QOBL 1 |
| `datadesk.core.release.rows.to_release_rows` | 1 | BSALES 1 |
| `datadesk.core.rowschemas.schema_for` | 1 | MSCH 1 |
| `datadesk.core.tables.collections_city.checks_for` | 1 | MCITY 1 |
| `datadesk.core.tables.collections_common.dedupe_overprint` | 1 | MCITY 1 |
| `datadesk.core.tables.collections_school.parse` | 1 | MSCH 1 |
| `datadesk.core.tables.qcmr_cash.find_balance_page` | 1 | QCASH 1 |
| `datadesk.core.measures.scope_for` | 1 | QCASH 1 |
| `datadesk.core.tables.qcmr_personal_services.drop_footnotes` | 1 | QOBL 1 |
| `datadesk.core.tables.qcmr_positions.parse` | 1 | QPOS 1 |
| `datadesk.core.tables.supp_activity.parse` | 1 | SUPOP 1 |
| `datadesk.core.tables.supp_common.lift_subtotal_labels` | 1 | SUPOP 1 |
| `datadesk.core.tables.supp_revenues.GRAMMAR_WATER_FY2010` | 1 | SUPOP 1 |
| `datadesk.core.tables.wage_industry.parse` | 1 | WAGE 1 |
| `datadesk.core.words_audit.compare_sources` | 1 | QCASH 1 |

`DATA:` record kinds:

| Kind | What it is |
|---|---|
| `RowSchema` | a `[[row]]` entry in `datadesk/data/rows/<table>.toml`: key, kind, period, labels for table lines, `forms` for entity rows, `follows`, `absent_editions` |
| `Registry` | an entry in `datadesk/data/registry/`: entity, dated name, code, parent, alias, relation |
| `Acknowledgment`, `WordSourcePlan`, `ReviewedReading`, `DashRule`, `EditionNote` | the record types of sections 2.1 and 2.2 |
| `Era` | an `Era` value in a table module |
| `MeasureSpec` | a `MeasureSpec` or `RowMeasure` value in a table module (design C filed these under `Era`, R1) |
| `SourceCatalog` | an entry in `datadesk/data/catalog.toml`: listing URL pattern or manual URLs, slug exceptions, expected editions, lag |

Why the large ones are not catch-alls:

- `DATA:RowSchema` (42) is data, not code. Each quirk is one or two lines in one table's file. It
  is a label for a table line, a period bound, an edition-bound spelling or a form template. The file
  has one shape and no options, and the lint rejects overlaps. Department spellings moved out of
  it into the registry (change 11), which is why it fell from 46.
- `DATA:Acknowledgment` (33) is one record per printed source fault, with an exact key and
  residual. A record cannot cover a second failure, and an unused one blocks.
- `parse_listing` (24) dispatches on a closed enum to one small parser per listing shape. The
  per-series title rules live in `listings/titles.py`, one function per series. The count is
  high because publishers are sloppy about titles and filenames. No single function decides much.
- `DATA:Registry` (23) holds dated names, codes, parents and three relation kinds. It has no
  matching rules; matching is `resolve`, exact on norm then squash.
- `read_grammar` (17) and `match_rows` (17) are the two row readers. Each quirk they carry is a
  rule, slot or block in one table's own grammar or schema. The functions hold no
  family-specific branch, and their parameters and fields are pinned by the shape test.

`NOT_HANDLED`:

| Id | Reason |
|---|---|
| SUPOP-Q46 | The comparison of FY2020 supplemental cells with the FY2021 budget book belongs to budget detail, which stays in gov-budget-data. The supplemental values publish as printed. |

How the 87 `unsure` quirks are treated. Each now has a row in the coverage file. The design fails
closed on each, so the first corpus run settles it instead of a guess:

- A column, caption or era question (QPOS-Q02, QOBL-Q29, SUPOP-Q15, MSCH-Q12, RTT-Q21) becomes a
  binding or era finding if the guess is wrong.
- A label question (QPOS-Q10, MSCH-Q19 to Q21, ENT-Q09, ENT-Q10, ENT-Q64, QOBL-Q47) becomes an
  `unknown_row`, `duplicate_row` or truncation finding.
- A source question (QCASH-Q18, QOBL-Q18, WAGE-Q15) becomes a stray-word, unreadable-cell or
  period finding.
- A publisher-or-OCR question on arithmetic (QPOS-Q19, Q20, SUPCAP-Q21, Q22) becomes a blocking
  failure. Someone must look at the page before writing an acknowledgment or a reading.
- A completeness question (SUPCAP-Q02, QOBL-Q10, BIB-Q07, BIB-Q08) becomes a `Gap` in the watch
  pull request. Decisions 1 and 4 settled where the documents come from (section 16).
- Design C's `datadesk probe` command is dropped (R3). The first corpus run answers these
  questions through findings, and a question it cannot answer is listed in section 17.

Why each dossier's `artifact` quirks do not arise here:

| Dossier | Reason |
|---|---|
| BIB | No first-match profiles or dummy markers. Titles find pages. Acks key on a semantic `FailureKey`. Cross-table checks are declared relations over table keys, with no exclusion list and no 1,747-line engine. |
| BSALES | Identity is the sha; the coverage path is never used. Canonical years come from one policy function. Years come from the Period line once. Row roles come from the schema, with no indentation trial. TOML cannot split an alias at a comma. |
| ENT | Aliases are table-scoped and edition-scoped. Spellings have one home. Resolution happens during parsing with a duplicate-key check. The release diff keys rows semantically and flags entity and key changes. |
| MCITY | Dash and N/A are cell types. Each record is matched one to one and must be used. Eras are chosen by captions; no glob picks a profile. The manifest says "period" where the old one said "fiscal_year". |
| MSCH | Checks are declared per era in code and must evaluate, so no profile shadows another. Every value is `Decimal`. Acks cover failures, never cells. |
| QCASH | No table-finder priors, no fixed lookback and no stitching. Page 2 is its own table, found by its rows. One word source is declared per page and compared where a record asks. Columns bind by caption. |
| QOBL | No cut PDFs. One declared source per page. Headers are always verified and columns have names. Every check is declared and must evaluate, so none can be dropped on a retry. |
| QPOS | One parser per table, with records kept apart from layout. No hypothesis search and no value repair. Count columns lex strictly. |
| RTT | The index keys by sha, with versions. Zones split by headings, with no consensus region or budget-detail clip. Each zone is one long table with the window as data. |
| SUPCAP | The period is read from the page. Column eras are declared. The reporting-year exclusion is an `Except` selector declared in the check. |
| SUPOP | Lanes bind by caption and rules, so no positional shift. No region bridging. Acks are semantic. |
| VAL | No backend ranking, letter maps or arithmetic digit picks. One lexer, which never inserts a decimal point. Dash meaning is declared. Every published row carries its evidence and proof kind. |
| WAGE | `watch` owns the URL reuse guard for every command. Subsets are typed by period kind. Per-edition notes replace copied profiles. Years are read from headers. |

## 14. What moves from the old code

Paths drop `packages/gov-budget-etl/src/gov_budget_etl/`.

| Old file | Fate | Goes to |
|---|---|---|
| `qcmr.py` (435) | Rewrite smaller: header band, page runs, period phrase, quarter mapping; drop splitting | `checkedtables.pages`, `datadesk.core.periods`, `listings/titles.py` |
| `phila_media.py` (932) | Rewrite smaller: titled-link parser, media regex, `MONTHS` | `listings/phila_documents.py`, `periods.py` |
| `phila_source_sync.py` (231) | Knowledge only: host aliasing, FY2022 floor, `allow_unpublished` | `watch.py`, `catalog.toml` |
| `revenue_collections.py` (888) | Moves with changes: listing regex, `_month_year`, one-edit months, alias rule, validate before add | `listings`, `fetch.confirm_period`, `watch` |
| `wage_tax_industry.py` (304), `wage_tax_residency.py` (111) | Moves with changes: title period parse, reuse detection, Wayback recovery, year-range parse | `listings/titles.py`, `watch.pick_capture` |
| `birt_sector.py` (165), `sales_tax_sector.py` (214), `realty_transfer_tax.py` (135) | Moves with changes: coverage and upload stamp, page-year check, title-first period; drop path storage and page cutting | `listings`, `fetch`, table modules |
| `budget_in_brief.py` (195), `publication_stage.py` (29) | Moves with changes: stage from title, FY token rule | `listings/titles.py`, `domain.Stage` |
| `funds.py` (319) | Rewrite smaller: `normalize_printed_code`, code intervals, scope before name | `registry/resolve.py` |
| `entities.py` (1,494) | Rewrite smaller: `normalize_entity_label` (78-98), suffix split, succession shape, code interval checks | `checkedtables.text`, `registry` |
| `resolution.py` (2,267) | Knowledge only: qualifier cases become declared parents; org context rules become grammar slots | row schemas and grammars |
| `tables/amounts.py` (278) | Rewrite smaller: strict grouping, paired parentheses, split sequences; fix the bare-integer join | `checkedtables.lex` |
| `tables/checks.py` (1,357) | Rewrite smaller: the rounding bound at 80-100 | `checkedtables.checks.dsl.PerOperand` |
| `semantic_accounting.py` (631) | Rewrite smaller: exact row identity, half-increment ratio | `checks.engine`, `Ratio` |
| `series_checks.py` (203) | Moves with changes: three cross-edition checks | `checks/series.py` |
| `page_table_scoping.py:1170-1218` | Rewrite smaller: zone rebuild from amount lines | `rtt.split_zones`, `lanes_from_values` |
| `tables/rule_grid.py` (1,366) | Rewrite smaller: lanes from vertical rules only | `lanes_from_rules` |
| `tables/line_repair.py`, `row_detection.py:152-334` | Rewrite smaller: overprint dedupe with welded copies, stacked labels scoped to the 2014 window | `collections_common` |
| `tables/text_cleaning.py` (274) | Rewrite smaller: currency, fused suffix | `lex.split_numeric_runs` |
| `parsers/pdfplumber_backend.py` (476), `parsers/textract_backend.py` (495) | Moves with changes: extraction and response mapping only | shell adapter, `core/ocr.py` |
| `gov_budget_data/lineage.py` (86) | Moves as is: `predecessor_spans`, split refusal | `phillyledger.lineage` |
| Reconciler, recovery, stitching, region detection, staleness, backend ranking (`reconcile.py`, `value_recovery.py`, `numeric_value_recovery.py`, `reconciliation_*.py`, `stitching.py`, `region_detection.py`, `fused_columns.py`, `totals.py`, `staleness.py`, `artifact_selection.py`, `reconciliation_status.py`, `resolved_assertions.py`) | Knowledge only | nothing |
| `config/entities.yml` (4,730) | Data, split: department, fund, class and tax spellings to `registry/`; table lines to `rows/*.toml`; OCR aliases with editions | data |
| `config/layouts/*.yml` acks, `config/resolved_assertions.yml` | Data, re-keyed by `propose_rekey` | `data/acks/` |
| `config/semantics.yml` | Knowledge: column lists per era become `ERAS` constants; the 34 decimal repairs become readings | table modules, `data/records/` |
| `config/page_types.yml` | Knowledge: titles and banner regexes | table modules |
| Tests: listing, period, alias, Wayback, stage tests | Moves with changes | `tests/core/` |
| Tests: continuity and acknowledgment tests | Knowledge: expected residual sets become ack records and fixture assertions | `tests/tables/` |

## 15. Build order

This order has no deadline. A step is finished when its check passes, and nothing is published
before step 6. The last gov-budget-data release, pinned by its manifest sha, is the baseline: the
new parser's output is compared with it cell by cell, and every difference is resolved on the page
before the first release (Codex review).

The first release-quality table from the new code is QCMR positions for FY2022 Q1 to FY2026 Q4, at
step 6. Those 20 editions are whole publisher PDFs with a text layer, so they need no declared
pages and no OCR. Ten of them, FY2023 Q1 to FY2025 Q2, extract their grid fonts as `(cid:N)`
codes, and six open with a commentary page that also prints the `TABLE P-1` band.

1. **Workspace.** Three packages, uv, `uv_build`, ruff, ty, import-linter, prek, pytest-socket,
   the purity test and the library shape test on empty modules.
   *Check:* CI is green. A planted `import boto3` in `datadesk.core`, a planted `bool` parameter
   in `checkedtables`, and a planted socket call in a core test each fail CI.
2. **Kit, words to cells.** `refs`, `kinds`, `words`, `labels`, `text`, `lines`, `cells`, `lex`,
   `records`, `testing.page_from_text`, the `NumberFormat` and `ColumnSpec` types of `columns`,
   and the `RowKey`, `Severity` and `Finding` types of `table`, with unit and property tests.
   *Check:* Hypothesis suites pass. The 55 probe inputs of VAL section 3.2 give the documented new
   results (decision 12). `transliteration_ok` refuses "65.8" to "85.8" and "77,500,000" to
   "7,500,000".
3. **Archive for the QCMR from FY2022.** Index format, `confirm_period`, `plan_fetch`, the S3
   adapter, the QCMR catalog entry, and a one-time import of held FY2022 to FY2026 reports by sha.
   *Check:* each of the 20 reports is indexed once, by the sha in an inventory checked by hand.
   Fetching the same listing again adds nothing.
4. **Words.** PDF adapter with the font repair ported from `text_cleaning.repair_cid_words`
   (old repo, line 138), word cache, `codec`. A word still holding `(cid:` after repair lexes as
   `Unreadable`.
   *Check:* word fixtures regenerate byte-identical. A cache hit returns an equal `Document`. On
   all 20 grid pages with font codes, no `(cid:` remains, and a rendered crop of each page's
   first and last department rows matches the repaired digits.
5. **QCMR positions parser.** Kit `pages`, `columns`, `pipeline`, `table`, `rows`, `assemble`; the
   department part of the registry; `rowschemas`; `vocab`, `measures` and the catalog test;
   `qcmr_positions`.
   The run starts at the first page whose header carries the era's captions; a page with the
   `TABLE P-1` band and no grid captions is commentary, reported and not parsed.
   *Check:* the 20 editions parse with no BLOCK finding. The no-ink-lost property holds on their
   fixtures. Each department label resolves through the registry, and the schema carries none.
   The ten positions columns have ten different descriptions, and the catalog test fails when
   two are made equal. Paired fixtures on both sides of each entity seam in the range resolve to
   different entities: "Streets" in FY2025 Q4 is Streets with Sanitation, and in FY2026 Q1 it is
   Streets.
6. **Checks, gate and release for positions.** Engine, coverage, acks, gate, report; release
   rows, proof, provenance, encoders, diff, `plan_release` and its executor, with conditional
   writes and a two-writer test; the manifest schema. The reader is built at step 13 (section
   18.4).
   *Check:* every positions check evaluates in every edition. The gate passes for FY2022 to
   FY2026. The canary passes. Two runs give identical bytes. A hand-edited cell value is caught by
   `verify_cell_provenance`. Every release row carries its column's description, and the manifest
   carries the vocabulary with a definition per member; a release file with a value
   outside it fails validation. The Q4 FY2024 quarter-end count and the FY2025 "Year-End Actual" are one subject.
   Every cell matches the pinned gov-budget-data release by edition, row key and column, or the
   difference is resolved on the page. Labeled fixtures for each layout tie a number to its row label and
   fund caption. This step ships the files, the manifest and a checksum command. Both the CSV and
   the Parquet file are read back, and their typed contents equal the approved rows.
   **First release-quality dataset.**
7. **Older QCMR positions.** The owner's whole reports from FY2008 to FY2021 indexed by sha;
   `TablePages` records for reports whose P-1 pages code cannot find, scans first;
   `WordSourcePlan` records for scans; `datadesk ocr --spend` for declared pages with no archived
   response; the seven records migrated.
   *Check:* 75 editions parse and 74 release. The 12 known residual cells reproduce. FY2008 Q2 is
   withheld with its 11 open failures until the owner reviews it (decision 5), and every other
   edition still releases (per-edition gate). Every `TablePages` record is used. Each entity seam
   from FY2008 to FY2021 has paired fixtures, as at step 5.
8. **The rest of the QCMR.** Cash (page 1 grids and page 2), O-2 in both layouts (nine columns,
   and the six-column year-end form FY2026 Q4 prints), O-3; `compare_sources` wiring
   in `plan_parse` and `run_parse_job`; `suggest`, first used on the cash identities. From this step on, each table's provisional column
   descriptions are settled by reading one page before the table releases (section 17.3).
   *Check:* cash eras are chosen by captions in every edition. FY07 Q4 reports exactly three
   source disagreements, and three readings clear them. Page 2 is found by its rows in editions
   with a damaged caption. O-3 citywide sums are exact; `parent_is_sub_blocks` runs at WARN.
   O-2's nine columns have nine descriptions. A cash month is actual in the edition whose cutoff
   covers it and a projection in the editions before.
9. **Monthly City and School.**
   *Check:* 143 City and 142 School editions parse. The 74 numeric records are re-keyed and all
   used. August 2026 needs one `DashRule`. Stacked labels join only inside the 2014 window; a test
   page from 2016 with the same shape gives an orphan finding.
10. **The five tax families.** Wage by industry, wage by resident status, BIRT, sales, RTT.
    *Check:* BIRT canonical years equal the old split. Sales FY2019 comes from FY2020's prior
    column. RTT property totals equal location totals.
11. **Budget in Brief.** Obligation history, fund summary, revenue schedules with both grammars,
    and `bib_cross`.
    *Check:* the 26 cross-table cells are acknowledged. FY2011 to FY2015 schedules parse with the
    scan grammar. The text grammar on a scan fixture yields `style_unavailable`.
12. **Supplemental reports.** A catalog entry and title rule on the Finance document-finder feed
    the QCMR already uses; FY2003 to FY2006 indexed by hand from held copies and the City's old
    `/reports/pdfs/` address. Then six operating tables and three capital tables. Acceptance is
    per statement, not per family: each of the nine tables passes on its own, and the first
    difficult edition of the operating statement (about 430 rows) is finished, with review,
    before the others start (Codex review).
    *Check:* the 32 records are re-keyed or replaced (FY23 p93 by the declared reporting-year
    `Except`). Every grand total has the category totals as children. FY2010 Water passes
    `sections_add_up` or shows which side its bold line sits on.
13. **`watch`, the reader and the first full release.** `watch` with Wayback and gaps, the pull
    request executor, `suggest --promote` and registry lint in CI. The reader (`plan_load`,
    `load`, `pin`, `lineage`, HTTP and cache), with its return type settled first. Then a
    release, diffed against the last gov-budget-data release by (dataset, edition, row label,
    column).
    *Check:* a recorded listing with a reused URL yields one `url_reused` item and one Wayback
    lookup. The canary starts from `watch`. The reader opens a release by manifest sha, verifies
    each file's hash on every open, and rejects a value the manifest does not define. Every
    difference from the old release is explained in the release notes.
14. **QSMR, the held-out test.** Catalog entries with manual URLs, the QSMR period reader, School
    District funds in the registry, `qsmr_common`, CF-3 and the other tables, `qsmr_cross`.
    *Check:* `git diff <step-13 tag> -- packages/checkedtables` is empty, and the shape snapshot is
    unchanged. Any kit change found here is reported as a failed test of the design, then decided
    in review. The same holds for the vocabulary: the kind, version, window, derivation and
    dimension lists are unchanged, and a new `Quantity` member is reported.

## 16. Decisions

The owner answered these on November 22, 2026. Decision 6 followed the Codex review the same day. Two setup questions were settled the same day: the repository and its folder are
named `phillyledger`, and both buckets use Cloudflare R2. Decision 12 came on November 23, 2026.
Decisions 13 to 17 came the same day, after the step 2 build run. The run put five
recommendations to the owner in chat, each a few sentences long, and he adopted them with the
words "follow your recommendations". The rows below give each recommendation as he saw it.
The run then checked them against real pages and the old repository's readings. That work
went further than the recommendations, and in one place against one. Section 16.3 lists,
decision by decision, what was worked out after he answered. The run told him in chat that
the reading rule of section 16.2 goes beyond his recommendation and reverses it on confusable
letters, and he confirmed that rule the same day with the words "I approve the detailed
ruled". The other entries of section 16.3 are proposals. The owner confirms or changes them
before the step 5 plan builds on them. Until step 5 the code keeps the rule that section 3.1
states, and section 3.1 points at the decision from each function it touches.

| # | Question | Answer |
|---|---|---|
| 1 | Excerpts and the "no cut PDFs" rule | Whole documents only. The owner holds most or all full QCMR reports from before FY2022. Page-finding code must work on the FY2022-on reports; older reports, scans above all, get a `TablePages` record naming each table's pages (section 2.2). An edition with no full document is listed as a `Gap` and decided then; `Holding.EXCERPT` stays for that case only. The same rule applies to the Budget in Brief books held as excerpts. |
| 2 | Does cross-edition agreement ever block? | No. Always WARN. |
| 3 | When does `checkedtables` go to PyPI? | After build step 14 passes with no kit change. |
| 4 | Supplemental report acquisition | From the City's site, through the Finance document-finder feed the QCMR already reads. Years the City no longer posts are indexed by hand from held copies or the old `/reports/pdfs/` address. No Wayback search for this family. What the City posts is below. |
| 5 | QCMR positions FY2008 Q2 | Withheld for now, fixed later. The release notes list it. |
| 6 | QSMR repeated labels | The printed vendor number when the edition prints one, unique within the edition. Otherwise an occurrence number within the edition. No vendor identity across editions, and no acknowledgment may target an occurrence key. Decided on November 22 after both Codex runs recommended it. |
| 7 | What happens to a withheld edition | Keep the previous release's rows. An edition never released, such as FY2008 Q2, is simply absent. |
| 8 | OCR confidence floor | One floor of 95 for every series. |
| 9 | A wrapped supplemental source label | WARN on each join. |
| 10 | Keep `verify_cell_provenance` | Keep. |
| 11 | Six captions where the kind of number is a judgment | As filed in section 2.2. The owner confirmed that Budget in Brief "Current Estimate" and collections "Current Estimates" are projections. |
| 12 | Which 55 inputs does the probe clause of step 2 mean? | The 55 of VAL section 3.2.1. The original inputs are in no file. The owner decided on November 23, 2026, with the words "[u]se your list, but make row 4 unreadable." |
| 13 | What may a reviewed reading change? | Tighten the rule, and fix its exact form before step 5, after a run on the old repository's reviewed readings. Every word of the cell must look like a number, or the cell takes only a null reading. A reading may add a decimal point or a sign that extraction lost, and may not move or drop one the cell prints. The pinned confusable list stays as it is. Section 16.2 holds the exact form the run proposes, and section 16.3 sets it beside this row. `transliteration_ok` keeps its signature. Built at step 5, with `load_records`. |
| 14 | A raised footnote mark that falls outside its row | `group_lines` lets a small word join a line when its bottom edge falls inside that line's vertical span, with the 0.7 ratio of the lexer's raised-digit rule. Built at step 5 and proven on a word fixture of the page that holds "Human Services (1)", where the raised `(1)` opens a line of its own today. That is page 2 of the held FY2026 Q4 positions excerpt. The old repository's splitter audit puts positions on pages 32 to 34 of the publisher's 92-page report, which makes it page 33 of the publisher's file. Section 16.3 holds two details the run proposes. |
| 15 | Which printed forms are a value with no number? | `N/A` and `NA` in any case are not applicable (`n/a` on page 19 of the FY2009 Budget in Brief). A cell that holds only U+2010 is a dash (page 17 of the FY2021 supplemental report). `#DIV/0!` is a value word and lexes as `NotApplicable` with its text kept (page 1 of the July 2020 School report). VAL section 3.2.1 pins `N/A` in upper case at row 28 and holds no row with `n/a`, U+2010 or `#DIV/0!`, so no acceptance row changes. Built at step 5. The recommendation said U+2010 is not a minus sign until a page prints it as one. A page does, and section 16.3 holds the change the run proposes. |
| 16 | When may a leading digit join a grouped number? | Only when the two words have the same size and the gap between them is under a limit. Step 5 sizes the limit on word fixtures. It must keep every row of VAL section 3.2.1 as documented, and it must leave `6` and `30,223` as two cells, which page 1 of the held FY2006 obligation-history excerpt prints 51.55 points apart. |
| 17 | Is a bare digit at the end of a label a footnote mark? | Off by default. It is a mark only when it is small and raised, or when the table's row schema says its pages use digit footnotes ("Sheriff 2", ENT-Q07). Otherwise it stays in the label, so the project label that ends in "PHASE 2" on page 107 of the FY2023 supplemental report keeps its 2. The recommendation asked for this to be settled before step 12. Section 16.3 proposes building it at step 5, with the row schemas. |

### 16.1 Supplemental reports the City posts

Found on November 22, 2026 by searching phila.gov. The Finance document-finder feed itself was
not read, so a year missing from this table may still be in the feed.

| Fiscal years | Where the City posts it | Held before |
|---|---|---|
| FY2010 to FY2019 | `phila.gov/media/`, uploaded October 19, 2020 (FY2011 found by the Codex review) | FY2010, FY2015 |
| FY2020 to FY2022 | `phila.gov/media/`, uploaded March 2023 | all three |
| FY2023 | not seen in the search | held |
| FY2024 | `phila.gov/media/`, uploaded February 2025 | held |
| FY2025 | `phila.gov/media/`, uploaded August 28, 2026 | no |
| FY2002, FY2006 | the City's old `/reports/pdfs/` address | no |
| FY2003 to FY2005 | held copies; FY2004 also at the old address through a web archive | all three |
| FY2007 to FY2009 | not found | no |

So 9 of the 12 missing years are on the City's site (FY2011 to FY2014 and FY2016 to FY2019 on the
current site, FY2006 at the old address), and FY2025 is new. FY2002 is also available, one year
before the series was thought to start. FY2007 to FY2009 were not found.

### 16.2 The reading rule (decision 13)

The owner adopted decision 13 as its row above states it. The exact rule below was worked out
after he answered, through three verifications and three Codex reviews, and section 16.3 says
where it goes beyond or against what he saw. He was told of that in chat and confirmed the
rule on November 23, 2026, with the words "I approve the detailed ruled". He was not shown
this section clause by clause. The list at its end, of what the step 5 plan carries, is not
part of what he confirmed, and one question on it is his to answer.

`transliteration_ok(seen, reading)` is true when `reading` reads as one signed number through the
private reader of `lex_cell`, and clauses 1 to 5 hold. `seen` is the cell's text less its mark
words, which `apply_reading` removes today for an `Amount`. Its words are the pieces between
single spaces. A digit glyph is an ASCII digit or a pinned confusable glyph, which reads as its
digit. The minus glyphs are the four of section 3.1 and U+2010, as section 16.3 proposes for
decision 15.

1. Digits. The digits of `reading`, in order, equal the digit glyphs of `seen`. This is the rule
   of section 3.1, unchanged, with its refusal of a font code and of a decimal digit that is
   not ASCII.
2. Word shape. A number word is, in this order: a lead of at most one `(`, at most one `$` and at
   most one minus glyph, in any order; a body made of digit glyphs and the glyphs `.`, `,` and
   `:`, whose first digit glyph is an ASCII digit; an optional `%`; an optional `)`; and any
   number of mark glyphs. A word whose lead holds a `(` may hold a `j` in the place of the `)`
   (VAL-Q36, `(59.8j`). Every word of `seen` is a number word, with two exceptions: the first
   word may be `$` alone, and any word after the last number word may be `%` alone or made of
   mark glyphs. An empty word, which two spaces in a row would make, is neither.
3. One number. `seen` holds one number word or two. Two stand for one number whose decimal point
   was lost at the break between them (`(29 1)`, `67: 3`, VAL-Q35). The first then ends with its
   body. The second has no lead, and its body holds digit glyphs only. An optional `%`, an
   optional `)` and mark glyphs may follow that body.
4. The point. `seen` prints a point in three places: at each `.` of a body; at each `,` or `:`
   that stands between two digit glyphs of one body and is not a grouping comma; and at the
   break between two number words. A grouping comma is a `,` followed by exactly three digit
   glyphs and then by a glyph that is not one, or by the end of the body. So `69,2` prints a
   point, `1,234` prints none, and `1,370,4` prints one, at its second comma. Where `seen` prints
   one point, as many digits come before the point of `reading` as digit glyphs come before the
   point in `seen`, and a reading with no point counts as having it after its last digit. Where
   `seen` prints two or more, no reading passes. Where it prints none, a reading may place a
   point anywhere.
5. The sign. `seen` prints a sign when a number word holds a minus glyph, a `(`, a `)` or the
   `j` that stands for one. Then `reading` reads as a negative number, a negative zero included.
   Where `seen` prints no sign, a reading may add one.

Three more tests need what the two texts do not hold, so `apply_reading` and `reading_for` make
them and the function does not.

6. The source. On a text layer that the publisher's software wrote, `seen` holds no confusable
   glyph. Such a layer prints its own letters, so `15030B`, a project number on page 92 of the
   FY2015 supplemental report, is not 150308. A text layer that a scanner's OCR wrote counts as
   an OCR page here. The held FY2007 Q4 cash report is one: ScanSnap and Acrobat Paper Capture
   made it, and its text layer holds `20.B` and `25.B`. `apply_reading` knows the reading's
   source, and `SourceKind` does not yet tell the two kinds of text layer apart.
7. The gap. The two number words of clause 3 have the same size and stand closer than the gap
   limit, both as decision 16 sets them. `reading_for` sees the word boxes. On page 1 of
   the held FY2006 excerpt, `30,217` and `6` are two columns, and without this test they read
   as 30217.6. Where one extraction word holds both number words, there is no gap to measure and
   the clause holds: Textract returned `(29 1)`, `(3 2)` and `266 1` of the FY2007 Q3 cash
   report as one word each.
8. A confirmation. `apply_reading` accepts, without the function, a reading that reads as the
   very number an `Amount` cell already prints, with an equal `as_tuple()`, so that a printed
   sign on a zero stays. It confirms what the lexer read, as a source disagreement asks
   (section 9). The lexer's two join shapes would fail clauses 3 and 4 (`1 37,332,523` and
   `67,215,504.0 0`, rows 36 and 37 of VAL section 3.2.1).

A null reading needs none of these. It accepts the cell as unreadable.

The table is for an OCR page, and for clauses 1 to 5 alone unless the row names another.

| `seen` | `reading` | Section 3.1 today | This rule | Clause that fails |
|---|---|---|---|---|
| `408,491,218 NET PROFITS TAX` | `4084912180` | passes | fails | 2 |
| `TOTAL TAX REVENUE *` | `0` | passes | fails | 2 |
| `#DIV/0!` | `0.0%` | passes | fails | 2 |
| `29l8` | `29.8` | passes | fails | 2 |
| `10( cid:28)` | `10028` | passes | fails | 2 |
| `Bob` | `808` | passes | fails | 2 |
| `5-3` | `53` | passes | fails | 2 |
| `408,491,218 1,234` | `4084912181234` | passes | fails | 3 |
| `110,626,142.01 92.31` | `1106261420192.31` | passes | fails | 3 |
| `29.18` | `291.8` | passes | fails | 4 |
| `29.` | `2.9` | passes | fails | 4 |
| `(29.1)` | `29.1` | passes | fails | 5 |
| `$-5` | `5` | passes | fails | 5 |
| `6 30,223` | `630223` | passes | fails | 3 |
| `B $23,014` | `823014` | passes | fails | 2 |
| `.5` | `5` | passes | fails | 4 |
| `(29.8l` | `(29.8)` | passes | fails | 2 |
| `Q2` | `0.2` | passes | fails | 2 |
| `69,2` | `6.92` | passes | fails | 4 |
| `67:3` | `673` | passes | fails | 4 |
| `‐2.75` | `2.75` | passes | fails | 5 |
| `2918` | `291.8` | passes | passes |  |
| `1o4.o` | `104.0` | passes | passes |  |
| `(29 1)` | `(29.1)` | passes | passes |  |
| `67: 3` | `67.3` | passes | passes |  |
| `69,2` | `69.2` | passes | passes |  |
| `1,370,4` | `1370.4` | passes | passes |  |
| `(59.8j` | `(59.8)` | passes | passes |  |
| `$ 2.8` | `2.8` | passes | passes |  |
| `$(1,234)` | `(1234)` | passes | passes |  |
| `2Q` | `20` | passes | passes |  |
| `15030B` | `150308` | passes | passes |  |
| `‐435.43%` | `-435.43%` | passes | passes |  |
| `65.8` | `85.8` | fails | fails | 1 |
| `77,500,000` | `7,500,000` | fails | fails | 1 |
| `15030B` on a publisher's text layer | `150308` | passes | fails | 6 |

The rule was run on November 23, 2026, as a prototype outside this repository, with the kit at
`2638173a` for clause 1, for the reader and for the "today" column. It passes all 34 reviewed
readings of the old repository (`reviewed_fixed_decimal_cells` in `config/layouts/qcmr-cash.yml`
at `22f355da`), all of them OCR readings of the cash report. Without the colon in clause 2,
`67: 3` read as 67.3 fails, and it is a right reading. The table above is printed from that run,
and 121 cases in all gave the results that clauses 1 to 6 state. Clauses 7 and 8 were not run.

The rule took four forms, and each change came from a check of the one before.

- The first asked only that each word hold permitted glyphs. A verifier that built it from its
  words alone refused it, because it passed `Bob` read as `808` and joined `408,491,218 1,234`.
- The second stated the word shapes. A second verifier built that from its words, matched every
  row of its table, and found that a word could open with a confusable, so that the quarter
  label `Q2` read as 0.2. The body's first digit glyph is an ASCII digit for that reason.
- The Codex review of the second form found the last three clauses and the comma: `69,2` read
  as 6.92 or 692 as well as 69.2, `15030B` read as 150308, `30,217 6` read as 30217.6, and a
  reviewer could not confirm three amounts the lexer reads.
- A third verifier built the fourth form from its words and matched every row and all 34
  readings. It and the third Codex review changed no result of the table. They corrected this
  section where it disagreed with itself or with a held file: the scanned FY2007 Q4 report, the
  three Textract words that hold a space, and the wording of clauses 4, 7 and 8. No verifier
  and no Codex review has read the section since that last correction.

The step 5 plan carries what the run could not settle.

- None of the 34 readings uses a confusable letter. The pinned list rests on the examples of
  section 3.1 and on VAL-Q36, not on a reviewed reading. It stays as it is, and `l` or `I` for 1
  joins it only when a page shows the need (hard rule 6 of `CLAUDE.md`).
- On an OCR page a confusable still reads as its digit after an ASCII digit, as `1o4.o` needs.
  So `2Q` reads as 20, and `15030B` would read as 150308 on a scanned page. The rule cannot tell
  such a label from a damaged number. The cut keeps labels out of value cells.
- Clause 6 needs to know which kind of text layer a document has. `SourceKind` has one member
  for both. Step 4, which ports the word reader, records which documents carry a scanner's OCR
  as their text layer. Until it does, clause 6 would refuse a right reading of `20.B` on the
  FY2007 Q4 cash report wherever that layer is the primary source.
- A cell that the cut gave a label word takes only a null reading. The first rows of the table
  are such cells, and so is `B $23,014`, which the last word of "Series 2008 A & B" on page 12
  of the FY2010 Budget in Brief would make. The fix for such a cell is the cut, not a reading.
- Two number words read only with the point at their break. `12 345` reads as `12.345` and not
  as `12345`.
- The rule sees no column. In a count column `12 345` still reads as 12.345, where VAL calls
  that input two count cells in one lane, and a count has no fraction. A reading may also place
  a point inside a grouped number, so `1,234` reads as 12.34. Step 5 decides whether assembly,
  which knows the column, refuses a point in a count column or a reading outside the column's
  decimals. `apply_reading` applies no column format today.
- A comma or a colon at the edge of a word prints no point, so `29:` reads as 2.9 while `29.`
  does not.
- Decision 16 names the first join shape only. The second, a fraction digit on a word of its
  own, joins `39,414.37` and `9` into 39414.379 on page 2 of the March 2013 realty transfer
  report, which prints them 68 points apart in two columns. The owner decides whether the size
  and gap test covers both shapes. Clause 8 would confirm either join.
- `load_records` cannot call the whole function. It has the record's text and source and no
  cell, so it can make the tests of clauses 1 and 6 and no more: a confirmation of rows 36 and
  37 would fail clauses 3 and 4 before any cell exists. Section 3.2 says the loader refuses a
  reading whose digits fail, which is clause 1. Step 5 says which clauses run at load.
- An `Unreadable` cell keeps a raised footnote digit in its text, because `Unreadable` has no
  marks. `2918` with a raised `1` then reads only as `2918.1`, where the page prints 291.8 and a
  footnote. Step 5 either gives `apply_reading` the marks the lexer found for an `Unreadable`
  cell, or keeps the mark out at the cut (the notes "What a reviewed reading can still do" and
  "The loader's digit check and a footnoted reading disagree" of `docs/plan-notes.md`).
- A word that extraction glued from two printed numbers still reads. `1,2345,678` reads as
  1.2345678: clause 4 takes its first comma as the point, since four digits follow it, and its
  second as grouping, and clause 7 measures no gap inside one word. The last verifier found
  it at `13b94b9`. The word reader and the cut keep two numbers in two words.
- Clauses 7 and 8 are not yet exact enough to build. Clause 7 does not say how the size of two
  words is compared, or which finding a failure raises. Clause 8 does not say whether clause 6
  still applies to a confirmation. The last verifier asked both, and the step 5 plan answers.
- A cell that prints `.5` takes only a null reading. A reading of `0.5` adds a digit the cell
  does not print, the reader does not read `.5`, and row 14 of VAL section 3.2.1 keeps `.5`
  unreadable.

### 16.3 What was worked out after the owner answered

The owner saw five short recommendations and adopted them. The second column gives each as he
saw it. The third gives what sections 16 and 16.2 hold beyond it. The last says whether he has
confirmed that.

| # | As recommended and adopted | Worked out after | Confirmed |
|---|---|---|---|
| 13 | Every word of the cell must look like a number. A reading may add a point or a sign that extraction lost, and may not move or drop one the cell prints. The confusable list stays. The recommendation also said that confusables would not be limited to OCR pages. | The five clauses and three tests of section 16.2. They add a limit of two number words with the point at their break, a comma or a colon between digits as a point unless the comma groups thousands, a `j` for a closing parenthesis, a first digit glyph that is an ASCII digit, a gap test on two words, and a confirmation of an `Amount`. One of them goes against the recommendation: clause 6 reads a confusable as a digit only on an OCR page, because `15030B` on a publisher's text layer would otherwise read as 150308. | Yes, on November 23, 2026: "I approve the detailed ruled". |
| 14 | A small word joins a line when its bottom falls inside that line's vertical span, at the lexer's 0.7 ratio, proven on the FY2026 Q4 positions page as a word fixture. | The span holds the edge when the line's top is above it and the line's bottom is at or below it. Small is measured against that line's median word height. Where two lines hold the word, it joins the one whose bottom edge is nearer to its own, and on a tie it stays a line of its own. | Not yet. |
| 15 | `N/A` and `NA` in any case. U+2010 as a dash placeholder only, and not a minus sign until a page shows it as one. `#DIV/0!` as a value word that lexes as `NotApplicable`. | U+2010 is also a minus glyph. The FY2021 supplemental report prints it before 2.75 on page 15 and before 435.43% on page 18. The owner was told this in chat and has not answered it. | Not yet. |
| 16 | Keep the join, only at equal size and a small gap, with the limit sized on real fixtures at step 5. | Nothing. One question is open and is the owner's: whether the same test covers the lexer's second join shape (the list at the end of section 16.2). | The question is open. |
| 17 | Off by default. A mark when small and raised, or where the row schema says the pages use digit footnotes. To be decided before step 12. | It is built at step 5, with the row schemas. | Not yet. |

## 17. Known gaps

### 17.1 Reviewer findings fixed in this design

Every finding of kind missing, hand-waved, purity break or logic error against design C is listed
here with the section that answers it.

| Finding | Review | Where |
|---|---|---|
| SUPOP-Q21: no bold rule and no FY2010 era | R1, R2 | 5.2, 6.1 |
| BIB-Q21: bold on scans undefined | R1, R2 | 3.1.1, 6.1 |
| QCASH-Q37: measure per column only | R1 | 2.2 `RowMeasure` |
| QCASH-Q38: page 2 with a damaged caption | R1 | 6.2 `find_balance_page` |
| MCITY-Q18: welded copies and amounts in label spans | R1, R3 | 5.3 |
| QOBL-Q19, Q20: O-3 stop rule and wrapped footnotes | R1 | 6.2 |
| QCASH-Q22, Q23, VAL-Q02: `compare_sources` had no caller | R1, R2 | 3.2, 4.4, 11.3 |
| MCITY-Q20: stacked labels on every edition | R2 | 5.3, 6.1 |
| MCITY-Q21: `truncated_labels_ok` flag | R2 | 2.1 `Truncation` |
| QPOS-Q08, ENT-Q08: prefix numbers could form a lane | R3 | 3.1 `split_line_prefix` |
| QCASH-Q27: unlabeled `RowDef` claims any orphan line | R3 | 2.1 `follows`, 6.2 |
| MSCH-Q23: PILOT relabel makes the misc row missing | R3 | 3.2 `schema_for` |
| VAL-Q28: superscript digits | R3 | 3.1 `lex_cell` |
| DATA:Era filed for measure facts | R1 | 13, `DATA:MeasureSpec` |
| Wrapped source labels open phantom departments | R1 | 5.2 `join_wrapped_labels` |
| City remaining and percent at BLOCK on every row | R1 | 5.3, 8.1 |
| Supplemental percent collected at BLOCK | R1 | 5.2, 8.1 |
| Grand total gets no children | R1 | 3.1.1 |
| `all_funds_total` counts the total among its parts | R1, R2 | 8.2 rule 2, 5.1 |
| "Actual" caption also matches "Prior Year Actual" | R1 | 3.1 `bind_columns` |
| `drop_noted_lines` missing from the records API | R1 | 3.2 |
| MCITY-Q46 note says 0.5, code says 1 | R1 | coverage file |
| Checks silently stop applying (MSCH-Q14) | R2 | 8.2 rule 7, 11.3 |
| `ReleasePlan.blobs` holds bytes | R1, R2, R3 | 4.5 |
| Module-level dicts; `initial={}` | R1, R2 | 5.4, 3.1, 3.2 |
| `run_parse` re-reads the cache to decide again | R1, R2, R3 | 4.4 |
| `run_release` re-runs the parse | R1, R2 | 4.5 |
| `table_module: str` dispatch; `PARSER_REVISION` | R1, R2, R3 | 2.2 `TABLES` |
| `write_index_in_branch` needs an undeclared method | R2 | 4.2 |
| `Http.get(accept_404=...)`, `PdfReader.page_count` | R2 | 4, 4.1 |
| `Clock` port called inside executors | R2 | 1.4, 4 |
| Fetch stages every PDF and copies it | R2 | 4.2 |
| Reader calls `cache.index()`, port says `keys()` | R2 | 4.6 |
| Executors receive registry and records beside the plan | R3 | 4, `RepoSnapshot`, `parse_context` |
| `checks_for` reads the parsed table | R3 | 5, 8.1, 11.2 |
| Import-linter lists omit `os`, `pathlib`, `time`, `random` | R2 | 12.5 |
| `bib_cross` takes `totals[-1]` by position | R2 | 5.4 |
| `Binding` or `None` passed into `assemble` | R1, R2, R3 | 2.1 `CutPages` |
| `split_statements` returns lists | R2, R3 | 5.2 |
| Row keys parsed from strings at import | R2 | 5.3 `RowKey.of` |
| Table name put in `Finding.message` | R2 | 2.1 `Finding.subject` |
| `ctx.edition.edition.period` | R2 | 2.2 `ParseContext.period` |
| `Tolerance` as a literal tag; no `assert_never` | R1, R2, R3 | 2.1 |
| `Term` with three optional fields; `Check` with optional parts | R1, R2, R3 | 2.1 relation classes |
| `RowSel.additive_only` flag | R1, R2 | 2.1 `AdditiveRows` |
| `RowRule.values`, `RowRule.bold` tri-state flags | R1, R2, R3 | 2.1 `Values`, `Style` |
| `NumberFormat.implied_decimal` switch | R2, R3 | 2.1; readings only (8.4) |
| `RowKind` and `Additivity` overlap | R3 | 2.1 `additivity_of` |
| No-bool rule covers only `*_common` | R1, R2, R3 | 11.4 |
| `ERA_OVERRIDE` is a per-document layout switch | R1, R3 | 2.2, 6.1 |
| Department spellings in schemas and registry | R1, R2 | 7.2 |
| Repeated QSMR keys; no rule against acks on them | R1, R2, R3 | 5.5, 8.4 |
| "NA" token unknown to the lexer | R1 | 3.1 `lex_cell` |
| `find_run` drops a second run silently (case F5) | R3 | 3.1 `find_runs`, `only_run` |
| OCR-only values publish as proven (case F4) | R3 | 8.3 `ocr_arithmetic` |
| Textract could run outside a reviewed plan | R3 | 4.3 |
| One stray word stopping a table | R3 | 9 |
| Grammar tables have no line prefix (QSMR-Q04) | R3 | 2.1 `BodyRule.prefix` |
| VOID blocks every CF-3 edition | R3 | 5.5 |
| No Police-lesson test; no ack-shift property | R2 | 11.2, 11.3 |
| `Mapping` fields inside frozen values | R3 | 2.1, 2.2 |
| No rows for unsure quirks (ENT-Q61, QOBL-Q47) | R2 | coverage file |
| `MatchHow` diagnostics on every row | R1, R2, R3 | removed; a truncated match is a WARN finding |
| Protocols with one implementation | R1, R3 | removed; record types live in the kit |
| `datadesk probe` as a feature | R3 | removed |
| `MeasureSpec` list beside `ColumnSpec` can drift | R3 | 11.2 catalog test |

### 17.2 Kept as designed, with the reason

| Item | Review | Reason |
|---|---|---|
| Three row types: `RawRow`, `KeyedRow`, `Row` | R1, R3 | Each stage lacks something the next adds: identity, then lexed cells. Merging them would make half-built rows constructible. |
| `refs.py` and `kinds.py` | R3 | They let `checks` import cell and key types without importing words, which the "arithmetic never sees words" contract needs. |
| `verify_cell_provenance` | R2 | Decision 10. |
| `ObjectStore.list` | R2 | One caller, `plan_parse`, needs the set of archived OCR keys; one listing per run is cheaper than one `exists` per page. |
| `ReleaseRow` with 33 fields | R2 | It is the published schema; each field is something a reader asked for (VAL section 6.1). Values are now typed (`Decimal`, `date`, `Proof`). |
| `PageRun`, `Lane`, `Dated` as dataclasses | R2 | Named fields cost nothing and read better than tuples. `Offset` is gone: the window carries the year basis (section 2.2). |
| `used` record ids from `assemble` and note helpers | R2 | Readings and dash rules already leave ids on cells; notes change lines that leave no trace, so their helpers return the ids. |
| A Python module plus a TOML schema per table | R1 | Two files per table; the schema no longer repeats registry names, which was the drift risk. |
| `MeasureSpec` separate from `ColumnSpec` | R3 | The kit knows no fiscal year; the catalog test stops drift. |
| `checks_for` branches on era and period | R3 | Both are declared inputs, never parsed values; section 11.2 tests that. |
| `bib_cross` builds instances from the tables printed | R3 | The relation is fixed and the instances follow keys, never values; tested like `checks_for`. |
| `caption_lanes` stays in `qsmr_common` at its second user | R3 | Both users are QSMR tables; moving it into the kit would itself fail step 14. It moves only after step 14 passes, as a reviewed change. |

### 17.3 Gaps this design does not close

| Gap | Reason it stays open |
|---|---|
| A level shown only by indent (R3 case F3) | `RowRule` reads no x position. A family helper can rewrite rows first. If two families need it, an indent field on `RowRule` is a reviewed kit change. |
| Two rows with the same exact label in one block of one edition (R3 case F6) | `match_rows` reports `ambiguous_row` and blocks; telling them apart needs print position, which the design refuses outside list tables. |
| Supplemental wrapped-label joins warn instead of blocking | Decision 9. |
| Occurrence keys in list tables are positional among equal names | Accepted for CF-3 only, with acknowledgments refused on them and key changes gated by `--accept-diff`. |
| A 2023 CF-3 name that starts with a 4 to 8 digit token loses it to `line_no` | The printed label keeps every word; the key is affected. Narrow the prefix by era if the corpus shows such names. |
| SUPOP-Q46 comparison with budget books | Budget detail stays in gov-budget-data (section 13). |
| June close column order (City and School) | MCITY section 3 does not list it left to right; confirm on one June page before the first City release. |
| School stacked-label window | MSCH-Q30 gives "2014_07 to about 2015"; the window is a guess until the first run. |
| QSMR era boundaries, VOID position, OF-3 margin numbers | From two editions read through a summarising fetch; placeholders until the corpus is held. |
| QSMR P-1 FY2016 extracts scrambled (QSMR-Q13) | It depends on OCR quality. No design choice settles it. |
| Percent change, share and annual growth columns cannot be checked | None of the six check relations expresses them; `Ratio` covers only one column over another. These columns publish as `unchecked`: 25 of the 272 declared columns, in wage by industry (4), the residency summary (8), sales (5), RTT (6) and Budget in Brief (2). A seventh relation in the kit would be a reviewed kit change. |
| 47 of 272 column descriptions are provisional | The dossiers give the caption and not the meaning: QCMR cash endpoint columns, the three capital tables, residency change columns, the June close "before accruals" columns, and a few more. Each is settled when its table is built, by reading one page. |
| Supplemental "FAMIS" and "Fd BAL/AP Adjs" columns | `NotPublished` until a page shows what they hold (SUPOP-Q15). They are read and can be operands of checks. |
| Supplemental FY2007 to FY2009 | Not found on the City's site (section 16.1). The series has those holes until the documents turn up. |
| QCMR positions FY2008 Q2 | Withheld until its 11 failures are reviewed against the page (decision 5). |

### 17.4 Not verified

- Nothing in this design has been run against a PDF. The code in section 5 parses with Python's
  `ast` module and has not been type-checked; the kit it calls does not exist yet. The one
  exception is the column vocabulary: its lists, types and tests run as Python in
  `final/vocab/`, against column lists taken from the dossiers, not from the documents.
- Line estimates in section 12 are estimates.
- Whether any Budget in Brief category has more than one schedule per fund. The design now
  reports it as a finding (R1).
- Whether FY2010 Water prints its bold line above or below its children (R1).
- Whether O-3 parent blocks equal the sum of their sub-blocks; the check starts at WARN (R1).
- How QCMR cash page 2 reads in the editions where its caption is damaged (R1).
- Whether "Streets" means different things in two tables in one fiscal year. Table-scoped
  aliases can express it if so (R1).
- Whether City pages shift x positions between pages. Binding per page with the page agreement
  check handles either case (R2).
- Whether pdfplumber's font names give a reliable bold flag on these text layers.
- Whether any family prints superscript footnote digits on amounts (VAL section 3).

## 18. The Codex review of November 22, 2026

The owner ran the full plan past Codex (GPT-6.2 Astra at extra-high effort) twice with the prompt
in `codex-review/PROMPT.md`. The two runs agree on every main finding. Codex had the
gov-budget-data checkout and the City's PDFs. It ran the vocabulary tests, applied the P-1 checks
to the printed FY2026 Q4 grid, surveyed fonts on the 20 editions from FY2022 Q1 to FY2026 Q4, and verified a sample of
citations at the old repo's head (two cash line numbers had drifted; the facts held).

### 18.1 Accepted and changed

| Finding | Change | Where |
|---|---|---|
| Swapping General and Other Funds across the FY2026 Q4 P-1 grid, or the rows of two departments, still passes all 291 arithmetic comparisons, so a wrong name can publish as `proven` | `proven` becomes `arithmetic`, which claims only that sums tie. A `bound_by` field says how each column was bound. Labeled fixtures per layout and a cell-by-cell comparison with the pinned gov-budget-data release are the evidence for names. | 2.2, 8.3, 15 step 6 |
| The FY2022 to FY2026 set is 20 editions, not 19; FY2026 Q4 was published August 17, 2026 | Steps 3 to 6 name 20, from a hand-checked inventory of shas | 15 |
| Six P-1 runs open with a commentary page that also prints `TABLE P-1`, and the era is chosen from the first page | The run starts at the first page that carries the era's captions; a band-only page is reported as commentary | 15 step 5 |
| Grid pages in FY2023 Q1 to FY2025 Q2 extract as `(cid:N)` font codes on 20 pages | The PDF adapter ports `repair_cid_words`; a leftover code lexes as `Unreadable`; step 4 checks rendered crops | 15 step 4 |
| Legacy cash "Under (Over) Revenues" is Budget minus Total minus Accrued, and a difference could name only two columns | `Derived(DIFFERENCE)` takes two or more operands: the first minus each later one | 2.2, `vocab/` |
| O-3 Full-Time Positions rows inherited dollars and flow | Row overrides now match on key parts; every column of a `metric=positions` row is a count at a point | 2.2, `vocab/` |
| Monthly opening and closing cash balances inherited flow | Both rows are levels in every column. A month's opening balance is dated at the end of the month before, so it matches that month's close | 2.2, `vocab/` |
| QSMR OF-1 FY2023 has no adopted column and its variance is projection minus amended | Declaration corrected from the District PDF | `vocab/` |
| O-2 FY2026 Q4 prints a six-column year-end form | New `year_end` era | 6.1, 15 step 8 |
| An acknowledgment matched on residual alone survives a different error with the same residual | `ExpectedFailure.operands` pins each operand's row key, column and signed printed value; no coordinates | 2.1 |
| A check whose every result is `MISSING_OPERAND` only warned | It blocks | 8.2 |
| A cell in a passing check and a covered failure met two proof definitions | `acknowledged` wins | 8.3 |
| A whole fund statement can vanish without an arithmetic failure | `ExpectedTables` records list the table instances each edition should hold, from its contents page; a missing one blocks unless a record gives the reason | 18.3 |
| `latest.json` was written with no precondition, so a slower run could undo a newer release | `ObjectStore.put` takes `CreateOnly` or `IfMatch(etag)`; the pointer moves only against the etag read at planning; immutable objects are create-only and a conflict verifies the existing bytes. The old repo already did this (`release_s3.py:513-524`) | 4, 4.5 |
| One edition needing OCR stopped every release | That edition is withheld and the rest release | 4.5 |
| Withholding carried a known-wrong published value forward | A `Withdrawal` record removes named rows, stops the carry-forward and points to a correction | 4.5, 18.3 |
| `watch` read listings only, so a replaced PDF behind an unchanged listing was invisible | Indexed URLs are re-downloaded and hashed on a catalog interval; a new sha goes into the pull request | 3.2 |
| The source comparison saw only overlapping numbers whose digits differ | It also reports sign and decimal differences and numbers one source has and the other lacks; a reading may accept the other source's token | 3.2 |
| The reader trusted its cache by key | It verifies the hash on every open | 4.6 |
| The "Binance" alias named FY2009 Q2; the old continuity test pins FY2012 Q3 | Corrected | 5.1 |
| FY2011 supplemental report is on the City's site | Inventory corrected: 9 of the 12 missing years exist | 16.1 |
| Fund ids were checked by prefix and the vocabulary pins were built from the live enums | A fund must be in the registry; the pins are literal lists | `vocab/` |
| Nothing tied an article's figures to a release | `ArticleFigure` records (section 18.3) | 18.3 |
| "Streets" is a different department on either side of FY2026, and a wrong effective year still gives a valid key and perfect arithmetic | Paired fixtures on both sides of each entity seam; `entity_changed` between releases blocks without `--accept-diff`, like `key_changed` | 4.5, 7, 15 steps 5 and 7 |
| Identical bytes from two builds only show a consistent encoding | Both packaged formats are read back and compared, typed, with the approved rows | 15 step 6 |
| The step 6 canary called `watch`, which step 13 builds | The canary starts from `fetch` of pinned PDFs until step 13 | 11, 15 |
| Step 12 combines nine statements and 32 records under one acceptance | Acceptance per statement; the first difficult operating edition is finished, with review, before the rest | 15 step 12 |

### 18.2 Partly accepted or not accepted

- **The swaps are mutations, not observed misbindings.** Columns bind by printed caption text and
  rows by printed labels through the registry, so the parser would need a bug or a positional
  binding to swap them. The point that arithmetic cannot show the binding stands, and 18.1
  answers it.
- **O-3 "Unaudited Actual" and the later "Year-End Actual (FY-1)" share a subject.** That is the
  intent: matching them is how a restated prior year shows up, and the newest edition already
  wins `is_canonical`. `Subject` now carries the unit, so counts and dollars never meet. Accounting
  basis is carried by `quantity` where the publisher prints it (cash, accruals, budget basis).
- **Shape tests as hard gates.** The closed-list pins stay as failing tests. The 3,800-line and
  140-name budgets become a report printed in CI.
- **The January recommendations.** Codex sized its advice to a January 2027 article: publish
  from the old release (the plan's option A) and defer five pieces of the new code. The owner set
  no date, so option A is dropped and the five pieces are placed by need (section 18.4). The
  old release keeps one role, as the pinned baseline for step 6.
- **Public archive takedown.** Accepted as a procedure: a `Withdrawal` can also remove an
  archived PDF's public bytes while its sha, URL and reason stay in the index. Whether the City's
  terms cover mirroring remains the owner's accepted risk.

### 18.3 New records and modules

```python
# datadesk/core/records.py (added)
@dataclass(frozen=True, slots=True)
class ExpectedTables:
    id: str
    doc_sha256: str
    table: str
    instances: tuple[str, ...]       # TableId instance strings the contents page lists
    absent: tuple[tuple[str, str], ...] = ()   # (instance, reason) for listed tables not printed


@dataclass(frozen=True, slots=True)
class Withdrawal:
    id: str
    dataset: str
    edition_id: str
    rows: tuple[str, ...]            # row keys; empty means the whole edition
    reason: str
    correction: str                  # URL of the published correction
    archive_bytes: Holding | None = None   # set to remove a PDF's public bytes as well


# datadesk/core/articles.py
@dataclass(frozen=True, slots=True)
class ArticleFigure:
    id: str                          # "vacancy-rate-fy2026"
    article: str                     # slug
    manifest_sha256: str             # the pinned release
    formula: str                     # "1 - actual_total / adopted_total"
    cells: tuple[tuple[str, str, str, str], ...]   # (dataset, edition_id, row key, column)
    printed: str                     # the figure as the article prints it
    pages: tuple[str, ...]           # "sha8:p33"
    reviewed_by: str
    reviewed_on: date


def recompute_figures(figures: Sequence[ArticleFigure], rows: Sequence[ReleaseRow]) -> tuple[Finding, ...]: ...
```

`ExpectedTables` matters for open families: the supplemental report, Budget in Brief schedules,
and later the QSMR. A closed table already blocks on a missing required row. A CI test recomputes
every `ArticleFigure` from its pinned release; a correction is rehearsed once before the first public release by
withdrawing a figure in a test release.

### 18.4 Built where first needed

Codex proposed deferring five pieces to reach a January date. With no date they are all built,
each at the step that first needs it:

- The reader's `api`, `plan`, `pin`, `lineage` and adapters (590 lines) at step 13. By then the
  manifest has carried every family, and the return type is settled against them: the
  engineering plan promised pandas by default, and the example in section 4.6 returns an Arrow
  table. Step 6 ships files, a manifest, a checksum command and the read-back test.
- `suggest.py` (210) at step 8, for the cash identities, the first not already known.
- `acks_migrate.py` (140) at step 7, where the seven historical acknowledgments are.
- `grammar.py` (260) at step 8, for O-2.
- The parse-result cache is dropped for correctness, not time. Its key left out the table name
  and the comparison word keys, and a parser run over cached words is quick. The word cache
  stays. If builds become slow, the cache returns with those fields in its key.

The section 12 totals count all of these, including the parse cache's share of `codec` and the
planner (about 100 to 180 lines), so they stay an upper bound.

### 18.5 Size

The changes add about 405 lines: conditional writes and the pointer race (55), font repair (60),
watch re-hash (55), the new records and article figures (140), withdrawals and `bound_by` in the
release (30), the acknowledgment fingerprint (20), the source comparison (20), per-edition OCR
withholding (15) and the reader's cache check (10).
