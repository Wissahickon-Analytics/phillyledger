# BSALES: Philadelphia BIRT by sector and Sales Tax by sector

Datasets `collections_birt_sector` and `collections_sales_tax_sector`. Paths are shortened by
dropping `packages/gov-budget-etl/src/gov_budget_etl/`. Test paths starting with `tests/` are under
`packages/gov-budget-etl/`. The checkout has no PDFs. Every statement about page content comes from
config comments, acknowledgment records, tests, notebooks, release notes or the audit docs.

The two series share a publisher (the Revenue Department), a shape (one sector grid per year)
and a problem (overlapping editions). They differ in almost
everything else. BIRT is by calendar tax year from cumulative filing snapshots. Sales tax is by
fiscal year from annual reports. Neither shares a sector classification with the other or with
wage tax by industry (section 6).

## 1. Documents

### BIRT by sector

One documents page lists every edition:
`https://www.phila.gov/documents/business-income-and-receipts-tax-by-sector/` (`birt_sector.py:22`).
Links are kept when title plus filename contain "birt" or "business income" (`birt_sector.py:72-73`).

Each PDF is a cumulative filing snapshot that covers several tax years. Editions overlap, and a
later edition revises earlier years as more returns arrive (`birt_sector.py:3-10`). Six editions
are held, matching the live page on 2026-09-11 (`docs/philly-source-monitoring-audit-2026-09-11.md:38`).

| Edition (coverage) | Release date in test fixture | Canonical tax years today |
|---|---|---|
| 2004-2017 | 2019-05-21 | 2004 to 2007 |
| 2008-2018 | 2020-03-26 | 2008 |
| 2009-2019 | 2021-04-06 | 2009 to 2017 |
| 2018-2021 | 2023-06-14 | none |
| 2018-2022 | 2025-03-18 | none |
| 2018-2023 | 2025-12-01 | 2018 to 2023 |

The release dates come from `tests/test_birt_sector.py:107-114`. They look like real upload
stamps, but nothing confirms them. The canonical split is in `config/semantics.yml:3889-3931`
and `README.md:324-331`.

Coverage is read from the listing title when it holds two years, else from the filename
(`birt_sector.py:67-82`). Release order comes from the upload stamp in the media URL,
`/media/YYYYMMDD.../` (`birt_sector.py:25, 55-64`).

Pages. Each page is one ruled table comparing two tax years (`config/page_types.yml:937-941`).
Acknowledgments place tax year 2017 on page 1 of the 2004-2017 edition and 2018 on page 3 of the
2018-2023 edition (`config/layouts/collections-tax-details.yml:240-251, 273-285`). That fits a
newest-first layout of one page per pair: 7 pages for 2004-2017 and 3 for 2018-2023. Editions
with an odd number of years (2008-2018, 2009-2019, 2018-2022) cannot pair cleanly. How they are
paged is unknown.

### Sales tax by sector

One documents page lists the series:
`https://www.phila.gov/documents/annual-sales-tax-collections-reports/` (`sales_tax_sector.py:23`).
Links are kept when title plus filename contain "sales" and "tax" (`sales_tax_sector.py:67-69`).

Seven attachments hold 14 annual tables, FY2006 to FY2018 and FY2020
(`docs/philly-source-monitoring-audit-2026-09-11.md:39`, `README.md:26`). The two oldest
attachments bundle one annual table per page (`sales_tax_sector.py:3-5`). The test fixtures use
"2006-2009" and "2010-2014" bundles (`tests/test_sales_tax_sector.py:53-56`). Two bundles of 4 and
5 years plus five single years gives exactly 7 and 14, so the bundles are probably FY2006-2009
and FY2010-2014. That is inferred.

No FY2019 report was published. FY2019 exists only in the FY2020 report's prior-year column
(`notebooks/sales_tax_sector_trends.ipynb`, first and fifth cells).

Pages. Every page of every attachment carries the title "Fiscal Year YYYY Collections" or
"... Collections Report". Ingest fails when any page lacks it (`sales_tax_sector.py:159-165`).
So every annual table is exactly one page, and every page has a text layer.

### Scans and text layer

No config records which editions are scans. `config/document_metadata.yml` holds an empty list.
For sales tax the ingest title check proves a text layer on every page (above). The audit names the
`geometric` backend for FY2015 and FY2016 (`docs/investigations/unverified-row-audit/CASES.md:17-18`).
Split words in aliases ("truc k", "s oftware", "Sales T ax") show a text layer with
letter-spacing gaps (section 6). For BIRT nothing records the text layer status.

## 2. Tables

### BIRT: `birt_sector_by_tax_year`

A row is one sector or sub-sector. A page has a fixed grid of 8 value columns. The first four are
accounts, net income, gross receipts and total for the leading tax year. The last four repeat them
for the prior tax year (`config/semantics.yml:3862-3888`). Net income plus gross receipts equals total
(`notebooks/birt_sector_trends.ipynb`, "Citywide nominal revenue" cell).

