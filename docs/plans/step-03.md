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
| C1 | Each of the 20 reports, FY2022 Q1 to FY2026 Q4, is indexed | S3-E | `test_each_of_the_20_reports_is_indexed` in `tests/test_archive_inventory.py` |
| C2 | Each is indexed once | S3-E | `test_each_inventory_sha_is_indexed_once`, same file |
| C3 | Each is indexed by the sha in the inventory | S3-E | `test_the_index_holds_the_inventory_shas`, same file |
| C4 | The inventory is checked by hand | S3-E | `test_every_inventory_row_is_checked`, same file, and the owner's words in the pull request |
| C5 | Fetching the same listing again adds nothing | S3-D | `test_fetching_the_same_listing_again_adds_nothing` in `packages/datadesk/tests/shell/test_run_fetch.py` |

The three tests of C1 to C3 read the index file and the inventory file from the checkout and
compare them. The index comes from `datadesk`. The inventory comes from `shasum`, `pdfinfo` and
`pdftotext`, so the two sides share no code. C4's test fails while any row has an empty
`checked` cell, and only the owner's word fills a cell (see "The inventory").

C5's test runs `run_fetch` twice against a fake `Http` that replays the recorded feed, a fake
`PdfReader` and the dict store. After the second run the store saw no `put`, the index text is
byte for byte the same, and the plan holds no file to write. S3-C adds the pure half,
`test_plan_fetch_adds_nothing_for_an_indexed_sha`. S3-E records the second real run against the
City's site and R2 in its pull request.

## Shapes the design leaves open

The Build sessions skip `how` and `architect`, so this plan names what the design does not. The
pull request that builds a shape records it in `docs/design.md` and in
`docs/deviations/step-03.md` (hard rule 7).

