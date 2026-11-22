# RTT: Philadelphia Realty Transfer Tax collections

Dataset `collections_realty_transfer_tax`. Paths are shortened by dropping
`packages/gov-budget-etl/src/gov_budget_etl/`. Test paths start at `tests/` under
`packages/gov-budget-etl/`. The checkout has no PDFs, so every statement about page content
comes from config comments, acknowledgment records, tests, release notes or the audit docs.

The owner calls this report "real estate transfer by sector". It has no industry sector. Each
analytical page prints the same transactions classified two ways: by property type and by
location. The 12 typed subsets are those 2 classifications times 6 period presentations. That
split is an artifact of how the old engine names table types (RTT-Q46).

## 1. Documents

The Revenue Department publishes one documents page per calendar year at
`https://www.phila.gov/documents/{year}-realty-transfer-tax-collection/`. The 2015 page alone
has a `-2` slug suffix (`realty_transfer_tax.py:48-51`, `tests/test_realty_transfer_tax.py:110-112`).
A page whose year is not yet published returns 404 (`docs/philly-source-monitoring-audit-2026-09-11.md:36`).

Each page lists PDF links among other documents. Only anchors whose title plus filename contain
"realty", "transfer" and "tax" are kept (`realty_transfer_tax.py:89-92`). The report period comes
from the link title first, then the filename, then the page year (`realty_transfer_tax.py:54-79`).

Cadence and count. The catalog shows 60 source documents, FY2013 to FY2025
(`docs/site/data/index.md:376-379`). The count is consistent with this breakdown, which I inferred
and did not confirm document by document:

| Years | Cadence | Editions | Key months |
|---|---|---|---|
| 2013 to 2019 | calendar quarter | 28 | 03, 06, 09, 12 |
| 2020 | month | 12 | 01 to 12 |
| 2021 | January monthly, then quarterly | 5 | 01, 03, 06, 09, 12 |
| 2022 to 2024 | calendar quarter | 12 | 03, 06, 09, 12 |
| 2025 | calendar quarter | 3 | 03, 06, 09 |

The first edition is 2013 Q1 (`tests/test_layout_composition.py:261`). The latest held is July
to September 2025 (`docs/philly-source-monitoring-audit-2026-09-11.md:36`). January 2021 and
January to March 2021 both exist (`tests/test_realty_transfer_tax.py:45-65`,
`config/semantics.yml:3086-3088`).

Scans and text layer. Nothing in config records which editions are scans. `document_metadata.yml`
has an empty list. The audit cases for 2020-08 and 2020-09 name the `geometric` backend
(`docs/investigations/unverified-row-audit/CASES.md:15-16`), so those two have a text layer.
The rest is unknown.

Pages. Acknowledgment evidence puts the quarterly tables on page 1 and the FYTD tables on page 2
(`config/layouts/collections-tax-details.yml:334,371,387,417,449,476-487`). A "Top 10
Transactions" list appears on page 3 of the December 2020 edition (`tests/test_page_types.py:724-732`).
Typical length is two or three pages. That is inferred, not verified.

## 2. Tables

A report page holds up to three stacked zones, each opened by a printed heading
(`config/page_types.yml:973-979, 1007-1049`):

- "Realty Transfer Tax by Property Type": one row per property classification.
- "Realty Transfer Tax by Location": one row per location crossed with a property group.
- "Comparison with FAMIS" or "FAMIS Total Transfer Tax": a short reconciliation of the City's
  accounting ledger (FAMIS) against the RTT data file. It has no total row (`config/page_types.yml:1050-1051`).

The page title names the period window. Seven titles exist (`config/page_types.yml:984-1005`):

