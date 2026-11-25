# QPOS: QCMR positions (table P-1, dataset `qcmr_positions`)

Paths drop `packages/gov-budget-etl/src/gov_budget_etl/`. Tests are under
`packages/gov-budget-etl/tests/`. The checkout has no PDFs and no pipeline artifacts. Every
statement about the printed page comes from config, tests, docs, release notes and
acknowledgment text. Statements marked "inferred" are my reading of that evidence.

## 1. Documents

P-1 is one table inside the Quarterly City Managers Report (QCMR). It is never published alone.

- Publisher listing: the City's financial reports page, document-finder post 151831, category
  "Quarterly City Managers Report" (`qcmr.py:48-53`). One document per quarter. The title carries
  the quarter-ending date, and the URL cannot be rebuilt from the date (`qcmr.py:351-359`).
- The same category lists one-page infographics with the same date. They are skipped by title
  (`qcmr.py:382-385`).
- The City appends revised attachments after the original. The old code keeps the last listing
  per quarter (`qcmr.py:393-395`).
- Cadence: quarterly. Quarter ends Sep 30 (Q1), Dec 31 (Q2), Mar 31 (Q3), Jun 30 (Q4). September
  and December reports belong to the next fiscal year (`qcmr.py:38-46`).
- Corpus: 75 editions, FY2008 Q1 to FY2026 Q3, with no gaps
  (`tests/test_qcmr_positions_continuity.py:19-34, 85`). FY2025 Q3 was missing and was restored
  from the official report (`release-notes/data/2026.07.31.yml:14-30`).
- Automated acquisition starts at FY2022 (`config/source_sync.yml:3-6`). Older editions exist
  only as hand-cut sub-PDFs (`qcmr.py:426-428`). Completeness before 2022 is "unknown"
  (`config/admin.yml:18-20`).
- Size: the P-1 sub-PDF is 2 pages in the fixture and in FY2023 Q4 and FY2024 Q4, and 3 pages
  in FY2025 Q4 (712,350 bytes against 110,605 and 131,297)
  (`archive/documentation/assets/data/playground-sample.json`; `tests/test_qcmr.py:85-99`).
- Scans: no file in the checkout lists which editions have a text layer. The backend choice
  lives in a selection manifest that is a pipeline artifact (`tests/test_qcmr_positions_continuity.py:37-45`).
  Evidence by edition:
  - FY2008 Q2 and Q3 were read with `textract_geometric`
    (`docs/investigations/unverified-row-audit/CASES.md:35-36`).
  - OCR label damage appears in FY2008 Q1 through FY2014 Q1 ("Binance", "Stroets . Sanitation",
    "Hith") (`tests/test_qcmr_positions_continuity.py:89-149`).
  - FY2023 Q4, FY2024 Q4 and FY2025 Q4 were read from the text layer (`geometric`)
    (`playground-sample.json`).
  - Inferred: FY2008 to about FY2014 are scans. The boundary is not recorded.

## 2. Tables

There is one table per edition. It is a list of departments with ten count columns.

**Columns.** The value grid is three fund triplets plus one variance column. Roles are assigned
right to left (`config/semantics.yml:2516-2538`).

| Col | Printed meaning (from ack text and header templates) | Old role, tag |
|---|---|---|
| 1 to 3 | FY-1 Year-End Actual: General, Other, Total | `prior_year_final`: General Fund, Other Funds, All Funds |
| 4 to 6 | FY Adopted Budget: General, Other, Total | `budget_estimate`: same tags |
| 7 to 9 | Month End Actual at quarter end: General, Other, Total | `month_actual`: same tags |
| 10 | (Over) Under Budget | `remaining_estimate`, no tag |

Column 0 is the label. A real fact row confirms column 9 is quarter-end All Funds
(`playground-facts.json`, `column_index: 9`). The ack text uses "Month End Actual",
"Year End Actual", "FY2008 adopted", "current positions" and "budgeted positions"
(`config/layouts/qcmr-positions.yml:16-19, 49-52, 176-179`). The quarter-end count is a point in
time at the report date (`packages/gov-budget-data/src/gov_budget_data/data/temporal_contracts.json`,
`philadelphia_qcmr`).

General Fund and Other Funds are column groups, not row blocks. Every row in every edition has
all three tags under all three roles (`tests/test_qcmr_positions_continuity.py:323-332`). No
"Total General Fund" row exists in config for this family.

