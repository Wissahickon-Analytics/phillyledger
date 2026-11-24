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
  excerpt titled after a report is never read as the report. The word in the month's place is any
  run of letters, so "Smarch 31, 2026" is `not_a_quarter_end` too, and a report title with a bad
  date raises a WARN instead of vanishing. The City's second uploads keep the title (plan fact 5).
  With the apostrophe dropped from the rule,
  `test_managers_and_manager_s_read_the_same` fails, and with the quarter-end check dropped,
  `test_a_report_title_dated_on_any_other_day_is_not_a_quarter_end` fails. With a word that names
  no month read as `unrelated`, the `a_month_that_is_not_a_month` case of
  `test_qcmr_title_reads_an_edition_or_a_skip_reason` fails. A letter is a character that
  `str.isalpha` accepts, so "Märch" makes a report title and "Mar½ch" does not. With ASCII letters
  alone, the `a_month_word_with_a_letter_outside_ascii` case fails. With `[^\W\d_]`, which also
  takes number signs such as "½", the `a_month_word_with_a_character_that_is_not_a_letter` case
  fails. Design section 3.2.
- **Step 3: `ListedLink.listed_at`, and a parser per page shape** (November 24, 2026, S3-B). The
  design's rule "Later `listed_at` wins" (section 6.3) needs the upload stamp of each link, and the
  design's `ListedLink` had only `position`, which gives feed order. The S3-B build session chose to
  add `listed_at` to `ListedLink`, filled by the shape's parser, because that parser alone knows the
  page. For document-finder it is the 14-digit upload stamp in
  the URL path (shape 2). A document-finder URL with no stamp makes the whole listing unreadable.
  All 97 QCMR links of the July 28, 2026 recording carry one, so a link without one means the page
  changed shape. One regular expression finds the path the way RFC 3986, appendix B splits a URL,
  because the `datadesk core is pure` contract forbids all of `urllib`, and import-linter cannot
  forbid `urllib.request` alone. With the whole URL searched,
  `test_an_upload_stamp_outside_the_url_path_makes_the_feed_unreadable` fails. A shape parser
  returns `PageLink(title, url, listed_at)`, and `parse_listing` reads the title and puts the URL on
  `www.phila.gov` (QCASH-Q04), so no shape module imports the `listings` package. `ListedLink`
  refuses a link with both an edition and a skip reason, or neither. With `listed_at` left empty,
  `test_each_link_is_listed_at_its_upload_stamp_in_feed_order` and three tests of `plan_watch`
  fail. Design section 3.2.
- **Step 3: `parse_listing` returns `Listing | Finding`** (November 24, 2026, S3-B). The design
  returned a `Listing` alone, so a feed that is not JSON, a category that is missing, a shape with
  no parser yet (`phila_documents`, `manual`) and a series with no title rule had no answer but an
  exception. Each is now a BLOCK finding, `listing_unreadable` or `listing_unsupported`.
  `test_a_shape_with_no_parser_yet_is_a_finding`, `test_a_series_with_no_title_rule_is_a_finding`
  and `test_a_feed_the_parser_cannot_read_is_a_finding` show each case. The `run_watch` sketch adds
  each such finding to the run's problems and passes only a `Listing` to `plan_watch`, which reads
  `listing.links`. Design sections 3.2 and 4.1.
- **Step 3: `plan_watch`, first cut** (November 24, 2026, S3-B). The design's comment named rules
  for step 13 and no first cut. S3-B builds shape 5. The last link of each edition wins, an edition
  that ends before `first_period_end` is dropped, and a kept link is asked for unless an indexed
  version of its own edition holds its URL, with the reason `new` or `revision`. The last link is
  the one with the greatest `listed_at`. On equal stamps the link listed later wins, because the
  City appends a revised attachment after the original (QPOS-Q32). No edition has two links in the
  July recording or in the feed saved on November 23, 2026, so the tie rule is fixed and stated
  rather than shown by a page. A `not_a_quarter_end` link is a WARN finding of that code. The link
  is never fetched, so no wrong period enters the index, and the other editions are still fetched.
  `PullRequestPlan` holds `files` as `(path, text)` pairs. With the tie rule reversed,
  `test_a_tie_of_upload_stamps_goes_to_the_link_listed_later` fails. With feed order in place of
  the stamp, `test_an_earlier_stamp_listed_last_does_not_win` fails. With the floor removed, four
  tests fail. With the URL matched against every edition,
  `test_a_url_that_another_edition_holds_is_still_asked_for` fails. Design sections 3.2 and 6.3.