| Page title | Window | Old table types | Value columns |
|---|---|---|---|
| Table 1: Monthly Collection Data | each month of the quarter, then the quarter | `*_monthly_grid` | 8: (records, tax) for month 1, 2, 3 and quarter (`config/semantics.yml:2891-2912`) |
| Monthly Comparison | one month vs same month 1 and 2 years earlier | `*_monthly_comparison` | 14: three (records, tax) pairs, two change pairs, two percent pairs (`config/semantics.yml:3093-3123`) |
| Quarterly Comparison | quarter vs prior-year quarter | `*_quarter` | 8: current pair, prior pair, change pair, percent pair (`config/semantics.yml:3257-3267`) |
| Fiscal Year to Date, FYTD Comparison, Table 3: Fiscal Year to Date | July through report month vs prior FYTD | `*_fytd` | 8, or 6 in the 2020 location grid (`config/semantics.yml:3166-3236`) |
| ... Fiscal Year Comparison | full fiscal year vs prior | `*_fiscal_year` | 8 (`config/semantics.yml:3285-3295`) |
| ... Calendar Year Comparison | full calendar year vs prior | `*_calendar_year` | 8 (`config/semantics.yml:3312-3322`) |
| Top N Transactions, Realty Transfer Tax | transaction list | `*_top_transactions` | kept as evidence only (`config/page_types.yml:984-987`) |

Every value column is a pair. "Records" is a transaction count and "local tax" is whole US
dollars (`config/semantics.yml:2840-2889`). The tax is the City's local share only, not the
state portion (notebook `notebooks/realty_transfer_tax_trends.ipynb`, closing notes).

Property table hierarchy. Rows sit under Residential, Non-residential and Vacant Land sections.
Each closes with a printed subtotal: Total Residential, Total Non-residential, Total Vacant Land
(`config/entities.yml:4017-4037`). Then Unclassified, Voided Transactions and Total RTT records
follow (`config/entities.yml:4209-4227`). Some labels repeat in more than one section, so the
section is part of the row key (`config/semantics.yml:3157-3164`).

Location table hierarchy. Rows sit under Center City and Other Neighborhoods. Each row is a
location crossed with a property group ("Center City Small Apartments"). Subtotals are Total
Center City and Total Other Neighborhoods (`config/entities.yml:4195-4208`). The same three
citywide rows close the table.

Size. Total RTT records is row 19 of the location quarter table and Total Non-residential is row
9 of the property FYTD table (`config/layouts/collections-tax-details.yml:345,487`). Tables run
about 15 to 25 rows. Every table fits on one page; nothing in config shows a table crossing pages.

Which periods print which windows. The fiscal-year table is tested on a June edition and the
calendar-year table on a December edition (`tests/test_semantics.py:502-522`). That suggests
June and December editions add a full-year page. It is not confirmed.

## 3. Format eras

| Era | Editions | Forms | Evidence |
|---|---|---|---|
| A. Legacy quarterly | 2013 Q1 to 2019 Q4 | Monthly grid (three months plus quarter), Quarterly Comparison, Table 3 FYTD, full-year pages | `config/semantics.yml:2891-2894`; notebook says quarter tables exist 2013 to 2019; `tests/test_page_types.py:734-745` (2016-12 monthly grid) |
| B. Monthly | 2020-01 to 2021-01 | 14-column Monthly Comparison, FYTD, top transactions list | `config/semantics.yml:3086-3088`; `tests/test_page_types.py:724-732` |
| C. Quarterly again | 2021 Q1 to 2025 Q3 | Quarterly Comparison, FYTD, FAMIS zone in at least 2021-12 | `realty_transfer_tax.py:4-5`; `tests/test_memo_export_contract.py:116-128` |
| C2. 2024 classification | from some 2024 edition | Apartments, condominiums and vacant land split into new classes | `config/entities.yml:3886-3890` |

Changes inside eras:

- Feb and Mar 2020 property Monthly Comparison grids extract with a lost column and a fused cell
  (`config/semantics.yml:2917-3071`).
- The 2020 location FYTD grid prints both percent changes in one cell in Feb to Jun and Aug to Dec
  2020. The property grid in the same files keeps 8 columns (`config/semantics.yml:3136-3206`).