**Rows.** About 61 printed rows per edition: 4,585 logical rows across 75 editions
(`tests/test_qcmr_positions_continuity.py:285-286`). 4,585 times 10 is 45,850, less 12 blank
cells, gives 45,838 values (`dataset-catalog.json`, `n_rows`).

| Row kind | Examples | Count per edition |
|---|---|---|
| Department line | Aviation, City Treasurer, Public Health | most rows |
| Parent total | District Attorney Total, Fire Total, Police Total | 3 |
| Component | Civilian, Uniform under each parent | 6 |
| Grand total | TOTAL ALL FUNDS | 1, last page |

Hierarchy has two levels. The parent prints above its two components. Order is alphabetical by
department, so Prisons follows Police's components (`config/layouts/qcmr-positions.yml:5-8`;
in FY2023 Q4, Fire Total is row 23 on page 1, Police Total row 54 and Public Health row 59 on
page 2, `playground-facts.json`).

**Multi-page.** The table runs across 2 pages (3 in FY2025 Q4). TOTAL ALL FUNDS is on the last
page and sums rows from every page (`config/layouts/qcmr-positions.yml:20-36`). The old pipeline
stitches the pages into one table: one classification file per edition, table index 1
(`tests/test_qcmr_positions_continuity.py:431-432`).

## 3. Format eras

Config knows one column layout for all 75 editions: one semantics profile with ten columns
(`config/semantics.yml:2467-2557`) and one effective layout rule (`qcmr-positions.yml:228-232`).
The eras below are about labels, scans and acquisition.

| Era | Editions | What changes | Evidence |
|---|---|---|---|
| Scan, OCR labels | FY2008 Q1 to about FY2014 Q1 | Damaged labels, leading digit or "I" prefixes | continuity test `:89-149`; `entities.yml:4588-4608` |
| City Rep. / Commerce combined row | 4 editions in FY2008 | One combined row in place of two departments | continuity test `:541-550`; `entities.yml:781-789` |
| Fairmount Park and Recreation separate | early editions, end not recorded | Later Parks and Recreation | `phl_dept_fairmount_park`, `phl_dept_recreation` are in scope (`qcmr_*`) |
| OPA appears | from FY2011 Q2 | 134 current, 0 budgeted in FY2011 Q2 | `qcmr-positions.yml:176-179` |
| FY2010 blank variance | FY2010 Q1 to Q4 | Column 10 blank for 3 offices | continuity test `:443-452` |
| "Streets" is the department | FY2008 to FY2013, FY2026 | Separate from Sanitation | `entities.yml:1545-1550` |
| No bare "Streets" label | FY2014 to FY2017 | Not recorded | inferred from 27 + 32 + 16 = 75 |
| "Streets" is Streets plus Sanitation | FY2018 to FY2025 | Same ink, wider scope | `entities.yml:1557-1565`; continuity `:551-555` |
| Text layer | FY2023 Q4 onward at least | `geometric` backend | `playground-sample.json` |
| Automated split by "TABLE P-1" | FY2022 onward | Header code anchors the split | `qcmr.py:79-86`; `source_sync.yml:3` |
| 3-page sub-PDF | FY2025 Q4 | One extra page, 5x size | `playground-sample.json` |

Parent label style varies: "Police Total", "Police - Total", "Fire Total", "Fire - Total",
"District Attorney - Total" all occur, including both styles in FY2008 Q2
(`qcmr-positions.yml:45`; continuity test `:204, 353`).

## 4. Finding the table

Today pages are found by cutting. For FY2022 on, `split_report` reads the first two non-empty
lines of each page and keeps the longest contiguous run whose header has `TABLE P-1`
(`qcmr.py:166-219`). Before FY2022 the sub-PDFs were cut by hand. Inside the sub-PDF the whole
page is the table.

Simplest reliable rule under the "no cut PDFs" decision:

1. Find the pages whose header band reads `TABLE P-1`, take the longest contiguous run.
2. On each page, the table runs from the column header block to the last department row. On the
   last page it ends at `TOTAL ALL FUNDS`.
3. Require exactly one `TOTAL ALL FUNDS` and exactly one Police parent.

