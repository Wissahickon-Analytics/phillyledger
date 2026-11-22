# MCITY: Philadelphia monthly City revenue collections

Dataset `collections_monthly_city`. One PDF per month, the City's "Comparative Statement of Net Revenue Collections". Paths below drop `packages/gov-budget-etl/src/gov_budget_etl/`; `tests/` means `packages/gov-budget-etl/tests/`. The checkout has no PDFs and no pipeline artifacts, so page facts come from config, tests, release notes and review records.

## 1. Documents

The publisher lists one HTML page per fiscal year and series. The URL is `https://www.phila.gov/documents/fy-<FY>-city-monthly-revenue-collections/` (`revenue_collections.py:383-392`). The page is server rendered, so links are read with one regex over `https://www.phila.gov/media/<digits>/<name>.pdf` (`revenue_collections.py:9-11, 39`). A link belongs to the City series when its filename contains "city" and "collection" (`revenue_collections.py:312-316`).

- Cadence: monthly. Philadelphia's fiscal year runs July to June (`revenue_collections.py:65, 339-341`).
- Editions in the last published release (`2026.07.31`): 143, July 2014 to May 2026, with no gap. The tracker notebook reports 143 expected reports and a first report dated 2014-07-31 (`notebooks/monthly_revenue_tracker.ipynb:44, 747`). July 2014 to May 2026 is exactly 143 months.
- The catalog says "FY2014 to 2026" (`docs/site/data/index.md:39, 228`). That is wrong by one year at the start. The first edition, July 2014, belongs to FY2015. See MCITY-Q10.
- The local corpus later gained August 2026 (`config/layouts/collections-monthly-city-2026-08.yml:1-6`). A test names September 2026, but only as a profile-matching probe (`tests/test_layout_composition.py:234`).
- Text layer: every edition has one on page 1, at least. Acquisition reads the printed period from page 1 with PyMuPDF and fails closed without it (`revenue_collections.py:624-636, 848-861`). The corpus-wide source audit quarantines only one source, and it is a School document (`release-notes/data/2026.08.02.yml:115-118`). Every City citation in the review records names the `geometric` (native text) backend. No City edition is recorded as a scan.
- Pages: four. The August 2026 review inspected "all four rendered source pages" (`collections-monthly-city-2026-08.yml:2`). Page 1 holds wage, earnings, net profits and real estate. Page 2 holds BIRT, other taxes, beverage tax and usually TOTAL TAX REVENUE. Page 3 holds local non-tax detail. Page 4 holds other funds, governmental revenue, the grand totals and the non-General-Fund funds. Placement shifts by era (MCITY-Q50).
- Watch scope today: fiscal-year pages from FY2025 on (`config/source_sync.yml:7-8`). The current year's page may not exist yet (`phila_source_sync.py:188-203`). Older editions were acquired before source sync existed.

## 2. Tables

There is one logical table per edition: a statement that runs over all four pages with the column header repeated on each page (`tests/test_classification.py:782-806`).

- Row: one revenue line, subtotal or total, for one fund scope. Printed row count is about 90 to 100. Review records cite row indices up to 96 (`config/layouts/collections-monthly.yml:2069`).
- Facts per edition: 92,515 facts over 143 editions is about 647 cells each (`docs/site/data/index.md:230`).
- Columns, right to left in the ordinary grid: percent of budget collected, necessary to meet budget, FYTD increase (decrease), FYTD prior year, FYTD current, month prior year, month current, revised or current budget estimate (optional), budget estimate, prior-year final (`config/semantics.yml:2574-2584`). The June close grid has 13 amount columns (MCITY-Q16).
- Header: three or four printed lines, with years split from their words ("JULY, / 2014 / TO FY2016 / FINAL", "MONTH OF MAY / 2016") (`tests/test_classification.py:760-780`).
- Row kinds: detail lines, current/prior qualifier rows, subtotals, rollups, a deduction row and grand totals. There are no printed codes.

Row hierarchy, reconstructed from entity aliases and review records (`config/entities.yml`; review reasons in `collections-monthly.yml`):