- January 2020 FYTD omits the General Commercial label (`config/entities.yml:3904-3906`).
- Legacy property labels carry assessment use codes in parentheses, for example "General
  Commercial (88-2)". The code list on Other Non-residential gains "87" at some point
  (`config/entities.yml:3933-3935`).
- "Residential Wards (01 thru 76)" becomes "Single/Multi-family Homes (01 thur 76)" and then
  "Single/Multi-family Homes" (`config/entities.yml:3967-3970`).
- Location rows move from Residential and Non-residential aggregates to per-class rows. Then the
  2024 split happens (`config/entities.yml:4044-4112`). The year of the first change is unknown.
- FAMIS heading wording: "Comparison with FAMIS" or "FAMIS Total Transfer Tax". Which vintages
  carry it is not recorded.

## 4. Finding the table

Today. Pages are typed by title, because the marker regex is a placeholder that never matches
(`config/page_types.yml:982`). Each typed page is then split into zones at the three headings
(`page_table_scoping.py:543-605, 959-1108`). The consensus region detector keeps the strongest
grid and can clip an earlier stacked table (`page_table_scoping.py:999-1004`). When it does, the
zone is rebuilt from parse lines: slice by heading, find column bounds from lines with two or
more amounts, bin every line (`page_table_scoping.py:1170-1218`). That fallback is 47 lines and
is the whole method a clean parser needs.

Simplest reliable rule:

1. Classify a page by its title line, matched against the seven title patterns.
2. On that page, find the "by Property Type", "by Location" and FAMIS headings. Each zone runs
   to the next heading or page end. Require both classification headings on analytical pages.
3. Inside a zone, find columns from amount-bearing lines only. Assign labels by left edge.
4. Do not clip at the lowest wide rule. That clip was written for budget detail and runs on RTT
   pages today (`page_table_scoping.py:385-404, 556-566`).

## 5. Arithmetic that holds

| Relation | Scope | Declared in old config | Source breaks it |
|---|---|---|---|
| Section items sum to section subtotal | each table, each additive column | yes, by engine inference | not recorded as broken |
| All line items sum to Total RTT records | each table | yes (hypothesis `all_line_items`) | location table, 5 editions |
| Change = current minus prior, per row | comparison tables | yes (`declared_difference_identity`) | 2025-03 General Commercial; 2020-09 off by $1 |
| Percent = change / prior, rounded | comparison tables | only for 2020 monthly local tax (`config/semantics.yml:3076-3085`) | 2020-09 case matches at one decimal (`CASES.md:16`) |
| Month 1 + 2 + 3 = quarter, per measure | legacy monthly grid | no | unknown |
| Property Total RTT records = location Total RTT records | same page, every column | no, only stated in ack prose (`collections-tax-details.yml:316-318`) | never, per the five acks |
| Prior column = earlier edition's current column | quarter, FYTD, monthly | no | consistent in 2022 Q1 and 2023 Q1 (same 7,868 omission) |
| FYTD(n) = FYTD(n-1) + window(n) | consecutive editions in a fiscal year | no | unknown |
| June FYTD = fiscal-year table; December calendar-year = four quarters | full-year pages | no | unknown |
| 2020 monthly current values sum to the FYTD | 2020 editions | no | unknown |
| FAMIS total vs RTT data file | FAMIS zone | memo only; difference is published and may be nonzero (`collections-tax-details.yml:306-309`) | expected to differ |

Acknowledgment records, all in `config/layouts/collections-tax-details.yml:321-493`:

| Kind | Count | Editions |
|---|---|---|
| Location detail omits small amounts; property and location grand totals agree | 4 | 2021-12 (prior, 66,632), 2022-03 (current and prior, 7,868 and 99,782 tax, 1 and 10 records), 2022-09 (2,323), 2022-12 (2,474) |
| Same omission repeated as a later edition's prior period | 1 | 2023-03 (7,868, from 2022-03) |
| Difference column repeats current value | 1 | 2025-03 property FYTD, General Commercial (8,796,307) |