Header. Above the grid the page prints a title, a Period line and a Tax Year caption line:

```
Summary of Business Income & Receipts Tax (BIRT) Revenues
Period: 12/31/2022 (Preliminary) Period: 12/31/2021
Tax Year 2022 (returns filed thru 11/14/2023) Tax Year 2022 (returns filed thru 11/14/2023)
```

This is the fixture at `tests/test_page_types.py:627-654`. The second caption is the known defect
(BSALES-Q18).

Rows. 35 identities: 20 top-level sectors, 14 sub-sectors under three parents, and Total
(`notebooks/birt_sector_trends.ipynb`, "Sector hierarchy" cell; `config/entities.yml:4229-4429`).
Both acknowledgments put Total at row index 34 (`collections-tax-details.yml:250-251, 284-285`).
That means 34 body rows above it and no value-less heading rows.

| Level | Rows |
|---|---|
| Rollup | Total |
| Sector | Construction; Manufacturing (printed "Manufacturing, subtotal"); Wholesale Trade; Retail Trade; Transportation and Storage; Information (printed "Information, subtotal"); Banking and Related Activities; Financial Investment Services; Insurance; Real Estate (including REITS); Professional Services (printed "Professional Services, subtotal"); Business Support Services (printed with "**1"); Educational Services; Health and Social Services; Sports; Hotels and Other Accommodations; Restaurants, Bars, and Other Food Services; Other Repair and Personal Services (printed "Other Services **2"); All Other Sectors; Unclassified |
| Sub-sector of Manufacturing | Food and Beverage Products; Chemicals, Pharmaceuticals & Petroleum; Other Manufacturing |
| Sub-sector of Information | Publishing; Broadcasting (TV and Radio); Telecommunications; Other Information |
| Sub-sector of Professional Services | Legal Services; Accounting, Tax and Payroll Services; Architect and Engineering; Computer Services; Management and Technical Consulting; Advertising; Other Services (printed "Other Services") |

Sources: names and parents at `config/entities.yml:4234-4429`; printed forms at
`config/entities.yml:4248, 4287, 4337, 4380, 4417` and `tests/test_entities.py:1838-1874`. The order
is registry order. It probably follows print order, but that is not verified. Whether a
"subtotal" row sits above or below its children is not recorded.

Multi-page. Each page is its own table. Pages must never be stitched (BSALES-Q19). Size: 35 rows
by 8 values, 280 cells per page. The canonical dataset is 35 rows by 4 measures by 20 years,
2,800 values (`docs/site/data/index.md:327`, `notebooks/birt_sector_trends.ipynb` audit cell).

### Sales tax: `sales_tax_sector`

A row is one sector, one Retail store type, or one of four bottom rows. Columns by era:

| Era | Value columns, left to right |
|---|---|
| FY2006 to FY2016 | entity count; local tax; percent of total |
| FY2017, FY2018, FY2020 | entity count; local tax FY; percent of total; local tax FY-1; FY-2; FY-3; % current vs prior; % prior vs prior 2; % prior 2 vs prior 3; 3-year annualized %; current minus prior ($) |

Source: `config/semantics.yml:3621-3711`, read right to left. Header text was never checked
(BSALES-Q37).

Rows. 31 identities over all years (`packages/gov-budget-data/tests/test_real_artifacts_optional.py:89-118`):

| Level | Rows |
|---|---|
| Sector (15) | Construction; Manufacturing; Public Utilities; Telecommunications; Wholesale; Delivery/couriers (FY2020 report only); Car and truck rental; Rentals except car and truck rentals; Repair services; Services other than repair services; Hotels; Restaurants, bars, concessionaires and caterers; All Other Sectors; Retail (printed "Total Retail"); Unclassified |
| Store type under Retail (12) | Furniture stores retail; Appliance, other electronics, retail; Computer and software stores, retail; Home centers, retail; Supermarkets, retail; Convenience stores, retail; Liquor and beer stores, retail; Pharmacies, retail; Department stores, retail; Office supplies stores, retail; Online retailers (FY2020 report only); Other retail |
| Bottom rows (4) | Subtotal; Motor Vehicle Sales Tax; Total Philadelphia Sales Tax; Total FYyy Sales Tax per FAMIS (Accrual Basis) |
| Memo (not exported) | FAMIS amount as a percent of total |

Sources: `config/entities.yml:3688-3884`, `config/layouts/collections-tax-details.yml:4-20`. The
registry order is not print order. Retail prints as a parent followed by its store types
(`collections-tax-details.yml:4-11`). Before FY2020 the block ends at "Car and truck rental". In
FY2020 the rentals move above Retail and the block ends at "Unclassified".

So the tables before FY2020 have 14 sectors and 11 store types. Delivery/couriers and Online
retailers have values for 2017 to 2020 only, all from the FY2020 report's comparison columns
(`test_real_artifacts_optional.py:109-112`).