1. **A QCMR edition's period is its fiscal quarter.** `Period(first day of the quarter, the
   printed end date)`, so FY2026 Q4 is April 1 to June 30, 2026, and its id is
   `qcmr:2026-06-30:none`. Editions then never overlap.
2. **`listed_at`.** For a document-finder link it is the 14-digit upload stamp in the URL path.
   For a held copy it is the empty string, which sorts first, so a held copy never outranks a
   listed version. Two versions of one edition with the same `listed_at` make `add_versions`
   return a finding.
3. **The index file** is `packages/datadesk/src/datadesk/data/index.jsonl`, one
   `DocumentVersion` on each line.
4. **`SourceEntry`** has `id`, `series`, `shape`, `listing_url`, `category` and
   `first_period_end`. `shape` is a `ListingShape`, a `StrEnum` of `document_finder`,
   `phila_documents` and `manual`. `SourceCatalog` holds the entries and `entry(id)`.
   `load_catalog(text)` returns a `SourceCatalog` or findings. Lag, recheck interval,
   `missing_ok`, slug exceptions and `DatasetSpec` wait for the steps that need them.
5. **`plan_watch`, first cut.** It keeps the design's signature. A listed link gets one
   `FetchRequest` when it has an edition and no skip reason, its period ends on or after the
   entry's `first_period_end`, and no indexed version holds its URL. The reason is `new` when
   the edition has no version and `revision` when it has one. `wayback`, `gaps` and `findings`
   stay empty until step 13. `PullRequestPlan(files, branch, title, body)` lives in
   `core/watch.py`.
6. **The City's file first, the held copy second.** `datadesk fetch qcmr` downloads every listed
   report from FY2022 Q1 on, because five URLs show a second upload and the City's last listed
   file is the current version of its edition (design 6.3). `datadesk import-held` then builds
   one `Fetched` for each held file, with the reason `held` and no URL, and sends it through the
   same `plan_fetch`. A held sha that is already indexed under its edition adds nothing. A held
   file for an edition with no version is indexed with `Via.MANUAL` and no URL. A held sha that
   differs from its edition's listed version is a `Rejection` with the reason
   `differs_from_listed`, and the owner decides it.
7. **`confirm_period` returns the period the page prints.** It is the expected period, or the
   period a `PRINTED_PERIOD` note names for a text that page 1 holds. Anything else is a
   finding: no phrase, a date that is not a quarter end, or another quarter with no note.
   `plan_fetch` passes it only the notes whose `doc_sha256` is the fetched sha.
8. **One store for each bucket.** R2 cannot make one object public (fact 7), so
   `ObjectStore.put` loses `public` and becomes `put(key, data, condition)`. `Deps` holds a
   store bound to the archive bucket. A later step adds a store for each bucket it needs. The
   sketch of `run_fetch` at design line 2381 also omits `condition`. A report is stored with
   `CreateOnly`, and a `PreconditionFailed` on a key that is the report's own sha counts as
   stored.
9. **`run_fetch` returns the `FetchPlan` and calls no `GitHost`.** The CLI writes the plan's
   files into the checkout, last, after every `put`, and prints the title and the body. The
   session opens the pull request. Step 13 builds the `GitHost` port and its adapter.
10. **`PdfReader` has `page1_text` alone** at step 3. Step 4 adds `words` and `render`.

## Pull requests

One GitHub stack, bottom first. Each pull request also touches `docs/design.md`,
`docs/deviations/step-03.md` and `docs/progress.md` for what it builds, and `tests/test_purity.py`
for the outside names its core modules import. Paths below drop `packages/datadesk/`.

### S3-A, `step-03/a-index`: the index format

Builds on `main`. `feat(datadesk): add the archive index`.

- Files: `src/datadesk/core/domain.py`, `src/datadesk/core/index.py`,
  `tests/core/test_domain.py`, `tests/core/test_index.py`.
- Proves: `render_index(parse_index(text)) == text` for a sorted text, and
  `parse_index(render_index(index)) == index` as a Hypothesis property. `ArchiveIndex` refuses
  one sha twice. `add_versions` returns a finding for a sha under another edition and for two
  versions with one `listed_at`. `current` gives the last listed version.

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
- Proves, on the recorded feed: 21 report links get editions and 13 infographics get the skip
  reason `infographic`. "Manager's" and "Managers" read the same. The host `admin.phila.gov`
  becomes `www.phila.gov` (QCASH-Q04). The edition comes from the title and never from the URL.
  `plan_watch` asks for 21 fetches on an empty index and none when the index holds every URL.

### S3-C, `step-03/c-fetch-plan`: `confirm_period` and `plan_fetch`

Builds on S3-B. `feat(datadesk): confirm the printed period and plan a fetch`.

- Files: `src/datadesk/core/fetch.py`, `src/datadesk/core/records.py` with `NoteKind` and
  `EditionNote` alone, `tests/core/test_fetch.py`, and
  `packages/checkedtables/tests/test_library_shape.py`, where `test_closed_lists_are_pinned`
  starts with the `NoteKind` pin (hard rule 6, design 11.4).
- Proves, for `confirm_period`: the printed quarter end passes. Another quarter is a finding
  (QOBL-Q06). A mismatch passes only with a `PRINTED_PERIOD` note whose text page 1 holds
  (QCASH-Q07). A cover with no phrase is a finding. September and December ends belong to the
  next fiscal year (QPOS-Q34).
- Proves, for `plan_fetch`: a confirmed report gets one `StoreObject` at
  `pdf/<sha[:2]>/<sha>.pdf` and one index line. A sha indexed under another edition is a
  `content_alias` rejection (MSCH-Q01). A status other than 200 is a rejection. A later listing
  of an edition supersedes the earlier version (QPOS-Q32). A held copy that differs from the
  listed version is a `differs_from_listed` rejection. An indexed sha adds nothing.

### S3-D, `step-03/d-shell`: the S3 adapter and the two commands

Builds on S3-C. `feat(datadesk): store reports in R2 and run fetch`.

- Files: `src/datadesk/shell/ports.py`, `settings.py`, `gather.py`, `run_fetch.py`, `cli.py`,
  `src/datadesk/shell/adapters/__init__.py`, `s3.py`, `http_httpx.py`, `pdf_pdfplumber.py`,
  `tests/shell/` with the fakes, the contract suite and the tests below,
  `packages/datadesk/pyproject.toml` for `boto3`, `httpx`, `pdfplumber` and the `datadesk`
  script, `uv.lock`, and `CLAUDE.md` for the two new commands.
- Proves: C5. The `ObjectStore` contract suite passes on the dict store in CI. `CreateOnly`
  refuses a key that exists and leaves its bytes. `IfMatch` refuses a stale etag.
  `load_settings` names a missing variable and never prints a value. `import-held` stops when a
  held file's sha is not the one its inventory row gives.
- The owner of S3-D runs the same contract suite against MinIO in Docker and records the run in
  the pull request. Design 11.1 runs real-adapter contracts nightly and before a release, so CI
  skips that half, and the suite reports the skip.

### S3-E, `step-03/e-archive`: the 20 reports

Builds on S3-D. `feat(datadesk): index the QCMR reports from FY2022`. It adds data and no code
under `src/`.

- Files: `src/datadesk/data/index.jsonl`, `docs/evidence/inventory/qcmr.tsv`,
  `tests/test_archive_inventory.py`, `docs/plan-notes.md`, `CLAUDE.md`.
- Runs, each recorded in the pull request with its command and output: the contract suite
  against R2, `datadesk fetch qcmr`, `datadesk import-held`, and `datadesk fetch qcmr` a second
  time.
- Owns C1 to C4. `docs/plan-notes.md` gets a note for step 7: the feed lists QCMR reports back
  to December 31, 2006. `CLAUDE.md` gets the folder of the held reports in place of "ask for
  the path when step 3 starts".

## The inventory

`docs/evidence/inventory/qcmr.tsv` has one row for each indexed report, with the columns
`edition`, `sha256`, `bytes`, `pages`, `page1_period`, `url`, `held_file`, `held_sha256` and
`checked`.

How it is made, in S3-E:

1. After the first fetch, the session downloads each stored report from the archive bucket by
   its key into a scratch folder.
2. A shell loop over that folder fills `sha256` with `shasum -a 256`, `bytes` with `stat`,
   `pages` with `pdfinfo`, and `page1_period` with the `PERIOD ENDING` phrase from
   `pdftotext -f 1 -l 1`. The same loop over the owner's folder fills `held_file` and
   `held_sha256`. The pull request prints the loop, so anyone can run it again.
3. The session checks each row against the table above. A sha that differs from the copy seen
   is reported to the owner before anything else.

How it is checked: the owner opens each PDF from the scratch folder. He confirms that the cover
names the row's period, that the file is the whole report with the row's page count, and that
his own `shasum -a 256` of the file prints the row's sha. He says so in the session. The session
then writes the date in `checked` for the rows he named, and quotes his words in the pull
request. No agent fills `checked` on its own reading.

The owner has seen an earlier form of this proposal and has not confirmed it (question 4).

## Environment variables

`load_settings(environ)` reads these six and nothing else. The S3 adapter passes the values to
its client itself and reads no `AWS_*` variable and no credentials file, so a profile set for
another account is never used.

| Variable | Holds |
|---|---|
| `DATADESK_R2_ENDPOINT_URL` | `https://<account id>.r2.cloudflarestorage.com` |
| `DATADESK_R2_ACCESS_KEY_ID` | the R2 token's access key id, a credential |
| `DATADESK_R2_SECRET_ACCESS_KEY` | the R2 token's secret, a credential |
| `DATADESK_R2_ARCHIVE_BUCKET` | the name of the archive bucket |
| `DATADESK_R2_ARCHIVE_PUBLIC_URL` | the bucket's public address, which the hand check downloads from |
| `DATADESK_HTTP_USER_AGENT` | the User-Agent that `Http` sends to the City's site |