| Level | Rows |
|---|---|
| Qualifier | CURRENT YEAR, PRIOR YEAR, PRIOR YEARS under a tax heading, or a suffix such as REAL ESTATE TAX-CURRENT |
| Tax subtotal | TOTAL CITY WAGE TAX, TOTAL PICA WAGE TAX, same for earnings and net profits; TOTAL REAL ESTATE TAX; TOTAL BUSINESS INCOME & RECEIPTS TAX; TOTAL PHILADELPHIA BEVERAGE TAX |
| Combined | TOTAL PICA AND CITY WAGE TAX (and earnings, net profits) |
| Wage block | TOTAL WAGE, EARNINGS AND NET PROFITS (gross); LESS PICA ... (deduction); TOTAL CITY WAGE, EARNINGS AND NET PROFITS (net) |
| Section totals | TOTAL TAX REVENUE * (excludes PICA), TOTAL LOCAL NON-TAX REVENUE, REVENUE FROM OTHER FUNDS, TOTAL REVENUE FROM GOVERNMENTAL UNITS |
| Grand total block | TOTAL GENERAL FUND AND PICA, then LESS PICA, then TOTAL GENERAL FUND |
| Other funds | Grants Revenue, Community Development, Capital Improvement, PICA Capital Projects, Acute Care Hospital Assessment, Hotel Fund (HOTEL TAXES + INTEREST = TOTAL HOTEL FUND), a dedicated-tax "TAXES" block ending in TOTAL TAX |

Pages 1 to 4 belong to one table. Totals on page 4 use operands from pages 1 to 3 (`collections-monthly-city-2026-08.yml:330-338`).

## 3. Format eras

Eras live mostly in `config/semantics.yml` profiles, selected by document id glob, first match wins (`semantics.py:1657-1676`).

| Era | Editions | What differs | Evidence |
|---|---|---|---|
| Stacked labels | 2014-07 to 2015-11 (not 2015-12) | Grants, Community Development and some BIRT current/prior labels print on their own plain baseline above their amounts | `collections-monthly.yml:18-26`; `tests/test_layout_composition.py:229-231, 250` |
| 2010s spring | Mar to Jun, 2014 to 2019 | Adds a "Current Estimates March FY" column | `semantics.yml:2693-2749`; `tests/test_semantics.py:205-209` |
| 2010s other months | Jul to Feb, 2014 to 2019 | Optional prior-year budget and optional prior-year final columns | `semantics.yml:2750-2809` |
| Data Warehouse | from 2016-02 | Budget total keeps 5,700,000 for a line no longer itemized | `collections-monthly.yml:2139-2163` |
| Beverage tax | by 2018-01 | Beverage current/prior rows in OTHER TAXES; start month not verified | `tests/test_resolution.py:2920-2940` |
| 2020 | 2020-01 to 2020-12 | Optional revised budget estimate; month caption with calendar year | `semantics.yml:2679-2692` |
| Fiscal captions | from 2021-07 (FY2022) | Month captions print the fiscal year, not the calendar year | `semantics.yml:2640-2678, 2819-2821` |
| FY2022 revised budget | 2022-01 to 2022-06 | Revised budget estimate column verified by caption | `semantics.yml:2558-2612` |
| Parking leaves General Fund | FY2024 on | General Fund Parking and Valet rows print N/A in current columns; dedicated-fund rows keep values | `collections-monthly.yml:2-17` |
| Default | 2024 on | Same grid as 2021 to 2023 | `semantics.yml:2810-2828` |
| Close editions | June | 13-column grid with pre-accrual FYTD and net accruals for both years | `semantics.yml:2255-2274`; `tests/test_accrual_semantics.py:126-146` |
| Hotel label | 2025-06 | TOTAL HOTEL FUND printed as HOTEL TAX | `collections-monthly.yml:2126-2133` |
| FY2027 | 2026-08 | BIRT and beverage budgets only at subtotal with N/A split; dashes for PICA prior years; N/A for every remaining-budget cell in local non-tax detail; PICA Capital Projects all N/A | `collections-monthly-city-2026-08.yml` reasons |

Whether the 2026-08 presentation continues for all of FY2027 is unknown. Only one FY2027 edition was reviewed. N/A cells existed before (2024-04, 2024-10, 2024-11, 2025-02), so August 2026 is not the first edition with N/A. It is the first with dashes and N/A on all four pages.

## 4. Finding the table

Today the engine does not classify pages for this family. The page-classification stage exits with no profile, stitching pools all four pages under table type None, and layouts address "table 1" by index (`collections-monthly.yml:43, 127`; scratch report E07 section 2). The column grid is then chosen by document id and checked against header templates (`semantics.yml:2601-2611`).

