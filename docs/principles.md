# Design principles for the phillyledger repo

Written from primary sources on November 21, 2026. Claims about Oxide come only from its
public Reconfigurator document. Anything not found in a source is marked "not confirmed".
Section 8 was added on November 25, 2026, with no copy of its source at hand, and says so.

## 1. Functional core, imperative shell

The phrase comes from Gary Bernhardt's Destroy All Software screencast of that name and his
2012 talk "Boundaries". The program is split in two.

- The core is pure functions over plain values. It holds the decisions, so it has many code
  paths and almost no dependencies. It can be tested with values in and values out.
- The shell reads and writes the outside world: files, network, database, terminal. It acts on
  values the core returns. It has many dependencies and should have very few code paths.
- Values, not objects with behavior, cross the boundary between the two. That is what lets the
  boundary move without rewriting either side.

The test of the split is where an `if` lives. A branch that depends on the data belongs in the
core. A shell with real branching has taken decisions that cannot be tested without I/O.

## 2. Sans-I/O in Python

The Python community's sans-I/O work applies the same idea to network protocols. A sans-I/O
library performs no network I/O and no asynchronous control flow. It is plain synchronous
functions over bytes or text, and the caller drives the I/O. The stated reason is reuse: the
same protocol code then serves blocking and async callers. Libraries built this way include
`h11`, `h2` and `wsproto`. The lesson for this repo is that "abstracting the I/O behind an
interface" is weaker than "the core never sees I/O at all".

## 3. How Oxide applies it: plan, then execute

Oxide's control plane (the `omicron` repository) has a facility called Reconfigurator. Its
design document names the plan-execute pattern as fundamental. What the document says:

- A planner takes the current policy and the latest view of the system and produces a
  blueprint. Planning changes no state. A blueprint that never becomes the target has no
  effect.
- A blueprint is immutable. A change makes a new blueprint.
- A blueprint is specific. It carries every detail needed, down to ids and addresses, so that
  execution involves no meaningful choices.
- An executor works to make reality match the target blueprint. Execution can be slow, can
  fail partway and can be retried. The executor does not make allocation decisions. Those
  belong to the planner.
- Because the planner is deterministic and has no side effects, it is easy to test, and an
  operator can generate a blueprint and compare it with the current one before committing.
- The planner works from a view of the world that may be incomplete or out of date, and the
  design accepts that.

Not confirmed: whether the planner function itself reads the database or is handed a prepared
snapshot. The document does not say.

## 4. The pattern, stated for this project

Every operation that touches the world has three steps.

1. Gather. The shell reads what the decision needs and builds a snapshot as plain values.
2. Plan. A pure function takes the snapshot and returns a plan as plain values.
3. Execute. The shell carries out the plan. It makes no decision the plan did not make.

| Operation | Snapshot (values in) | Plan (values out) |
|---|---|---|
| `watch` | saved listing pages, the archive index, today's date | files to fetch, index lines to add, gaps to report |
| `fetch` | the plan from `watch`, response bytes and hashes | objects to store, index lines, rejections with reasons |
| `parse` | page words for one document, the table specification, the row schema | a typed table with evidence, or findings |
| `check` | tables, declared checks, acknowledgment records | a check report |
| `release` | checked tables, the previous manifest, the release id | files to write with their bytes, the manifest, the row diff, the pointer change |
| reader `load` | the manifest, the request, what the cache holds | downloads to make, hashes to verify, the path to open |

A plan can be printed, diffed, stored and reviewed. That is what makes a dry run, a pull
request and a release gate cheap: each is a plan that has not been executed yet.

What goes wrong when decisions leak into the executor: the same input stops giving the same
output, a retry can take a different branch, tests need the network again, and a dry run no
longer shows what will happen.

## 5. Rules for this code, with reasons

- Domain values are frozen dataclasses and enums. A value that cannot change can be cached,
  compared and shared. The one exception is a value that is one piece of text with a rule,
  such as `Sha256`: a `str` subclass whose constructor checks the rule (section 8.3).
- Every effect sits behind a `typing.Protocol` port owned by the shell: HTTP, object store,
  OCR service, local cache, git host, clock. The core imports none of them.
- The core has no file, network, clock, environment, randomness, logging handler or
  module-level mutable state. Time, ids and configuration arrive as arguments.
