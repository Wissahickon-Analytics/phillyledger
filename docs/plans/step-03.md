# Build step 3 plan

Build step 3 of `docs/design.md` section 15 builds the archive for the QCMR from FY2022. It
puts each whole report in the archive bucket under its sha256, and it lists each one in an index
that a person has checked against the PDFs. It publishes nothing. The work is for the owner, who
checks the inventory and lands each pull request, and for steps 4 to 6, which read reports from
the archive by sha. Five pull requests stack in the order S3-A, S3-B, S3-C, S3-D, S3-E.

The step's check: "each of the 20 reports is indexed once, by the sha in an inventory checked by
hand. Fetching the same listing again adds nothing."

## Track

Full track. The owner chose it on November 23, 2026, with the words "Full track". He had been
shown this recommendation: full track, because `confirm_period` decides the period a report is
filed under, and a wrong period is a wrong published fact.

## What the owner said and what a look found

All of this is from November 23, 2026.

The owner answered two questions. The folder that holds his whole QCMR reports is
`~/Software/phl-budget-data2/data/qcmr`. Asked whether he holds all 20, he picked "Some, fetch
the rest", an option that read: "I hold some. The rest should be downloaded from the City's
Finance document-finder feed by the new fetch code, then checked by hand like the others."

A look at the folder, the old repo and the City's site found these facts. Each was measured by
the command or the page named.

1. The folder holds 73 PDFs, `FY07_Q1.pdf` to `FY25_Q2.pdf`. Fourteen are in the step's range,
   FY2022 Q1 to FY2025 Q2. Six are not held there: FY2025 Q3, FY2025 Q4 and FY2026 Q1 to Q4.
2. `../gov-budget-data` holds whole copies of five of those six, under
   `artifacts/source_cache/phila/qcmr/` and `artifacts/source_audits/2026-09-11/`. FY2025 Q4 is
   in neither place.
3. Page 1 of all 19 copies prints `FOR THE PERIOD ENDING <MONTH> <D>, <YYYY>` with the quarter
   end that the table below gives (`pdftotext -f 1 -l 1 -layout`).
4. The City's feed, `https://api.phila.gov/phila/document-finder/v1/151831`, read in a browser,
   has a category titled "Quarterly City Managers Report" with 99 documents, back to December
   31, 2006. From September 30, 2021 on it lists 34 documents: 21 reports, one for each quarter,
   and 13 infographics. The 21st report is FY2027 Q1, with the title date September 30, 2026,
   uploaded November 16, 2026.
5. A report's title is "Quarterly City Managers Report - <Month> <D>, <YYYY>". Four of the 21
   print "Manager's". Every URL is on `admin.phila.gov` and carries a 14-digit upload stamp in
   its path. Five URLs show a second upload: FY2022 Q3 and Q4 end in `-1.pdf`, FY2023 Q1 has a
   stamp of February 15, 2023, FY2026 Q2 ends in `-3.pdf`, and FY2026 Q3 is
   `...March-30-2026R.pdf` under a title and a cover that say March 31.
6. The City's CDN refuses `curl`. The feed and a report URL on `www.phila.gov` both returned
   HTTP 403, "Request blocked", from CloudFront, with curl's own User-Agent and with `-A curl`.
   The browser got the feed. The old repo sends a browser User-Agent
   (`publisher_http.py:199`).
7. Cloudflare's page "S3 API compatibility" marks `If-Match` and `If-None-Match` as supported on
   PutObject, and `x-amz-acl` as not supported. So R2 has conditional writes and no setting that
   makes one object public.
8. `gh extension list` shows no `stack` extension. `docker` is installed and `minio` is not.
9. The design gives no fields for `SourceCatalog`, `SourceEntry`, `PullRequestPlan`,
   `HttpResponse` or `Deps`, no path for the index file, and no environment variable name.
10. Cloudflare's R2 pages, read after the owner's answer 3. "Authentication" says "You must
    purchase R2 before you can generate an API token", and a token with the permission "Object
    Read & Write" can be scoped to named buckets. "Pricing" gives a free allowance each month
    of 10 GB of Standard storage, 1 million Class A operations and 10 million Class B
    operations, and charges nothing for egress. "Create new buckets" says a bucket is not
    public until its owner makes it so. "aws CLI" runs the `aws` CLI against R2 with
    `--endpoint-url https://<account id>.r2.cloudflarestorage.com` and the region `auto`. The
    owner's machine has `aws` and no `wrangler`. `uv run` takes `--env-file` (uv 0.13.6), and
    `.gitignore` lists `.env`.
11. The City's server refused a plain User-Agent. After the owner's answer 1, `curl` asked for
    the feed twice, as `datadesk/0.1` and as
    `datadesk/0.1 (+https://github.com/Wissahickon-Analytics/phillyledger)`. Both got HTTP 403
    from `awselb/2.0` behind CloudFront. The old repo sends a `User-Agent` header and no other,
    with a browser's string (`publisher_http.py:199`). No request with a browser's string was
    run here.

