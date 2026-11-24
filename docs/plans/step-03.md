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
12. A real browser reads the City's files. In the built-in browser of the Claude app, a page on
    `https://www.phila.gov` fetched each of the 21 report URLs and hashed the bytes with
    `crypto.subtle.digest`. All 21 came back with HTTP 200. The second table below gives the
    byte count and the sha256 of each. The five copies in the old repo have the City's sha.
    None of the 14 copies in the owner's folder does. `FY22_Q1.pdf` holds 2,748,146 bytes, and
    the City's file for that quarter holds 1,781,180.
13. That browser cannot write a file to disk. A click on a download link left no file, and the
    pane blocks a page's request to `127.0.0.1` (`net::ERR_BLOCKED_BY_CLIENT`). Chrome can.
    Once the owner had connected its Claude extension, the planning session saved the feed's
    body and the 21 reports through Chrome, each by a click on a link to its URL. The files are
    in `~/DataProjects/phillyledger-held/qcmr-city` with `responses.tsv`. `shasum -a 256` of
    each report equals its sha in the second table below. The feed's body holds 388,460 bytes,
    and its sha256 is `aa6b4e4708d780d6b005b1e74731fba7a6938427168a0799cacdad943473d837`.
14. The FY2027 Q1 report has no text that a program can read. Its two fonts are CID TrueType
    with `Identity-H` and no Unicode map (`pdffonts`), so `pdfplumber` returns `(cid:38)` codes
    on pages 1, 2 and 10, and `pdftotext` returns shifted characters. `tesseract` on the cover
    image reads "FOR THE PERIOD ENDING SEPTEMBER 30, 2026". The other 20 covers print their
    `PERIOD ENDING` phrase as text, each with the expected quarter end, and the 21 files have
    78, 78, 79, 79, 78, 77, 74, 73, 74, 74, 74, 74, 98, 96, 90, 88, 92, 95, 94, 92 and 92
    pages (`pdfinfo`).

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

The City's files, as a browser read them on November 23, 2026 (fact 12). The 21 files hold
42,108,658 bytes. This is not the inventory either. No one has opened these files.

| Edition | Bytes | sha256 of the City's file | The copy seen |
|---|---:|---|---|
| FY2022 Q1 | 1,781,180 | `7c4a2e5abb00a5084cdb24fb35325cd1f2cdee42cfd9b30cf7c62c46c2f22918` | differs |
| FY2022 Q2 | 2,292,284 | `401136b9ca279d46ab11e25a6d3da0980b30cbf147fc23976cc467519aa7aed7` | differs |
| FY2022 Q3 | 1,819,602 | `212011ea27a2b2f250b10df6803a9b5a8479c50c2cbbdde4e6337572ed7a3c17` | differs |
| FY2022 Q4 | 1,800,765 | `940773bc90362453fb4709f5791fc61ee650e1c82dfa2f56627a7ce266bc40da` | differs |
| FY2023 Q1 | 1,645,726 | `cbddaf2fb174d1eb6400e460244324cbb1c13ae4e1f0565f50c0929bfc694d1e` | differs |
| FY2023 Q2 | 2,252,295 | `a6654785d20f6d906488d3936c4d1b4ad8a0b176756acb2cbb43fbbbe32fc233` | differs |
| FY2023 Q3 | 2,007,412 | `d72aef7a2d98bfcca8f732e4511de5486938b1be0d1952761eb8e20f8f328d4c` | differs |
| FY2023 Q4 | 2,546,166 | `bf29b59e623b7465da67743d376df6d8ceadb59995fbc7ce96d01b90d1c1594c` | differs |
| FY2024 Q1 | 1,861,104 | `92eb0fda42dbf566f1a01c25a8b42ed7f0a887cff9c5a0b7bff35fb999ffc82a` | differs |
| FY2024 Q2 | 2,171,533 | `852b850f3b0ae77ecf2ccdac065da73cc6d4afa0e87756bcc5e79f9ec204c52c` | differs |
| FY2024 Q3 | 2,294,974 | `7a859d47071c6dac4ad98f8f2c9a62e4f2dc1c59614fae109f78d9f189990c6b` | differs |
| FY2024 Q4 | 1,868,452 | `bda61e16130d7fb311024b951cbc0afbe3c6ad615ac69516efe07ea4e3683824` | differs |
| FY2025 Q1 | 1,592,311 | `ea2a183e2cc251d63e5063234483d79e0f4c38c01da2341348634e1f64d8a34c` | differs |
| FY2025 Q2 | 2,224,737 | `85b1c8720e1c280090e0f3e3bbe51240086d3b830a9c2774e751dfd54dc27843` | differs |
| FY2025 Q3 | 2,937,675 | `0e6895f1cc3fa8476761cf71decc930a473f7be48662b11fdfa8663f94eeb63f` | same sha |
| FY2025 Q4 | 1,636,815 | `fdae8df31b0d7144557d5a803b1eb5f0a969ee43b60a55960db71b7e77e4afdd` | no copy |
| FY2026 Q1 | 1,688,297 | `377c9305e6ac182da830aaeaf0e7892c53b79e94c05ecc85b61103157f152747` | same sha |
| FY2026 Q2 | 1,745,318 | `f7b627e958ffa22c63d0af8b5584c4b3bf2266907156891fd84614186f083aae` | same sha |
| FY2026 Q3 | 2,386,107 | `032c5cfddfb77c50b270d5f0954d73674b5ec1c92c5d3fdee4b60e53efd82827` | same sha |
| FY2026 Q4 | 2,483,740 | `48fd9aa936df05a28bb7f37083720afac85d1ee2a2c9a70be832382f0dc55020` | same sha |
| FY2027 Q1 | 1,072,165 | `640068cb7a8a5d6c621f0ac6a0b2e16df6c290fc1036ea95f2260057be58f365` | no copy |

