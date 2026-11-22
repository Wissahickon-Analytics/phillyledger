# Column vocabulary prototype

A tested prototype of the closed column vocabulary in design section 2.2, written before any
package existed. It declares all 23 in-scope column sets (40 layouts) and the four held-out QSMR
tables, and checks them against 72 sample editions.

- `vocab.py`: the six closed lists.
- `measures.py`: `Stated`, `Derived`, `NotPublished`, `MeasureSpec`, `RowMeasure`, `Scope`,
  `Subject` and the functions that turn a declaration into a description.
- `tables.py`: every column set, with captions and sample editions.
- `test_vocab.py`: the tests. `python test_vocab.py` prints a summary and fails on any broken
  rule. `python test_vocab.py --write` also writes `COLUMNS.md`.
- `render_ref.py` writes `REFERENCE.md`, the column reference.

Step 5 ports `vocab.py` and `measures.py` into `datadesk.core`, and each table's declaration into
its table module when that table is built. The tests move with them. Nothing in `packages/`
imports from this folder.