Not verified: whether editions before FY2022 print `TABLE P-1`. If not, scans need a title
anchor or a page range per edition. Every acknowledgment page number today is a sub-PDF page
(`qcmr-positions.yml:22-24`) and every `source_sha256` is the sub-PDF's hash, so all seven must be
remapped to whole-report pages.

## 5. Arithmetic that holds

All arithmetic is exact integer arithmetic. A one-position residual is evidence, never rounding
(`config/layouts/qcmr-positions.yml:4`; `layouts.py:890-896, 1628-1629`; `tables/checks.py:72-77`).

| Relation | Scope | Source breaks it | Evidence |
|---|---|---|---|
| General + Other = Total, per role | every row, 3 roles | 20 residual cells, all FY2008 or FY2011 | continuity `:343-369` |
| Adopted Total minus Actual Total = (Over) Under | every row with a variance | 3 rows, all FY2008 Q2 | continuity `:402-406` |
| Civilian + Uniform = parent | DA, Fire, Police, all 10 columns | 2 cells, both FY2008 Q2 | continuity `:509-521` |
| Police check holds in all 750 cells | 75 editions x 10 | 0 | continuity `:227-228` |
| Department and parent rows sum to TOTAL ALL FUNDS | columns 1 to 9 | FY2008 Q1 to Q4, FY2008 Q2 FY2007, FY2011 Q2, Q3 | `qcmr-positions.yml` |
| Fund columns are non-negative | all | 0 | continuity `:414-416` |
| Variance column on a total follows its row identity, not a column sum | TOTAL ALL FUNDS | needed because of FY2010 blanks | `tables/checks.py:1211-1217` |

Components must be excluded from the vertical sum. The parent is the contributor.

Cross-edition relations that should hold but are not checked anywhere today:

- The FY adopted column repeats in all four quarters of a fiscal year. The FY2008 -9 defect
  repeats in all four FY2008 editions, which fits a copied column.
- The FY-1 year-end actual repeats in all four quarters.
- Q4 quarter-end actual against next year's FY-1 year-end actual. Unknown whether these agree.
- Personal services (O-3) prints "Full-Time Positions" per department. Agreement with P-1 is not
  configured (`/home/claude/scratch/reports/E10.md:169`).

**Acknowledgment records: 7, all numeric source errors, all on TOTAL ALL FUNDS or DA.**

| Edition | Row | Residuals | Kind | Fingerprints |
|---|---|---|---|---|
| FY2008 Q1 | TOTAL ALL FUNDS | -9 adopted, -3 actual | publisher arithmetic | none |
| FY2008 Q2 | District Attorney - Total | +100 FY2007 All Funds | publisher arithmetic | both |
| FY2008 Q2 | TOTAL ALL FUNDS | +10, -9, -4 | publisher arithmetic | none |
| FY2008 Q3 | TOTAL ALL FUNDS | -9, -4 | publisher arithmetic | none |
| FY2008 Q4 | TOTAL ALL FUNDS | -9, -6 | publisher arithmetic | none |
| FY2011 Q2 | TOTAL ALL FUNDS | -134 actual | publisher omission (OPA) | none |
| FY2011 Q3 | TOTAL ALL FUNDS | -138 actual | publisher omission (OPA) | none |

Source: `config/layouts/qcmr-positions.yml:2-227`; `tests/test_qcmr_positions_source_acknowledgments.py:14-20`.
These 7 records hold 12 residual values. That is the "twelve reviewed fund residuals" of the
release note (`release-notes/data/2026.07.31.yml:164-167`). Six of seven lack the two
fingerprints that `can_cover_live_assertions` needs (`layouts.py:214-231`), so they cannot
authorize a live check.

**Unacknowledged failures.** FY2008 Q2 has 8 more fund residuals and 3 variance residuals with no
record (continuity `:352-362, 402-406`). The old pipeline publishes those cells with
`value_verified` false (continuity `:335-340`), yet the catalog counts all 45,838 values as
trusted. Under the new rule these 11 failures block the release until someone reviews the page.
Each one localizes to a single All Funds cell, because two identities agree on it. Example: City
Planning budget All Funds is 10 high against both General + Other and the variance.

Related outside this family: personal services FY2014 Q4 also leaves OPA (39 positions) out of a
citywide variance (`tests/test_qcmr_personal_services_source_acknowledgments.py:11-14`).

## 6. Row labels and entities

