# QOBL: QCMR obligations (O-2) and personal services (O-3)

Datasets `qcmr_obligations` (table O-2) and `qcmr_personal_services` (table O-3). Both are sections of
one quarterly PDF, the Quarterly City Managers Report. Paths drop
`packages/gov-budget-etl/src/gov_budget_etl/`. Test paths are under `packages/gov-budget-etl/tests/`
unless they start with `packages/`. The checkout has no PDFs, so every page fact comes from config,
comments, tests, notebooks with saved outputs, release notes and audit records.

## 1. Documents

The QCMR is one PDF per fiscal quarter, listed on the City's financial reports page. That page is a
client-rendered document finder (post 151831). The "Quarterly City Managers Report" category holds one
document per quarter, and its title carries the quarter-ending date (`qcmr.py:48-53`). The same
category also lists one-page infographics with the same date, which are dropped by title
(`qcmr.py:382-385`). Revised attachments are appended after the original, and the last listing for a
quarter wins (`qcmr.py:393-395`, `tests/test_qcmr.py:165-179`).

Cadence is quarterly. Quarter ends map to Philadelphia fiscal quarters: September is Q1 and December
is Q2 of the next fiscal year, March is Q3 and June is Q4 (`qcmr.py:38-46`).

| Fact | Obligations (O-2) | Personal services (O-3) | Source |
|---|---|---|---|
| Editions in release 2026.07.31 | 73 | 39 | `docs/site/data/index.md:440`, `:459` |
| Coverage | FY2008 to FY2026 Q3 | FY2008 to FY2026 Q3 | same |
| Published values | 44,511 | 68,482 | same; notebook outputs |
| Pages in FY2026 Q4 (92-page report) | PDF pp. 21 to 22 | PDF pp. 23 to 29 | `docs/philly-source-monitoring-audit-2026-09-11.md:51-54` |
| Pages in sample editions | FY13 Q3: 2 pages, starts at printed p. 9 | FY14 Q4: at least 15 pages, printed p. 13 is cut p. 3 | `docs/investigations/unverified-row-audit/source-observations.json:26-28`, `config/layouts/qcmr-personal-services.yml:67-71` |

Personal services has far fewer editions than obligations. A September 2026 audit found that 39
historical quarters lack a personal-services PDF, five also lack obligations, and three lack positions
(`docs/philly-source-monitoring-audit-2026-09-11.md:92-99`). Which quarters have O-3 is not recorded in
the checkout. The audit's counts are each one higher than the release counts (40 versus 39, 74 versus
73, 76 versus 75); I could not explain the offset.

Scan or text layer is recorded nowhere per document. The engine runs several word sources and keeps
the one whose output yields the most assertions, then the most rows, then readiness, then a fixed
preference for `geometric` (`reconciliation_status.py:38-43`, `:393-434`). Indirect evidence:
obligations FY13 Q3 was read by `textract`; personal services FY14 Q4 by `geometric`
(`docs/investigations/unverified-row-audit/CASES.md:31-34`). FY11 Q4 personal services was "OCR'd"
(`config/layouts/qcmr-personal-services.yml:36-37`). The personal-services profile for FY08 to FY13 is
named `qcmr_personal_services_scan_era` (`config/layouts/qcmr-personal-services.yml:2`).

Pre-FY2022 section PDFs were cut by hand and carry no acquisition sidecar, so their URL and retrieval
date are null (`release-notes/data/2026.08.02.yml:103-105`). The automatic splitter covers FY2022 on
(`config/source_sync.yml:3`, `phila_source_sync.py:176-179`).

## 2. Tables

### O-2 obligations

A row is one General Fund appropriation line: a department, a department's own "Base" appropriation,
or a central appropriation administered by a department. The table ends with `TOTAL GENERAL FUND`
(`config/entities.yml:3248-3257`). The FY13 Q3 header reads "period ending March 31, 2013, General Fund"
(`source-observations.json:26`).

Nine value columns, whole US dollars, left to right (`config/semantics.yml:1305-1350`):