Totals sit in a ruled box below footnotes in some legacy tables (`collections-tax-details.yml:25`,
`tables/region_detection.py:331-345`). Which rows the box holds is not recorded. Size: about 30 rows
by 3 or 11 columns. The dataset is 1,884 values (`docs/site/data/index.md:353`).

## 3. Format eras

| Series | Years | Change | Evidence |
|---|---|---|---|
| BIRT | older pages | Title "Summary of Business Privilege Tax (BPT) Revenues" | `config/page_types.yml:948`, `tests/test_page_types.py:656-672` |
| BIRT | newer pages | Title "Summary of Business Income & Receipts Tax (BIRT) Revenues" | same |
| BIRT | newer editions | "(Preliminary)" after the leading Period date | `config/page_types.yml:951`, `tests/test_page_types.py:633-651` |
| BIRT | 2018-2022 edition | Right caption repeats the leading Tax Year and filing date | `config/page_types.yml:937-941`, `tests/test_page_types.py:637-640` |
| BIRT | all | Same 35 rows, 8 columns, 2004 to 2023 | `test_real_artifacts_optional.py:63-86` |
| Sales | FY2006-FY2014 | Bundled in two attachments, one page per year | `sales_tax_sector.py:3-5` |
| Sales | FY2006-FY2016 | 3 value columns | `config/semantics.yml:3621-3623, 3693-3711` |
| Sales | FY2017, FY2018, FY2020 | 11 value columns with three prior years and growth | `config/semantics.yml:3621-3692` |
| Sales | FY2019 | No report published | `README.md:26`, sales notebook |
| Sales | FY2020 | Rentals move above Retail; Delivery/couriers and Online retailers added; title may read "Collections Report" | `collections-tax-details.yml:4-11`, `tests/test_sales_tax_sector.py:110` |

Which BIRT pages use the BPT title is not recorded. The BPT fixture is synthetic. The real-corpus
test asserts all 35 identities have every tax year 2004 to 2023. So the row set did not change
when the tax was renamed, at least in the canonical editions.

## 4. Finding the table

Today, both series are typed by page title only. The required `marker_line_pattern` is filled
with a code that cannot match (`config/page_types.yml:890, 944`). The title rules are:

- Sales: `^Fiscal Year\s+(?:19|20)\d{2}\s+Collections(?: Report)?$` (`config/page_types.yml:891-894`).
- BIRT: `^Summary of Business (?:Income & Receipts Tax \(BIRT\)|Privilege Tax \(BPT\)) Revenues$`
  (`config/page_types.yml:942-948`). Untitled pages are evidence only (`:949`).

BIRT also needs two context captures per page (`config/page_types.yml:950-952`): the Period line
gives `tax_year`, its status, and `prior_tax_year`; the caption line gives two filing-through
dates. Pages are partitioned by `tax_year` so the stitcher cannot merge them (`:953-955`).

The table region is found by the generic geometric engine. The engine begins the region at the
first data row (`config/semantics.yml:3684-3685`). For sales tax a drawn total box below
footnotes must be rejoined (`collections-tax-details.yml:25`).

Simplest reliable rule:

- Sales: one page per year. Assert the title and read the fiscal year from it. Assert it matches
  the listing. Read rows from the first sector row to "Total FYyy Sales Tax per FAMIS" or the FAMIS
  percent memo, including the drawn box.
- BIRT: every page whose title matches is one table. Read the two years from the Period line,
  never from the caption. Fail if the Period line is missing. Read rows from the first sector to
  "Total". Each page stands alone.

## 5. Arithmetic that holds

### BIRT, per page and per half (8 column checks each)

| Relation | Declared today | Source breaks |
|---|---|---|
| Total = sum of the 20 top-level rows (subtotal rows count, sub-sectors do not), each of 8 columns | Found by the engine as `same_depth_rows_above` | 2 cells in the corpus |
| Parent subtotal = sum of its children (3, 4, 7 rows), each column | Not declared. Depends on the indentation trial | Unknown |
| Total = Net Income + Gross Receipts, each row, each half | Not declared | Not checked. The 2018 Total row breaks it |
| Accounts additive down the column | Checked (column 1 and 5 are not excluded) | 1 cell |
| Cross-edition: same tax year in two editions | Not a check. Revisions are expected | Not applicable |

Acknowledgments for BIRT: 2 records, both kind "printed total disagrees with printed parts".

| Edition, page, column | Year | Printed | Sum of parts | Residual | Record |
|---|---|---|---|---|---|
| 2004-2017, p1, col 1 (accounts) | 2017 | 32,956 | 34,487 | -1,531 | `collections-tax-details.yml:224-257` |
| 2018-2023, p3, col 8 (total) | 2018 | 468,801,829 | 468,794,493 | 7,336 | `collections-tax-details.yml:258-291` |

