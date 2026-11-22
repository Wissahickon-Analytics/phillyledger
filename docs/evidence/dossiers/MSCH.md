# MSCH: Monthly School District revenue collections

Dataset `collections_monthly_school`. One PDF per month, "School District of Philadelphia, Comparative Statement of Net Revenue Collections". Paths below drop `packages/gov-budget-etl/src/gov_budget_etl/` and cite the checkout at commit 49b59ea. Nothing here was checked against a PDF, because the checkout holds none.

## 1. Documents

**Publisher listing.** The City posts one page per fiscal year at `https://www.phila.gov/documents/fy-{FY}-school-district-monthly-revenue-collections/`. The page is server-rendered HTML and each month is a `www.phila.gov/media/<digits>/...pdf` link (`revenue_collections.py:38-39, 296-316, 383-392`). A link belongs to the School series when its filename contains both "school" and "collection" (`revenue_collections.py:312-316`). When a month has several links, the last one wins (`revenue_collections.py:360-379`).

**Filename years are not reliable.** The publisher has named some July and August School PDFs with the fiscal year instead of the calendar year. The code therefore derives the calendar year from the listing page's fiscal year, not the filename (`revenue_collections.py:373-378`; test `test_revenue_collections.py:88-93`).

**Cadence and count.** Monthly. The real-artifact test expects every month from 2014_07 to 2026_05, which is 143 ids (`gov-budget-data/tests/test_real_artifacts_optional.py:466-482`). Release `2026.07.31` holds 142 eligible editions, because 2015_12 is quarantined (`docs/site/data/index.md:246-249`). A reviewed acknowledgment for 2026_08 exists (`config/layouts/collections-monthly.yml:35-67`), so June to August 2026 were acquired later. The catalog says "FY2014 to 2026", but the first edition is July 2014 (FY2015). FY2014 values come only from the prior-year-final column ("July {fy_minus_2} to June {fy_minus_1}", `config/semantics.yml:2302`).

**Monitoring.** The old source monitor covers listing pages from FY2025 on (`config/source_sync.yml:9-10`). The catalog says "Older historical completeness is unknown" (`config/admin.yml:30-32`).

**Text layer versus scans.** Every eligible edition has a page-1 text layer, as far as the code shows. Eligibility requires reading the printed period from `document[0].get_text()` (`revenue_collections.py:624-636, 677-678`), and an unreadable page fails closed as `period_unverifiable`. Only 2015_12 is quarantined, and for a different reason. No collections layout names a Textract backend; `grep -i textract config/layouts/collections-*.yml` returns nothing. Every sampled collections document in the October audit was authoritative on `geometric` (`docs/investigations/unverified-row-audit/CASES.md:13-14`). The earlier claim that "school collections need Textract for some editions" is not supported by anything in the checkout. The only damaged text layers recorded are 2016_04 and 2016_11 (MSCH-Q25, Q26), and they are handled by acknowledgments, not OCR.

**Pages.** The report is one page. All three School acknowledgments cite page 1 and table index 1 (`collections-monthly.yml:44, 57, 75, 87, 100, 111`), and two describe "the selected one-page stitched grid" (`:81, :106`). City acknowledgments cite pages 2, 3 and 4 (`collections-monthly.yml:2150-2151, 2175-2176`).

## 2. Tables

One table per edition: revenue lines by column measure.

**A row** is one revenue line, cohort row, subtotal or total. Row indices in reviewed records reach 19 or 20 (`TOTAL REVENUE` at row 19 in 2026_08, `collections-monthly.yml:44`; row 20 column 2 in 2016_04, `CASES.md:13`). The release averages about 149 facts per edition (21,189 facts over 142 editions, `archive/documentation/assets/data/dataset-catalog.json`, `n_rows`). That fits about 15 value rows by 10 columns.

**Row hierarchy.** Three levels.