- **Step 3: `fiscal_quarter` takes any date** (November 24, 2026, S3-B). The design gave the quarter
  of a quarter end alone. Any date now gives the fiscal quarter it falls in, so the function has no
  failure case. The Hypothesis property
  `test_the_fiscal_quarter_turns_on_the_first_of_january_april_july_and_october` draws days from
  1900 to 2199, so a version that refuses other days fails it. Design section 3.2.
- **Step 3: `datadesk.core` imports from four more outside modules** (November 24, 2026, S3-B).
  `catalog.py` parses TOML with `tomllib`, `listings/__init__.py` hashes the listing with `hashlib`,
  the listing modules use `re`, and `periods.py` and `titles.py` hold constant maps in
  `types.MappingProxyType`. Python's `json.loads` accepts the bare tokens `NaN`, `Infinity` and
  `-Infinity`, which are not JSON, so `document_finder.py` passes a `parse_constant` that raises,
  typed `Never`, and reads any `ValueError` as `listing_unreadable`.
  `PURE_IMPORTS["datadesk.core"]` in `tests/test_purity.py` pins seven new pairs:
  `collections.abc.Callable`, `hashlib.sha256`, `re.compile`, `tomllib.TOMLDecodeError`,
  `tomllib.loads`, `types.MappingProxyType` and `typing.Never`. With the default `parse_constant`,
  `test_a_bare_nan_or_infinity_makes_the_feed_unreadable` fails. Design section 11.1.
- **Step 3: `confirm_period` reads the QCMR cover** (November 24, 2026, S3-C). The design named
  the "PERIOD ENDING" reader and gave it no rule or finding codes. `PERIOD_READERS` maps a
  series to its reader, as `TITLE_RULES` does for titles, and holds `qcmr_period` alone. A
  series with no reader is `period_unsupported`. `qcmr_period` reads every
  `PERIOD ENDING <Month> <D>, <YYYY>` phrase on page 1 (QCASH-Q05, QOBL-Q04), in any case, with
  any run of whitespace between words (QOBL-Q02), the comma optional, and the year not followed
  by another digit. It ports the shape of `_PERIOD_ENDING_RE` in the old repo's `qcmr.py`. It
  never reads the bare date that the cover also prints (plan risk 3). A cover with no phrase, or
  with a phrase it cannot read, is `period_unreadable`. Two dates are `period_ambiguous`, and a
  date that is not a quarter end is `period_not_a_quarter_end`. Any other date gives the fiscal
  quarter it ends, and `confirm_period` confirms it only when it equals the whole expected
  period, start included. The build session chose the whole period over the end date alone, so
  a wrong first day of a quarter cannot pass. With `(?!\d)` dropped from the phrase, the
  `a_year_run_on_into_another_digit` case fails. With spaces alone between its words, the
  `a_phrase_broken_across_lines` and `a_phrase_spaced_with_no_break_spaces` cases fail. With the
  words "PERIOD ENDING" made optional, the two bare date cases fail. With each fiscal quarter
  that starts in July or October moved back a year, every case that prints September 30 or
  December 31 fails, `september_opens_the_next_fiscal_year` and
  `december_is_in_the_next_fiscal_year` among them (QPOS-Q34), and the March and June cases
  pass. Without the check for two dates, the `two_phrases_with_two_dates` case fails, and
  without the quarter end check, `a_date_that_is_not_a_quarter_end` fails. Design section 3.2.
- **Step 3: a `PRINTED_PERIOD` note clears a mismatch only when it fits the cover** (November
  24, 2026, S3-C). The design said that a note is the only way past a mismatch (QOBL-Q06) and
  did not say when a note fits. A note fits when its kind is `PRINTED_PERIOD`, its page is 1 or
  none, page 1 holds its printed text, and its value is the printed end date in ISO form. Both
  texts are compared with each run of whitespace made one space, so a line break on the page
  does not hide the text (QOBL-Q02). `confirm_period` then returns the printed period, not the
  expected one (shape 8). No note clears a code that the reader returns, so a note cannot file a
  report under a date that is not a quarter end. `plan_fetch` passes only the notes whose
  `doc_sha256` is the fetched sha. With the kind, the page, the text or the value left out of
  the fit, the matching case of `test_a_note_that_does_not_fit_the_cover_leaves_the_mismatch`
  fails. With the texts compared as they are, the `a_page_that_spaces_the_text_another_way`
  case fails. With every note passed through, the second half of
  `test_plan_fetch_clears_a_mismatch_only_with_a_note_for_the_fetched_sha` fails. Design
  section 3.2.