The copies seen, by edition. This is not the inventory. No one has checked it by hand, and the
City's file for an edition may differ from the copy.

| Edition | Cover period end | Upload stamp in the feed URL | Copy seen | Pages | sha256 of the copy |
|---|---|---|---|---:|---|
| FY2022 Q1 | 2021-09-30 | 20211116102946 | `FY22_Q1.pdf` | 78 | `43a5c394f45fa07a56db8562ebc54a72e86a98e08879b73855935dc1c30d355d` |
| FY2022 Q2 | 2021-12-31 | 20220217152839 | `FY22_Q2.pdf` | 78 | `9932767086dcf5bb62414486de4402e3a26ab9d5cea15419916862a33668f9ef` |
| FY2022 Q3 | 2022-03-31 | 20220517124525 | `FY22_Q3.pdf` | 79 | `a9c9b86474e01f4ec1fa0ff6afd4dd46b30195daeb80e76de6e52a0c69eb3e86` |
| FY2022 Q4 | 2022-06-30 | 20220818093154 | `FY22_Q4.pdf` | 79 | `5c22a51c9393231cd68a0718750e93d74f8f70de7705459644540598c4bfadbd` |
| FY2023 Q1 | 2022-09-30 | 20230215183912 | `FY23_Q1.pdf` | 78 | `5f238d57700f393ae6d9b795c139b33db64a74609e62a524cb83befdabd85b82` |
| FY2023 Q2 | 2022-12-31 | 20230215125210 | `FY23_Q2.pdf` | 77 | `deaad9ea651a153e460c7be9633ac06798059879733d2c17fcf1c7bfcbcf9dee` |
| FY2023 Q3 | 2023-03-31 | 20230515170230 | `FY23_Q3.pdf` | 74 | `f75a6cf21dbe130a7d1328851ba0496262ac06c3f2a82d127f50431efb54b1d5` |
| FY2023 Q4 | 2023-06-30 | 20230815135251 | `FY23_Q4.pdf` | 73 | `fdcc6829b3d840474deb8c3e708a67d959d6777f015df2eb8d0de7ea2d0cb5bb` |
| FY2024 Q1 | 2023-09-30 | 20231115154830 | `FY24_Q1.pdf` | 74 | `e18d426d4dac41ba1959903b462cc866e7ffa5927a72aefece8ec07ae161c66b` |
| FY2024 Q2 | 2023-12-31 | 20240215211406 | `FY24_Q2.pdf` | 74 | `dad6ccbb5497e994c334e99f70ccc096f71b98a9fd990c3c8fefd4db279cc968` |
| FY2024 Q3 | 2024-03-31 | 20240515173722 | `FY24_Q3.pdf` | 74 | `c16aaea90ea9c7d3775d00d49d081092061cd5aaebfd158e7c4c9e351792b574` |
| FY2024 Q4 | 2024-06-30 | 20240815160044 | `FY24_Q4.pdf` | 74 | `a772dd93bcaaecdc8d8b6718455069a05d2aa366555a4f5f4d31db63a3c8824b` |
| FY2025 Q1 | 2024-09-30 | 20241115161234 | `FY25_Q1.pdf` | 98 | `53fa613ade39a4ed13842c6c73280bf9e102c0b14e5c9b363813b6d89a5502fb` |
| FY2025 Q2 | 2024-12-31 | 20250218155042 | `FY25_Q2.pdf` | 96 | `36ef9e8a539ed6c10249eb6b06a2abb631f1632d96cb952f49516877eb3e46f9` |
| FY2025 Q3 | 2025-03-31 | 20250515134742 | old repo, `source_cache` | 90 | `0e6895f1cc3fa8476761cf71decc930a473f7be48662b11fdfa8663f94eeb63f` |
| FY2025 Q4 | 2025-06-30 | 20250815155820 | none | | |
| FY2026 Q1 | 2025-09-30 | 20251117160106 | old repo, `source_cache` | 92 | `377c9305e6ac182da830aaeaf0e7892c53b79e94c05ecc85b61103157f152747` |
| FY2026 Q2 | 2025-12-31 | 20260224123226 | old repo, `source_cache` | 95 | `f7b627e958ffa22c63d0af8b5584c4b3bf2266907156891fd84614186f083aae` |
| FY2026 Q3 | 2026-03-31 | 20260515154446 | old repo, `source_cache` | 94 | `032c5cfddfb77c50b270d5f0954d73674b5ec1c92c5d3fdee4b60e53efd82827` |
| FY2026 Q4 | 2026-06-30 | 20260817162758 | old repo, `source_audits` | 92 | `48fd9aa936df05a28bb7f37083720afac85d1ee2a2c9a70be832382f0dc55020` |

## Clauses