## Clauses

| # | Clause of the check | Owner | Test that proves it |
|---|---|---|---|
| C1 | Each of the 20 reports, FY2022 Q1 to FY2026 Q4, is indexed | S3-E | `test_each_expected_edition_has_a_row_and_an_indexed_version` in `tests/test_archive_inventory.py` |
| C2 | Each is indexed once | S3-E | `test_each_inventory_pair_is_indexed_once`, same file |
| C3 | Each is indexed by the sha in the inventory | S3-E | `test_each_edition_is_indexed_under_its_inventory_sha`, same file |
| C4 | The inventory is checked by hand | S3-E | `test_every_inventory_row_is_checked`, same file, and the owner's words in the pull request |
| C5 | Fetching the same listing again adds nothing | S3-D | `test_fetching_the_same_listing_again_adds_nothing` in `packages/datadesk/tests/shell/test_fetch_command.py` |

The tests of C1 to C3 read the index file and the inventory file from the checkout. The test
file holds 20 edition ids as its own list, the quarter ends from September 30, 2021 to June 30,
2026. FY2027 Q1 is not among them at step 3 (fact 14, open question D). C1 requires one
inventory row and an index line for each id, so an edition that is missing from both files
fails. C2 and C3 compare pairs. Each row's
`(edition, sha256)` must be on exactly one index line, as a version of that edition. They do
not ask for the current version, because one edition can have several versions (design line
3483) and a later step may index a revision.

S3-E shows two changes failing, each in its pull request: the shas of FY2022 Q1 and Q2
swapped in the index, and one quarter removed from both files. It also prints a run that
compares the two files as multisets of pairs and finds them equal, so the index holds no line
beyond the 20. That equality is a run at S3-E and not a
lasting test, because a later step may add a version.

The index comes from `datadesk`. The inventory's `sha256` comes from `shasum` of a file that a
browser saved, beside a digest that the browser computed from the City's URL (see "The
inventory"), so the two sides share no code. C4's test fails while any row
has an empty `checked` cell, and only the owner's word fills a cell.

C5's test drives the function behind `datadesk fetch qcmr` twice, so it covers the listing
read, `run_fetch` and the index write. It uses a temporary checkout, a fake `Http` that replays
the recorded feed and one body for each report URL, a fake `PdfReader`, and the dict store.
After the first run it asserts the store's keys, the bytes under each key, and the edition and
sha of each index line. It then loads the checkout again and runs the command a second time.
The store saw no new `put`, the index file is byte for byte the same, and the plan holds no
file to write. The fake's call log shows that the second run asked for the listing again, and
the run reports the same listing digest with no finding and no rejection. A third run, on a
feed with one more edition, adds that edition alone. So a command that returns early on a
filled index fails. S3-C adds the pure half, `test_plan_fetch_adds_nothing_for_an_indexed_sha`.
S3-E records two real runs over the saved folder and R2 in its pull request, and each run
prints the listing's `html_sha256`.

