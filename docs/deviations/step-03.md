# Step 3: deviations from the design

What step 3 changed in `docs/design.md`, and why. The design holds each rule as it now stands,
so read this file only to learn why the design says what it says. Each entry: what changed,
why, the run that shows it, and the design section updated. Shape numbers refer to "Shapes the
design leaves open" in `docs/plans/step-03.md`.

- **Step 3: a QCMR edition's period is its fiscal quarter** (November 23, 2026, S3-A). The
  design gave no period for a QCMR edition. It is now `Period(first day of the quarter, printed
  end)`, so editions never overlap and FY2026 Q4 is `qcmr:2026-06-30:none` (shape 1). S3-A
  records the rule. No code derives it yet, and S3-B does. Design sections 2.2 and 6.3.
- **Step 3: the versions of an edition form one chain** (November 23, 2026, S3-A). The design
  gave `current` no rule. It is now the edition's version that no other version supersedes, and
  a version may share its `listed_at` with the one it supersedes, so new bytes behind an
  unchanged URL can be recorded (shape 2). `index_problem` in `domain.py` names the first rule
  a tuple of versions breaks, as a BLOCK finding: out of order, one sha on two lines
  (`content_alias`), a `supersedes` that names no version of its own edition
  (`supersedes_outside_edition`), an edition with two versions that nothing supersedes
  (`two_current_versions`), or an edition whose versions are not one chain (`broken_chain`).
  The chain rule follows `supersedes` from the version that nothing supersedes and requires the
  walk to reach every version of the edition once and then end, so a version that supersedes
  itself, two versions that supersede each other beside a third, and a chain that runs into a
  cycle are all refused. Without it `current` can return `None` for an indexed edition.
  `ArchiveIndex` raises `ValueError` with that finding's message, and `add_versions` returns the
  finding, so each rule is written once. The design's `__post_init__` checked only for one sha
  indexed twice. With `current` changed to return the edition's last version,
  `test_current_is_the_version_that_nothing_supersedes` fails. With the `broken_chain` rule
  removed, `test_index_refuses_an_edition_whose_versions_are_not_one_chain`,
  `test_add_versions_refuses_a_version_that_supersedes_itself` and
  `test_add_versions_refuses_two_versions_that_supersede_each_other_beside_a_third` fail, and
  with only the stop on a repeated version removed, the `a_chain_that_runs_into_a_cycle` case
  fails. Design sections 2.2, 6.3 and 12.3.
- **Step 3: the index sorts by `(edition, listed_at, sha256)`** (November 23, 2026, S3-A). The
  design sorted by `(edition, listed_at)`, which is not a total order once two versions of one
  edition share a `listed_at`. The sha is the last key. `ArchiveIndex` refuses an unsorted
  tuple, and `parse_index` and `add_versions` sort through `sort_versions` before they build
  one. With the sha dropped from the key,
  `test_index_orders_versions_of_one_edition_by_listed_at_then_sha` fails. Design section 2.2.
- **Step 3: the index file and its line** (November 23, 2026, S3-A). The design gave no path
  and no line format. The file is `packages/datadesk/src/datadesk/data/index.jsonl`, which S3-D
  creates. Each line is `dumps(asdict(version))` with dates in ISO form and `ensure_ascii`
  off, then a newline, so the edition keeps its period start and the empty index renders as
  `""` (shape 3). `parse_index` splits on `"\n"` alone. With `splitlines()` in its place, the
  Hypothesis property `test_parse_index_reads_back_what_render_index_writes` fails, because a
  title may hold a character such as U+2028 that `splitlines()` breaks on and `dumps` leaves
  unescaped. Design section 3.2.
- **Step 3: `add_versions` merges a new URL into its version's line** (November 23, 2026, S3-A).
  The design did not say what `add_versions` does with a sha it already holds. A new version
  whose sha and edition are indexed adds its URLs to that line, after the URLs it holds and
  without repeats, and changes nothing else (shape 7). A sha under another edition becomes a
  second line, and `index_problem` turns it into a `content_alias` finding. With the merge keyed
  by sha alone, `test_add_versions_refuses_a_sha_indexed_under_another_edition` fails, because
  the alias merges into the other edition's line. The `superseded_sha_relisted` rejection and
  the `listed_at` order belong to `plan_fetch` in S3-C. Design sections 3.2 and 6.3.
- **Step 3: `datadesk.core` imports from seven outside modules** (November 23, 2026, S3-A). The
  closed list in section 11.1 was empty. `domain.py` and `index.py` import `Counter`,
  `Iterable`, `Sequence`, `asdict`, `dataclass`, `replace`, `date`, `StrEnum`, `dumps`, `loads`
  and `Any`, by name, and `PURE_IMPORTS["datadesk.core"]` in `tests/test_purity.py` pins the
  eleven pairs. Design section 11.1.