- **Step 3: `plan_fetch` decides each fetch against one working index** (November 24, 2026,
  S3-C). The design gave `plan_fetch` the `content_alias` rule alone. It is now a fold over the
  fetched reports in input order. A working index starts as the given index and grows by
  `add_versions` after each added line, so two requests in one batch see each other, and every
  question of what is already indexed goes to that one index. The first rule that fits decides
  a fetch: a status other than 200 (`http_<status>`), a sha under another edition
  (`content_alias`, MSCH-Q01), a superseded sha, the current sha at a known URL (nothing), the
  current sha at a new URL (the URL alone, shape 7), and then a new sha. A new sha goes through
  `confirm_period`, and a `Fetched` with no page 1 text reads as an empty page, so it is
  `period_unreadable` with no branch of its own. The new version supersedes the current one,
  and a new version is stored once. A finding from `add_versions` becomes a rejection with its
  code. With the input index in place of the working one,
  `test_one_sha_fetched_for_two_editions_in_one_batch_is_a_content_alias` fails. With the alias
  check removed, both `content_alias` tests fail. With every added line stored,
  `test_the_current_sha_at_a_new_url_adds_the_url_and_stores_nothing` fails, and with a known
  URL added again, `test_plan_fetch_adds_nothing_for_an_indexed_sha` fails. With `supersedes`
  left empty, `add_versions` returns `two_current_versions` and both cases of
  `test_new_bytes_of_an_indexed_edition_supersede_its_current_version` fail. Design section 3.2.
- **Step 3: a superseded sha listed again is a rejection** (November 24, 2026, S3-C). With bytes
  A, then B, then A again at a later stamp, the design's URL merge would add the URL to A's line
  and leave B current. One line for each sha cannot say that A now supersedes B, and the later
  `listed_at` must win (shape 7). So `plan_fetch` rejects the third fetch as
  `superseded_sha_relisted`, for the owner. Without the rule,
  `test_a_superseded_sha_listed_again_is_rejected_and_the_newer_bytes_stay_current` fails.
  Design sections 3.2 and 6.3.
- **Step 3: new bytes listed before the current version are a rejection** (November 24, 2026,
  S3-C). The design said that the later `listed_at` wins and did not say what happens to new
  bytes listed earlier than the edition's current version. `index_problem` does not compare a
  version's `listed_at` with the one it supersedes, so such bytes would become current. They are
  now the rejection `listed_before_current`, for the owner (shape 2, follow-up 5 of pull request
  32). The same `listed_at` still supersedes, so new bytes behind an unchanged URL are recorded
  (design 18.1). Without the rule,
  `test_new_bytes_listed_before_the_current_version_are_rejected` fails, and with `<=` in place
  of `<`, the `new_bytes_behind_the_same_listing` case fails. Design sections 3.2 and 6.3.
- **Step 3: `FetchPlan.pull_request` holds the index file** (November 24, 2026, S3-C). The
  design said only that the pull request holds the new index lines. `fetch.py` defines
  `INDEX_PATH` (shape 3). When `index_add` is empty, `files` is empty. Otherwise it holds one
  pair, the path and the rendered index after every added line, so S3-D writes the whole file.
  The branch is `fetch/index` and the title is fixed. The body lists each added line by
  edition id, sha and URL, and each rejection by edition id, URL and reason. With the file
  written whatever was added, nine tests fail, among them
  `test_plan_fetch_adds_nothing_for_an_indexed_sha`. Design section 3.2.
