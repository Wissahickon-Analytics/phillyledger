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
  creates. Each line is `dumps(asdict(version))` with keys sorted at every level, dates in ISO
  form and `ensure_ascii` off, then a newline, so the edition keeps its period start and the
  empty index renders as `""` (shape 3). Sorted keys follow section 10, which renders all JSON
  (index, manifest, plans) with sorted keys. With `sort_keys` dropped,
  `test_render_index_writes_one_line_for_each_version_with_sorted_keys` fails. `parse_index`
  splits on `"\n"` alone. With `splitlines()` in its place, the Hypothesis property
  `test_parse_index_reads_back_what_render_index_writes` fails, because a title may hold a
  character such as U+2028 that `splitlines()` breaks on and `dumps` leaves unescaped. Design
  section 3.2.
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
- **Step 3: the source catalog and its TOML** (November 24, 2026, S3-B). The design named
  `SourceCatalog` and `SourceEntry` with no fields. `SourceEntry` holds `id`, `series`, `shape`,
  `listing_url`, `category` and `first_period_end`, and `catalog.toml` holds one `[[source]]` table
  for each (shape 4). `load_catalog` parses the text and returns each problem as a BLOCK finding. A
  date and time where a date belongs is one. `entry(id)` raises `KeyError` for an id the catalog
  lacks, and `SourceCatalog` refuses a repeated id. With the check of exact field types replaced by
  `isinstance`, the `a_date_and_time` case of `test_load_catalog_returns_a_finding_for_each_problem`
  fails. Design section 3.2.
- **Step 3: a QCMR edition comes from its title** (November 24, 2026, S3-B). The design gave the
  title rules no shape. `qcmr_title` reads "Quarterly City Managers Report" or "Quarterly City
  Manager's Report", a hyphen or an en dash, and a date, and nothing more. A quarter-end date gives
  `EditionKey("qcmr", Period(first day of the fiscal quarter, the date))`, as S3-A recorded, and the
  URL is never read, so `...March-30-2026R.pdf` under its March 31 title is FY2026 Q3 (risk 4). A
  title with "infographic" is `infographic`, a report title with any other date is
  `not_a_quarter_end` (shape 5), and every other title is `unrelated`. So the old test's "Quarterly
  City Managers Report Revised - June 30, 2025" is `unrelated`, and an executive summary or an
  excerpt titled after a report is never read as the report. The City's second uploads keep the
  title (plan fact 5). With the apostrophe dropped from the rule,
  `test_managers_and_manager_s_read_the_same` fails, and with the quarter-end check dropped,
  `test_a_report_title_dated_on_any_other_day_is_not_a_quarter_end` fails. Design section 3.2.
- **Step 3: `ListedLink.listed_at`, and a parser per page shape** (November 24, 2026, S3-B). The
  design gave `ListedLink` no upload time, so `plan_watch` could not find the last link of an
  edition. The owner decided that `ListedLink` gains `listed_at`, filled by the shape's parser,
  because that parser alone knows the page. For document-finder it is the 14-digit upload stamp in
  the URL path (shape 2). A document-finder URL with no stamp makes the whole listing unreadable.
  All 97 QCMR links of the July 28, 2026 recording carry one, so a link without one means the page
  changed shape. A shape parser returns `PageLink(title, url, listed_at)`, and `parse_listing` reads
  the title and puts the URL on `www.phila.gov` (QCASH-Q04), so no shape module imports the
  `listings` package. `ListedLink` refuses a link with both an edition and a skip reason, or
  neither. With `listed_at` left empty, `test_each_link_is_listed_at_its_upload_stamp_in_feed_order`
  and three tests of `plan_watch` fail. Design section 3.2.
- **Step 3: `parse_listing` returns `Listing | Finding`** (November 24, 2026, S3-B). The design
  returned a `Listing` alone, so a feed that is not JSON, a category that is missing, a shape with
  no parser yet (`phila_documents`, `manual`) and a series with no title rule had no answer but an
  exception. Each is now a BLOCK finding, `listing_unreadable` or `listing_unsupported`.
  `test_a_shape_with_no_parser_yet_is_a_finding`, `test_a_series_with_no_title_rule_is_a_finding`
  and `test_a_feed_the_parser_cannot_read_is_a_finding` show each case. Design section 3.2.
- **Step 3: `plan_watch`, first cut** (November 24, 2026, S3-B). The design's comment named rules
  for step 13 and no first cut. S3-B builds shape 5. The last link of each edition wins, an edition
  that ends before `first_period_end` is dropped, and a kept link is asked for unless an indexed
  version of its own edition holds its URL, with the reason `new` or `revision`. The last link is
  the one with the greatest `listed_at`. On equal stamps the link listed first wins, since the feed
  lists its quarters newest first. No edition has two links in the July recording or in the feed
  saved on November 23, 2026, so the tie rule is fixed and stated rather than shown by a page. A
  `not_a_quarter_end` link is a WARN finding of that code. The link is never fetched, so no wrong
  period enters the index, and the other editions are still fetched. `PullRequestPlan` holds `files`
  as `(path, text)` pairs. With the tie rule reversed,
  `test_a_tie_of_upload_stamps_goes_to_the_link_listed_first` fails. With feed order in place of the
  stamp, `test_the_last_of_two_attachments_for_one_quarter_is_asked_for_alone` fails. With the floor
  removed, four tests fail. With the URL matched against every edition,
  `test_a_url_that_another_edition_holds_is_still_asked_for` fails. Design sections 3.2 and 6.3.
- **Step 3: `fiscal_quarter` takes any date** (November 24, 2026, S3-B). The design gave the quarter
  of a quarter end alone. Any date now gives the fiscal quarter it falls in, so the function has no
  failure case. The Hypothesis property
  `test_the_fiscal_quarter_turns_on_the_first_of_january_april_july_and_october` draws days from
  1900 to 2199, so a version that refuses other days fails it. Design section 3.2.
- **Step 3: `datadesk.core` imports from four more outside modules** (November 24, 2026, S3-B).
  `catalog.py` parses TOML with `tomllib`, `listings/__init__.py` hashes the listing with `hashlib`,
  the listing modules use `re`, and `periods.py` and `titles.py` hold constant maps in
  `types.MappingProxyType`. `PURE_IMPORTS["datadesk.core"]` in `tests/test_purity.py` pins seven new
  pairs: `collections.abc.Callable`, `hashlib.sha256`, `json.JSONDecodeError`, `re.compile`,
  `tomllib.TOMLDecodeError`, `tomllib.loads` and `types.MappingProxyType`. Design section 11.1.