The 2018 defect is on a canonical year, so a published canonical Total is a wrong printed number.
The 2017 count defect is on a superseded year. Whether the 2009-2019 edition's 2017 page reconciles
is not recorded. The BIRT notebook says the account mismatch is in the 2018-2023 table. That text
predates the current records and is wrong against them.

### Sales tax, one table per year

| Relation | Declared today | Source breaks |
|---|---|---|
| Subtotal = sum of top-level sectors including Total Retail, excluding store types (local tax) | Found by the engine | None acknowledged. Notebook residual up to $2 |
| Total Retail = sum of store types (local tax) | `component_blocks` | None acknowledged |
| Total Philadelphia Sales Tax = Subtotal + Motor Vehicle Sales Tax | Not declared as such | Unverified. The notebook says the total includes Motor Vehicle |
| Same relations for each prior-year column (FY2017 on) | Engine runs every non-excluded column | None acknowledged |
| Percent of total = local tax / Total Philadelphia Sales Tax | Not declared | Unknown |
| Current minus prior = FY minus FY-1, each row | Not declared | Unknown |
| Growth rates from the four tax columns | Not declared | Unknown |
| Entity counts | Excluded from arithmetic (`collections-tax-details.yml:21-24`) | Not additive by design |
| FAMIS total against the City total | No relation. It is an accrual comparator | Not applicable |
| Cross-edition: FY17 prior columns against FY14 to FY16 reports, and so on | Not declared | Unknown |

Acknowledgments for sales tax: 0. Reviewed-cell records for either series: 0. No entry for these
families in `config/layouts/review-overrides.yml`, `config/resolved_assertions.yml` or
`config/document_metadata.yml`.

Rounding. Whole-dollar items sum to the subtotal within $2 in every year
(`notebooks/sales_tax_sector_trends.ipynb`, "Build one observation" cell and final cell). A check
needs a tolerance of about half a dollar per operand, or an exact acknowledgment per year.

## 6. Row labels and entities

Labels are stable within each series. BIRT has 35 entities and sales tax 31
(`config/entities.yml:3688-3884, 4229-4429`). All BIRT entities share `families:
[collections_birt_sector_*]`. All sales entities share `[collections_sales_tax_sector_*]`.

Label problems the registry handles:

- BIRT "Other Services" appears twice. One is the Professional Services child, the other is
  "Other Services **2", the standalone sector. Both normalize to "other services". They are
  separated by row kind (`config/entities.yml:4375-4382, 4413-4419`, `tests/test_entities.py:1860-1874`).
  The 2026.07.24.1 release still had two 2020 rows under one identity (BIRT notebook, "2020 shock" cell).
- BIRT parents print with ", subtotal" (`entities.yml:4248, 4287, 4337`).
- Footnote marks "**1" and "**2" are stripped by normalization (`entities.py:78-98`).
- Sales labels with letter-spacing gaps: "Car and truc k rental", "Services other than repai r
  services", "Total Philadelphia Sales T ax", "Total FY09 Sales T ax per FAMIS (Accrual Basis)",
  "Computer and s oftware stores, retail", "Liquor and beer s tores, retail", "Department s tores,
  retail" (`entities.yml:3727, 3743, 3861, 3872, 3783, 3808, 3821`).
- "Delivery / couriers" against "Delivery/couriers" (`entities.yml:3721`).
- The FAMIS row names its fiscal year, so it needs 16 aliases, FY06 to FY20, plus one spaced
  variant (`entities.yml:3867-3883`). An FY19 alias exists though no FY19 report does.

Confirmed defect. Three aliases at `config/entities.yml:3783, 3808, 3821` are YAML flow sequences
written without quotes. Each splits at the comma into two aliases, for example
`["Computer and s oftware stores", "retail"]`. Each therefore claims "retail". The Retail parent's
name "Retail" also normalizes to "retail". Four claimants means the resolver returns nothing
(`entities.py:947-1004`). The spaced full labels ("Computer and s oftware stores, retail") match
no alias at all. Whether those labels reach resolution today is not recorded.

Shared classification. None. BIRT, sales tax and wage tax by industry use three different
publisher taxonomies. They have separate entity ids and no crosswalk:

| Topic | Wage tax by industry | BIRT | Sales tax |
|---|---|---|---|
| Top level | 22 industries | 20 sectors | 15 sectors |
| Sub-levels | 30 under 6 parents | 14 under 3 parents | 12 under Retail |
| Example: finance | "Banking & Credit Unions", "Securities / Financial Investments" | "Banking and Related Activities", "Financial Investment Services" | none |
| Example: information | one industry, "Publishing, Broadcasting, and Other Information" | parent "Information" with 4 children | "Telecommunications" only |
| Example: sports | "Sport Teams" | "Sports" | none |
| Entity id prefix | `phl_wage_tax_industry_`, `phl_wage_tax_subindustry_` | `phl_birt_sector_`, `phl_birt_subsector_` | `phl_sales_tax_sector_`, `phl_sales_tax_subindustry_` |