## Shapes the design leaves open

The Build sessions skip `how` and `architect`, so this plan names what the design does not. The
pull request that builds a shape records it in `docs/design.md` and in
`docs/deviations/step-03.md` (hard rule 7).

1. **A QCMR edition's period is its fiscal quarter.** `Period(first day of the quarter, the
   printed end date)`, so FY2026 Q4 is April 1 to June 30, 2026, and its id is
   `qcmr:2026-06-30:none`. Editions then never overlap.
2. **`listed_at` and the order of versions.** For a document-finder link `listed_at` is the
   14-digit upload stamp in the URL path.
   `current(edition)` is the edition's version that no other version supersedes. A new version
   supersedes the current one when its `listed_at` is later or the same, so step 13 can record
   new bytes behind an unchanged URL (design 18.1). A new version with an earlier `listed_at`
   is a rejection for the owner.
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
   one `FetchRequest` for each link whose URL no indexed version of its own edition holds. A
   link to a URL that another edition's version holds is still fetched, so `plan_fetch` sees
   the bytes and rejects them as `content_alias` (design line 3489). The reason is `new`
   when the edition has no version and `revision` when it has one. A link whose title reads as
   a report and whose date is not a quarter end gets the skip reason `not_a_quarter_end`, and
   `plan_watch` returns a finding for it in `WatchPlan.findings`. `wayback` and `gaps` stay
   empty until step 13. `PullRequestPlan(files, branch, title, body)` lives in `core/watch.py`.
6. **The City's responses come from a folder that a browser saved.** The City refuses a client
   that is not a browser (facts 6 and 11), and the owner chose a real browser (answer A). So at
   step 3 the `Http` port has one adapter, `http_saved.py`. It reads `responses.tsv` in a
   folder, a list of `url` and `file`. It answers a listed URL with status 200 and the bytes of
   its file, and any other URL with status 404, which `plan_fetch` rejects.
   `datadesk fetch qcmr --saved <folder>` then runs the design's whole path on the City's real
   feed and files: `parse_listing`, `plan_watch`, `run_fetch`, `confirm_period`, `plan_fetch`,
   `put_immutable` and the index write. It takes the last listed report of every edition from
   FY2022 Q1 on (design 6.3), and the index says `Via.PUBLISHER`, because the bytes came from
   the City's URL. This run is the design's "one-time import of held FY2022 to FY2026 reports
   by sha". The live adapter, its User-Agent and its contract suite wait for step 13, with
   `watch`. This plan no longer has `import-held`, `Held` or `plan_import`. None of the owner's
   14 copies has the City's sha (fact 12), and answer 5 leaves a copy that differs out of the
   index. S3-E lists the 14 in its pull request.
7. **A version gains a URL.** When a fetched sha is already indexed under its edition and the
   request's URL is new, `plan_fetch` stores nothing and `index_add` carries the version with
   that URL. `add_versions` merges it into the one line, so `urls` holds every URL that served
   the bytes (design line 1102) and the next `plan_watch` asks for nothing. This holds for the
   edition's current sha alone. When a later listing serves a superseded sha again, as in
   bytes A, then B, then A, the request is a `Rejection` with the reason
   `superseded_sha_relisted`, for the owner. One line for each sha cannot say that A now
   supersedes B, and the later `listed_at` must win (design line 3488).
8. **`confirm_period` returns the period the page prints.** It is the expected period, or the
   period a `PRINTED_PERIOD` note names for a text that page 1 holds. Anything else is a
   finding: no phrase, a date that is not a quarter end, or another quarter with no note.
   `plan_fetch` passes it only the notes whose `doc_sha256` is the sha at hand. The command
   passes no notes at step 3. `load_records` arrives at step 5. No cover seen so far
   needs a note. QCASH-Q07 is about a cash page, and the cover of the owner's whole FY2014 Q2
   report prints December 31, 2013 (`pdftoppm` and `tesseract` on `FY14_Q2.pdf`). So unit tests
   alone prove the note path here, and a real note needs a page 1 mismatch on an archived sha.
   A cover among the 20 that fails stops S3-E for the owner. The cover of FY2027 Q1 fails in
   a known way (fact 14), so `plan_fetch` rejects that report and stores nothing for it.
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
- The fixture is cut from a recording of the feed that the old repo holds, read only, under
  `../gov-budget-data/data/phila/catalog-snapshots/document-finder/151831/`. The file is
  `e483743d16cf909edf38abbe54dc32a2296159cf42716ae89862b7e10640115d.json`, 384,679 bytes,
  observed July 28, 2026. Its name is its sha256, checked with `shasum`.
  So S3-B needs no browser and nothing from the owner. The cut keeps the QCMR category from
  the last report before September 30, 2021 on, and one other category whole. The fixture
  states the cut, and no one types it.
- Proves, on the recorded feed: the report links from September 30, 2021 on get editions and
  the infographics get the skip reason `infographic`. Codex counted 19 and 13 in the
  recording, which predates FY2026 Q4 and FY2027 Q1, and S3-B asserts the counts it finds. The
  report before the floor gets no request, and the first one after it gets one. A link of the
  other category is never listed. "Manager's" and "Managers" read the same. The host
  `admin.phila.gov` becomes `www.phila.gov` (QCASH-Q04). The edition comes from the title and
  never from the URL, so `...March-30-2026R.pdf` under its March 31 title is FY2026 Q3.
  `plan_watch` asks for one fetch for each listed edition on an empty index and none when the
  index holds every URL. S3-E runs the saved feed, with its 21 report links.
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
  (QOBL-Q06). A mismatch passes only with a `PRINTED_PERIOD` note whose text page 1 holds, on
  a cover the test builds, and a note for another sha does not clear it. A cover with no phrase is a
  finding. September and December ends belong to the next fiscal year (QPOS-Q34).
- Proves, for `plan_fetch`: a confirmed report gets one `StoreObject` at
  `pdf/<sha[:2]>/<sha>.pdf` and one index line. A sha indexed under another edition is a
  `content_alias` rejection (MSCH-Q01). A status other than 200 is a rejection. A later listing
  of an edition supersedes the earlier version (QPOS-Q32), and so do new bytes with the same
  `listed_at`. An indexed sha at an indexed URL adds nothing. The current sha at a new URL
  adds the URL and stores nothing. With bytes A, then B, then A again at a later stamp, the
  third request is a `superseded_sha_relisted` rejection and B stays current.

### S3-D, `step-03/d-shell`: the S3 adapter and the fetch command

Builds on S3-C. `feat(datadesk): store reports in R2 and run fetch`.

- Files: `src/datadesk/shell/ports.py`, `settings.py`, `gather.py`, `run_fetch.py`, `cli.py`,
  `src/datadesk/shell/adapters/__init__.py`, `s3.py`, `http_saved.py`, `pdf_pdfplumber.py`,
  `src/datadesk/data/index.jsonl`, empty, `tests/shell/` with the fakes, the contract suites
  and the tests below, `packages/datadesk/pyproject.toml` for `boto3`, `pdfplumber` and the
  `datadesk` script, `uv.lock`, the root `conftest.py` for `import ssl`
  (`docs/progress.md`), and `CLAUDE.md` for the new command.
- Proves: C5. The `ObjectStore` contract suite covers a create on an absent key, a replacement
  with the current etag, a stale etag refused with the bytes kept, `CreateOnly` on a key that
  exists, and `IfMatch(None)` on an absent key and on one that exists. `put_immutable`
  completes when the store already holds the same bytes and raises when it holds others, each
  with the dict store loaded first. A failed `get` or `put` that then succeeds stores once.
  Three failures stop the command with the index file untouched.
- Proves: `load_settings` names a missing variable and prints no value.
  `test_s3_client_ignores_the_ambient_aws_profile` builds the adapter's client under an
  `AWS_PROFILE` that does not exist and under shared files that hold other keys.
- Proves: the `page1_text` contract on two PDFs the test builds, a text page and an image
  page. The `Http` contract passes on the fake and on `http_saved.py`, over a folder the test
  writes: a listed URL gives status 200 and its file's bytes, and any other URL gives 404.
- Proves, through the command with `--saved` on a folder the test writes: the run stores and
  indexes what the folder lists. With the feed's own row removed, or with a row that names a
  missing file, the command stops before any `put`. An edition listed at a URL that another
  edition's version holds is fetched and ends as a `content_alias` rejection.
- The contracts of `http_saved.py` and `pdf_pdfplumber.py` need no network and no credential,
  so they run in CI beside the fakes. CI skips the real half of the `ObjectStore` suite alone,
  with a message (design 11.1). The owner of S3-D runs it against MinIO in Docker and records
  the run in the pull request. No test and no session sends the City a request (fact 11).

### S3-E, `step-03/e-archive`: the 20 reports

Builds on S3-D. `feat(datadesk): index the QCMR reports from FY2022`. It adds data and no code
under `src/`.

- Files: `src/datadesk/data/index.jsonl`, `docs/evidence/inventory/qcmr.tsv`,
  `tests/test_archive_inventory.py`, `docs/plan-notes.md`, `CLAUDE.md`.
- Before the runs, the session checks the saved folder, which exists ("The saved folder").
- The session adds the quirk of fact 14 to `docs/evidence/quirks.tsv`, to `coverage.tsv` and
  to the dossier it belongs in.
- Runs, each recorded in the pull request with its command and output:
  `datadesk fetch qcmr --saved <folder>`, twice. The session starts both, and neither sends
  the City a request. With the owner's go (open question B), the `ObjectStore` suite also runs
  against a scratch bucket on R2.
- S3-E starts only after the owner has set up R2 ("Setting up R2"). S3-A to S3-D do not wait
  on it.
- Owns C1 to C4. The pull request lists the owner's 14 copies that differ from the City's
  files, each with its sha (answer 5, fact 12).
- `docs/plan-notes.md` gets two notes. For step 7: the feed lists QCMR reports back to
  December 31, 2006. For step 13: the City refuses a client that does not send a browser's
  User-Agent (fact 11), the owner's answer for a run that is his is the string the old repo
  sends (answer A), and the live `Http` adapter waits for that step.
- `CLAUDE.md` gets the saved folder in place of "ask for the path when step 3 starts".

## The saved folder

The saved folder holds what the City serves, as a real browser saved it: the feed's body, the
21 reports and `responses.tsv`. It is `~/DataProjects/phillyledger-held/qcmr-city`, on the
owner's machine and outside git. The planning session made it on November 23, 2026, after the
owner asked for the fetch through a real browser and connected Chrome (fact 13).

How it was made:

1. In a browser, on a page of `https://www.phila.gov`, the session fetched each of the 21
   report URLs of the feed and recorded the status, the byte count and the sha256 that the
   page computed (fact 12).