Six acks across 60 editions. Two lack both fingerprints (2022-03, 2023-03), and 2022-03 also
lacks `assertion_page`. Residuals are pinned so an extraction error cannot hide behind an ack
(`collections-tax-details.yml:316-320`). There are no RTT entries in `review-overrides.yml`.
Two audit cases add source facts that are not acks: the 2020-08 FYTD header range and the 2020-09
$1 difference (`CASES.md:15-16`).

## 6. Row labels and entities

The registry holds 44 RTT entities: 2 classification roots, 14 property leaves and 3 property
subtotals, 20 location leaves and 2 location subtotals, and 3 shared rows
(`config/entities.yml:3891-4227`). Nine entities appear in all 60 reports: the 3 shared rows,
Single/Multi-family Homes, General Commercial, Office/Hotels/Garages, Industrial, Total
Residential and Total Non-residential (notebook markdown).

Stability findings:

- Renames kept as one entity: Residential Wards to Single/Multi-family Homes; code suffixes dropped.
- Splits kept apart: legacy Apartments (88-1) vs Large and Small Apartments; legacy Condominiums
  (88-8) vs Small Condominiums; Vacant Land vs three vacant land classes; location aggregates vs
  per-class rows (`config/entities.yml:3889-3890`, `tests/test_entities.py:1513-1523`).
- Same label, different meaning: "Other Vacant Land" is a property class in one table and an
  Other Neighborhoods row in the other (`tests/test_entities.py:1497-1511`). Resolution needs the
  table's dimension.
- Same label in two sections of one table: resolution needs the section
  (`tests/test_semantics.py:1609-1634`).
- Source typos and truncations: "thur", "Mixed used", "Centery City Vacant Land", "Other
  Neighborhds Single/Multi-family Ho", "Unclassified (garb the most recent period from assessment
  file)", "Void accounts", "Large apartment" (`config/entities.yml:3943, 3969, 3978, 4118, 4156, 4214, 4220`).
- Footnote mark on the grand total: "Total RTT records **1" (`config/entities.yml:4226`).

The same tax appears in other families as a single line: "REAL ESTATE TRANSFER TAX" in monthly
City collections (`config/entities.yml:172-178`) and "Realty Transfer Tax" in QCMR cash, with an
OCR variant "Really Transfer Tax" (`config/entities.yml:1782-1789`). No cross-family check exists.

## 7. Values

- Whole dollars for tax; integer counts for records; percents for change rates
  (`config/semantics.yml:2840-2889`).
- A dash means no value. The 2020-08 voided-transaction count is a dash and is kept null
  (`CASES.md:15`).
- Percent columns are excluded from sums. The layout also sets `exclude_bare_percent_columns`
  (`collections-tax-details.yml:315, 497`), which targets percents printed without "%"
  (`tables/reconciliation_columns.py:68-100`). Whether RTT prints bare percents is not recorded.
- Printed differences can be $1 or $2 off from subtraction, from rounding of unprinted cents
  (`CASES.md:16`; `collections-tax-details.yml:378-380, 408-413`).
- Negative format: the 2023-03 ack quotes "(131,991,682)", so parentheses mark negatives
  (`collections-tax-details.yml:453-455`).

## 8. Editions and revisions

- The City appends a revised attachment for the same period on the same page. The last titled
  link wins (`realty_transfer_tax.py:85-87, 97`, `tests/test_realty_transfer_tax.py:91-106`).
- A revision posted after first download is never fetched. `is_ingested` checks only that the
  path exists, and replacement is refused (`realty_transfer_tax.py:118-135`,
  `tests/test_realty_transfer_tax.py:153-165`).
- Every edition reprints earlier periods in its prior-year columns, and Monthly Comparison
  reprints two years back. The canonical value for a period is the current-period column of the
  edition whose window is that period. The notebook builds its series that way and never uses
  prior columns. No RTT canonical-selection config exists.