Simplest reliable rule: the whole document is the table. Start below the title block that contains "Comparative Statement of Net Revenue Collections" (`revenue_collections.py:56-58`). Drop the repeated header lines on pages 2 to 4. Stop after the last fund row on page 4. Identify the grid by caption words, not by count: "Net Accruals" selects the close grid (`semantics.py:836-850`), "Current Estimates" or "Revised Budget Estimate" adds that column. Fail if the captions do not match a declared grid.

## 5. Arithmetic that holds

| Id | Relation | Columns | Source breaks it |
|---|---|---|---|
| A1 | Current + prior = tax subtotal (wage, earnings, net profits, real estate, BIRT, beverage) | all money | 2022-03 to 2022-06 revised column (MCITY-Q40); 2018-03 increase column (Q43); wage current + prior = total within 1 dollar in all 143 editions (`release-notes/data/2026.07.28.1.yml:69-71`) |
| A2 | City + PICA = combined | all money | none recorded |
| A3 | LESS PICA = sum of three PICA subtotals | all money | 2017-01 (30,321,984); 2022-02 to 2022-05 (3 or 4 dollars); 2022-03 to 2022-06 revised column (Q41) |
| A4 | Gross wage block = City net + LESS PICA | all money | 2017-01 holds by this relation while A3 fails |
| A5 | TOTAL TAX REVENUE = tax subtotals, PICA excluded | all money | 2016-02 (5,700,000), 2024-07 (188,954 twice); 2024-04 blocked by N/A operands |
| A6 | TOTAL LOCAL NON-TAX = its detail | all money | 2020-06 (typo, -133,469), 2025-09 (-517) |
| A7 | TOTAL REVENUE FROM GOVERNMENTAL = four rows | all money | 2020-12 (stale, -63,969,127); 2020-06 accrual columns |
| A8 | TOTAL GENERAL FUND AND PICA = tax + PICA + local non-tax + other funds + governmental | all money | 52 editions (table below) |
| A9 | TOTAL GENERAL FUND = GFP minus LESS PICA | all money | 2025-03 (2 dollars) |
| A10 | TOTAL HOTEL FUND = HOTEL TAXES + INTEREST | all money | holds within 1 dollar at 2025-06 (`collections-monthly.yml:2128-2131`) |
| A11 | Dedicated Parking: remaining = revised (else budget) minus FYTD | row | declared today, `semantics.yml:2644-2662` |
| A12 | Increase = FYTD minus FYTD prior; remaining = budget minus FYTD; percent = FYTD / budget | row | not declared for the City today; 2018-03 increase cell wrong |
| A13 | FYTD this month minus FYTD last month = month | cross-edition | checked as a diagnostic, tolerance 2.0 (`series_checks.py:77-178`); 2020-06 used it to prove a typo |
| A14 | July: month = FYTD for current and prior | within edition | 2024-07 defect repeats in both cells |
| A15 | FYTD prior year = last year's FYTD for the same month | cross-edition | graded "restated" when large (`series_checks.py:93-100, 179-202`); frequency unknown |
| A16 | Pre-accrual FYTD + net accrual = final FYTD | close editions | 2020-06 transposes values between Other Governmental Units and PICA Transfer |

Rounding: whole dollars. One subtotal can be off by 1 dollar. Long leaf sums can be off by 3 dollars (`collections-monthly-city-2026-08.yml` TOTAL GENERAL FUND AND PICA reason). A tolerance must stay below the real 50 to 57 dollar defects of 2020 to 2022.

Acknowledgment records for this family (counted by parsing the YAML):

| Kind | Records | Cells | Editions |
|---|---|---|---|
| GFP vertical sum (A8) | 52 | 69 | 52 |
| PICA deduction (A3) | 6 | 9 | 6 |
| City / PICA wage subtotal transposition (A1) | 8 | 8 | 4 |
| TOTAL TAX REVENUE (A5) | 2 | 3 | 2 |
| Governmental (A7) | 2 | 3 | 2 |
| Local non-tax (A6) | 2 | 2 | 2 |
| Beverage increase (A1, A12) | 1 | 1 | 1 |
| TOTAL GENERAL FUND (A9) | 1 | 1 | 1 |
| Numeric total | 74 | 96 | 57 of 143 |
| Source presentation, 2026-08 | 63 | 63 | 1 |