Sources: `config/entities.yml:3360-3687` (wage tax, shared with residency), `4234-4429`,
`3692-3884`. No entry in `successions` touches these ids. The same word ("Construction",
"Hotels", "Retail Trade") is claimed in each family. Family scoping keeps them apart.

Same entity elsewhere. Only at the tax level: `phl_birt` and `phl_sales_tax` in monthly city
collections (`entities.yml:152-171`), and `phl_cash_birt`, `phl_cash_sales_tax` in QCMR cash
(`entities.yml:1792-1809`). None is linked to these totals. The bases differ: BIRT here is by tax
year and filing date, monthly BIRT is cash by fiscal year.

## 7. Values

- BIRT: net income, gross receipts and total in whole USD; accounts as a count
  (`config/semantics.yml:3852-3860`).
- Sales: local tax and current-minus-prior in whole USD; share and four growth columns in percent;
  entities as a count (`config/semantics.yml:3632-3649`). An unknown tag fails closed
  (`release-notes/data/2026.07.26.yml:48-58`).
- Sales Motor Vehicle Sales Tax entity count prints a dash next to a dollar amount (FY2015
  35,806,085; FY2016 38,127,602). The footnote cites state county remittances. The dash means no
  count, never zero (`docs/investigations/unverified-row-audit/CASES.md:17-18`,
  `source-observations.json:12-13`).
- Sales FY2017 on: dense percent and tax cells, and adjacent growth cells, fuse with no whitespace
  corridor. The engine splits them using the declared column count (`config/semantics.yml:3623-3625`,
  `tables/fused_columns.py:388-417`).
- Negative formats, blank cells and percent signs are not recorded for either series.
- BIRT time base is the calendar tax year ending 12/31. Sales is the fiscal year ending June 30.

## 8. Editions and revisions

BIRT. Every edition is kept. The rule for the canonical value is: for each tax year, the newest
edition by upload date whose coverage contains it (`birt_sector.py:116-140`). The same answer is
typed by hand into `canonical_value_years` per edition (`config/semantics.yml:3889-3931`). Rows of
other years are tagged `superseded`, not dropped (`normalization.py:711-722`). The two editions
with no canonical years must carry a written reason (`semantics.py:1127-1135`). The default view
holds only canonical rows. Four editions supply facts and two supply none
(`test_real_artifacts_optional.py:69-74`).

A revised edition with the same coverage on the listing wins by upload date
(`birt_sector.py:104-106`, `tests/test_birt_sector.py:57-79`). But ingest stores by coverage path
and skips any path that exists (`birt_sector.py:143-150`, `commands/collections.py:470-482`). So a
same-coverage revision is never fetched.

Sales tax. One attachment per year, no listed revisions. A listing that repeats a year fails
(`sales_tax_sector.py:73-76`). But the FY2017, FY2018 and FY2020 reports restate three prior years
each. FY2017 covers FY2014 to 2017, FY2018 covers FY2015 to 2018, FY2020 covers FY2017 to 2020. No
vintage policy is declared. The profiles default to `not_applicable` (`semantics.py:1040`), and the
dataset publishes every repeated observation (`test_real_artifacts_optional.py:115-118`). The
notebook's rule: each report's current-year column, plus FY2020's prior-year column for FY2019.
FY2020's restated 2017 to 2019 values include the two new categories, so they reflect a
reclassification and may not match the FY2017 and FY2018 reports.

## 9. Quirk ledger