- The same inputs give the same outputs, byte for byte. Sort every collection before it is
  written. This is what lets a result be cached by the hash of its inputs.
- A problem in the data is a returned value, because the caller must decide what to do with
  it. An exception means a bug or a failed effect, and only the shell catches effect failures.
- Money is `Decimal` or integer cents, never float.
- Make wrong states hard to build. A cell that is "blank", "dash" or "amount" is three cases
  of one type, not one field with two flags.
- Pure functions get example tests and property tests. Adapters get contract tests against a
  fake and, where cheap, the real thing. One end-to-end test proves the wiring.
- import-linter enforces the boundary: core packages may not import `boto3`, `httpx`, a PDF
  library or the shell.

## 6. Where the principle should bend

- Do not build an effect system. Plans are small dataclasses and executors are short loops.
  An interpreter for a general effect language is more machinery than this repo needs.
- Reading a PDF's words is an adapter, and it is fine for it to be one function that opens a
  file and returns values. Do not model each read as a planned action.
- Some work is a loop of gather, plan, execute, because the next decision needs the result of
  the last action (download, then hash, then decide). Use several small plans. Do not force
  one giant plan that pretends to know results in advance.
- Large byte payloads should be passed by content hash and fetched by the shell when needed,
  so plans stay small enough to read.
- Logging and progress output belong to the shell. The core returns findings, and the shell
  decides how to show them.
- A port with one real implementation and one fake is enough. Do not add layers that only
  forward calls.
- Purity is not the goal by itself. The goal is that every decision about the data can be
  tested without the world, and every action on the world can be reviewed before it runs.

## 7. Purity checklist for a reviewer

1. Does any core module import an I/O library, `os`, `pathlib` file methods, `datetime.now`,
   `random`, `logging` handlers or `time`?
2. Does any core function take a path, a client or a session instead of values?
3. Does any shell function contain a branch on the content of the data?
4. Can each plan be serialized, printed and compared with yesterday's plan?
5. Does the executor need anything that is not in the plan?
6. Given the same snapshot twice, is the plan identical byte for byte?
7. Can the whole core test suite run with the network unplugged and an empty temp directory?
8. Is there module-level mutable state, a registry filled at import time, or a cache inside
   the core?

## 8. Types and docstrings that say what the code means

Added on November 25, 2026. The owner read the pull requests of step 3 and wrote: "we need to
maintain docstring standards. I see some functions without any docstrings. We need the code to
be readable. I'd like to also follow the principles outlined in the "Robust Python" book by
Patrick Viafore. I'd like to incorporate those principles with our existing core/shell set up
too". In the same message he chose typer for the command line. This section is the repo's
answer, and `CLAUDE.md` (Code) holds the rules in short form.

Not confirmed: every claim below about what the book says. The session that wrote this section
had no copy of the book, and O'Reilly's page for it refused the request that day. The section
names the book's four parts from memory and quotes nothing from it.

### 8.1 What the book argues

Code is read and changed for years by people who cannot ask its author what was meant. Robust
code tells them. A name, a type and an interface are each a message to that later reader, and
the best message is one a tool checks on every commit. The book has four parts.

- "Annotating Your Code with Types": a type hint is a checked statement of intent. The narrow
  forms (`Optional`, `Union`, `Literal`, `NewType`, `Final` and the collection types) say more
  than `str` or `list` can.
- "Defining Your Own Types": an enum for a closed set, a data class for fields that vary
  freely, a class when the fields must obey a rule together, interfaces that are easy to use
  correctly and hard to use incorrectly, protocols, and a check on outside data at the point
  where it enters the program.
- "Extensible Python": new behavior arrives without edits to what exists, dependencies stay
  visible, and policy is kept apart from mechanism.
- "Building a Safety Net": linters, tests that state behavior, property tests and mutation
  tests.

### 8.2 How it joins the core and the shell

Sections 1 to 4 say where effects go. The book says what the values that cross the boundary
should look like. Together they give one rule: text is parsed once, and past the parser the
code takes only types.

- The shell reads bytes, text, environment variables and command-line words. One pure function
  for each format turns them into typed values, as `parse_index` and `parse_listing` do. A
  value that breaks its type's rule stops there, as a finding or as refused input.