`Settings` keeps the secret out of its `repr`. No test and no CI job reads a real credential.
The MinIO run sets the same variables for a local server.

## Risks to probe

1. **The City's CDN refuses a client that is not a browser** (fact 6). S3-D sends one request
   with the User-Agent the owner picks, before it writes the adapter. A refusal stops the step
   for the owner.
2. **A held copy may not be the City's current file** (fact 5, QPOS-Q32). S3-E compares the two
   shas for each of the 14 editions before any row is checked.
3. **Page 1 prints the period twice**, once in the phrase and once as a bare date
   (`FY22_Q1.pdf`). `confirm_period` reads the `PERIOD ENDING` phrase alone (QCASH-Q05,
   QOBL-Q04). pdfplumber may break the phrase across lines or put U+00A0 in it (QOBL-Q02), so
   S3-C tests both, and S3-E runs the 20 real covers.
4. **A title, a cover and a URL can name different days** (fact 5, FY2026 Q3). A report title
   whose date is not a quarter end gets a skip reason that `plan_watch` reports, and never
   disappears, as it did in the old `reports_from_feed`.
5. **Conditional writes through boto3** (design line 2290, section 18.1). `IfNoneMatch="*"` and
   `IfMatch` on `put_object` must raise `PreconditionFailed` on MinIO and on R2, and the etag
   that `put` and `head` return must be the same string.
6. **The feed fixture is a recorded response.** S3-B saves the feed's body with the adapter's
   client or from the owner's browser, cuts it to the QCMR category, and states the cut in the
   fixture. No one types it.
7. **The import pin and the socket block.** `import json` fails the purity test and
   `from json import loads` passes with a pin (design 11.1). The MinIO test needs the
   `enable_socket` marker, and a test over TLS needs `import ssl` at the top of the root
   `conftest.py` (`docs/progress.md`).
8. **S3-D is the largest pull request**, about 670 lines by the estimates of design 12.3. If
   its review finds the adapter and the commands too much for one fix round, the owner may
   split it at `s3.py`.

## Questions for the owner

1. **What User-Agent may `datadesk` send to the City's site?** The proposal is a plain one that
   names the tool and a contact address. If the City refuses it, the choices are the browser
   User-Agent the old repo sends, or six downloads by hand into the held folder.
2. **Does step 3 index FY2027 Q1?** The feed lists it (fact 4). The proposal is yes, with a 21st
   inventory row. The clauses stay about the 20. If no, the catalog entry gets a last period
   end of June 30, 2026, which a later step removes.
3. **Which R2 bucket is the archive, and what is its public address?** The design says "both
   buckets use Cloudflare R2" and names neither. Step 3 needs the archive bucket, a token that
   can write to it, and the six variable names above confirmed or changed.
4. **Is the inventory right as proposed?** The form shown earlier was a 20-row table computed
   from the held folder: edition, file name, sha256, page count and the period printed on page
   1, each row checked by opening the PDF. This plan changes two things. The rows come from the
   City's files in the archive, and the held copies are a second sha beside them (shape 6).
5. **What happens to a held copy that differs from the City's file?** The proposal is to leave
   it out of the index and list it in the pull request. The other choice is to index it as an
   earlier version.
6. **May the Build session install the `gh stack` extension?** It is not installed (fact 8), and
   `docs/plans/README.md` requires it from this step on.