- Tax blocks: Real Estate, School Income, Use and Occupancy, Liquor Sales. Each has a CURRENT and a PRIOR cohort row and a tax total (`config/entities.yml:1637-1700, 4609-4640`).
- Use and Occupancy also had a settlements block in some era: BANK USE & OCCUPANCY SETTLEMENTS, SETTLEMENTS, and TOTAL U&O TAX COLLECTIONS & SETTLEMENTS (`entities.yml:1673-1688, 1720-1727`). The era is not recorded.
- Non-tax lines: PAYMENT IN LIEU OF TAXES and MISCELLANEOUS NON TAX REVENUES (or OTHER NON TAX). Then TOTAL REVENUE (`entities.yml:1701-1735`).

**Columns, ordinary months.** Mapped right to left (`config/semantics.yml:2275-2298`):

| Position from right | Role | Tag |
|---|---|---|
| 1 | pct_collected (percent) | |
| 2 | remaining_estimate ("Necessary to Meet Budget Estimates") | |
| 3 | increase_decrease | Fiscal Year to Date |
| 4 | fytd_prior_year | |
| 5 | fytd_actual | |
| 6 | increase_decrease | Month |
| 7 | month_prior_year | |
| 8 | month_actual | |
| 9 | budget_current_estimate (optional) | |
| 10 | budget_estimate | |
| 11 | prior_year_final (optional except 2021_07 to 2023_12) | |

Reviewed records confirm the 10-column form without a revised column. In 2016_04, columns 1, 2 and 4 are final, budget and prior-year month (`collections-monthly.yml:73, 81-82`). In 2018_02, column 10 is the percent (`CASES.md:14`).

**Columns, June close.** A 13-column grid adds FYTD before accruals and net accruals, for current and prior year. It is selected when header tokens include "net" and "accruals" and at least 13 amount columns exist (`semantics.yml:2255-2274`). City and School share this grid (`tests/test_accrual_semantics.py:125-143`). June 2020 School carries `fytd_prior_year_pre_accrual` (`test_real_artifacts_optional.py:449-452`).

**Multi-page behavior.** None. One page, one table.

### How School differs from City

| Property | School | City |
|---|---|---|
| Pages | 1 (`collections-monthly.yml:57`) | at least pages 2 to 4 (`:2150, :2176`) |
| Facts per edition | about 149 (21,189 / 142) | about 647 (92,515 / 143, `docs/site/data/index.md:228-230`) |
| Increase columns | two, Month and FYTD (`semantics.yml:2281, 2293`) | one (`semantics.yml:2574-2584`) |
| `min_amount_columns` | 8, or 9 in 2021_07 to 2023_12 (`semantics.yml:2254, 2375, 2443`) | 6 (`semantics.yml:2585, 2665, 2817`) |
| Extra column in 2010s | none | `prior_year_budget` (`semantics.yml:2762-2763`) |
| Fund scopes | none | General Fund tax detail versus dedicated fund summary (`semantics.yml:2566-2572`) |
| Row identities | remaining and percent on every row, catch-all profile only (`semantics.yml:2422-2440`) | Parking Lot Tax only (`semantics.yml:2650-2662`) |
| Exact Decimal and dash contract | none, on purpose (`tests/test_semantics.py:1944-1948`) | yes (`semantics.yml:2614-2620`; `config/release_contracts.yml:5`) |
| Semantics eras | 3 profiles | 6 profiles |
| Layout profiles | 3, all single-edition acks, no catch-all | 18 with a catch-all: 17 in this file plus `collections-monthly-city-2026-08.yml` (`collections-monthly.yml:2134-2135`) |
| Acknowledgments | 3 | 76 numeric plus 63 source-presentation (`/home/claude/scratch/reports/C01.md:136-137`) |
| Jurisdiction | `philadelphia_school_district` (`config/document_roots.yml:24-26`) | `city_of_philadelphia` |
| Header caption checked for revised column | "Revised Budget" or "Current Estimates" (`semantics.yml:2319, 2405, 2454`) | "Revised Budget Estimate" (`semantics.yml:2611`) |

The acquisition code, period reader and wrong-period quarantine are shared (`revenue_collections.py:60-64`).

## 3. Format eras

Eras are declared only in `config/semantics.yml`, as three first-match profiles. Label eras come from tests and entity aliases and have no dated boundaries.