- Past the parser no function takes a `str`, a `dict` or a `tuple` whose meaning the reader
  has to look up. It takes the type.
- The function that builds a type checks its rule, so the core does not check it again. A
  defensive check deep in the core is a sign that some type is too loose.
- A plan is already this kind of value. It is specific, immutable and printable (section 3),
  so the executor has nothing left to decide and nothing left to validate.

### 8.3 Rules, with reasons

- A value with a rule of its own has a type of its own. A sha256 is 64 lowercase hex
  characters, and `str` says none of that. Where there is a rule to check, the type is a
  frozen, slotted dataclass with one builder that checks it. Where the value is one piece of
  text with a rule, the type may instead be a `str` subclass with empty `__slots__` whose
  constructor checks the rule and builds from the text it checked, as `Sha256` is. It equals
  its text and serves as a key, a path or JSON, so the files it is written to keep their bytes.
  It overrides only `__new__` and `__repr__`, so it changes how a value is built and printed,
  not what code does with it. Where there is only a meaning to keep apart, such as two kinds of id, `typing.NewType` is
  enough. What the builder does with a bad value follows section 5: a problem in the
  publisher's data comes back as a value. Step 3 shows the cost of the loose form. Pull request
  38 added a guard to `parse_index` for a sha that was not 64 lowercase hex characters, and its
  review then found the sha that was not a string at all. Standards sweep B gave the sha its
  type. On November 25, 2026 the owner was shown three forms of `Sha256` with their pytest and
  `ty` counts, whether the index bytes change and their `repr`, and chose "Checked str
  subclass (Recommended)". Its text said the form "needs 8.3 reworded to allow this form for a
  value that is one piece of text".
- A result with more than one outcome is a union of named types. It is never a bare `str` or
  `tuple` that stands for "it failed". The caller handles each member and ends with
  `typing.assert_never`, so `ty check` fails at every caller that ignores a new member. A run
  on November 25, 2026 showed that `ty` reports the missed member after a `match` and after a
  chain of `isinstance` checks. At head `3643f40`, `qcmr_period` returned `Period | str`, where
  the `str` was a refusal code, which is the loose form. Standards sweep B made it return
  `Period | PeriodRefusal`, and `confirm_period` ends its `match` in `assert_never`. This
  section also called `isinstance(repo, tuple)` in `fetch_command` the loose form. Asked on
  November 25, 2026 "Should the sweep B build reword 8.3 so it no longer says that?", the owner
  chose "Yes, withdraw it (Recommended)", so it no longer does.
- A closed set of values is a `StrEnum`, pinned by a test (hard rule 6). A `str` parameter that
  takes one of four words is an enum that nobody wrote.
- Fields that vary freely are a frozen dataclass. Fields that must agree with each other get
  one builder that checks the agreement, and nothing else builds the type.
- An interface is written from the caller's side. What a function needs is a typed parameter,
  never something to set up first. Gather, plan, execute already works this way: `run_fetch`
  takes the plan that `plan_watch` returned, so it cannot run before it. When two parameters
  share a type, a caller can swap them and no tool notices. Give one a type of its own, or make
  both keyword-only.
- Behavior varies by a `Protocol` port or by a member of a union. It never varies by a subclass
  that overrides part of its parent, and never by a flag. Hard rule 5 holds the last point for
  the kit.
- A name comes first, then a type, then a test, then a docstring. Each says what the one before
  could not. A docstring tells the reader what the value means on the printed page, its unit
  and its period, what comes back when the input is bad, and which page or quirk forced a
  choice. A docstring that repeats its signature tells the reader nothing, and it can still go
  out of date.
- A docstring is a sentence, and it can be false. A reviewer reads it against the code under
  it, the same way as a sentence in the design.

### 8.4 One docstring, before and after

At head `3643f40`, `qcmr_period` has no docstring. Its name and types leave three questions
open: which text on the page it reads, what the `str` is, and why a date can be refused. This
docstring answers them.

```python
def qcmr_period(page1_text: str) -> Period | str:
    """Read the quarter that a QCMR cover prints.

    The cover prints "FOR THE PERIOD ENDING <Month> <D>, <YYYY>" (QCASH-Q05, QOBL-Q04). Every
    such caption on page 1 is read, and all of them must give one date.

    Returns
    -------
    Period | str
        The three months that end on the printed date. Otherwise a refusal code:
        "period_unreadable" when the page has no caption, or has one with no date a program
        can read, "period_ambiguous" when two captions give different dates, and
        "period_not_a_quarter_end" for a date that ends no quarter.
    """
```