GFP residual classes: 2017-01 to 2019-08, 22 editions, overstated by 1.5 million to 992.5 million and growing through each fiscal year; 2020-02 to 2020-05, 1,822 to 4,866; 2020-07 and 2020-08, about 100,000,007; 2020-09 to 2021-06, a stale 63,969,1xx; 2020-08 to 2022-06, 50 to 57 dollars (`collections-monthly.yml:176-1333, 1434-1985`). Only 14 of the 74 numeric records carry fingerprints.

## 6. Row labels and entities

The registry has 70 entities for this family: 23 tax, 22 revenue category, 13 rollup, 5 fund, 4 department, 3 other (`config/entities.yml`, parsed). The default view in release 2026.07.31 has 68 stable line items (`notebooks/monthly_revenue_tracker.ipynb:549`).

- Renames: SALE OF ASSETS / ASSET SALES; INTEREST INCOME / INTEREST EARNINGS; SWEETENED BEVERAGE TAX / PHILADELPHIA BEVERAGE TAX; TOBACCO AND TOBACCO RELATED PRODUCTS TAX / SMOKELESS TOBACCO; COURT RELATED COSTS / COURT RELATED; LICENSES AND INSPECTION FEES / LICENSES & INSPECTIONS.
- Truncated labels: 39 aliases are strict prefixes of another alias of the same entity, such as TOTAL GENERAL FUND AND PIC and LESS: TOTAL PICA WAGE, EARN (`tests/test_entities.py:1662-1683`). Some may be wrapped rather than clipped; the PDFs would tell.
- Damaged labels from overprint: TOTAL TOTAL PICA PICAWAGETAX WAGE TAX, HOTEL HOTEL TAX TAX (`tests/test_entities.py:1677-1683`).
- Same label, two scopes: PARKING LOT TAX and VALET PARKING TAX under OTHER TAXES (General Fund) and under TAXES (dedicated funds) (`semantics.yml:2561-2572`).
- Context-dependent labels: INTEREST means Hotel Fund interest; TOTAL TAX means the dedicated-fund total; HOTEL TAX means the Hotel Fund total only in 2025-06 (`tests/test_entities.py:1700-1729`).
- Departments shared with QCMR, Budget in Brief, budget detail and supplemental reports: Health, Records, Sheriff, Streets. TOTAL GENERAL FUND is shared with Budget in Brief.
- QCMR cash prints the same taxes but uses separate "(Cash)" entities, such as `phl_cash_birt`. No cross-family link is declared.

## 7. Values

- Unit: whole US dollars, multiplier 1 (`config/release_contracts.yml:8-31`). The percent column is a ratio, passed through with unit percent (`semantics.yml:2635-2639`).
- Negatives: parentheses, for example (359,304,205) (`collections-monthly.yml:33-34`).
- Dash: sometimes means zero. The maintainer confirmed this for PICA prior-year cells and local non-tax cells in 2026-08 (`collections-monthly-city-2026-08.yml:19-24`). The old engine nulls every dash before arithmetic (`tables/reconcile.py:1330-1349`).
- N/A: not applicable. Must stay null. Whole fund rows can print N/A in every measure, including the percent column (`tables/classification.py:1080-1086`).
- Footnote marks inside labels: `TOTAL TAX REVENUE *`, `PARKING LOT TAX **2` (`collections-monthly.yml:8-9`).
- Overprint: amounts painted twice, grouped and comma-less ("40905296" beside "40,905,296"), and amounts painted inside a label's span (`tests/test_table_primitives.py:712-725, 1082-1094`).
- Equal neighbours are real: in July, month and FYTD are identical (`tests/test_table_primitives.py:1070-1080`).
- Blank cells: the 2018-03 beverage total FYTD prior cell is blank (`collections-monthly.yml:1333-1368`).

## 8. Editions and revisions

- One PDF per month. When a listing has two links for one month, the last wins, such as a "-revised" file (`revenue_collections.py:379`; `tests/test_revenue_collections.py:55-62`). No City reissue is recorded.
- Every edition restates last year in its prior-year columns. The old code keeps each edition as its own observation. It grades disagreements as "restated" diagnostics and does not pick a canonical value (`series_checks.py:93-100`).
- The same bytes under two month keys is a real hazard. School 2015-12 holds the December 2014 PDF and stays quarantined. The rule keeps only the alias whose printed period matches its key (`revenue_collections.py:644-729`). No City alias is recorded.
- A downloaded file replaces an existing one only after its printed period matches the listing (`revenue_collections.py:875-888`).