| # | Printed tag | Old role | Notes |
|---|---|---|---|
| 1 | Prior Year Actual | prior_year_final | value year = report FY minus 1 |
| 2 | YTD Target Plan | budget_estimate | |
| 3 | YTD Actual | fytd_actual | |
| 4 | YTD (Over) Under Target | increase_decrease | derived |
| 5 | Adopted Budget | budget_estimate | |
| 6 | Target Budget | budget_estimate | |
| 7 | Current Projection | budget_current_estimate | |
| 8 | Projection (Over) Under Adopted | increase_decrease | derived |
| 9 | Projection (Over) Under Target | increase_decrease | derived |

Three printed columns share `budget_estimate` and differ only by tag. That is a vocabulary limit of the
old design, not a document fact.

Row hierarchy is not settled by the evidence. The entity registry treats central lines such as
"Finance-Indemnities", "Public Property-SEPTA Subsidy" and "Fleet Management - Vehicle Purchases" as
distinct series with a parent department, "deliberately NOT aliases" (`config/entities.yml:3266-3353`).
The FY13 Q3 audit note says "Nested italic departmental components must not be double-counted with
bold parent totals" (`source-observations.json:27`). So O-2 likely prints bold department totals over
italic component lines in at least some eras. Size: about 95 rows in FY13 Q3 (Register of Wills is row
94, `CASES.md:32`). The release averages about 610 values per edition, which fits 65 to 70 rows of nine
columns.

### O-3 personal services

O-3 is a metric grid. Each department is a section row followed by the same three metric rows:
`Full-Time Positions`, `Class 100 Total Oblig./Approp.` and `Class 100 Overtime Oblig./Approp.`
(`config/entities.yml:4656-4664`). A row is (department section, metric). The row label alone never
identifies the row.

Sub-department blocks print beside their parents and are summed into them: OIT, MDO, OPS, Human
Services, Public Health, Streets and First Judicial District units
(`config/layouts/qcmr-personal-services.yml:100-111`). The table ends with a value-less `TOTAL GENERAL
FUND` row followed by the three citywide metric rows (`tables/totals.py:2841-2847`). On the last page
that citywide block sits in its own drawn box, below a run of footnotes the body columns do not span
(`config/layouts/qcmr-personal-services.yml:92-96`). Footnotes also appear mid-body: FY11 Q4 has a
Gasoline Funds footnote just above the Engineering Design block (`:36-38`).

FY14 Q4 had 52 parent departments in the citywide sum (`docs/code-review-fix-workorders-2026-08-01.md:577`)
and the citywide rows sit at stitched rows 329 and 330 (`config/layouts/qcmr-personal-services.yml:57`,
`:77`). That implies about 80 section blocks of four rows each.

Columns differ by form (`config/semantics.yml:1169-1304`):

| Form | Editions | Columns, left to right |
|---|---|---|
| In-year | Q1 to Q3, plus Q4 outside FY11 to FY25 | Year-End Actual (FY-3), Year-End Actual (FY-2), Unaudited Actual, YTD Target Plan, YTD Actual, YTD (Over) Under Target, Adopted Budget, Target Budget, Year-End Projection, Projection (Over) Under Adopted, Projection (Over) Under Target. 9 to 11 columns; the oldest prior years are optional. |
| Year-end | Q4 FY2011 to FY2025 | Year-End Actual (FY-3), (FY-2), (FY-1), Adopted Budget, Target Budget, Year-End Projection, Projection (Over) Under Adopted, Projection (Over) Under Target. 8 columns, no YTD block. |

Units change by row: `Full-Time Positions` is a position count, the Class 100 rows are whole USD,
under the same column headers (`config/semantics.yml:1189-1225`). The fiscal-year sub-columns are not
ruled, and a ruled-grid rebuild merges them (`config/page_types.yml:1053-1059`).

## 3. Format eras