| # | Clause of the check | Owner | Test that proves it |
|---|---|---|---|
| C1 | Each of the 20 reports, FY2022 Q1 to FY2026 Q4, is indexed | S3-E | `test_each_of_the_20_editions_has_a_row_and_a_current_version` in `tests/test_archive_inventory.py` |
| C2 | Each is indexed once | S3-E | `test_each_inventory_sha_is_indexed_once`, same file |
| C3 | Each is indexed by the sha in the inventory | S3-E | `test_each_edition_is_indexed_under_its_inventory_sha`, same file |
| C4 | The inventory is checked by hand | S3-E | `test_every_inventory_row_is_checked`, same file, and the owner's words in the pull request |
| C5 | Fetching the same listing again adds nothing | S3-D | `test_fetching_the_same_listing_again_adds_nothing` in `packages/datadesk/tests/shell/test_fetch_command.py` |

The tests of C1 to C3 read the index file and the inventory file from the checkout. The test
file holds the 20 edition ids as its own list, built from the 20 quarter ends, September 30,
2021 to June 30, 2026. So a quarter that is missing from both files fails C1. C3 compares
pairs: the sha of an inventory row must be the sha of the index's current version of that
row's edition. C2 requires each inventory sha on exactly one index line. S3-E shows two changes
failing, each in its pull request: the shas of FY2022 Q1 and Q2 swapped in the index, and one
quarter removed from both files. Both files also hold FY2027 Q1 (answer 2). C2 to C4 cover its
row, and C1's list stays the 20.

The index comes from `datadesk`. The inventory's `sha256` comes from a `curl` download and
`shasum` (see "The inventory"), so the two sides share no code. C4's test fails while any row
has an empty `checked` cell, and only the owner's word fills a cell.

C5's test drives the function behind `datadesk fetch qcmr` twice, so it covers the listing
read, `run_fetch` and the index write. It uses a temporary checkout, a fake `Http` that replays
the recorded feed and one body for each report URL, a fake `PdfReader`, and the dict store.
After the first run it asserts the store's keys, the bytes under each key, and the edition and
sha of each index line. It then loads the checkout again and runs the command a second time.
The store saw no new `put`, the index file is byte for byte the same, and the plan holds no
file to write. S3-C adds the pure half, `test_plan_fetch_adds_nothing_for_an_indexed_sha`.
S3-E records two real runs against the City's site and R2 in its pull request, and each run
prints the listing's `html_sha256`.

## Shapes the design leaves open

The Build sessions skip `how` and `architect`, so this plan names what the design does not. The
pull request that builds a shape records it in `docs/design.md` and in
`docs/deviations/step-03.md` (hard rule 7).