| Era | Editions | What changes | Evidence |
|---|---|---|---|
| Stacked headings | 2014_07 to about 2015 | Tax heading row, then bare CURRENT YEAR and PRIOR YEARS rows. Some headings fused with the cohort. Label printed on its own baseline above amounts. "FISCAL YEAR TO DATE" furniture inside the table. | `tests/test_resolution.py:2601-2728, 3020-3167` (2015_05, 2015_06, 2015_11); `release-notes/data/2026.07.31.yml:71-77` |
| Suffix cohorts | about 2016 to 2017 and later | "TAX: CURRENT" and "TAX: PRIOR" labels, often clipped | `tests/test_entities.py:1537-1612` (2016_06, 2017_11) |
| Default columns | 2014_07 to 2020_02 | 10 or 11 columns. Caption "Current Estimates" accepted for the optional revised column. Month captions use calendar year. | `semantics.yml:2441-2465` |
| Revised budget | 2020_03 to 2021_06 | "FY{fy} Revised Budget Estimate" column. Caption check "Revised Budget". | `semantics.yml:2354-2419` |
| Fiscal labels | 2021_07 to 2023_12 | Month captions verified against the fiscal year. Prior-year final required. At least 9 columns. | `semantics.yml:2246-2254, 2299-2300, 2316-2322` |
| Default again | 2024_01 on | Catch-all rules apply again | `semantics.yml:2420-2466` |
| June close | Junes, years not listed | 13-column accrual grid | `semantics.yml:2255-2274` |
| One-edition relabel | 2020_06 | PILOT printed as MISCELLANEOUS NON TAX REVENUES, misc row absent | `entities.yml:4578-4587` |

Counts: 68 editions use the default profile before 2020_03, 16 use the revised profile, 30 use the fiscal profile, and 29 or more use the default after 2024_01. The 2024 boundary is a guess by the old author: nothing in the checkout says whether 2024 editions print calendar-year or fiscal-year month captions.

## 4. Finding the table

**Today.** School has no `page_types.yml` entry (`grep collections_monthly config/page_types.yml` returns nothing). It has no layout catch-all, so 139 or more editions run with engine defaults. The generic geometric extractor finds the table on page 1 and stitches a one-page grid (`collections-monthly.yml:81`). Columns get roles by counting populated amount columns from the right (`semantics.py:1419-1442`). Optional roles are resolved by trying variants with each optional column present and absent, judged by printed captions (`semantics.py:1453-1500, 2189-2195`).

**Simplest reliable rule.** Take page 1. The table starts below the caption band that contains "Necessary to Meet" and "Pct". It ends at the row labeled TOTAL REVENUE. Columns come from the caption band, not from counting: the caption text distinguishes Month from FYTD increases, revised from original budget, and closes from ordinary months. The period comes from the title block ("MONTH OF <month>" plus "FY<year>"), as today.

## 5. Arithmetic that holds

| Relation | Declared today | Source breaks it |
|---|---|---|
| CURRENT + PRIOR = tax total, each column | generic total detection (hypothesis `items_since_previous_total`, `collections-monthly.yml:76, 101`) | never recorded. The 2016 failures are extraction damage (`:78-84, :103-108`). |
| Tax totals + PILOT + misc = TOTAL REVENUE | generic (`sum_of_unconsumed_from_0`, `:45`) | never recorded. A printed dash in misc makes it uncheckable (2026_08 ack; `CASES.md:13`). |
| U&O collections + settlements = combined total | inferred from rollup entity `entities.yml:1681-1688` | unknown |
| remaining = (revised if printed, else budget) minus FYTD | `remaining_budget`, `semantics.yml:2423-2431`, exact Decimal (`semantic_accounting.py:423-440`) | none recorded. Example: 937,576,000 minus 887,862,525 = 49,713,475 in 2016_04 (`CASES.md:13`). |
| pct = FYTD / (revised or budget) x 100, whole percent, within half the printed increment | `share_of_budget_collected`, `semantics.yml:2432-2440`; `semantic_accounting.py:402-422` | none recorded. Example: 50,578,455 / 73,800,000 = 69% in 2018_02 (`CASES.md:14`). |
| Month increase = month minus prior-year month | not declared | holds in the one reviewed case: -68,436 prior, 68,436 increase, zero month (`collections-monthly.yml:50-51, 62`) |
| FYTD increase = FYTD minus prior FYTD | not declared | unknown |
| Close: FYTD before accruals + net accruals = FYTD | `series_checks.py:91-92, 109-140` | unknown |
| Across editions: FYTD(m) minus FYTD(m-1) = month(m) | `series_checks.py:87-90, 147-178`, tolerance 2.0 | unknown; graded minor, restated or major (`series_checks.py:96-100`) |
| Across editions: prior FYTD = last year's FYTD, same month | `series_checks.py:93-94, 180-195` | unknown |
| July: month = FYTD | not declared | unknown |
| Prior-year final in FY t = June close FYTD of FY t-1 | not declared | unknown |