- 2020 has no quarter table. A quarterly series must sum 2020 monthly current values (notebook).
- One unresolved restatement: December 2021's prior FYTD Unclassified is 72,642, but December
  2020's own FYTD Unclassified is 6,010 (`release-notes/data/2026.08.02.yml:85-89`).

## 9. Quirk ledger

| ID | What happens in the document | Where the old code handles it | Kind |
|---|---|---|---|
| RTT-Q01 | One listing page per calendar year; 2015 slug ends `-2` | `realty_transfer_tax.py:48-51` | inherent |
| RTT-Q02 | Listing pages carry unrelated PDFs | `realty_transfer_tax.py:89-92` | inherent |
| RTT-Q03 | Filename can name the wrong year or month; title is the better witness | `realty_transfer_tax.py:54-79`; `tests/test_realty_transfer_tax.py:67-82` | unsure: the case is a test fixture; archived listing HTML would settle it |
| RTT-Q04 | Title forms vary: "2014 Q4", "January 2021", "October to December 2021" (printed with a dash); quarters are calendar quarters | `realty_transfer_tax.py:17-23, 68-76` | inherent |
| RTT-Q05 | Title with no period falls back to compact `YYYYMM` in filename, then page year | `realty_transfer_tax.py:60-66, 77-78`; test `:84-89` | inherent |
| RTT-Q06 | Revised attachment appended for the same period | `realty_transfer_tax.py:85-87, 97` | inherent |
| RTT-Q07 | Revision posted after first ingest is never picked up | `realty_transfer_tax.py:118-120` | artifact: path-existence check instead of SHA tracking |
| RTT-Q08 | Quarterly and monthly editions share one ending-month key; `2020_03` is a month, `2021_03` a quarter | `realty_transfer_tax.py:4-6, 37-40` | artifact: key omits window length |
| RTT-Q09 | No check that a file's printed period matches its key | all RTT `verify_templates` are `''` (`config/semantics.yml:2915-2916, 2992-2997, 3130-3135, 3242-3246, 3273-3277, 3301-3305`) | artifact: gap; the School Dec 2015 quarantine shows the risk is real |
| RTT-Q10 | Next year's page 404s until published; monitored from 2025 by calendar year | `phila_source_sync.py:204-220`; `config/source_sync.yml:13-14` | inherent (404); artifact (start year) |
| RTT-Q11 | Two or three independent tables stacked on one page | `config/page_types.yml:1007-1049` | inherent |
| RTT-Q12 | Page typing by title; marker regex is a never-matching placeholder | `config/page_types.yml:982` | artifact: profile schema requires a marker |
| RTT-Q13 | Seven page titles; FYTD has three wordings; year-comparison titles are unanchored | `config/page_types.yml:984-1005`; `tests/test_page_types.py:697-722` | inherent |
| RTT-Q14 | Top transactions page is not an aggregate table | `config/page_types.yml:984-987` | inherent |
| RTT-Q15 | FAMIS zone: comparator rows, no total, spelling "Data file" and "Datafile" | `config/page_types.yml:1050-1051`; `collections-tax-details.yml:306-314`; `tests/test_memo_export_contract.py:116-128` | inherent |
| RTT-Q16 | Region detector clips one stacked grid | `page_table_scoping.py:999-1004, 1081-1098, 1170-1218` | artifact: consensus region detection |
| RTT-Q17 | Budget-detail box-bottom clip runs on RTT pages | `page_table_scoping.py:385-404, 556-566` | artifact: shared parse cleanup |
| RTT-Q18 | Page with no zone heading stays whole under its form type, which has no semantics profile | `page_table_scoping.py:978-979, 1048-1049` | artifact: should fail instead |
| RTT-Q19 | Legacy grid: three months then quarter, each a (records, tax) pair | `config/semantics.yml:2891-2912` | inherent |
| RTT-Q20 | 2020 and Jan 2021 Monthly Comparison has 14 columns over three years | `config/semantics.yml:3072-3135` | inherent |
| RTT-Q21 | Feb and Mar 2020 property comparison: lost column, fused cell, empty slots; pinned by absolute index | `config/semantics.yml:2917-3071`; `tests/test_semantics.py:450-484` | unsure: render the page and inspect word boxes |
| RTT-Q22 | 2020 location FYTD prints both percents in one cell; property grid in the same file does not | `config/semantics.yml:3136-3206`; `tests/test_semantics.py:301-325, 486-500` | unsure: same test |
| RTT-Q23 | Jan 2020 FYTD prints "Non-residential" where "General Commercial" belongs | `config/entities.yml:3904-3906` | inherent |
| RTT-Q24 | Aug 2020 FYTD header reads July 2019 to August 2020 | `normalization.py:234-245`; `semantics.py:225-262`; `release-notes/data/2026.08.02.yml:73-75` | inherent |
| RTT-Q25 | Sep 2020 printed difference 836,440; subtraction gives 836,439 | none; audit case `CASES.md:16` | inherent |
| RTT-Q26 | Difference residuals off by 1 to 2 dollars from rounding | `collections-tax-details.yml:378-380, 408-413` | inherent |
| RTT-Q27 | Location detail omits small amounts; grand totals still match property table | `collections-tax-details.yml:321-434` | inherent |
| RTT-Q28 | Omission carried into a later edition's prior column | `collections-tax-details.yml:435-464` | inherent |
| RTT-Q29 | Location difference total computed from grand totals, not from its own rows | `collections-tax-details.yml:358-367` | inherent |
| RTT-Q30 | 2025-03 General Commercial difference repeats current value | `collections-tax-details.yml:465-493` | inherent |
| RTT-Q31 | Dec 2021 prior FYTD Unclassified 72,642 vs Dec 2020 6,010 | `release-notes/data/2026.08.02.yml:85-89` | unsure: compare both rendered pages |
| RTT-Q32 | Property labels repeat under Residential and Non-residential | `config/semantics.yml:3157-3164`; `tests/test_semantics.py:1609-1634` | inherent |
| RTT-Q33 | Same label means different rows in property and location tables | `config/entities.yml:3886-3888, 4009-4016, 4187-4194`; `tests/test_entities.py:1497-1511` | inherent |
| RTT-Q34 | Section and dimension scope declared on some profiles only (absent on monthly grid, fiscal-year, calendar-year; no section rules on monthly comparison) | `config/semantics.yml:2835-2916, 3072-3075, 3278-3324` | unsure: check whether those tables repeat labels |
| RTT-Q35 | Label drift: ward wording, assessment code suffixes, code list grows | `config/entities.yml:3897-3972` | inherent |
| RTT-Q36 | 2024 classification split; old and new classes do not join | `config/entities.yml:3889-3890, 3946-4016, 4044-4112` | inherent |
| RTT-Q37 | Typos and truncated labels in the source | `config/entities.yml:3943, 3969, 3978, 4118, 4156, 4214, 4220` | inherent |
| RTT-Q38 | Footnote mark on grand total label | `config/entities.yml:4226` | inherent |
| RTT-Q39 | Dash for a missing count | `CASES.md:15` | inherent |
| RTT-Q40 | Percent columns possibly printed without "%" | `collections-tax-details.yml:315, 497` | unsure: inspect any legacy page |
| RTT-Q41 | One document mixes year bases: quarter, month and calendar-year tables use the key's calendar year; FYTD and fiscal-year tables use the fiscal year | `config/semantics.yml:3165, 3217, 3284`; `semantics.py:980-983`; `normalization.py:651-654` | inherent |
| RTT-Q42 | Release column `fiscal_year` holds a calendar year for quarter tables | notebook uses it as calendar year | artifact: one year field for two bases |
| RTT-Q43 | Percent identity declared only for 2020 monthly local tax | `config/semantics.yml:3076-3085` | artifact: per-profile declaration |
| RTT-Q44 | Property total equals location total, never declared as a check | stated in `collections-tax-details.yml:316-318` only | artifact: no cross-table checks for this family |
| RTT-Q45 | Acks keyed to table index, row index, hypothesis string and fingerprints; two lack fingerprints, one lacks page | `collections-tax-details.yml:321-493` | artifact |
| RTT-Q46 | 12 typed subsets: table type encodes dimension and window | `config/page_types.yml:1007-1049`; `docs/site/data/index.md:390-401` | artifact |
| RTT-Q47 | Ack profile repeats family options by YAML anchor because the first matching profile wins | `collections-tax-details.yml:298-315, 494-497`; `layouts.py:1408-1410` | artifact |
| RTT-Q48 | 2020 has no quarter table | notebook markdown | inherent |
| RTT-Q49 | FAMIS total could be checked against monthly City and QCMR cash lines | none | unsure: needs units and timing basis from the PDFs |