| Era | Editions | What changes | Evidence |
|---|---|---|---|
| O-3 scan era | FY08 Q1 to FY13 Q4 | Sanitation prints as a standalone department; Streets equals its other five divisions. OCR damage in labels. | `config/layouts/qcmr-personal-services.yml:3-11`, `:36-38` |
| O-3 text era | FY14 on | Sanitation is a Streets division and is excluded from the citywide sum. | `:104-137` |
| O-3 year-end form | Q4 FY11 to FY25 | 8 columns, no YTD block, "Year-End Actual (FY-1)" replaces "Unaudited Actual". | `config/semantics.yml:1181-1188` |
| O-3 FY21 | FY21 | Section "Office of Children & Families / Human Services". | `config/entities.yml:937-938` |
| O-3 and O-2 FY26 | FY26 | Office of Public Safety appears with OPS-Base and OPS-Office of Prison Oversight sub-blocks. | `config/layouts/qcmr-personal-services.yml:108-111`, `config/entities.yml:2562-2580` |
| O-2 FY26 | FY26 Q1 to Q3 | Footnote markers "(3)" to "(10)" appended to labels; "Creative Philadelphia" names Arts and Culture. | `tests/test_entities.py:2377-2408` |
| O-2 FY18 | FY18 | Retired Office of Planning and Development prints beside new Planning & Development. | `config/entities.yml:1302-1305` |
| O-2 and O-3 FY08 | FY08 Q4 at least | Combined "City Rep. / Commerce" row or section. | `config/entities.yml:781-789`, `:4559-4568` |
| Acquisition | FY22 on | Splitter finds sections by TABLE code; older editions were cut by hand. | `config/source_sync.yml:3` |

The O-2 column set has a single profile for all 73 editions with exactly nine roles and a minimum of
nine (`config/semantics.yml:1317-1337`). Header verification is switched off for every role
(`:1345-1350`), so nothing shows that the nine columns are stable. The FY13 Q3 note mentions an
"original 898,000" for Board of Ethics (`source-observations.json:26`), which hints at an "Original"
rather than "Adopted" caption in that era. Not verified.

## 4. Finding the table

Today the splitter reads the first two non-empty lines of each page, collapses whitespace including
U+00A0, and looks for `TABLE <code>` (`qcmr.py:34`, `:166-180`). Codes compare exactly, so O-3 pages
never join O-2 (`tests/test_qcmr.py:101-107`). A section is the longest contiguous run of matching
pages, which drops a stray match such as a contents line (`qcmr.py:183-219`). The period comes from the
first "FOR THE PERIOD ENDING <Month D, YYYY>" phrase in the report (`qcmr.py:35-37`, `:258-267`). The
June 2026 report was split correctly by this rule without code changes (audit doc `:51-54`).

Inside a section the engine finds the table region by geometric consensus. For O-3 that consensus stops
at the footnotes and drops the citywide box, so `recover_trailing_total_box` rejoins a box drawn as a
wide top rule with at least two vertical rules, binned with the body's columns
(`parsers/geometric_backend.py:1052-1068`, `tables/region_detection.py:331-414`). The scan-era profile
does not set this flag.

Simplest reliable rule: locate pages by the printed TABLE code in the page header, require a
contiguous run, and confirm the period phrase. Inside the run, take every row from the first department
to the `TOTAL GENERAL FUND` block, and treat footnote text as non-table lines rather than as a region
boundary. For pre-FY2022 editions it is unknown whether the TABLE codes are printed.

## 5. Arithmetic that holds

| Relation | Declared today | Known source breaks |
|---|---|---|
| O-3 citywide metric row = sum of same metric over parent departments, sub-department blocks excluded | Yes, `metric_grid` (`tables/totals.py:2832-2907`) | FY14 Q4: citywide target variance omits OPA, 39 positions and 1,200,000 USD (2 cells) |
| O-3 Full-Time Positions sums are exact | Yes, `metric_grid_exact_labels` (`config/layouts/qcmr-personal-services.yml:13-14`, `:98-99`) | none known |
| O-3 Adopted minus Year-End Projection = Projection (Over) Under Adopted, on all three metric rows | Year-end form only (`config/semantics.yml:1171-1180`) | none known; S25 confirms one cell (`CASES.md:33`) |
| O-3 Streets = sum of its five non-Sanitation divisions, FY08 to FY13 | No; noted in a comment, "verified to the position in fy08/fy10/fy13 Q4" (`config/layouts/qcmr-personal-services.yml:3-7`) | none known |
| O-3 parent department = sum of its sub-department blocks | No. S26 notes the components have no local check (`CASES.md:34`) | unknown |
| O-2 TOTAL GENERAL FUND = sum of lines | Inferred by the generic engine, not declared | FY13 Q3: IAFF arbitration provision has no FY2012 value, so the prior-year sum is uncheckable (`CASES.md:31-32`) |
| O-2 and O-3 Target minus Projection = Projection (Over) Under Target; Adopted minus Projection = Projection (Over) Under Adopted; YTD Target minus YTD Actual = YTD (Over) Under Target | No (E08 noted this gap) | unknown |
| Cross-edition: Prior Year Actual or Unaudited Actual in FY N against Q4 of FY N minus 1; Adopted Budget constant within a fiscal year | No | unknown |
| Cross-table: O-3 Full-Time Positions against P-1 General Fund positions | No | unknown; timing and fund scope may differ |
| Cross-family: O-2 Adopted Budget against Budget in Brief; O-2 Prior Year Actual against the Supplemental Report | No | unknown |