The two row identities apply only to the 97 editions matched by the catch-all profile. Profile matching is first match (`semantics.py:1657-1675`), and identities run only for the matched profile (`semantic_accounting.py:190, 215`). The revised and fiscal profiles declare neither identities nor `series_scope` (`semantics.yml:2246-2419`). So 46 editions, 2020_03 to 2023_12, get no row proof for remaining or percent.

**Acknowledgment records for School: 3.**

| Kind (as filed) | Count | What it really is |
|---|---|---|
| `uncheckable_source_presentation` | 1 | 2026_08: misc non-tax month cell is a dash; maintainer confirmed it means zero on 2026-10-01. Output stays null. Has both fingerprints. (`collections-monthly.yml:35-67`) |
| `numeric_discrepancy` (default kind, `acknowledgments.py:112`) | 2 | 2016_04 and 2016_11: overprinted text destroyed U&O Prior row cells. Extraction failure, not a source error. No fingerprints. (`:68-116`) |

No School acknowledgment records a source-side arithmetic error. City monthly has 76.

## 6. Row labels and entities

Ten entities, all `jurisdiction: philadelphia_school_district`, all scoped to `collections_monthly_school_*` (`entities.yml:1637-1735`). They take 29 printed alias forms. Cohorts are a separate axis, `entity_qualifier` current or prior.

| Entity | Aliases |
|---|---|
| `phl_school_real_estate` | TOTAL REAL ESTATE TAXES, Subtotal REAL ESTATE TAX, REAL ESTATE, REAL ESTATE TAX, REAL ESTATE TAXES |
| `phl_school_income_tax` | TOTAL SCHOOL INCOME TAX, SCHOOL INCOME TAX |
| `phl_school_use_occupancy` | 8 forms, including clipped TOTAL USE AND OCCUPANCY T and TA, and "... TAX COLLECTIONS" |
| `phl_school_use_occupancy_settlements` | BANK USE & OCCUPANCY SETTLEMENTS |
| `phl_school_use_occupancy_and_settlements_total` (rollup) | TOTAL U&O TAX COLLECTIONS & SETTLEMENTS |
| `phl_school_liquor_sales` | TOTAL LIQUOR SALES TAX, LIQUOR SALES TAX, LI QUOR SALES TAX, TOTAL LIQUOR TAX, LIQUOR TAX |
| `phl_school_pilots` | PAYMENT IN LIEU OF TAXES, IN LIEU OF TAXES; plus MISCELLANEOUS NON TAX REVENUES in 2020_06 only (`:4578-4587`) |
| `phl_school_misc_nontax` | MISCELLANEOUS NON TAX REVENUES, MISCELLANEOUS NON TAX, OTHER NON TAX |
| `phl_school_settlements` | SETTLEMENTS |
| `phl_school_total_revenue` | TOTAL REVENUE |

Cohort tokens: CURRENT YEAR, PRIOR YEAR, PRIOR YEARS as rows under a heading (`entities.yml:4609-4616`); suffixes after a colon or hyphen: C, CU, CUR, CURRE, CURREN, CURRENT, P, PR, PRI, PRIOR (`:4617-4640`; split rule `entities.py:224-232`). The reader also maps "curre" and "curren" (`gov-budget-data/src/gov_budget_data/series_models.py:38-44`).