- **Step 3: a `PRINTED_PERIOD` note must quote the printed period** (November 24, 2026, S3-C
  fix round). The S3-C rule let a note clear a mismatch when page 1 held its printed text. The
  empty string is on every page, so a blank note filed a December report under September (Codex
  review of S3-C, finding 1). A note now fits only when the series reader also reads its printed
  text alone as the very period page 1 prints. A blank note, or one that quotes other words on
  the cover, clears nothing. The kind, page, on-page text and value conditions stay. With the
  reader condition dropped, the `a_blank_note` and `a_note_that_quotes_other_words` cases of
  `test_a_note_that_does_not_fit_the_cover_leaves_the_mismatch` fail. The reader now also
  refuses the older `a_note_whose_text_page_1_lacks` case, so the new case
  `a_note_that_reads_as_the_period_in_words_page_1_lacks` keeps the on-page text condition
  tested, and it fails with that condition dropped. Design sections 3.2 and 6.3.
- **Step 3: a URL that joins a line brings its `listed_at`** (November 24, 2026, S3-C fix
  round). S3-A had `add_versions` add a new URL to a held line and change nothing else (shape 7).
  So when the current bytes came back in June at a new URL, the line kept its November stamp.
  Other bytes listed in March then became current with no rejection, though the later
  `listed_at` wins (shape 2, Codex review of S3-C, finding 2). When a URL joins a line,
  `add_versions` now gives the line the later of its own `listed_at` and the new version's. A
  version with no new URL still changes nothing. `plan_fetch` adds the URL with the request's
  `listed_at`, so the March bytes are `listed_before_current` and the June line stays current.
  With the held stamp kept,
  `test_older_bytes_after_a_repost_of_the_current_sha_are_listed_before_current`,
  `test_the_current_sha_at_a_new_url_adds_the_url_and_stores_nothing` and
  `test_add_versions_merges_a_new_url_into_the_line_of_the_same_sha_and_edition` fail. With the
  new stamp taken whatever its order,
  `test_the_current_sha_at_a_new_url_listed_earlier_keeps_the_later_stamp` fails. With the later
  stamp taken when no URL joins,
  `test_add_versions_adds_nothing_for_an_indexed_sha_at_an_indexed_url` fails. Design sections
  3.2 and 6.3.
- **Step 3: every `PERIOD ENDING` caption must carry a readable date** (November 24, 2026, S3-C
  fix round). The S3-C pattern matched a whole phrase with an ASCII month word. So
  `PERIOD ENDING Märch 31, 2022` never matched, and a readable phrase beside it decided the
  period, though the design called such a phrase `period_unreadable` (Codex review of S3-C,
  finding 3). The pattern also matched inside a longer word, so `SUBPERIOD ENDING SEPTEMBER 30,
  2021` read as FY2022 Q1. `qcmr_period` now finds every `PERIOD ENDING` caption, with a word
  boundary before `PERIOD` and after `ENDING`. Each caption must be followed by a readable date,
  whose month word is any run of word characters, as in the title rule. Otherwise the page is
  `period_unreadable`. With the S3-C pattern, the cases
  `a_month_word_of_other_letters_beside_a_readable_phrase`,
  `a_caption_with_no_date_beside_a_readable_phrase` and `a_longer_word_in_place_of_the_caption`
  of `test_confirm_period_returns_a_finding_for_a_cover_it_cannot_confirm` fail. The `Märch` case
  passes with either half of the change alone, the optional date or the wider month word. With
  the date required after the caption, the caption case fails. Without the boundary before
  `PERIOD`, the `SUBPERIOD` case fails, and without the one after `ENDING`, the
  `a_longer_word_after_period_is_not_a_caption` case fails. Page 1 of the owner's 21 saved City
  reports, read with `pdftotext -f 1 -l 1 -layout`, gives the same result before and after the
  change. The 20 reports from FY2022 Q1 to FY2026 Q4 read as their own quarters, and FY2027 Q1
  is `period_unreadable`. Design section 3.2.
- **Step 3: a note's quote must stand on page 1 as whole words** (November 24, 2026, S3-C
  second fix round). The S3-C fix round let a note clear a mismatch when page 1 held its
  printed text anywhere and the series reader read that text alone as the printed period. Read
  alone, a quote cut from inside a longer word begins at a word boundary the page lacks. So a
  December cover with `SUBPERIOD ENDING DECEMBER 31 2021` added, and a note that quotes the
  text after `SUB`, was filed under September (Codex read of the S3-C fix round, finding 1).
  The quote must now occur on page 1 with no word character right before it and none right
  after it. `PURE_IMPORTS["datadesk.core"]` in `tests/test_purity.py` pins the new pair
  `re.escape`. With the plain substring test back, both cases of
  `test_a_note_quoted_from_inside_a_longer_word_leaves_the_mismatch` fail, and each case fails
  with its own half of the boundary dropped. The `PERIOD ENDING` caption of each of the 20
  readable saved City covers, quoted as printed, still meets the rule. Design section 3.2.