2. In Chrome, on that origin, it clicked a link to each report URL, with a file name for the
   download. It then opened the feed's URL and saved its body with one more click. Chrome
   wrote the 22 files to `~/Downloads`, and the session moved them into the folder as
   `feed.json` and `qcmr-<period end>.pdf`.
3. `shasum -a 256` of each saved report equals the sha256 that the page computed for its URL.
4. A short script wrote `responses.tsv`. Its first row maps the feed's own URL,
   `https://api.phila.gov/phila/document-finder/v1/151831`, to `feed.json`. The 21 report rows
   are read from those same feed bytes, with the host `www.phila.gov` (QCASH-Q04).

What S3-E does with it:

1. It hashes the 22 files again and compares the 21 reports with the second table above.
2. It reads the City's 21 URLs in a browser again, as in fact 12. A sha that differs from the
   saved file is a new upload, and it goes to the owner before any run.
3. If a file is missing or has changed, the session saves it again through Chrome. The owner
   asked for the agent to fetch (answer A), so a save by his hand needs his agreement.
4. Its two runs must end with 20 editions, one rejection, and no request for a report from
   before FY2022. The rejection is FY2027 Q1, for a cover with no readable phrase (fact 14).

## The inventory

`docs/evidence/inventory/qcmr.tsv` has one row for each expected edition, with the columns
`edition`, `sha256`, `bytes`, `pages`, `page1_period`, `url`, `browser_sha256` and `checked`.