Continuity: the release test expects exactly one row gap, `phl_school_misc_nontax` in 2020_06, and 17 continuous FYTD lanes (`test_real_artifacts_optional.py:261-269`).

Elsewhere: "REAL ESTATE TAX" is also a City entity (`phl_real_estate_tax`, `entities.yml:127-135`). Only family scoping keeps the School row from resolving to the City entity. The QSMR will print the same School revenue lines; nothing links them yet.

## 7. Values

- Whole US dollars, multiplier 1; percent passes through with unit `percent` (`semantics.yml:2331-2353`).
- No `decimal_precision` and no `source_dash_value`. The test says exact-value and dash semantics were "validated against City collections only" and must not be extended silently (`tests/test_semantics.py:1944-1948`).
- Dash: printed in misc non-tax cells. In 2026_08 it means zero by maintainer review, yet stays null (`collections-monthly.yml:47-53`).
- Negative amounts occur in prior-year cells (-68,436, `:51`). The printed form (parentheses or minus) is not recorded.
- Percent is a whole number ("69%", `CASES.md:14`).
- Overprinted text in 2016_04 and 2016_11 drops amounts and changes digits (MSCH-Q25, Q26).
- A "fused money lane" in 2016_04 is kept before reconciliation (`release-notes/data/2026.07.29.yml:110-111`), handled by generic `tables/fused_columns.py`.

## 8. Editions and revisions

- **Wrong file under a right name.** `collections_monthly_school_2015_12` has the same bytes as `2014_12` and prints "MONTH OF DECEMBER" with FY2015. Alias grouping by SHA-256 and document type finds it (`documents.py:53-76`). The unique alias whose printed period matches stays canonical; the other is quarantined with `printed_period_mismatch` and `content_alias_nonmatch` (`revenue_collections.py:689-727`; `test_real_artifacts_optional.py:484-495`). The real December 2015 report is not held, so FY2016 has a gap (`release-notes/data/2026.07.28.yml:80-83`).
- **Ingest guard.** A downloaded PDF must print the listing's period before it replaces a held file (`revenue_collections.py:848-888`).
- **Restatement.** Each edition reprints the prior year's month and FYTD and the prior fiscal year's final. Cross-edition checks compare them but do not choose between editions. No School reissue or reused URL is recorded.
- **Canonical value today.** One edition per month. The latest edition is not preferred over earlier ones for overlapping measures. Each value is cited to its own edition.

## 9. Quirk ledger