- **Step 3: `listed_at` is the latest stamp at which one of its URLs joined the line**
  (November 24, 2026, S3-C second fix round). The S3-C fix round called the field "the latest
  of the stamps its urls were listed at", and said that `add_versions` changes nothing for a
  version with no new URL. Both cannot hold when one URL is listed on two dates under a
  `<listing date>#<position>` stamp (Codex read of the S3-C fix round, finding 2). The field
  now has the meaning the code already had: the latest of the stamps at which each of its URLs
  joined the line. A URL the line already holds, listed again at a later stamp, changes
  nothing. So new bytes listed in March still supersede a November line whose URL was listed
  again in June. On the document-finder feed the stamp is in the URL, so a later listing is
  always a new URL. No code changed.
  `test_add_versions_adds_nothing_for_an_indexed_sha_at_an_indexed_url` pins the meaning, and
  fails when the line takes the later stamp with no URL joining. Design sections 2.2 and 3.2.
- **Step 3: a URL joins a line only when the line lacks it** (November 24, 2026, S3-C second
  fix round). The S3-C fix round had `add_versions` decide that a URL joined when the merged
  URLs differed from the held ones. Dropping a URL the held line repeats also makes them
  differ, so a version at a URL the line already held gave the line its later `listed_at`
  (Codex read of the S3-C fix round, finding 3). A URL now joins only when the held line lacks
  it, and a version with no such URL leaves the line exactly as it was, its URLs and
  `listed_at` included. With the tuple comparison back,
  `test_add_versions_leaves_a_line_that_repeats_a_url_as_it_was_when_no_url_joins` fails.
  Design section 3.2.
- **Step 3: section 6.3 says a joined line holds each URL once** (November 24, 2026, S3-C
  third fix round). Section 3.2 says that when a URL joins, the line holds each URL once. The
  section 6.3 row for the same bytes at a new URL said the URL joins after the ones the line
  holds and that nothing else changes, which is false for a line that repeats a URL: `(A, A)`
  with `B` joining gives `(A, B)` (Codex read of the S3-C second fix round, finding 1). The row
  now agrees with 3.2: the line holds each URL once, the held ones first, and takes the later
  `listed_at`. No code changed.
  `test_add_versions_holds_each_url_once_when_a_url_joins_a_line_that_repeats_one` pins the
  rule, and fails when the merge keeps the held tuple as it is and appends the new URLs.
  Design section 6.3.
- **Step 3: the ports as step 3 builds them** (November 24, 2026, S3-D). The design's
  `ObjectStore.put` took `public`, and R2 has no setting that makes one object public (plan fact
  7). So `put(key, data, condition)` takes no flag, each store is bound to one bucket, and `Deps`
  holds `http`, a `store` bound to the archive bucket, and `pdf` (shape 9). `ObjectStore` has
  `put`, `head` and `get` at step 3, and `PdfReader` has `page1_text` alone (shape 11).
  `HttpResponse` holds `status` and `body`, and `text` decodes the body as UTF-8. A new
  `EffectError` marks a failed effect that may be tried again. Each adapter raises it from its
  library's failure, and `PreconditionFailed` is not one. With `PreconditionFailed` made a
  subclass of `EffectError`, `test_other_bytes_under_a_report_s_key_stop_the_command_after_one_put`
  fails, because the put is tried three times. The sketches in sections 4.3 and 4.5 no longer pass
  `public`. The 4.5 sketch publishes through `deps.public`, a store bound to a public bucket, which
  is a proposal for the step that builds the release. Design sections 4, 4.3 and 4.5.