### Which rows are withheld today, and why

The 99.4 percent is 91,914 of 92,515 facts in release 2026.07.31 (`docs/site/data/index.md:230`). A "row" is one fact cell, not a printed line (`docs/investigations/unverified-row-audit/README.md:25`). So 601 cells are withheld. That release is fact-schema v1 for this family. Its default filter is the table accounting and header predicate (`docs/site/explanation/trust-model.md:68-71`).

The exact 601 cells cannot be listed from the checkout. The release files are not in it. The known causes, with evidence:

1. Dash, N/A and blank cells. They are nulled and each one opens an `unresolved_source_cell_presence` assertion (`tables/reconcile.py:1000-1045`). Known cases: 2025-02 PILOT remaining estimate N/A, judged a correct exclusion (audit case S04, `docs/investigations/unverified-row-audit/CASES.md:12`); PICA Capital Fund N/A in October and November 2024 (`release-notes/data/2026.08.02.yml:111-114`). Most withheld cells are probably of this kind. That is not verified.
2. Totals blocked by N/A operands. In 2024-04, TOTAL TAX REVENUE could not be checked because Parking and Valet print N/A (audit S03, `CASES.md:11`). A fix landed on 2026-10-16, after the release (`docs/analysis-readiness-0.4.1-status.md:51-54`). Other FY2024 and later editions get no such rule.
3. One TOTAL GENERAL FUND monthly value is missing from the default series: 142 of 143 reports (`notebooks/monthly_revenue_tracker.ipynb`, series check cell). Which edition is not recorded.
4. Editions with no acknowledgment despite neighbours with the same defect: 2017-06, 2018-01, 2018-02 and 2019-03 to 2019-07 fall inside the 2017 to 2019 GFP run. Either they reconcile or their cells are withheld.

Acknowledged defects do not withhold cells. An acknowledgment marks the total as accounted.

## 9. Quirk ledger