76 registry entities can resolve in a positions edition: 74 scoped `qcmr_positions_*` (or an era
pattern) plus Fairmount Park and Recreation scoped `qcmr_*`. Count from `config/entities.yml`. The
distinct printed label count is not recoverable without artifacts.

- Aliases are shared across QCMR, Budget in Brief, budget detail and supplemental reports, and
  mix spelling variants with OCR damage ("Atwater Kent Musoum" `entities.yml:596`, "Binance"
  `:811`, "I Records" `:1484`, "27 Recreation" `:2551`, "Capital Program Office, Mayor-" `:2633`).
- Footnote mark in a label: "Human Services (1)" (`entities.yml:933-935`).
- Civilian and Uniform are qualifiers of the preceding total, with OCR variants "I Civilian",
  "23 Civilian", "24 Civilian", "26 Civilian", "I Uniform", "26 Uniform" (`entities.yml:4588-4608`).
  "I Uniform" occurs in FY2011 Q4 and FY2013 Q3 (continuity `:229-232`).
- Scope changes kept as separate series: "City Rep. / Commerce" rollup in 4 editions; "Streets"
  department in 27 editions and Streets plus Sanitation rollup in 32 (continuity `:544-555`).
- Renames and merges visible in aliases: Board of Revision of Taxes to Office of Property
  Assessment; Personnel to Office of Human Resources; Information Services and Division of
  Technology to Office of Innovation and Technology; Emergency Shelter and Supportive Housing to
  Office of Homeless Services; Fairmount Park and Recreation to Parks and Recreation.
- The grand total resolves to `phl_positions_all_funds_total` (`entities.yml:3258-3264`).
- Same departments appear in QCMR obligations, personal services, Budget in Brief, budget detail
  (positions schedules) and supplemental reports. Most positions entities list all of these
  families.

## 7. Values

- Unit: positions, multiplier 1 (`config/semantics.yml:2549-2557`).
- Integers only (continuity `:413`). Counts of 1,000 or more print with commas ("29,346").
  Counts under 1,000 print bare ("11", "0", "134").
- Negative values only in column 10, in accounting parentheses: "(134)"
  (`qcmr-positions.yml:179-180`).
- Blank: 12 publisher-blank cells, column 10 of three offices in FY2010 Q1 to Q4 (Mayor - Office
  of Arts and Culture, Mayor - Office of the Inspector General, Office of Human Resources).
  They stay null (continuity `:443-452`).
- No dashes, N/A or percents are recorded for this family.
- Bare integers are the hazard. Three old paths mishandle them:
  - `parse_amount("12 345")` joins two tokens into 12345 when neither has a comma or point
    (`tables/amounts.py:54-65, 123`).
  - A bare integer within the merge tolerance welds into the label phrase
    (`tables/line_grouping.py:15-23`).
  - The orphan-line merge drops displaced bare integers, because only grouped or decimal words
    count as table amounts (`tables/line_repair.py:250-253`).
  These are code paths read in the source. I found no record of a positions cell lost this way.
- OCR digit damage is likely in scans. The exact-count recovery strategies exist for it
  (`tables/numeric_value_recovery.py:636, 800`; `tables/reconcile.py:502-545`).

## 8. Editions and revisions

- Each edition restates FY-1 actuals and the FY adopted budget. The same number is printed up to
  four times. The old code keeps every edition's value as its own observation; there is no
  canonical-value rule across editions.
- Corrected reissues: the listing can carry a revised attachment after the original. The old
  rule keeps the last one per quarter (`qcmr.py:393-395`). Whether any P-1 changed in a reissue
  is unknown.
- One full report yields four sub-documents (cash, obligations, personal services, positions)
  (`config/admin.yml:17`; `release-notes/data/2026.07.31.yml:21-25`).
- QCMR cash FY2014 Q2 prints the Q3 cutoff date
  (`packages/gov-budget-data/src/gov_budget_data/data/report_editions.json`). Whether the
  positions table in that report has the same problem is unknown.

## 9. Quirk ledger