Sign convention: "(Over) Under" is budget minus projection, positive when under budget
(`config/semantics.yml:1172-1180`). A related family shows the same publisher habit: QCMR positions
FY11 Q2 and Q3 also leave OPA out of the citywide total (scratch report C01, section 4).

Acknowledgment records:

| Dataset | Kind | Count | Editions |
|---|---|---|---|
| `qcmr_personal_services` | numeric_discrepancy | 2 | FY14 Q4 (`config/layouts/qcmr-personal-services.yml:51-91`) |
| `qcmr_obligations` | any | 0 | no layout profile matches O-2 |
| either | reviewed cells, resolved assertions, reconciliation.yml entries | 0 | grep of `config/` finds none |

Both personal-services records lack evidence and check fingerprints and are keyed to table index 1,
row index 329 or 330, column 8 and hypothesis `sum_of_same_label_items`. Neither dataset has an exact
Decimal release contract (`config/release_contracts.yml:4-6`).

## 6. Row labels and entities

The registry scopes 107 entities to O-2 (95 departments, 10 other, 2 rollups) and 75 to O-3 (74
departments, 1 other). 101 of the O-2 entities and 74 of the O-3 entities are shared with Budget in
Brief, Budget Detail or the Supplemental Report. Names plus aliases total 433 strings for O-2 and 340
for O-3, an upper bound on label variants because aliases are not family-specific. The FY26 Q3 release
saw 103 O-2 entities, 927 exact series and 16 unresolved labels (notebook
`quarterly_obligations_tracker.ipynb`, cell 3 output).

Label behavior the parser must expect:

- O-3 metric labels repeat in every section, so identity is (section, metric). Section names may match
  a department only through organization aliases such as "COMMERCE / AVIATION"
  (`config/entities.yml:4656-4664`).
- Central appropriations are separate series with a parent: 28 O-2 entities carry `parent_id`
  (`config/entities.yml:3266-3353`). "Managing Director-Base" and "Office of Public Safety-Base" are the
  department itself (`tests/test_entities.py:2411-2470`).
- Several labels can resolve to one department in one edition; the notebook sums them before pivoting
  (`quarterly_obligations_tracker.ipynb`, cell 6).
- Streets and Sanitation move between standalone and nested. "Streets - Sanitation" shows 297 internal
  absent series-editions in O-2 and 762 in O-3 (notebook outputs). Sanitation is again its own
  department with code 82 in FY2026 budget books (scratch report C02).
- Fairmount Park and Recreation merged into Parks and Recreation in FY2011 (`config/entities.yml`
  successions block).
- Combined "City Rep. / Commerce" is a rollup organization, not an atomic department
  (`tests/test_qcmr_positions_continuity.py:161-175`).

## 7. Values

O-2 is whole USD (`config/semantics.yml:1307-1316`). O-3 is whole USD for Class 100 rows and position
counts for Full-Time Positions. The unit is chosen by row label, under identical column tags
(`config/semantics.yml:1189-1225`, `tests/test_semantics.py:1952-1976`).

- Negative values: the ack text shows a printed -900,000 citywide variance, but whether negatives print
  with parentheses or a minus sign is not recorded.
- Blank cells exist and mean "no value": the IAFF row has no FY2012 value, and the audit says not to
  infer zero (`docs/investigations/unverified-row-audit/findings.json`, S23).
- Footnote marks fuse into labels: "Human Services (1)" (`config/entities.yml:934-935`), FY26 "(3)" to
  "(10)", and in scans "Full-Time Positions (1)" or "... Oblig./Approp. (*) Transfer ..."
  (`tables/totals.py:2820-2830`).