| Id | What happens in the document | Old code | Kind |
|---|---|---|---|
| MSCH-Q01 | 2015_12 file is the December 2014 report, byte-identical to 2014_12. December 2015 is missing. | `revenue_collections.py:644-729`; `documents.py:53-76`; `validation.py:288-296` | inherent |
| MSCH-Q02 | July and August filenames sometimes carry the fiscal year. | `revenue_collections.py:373-378` | inherent |
| MSCH-Q03 | Year override trusts the listing page. A page listing a month from the next fiscal year would be misdated (seen on the Water page). | `revenue_collections.py:377-378`; `docs/philly-source-monitoring-audit-2026-09-11.md:77-81` | unsure: needs a School page with an out-of-year link |
| MSCH-Q04 | Title prints the month without a year; year comes from the one printed "FY". Fallbacks: title date "October 31,2018", body month-year, decayed tokens "SEPTMEBER", "APRI L". | `revenue_collections.py:438-616`; `tests/test_revenue_collections.py:164-243` | inherent (examples are shared with City; their family is not recorded) |
| MSCH-Q05 | Narrative "month of December 2023" text near the title must not win. | `revenue_collections.py:464-474, 518-519` | inherent |
| MSCH-Q06 | The manifest field `fiscal_year` holds the calendar year for monthly reports. | `documents.py:201-212`; `tests/test_revenue_collections.py:311-319` | artifact (field naming) |
| MSCH-Q07 | One-page report; one table. | `collections-monthly.yml:57, 75, 81` | inherent |
| MSCH-Q08 | Two increase/decrease columns, Month and FYTD. | `semantics.yml:2275-2298` | inherent |
| MSCH-Q09 | Revised estimate and prior-year final are each optional; 8 to 11 columns. | `semantics.yml:2377-2379, 2447-2449`; `semantics.py:1453-1500` | inherent |
| MSCH-Q10 | 2020_03 to 2021_06 print a revised budget column. | `semantics.yml:2354-2419` | inherent |
| MSCH-Q11 | 2021_07 to 2023_12 month captions carry the fiscal year; prior-year final always printed. | `semantics.yml:2246-2254, 2316-2322` | inherent (caption text itself unverified) |
| MSCH-Q12 | 2024 on fall back to "Current Estimates" and calendar-year captions. | `semantics.yml:2451-2456` | unsure: render one 2024 and one 2025 edition |
| MSCH-Q13 | June close adds four accrual columns (13 total). | `semantics.yml:2255-2274` | inherent |
| MSCH-Q14 | Remaining and percent identities are missing for 46 editions because the era profiles shadow the catch-all. | `semantics.yml:2246-2441`; `semantics.py:1657-1675`; `semantic_accounting.py:190` | artifact (first match, no inheritance) |
| MSCH-Q15 | No exact Decimal or dash contract for School. | `tests/test_semantics.py:1944-1948` | artifact (contract rolled out family by family) |
| MSCH-Q16 | Tax heading rows carry the parent for bare CURRENT YEAR and PRIOR YEARS rows. "FISCAL YEAR TO DATE" furniture must not reset it. | `tests/test_resolution.py:2601-2656, 3020-3113` | inherent |
| MSCH-Q17 | Fused parent and cohort: "SCHOOL INCOME TAX CURRENT YEAR", "USE AND OCCUPANCY TAX CURRENT YEAR COLLECTIONS". | `resolution.py:1551-1575`; `tests/test_resolution.py:2659-2728` | inherent |
| MSCH-Q18 | An unknown heading or unknown fused label clears the parent; cohort rows stay unresolved. | `tests/test_resolution.py:2938-2980, 3118-3167` | inherent (safety rule) |
| MSCH-Q19 | Clipped cohort suffixes: C, CU, CUR, CURRE, CURREN, P, PR, PRI. | `entities.yml:4617-4640`; `tests/test_entities.py:1586-1612` | unsure: release notes say "OCR labels" (`2026.07.28.1.yml:25-30`); a render shows whether the clip is printed |
| MSCH-Q20 | "LI QUOR SALES TAX" spaced label. | `entities.yml:1696` | unsure, as Q19 |
| MSCH-Q21 | Clipped totals "TOTAL USE AND OCCUPANCY T" and "TA"; "Subtotal REAL ESTATE TAX". | `entities.yml:1642-1670`; `collections-monthly.yml:71, 96` | unsure, as Q19 |
| MSCH-Q22 | U&O settlements block with a two-line total label "TOTAL U&O TAX COLLECTIONS &" / "SETTLEMENTS". | `entities.yml:1673-1688`; `tables/row_repairs.py:1208-1272` | inherent (era unknown) |
| MSCH-Q23 | June 2020 prints the PILOT row as MISCELLANEOUS NON TAX REVENUES; the misc row is absent. | `entities.yml:4578-4587`; `tests/test_entities.py:1551-1563` | inherent |
| MSCH-Q24 | Misc non-tax cells print a dash meaning zero; it blocks the TOTAL REVENUE sum in that column. | `collections-monthly.yml:35-67`; `CASES.md:13` | inherent |
| MSCH-Q25 | 2016_04 overprint: U&O Prior final, budget and prior-month amounts unreadable. | `collections-monthly.yml:68-92` | inherent (needs OCR or a reviewed cell) |
| MSCH-Q26 | 2016_11 overprint: two Prior amounts lost and 7,500,000 read as 77,500,000. The ack encodes the -70,000,000 residual. | `collections-monthly.yml:93-116` | inherent damage |
| MSCH-Q27 | An acknowledged numeric review marks every covered cell in its columns as accounted, so the misread 77,500,000 can pass the accounting gate. | `export.py:1024-1040` | artifact (acks cover failed checks, not cells) |
| MSCH-Q28 | The two 2016 acks are filed as `numeric_discrepancy` and have no fingerprints. | `acknowledgments.py:112`; `collections-monthly.yml:68-116` | artifact |
| MSCH-Q29 | April 2016 has a fused money lane. | `release-notes/data/2026.07.29.yml:110-111`; `tables/fused_columns.py` | unsure: exact shape not recorded |
| MSCH-Q30 | Early labels sit on their own baseline above amounts. City needs a layout flag; School uses the unflagged repair. | `tables/row_repairs.py:1003-1075`; `collections-monthly.yml:18-26`; `2026.07.31.yml:71-77` | inherent (era bounds unknown) |
| MSCH-Q31 | No layout catch-all for School; most editions run engine defaults. | `layouts.py:1408-1410` | artifact |
| MSCH-Q32 | Remaining and percent use the revised estimate when printed, else the budget. A printed but unusable revised cell must not fall back. | `semantics.yml:2428, 2439`; `semantic_accounting.py:286-294`; comment `semantics.yml:2644-2649` | inherent |
| MSCH-Q33 | Percent proof needs accounted operands and proves only the result. | `semantic_accounting.py:120-125, 402-409` | inherent (rule) |
| MSCH-Q34 | Prior-year month cells can be negative. | `collections-monthly.yml:50-51` | inherent |
| MSCH-Q35 | "REAL ESTATE TAX" also names a City entity. | `entities.yml:127-135, 1645` | inherent |
| MSCH-Q36 | FY2014 appears only through prior-year columns. | `semantics.yml:2302`; `test_real_artifacts_optional.py:466-482` | inherent |
| MSCH-Q37 | Watch covers FY2025 pages on; older completeness unknown. | `source_sync.yml:9-10`; `admin.yml:30-32` | artifact (scope choice) |
| MSCH-Q38 | Several links per month: last wins. Seen for City ("March-2025-revised.pdf"). | `revenue_collections.py:360-379`; `tests/test_revenue_collections.py:55-62` | unsure for School |