1. **A QCMR edition's period is its fiscal quarter.** `Period(first day of the quarter, the
   printed end date)`, so FY2026 Q4 is April 1 to June 30, 2026, and its id is
   `qcmr:2026-06-30:none`. Editions then never overlap.
2. **`listed_at` and the order of versions.** For a document-finder link `listed_at` is the
   14-digit upload stamp in the URL path. For a held copy it is the empty string.
   `current(edition)` is the edition's version that no other version supersedes. A new version
   supersedes the current one when its `listed_at` is later or the same, so step 13 can record
   new bytes behind an unchanged URL (design 18.1). A new version with an earlier `listed_at`
   is a rejection for the owner, so a held copy never supersedes a listed version.
   `add_versions` returns a finding when an edition would have two versions that nothing
   supersedes.
3. **The index file** is `packages/datadesk/src/datadesk/data/index.jsonl`, one
   `DocumentVersion` on each line. S3-D commits it empty, and `parse_index("")` is the empty
   index, so the first command runs on a fresh checkout.
4. **`SourceEntry`** has `id`, `series`, `shape`, `listing_url`, `category` and
   `first_period_end`. `shape` is a `ListingShape`, a `StrEnum` of `document_finder`,
   `phila_documents` and `manual`. `SourceCatalog` holds the entries and `entry(id)`.
   `load_catalog(text)` returns a `SourceCatalog` or findings. Lag, recheck interval,
   `missing_ok`, slug exceptions and `DatasetSpec` wait for the steps that need them.
5. **`plan_watch`, first cut.** It keeps the design's signature. `parse_listing` keeps the links
   of the entry's category alone. `plan_watch` takes the last listed link of each edition
   (design line 2035), drops an edition whose period ends before `first_period_end`, and makes
   one `FetchRequest` for each link whose URL no indexed version holds. The reason is `new`
   when the edition has no version and `revision` when it has one. A link whose title reads as
   a report and whose date is not a quarter end gets the skip reason `not_a_quarter_end`, and
   `plan_watch` returns a finding for it in `WatchPlan.findings`. `wayback` and `gaps` stay
   empty until step 13. `PullRequestPlan(files, branch, title, body)` lives in `core/watch.py`.
6. **The City's file first, the held copy second.** `datadesk fetch qcmr` downloads the last
   listed report of every edition from FY2022 Q1 on, because five URLs show a second upload and
   the City's last listed file is the current version of its edition (design 6.3).
   `datadesk import-held` then reads the inventory. For each row with a `held_file` it reads
   that one file, checks its sha against the row's `held_sha256`, and builds a
   `Held(edition, name, sha256, size, page1_text)`. It opens no other file in the folder, so
   the 59 older reports there wait for step 7. `plan_import(held, index, notes)` in
   `core/fetch.py` sends each `Held` through `confirm_period` and the index rules of
   `plan_fetch`. A held sha that is already indexed under its edition adds nothing. A held file
   for an edition with no version is indexed with `Via.MANUAL` and `urls=()`. A held sha that
   differs from its edition's listed version is a `Rejection` with the reason
   `differs_from_listed`, and the owner decides it. A `Rejection` names the `FetchRequest` or
   the `Held` it refuses.
7. **A version gains a URL.** When a fetched sha is already indexed under its edition and the
   request's URL is new, `plan_fetch` stores nothing and `index_add` carries the version with
   that URL. `add_versions` merges it into the one line, so `urls` holds every URL that served
   the bytes (design line 1102) and the next `plan_watch` asks for nothing. A held version that
   a listing later serves takes the listing's `listed_at` and title, and `Via.PUBLISHER`.
8. **`confirm_period` returns the period the page prints.** It is the expected period, or the
   period a `PRINTED_PERIOD` note names for a text that page 1 holds. Anything else is a
   finding: no phrase, a date that is not a quarter end, or another quarter with no note.
   `plan_fetch` and `plan_import` pass it only the notes whose `doc_sha256` is the sha at hand.
   The two commands pass no notes at step 3. `load_records` arrives at step 5 and the first
   real note at step 7 (QCASH-Q07), so unit tests alone prove the note path here. A cover among
   the 20 that fails stops S3-E for the owner.
9. **One store for each bucket.** R2 cannot make one object public (fact 7), so
   `ObjectStore.put` loses `public` and becomes `put(key, data, condition)`. `Deps` holds a
   store bound to the archive bucket. A later step adds a store for each bucket it needs. The
   sketch of `run_fetch` at design line 2381 also omits `condition`. A report is stored through
   `put_immutable(store, key, data, sha)`, the helper of design 4.5 less its `public`
   parameter. It writes with `CreateOnly`. On `PreconditionFailed` it reads the object and
   hashes it. The same bytes complete the put. Other bytes raise, and the command stops before
   it writes the index.
10. **`run_fetch` returns the `FetchPlan` and calls no `GitHost`.** It tries a failed `get` or
    `put` up to three times and then stops (design section 9). The CLI writes the plan's files
    into the checkout last, after every `put`, and prints the title and the body. The session
    opens the pull request. Step 13 builds the `GitHost` port and its adapter.
11. **`PdfReader` has `page1_text` alone** at step 3. Step 4 adds `words` and `render`.

## Pull requests

One GitHub stack, bottom first. Each pull request also touches `docs/design.md`,
`docs/deviations/step-03.md` and `docs/progress.md` for what it builds, and `tests/test_purity.py`
for the outside names its core modules import. Paths below drop `packages/datadesk/`.

### S3-A, `step-03/a-index`: the index format

Builds on `main`. `feat(datadesk): add the archive index`.

- Files: `src/datadesk/core/domain.py`, `src/datadesk/core/index.py`,
  `tests/core/test_domain.py`, `tests/core/test_index.py`.
- Proves: `render_index(parse_index(text)) == text` for a sorted text, and
  `parse_index(render_index(index)) == index` as a Hypothesis property. `parse_index("")` is the
  empty index. `ArchiveIndex` refuses one sha twice. `add_versions` merges a new URL into the
  line of the same sha and edition. It returns a finding for a sha under another edition, and
  for an edition left with two versions that nothing supersedes. A version with the same
  `listed_at` as the one it supersedes round-trips. `current` gives the version that nothing
  supersedes.

### S3-B, `step-03/b-listing`: the QCMR catalog entry and its listing

Builds on S3-A. `feat(datadesk): read the QCMR listing`.

- Files: `src/datadesk/core/catalog.py`, `src/datadesk/core/periods.py`,
  `src/datadesk/core/listings/__init__.py`, `src/datadesk/core/listings/document_finder.py`,
  `src/datadesk/core/listings/titles.py`, `src/datadesk/core/watch.py`,
  `src/datadesk/data/catalog.toml`, `tests/core/` tests for each module,
  `tests/core/fixtures/qcmr_feed.py`, and `tests/test_catalog_data.py` at the root, which loads
  the real `catalog.toml`.
- `periods.py` gets `MONTHS`, `fiscal_year_of` and `fiscal_quarter`. `fiscal_period` needs
  `Window` and waits for step 5. `match_month` waits for step 9.
- The fixture keeps the QCMR category from September 30, 2021 on and one other category whole.
- Proves, on the recorded feed: 21 report links get editions and 13 infographics get the skip
  reason `infographic`. A link of the other category is never listed. "Manager's" and
  "Managers" read the same. The host `admin.phila.gov` becomes `www.phila.gov` (QCASH-Q04). The
  edition comes from the title and never from the URL, so `...March-30-2026R.pdf` under its
  March 31 title is FY2026 Q3. `plan_watch` asks for 21 fetches on an empty index and none
  when the index holds every URL.
- Proves, on changed copies of the feed: with a second attachment appended for one quarter,
  `plan_watch` asks for the last one alone, a test ported from the old `test_qcmr.py:165`. A
  report title dated March 30, 2026 gives a finding and no fetch.

### S3-C, `step-03/c-fetch-plan`: `confirm_period` and `plan_fetch`

Builds on S3-B. `feat(datadesk): confirm the printed period and plan a fetch`.

- Files: `src/datadesk/core/fetch.py`, `src/datadesk/core/records.py` with `NoteKind` and
  `EditionNote` alone, `tests/core/test_fetch.py`, and
  `packages/checkedtables/tests/test_library_shape.py`, where `test_closed_lists_are_pinned`
  starts with the `NoteKind` pin (hard rule 6, design 11.4).
- Proves, for `confirm_period`: the printed quarter end passes. Another quarter is a finding
  (QOBL-Q06). A mismatch passes only with a `PRINTED_PERIOD` note whose text page 1 holds
  (QCASH-Q07), and a note for another sha does not clear it. A cover with no phrase is a
  finding. September and December ends belong to the next fiscal year (QPOS-Q34).
- Proves, for `plan_fetch`: a confirmed report gets one `StoreObject` at
  `pdf/<sha[:2]>/<sha>.pdf` and one index line. A sha indexed under another edition is a
  `content_alias` rejection (MSCH-Q01). A status other than 200 is a rejection. A later listing
  of an edition supersedes the earlier version (QPOS-Q32), and so do new bytes with the same
  `listed_at`. An indexed sha at an indexed URL adds nothing. An indexed sha at a new URL adds
  the URL and stores nothing.
- Proves, for `plan_import`: a held file for an edition with no version is indexed with
  `Via.MANUAL` and no URL. One that equals the listed version adds nothing. One that differs
  from it is a `differs_from_listed` rejection.

### S3-D, `step-03/d-shell`: the S3 adapter and the two commands

Builds on S3-C. `feat(datadesk): store reports in R2 and run fetch`.

- Files: `src/datadesk/shell/ports.py`, `settings.py`, `gather.py`, `run_fetch.py`, `cli.py`,
  `src/datadesk/shell/adapters/__init__.py`, `s3.py`, `http_httpx.py`, `pdf_pdfplumber.py`,
  `src/datadesk/data/index.jsonl`, empty, `tests/shell/` with the fakes, the contract suites
  and the tests below, `packages/datadesk/pyproject.toml` for `boto3`, `httpx`, `pdfplumber`
  and the `datadesk` script, `uv.lock`, the root `conftest.py` for `import ssl`
  (`docs/progress.md`), and `CLAUDE.md` for the two new commands.
- Proves: C5. The `ObjectStore` contract suite covers a create on an absent key, a replacement
  with the current etag, a stale etag refused with the bytes kept, `CreateOnly` on a key that
  exists, and `IfMatch(None)` on an absent key and on one that exists. `put_immutable`
  completes when the store already holds the same bytes and raises when it holds others, each
  with the dict store loaded first. A failed `get` or `put` that then succeeds stores once.
  Three failures stop the command with the index file untouched.
- Proves: `load_settings` names a missing variable and prints no value.
  `test_s3_client_ignores_the_ambient_aws_profile` builds the adapter's client under an
  `AWS_PROFILE` that does not exist and under shared files that hold other keys. `import-held`
  never opens an older file in the folder, indexes a held report that the fetch did not
  bring, and stops when a held file's sha is not the one its inventory row gives.
- Proves: the `page1_text` contract on two PDFs the test builds, a text page and an image
  page. The `Http` contract passes on the fake.
- The suites run on the fakes in CI. Design 11.1 runs the real halves nightly and before a
  release, so CI skips them and reports the skip. The owner of S3-D runs the `ObjectStore`
  suite against MinIO in Docker and the `Http` suite against a local server that the test
  starts, and records both runs in the pull request. No session sends the City a request in
  S3-D (fact 11).

### S3-E, `step-03/e-archive`: the 20 reports

Builds on S3-D. `feat(datadesk): index the QCMR reports from FY2022`. It adds data and no code
under `src/`.

- Files: `src/datadesk/data/index.jsonl`, `docs/evidence/inventory/qcmr.tsv`,
  `tests/test_archive_inventory.py`, `docs/plan-notes.md`, `CLAUDE.md`.
- Runs, each recorded in the pull request with its command and output: `datadesk fetch qcmr`,
  `datadesk import-held`, and `datadesk fetch qcmr` a second time. The owner starts the two
  fetch runs in his terminal, and the session reads their output (answer A). The session runs
  `import-held`, which reaches R2 and no server of the City. With the owner's go (open
  question B), the `ObjectStore` suite also runs against a scratch bucket on R2.
- S3-E starts only after the owner has set up R2 ("Setting up R2"). S3-A to S3-D do not wait
  on it.
- Owns C1 to C4. `docs/plan-notes.md` gets two notes. For step 7: the feed lists QCMR reports
  back to December 31, 2006. For step 13: the City refuses a client that does not send a
  browser's User-Agent (fact 11), which `watch` must answer before it runs on a schedule.
  `CLAUDE.md` gets the folder of the held reports in place of "ask for the path when step 3
  starts".

## The inventory

`docs/evidence/inventory/qcmr.tsv` has one row for each expected edition, with the columns
`edition`, `sha256`, `bytes`, `pages`, `page1_period`, `url`, `held_file`, `held_sha256` and
`checked`.

How it is made, in S3-E:

1. Before any command runs, the session writes one row for each of the 20 editions, and one
   for FY2027 Q1 (answer 2), with `edition` alone. A shell loop over the 14 in-range
   files of the owner's folder fills `held_file` and `held_sha256` with `shasum -a 256`. The
   session checks those shas against the table above.
2. `datadesk fetch qcmr` runs, then `datadesk import-held`, which reads the rows of step 1.
3. For each row the owner saves the City's file in his browser, from the URL the index gives,
   into a scratch folder. The City refuses `curl` (facts 6 and 11), so the session cannot make
   this download. `sha256` is `shasum -a 256` of the saved file, `bytes` its size, `pages`
   comes from `pdfinfo`, and `page1_period` is the `PERIOD ENDING` phrase from
   `pdftotext -f 1 -l 1`. This download shares no code with `datadesk`. For a report that
   reached the archive from the held folder, the source is the held file.
4. For each row the session compares that source digest, the digest of the object read back
   from the archive bucket, the object's key and the index line. The read-back is
   `aws s3 cp` under the owner's `r2` profile ("Setting up R2"), piped to `shasum`. Where the
   table above has a copy, its sha is a fifth witness. Any difference goes to the owner before
   he checks a row.

The pull request prints each loop, so anyone can run it again.

How it is checked: the owner opens each PDF from the scratch folder. He confirms that the cover
names the row's period, that the file is the whole report with the row's page count, and that
his own `shasum -a 256` of the file prints the row's sha. He says so in the session. The session
then writes the date in `checked` for the rows he named, and quotes his words in the pull
request. No agent fills `checked` on its own reading.

The owner confirmed this form on November 23, 2026 (answer 4). Two details came after his
answer, and he has not seen them: the download of step 3 is by his browser, where the form he
confirmed used `curl`, and the read-back of step 4 uses his `r2` profile.

## Setting up R2

The owner has no R2 bucket (answer 3). He sets it up himself, because it takes his Cloudflare
sign-in, a purchase and a credential. S3-A to S3-D need neither R2 nor the City's site. They
run on the fakes, MinIO and a recorded feed. S3-E starts after these steps are done.

The steps are in the Cloudflare dashboard, under R2 object storage (fact 10).

1. Turn R2 on. Cloudflare calls this a purchase. This plan has not seen that page, so it does
   not know whether the page asks for a payment card. Step 3 stores about 50 MB and makes a
   few hundred requests, inside the free allowance of 10 GB and 1 million Class A operations a
   month.
2. Create a bucket with the default location and Standard storage. The proposed name is
   `phillyledger-archive`. Infrequent Access storage is outside the free allowance. Public
   access stays off.
3. Create an API token with the permission "Object Read & Write", scoped to that bucket. The
   page shows the Access Key ID and the Secret Access Key once.
4. Write `.env` at the top of the checkout, with one `NAME=value` line for each of the five
   variables below. `.gitignore` lists the file. Each command runs as
   `uv run --env-file .env datadesk ...`, so no session reads or prints the file.
5. Run `aws configure --profile r2` with the two key values and the region `auto`. This is the
   `aws` CLI the owner knows, and no `wrangler` is needed. An empty listing with no error
   shows that the token works:

   ```bash
   aws s3 ls s3://phillyledger-archive --profile r2 \
     --endpoint-url https://<account id>.r2.cloudflarestorage.com
   ```

The bucket stays private at step 3, so this plan drops the public address it first asked for.
Making the bucket public is a publishing decision, and it waits for the step that first needs
a public read. The bucket's name, the private bucket, the `.env` file and the `r2` profile are
proposals that the owner has not seen.

## Environment variables

`load_settings(environ)` reads these five and nothing else. The S3 adapter gives its client the
endpoint and the two keys from `Settings`. That alone does not shut out an AWS profile. A boto3
1.43.26 client built with explicit keys raised `ProfileNotFound` under `AWS_PROFILE` set to a
missing profile (run on November 23, 2026). S3-D builds the client so that a profile or a
credentials file changes nothing, and `test_s3_client_ignores_the_ambient_aws_profile` proves
it.

| Variable | Holds |
|---|---|
| `DATADESK_R2_ENDPOINT_URL` | `https://<account id>.r2.cloudflarestorage.com` |
| `DATADESK_R2_ACCESS_KEY_ID` | the R2 token's access key id, a credential |
| `DATADESK_R2_SECRET_ACCESS_KEY` | the R2 token's secret, a credential |
| `DATADESK_R2_ARCHIVE_BUCKET` | the name of the archive bucket |
| `DATADESK_HTTP_USER_AGENT` | the User-Agent that `Http` sends to the City's site |