How it is made, in S3-E:

1. Before any command runs, the session writes one row for each of the 20 editions, with
   `edition`, `url` and `browser_sha256` from the browser run of "The saved folder".
2. For each row, `sha256` is `shasum -a 256` of the saved file, `bytes` its size, `pages`
   comes from `pdfinfo`, and `page1_period` is the `PERIOD ENDING` phrase from
   `pdftotext -f 1 -l 1`. None of this shares code with `datadesk`.
3. `datadesk fetch qcmr --saved <folder>` runs.
4. For each row the session compares four things with the row's `sha256`: its
   `browser_sha256`, the digest of the object read back from the archive bucket, the object's
   key and the index line. The read-back is `aws s3 cp ... - | shasum -a 256` under
   `set -o pipefail`, with the keys passed through the environment ("Setting up R2"). The pull
   request records the command with the variable names. For the five editions whose copy in
   the old repo has the City's sha, that copy is a fifth witness. Any difference goes to the
   owner before he checks a row.

The pull request prints each loop, so anyone can run it again.

How it is checked: the owner opens each PDF from the saved folder. He confirms that the cover
names the row's period, that the file is the whole report with the row's page count, and that
his own `shasum -a 256` of the file prints the row's sha. He says so in the session. The session
then writes the date in `checked` for the rows he named, and quotes his words in the pull
request. No agent fills `checked` on its own reading.