- OCR leaves marker-only or one-glyph section rows such as "2 4" or "I" (`tables/totals.py:57-66`).
- Value year comes from the column: FY minus 1, 2 or 3 for prior-year columns, else the report FY
  (`normalization.py:647-686`).

## 8. Editions and revisions

Every edition restates history. O-2 Prior Year Actual and O-3 Unaudited Actual repeat the previous
year in Q1 to Q3. The O-3 year-end form repeats three completed years. Adopted Budget repeats in all
four quarters of a year. The old code keeps every edition's value as its own row and picks no
canonical value. Analysts pick by hand: last edition per value year, or Q4 only
(`quarterly_obligations_tracker.ipynb` cell 5, `workforce_trends.ipynb` cell 11).

Reissues: the listing appends revised attachments, and the last one wins (`qcmr.py:393-395`). The
FY14 Q2 cash PDF duplicates Q3 content and prints "Projection as of March 31"
(`packages/gov-budget-data/src/gov_budget_data/data/report_editions.json`,
`release-notes/data/2026.08.02.yml:98-102`). Whether the O-2 and O-3 files for FY14 Q2 share that
defect is not recorded. The FY2025 Q3 report was missing and restored in release 2026.07.31
(`release-notes/data/2026.07.31.yml:13-30`).

## 9. Quirk ledger

