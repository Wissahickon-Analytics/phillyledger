# Design principles for the phillyledger repo

Written from primary sources on November 21, 2026. Claims about Oxide come only from its
public Reconfigurator document. Anything not found in a source is marked "not confirmed".

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
  compared and shared.
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

## Sources

- Gary Bernhardt, "Functional Core, Imperative Shell" (screencast):
  https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell
- Gary Bernhardt, "Boundaries" (talk): https://www.destroyallsoftware.com/talks/boundaries
- "Network protocols, sans I/O": https://sans-io.readthedocs.io
- "Writing I/O-Free (Sans-I/O) Protocol Implementations":
  https://sans-io.readthedocs.io/how-to-sans-io.html
- Oxide, `omicron` repository, `docs/reconfigurator.adoc`:
  https://github.com/oxidecomputer/omicron (read through a mirror of that file)