| Id | What happens in the document | Old code | Kind |
|---|---|---|---|
| MCITY-Q01 | Listing filenames put month and year in either order | `revenue_collections.py:344-350`; `tests/test_revenue_collections.py:37-45` | inherent |
| MCITY-Q02 | Two links for one month in a listing; the later one is the revision | `revenue_collections.py:379` | inherent (frequency unknown) |
| MCITY-Q03 | A filename carries the fiscal year instead of the calendar year; the listing's fiscal year overrides | `revenue_collections.py:373-378` | unsure for City; code comment names School July and August PDFs only. A City listing with this error would settle it |
| MCITY-Q04 | Title prints the month without a calendar year; year comes from one printed "FY YYYY", else a unique body "Month YYYY" | `revenue_collections.py:575-616` | inherent |
| MCITY-Q05 | Title forms vary: "MONTH OF DECEMBER" over "2014", "MONTH OF MAY, 2017", "October 31,2018" | `tests/test_revenue_collections.py:164-243` | inherent (fixtures are synthetic; which series each came from is not recorded) |
| MCITY-Q06 | Title month misspelled or split: SEPTMEBER, SEPT, APRI L. This is in the PDF title, not the listing | `revenue_collections.py:438-461`; `tests/test_revenue_collections.py:204-218` | inherent |
| MCITY-Q07 | A footnote names a different month and year than the title | `revenue_collections.py:464-474`; `tests/test_revenue_collections.py:178-192` | inherent |
| MCITY-Q08 | Same PDF bytes posted under two months | `revenue_collections.py:644-729`; `validation.py:287-297` | inherent (only a School case is known) |
| MCITY-Q09 | A stale link must not overwrite a good file | `revenue_collections.py:875-888` | inherent |
| MCITY-Q10 | Manifest field `fiscal_year` holds the calendar year, so the catalog says FY2014 for a series that starts in FY2015 | `documents.py:201-212`; `semantics.py:1748-1749`; `docs/site/data/index.md:39` | artifact (manifest naming) |
| MCITY-Q11 | From July 2021, month captions print the fiscal year ("Month of September 2022" in a September 2021 edition) | `semantics.yml:2668, 2819-2821` versus `2602` | inherent |
| MCITY-Q12 | Header captions span 3 or 4 lines with years on their own lines, repeated on every page | `tests/test_classification.py:760-806` | inherent |
| MCITY-Q13 | Header year split by a glyph seam ("Fiscal 202 4") | `semantics.py:164-174` | unsure: shared helper; a City page with this seam would settle it |
| MCITY-Q14 | 2014 to 2019: spring editions add "Current Estimates March"; other months may print prior-year budget and final | `semantics.yml:2693-2809` | inherent |
| MCITY-Q15 | 2020 on: revised budget estimate column is optional | `semantics.yml:2612-2613, 2676-2677` | inherent |
| MCITY-Q16 | June close editions insert FYTD before accruals and net accruals for both years (13 columns) | `semantics.yml:2255-2274`; `semantics.py:836-850` | inherent |
| MCITY-Q17 | July editions repeat month values as FYTD | `collections-monthly.yml:2010-2015`; `tests/test_table_primitives.py:1070-1080` | inherent |
| MCITY-Q18 | Text layer paints labels and amounts twice: welded copies (PICAWAGETAX), comma-less twins, amounts inside label spans | `tables/line_repair.py:426-464`; `tables/row_detection.py:152-165`; `tests/test_table_primitives.py:712-725` | inherent |
| MCITY-Q19 | A comma-less twin thrown into a neighbouring column survives as a cell | `tests/test_table_primitives.py:1082-1094` | unsure: may be an effect of old column bucketing. Rendering one affected page would settle it |
| MCITY-Q20 | 2014-07 to 2015-11: labels on their own baseline above their amounts | `collections-monthly.yml:18-26` | inherent |
| MCITY-Q21 | Labels truncated by column width | `config/entities.yml` aliases; `tests/test_entities.py:1662-1676` | inherent |
| MCITY-Q22 | Line items renamed across editions | `config/entities.yml` aliases | inherent |
| MCITY-Q23 | Current/prior split printed as qualifier rows or as label suffixes | `config/entities.yml` `qualifiers`; `tests/test_resolution.py:2920-2940` | inherent |
| MCITY-Q24 | 2015 compound headings, such as "WAGE, EARNINGS AND NET PROFITS TAX CITY WAGE" | `tests/test_entities.py:1642-1660` | inherent |
| MCITY-Q25 | Parking labels repeat in General Fund and dedicated-fund blocks | `semantics.yml:2561-2572` | inherent |
| MCITY-Q26 | Dedicated Parking row has a printed remaining-budget identity using revised budget when present | `semantics.yml:2644-2662` | inherent |
| MCITY-Q27 | FY2024 on: General Fund Parking and Valet print N/A in current columns; only 2024-04 is configured | `collections-monthly.yml:2-17` | inherent; coverage of other editions unknown |
| MCITY-Q28 | 2025-06 prints HOTEL TAX for TOTAL HOTEL FUND | `collections-monthly.yml:2126-2133`; `config/entities.yml` `scoped_aliases` | inherent |
| MCITY-Q29 | 2023-07 page 4: orphan (359,304,205) under TOTAL GENERAL FUND | `collections-monthly.yml:27-34` | inherent |
| MCITY-Q30 | Combined total printed above its deduction and net (GFP, LESS PICA, TGF) | `tables/totals.py:1958-1985` | inherent |
| MCITY-Q31 | Deduction row restates the three PICA subtotals under a truncated label | `tables/totals.py:2471-2477` | inherent |
| MCITY-Q32 | A measure printed only at subtotal level (BIRT and beverage budgets, 2026-08) | `tables/totals_coverage.py:212-222`; `collections-monthly-city-2026-08.yml` BIRT reason | inherent |
| MCITY-Q33 | Dashes meaning zero in some lanes | `tables/reconcile.py:1330-1349`; `collections-monthly-city-2026-08.yml:19-24` | inherent |
| MCITY-Q34 | N/A cells, including all-N/A fund rows | `tables/classification.py:1080-1086`; `release-notes/data/2026.08.02.yml:111-114` | inherent |
| MCITY-Q35 | Each null source cell opens a presence assertion that blocks trust | `tables/reconcile.py:1000-1045`; `export.py:1045-1070` | artifact: no cell type for dash and N/A, so arithmetic cannot skip them |
| MCITY-Q36 | August 2026 has its own layout file | `config/layouts.yml:1-3, 13-14`; `tests/test_layout_composition.py:233-234` | artifact: first match wins across fragments, so the 63 reviews must load before the `collections_monthly_city_*` catch-all |
| MCITY-Q37 | Two empty profiles shadow the catch-all for 2023-08, 2023-09, 2025-07, 2025-08 | `collections-monthly.yml:1986-1990, 2053-2057` | artifact (first match, no inheritance) |
| MCITY-Q38 | Semantics profile lists 2021-01 to 2021-06, but an earlier profile already matches them | `semantics.yml:2640-2641, 2679-2682` | artifact (dead glob) |
| MCITY-Q39 | GFP vertical sum broken in 52 editions | `collections-monthly.yml:117-1333, 1434-1985` | inherent |
| MCITY-Q40 | FY2022 revised budget: City wage subtotal adds City and PICA current rows (+502,034,000, opposite on PICA) | `collections-monthly.yml:1434-1985`; `tests/test_collections_source_acknowledgments.py:36-145` | inherent |
| MCITY-Q41 | PICA deduction disagrees with its parts (2017-01; 2022-02 to 2022-06) | `collections-monthly.yml:756-778, 1434-1985` | inherent |
| MCITY-Q42 | 2016-02 budget total keeps an unitemized 5,700,000 | `collections-monthly.yml:2139-2188`; `cross_document_totals.py:509-535` | inherent |
| MCITY-Q43 | 2018-03 beverage total prints current FYTD as the increase and leaves prior FYTD blank | `collections-monthly.yml:1333-1368` | inherent |
| MCITY-Q44 | 2020-06 monthly local non-tax total is a typo; governmental accrual columns transposed | `collections-monthly.yml:1369-1433` | inherent |
| MCITY-Q45 | 2024-07 TOTAL TAX REVENUE prior-period off by 188,954 in both duplicated cells | `collections-monthly.yml:1991-2052` | inherent |
| MCITY-Q46 | Whole-dollar rounding: 1 dollar per subtotal, up to 3 on long leaf sums | `collections-monthly-city-2026-08.yml` GFP reasons; `collections-monthly.yml:2128-2131` | inherent |
| MCITY-Q47 | A 2022-07 acknowledgment turned out to be an extraction error and was retired | `tests/test_collections_source_acknowledgments.py:278-296` | artifact; the lesson (an unused acknowledgment must fail) is inherent |
| MCITY-Q48 | Acknowledgments keyed by table index, row index, column index and hypothesis name; 60 of 74 lack fingerprints | `collections-monthly.yml`; `config/layouts.yml:5` | artifact |
| MCITY-Q49 | Literal asterisk in a label collides with glob matching | `acknowledgments.py:50-69` | artifact (glob patterns); the asterisk ink is inherent |
| MCITY-Q50 | Block placement shifts: TOTAL TAX REVENUE on page 3 in 2016-02, page 2 in 2024; GFP on page 3 in 2019-08 | `tests/test_collections_source_acknowledgments.py:13-34, 148-171` | inherent |
| MCITY-Q51 | Column index of the same measure moves by one when the optional estimate column prints (2017 to 2019 GFP records use 4, 6 and 7) | `collections-monthly.yml:730-1332` | artifact (positional indices) |
| MCITY-Q52 | Stray leading or trailing column shifts positional role mapping | `semantics.py:2107-2111` | unsure: may come from old column detection; a header-word grid match would show |
| MCITY-Q53 | Printed FYTD date range contradicting the edition's period | `semantics.py:226-262` | unsure: no City case recorded |
| MCITY-Q54 | Family hard-coded in staleness and source audit | `staleness.py:537-557`; `revenue_collections.py:60-63` | artifact |
| MCITY-Q55 | Release fails if no City document is eligible (exact-value contract) | `release_packaging.py:700-710`; `config/release_contracts.yml:4-6` | artifact |
| MCITY-Q56 | Current fiscal-year listing page may not exist yet | `phila_source_sync.py:201` | inherent |
| MCITY-Q57 | Prior-year columns can disagree with last year's own edition | `series_checks.py:179-202` | unsure: frequency not recorded; a corpus run of A15 would settle it |
| MCITY-Q58 | 201 default facts lack a stable entity (91,914 trusted versus 91,713 entity observations) | `notebooks/monthly_revenue_tracker.ipynb:44, 549` | unsure: could be orphan rows or memo rows; the release files would settle it |