## 10. Old code that serves this family

| Job | File and lines | Keep as code | Keep as knowledge |
|---|---|---|---|
| Acquisition | `realty_transfer_tax.py` (135) | title-first period parser, `-2` slug, last-link-wins | path-existence ingest check |
| Acquisition | `phila_source_sync.py:105-114, 204-220`; `commands/collections.py:369-435` (67); `Justfile:387-395` | none | calendar-year page rule |
| Page typing | `config/page_types.yml:973-1051` (79) | the seven titles and three headings as data | marker placeholder |
| Zoning | `page_table_scoping.py:795-1262` (about 470, shared) | the 47-line zone rebuild at 1170-1218 | the rest |
| Semantics | `config/semantics.yml:2835-3324` (490) | column orders per form | 2020 sparse and compact pins |
| Checks | `config/layouts/collections-tax-details.yml:298-497` (200) | six acks rebound to page, label, measure, residual | engine hypothesis names |
| Entities | `config/entities.yml:3886-4227` (342) | 44 entities, aliases, split decisions | |
| Tests | `tests/test_realty_transfer_tax.py` (165); `test_semantics.py:301-325, 411-522`; `test_entities.py:1478-1523`; `test_page_types.py:697-745` | listing fixtures, entity cases | profile-match tests |

## 11. The least a parser needs

