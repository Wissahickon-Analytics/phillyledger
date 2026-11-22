# phillyledger

Checked tables of Philadelphia budget and finance data, read from the City's and the School
District's published PDFs. Every number comes from words on a printed page, and every table
carries declared arithmetic checks that must pass, or be acknowledged with a page citation,
before it is released.

Three packages live here:

- `checkedtables`: a general kit for turning PDF words into checked tables.
- `phillyledger`: a reader for the released data.
- `datadesk`: the Philadelphia-specific parsers, registry and release tooling.

Nothing is built yet. The design is in [`docs/design.md`](docs/design.md), and progress through
its build order is in [`docs/progress.md`](docs/progress.md).
# phillyledger