## 10. Old code that serves this family

| Job | File (lines) | Keep as code | Keep as knowledge |
|---|---|---|---|
| Acquisition | `revenue_collections.py` (888) | listing regex, `_month_year`, period evidence, Damerau month match, alias rule, validate-then-replace | integrity report models and counts |
| Acquisition | `phila_source_sync.py` (231) | URL pattern and `allow_unpublished` | registry wiring |
| Acquisition | `phila_media.py` (932) | `MONTHS` table | rest |
| Layout | `config/layouts/collections-monthly.yml` (2,188, City part about 2,050) | none | 4 rules and 74 source defects, to rebind by page and label |
| Layout | `config/layouts/collections-monthly-city-2026-08.yml` (1,041) | none | two cell rules: dash may mean zero, N/A stays null |
| Semantics | `config/semantics.yml:2255-2315, 2558-2828` (about 330) | none | the era grids, caption words, parking scope and identity |
| Semantics | `semantics.py` (2,326) | `naming_context` year logic (1702-1760) | header layout selection, shift variants |
| Entities | `config/entities.yml` (70 City entities) | none | alias list, qualifiers, scoped HOTEL TAX |
| Text repair | `tables/line_repair.py` (464), `tables/row_detection.py:152-334` | overprint dedupe and welded-word drop, rewritten at word level | stacked-label case |
| Checks | `tables/totals.py` (2,907), `tables/totals_coverage.py` (494), `tables/reconcile.py` (1,471) | none | relations A1 to A12 |
| Checks | `series_checks.py` (203) | delta, accrual and continuity checks | severity grading |
| Checks | `cross_document_totals.py` (951) | none | omitted contributors can be proved from the adjacent month |
| Tests | `test_revenue_collections.py` (358), `test_collection_source_integrity.py` (294), three acknowledgment tests (973) | the 358-line listing and period tests | defect lists as fixtures |