The owner confirmed an earlier form on November 23, 2026 (answer 4). Three details came after
his answer, and he has not seen them. The files come from the saved folder, where the form he
confirmed used `curl`. `browser_sha256` replaces the two columns for his own copies. The
read-back of step 4 is the `aws` CLI with the keys from `.env`.

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
4. Write `.env` at the top of the checkout, with one `NAME=value` line for each of the four
   variables below. `.gitignore` lists the file. Each command runs as
   `uv run --env-file .env datadesk ...`, so no session reads or prints the file.
5. Look at the bucket with the `aws` CLI the owner knows. No `wrangler` is needed. The keys
   reach the CLI through the environment and are never written to a profile, because
   `aws configure` stores them in a shared file and hard rule 8 keeps credentials in the
   environment. An empty listing with no error shows that the token works:

   ```bash
   uv run --env-file .env bash -c 'AWS_ACCESS_KEY_ID="$DATADESK_R2_ACCESS_KEY_ID" \
     AWS_SECRET_ACCESS_KEY="$DATADESK_R2_SECRET_ACCESS_KEY" AWS_DEFAULT_REGION=auto \
     aws s3 ls "s3://$DATADESK_R2_ARCHIVE_BUCKET" --endpoint-url "$DATADESK_R2_ENDPOINT_URL"'
   ```

   The read-back of the inventory uses the same form with `aws s3 cp`. S3-E checks the command
   on its first object before it relies on it.

The bucket stays private at step 3, so this plan drops the public address it first asked for.
Making the bucket public is a publishing decision, and it waits for the step that first needs
a public read. The bucket's name, the private bucket and the `.env` file are proposals that
the owner has not seen.

## Environment variables

`load_settings(environ)` reads these four and nothing else. The S3 adapter gives its client the
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

`Settings` keeps both key values out of its `repr`, and no command prints either one. Step 3
sets no User-Agent, because no `datadesk` command sends the City a request (shape 6).

CI runs on the fakes and reads no credential. The `ObjectStore` contract suite reads its target
from four variables of its own: `DATADESK_CONTRACT_S3_ENDPOINT_URL`,
`DATADESK_CONTRACT_S3_ACCESS_KEY_ID`, `DATADESK_CONTRACT_S3_SECRET_ACCESS_KEY` and
`DATADESK_CONTRACT_S3_BUCKET`. It skips its real half, with a message, when they are unset. The
MinIO run sets them to a local server with throwaway keys. A run against R2 sets them to a
scratch bucket and a real token, and only with the owner's go (open question B). So no test
writes to the archive bucket, and no test reads the four variables above.

## Risks to probe

1. **The City's server refuses a client that is not a browser** (facts 6 and 11). At step 3 no
   `datadesk` command sends the City a request. A real browser reads the City's files (fact
   12). The save to disk through Chrome worked on November 23, 2026 (fact 13).
2. **The owner's copies are not the City's current files** (fact 12, QPOS-Q32). None of the 14
   has the City's sha, so none is indexed (answer 5). A City file may also change between
   fact 12 and the save, and step 1 of "The saved folder" catches that.
3. **Page 1 prints the period twice**, once in the phrase and once as a bare date
   (`FY22_Q1.pdf`). `confirm_period` reads the `PERIOD ENDING` phrase alone (QCASH-Q05,
   QOBL-Q04). pdfplumber may break the phrase across lines or put U+00A0 in it (QOBL-Q02), so
   S3-C tests both, and S3-E runs the 21 real covers. The cover of FY2027 Q1 is known to
   fail (fact 14).