| Id | What happens in the document | Old handling (`path:line`) | Kind |
|---|---|---|---|
| QPOS-Q01 | Ten count columns: three fund triplets plus one variance | `config/semantics.yml:2517-2538` | inherent |
| QPOS-Q02 | Columns mapped right to left by count; printed headers not verified (`verify_templates` empty) | `config/semantics.yml:2516, 2544-2548`; `semantics.py:1090-1096` | unsure: check header legibility on text-layer and scan editions |
| QPOS-Q03 | Counts add exactly; no rounding allowance | `qcmr-positions.yml:4`; `layouts.py:1628-1629`; `tables/checks.py:72-77` | inherent |
| QPOS-Q04 | One rule copied into 7 profiles to carry 7 acknowledgments | `qcmr-positions.yml:1-232`; `config/layouts.yml:1-3` | artifact: first-match-wins registry, acks stored in layouts |
| QPOS-Q05 | Police parent prints above Civilian and Uniform; Prisons follows | `qcmr-positions.yml:5-8`; `tables/reconciliation_rows.py:273-330` | inherent; the "until Prisons*" stop depends on alphabetical order |
| QPOS-Q06 | DA and Fire print the same parent-above-components shape but are not declared; found by `sum_of_next_k_items` search and re-kinded at resolution | `tables/totals.py:2097-2117`; `resolution.py:1902-1943`; `entities.yml:4588-4608` | artifact: inferred total scopes |
| QPOS-Q07 | A footnote mark can drag a child's left edge left of its parent, so indent cannot mark children | `tables/totals.py:2100-2105` | inherent |
| QPOS-Q08 | Civilian and Uniform labels carry OCR prefixes ("I", "23", "24", "26") | `entities.yml:4588-4608` | inherent in scans |
| QPOS-Q09 | OCR-damaged department labels in scans | aliases, e.g. `entities.yml:596, 811, 1148, 1484, 2551` | inherent in scans |
| QPOS-Q10 | Leading numbers on labels ("1", "2", "5", "23", "24", "25", "27") | aliases, e.g. `entities.yml:2550-2551` | unsure: margin text or OCR noise; settle by rendering FY2008 Q4 and FY2014 Q1 |
| QPOS-Q11 | Footnote mark in a label: "Human Services (1)" | `entities.yml:933-935` | inherent |
| QPOS-Q12 | "Streets" means the department or Streets plus Sanitation by era | `entities.yml:1545-1565`; continuity `:551-555` | inherent |
| QPOS-Q13 | Combined "City Rep. / Commerce" row in 4 FY2008 editions | `entities.yml:781-789`; continuity `:541-550` | inherent |
| QPOS-Q14 | Department renames and merges across 19 years | `entities.yml` aliases | inherent |
| QPOS-Q15 | TOTAL ALL FUNDS on the last page sums rows from all pages | `qcmr-positions.yml:20-36` | inherent |
| QPOS-Q16 | FY2008 Q1 to Q4: adopted total 29,346 for 29,355 (-9); actual -3, -4, -4, -6 | `qcmr-positions.yml:10-38, 76-165` | inherent (publisher) |
| QPOS-Q17 | FY2008 Q2: FY2007 total +10; DA total 635 for 535 (+100) | `qcmr-positions.yml:44-97` | inherent (publisher) |
| QPOS-Q18 | FY2011 Q2 and Q3: total omits OPA's 134 and 138; variance proves it | `qcmr-positions.yml:166-227` | inherent (publisher) |
| QPOS-Q19 | FY2008 Q2: 8 fund residuals and 3 variance residuals, no acknowledgment, published unverified | continuity `:352-362, 402-406` | unsure: publisher or Textract; render FY2008 Q2 pages 1 and 2 |
| QPOS-Q20 | FY2008 Q2: Fire budget General Fund total minus components is +1 | continuity `:515-519` | unsure: same evidence as Q19 |
| QPOS-Q21 | FY2010: column 10 blank for 3 offices, 12 cells | continuity `:420-452` | inherent |
| QPOS-Q22 | Variance on a total row is checked by row identity, not by column sum | `tables/checks.py:1211-1217` | inherent (follows from Q21) |
| QPOS-Q23 | Ack column indices shift by one between editions ([6, 9] vs [4, 7, 10] vs [7, 10]) | `qcmr-positions.yml:30-32, 64-65, 93, 123-125, 189-190` | artifact: backend cell grids (Textract adds a column, inferred) |
| QPOS-Q24 | 6 of 7 acks lack fingerprints and cannot cover live checks | `layouts.py:214-231`; `config/layouts.yml:5` | artifact: unfinished fingerprint migration |
| QPOS-Q25 | Acks pin engine hypothesis names that differ by edition for the same row | `qcmr-positions.yml:38, 71, 97, 131` | artifact: hypothesis search |
| QPOS-Q26 | Exact-count mode turns on digit-confusable repair, one-digit identity repair and near-consensus identity inference | `tables/reconcile.py:502-545`; `tables/reconciliation_columns.py:1121`; `tables/numeric_value_recovery.py:636, 800` | artifact: inference and value repair; forbidden now |
| QPOS-Q27 | Bare-integer counts: space join, label weld, orphan drop | `tables/amounts.py:54-65, 123`; `tables/line_grouping.py:15-23`; `tables/line_repair.py:250-253` | artifact (money-first parser); the bare-integer print is inherent |
| QPOS-Q28 | Fund identities declared twice, as accounting and as value identities | `config/semantics.yml:2469-2515` | artifact: two check systems |
| QPOS-Q29 | Components must be published as their own series, marked so nobody sums them | `layouts.py:811-821`; `export.py:1243-1244` | inherent need; flag mechanism is artifact |
| QPOS-Q30 | Split anchor `TABLE P-1` only for FY2022 on; older sub-PDFs hand-cut | `qcmr.py:79-86, 426-428`; `config/source_sync.yml:3` | unsure: do old editions print P-1 |
| QPOS-Q31 | Ack pages and hashes refer to cut sub-PDFs | `qcmr-positions.yml:21-24`; `qcmr.py:296-316` | artifact: cut PDFs |
| QPOS-Q32 | Revised attachment listed after the original | `qcmr.py:393-395` | inherent |
| QPOS-Q33 | Infographics share the listing category | `qcmr.py:382-385` | inherent |
| QPOS-Q34 | Fiscal quarter from period-ending date; Sep and Dec belong to next FY | `qcmr.py:38-46, 126-149` | inherent |
| QPOS-Q35 | FY2025 Q4 sub-PDF is 3 pages and 5 times the size | `playground-sample.json` | unsure: extra page or image content; open the PDF |
| QPOS-Q36 | Quarter-end count is a point-in-time value stored as `month_actual` | `config/semantics.yml:2542`; `temporal_contracts.json` | inherent meaning; role name is artifact |
| QPOS-Q37 | Parent labels print as "X Total" or "X - Total", both in one edition | continuity `:204`; `qcmr-positions.yml:45` | inherent |
| QPOS-Q38 | The FY2027 Q1 report (`qcmr-2026-09-30.pdf`, sha `640068cb...f365`, uploaded November 16, 2026) has pages with no text a program can read, the cover among them, and pages with such text. On pages 1 and 2, `pdftotext -f N -l N -layout` prints only shifted glyph codes. The third line of the cover prints as `)25^C7+(^C3(5,2'^C(1',1*^C6(37(0%(5^C^V^S^O^C^U^S^U^Y` (control bytes shown by `cat -v`), and page 1's text holds no `PERIOD ENDING`. Each of the two pages has two fonts, `TimesNewRomanPS-BoldMT` and `TimesNewRomanPSMT`, each CID TrueType with `Identity-H` and no Unicode map (`pdffonts -f N -l N`). On page 10, the title lines and the amounts print as shifted codes, and the row labels and column heads print as text. Page 6, whose text fonts are TrueType `WinAnsi`, prints "For the Period Ending September 30, 2026", and page 50 prints a table of performance measures. The step 3 planning session read pages 1, 2 and 10 with pdfplumber, which returned `(cid:38)` codes, and Tesseract on the cover image read "FOR THE PERIOD ENDING SEPTEMBER 30, 2026" (`docs/plans/step-03.md`, fact 14). The step 3 cleanup read pages 1, 2, 6, 10 and 50 with `pdftotext` and `pdffonts` (November 25, 2026). No run has sorted the other 87 of its 92 pages | None. The old repo never held this file. Its last commit, `22f355d` of November 12, 2026, is older than the upload, and `rg -uu` over its tree finds neither the upload stamp `20261116163840` nor the sha | inherent |