## 11. The least a parser needs

Inputs: the PDF bytes, its SHA-256, and the listing's fiscal year and month.

1. Confirm the period. Read page 1 text. Find "MONTH OF <month>" near the title. Accept one-edit month typos only when unique. Take the year from the title, else one printed FY label, else a unique body "Month YYYY". Reject a mismatch with the listing.
2. Read words from all pages. Collapse overprinted duplicates that overlap in geometry. Keep equal values that sit in different columns.
3. Drop the repeated header on pages 2 to 4. Read caption words to choose the grid.
4. Assign columns by caption, not by position. Grids by era: 10-column ordinary, optional revised or current estimate, optional prior-year budget and final (2014 to 2019), 13-column close.
5. Build rows. Attach a label printed on the line above its amounts (2014-07 to 2015-11). Keep truncated labels as printed.
6. Type each cell as amount, zero-dash, N/A or blank. Never write a number for N/A. A dash becomes zero only where a declared rule says so.
7. Resolve labels to entities with scope: General Fund versus dedicated funds, Hotel Fund context, current/prior qualifiers.
8. Emit one fact per cell with page, label, role, value year and raw text.

Parameters that differ by era: grid variant, month caption year basis (calendar before July 2021, fiscal after), stacked labels, the parking N/A scope from FY2024.

Checks to declare: A1 to A12 within an edition, with a 1-dollar tolerance per subtotal and a stated wider bound for the grand totals. A13 to A16 across editions. Pin the 74 known defects by document hash, page, row label, column caption and exact residual.

## 12. Unknowns

- The exact 601 withheld cells, and which edition lacks a default TOTAL GENERAL FUND monthly value.
- Whether FY2024 and later editions other than 2024-04 print N/A for General Fund Parking and Valet.
- Whether the 2026-08 dash and N/A presentation holds for the rest of FY2027.
- Why the 2017 to 2019 GFP overstatement grows through each year. The defect is acknowledged, not explained.
- Whether 2017-06, 2018-01, 2018-02 and 2019-03 to 2019-07 reconcile or are withheld.
- The month the beverage tax rows first appear.
- How often prior-year columns are restated against last year's edition.
- Whether any City listing has carried a fiscal-year filename or a second link for one month.
- Exact row lists and page breaks per era. These need the PDFs.