| Id | What happens in the document | Old handling (`path:line`) | Kind |
|---|---|---|---|
| QOBL-Q01 | Sections are marked by "TABLE O-2" and "TABLE O-3" in the page header. | `qcmr.py:34`, `:72-76`, `:81-86` | inherent |
| QOBL-Q02 | Header band is the first two non-empty lines; U+00A0 spacing must be collapsed. | `qcmr.py:172-180` | unsure: settle by checking the header band on pre-FY22 pages |
| QOBL-Q03 | A code can appear outside its section (contents); keep the longest contiguous run. | `qcmr.py:183-219` | unsure: the test is synthetic and uses the cash title, not O-2 |
| QOBL-Q04 | Period is printed as "FOR THE PERIOD ENDING Month D, YYYY"; Sep and Dec belong to the next FY. | `qcmr.py:35-46`, `:126-163` | inherent |
| QOBL-Q05 | Listing mixes reports and same-dated infographics; revisions are appended. | `qcmr.py:382-395` | inherent |
| QOBL-Q06 | Listing date and printed period can disagree; acquisition fails on mismatch. | `phila_source_sync.py:49-58` | inherent |
| QOBL-Q07 | Split writes section PDFs before the period and completeness checks raise. | `phila_source_sync.py:54-58`, `qcmr.py:273-319` | artifact: cut PDFs |
| QOBL-Q08 | Page numbers in records refer to cut files, not the report. | `config/layouts/qcmr-personal-services.yml:67`, `:87` | artifact: cut PDFs |
| QOBL-Q09 | Pre-FY22 editions were hand-cut and have no source URL or retrieval date. | `release-notes/data/2026.08.02.yml:103-105` | artifact: no archive |
| QOBL-Q10 | Many quarters have no O-3; completeness by file existence flags 39 quarters. | `qcmr.py:399-408`; audit doc `:92-99` | unsure: settle by listing O-3 presence per report |
| QOBL-Q11 | Scan or text layer is not recorded; word source is chosen per document by assertion count. | `reconciliation_status.py:393-434` | artifact: multi-backend ranking |
| QOBL-Q12 | O-3 rows repeat three metric labels under each department section. | `config/entities.yml:4656-4664`; `tables/totals.py:2832-2847` | inherent |
| QOBL-Q13 | O-3 citywide block is a value-less TOTAL GENERAL FUND row plus three metric rows. | `tables/totals.py:2850-2898` | inherent |
| QOBL-Q14 | Sub-department blocks print beside parents and are inside them; 30 text-era and 29 scan-era exclusion patterns. | `config/layouts/qcmr-personal-services.yml:15-46`, `:104-137` | inherent need; the label glob list is an artifact of having no indent or typography rule |
| QOBL-Q15 | FY08 to FY13 Sanitation is standalone; FY14 on it is a Streets division. | `config/layouts/qcmr-personal-services.yml:3-11`, `:127` | inherent |
| QOBL-Q16 | FY26 Office of Public Safety is a bold parent with OPS-* sub-blocks. | `config/layouts/qcmr-personal-services.yml:108-111` | inherent |
| QOBL-Q17 | FY26 Sanitation may be standalone again, but the text-era list still excludes it. | `config/layouts/qcmr-personal-services.yml:127` | unsure: check the FY26 O-3 pages and the FY26 citywide check result |
| QOBL-Q18 | FY11 Q4 OCR reads the Engineering Design section row as the tail of a Gasoline Funds footnote. | `config/layouts/qcmr-personal-services.yml:36-38` | unsure: depends on whether FY11 has a text layer |
| QOBL-Q19 | Footnotes print mid-body and above the citywide box. | `config/layouts/qcmr-personal-services.yml:36-38`, `:92-95` | inherent |
| QOBL-Q20 | Citywide total sits in its own drawn box below footnotes on the last page. | `config/layouts/qcmr-personal-services.yml:92-96`; `parsers/geometric_backend.py:1052-1068`; `tables/region_detection.py:331-414` | inherent fact; the recovery step is an artifact of consensus region detection |
| QOBL-Q21 | A split drawing stream can expose only the top rule of the footer box. | `parsers/geometric_backend.py:784-797` | inherent |
| QOBL-Q22 | Scan-era profile does not recover the trailing box. | `config/layouts/qcmr-personal-services.yml:2-46` | unsure: settle on an FY08 to FY13 last page |
| QOBL-Q23 | O-3 fiscal-year sub-columns are not ruled. | `config/page_types.yml:1053-1059` | inherent |
| QOBL-Q24 | Footnote marks fuse into scanned metric labels; match by prefix. | `tables/totals.py:2820-2830` | inherent for OCR words |
| QOBL-Q25 | OCR promotes marker-only or one-glyph fragments to section rows. | `tables/totals.py:57-66` | artifact: OCR line grouping |
| QOBL-Q26 | Position counts must sum exactly; generic money tolerance gave 26.5 positions of slack. | `config/layouts/qcmr-personal-services.yml:13-14`, `:98-99`; `layouts.py:885-895`; work order `docs/code-review-fix-workorders-2026-08-01.md:577-582` | inherent need; the slack was an artifact of contributor-scaled tolerance |
| QOBL-Q27 | One column holds positions and dollars, chosen by row label. | `config/semantics.yml:1189-1225` | inherent |
| QOBL-Q28 | O-3 Q4 FY11 to FY25 uses an 8-column year-end form without YTD. | `config/semantics.yml:1169-1258` | inherent |
| QOBL-Q29 | Year-end pattern ends at fy25; FY08 to FY10 Q4 and FY26 Q4 fall to the in-year profile. | `config/semantics.yml:1186-1188` | unsure: settle on FY08 to FY10 Q4 and FY26 Q4 headers |
| QOBL-Q30 | Most recent completed year is "Unaudited Actual" in-year and "Year-End Actual (FY-1)" in Q4. | `config/semantics.yml:1242`, `:1284` | inherent |
| QOBL-Q31 | O-3 in-year column count varies 9 to 11; mapped right to left with leading extras as unknown. | `config/semantics.yml:1262-1288`; `semantics.py:1424-1442` | inherent variation; positional mapping is an artifact |
| QOBL-Q32 | `optional_roles: [unknown]` on O-3 is a no-op. | `config/semantics.yml:1287-1288` | artifact |
| QOBL-Q33 | Header verification is off for every O-2 and O-3 role, so `column_verified` is vacuous. | `config/semantics.yml:1252-1258`, `:1297-1304`, `:1345-1350` | artifact |
| QOBL-Q34 | O-2 reuses `budget_estimate` for three printed columns. | `config/semantics.yml:1318-1336` | artifact: shared role vocabulary |
| QOBL-Q35 | Adopted minus projection identity is declared only for the O-3 year-end form. | `config/semantics.yml:1171-1180` | artifact: identity tied to one era profile |
| QOBL-Q36 | FY14 Q4 citywide target variance omits OPA (-39 positions, -1,200,000 USD). | `config/layouts/qcmr-personal-services.yml:51-91`; `tests/test_qcmr_personal_services_source_acknowledgments.py:7-44` | inherent |
| QOBL-Q37 | Acks are keyed to table, row and column indexes and a hypothesis name, without fingerprints. | `config/layouts/qcmr-personal-services.yml:52-58`, `:72-78` | artifact |
| QOBL-Q38 | Metric checks could be dropped on the acknowledged retry; now re-appended. | `tables/reconcile.py:791-803`, `:962` | artifact |
| QOBL-Q39 | O-3 sub-department blocks have no parent-equals-sum check. | `CASES.md:34` | inherent need, unchecked |
| QOBL-Q40 | O-3 sections match departments only via organization aliases. | `config/entities.yml:4656-4664` | inherent |
| QOBL-Q41 | FY08 Q4 O-3 prints the combined "City Rep. / Commerce" section. | `config/entities.yml:4559-4568` | inherent |
| QOBL-Q42 | FY21 O-3 section "Office of Children & Families / Human Services". | `config/entities.yml:937-938` | inherent |
| QOBL-Q43 | Section headings can carry footnote markers. | `tests/test_resolution.py:2165-2200` (synthetic "Historic Office (7)") | unsure: confirm on FY26 O-3 |
| QOBL-Q44 | O-2 has no layout profile; its checks are inferred, never declared. | `config/layouts.yml:7-19`; `layouts.py:1408-1410` | artifact |
| QOBL-Q45 | O-2 is General Fund only and ends with TOTAL GENERAL FUND. | `config/entities.yml:3248-3257` | inherent |
| QOBL-Q46 | O-2 central appropriations print as own rows with a parent department. | `config/entities.yml:3266-3353` | inherent |
| QOBL-Q47 | O-2 may nest italic components under bold department totals. | `source-observations.json:27` | unsure: settle on FY13 Q3 and FY26 O-2 pages |
| QOBL-Q48 | FY26 O-2 labels carry markers "(3)" to "(10)"; some editions print the name without one. | `tests/test_entities.py:2377-2408`; `packages/gov-budget-data/tests/test_real_artifacts_optional.py:1133-1170` | inherent |
| QOBL-Q49 | FY18 O-2 prints old and new Planning offices side by side. | `config/entities.yml:1302-1305`; `tests/test_entities.py:2478-2489` | inherent |
| QOBL-Q50 | O-2 lists CPOC under the Managing Director. | `config/entities.yml:2601-2603` | inherent |
| QOBL-Q51 | FY26 Office of Prison Oversight label wraps across two underlined lines. | `config/entities.yml:2576-2580` | unsure: the comment may describe Budget in Brief, not O-2 |
| QOBL-Q52 | FY13 Q3 IAFF arbitration provision has no FY2012 value; blank is not zero. | `CASES.md:31-32` | inherent |
| QOBL-Q53 | O-2 and O-3 FY08 print combined "City Rep. / Commerce". | `config/entities.yml:781-789` | inherent |
| QOBL-Q54 | Several O-2 labels resolve to one department in one edition. | `quarterly_obligations_tracker.ipynb` cell 6 | inherent |
| QOBL-Q55 | Line-numbered recap labels ("1 First Judicial District", "24 First Judicial District"). | `config/entities.yml:852-855` | unsure: family not named; may be P-1 only |
| QOBL-Q56 | "(Over) Under" columns are budget minus projection. | `config/semantics.yml:1172-1180` | inherent |
| QOBL-Q57 | Value year is set by column role offsets. | `normalization.py:647-686` | inherent |
| QOBL-Q58 | No canonical edition rule; notebooks choose last edition or Q4. | notebooks cited in section 8 | inherent need |
| QOBL-Q59 | FY14 Q2 container may hold Q3 content. | `release-notes/data/2026.08.02.yml:98-102` | unsure: settle by reading the FY14 Q2 O-2 and O-3 period lines |
| QOBL-Q60 | Neither dataset has an exact Decimal release contract. | `config/release_contracts.yml:4-6` | artifact |