## 10. Old code that serves this family

| Job | File | Lines | Keep as code or knowledge |
|---|---|---|---|
| Acquisition | `qcmr.py` | 435 | Code: listing parse, quarter mapping, `TABLE P-1` page run. Drop the cutting. |
| Acquisition | `phila_media.py` | 932 | Code for the feed reader, shared by all QCMR. |
| Layout | `config/layouts/qcmr-positions.yml` | 233 | Knowledge: one rule and seven acks. |
| Semantics | `config/semantics.yml:2467-2557` | 91 | Knowledge: column map and identities. |
| Entities | `config/entities.yml` | 76 entities, 2 qualifier rules | Knowledge, and the alias lists as data. |
| Checks | `tables/reconciliation_rows.py:273-330` | 58 | Knowledge: parent-above-components. |
| Checks | `tables/totals.py:2097-2117` | 21 | Knowledge only: the footnote indent fact. |
| Checks | `tables/reconcile.py`, `numeric_value_recovery.py` exact paths | about 300 | Neither: value repair is out. |
| Values | `tables/amounts.py` | 278 | Code with a count mode that refuses space-joined bare integers. |
| Tests | `test_qcmr_positions_continuity.py` | 556 | Knowledge: the expected residual sets, 12 blanks, 750 Police cells, scope counts. Becomes declared checks plus corpus tests. |
| Tests | `test_qcmr_positions_source_acknowledgments.py` | 134 | Knowledge: the seven records. |
| Tests | `test_qcmr.py` | 336 | Code: split and feed tests carry over. |
| Use | `notebooks/workforce_trends.ipynb` | 1,780 | Knowledge: the consumer shape (citywide total, Police components, vacancies). |