## 10. Old code that serves this family

| Job | File | Lines | Keep as code or as knowledge |
|---|---|---|---|
| Acquisition | `revenue_collections.py` | 888 | Code: listing scrape, period reader, alias quarantine (about 400 lines). Knowledge: the integrity report models. |
| Acquisition | `phila_source_sync.py` | 231 (School: 78-90, 188-203) | Knowledge; `watch` replaces it. |
| Acquisition | `commands/collections.py` | 544 | Knowledge. |
| Acquisition | `documents.py` alias groups | 24 of 348 | Code, small. |
| Layout | `config/layouts/collections-monthly.yml` School part | 82 of 2,188 | Knowledge: three reviewed cases with page-cited arithmetic. |
| Layout | generic `tables/row_repairs.py`, `fused_columns.py` | 1,319 and 1,491 | Knowledge for School; the stacked-label and wrapped-total cases are real. |
| Semantics | `config/semantics.yml` School profiles | 221 (2246-2466) | Knowledge: column order, captions, eras. |
| Semantics | `semantic_accounting.py` | 631 | Code: exact row identity and half-increment ratio, about 110 lines. |
| Entities | `config/entities.yml` School entries | about 120 | Data: move as is, cited. |
| Entities | `resolution.py` fused qualifier split | about 70 (1551-1620) | Knowledge; a School parser can emit parent and cohort directly. |
| Checks | `series_checks.py` | 203 | Code: three cross-edition checks. |
| Checks | `cross_document_totals.py` | 951 | Not used by School. |
| Tests | `test_revenue_collections.py`, `test_collection_source_integrity.py`, `test_phila_source_sync.py` | 358, 294, 121 | Keep the period and alias cases as fixtures. |
| Tests | School parts of `test_resolution.py`, `test_entities.py`, `test_semantics.py`, `test_accrual_semantics.py` | about 500 | Knowledge; rewrite as parser fixtures. |
| Tests | `gov-budget-data/tests/test_real_artifacts_optional.py` School parts | about 90 | Keep as release expectations: one row gap, 17 FYTD lanes, PILOT rename. |