`Settings` keeps both key values out of its `repr`, and no command prints either one. The
owner sets `DATADESK_HTTP_USER_AGENT` to the string the old repo sends, `BROWSER_UA` in
`publisher_http.py` (answer A). `datadesk` holds no User-Agent string of its own.

CI runs on the fakes and reads no credential. The `ObjectStore` contract suite reads its target
from four variables of its own: `DATADESK_CONTRACT_S3_ENDPOINT_URL`,
`DATADESK_CONTRACT_S3_ACCESS_KEY_ID`, `DATADESK_CONTRACT_S3_SECRET_ACCESS_KEY` and
`DATADESK_CONTRACT_S3_BUCKET`. It skips its real half, with a message, when they are unset. The
MinIO run sets them to a local server with throwaway keys. A run against R2 sets them to a
scratch bucket and a real token, and only with the owner's go (open question B). So no test
writes to the archive bucket, and no test reads the five variables above.

## Risks to probe

1. **The City's server refuses a client that is not a browser** (facts 6 and 11). The probe
   this risk asked for ran on November 23, 2026, and the City refused a plain User-Agent. The
   owner chose the browser's string that the old repo sends, and he starts the runs that reach
   the City (answer A). No request with that string has been run from this repo, so his first
   run in S3-E is the probe. A refusal stops S3-E for him.