Inputs: the PDF bytes, its SHA-256, and the listing title that named it.

Steps:

1. Read the report period from the page 1 title text. Reject the file if it disagrees with the
   listing title. Record window length (month or quarter) as data.
2. Classify each page by title into one of six windows, or the transaction list.
3. Split each analytical page at the property, location and FAMIS headings.
4. Per zone, find value columns from amount lines. Map them by a per-form column order.
5. Read labels, section headings and row kinds (item, subtotal, Unclassified, Voided, grand total).
6. Parse amounts: commas, parentheses negatives, dash as null, percent sign optional.
7. Emit one long table: edition, window, dimension (property or location), section, label,
   column role (current, prior, prior-2, change, percent), measure (records or tax), value, page.

Era parameters: the column order per form (8, 14 or 6 columns), and the 2020 fused-cell layouts
if they prove real.

Checks to declare:

- Items to subtotal and items to Total RTT records, per table and measure.
- Change equals current minus prior, tolerance 2 dollars.
- Percent equals change over prior at printed precision.
- Legacy grid: three months sum to the quarter.
- Property grand total equals location grand total, every column.
- Prior columns equal the earlier edition's current columns.
- Six acks, each bound to edition, page, table, label, measure and residual.

## 12. Unknowns

- Which editions are scans, and page counts per edition.
- Exact edition where the location table moved to per-class rows, and where the 2024 split starts.
- Which vintages carry the FAMIS zone, and its row labels.
- Whether June and December editions always add full-year pages.
- Whether the 2020 fused cells (Q21, Q22) are in the PDF or come from column detection.
- Whether RTT prints bare percents (Q40).
- Whether the legacy month grid and the cross-edition chains hold; no check was ever run.
- The Dec 2020 vs Dec 2021 Unclassified conflict (Q31).
- Whether the misleading-filename test case (Q03) came from a real listing.