| Id | What happens in the document | Old code (`path:line`) | Kind |
|---|---|---|---|
| BSALES-Q01 | BIRT editions are cumulative snapshots. They overlap and later ones revise earlier tax years | `birt_sector.py:3-10` | inherent |
| BSALES-Q02 | BIRT coverage is in the listing title. The filename may carry a later workbook date that must not widen it | `birt_sector.py:67-82`; `tests/test_birt_sector.py:82-93` | inherent |
| BSALES-Q03 | BIRT edition order is known only from the media URL upload stamp | `birt_sector.py:25, 55-64, 116-119` | inherent |
| BSALES-Q04 | A same-coverage BIRT revision is chosen on the listing but never downloaded, because the stored path is the coverage range | `birt_sector.py:104-106, 143-150`; `commands/collections.py:470-482` | artifact (path as identity) |
| BSALES-Q05 | Canonical edition per tax year is computed in code and typed again by hand in semantics, with no test tying them | `birt_sector.py:122-140`; `config/semantics.yml:3889-3931` | artifact (duplicated policy) |
| BSALES-Q06 | Editions with no canonical year need a written reason | `semantics.py:1127-1135`; `config/semantics.yml:3919-3922` | artifact |
| BSALES-Q07 | BIRT download is not checked against the PDF's printed years | `birt_sector.py:153-165` | artifact (gap) |
| BSALES-Q08 | Two oldest sales attachments hold one annual table per page | `sales_tax_sector.py:3-5` | inherent |
| BSALES-Q09 | Bundles are cut into one PDF per year with a sidecar naming the source page | `sales_tax_sector.py:114-135, 176-213` | artifact (one document per identity) |
| BSALES-Q10 | Sales listing year is a single year or a range with hyphen, en dash or em dash, in title or filename | `sales_tax_sector.py:25-27, 49-59` | inherent |
| BSALES-Q11 | Every sales page prints "Fiscal Year YYYY Collections". Its year must match the listing, once each | `sales_tax_sector.py:28-30, 108-111, 159-174` | inherent |
| BSALES-Q12 | A listing repeating a sales year fails. Whether the City ever reposts a sales report is unknown | `sales_tax_sector.py:73-76` | unsure: a revised posting on the live page would settle it |
| BSALES-Q13 | No FY2019 sales report. FY2019 comes from FY2020's prior-year column | `README.md:26`; `test_real_artifacts_optional.py:105-112` | inherent |
| BSALES-Q14 | BIRT document year is the coverage end, so the catalog shows "FY2017-2023" for tax years 2004 to 2023 | `documents.py:148-152`; `docs/site/data/index.md:43, 325` | artifact |
| BSALES-Q15 | Sales splitting needs PyMuPDF (AGPL) | `sales_tax_sector.py:127, 145-152` | artifact |
| BSALES-Q16 | BIRT title reads BPT on older pages, BIRT on newer | `config/page_types.yml:948`; `tests/test_page_types.py:656-672` | inherent |
| BSALES-Q17 | BIRT years come from "Period: 12/31/YYYY" twice per page, the first sometimes "(Preliminary)" | `config/page_types.yml:951`; `normalization.py:698-710` | inherent |
| BSALES-Q18 | 2018-2022 edition repeats "Tax Year 2022" and one filing date in the right caption | `config/page_types.yml:937-941`; `tests/test_page_types.py:627-654` | inherent |
| BSALES-Q19 | BIRT pages are partitioned by tax year so the stitcher does not join six years into one table | `config/page_types.yml:953-955`; `page_table_scoping.py:642-652` | artifact (cross-page stitcher) |
| BSALES-Q20 | Marker pattern filled with codes that cannot match | `config/page_types.yml:890, 944` | artifact |
| BSALES-Q21 | BIRT untitled pages are evidence only. Whether such pages exist is not recorded | `config/page_types.yml:949` | unsure: page list of one edition |
| BSALES-Q22 | Sales title ends "Collections" or "Collections Report" | `config/page_types.yml:894`; `tests/test_sales_tax_sector.py:108-111` | inherent |
| BSALES-Q23 | BIRT grid: 8 columns, two halves, each half a different tax year | `config/semantics.yml:3862-3888` | inherent |
| BSALES-Q24 | All 8 BIRT columns carry role `year_actual` against the coverage-end year, then the year is overwritten from context | `config/semantics.yml:3862-3870`; `normalization.py:698-710` | artifact |
| BSALES-Q25 | BIRT sub-sectors become components only through an indentation trial, backstopped by a registry relabel | `collections-tax-details.yml:292-297`; `tables/reconciliation_trials.py:840-1018`; `resolution.py:887-920` | artifact (inferred row roles) |
| BSALES-Q26 | BIRT prints "Other Services" as a Professional Services child and "Other Services **2" as a sector | `config/entities.yml:4375-4419`; `tests/test_entities.py:1860-1874` | inherent |
| BSALES-Q27 | BIRT labels carry ", subtotal" and footnote marks "**1", "**2" | `config/entities.yml:4248, 4287, 4337, 4417`; `entities.py:78-98` | inherent |
| BSALES-Q28 | Total Retail prints above its store types; block ends at "Car and truck rental" before FY2020 | `collections-tax-details.yml:4-12` | inherent |
| BSALES-Q29 | FY2020 moves the rental rows above Retail; block ends at "Unclassified" | `collections-tax-details.yml:5-11` | inherent |
| BSALES-Q30 | FY2020 adds Delivery/couriers and Online retailers and restates 2017 to 2019 with them | `test_real_artifacts_optional.py:109-112` | inherent |
| BSALES-Q31 | "Total FYyy Sales Tax per FAMIS" is a comparator line, not a total; label carries the year and "**2" | `collections-tax-details.yml:13-16`; `config/entities.yml:3863-3884`; `tests/test_entities.py:1462-1467` | inherent |
| BSALES-Q32 | "FAMIS amount as a percent of total" is a memo and is not published | `collections-tax-details.yml:17-20`; `tests/test_memo_export_contract.py:98-112` | inherent |
| BSALES-Q33 | Sales entity counts are not additive; one account can be in several sectors | `collections-tax-details.yml:21-24` | inherent |
| BSALES-Q34 | Sales totals sit in a ruled box below footnotes in some legacy tables | `collections-tax-details.yml:25`; `tables/region_detection.py:331-345` | inherent (box); the rejoin flag is artifact |
| BSALES-Q35 | Sales has a 3-column era and an 11-column era, chosen by a list of document ids | `config/semantics.yml:3626-3711` | inherent (eras); id list is artifact |
| BSALES-Q36 | FY2017 on, percent and tax cells fuse without whitespace | `config/semantics.yml:3623-3625`; `tables/fused_columns.py:388-417` | inherent |
| BSALES-Q37 | No header text is verified for either series; verify templates are blank or absent | `config/semantics.yml:3683-3692, 3709-3711, 3849-3931` | artifact (regions start at data rows) |
| BSALES-Q38 | Motor Vehicle Sales Tax count prints a dash; it means no count | `docs/investigations/unverified-row-audit/CASES.md:17-18` | inherent |
| BSALES-Q39 | Percent of total uses Total Philadelphia Sales Tax, which includes Motor Vehicle, so sector shares sum below 100 | sales notebook, "composition" cell | inherent |
| BSALES-Q40 | Sector sum and Subtotal differ by up to $2 from whole-dollar rounding | sales notebook, final cell | inherent |
| BSALES-Q41 | BIRT 2004-2017 page 1: 2017 account counts sum to 34,487; Total prints 32,956 | `collections-tax-details.yml:224-257` | inherent |
| BSALES-Q42 | BIRT 2018-2023 page 3: 2018 combined Total prints 468,801,829 against 468,794,493 | `collections-tax-details.yml:258-291`; `tests/test_collections_source_acknowledgments.py:172-176` | inherent |
| BSALES-Q43 | First match wins, so each BIRT acknowledgment profile repeats `export_component_rows` | `config/layouts.yml:1-3`; `collections-tax-details.yml:224-297`; `tests/test_layout_composition.py:257-259` | artifact |
| BSALES-Q44 | Acknowledgments pin evidence and check fingerprints and row indices | `collections-tax-details.yml:246-257, 280-291` | artifact |
| BSALES-Q45 | Three sales aliases split at a comma and each claims "retail" | `config/entities.yml:3783, 3808, 3821`; `entities.py:947-1004` | artifact (unquoted YAML flow list); defect |
| BSALES-Q46 | Sales labels have letter-spacing gaps ("truc k", "repai r", "T ax", "s oftware", "s tores") | `config/entities.yml:3727, 3743, 3783, 3808, 3821, 3861, 3872` | inherent |
| BSALES-Q47 | "Delivery / couriers" and "Delivery/couriers" | `config/entities.yml:3717-3722` | inherent |
| BSALES-Q48 | BIRT, sales and wage tax use three unrelated taxonomies; same words in each | `config/entities.yml:3360-3687, 3688-3884, 4229-4429` | inherent |
| BSALES-Q49 | Resolution fingerprint omits entity dimension; an industry to sub_industry edit leaves stale BIRT artifacts current | `docs/code-review-fix-workorders-2026-08-01.md:56-63` | artifact |
| BSALES-Q50 | Sales FY2017, FY2018, FY2020 restate prior years, but no vintage policy is declared | `semantics.py:1040`; `config/semantics.yml:3626-3711` | unsure: compare FY2017's FY2016 column with the FY2016 report |
| BSALES-Q51 | FY2020 sales had no export or resolved parquet on 2026-09-11 | `docs/philly-source-monitoring-audit-2026-09-11.md:39` | unsure: a pipeline run |
| BSALES-Q52 | FAMIS alias exists for FY19, a year with no report | `config/entities.yml:3882` | unsure: FY2020 page text |
| BSALES-Q53 | BIRT filing-through dates and "(Preliminary)" are captured as context and never used | `config/page_types.yml:950-952`; no reader in `packages/` | artifact (gap) |
| BSALES-Q54 | Editions with an odd number of tax years cannot be one pair per page | `config/semantics.yml:3890-3922` | unsure: page list of 2008-2018 and 2018-2022 |
| BSALES-Q55 | BIRT notebook text places the account mismatch in 2018-2023, contradicting the record | `notebooks/birt_sector_trends.ipynb` | artifact (stale doc) |

