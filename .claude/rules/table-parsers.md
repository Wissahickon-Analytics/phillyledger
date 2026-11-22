---
paths:
  - "packages/datadesk/**/tables/**/*.py"
  - "packages/datadesk/**/data/**"
---

# Table parsers and their data

Design section 5 shows how a parser is written, section 6 covers eras and editions, section 7
row identity, section 8 checks and acknowledgments.

- One parser per table. Its eras are constants chosen by printed captions, never by date alone.
- Columns bind by printed caption, rows by printed label through the registry. Never bind by
  position when a caption or label is available.
- Edition-specific facts are records in `data/`, each with a document sha, a page and a reason.
  A record that is never used blocks.
- Every column has a description in the vocabulary (design section 2.2). Two columns of one
  table with the same description fail the catalog test.
- Read the family's dossier in `docs/evidence/dossiers/` before writing the parser, and mark
  the quirks it handles in `docs/evidence/coverage.tsv`.
- An acknowledgment pins each operand's row key, column and signed printed value. It never
  targets an occurrence key.