## 11. The least a parser needs

Inputs: the PDF bytes, its listing month, the page-1 words with boxes.

1. Read the title block. Get the month and the single printed FY. Derive the calendar year. Stop if it disagrees with the listing month.
2. Hash the bytes. Stop if another held edition has the same hash and a different month.
3. On page 1, find the caption band. Name each column from its caption: final, budget, revised, month, prior month, month change, FYTD, prior FYTD, FYTD change, before accruals, net accruals, remaining, percent.
4. Take rows down to TOTAL REVENUE. For each row, record label, row kind and cohort. Carry the tax heading onto bare CURRENT and PRIOR rows. Split "TAX: CUR" style suffixes and fused "TAX CURRENT YEAR" labels.
5. Type each cell: amount, dash, blank. Keep the printed token. Do not turn a dash into zero.
6. Map labels to the ten School entities, with a per-edition override for 2020_06.

Parameters that differ by era: whether revised and final columns exist, the caption year basis, the close grid, and the label style. With caption-driven column naming, only the label style needs an era table.

Checks to declare:

- each tax: CURRENT + PRIOR = total, every column;
- tax totals + PILOT + misc = TOTAL REVENUE, every money column;
- remaining = (revised or budget) minus FYTD, every row;
- percent = FYTD / (revised or budget), within half a point;
- month change = month minus prior month; FYTD change = FYTD minus prior FYTD;
- close: before accruals + net accruals = FYTD;
- across editions: FYTD delta = month; prior FYTD = last year's FYTD; July month = July FYTD.

Acknowledgments needed on day one: the 2026_08 dash and reviewed cells for 2016_04 and 2016_11.

### Which rows are withheld and why

Release `2026.07.31` withholds 475 of 21,189 facts (97.8 percent pass, `docs/site/data/index.md:249`). A fact is one cell. A fact passes only when `value_verified`, `table_accounted` and `column_verified` are all true (`docs/site/explanation/trust-model.md:49-53`). The checkout has no artifacts, so the 475 cannot be listed. The recorded causes are these.

- Dash cells in misc non-tax are null, so `value_verified` is false. The dash also makes TOTAL REVENUE uncheckable in that column, so cells covered only by that sum lose `table_accounted` (`CASES.md:13`; `export.py:1003-1040`).
- Percent cells are left out of additive checks. Before October 16 they had no ratio proof, so any table with an open check withheld them (`CASES.md:14`).
- Remaining cells on rows covered only by a failed vertical sum were withheld the same way (S05, `CASES.md:13`).
- U&O Prior cells lost in 2016_04 and 2016_11 are null.
- Columns that fail caption checks lose `column_verified`. The catalog lists an `unknown` role for School, so some columns were never named (`dataset-catalog.json`, `column_roles`).

The October 16 fixes added the remaining and percent proofs (`docs/analysis-readiness-0.4.1-status.md:37-43`). They only reach the 97 catch-all editions (MSCH-Q14). No release after `2026.07.31` reports a School pass rate.

## 12. Unknowns

- Exact list of the 475 withheld facts and their reasons. Needs the release Parquet.
- Whether any School edition lacks a text layer beyond page 1, and whether Textract was ever run on School.
- Caption text in 2024 to 2026 editions (MSCH-Q12).
- Which Junes print the accrual grid.
- When the settlements block appears and disappears, and the label-style era bounds.
- Whether clipped labels are printed or produced by extraction (Q19 to Q21).
- Whether the misread 77,500,000 in 2016_11 is published as trusted (Q27). The code allows it.
- Printed form of negative numbers.
- Whether the PILOT cells in 2026_08 are blank, dash or zero.
- Whether the real December 2015 report still exists anywhere.