2. **A held copy may not be the City's current file** (fact 5, QPOS-Q32). S3-E compares the two
   shas for each of the 14 editions before any row is checked.
3. **Page 1 prints the period twice**, once in the phrase and once as a bare date
   (`FY22_Q1.pdf`). `confirm_period` reads the `PERIOD ENDING` phrase alone (QCASH-Q05,
   QOBL-Q04). pdfplumber may break the phrase across lines or put U+00A0 in it (QOBL-Q02), so
   S3-C tests both, and S3-E runs the 20 real covers.
4. **A title, a cover and a URL can name different days** (fact 5, FY2026 Q3). The edition
   comes from the title. The old `reports_from_feed` mapped a title date by its month alone
   (`qcmr.py:145`), so a title dated March 30 read as Q3. Here such a title is a finding
   (shape 5).
5. **Conditional writes through boto3** (design line 2290, section 18.1). `IfNoneMatch="*"` and
   `IfMatch` on `put_object` must raise `PreconditionFailed` on MinIO and on R2, and the etag
   that `put` and `head` return must be the same string.
6. **The feed fixture is a recorded response.** S3-B saves the feed's body from a browser,
   cuts it to the QCMR category and one other, and states the cut in the fixture. No one types
   it.
7. **The import pin and the socket block.** `import json` fails the purity test and
   `from json import loads` passes with a pin (design 11.1). The MinIO test needs the
   `enable_socket` marker, and a test over TLS needs `import ssl` at the top of the root
   `conftest.py` (`docs/progress.md`).