`"""Read the period."""` would pass ruff and tell the reader nothing. Under the second rule of
8.3 the `str` becomes a named type, and the `Returns` section shrinks to a line.

### 8.5 The command line

The rule: `datadesk` uses typer, in `datadesk.shell.cli` and nowhere else. At head `3643f40` it
still uses `argparse`. A typer command is a function whose typed parameters are the command's
arguments. The signature is the specification, and `--help` is generated from it. Three limits
keep it inside the shell's job.

- A command function builds `Deps`, calls one plain function and prints. The plain function is
  what tests call, as they call `fetch_command` at head `3643f40`. A command function holds no
  branch on the data (section 1).
- typer's own traceback printing is switched off with `pretty_exceptions_enable=False`. typer
  0.28.0, the version the lock pins, has it on by default (read from the signature of
  `typer.Typer` in the installed package on November 25, 2026). `main` sends
  every line it prints through `hide_keys`, and a traceback that typer prints itself would not
  pass through it (hard rule 8).
- Design section 9 says how each kind of stop exits. typer and click have their own handling
  of `--help`, a usage error and Ctrl-C, so the pull request that moves `datadesk` to typer
  writes that section again from runs.

### 8.6 The safety net

The book's last part maps onto gates this repo already runs.

| The book asks for | Here |
|---|---|
| A type checker and a linter on every change | `ty check` and ruff, among the six gates |
| Checks written for this code base alone | the purity test, the shape test, the pin tests and import-linter |
| Tests that state what a user was promised | the clauses of each step's check, each proven by a named test |
| Property tests | Hypothesis |
| Mutation tests | each new test is run with its rule removed, and the pull request records the run |

No mutation tool runs in the gates. A session makes each mutant by hand, runs it and restores
the code.

### 8.7 What this repo does not take

- `checkedtables` takes no runtime validation library such as pydantic, because it is
  published with no dependencies. For `datadesk` the choice is not made. The owner makes it at
  the step that builds the TOML loaders, most likely step 5, from a run that reads the same TOML
  with a hand-written loader and with a strict pydantic loader. The run includes the two cases
  that the review of pull request 38 found in `parse_index`: a sha that was not a string, and a
  `urls` list whose items were not strings. Until then typer stays below 0.29, because typer
  0.29.0 depends on pydantic, so pydantic is not installed. The owner chose this on November 25,
  2026, with the words "Keep the cap".
- No event system and no plug-in loading. Plans are small dataclasses and executors are short
  loops (section 6).
- No inheritance trees.
- No separate language for acceptance tests. A step's check is prose in design section 15, and
  a named test proves each clause.

### 8.8 Checklist for a reviewer

1. Past the parser, does a function take a `str`, `int`, `dict` or `tuple` whose meaning a type
   could carry?
2. Does a core function recheck a rule that a type's builder already holds?
3. Can a caller ignore one outcome of a result while `ty check` still passes?
4. Does a public name lack a docstring? Does a docstring only repeat its signature?
5. Is each docstring true of the code under it?
6. Does anything outside `datadesk.shell.cli` import typer? Does a command function branch on
   the data?
7. Can `datadesk` print a line that did not pass through `hide_keys`?

## Sources

- Gary Bernhardt, "Functional Core, Imperative Shell" (screencast):
  https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell
- Gary Bernhardt, "Boundaries" (talk): https://www.destroyallsoftware.com/talks/boundaries
- "Network protocols, sans I/O": https://sans-io.readthedocs.io
- "Writing I/O-Free (Sans-I/O) Protocol Implementations":
  https://sans-io.readthedocs.io/how-to-sans-io.html
- Oxide, `omicron` repository, `docs/reconfigurator.adoc`:
  https://github.com/oxidecomputer/omicron (read through a mirror of that file)
- Patrick Viafore, "Robust Python: Write Clean and Maintainable Code", O'Reilly Media, July
  2021, ISBN 9781098100650 (not read for section 8, as that section says):
  https://www.oreilly.com/library/view/robust-python/9781098100650/