No positions-specific Python exists in the engine; every behavior comes from generic code switched
on by config (`grep qcmr_positions` in `src` finds nothing).

## 11. The least a parser needs

Inputs: the whole QCMR PDF, its SHA-256, the edition's fiscal year and quarter.

1. Find the P-1 page run (section 4). Fail if none.
2. On each page, read words. For scans, read archived Textract words.
3. Find the ten value column bands from the header block. Assign columns left to right by the
   fixed order in section 2. Require exactly ten bands.
4. Group words into rows. Label is the text left of column 1. In count mode, never join two
   bare integers and never weld a number into a label.
5. Concatenate page rows in page order. Drop repeated headers.
6. Classify rows: `TOTAL ALL FUNDS` is the grand total. A label ending in "Total" is a parent.
   The next two rows labelled Civilian and Uniform are its components. All else are department
   lines.
7. Parse cells as exact integers. Parentheses mean negative, column 10 only. Blank stays null.
8. Resolve labels to entities with era-scoped aliases (Streets, City Rep. / Commerce).
9. Emit one row per department per edition, with ten typed columns and a page box per cell.

Parameters that differ by edition: page run, scan or text layer, alias era. Nothing else is
known to vary.

Checks to declare, all exact:

- Per row, for each of the three roles: General + Other = Total.
- Per row with a variance: Adopted Total minus Actual Total = (Over) Under.
- DA, Fire, Police: Civilian + Uniform = parent, all ten columns.
- Columns 1 to 9: department lines plus parent totals = TOTAL ALL FUNDS. Components excluded.
- Column 10 on TOTAL ALL FUNDS: row identity only.
- Exactly one TOTAL ALL FUNDS, exactly one of each parent, two components each.
- Fund columns non-negative.
- Optional, across editions: adopted and FY-1 actual columns equal across the four quarters of
  a fiscal year.

Acknowledgments to carry: the seven records, re-pointed to whole-report pages, plus whatever the
FY2008 Q2 review finds for its 11 open failures.

## 12. Unknowns

- Which editions are scans. The selection manifest is not in the checkout.
- Whether editions before FY2022 print `TABLE P-1` in the page header.
- Printed header wording per era, and whether it is legible enough to verify columns.
- Whether the FY2008 Q2 residuals (Q19, Q20) are publisher errors or Textract misreads.
- Why FY2025 Q4 is three pages.
- What FY2014 to FY2017 print in place of "Streets", and what FY2026 prints for Sanitation.
- Which four editions carry "City Rep. / Commerce", and when Fairmount Park and Recreation merge.
- The origin of numeric label prefixes ("23 Civilian", "27 Recreation").
- Whether the four-quarter repeats of adopted and FY-1 columns agree, and whether Q4 actuals
  match the next year's FY-1 actuals.
- Whether any reissued report changed P-1 values.
- Whether the FY2014 Q2 report's cutoff problem in cash also affects P-1.