8. **S3-D is the largest pull request**, about 670 lines by the estimates of design 12.3. If
   its review finds the adapter and the commands too much for one fix round, the owner may
   split it at `s3.py`.

## The owner's answers

The owner answered six questions in the session on November 23, 2026. Each row quotes the
question as the session put it to him, and his answer. The longer wording of each question is
in this file at commit `0d411bb`.

| # | What he was shown | His words |
|---|---|---|
| 1 | "What User-Agent may `datadesk` send to the City's site? I propose a plain one that names the tool and a contact. If the City refuses it, the choices are the old repo's browser User-Agent or six downloads by hand." | "Yeah use a plain one. Anything should work." |
| 2 | "Does step 3 index FY2027 Q1? I propose yes, with a 21st inventory row." | "Yes" |
| 3 | "Which R2 bucket is the archive, and may step 3 use it? It stores about 50 MB. I have not read your account's allowance. A second go is needed to run the contract suite on a scratch bucket with a real token." | "I don't have one set up. I'm not familiar with the cli tooling around R2, just aws s3" |
| 4 | "Is the inventory right as the plan proposes it? The rows now come from the City's files, downloaded apart from `datadesk`." | "yes" |
| 5 | "What happens to a held copy that differs from the City's file? I propose leaving it out of the index and listing it in the pull request." | "your rec is fine" |
| 6 | "May the Build session install the `gh stack` extension? It is not installed." | "yes" |

What follows from each answer:

1. `Http` sends the value of `DATADESK_HTTP_USER_AGENT`. The City then refused two plain
   values (fact 11), so this answer did not settle how the City's files arrive. Answer A
   below did.
2. The catalog entry has no last period end. The inventory and the index hold 21 rows.
3. "Setting up R2" gives the steps. His answer gives no go for the contract suite on R2, so
   open question B asks again.
4. "The inventory" stands, with the two later details it names.
5. `plan_import` refuses a held copy that differs, with the reason `differs_from_listed`
   (shape 6). It is not indexed, and the pull request of S3-E lists it.