4. **A title, a cover and a URL can name different days** (fact 5, FY2026 Q3). The edition
   comes from the title. The old `reports_from_feed` mapped a title date by its month alone
   (`qcmr.py:145`), so a title dated March 30 read as Q3. Here such a title is a finding
   (shape 5).
5. **Conditional writes through boto3** (design line 2290, section 18.1). `IfNoneMatch="*"` and
   `IfMatch` on `put_object` must raise `PreconditionFailed` on MinIO and on R2, and the etag
   that `put` and `head` return must be the same string.
6. **The feed fixture is a recorded response** from July 28, 2026, two reports short of the
   feed today. S3-B cuts it from the old repo's recording, so the tests of S3-B to S3-D prove
   the rules on a real feed and not the count of 21. S3-E runs the feed saved on November 23,
   2026, with its 21 report links.
7. **The import pin and the socket block.** `import json` fails the purity test and
   `from json import loads` passes with a pin (design 11.1). The MinIO test needs the
   `enable_socket` marker, and a test over TLS needs `import ssl` at the top of the root
   `conftest.py` (`docs/progress.md`).
8. **S3-D is the largest pull request.** If its review finds the adapter and the command too
   much for one fix round, the owner may split it at `s3.py`.

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

1. The City then refused two plain values (fact 11), so this answer did not settle how the
   City's files arrive. Answer A below did.
2. The catalog entry has no last period end, so the feed's 21st report is fetched. Its cover
   cannot be read (fact 14), so it is rejected and not indexed at step 3. Open question D asks
   what he wants.
3. "Setting up R2" gives the steps. His answer gives no go for the contract suite on R2, so
   open question B asks again.
4. "The inventory" stands, with the three later details it names.
5. A held copy that differs is not indexed, and the pull request of S3-E lists it. All 14 of
   his copies differ (fact 12).
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

The session answered that it had recorded his choice, and that the runs with that string were
his to start. His words: "No i want you to do the fetching". The session then offered two ways
it could fetch. One was a real browser: it opens each City URL, saves the feed and the 21
reports to a folder, and `import-held` indexes them. It said that the save was untested, that
the plan's order would reverse and need a revision and a second Codex read, and that
`datadesk fetch` would not reach the City at step 3. The other was a plain User-Agent that the
City lets through. His words: "Fetch through a real browser".

What follows from answer A:

- The City's files reach step 3 through a real browser and a saved folder (shape 6, "The saved
  folder"). No `datadesk` command sends the City a request at step 3, and no User-Agent is set.
- The agents that build this repo do not send a browser's string to a server that refuses
  other clients, whoever asks. His first words, the string the old repo sends, are a note for
  step 13, where `watch` runs on a schedule that is his. The City's permission is his
  statement. No session has checked it.
- Three things differ from what he was shown, after facts 12 and 13.
  `datadesk fetch qcmr --saved` reads the folder, where he was told `import-held` would. His
  14 copies are not indexed, because none has the City's sha. The save through Chrome was
  done the same day (fact 13).

## Still open

**B. May the `ObjectStore` contract suite run once against a scratch bucket on R2?** A yes adds
a second bucket, `phillyledger-scratch`, to steps 2 and 3 of "Setting up R2". Without a yes,
MinIO and Cloudflare's page are the proof of the conditional writes. S3-E proves upload,
read-back and a repeat fetch on R2. It does not prove that R2 refuses an overwrite, because its
first run writes absent keys and its second run writes nothing. The scratch run alone proves
that: a second create with other bytes must raise `PreconditionFailed` and leave the first
bytes.

**D. What happens to FY2027 Q1?** He said yes to indexing it (answer 2). Its cover has no
text a program can read (fact 14), so `confirm_period` cannot confirm its period, and the later
steps cannot read its tables without OCR. The plan takes the choice that publishes nothing: at
step 3 the fetch rejects it, the index holds the 20, and each run reports the rejection. It
enters when a later step can read it, by OCR or by a note that records a person's reading of
the cover. The other choice is to build that note at step 3. He has not seen this question.

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

## Changes after the first review