## 10. Old code that serves this family

| Job | File | Lines | Keep as code or as knowledge |
|---|---|---|---|
| Acquisition | `qcmr.py` | 435 | Code: period parsing, quarter mapping, TABLE code match, longest run, feed filter. Drop the PDF cutting. |
| Acquisition | `phila_source_sync.py:49-75`, `:176-185` | about 40 | Knowledge: promise check and FY2022 floor. |
| Acquisition | `commands/collections.py:29-115` | about 85 | Knowledge only. |
| Layout | `config/layouts/qcmr-personal-services.yml` | 137 | Knowledge: exclusion lists, Sanitation era, OPA source error. |
| Layout | `tables/region_detection.py:331-414` | 84 | Knowledge: the drawn-box shape; a clean region rule may not need it. |
| Checks | `tables/totals.py:2820-2907` | 88 | Code idea worth keeping: same-label block sum with exact count rows. |
| Checks | `tables/reconcile.py:791-803`, `:962` | about 15 | Knowledge only. |
| Semantics | `config/semantics.yml:1169-1350` | 182 | Knowledge: column lists, eras, unit by row, identity. |
| Entities | `config/entities.yml` (107 and 75 scoped entities, qualifiers, scoped alias) | about 1,000 shared | Data to migrate; shared with Budget in Brief and Budget Detail. |
| Tests | `tests/test_qcmr.py` | 336 | Code: the splitter and period tests port almost as is. |
| Tests | `tests/test_qcmr_personal_services_source_acknowledgments.py` | 44 | Knowledge: the two residuals. |
| Tests | `tests/test_entities.py:2377-2489`, `tests/test_qcmr_positions_continuity.py:161-175`, `tests/test_semantics.py:349-369`, `:1952-1976` | about 200 | Knowledge: label and era cases to re-express. |
| Notebooks | `quarterly_obligations_tracker.ipynb`, `workforce_trends.ipynb` | n/a | Knowledge: the user questions and saved outputs. |