6. The Build session of S3-A runs `gh extension install github/gh-stack`
   (`docs/working-with-claude-code.md`).

**Answer A.** He answered a seventh question later that day. The session had shown him the
City's refusal (fact 11) and three choices: he sets the User-Agent and starts
`datadesk fetch qcmr` himself, he saves the feed and the 21 reports by hand, or he asks the
City to let the tool through. It had also told him that it would not send a browser's string
to get past the City's block, and that a Build session should not either. The question as he
saw it: "How should the City's files arrive at step 3: you run the fetch, hand downloads, or
ask the City?" His words: "Run the fetch with browser user agent as the original repo did. I
used to work for the city we have permission".

What follows from answer A:

- `DATADESK_HTTP_USER_AGENT` in his `.env` holds the string the old repo sends, `BROWSER_UA`
  in `publisher_http.py`.
- He asked for the fetch to be run. The agents that build this repo do not send a browser's
  string to a server that refuses other clients, whoever asks. So he starts the two
  `datadesk fetch qcmr` runs of S3-E in his terminal, and the session reads their output. The
  plan's order of work stands as written.
- The City's permission is his statement. No session has checked it.

## Still open

**B. May the `ObjectStore` contract suite run once against a scratch bucket on R2?** A yes adds
a second bucket, `phillyledger-scratch`, to steps 2 and 3 of "Setting up R2". Without a yes,
MinIO and Cloudflare's page are the proof of the conditional writes, and the fetch of S3-E
proves `CreateOnly` on R2 and nothing more.

## Codex review

Codex reviewed commit `39f8af3e` on November 23, 2026. Its report is
`.codex-review/step-03-plan-39f8af3e.md`. It raised twelve findings, four as blocking. Each was
checked against the plan, the design or a run, all twelve held, and the plan above is revised
for each. None is disputed.

| # | Finding | How it was confirmed | What changed |
|---|---|---|---|
| 1 | C1 to C3 pass with two shas filed under each other's quarter, or with a quarter missing from both files | The plan's test names compared sha sets, not pairs | "Clauses": the test holds its own 20 ids and compares pairs, and two changes are shown failing |
| 2 | C5's test ran `run_fetch`, which neither reads the listing nor writes the index | Design line 2368, and shape 10 gives the write to the CLI | C5's test drives the command twice on a temporary checkout and asserts the first run's result |
| 3 | A create-only conflict counted as stored without reading the object | `put_immutable` at design line 2465 hashes the object | Shape 9 uses `put_immutable`, and S3-D tests both outcomes |
| 4 | `import-held` read all 73 files and needed inventory rows that did not exist yet | The plan's own text | Shape 6 and "The inventory": rows for the expected editions come first, and the import reads only the files they name |
| 5 | The inventory hashed the archive's own output | The plan's own text | "The inventory": the sha comes from a `curl` download, compared with the archive object, its key and the index |
| 6 | The fixture could not prove the category filter or "last link per edition wins" | Design line 2035, and the fixture was cut to one category | Shape 5 and S3-B: a second category stays, and the two-attachment test is ported |
| 7 | A new URL for indexed bytes was dropped, and new bytes at an unchanged URL could not be added | Design lines 1102 and 5056 | Shapes 2 and 7, with tests in S3-A and S3-C |
| 8 | `plan_watch` had no field for the bad title it promised to report, and the old code was misdescribed | Shape 5 kept `findings` empty, and `qcmr.py:145` maps by month | Shape 5 returns a finding, and risk 4 is corrected |
| 9 | A held file had no typed form, and no note reached the command | Design lines 2008 and 2379 | Shape 6 adds `Held` and `plan_import`, and shape 8 defers real notes to step 5 |
| 10 | The store tests passed an adapter that refuses every `IfMatch`, and two adapters had no contract | Design lines 2293, 3786 and 4051 | S3-D: the full condition matrix, retries, the `Http` and `page1_text` contracts, and the root `conftest.py` |
| 11 | Explicit keys do not shut out an AWS profile | Rerun: `ProfileNotFound` under a missing `AWS_PROFILE`, boto3 1.43.26 | "Environment variables": the claim is gone, and a test must prove the isolation |
| 12 | A real R2 run contradicted "no test reads a real credential", and the cost was unstated | The plan's own text, and the byte total recomputed as 38,831,218 | The contract suite has its own variables and a scratch bucket, and question 3 asks for the go |

## Changes after the review

Codex read commit `39f8af3e`. It has not read these changes, which follow the owner's answers
and facts 10 and 11.

- FY2027 Q1 is in, so the inventory and the index hold 21 rows (answer 2).
- The archive bucket is private at step 3, and `DATADESK_R2_ARCHIVE_PUBLIC_URL` is gone
  ("Setting up R2").
- The real half of the `Http` contract suite runs against a local server. No session sends the
  City a request (fact 11).
- The owner starts the two fetch runs of S3-E, with the User-Agent he sets (answer A).
- The inventory's download is by the owner's browser, and its read-back is `aws s3 cp`.
- S3-E adds a note for step 13 to `docs/plan-notes.md`.