## 10. Old code that serves this family

| Job | File | Lines | Keep as code | Keep as knowledge |
|---|---|---|---|---|
| Acquisition | `birt_sector.py` | 165 | Listing parse, coverage, upload date, newest-per-year (22-140) | Snapshot semantics |
| Acquisition | `sales_tax_sector.py` | 214 | Listing parse and page-year check (23-85, 108-111, 159-174) | Bundles; drop the page split |
| Acquisition | `phila_media.py` | 932 (shared) | `media_pdf_links`, media URL regex (39-42) | |
| Acquisition | `publisher_http.py` | 288 (shared) | `fetch_bytes` | |
| Acquisition | `commands/collections.py` | 438-544 | None | `--latest-only` and `--list` behavior |
| Page typing | `config/page_types.yml` | 885-895, 937-955 | Two title regexes, Period regex | Defective caption |
| Layout | `config/layouts/collections-tax-details.yml` | 1-25, 224-297 | None | Retail block, FAMIS, count column, two acknowledgments |
| Semantics | `config/semantics.yml` | 3621-3711, 3845-3931 | None | Column lists by era, units, canonical years |
| Entities | `config/entities.yml` | 3688-3884, 4229-4429 | Entity lists (fix three aliases) | Other Services scoping |
| Engine | `normalization.py:698-722`, `resolution.py:887-920`, `tables/fused_columns.py`, `tables/region_detection.py:331-414` | shared | None | Year from context; fused cells; total box |
| Tests | `tests/test_birt_sector.py` (232), `tests/test_sales_tax_sector.py` (157) | 389 | Listing and vintage fixtures | |
| Tests | `test_page_types.py:627-672`, `test_entities.py:1449-1476, 1838-1882`, `test_semantics.py:259-283, 371-389`, `test_collections_source_acknowledgments.py:172-176, 270-275`, `test_memo_export_contract.py:98-112` | shared | Page and label fixtures as parser tests | |
| Tests | `packages/gov-budget-data/tests/test_real_artifacts_optional.py:63-118` | 56 | Panel shape assertions (35 by 20; 31 entities) | |
| Notebooks | `notebooks/birt_sector_trends.ipynb`, `sales_tax_sector_trends.ipynb` | | None | Rollup checks, FY2019 rule |