## 11. The least a parser needs

Inputs: the archived full QCMR PDF and its period. Word source per edition, declared, not ranked.

Steps for O-2:
1. Find pages whose header band carries "TABLE O-2"; require one contiguous run.
2. Read words; find the nine value columns from the header captions; fail if the count is not nine.
3. Take rows from the first department to `TOTAL GENERAL FUND`; keep footnote lines out.
4. Record bold or italic and indent per row; assign parent totals and components from typography.
5. Strip trailing footnote markers into their own field; keep the printed label verbatim.
6. Type values as whole USD; blank stays null.

Steps for O-3:
1. Same page rule with "TABLE O-3"; allow footnotes inside the body.
2. Pick the form from captions: year-end (8 columns) or in-year (9 to 11). Bind each column by caption.
3. Group rows into blocks of section plus three metric rows. Mark sub-department blocks by typography
   or indent, else by the era's exclusion list.
4. Find the citywide block after the value-less `TOTAL GENERAL FUND`, including the drawn box on the
   last page.
5. Type Full-Time Positions as counts and Class 100 rows as USD.

Parameters that differ by era: O-3 form (in-year or year-end), number of prior-year columns,
whether Sanitation is a parent, the sub-department list (adds OPS in FY26), scan or text words.

Checks to declare:
- O-3 citywide metric = sum over parent departments, exact for positions.
- O-3 and O-2 per row: Adopted minus Projection, Target minus Projection, YTD Target minus YTD Actual
  against the printed deltas.
- O-3 parent block = sum of its sub-department blocks; FY08 to FY13 Streets = five divisions.
- O-2 TOTAL GENERAL FUND = sum of top-level lines, with blanks reported as missing operands.
- Cross-edition: Adopted Budget equal across one year's quarters; prior-year actual against the
  previous year's Q4.
- Carry the FY14 Q4 OPA record as a page-cited acknowledgment with pinned residuals.

## 12. Unknowns

- Which quarters have an O-3 section, and why the audit counts exceed the release counts by one.
- Whether pre-FY2022 editions print TABLE codes in the header band.
- Whether O-2 nests italic components under bold totals, and in which eras.
- How negatives, zeros and dashes print in either table.
- Whether O-2 columns ever differ from nine, given verification is off.
- Whether FY08 to FY10 Q4 and FY26 Q4 O-3 use the year-end form.
- Whether FY26 O-3 prints Sanitation as a parent, and whether the FY26 citywide check passed.
- Which editions are scans with no text layer.
- Whether the FY14 Q2 O-2 and O-3 files carry Q3 content.
- What O-1 and O-4 hold. The only code knowledge is one comment: "the obligations level summary
  (O-1/O-4)" is "not a pipeline family" (`qcmr.py:79-81`). No layout, semantics, entity or test touches
  them. The FY2026 Q4 report has pages 30 and 31 between O-3 and P-1 that no section claims; their
  content is unknown.