Codex first read commit `39f8af3e`. These changes came later, from the owner's answers and
facts 10 to 13. Rows 4, 5 and 9 of the table above describe parts that are now gone. Codex
read these changes at commit `46acec4a` (next section).

- FY2027 Q1 is in, so the inventory and the index hold 21 rows (answer 2).
- The archive bucket is private at step 3, and `DATADESK_R2_ARCHIVE_PUBLIC_URL` is gone
  ("Setting up R2").
- The City's files come from a folder that a browser saved, through `http_saved.py` and
  `datadesk fetch qcmr --saved` (shape 6, answer A). No `datadesk` command sends the City a
  request.
- The live `Http` adapter, its User-Agent and its contract suite wait for step 13.
- `import-held`, `Held` and `plan_import` are gone, because none of the owner's 14 copies has
  the City's sha (fact 12).
- The inventory takes its sha from the saved file, beside the digest the browser computed, and
  its read-back is `aws s3 cp`.
- S3-E adds a note for step 13 to `docs/plan-notes.md`.

## Second Codex review

Codex read commit `46acec4a` on November 23, 2026, after the owner chose the browser route.
Its report is `.codex-review/step-03-plan-46acec4a.md`. It raised twelve findings, four as
blocking. Each was checked against the plan, the design or a run. All twelve held, and the plan
above is revised for each. None is disputed.

| # | Finding | How it was confirmed | What changed |
|---|---|---|---|
| 1 | C1 to C3 passed with FY2027 Q1 gone from both files, or with an extra index line, and C3 would fail after a later revision | The plan's own text, and design line 3483 | "Clauses": the test's list holds 21 ids, C2 and C3 compare pairs and not the current version, and S3-E prints an equality run |
| 2 | The saved folder's recipe left out the feed's own URL, so the first lookup would be a 404 | The plan's own text | "The saved folder" step 4, and S3-D runs the command through the folder adapter |
| 3 | C5 passed for a command that returns early on a filled index | The plan's own text, and design line 4560 | "Clauses": the call log, the listing digest and a third run with one more edition |
| 4 | The read-back used `aws configure --profile`, which writes the keys to a shared file | Hard rule 8 of `CLAUDE.md` | "Setting up R2" step 5: the keys reach `aws` through the environment, and the profile is gone |
| 5 | S3-B needed a feed recording while the plan said S3-A to S3-D need nothing from the City | The plan's own text, and `shasum` of the old repo's July recording | S3-B cuts its fixture from that recording, and a save by hand needs the owner's agreement |
| 6 | The fixture started at the floor, so no test saw the FY2022 cutoff | The plan's own text | S3-B keeps the last report before the floor, and S3-E asks for no report before FY2022 |
| 7 | A link to a URL that another edition holds got no fetch, so the alias check never ran | The plan's own text, and design line 3489 | Shape 5 skips a request by edition and URL, and S3-D runs the case through the command |
| 8 | QCASH-Q07 is about a cash page, and the whole report's cover agrees with its quarter | `QCASH.md` lines 263 to 266, and `tesseract` on `FY14_Q2.pdf` printed "DECEMBER 31, 2013" | Shape 8 and S3-C: no real note is predicted, and the cite is gone from the test |
| 9 | A superseded sha that is listed again would merge a URL and leave the wrong version current | The plan's own text, and design line 3488 | Shape 7 and S3-C: a `superseded_sha_relisted` rejection, with an A, B, A test |
| 10 | The contracts of two local adapters could be skipped with the real halves | The plan's own text, and `ci.yml` runs on push and pull request alone | S3-D: both run in CI, and CI skips the MinIO half alone |
| 11 | Two runs on R2 do not prove that `CreateOnly` refuses an overwrite | The plan's own text | "Still open" B: the claim is gone, and the scratch run is the proof |
| 12 | `shasum` with no flag prints a SHA-1 | `shasum --help` on this machine | "The inventory" step 4: `shasum -a 256` under `set -o pipefail` |

## Changes after the second review

These came after the revision that answers the second review. Codex has not read them.

- The owner connected Chrome, and the planning session saved the feed and the 21 reports. The
  saved folder exists, and "The saved folder" says how it was made and what S3-E does with it.
- FY2027 Q1 has no readable text (fact 14). At step 3 the fetch rejects it, and the tests of C1
  to C3 hold the 20 editions of the check. Open question D asks the owner.