## 11. The least a parser needs

Inputs: the listing HTML, each archived PDF by SHA-256 with its listing title and media URL, and
the page words with coordinates.

BIRT steps:

1. From the listing, read coverage (title years, else filename) and the upload date from the URL.
2. For each page whose title matches the BIRT or BPT form, read the Period line. Fail when it is
   absent or unparseable. Never read years from the Tax Year caption.
3. Check that the page years fall inside the listed coverage. Report pages outside it.
4. Read rows from the first sector to "Total". Expect 35 rows. Map 8 value columns by position.
5. Assign each row a fixed role from a declared row list: total, sector, subtotal parent, or child
   with its parent. Use the label and position, not indentation. Disambiguate the two "Other
   Services" rows by position.
6. Emit one typed row per sector, tax year, measure and edition, with the edition's upload date
   and the page's filing-through date.

BIRT checks to declare, per page and half:

- Total equals the sum of the 20 top-level rows, for all four measures.
- Each parent equals the sum of its children.
- Total equals Net Income plus Gross Receipts, for every row.
- Carry the two acknowledgments.

BIRT canonical rule: for each tax year, the newest edition by upload date that prints it. Compute
it once, as data, not in two places.

Sales steps:

1. From the listing, read one year or a range per attachment. Fail on a repeated year.
2. For each page, read "Fiscal Year YYYY Collections( Report)?". Map page to year. Fail if it
   disagrees with the listing. Keep the page number; do not cut the PDF.
3. Read rows from the first sector through the FAMIS rows, including a drawn total box.
4. Choose the era by counting value columns (3 or 11) and confirm it against the year. Map columns
   by position. Split fused cells only to reach the declared count.
5. Assign row roles from a declared list: sector, Retail parent, store type, Subtotal, Motor
   Vehicle, City total, FAMIS comparator, FAMIS percent memo.
6. Treat a dash in the count column as missing.

Sales checks to declare, per tax column:

- Subtotal equals the sum of the top-level sectors.
- Total Retail equals the sum of its store types.
- City total equals Subtotal plus Motor Vehicle.
- Current minus prior equals the difference of the two tax columns.

Use a rounding tolerance of half a dollar per operand. Do not check the count column.

Sales canonical rule: the current-year column of each annual report, plus FY2020's prior-year
column for FY2019. Keep the other comparison columns as revisions.

Era parameters: BIRT title (BPT or BIRT), row count (fixed). Sales column count (3 or 11), Retail
block end ("Car and truck rental" or "Unclassified"), presence of the two FY2020 categories.

## 12. Unknowns

- Page count of each BIRT edition, and how editions with an odd number of years are paged.
- Whether a BIRT "subtotal" row sits above or below its children, and how far children indent.
- Which BIRT pages carry the BPT title.
- Whether BIRT parent subtotals and the horizontal Net Income plus Gross Receipts identity hold
  everywhere except the one 2018 cell.
- Whether the 2009-2019 edition's 2017 account counts reconcile.
- Which sales rows sit in the drawn total box, and the print order of sales rows.
- Whether Total Philadelphia Sales Tax always equals Subtotal plus Motor Vehicle.
- Whether FY2017, FY2018 and FY2020 prior-year columns match the earlier annual reports.
- Whether the spaced store-type labels still reach resolution, and so whether the alias defect
  drops values today.
- Which sales years print "Collections Report".
- The exact bundle ranges of the two oldest sales attachments.
- Negative values, blanks and percent formatting in either series.
- Whether any BIRT or sales PDF is a scan.