- **Step 3: `Settings` and the S3 client** (November 24, 2026, S3-D). The design named `Settings`
  and gave it no fields. It holds the endpoint, the two keys and the archive bucket from the four
  `DATADESK_R2_*` variables of the plan, and leaves both keys out of its `repr`. An empty variable
  counts as missing. With explicit keys alone, a boto3 1.44.5 client raised `ProfileNotFound` under
  an `AWS_PROFILE` that names no profile. So `s3_store` builds its client on a botocore session
  whose `profile` reads no variable and whose config and credentials files are `os.devnull`. The
  client also makes one attempt for each call, so the executor's three tries are all the tries. With
  a default session, `test_s3_client_ignores_the_ambient_aws_profile` fails with
  `ProfileNotFound`. With the keys in the `repr`,
  `test_settings_keep_both_keys_out_of_their_repr` fails. Design section 4.
- **Step 3: contract suites that run on every commit** (November 24, 2026, S3-D). Section 11.1
  ran the real adapters' contracts nightly and before release, against the network or MinIO. The
  saved-folder `Http` adapter and the pdfplumber reader need neither, so their contracts run in CI
  beside the fakes (plan, S3-D). The `ObjectStore` suite runs the dict store always and the S3
  store only when the four `DATADESK_CONTRACT_S3_*` variables are set. The `PdfReader` contract builds its two PDFs in the
  test, because `.gitignore` keeps every PDF out of git. With page 1 read as the last page,
  `test_page1_text_holds_the_words_of_page_1_alone` fails. Bytes that pdfplumber cannot open and a
  PDF with no page raise `EffectError`, so the command stops with one line and not a traceback.
  With that conversion removed, both cases of
  `test_page1_text_of_a_file_pdfplumber_cannot_read_is_an_effect_error` fail. Design sections 4,
  11.1 and 11.5.
- **Step 3: `run_fetch` returns the plan and tries each effect three times** (November 24, 2026,
  S3-D). The design's sketch called `GitHost`, put each report with `public=True`, and did not say
  how a failed effect is tried again. `run_fetch` now returns the `FetchPlan` and calls no `GitHost`
  (shape 10). Each `http.get` and each `put_immutable` is tried three times in all while it raises
  `EffectError`, and the third failure propagates. `put_immutable` writes with `CreateOnly` and, on
  `PreconditionFailed`, hashes the stored object, so a put whose reply was lost completes on the
  next try. With two tries, the `2-listing` case of
  `test_three_failures_stop_the_command_with_the_index_unchanged` fails, and with four, the
  `3-listing` case fails. With a failed put skipped, the `3-put` case fails. With the read-back
  removed, `test_put_immutable_completes_when_the_store_holds_the_same_bytes` fails. Design
  sections 1.4, 4.2, 4.5 and 9.
- **Step 3: the fetch command reads a saved folder and writes the index last** (November 24, 2026,
  S3-D). The design gave the fetch command no shape, and its `Http` adapter sent requests. The City
  refuses a client that is not a browser (plan facts 6 and 11), so at step 3 `datadesk fetch
  <source> --saved <folder>` reads a folder that a browser saved, through `SavedHttp` (shape 6).
  `fetch_command` returns `FetchRun(listing_sha256, findings, plan)`, raises `FetchStopped` before
  any report is fetched when the checkout or the listing cannot be read, and writes the plan's files
  after every put, each to a temporary file in its folder and then renamed. A command that returns
  before it asks for the listing when the index holds lines fails
  `test_fetching_the_same_listing_again_adds_nothing` on the call log of the second run. One that
  fetches nothing when the index holds lines fails it at the third run, which must store the new
  edition. With the listing's status left unchecked,
  `test_a_saved_folder_without_the_feed_s_row_stops_the_command_before_any_put` fails. With the
  bare-name check on a saved row dropped, the `a_file_outside_the_folder` case of
  `test_saved_http_refuses_a_folder_it_cannot_trust` fails. Design sections 1.4, 4.2, 12.3 and
  12.4.
- **Step 3: an index file that `parse_index` cannot read is a finding** (November 24, 2026, S3-D).
  Section 9 lets the shell catch only effect exceptions, and `parse_index` raises `KeyError`,
  `TypeError` or `ValueError` on a file it cannot read. The index file is input from the checkout,
  so `gather_repo` returns that as the BLOCK finding `index_unreadable`, beside any catalog
  findings, and the command stops before any request. `RepoSnapshot` holds the loaded catalog and
  index, not text. With only `OSError` caught, the `an_index_that_is_not_json` case of
  `test_a_checkout_the_command_cannot_read_stops_it_before_any_request` fails. Design sections 1.4,
  4 and 9.
