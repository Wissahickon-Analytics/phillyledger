# QCASH: QCMR cash statements (dataset `qcmr_cash`)

Paths are shortened by dropping `packages/gov-budget-etl/src/gov_budget_etl/`. Config paths are
relative to the repo root. Every citation was opened at commit 49b59ea. Nothing here was checked
against a PDF; the checkout has none.

## 1. Documents

The cash statement is a two-page section inside the Quarterly City Managers Report (QCMR). The
City publishes one large QCMR PDF per quarter. The old repo cuts the cash pages out into
`data/phila/qcmr/cash/FY##_Q#.pdf` and treats that cut file as the document (`qcmr.py:1-12`,
`config/document_roots.yml:3-5`).

| Fact | Value | Evidence |
|---|---|---|
| Publisher listing | phila.gov document-finder feed, post 151831, category "Quarterly City Managers Report" | `qcmr.py:48-53`, `phila_source_sync.py:23` |
| Listing noise | Same category lists dated one-page infographics; skipped by title | `qcmr.py:382-385` |
| Revisions | The City appends revised attachments after the original; last listing per quarter wins | `qcmr.py:393-395` |
| Host aliasing | `admin.phila.gov` and `www.phila.gov` URLs are one asset | `phila_source_sync.py:26-30` |
| Cadence | Quarterly, fiscal year July to June; Sep 30 is Q1, Dec 31 Q2, Mar 31 Q3, Jun 30 Q4 | `qcmr.py:38-46` |
| Coverage | FY2007 to FY2026, 79 documents, 47,667 published rows | `docs/site/data/index.md:419-422` |
| Earliest named edition | `qcmr_cash_fy07_q3` | `config/layouts/qcmr-cash.yml:90` |
| Automatic acquisition | FY2022 onward only; older cut files were made by hand | `phila_source_sync.py:176-179`, `config/source_sync.yml:3-5` |
| Provenance gap | Historical cut files have no sidecar, so no source URL or retrieval time | `release-notes/data/2026.07.31.yml` known issues |
| Missing then restored | FY2025 Q3 was absent and was restored from the official PDF | `release-notes/data/2026.07.31.yml:13-29` |
| Pages | Two pages per edition: page 1 General Fund cash flow, page 2 all-funds balances | `config/layouts/qcmr-cash.yml:706-712`, `tests/test_qcmr.py:85-86` |
| Location in the full report | Printed page 45 in FY12 Q4 | `docs/investigations/release-readiness-policy/protocol.md:23` |

Scan or text layer is not recorded in config. The per-edition word source was chosen at run time
by a score and stored in `artifacts/validation/authoritative_artifacts.json`, which is not in git.
The reviewed records name the parser they were bound to, which gives a partial picture.

| Edition | Word source named in a record | Reading |
|---|---|---|
| FY07 Q3 | `textract_geometric` (`qcmr-cash.yml:91`) | scan |
| FY07 Q4 | `textract` primary, native words as evidence (`qcmr-cash.yml:73-75`) | has a native word layer with correct digits; see QCASH-Q22 |
| FY08 Q1, Q2, Q3 | `textract_geometric` (`qcmr-cash.yml:390, 419, 567`) | scan |
| FY08 Q4, FY10 Q1 | `geometric` (`qcmr-cash.yml:596, 624`) | text layer |
| FY09 Q2 | `textract` (`docs/investigations/unverified-row-audit/CASES.md:30`) | scan |
| FY12 Q4 | `textract_geometric` (`docs/investigations/release-readiness-policy/trace_cases.py:23`) | unknown |
| FY18 Q2, FY19 Q1, FY25 Q3 | `geometric` (`qcmr-cash.yml:642, 660, 678`) | text layer |
| FY25 Q2 | `textract` (`qcmr-cash.yml:492`) | unknown; a modern edition read by OCR |

## 2. Tables

Page 1 holds two independent grids stacked on one page, followed by the monthly cash lifecycle
rows. Page 2 holds a fund balance grid. All amounts are "Amounts in Millions" with one decimal
(`config/semantics.yml:1777-1783`, `config/layouts/qcmr-cash.yml:50-58`).

**Revenue grid (page 1, top).** A row is one revenue line for the fiscal year. Columns are twelve
fiscal months July to June, then Total, then era-specific endpoint columns (section 3). Rows in
the modern form: Real Estate Tax; Total Wage, Earnings, Net Profits (with two memo rows, gross
City plus PICA and Tax to PICA); Realty Transfer Tax; Sales Tax; Business Income and Receipts
Tax; Beverage Tax; Other Taxes; Locally Generated Non-Tax; Total Other Governments, Excluding
PICA Tax; Total PICA Other Governments; Interfund Transfers; Total Current Revenue. Below the
total: Collection of prior year(s) revenue, Other fund balance adjustments, and in early forms
Non-revenue receipts and Non-budget Items; then TOTAL CASH RECEIPTS (`config/entities.yml:1753-1980`).

**Expense grid (page 1, below).** Columns are twelve months, Total, Vouchers Payable,
Encumbrances, and an estimate column (legacy adds Mergers). Rows: Payroll, Employee Benefits,
Pension, Purchase of Services, Materials and Equipment, Contributions and Indemnities, Debt
Service Short Term, Debt Service Long Term, Interfund Charges, Advances and Miscellaneous
Payments, then Current Year Appropriation (an unlabeled subtotal), Prior Year Encumbrances,
Prior Year Vouchers Payable, TOTAL DISBURSEMENTS (`config/semantics.yml:1904-1906`).

**Lifecycle rows (page 1, bottom).** Excess (Deficit) of Receipts over Disbursements, Opening
Balance, TRANS or TRAN, CLOSING BALANCE. Twelve months plus a thirteenth column. On flow rows
the thirteenth column is an annual sum. On Opening Balance it is the fiscal-year start balance;
on CLOSING BALANCE it is the fiscal-year end balance (`config/semantics.yml:1522-1617`).

**Fund balance grid (page 2).** Twelve month columns, no total. Rows: General, Grants Revenue,
Community Development, Vehicle Rental Tax, Hospital Assessment Fund, Housing Trust Fund,
Transportation Fund, Budget Stabilization Fund, Other Funds, TOTAL OPERATING FUNDS, Capital
Improvement, Industrial and Commercial Development, TOTAL CAPITAL FUNDS, TOTAL FUND EQUITY
(`config/semantics.yml:1492-1494`). Several funds start mid-series (`release-notes/data/2026.07.31.yml:34-40`).

Hierarchy is shallow: line items, a few memo breakdown rows, one subtotal per grid, one total
per grid. Nothing spans pages except that page 2 follows page 1. Typical size: the FY18 Q2
extracted page 1 table reaches CLOSING BALANCE at row 41 (`qcmr-cash.yml:644`). The legacy FY07
Q3 revenue grid ends at TOTAL CASH RECEIPTS on row 22 (`qcmr-cash.yml:295-297`).

## 3. Format eras

There are three column eras for the revenue grid and two for the expense grid. The boundaries
come from semantics profile globs; no test pins the exact boundary editions.

| Era | Editions (by glob) | Revenue columns after 12 months | Expense columns after 12 months | Evidence |
|---|---|---|---|---|
| Legacy | FY07 to FY10 | Total, Accrued, Under (Over) Revenues, Budget Revenues (16) | Total, Vouchers Payable, Encumbrances, Mergers, Budget Obligations (17) | `config/semantics.yml:1351-1487` |
| Middle | FY11 to FY16 | Total, Accrued, Estimated Revenues (15) | Total, Vouchers Payable, Encumbrances, Estimated Obligations (16) | `config/semantics.yml:1822-1977` |
| Modern | FY17 to FY26 | Total, Accrued, Not Accrued, Estimated Revenues (16) | same as middle (16) | `config/semantics.yml:2031-2196` |

Other changes that are not column changes:

| Change | When | Evidence |
|---|---|---|
| PDF exposes one narrow ruled fragment per grid to a table finder | FY14 onward | `qcmr-cash.yml:4-8` |
| Modern four-section report layout that the splitter understands | FY2022 onward | `qcmr.py:79-86`, `phila_source_sync.py:178-179` |
| Broken font map: EXPENSES prints as `E(cid:121)PENSES` | FY23 Q1, Q2 | `qcmr-cash.yml:15-17` |
| Page 2 caption: "CASHFLOW PROJECTIONS Consolidated", then "CONSOLIDATED", then "CASH . ALL FUNDS" | legacy, middle, modern | `config/semantics.yml:1692, 1978, 2197` |
| Label renames: Property Taxes to Real Estate Tax; Business Privilege Tax to BIRT; "Collection of 6-30-06/Govt." (year changes each edition) to "Collection of prior year(s) revenue"; Other Governments with CY/PY and PICA Debt Service/City Account to "Total Other Governments, Excluding PICA Tax" and "Total PICA Other Governments"; Advances wording changes four times; TRANS to TRAN | years not pinned | `config/entities.yml:1753-2148` |
| Gross and net wage rows: "City, PICA Wage, E, NP" and "Tax to PICA" beside a net row without "Total" | already in FY10 Q3 | `qcmr-cash.yml:1030-1039` |
| Actual months beyond the quarter cutoff | FY08 Q4, FY09 Q1, Q3, Q4, FY10 Q1, Q2, Q3 | `config/semantics.yml:1742-1776` |

The cut at FY10/FY11 and FY16/FY17 is a glob. A parser should select the era from the printed
header tokens ("Under", "Mergers", "Not Accrued"), as the old code already does
(`config/semantics.yml:1399-1487, 2079-2118`), and treat the year range as a cross-check.

## 4. Finding the table

**Pages today.** For FY2022 onward, `split_report` reads the first two non-empty lines of each
page, collapses non-breaking spaces, and keeps pages whose header contains "CASH FLOW
PROJECTIONS" (`qcmr.py:172-180, 72-76`). It keeps the longest contiguous run, which discards a
contents-page mention (`qcmr.py:183-219`). The two pages are "GENERAL FUND" and "CONSOLIDATED
CASH" (`tests/test_qcmr.py:85-86`). The period comes from "PERIOD ENDING" text and must match the
listing (`qcmr.py:152-163`, `phila_source_sync.py:55-56`). Older editions were cut by hand.

**Region today.** The geometric parser tries three paths in order (`parsers/geometric_backend.py:838-1016`):

1. Vertically disjoint structured table priors from pdfplumber, unless they omit a numeric row
   below the first caption (`geometric_backend.py:202-226, 845-889`).
2. Caption anchors: `^REVENUES$` and `^E(?:X|\(cid:\d+\)|\s)*PENSES (?:AND|ANO) OBLIGATIONS$`,
   both required in order or the path is skipped (`geometric_backend.py:177-199, 891-965`). Each
   section infers its own columns, and the densest numeric row can add boundaries the
   whitespace rule missed (`geometric_backend.py:229-257, 937-944`).
3. Disjoint structured spans with local column inference (`geometric_backend.py:967-1016`).

After parsing, stitching joins page 2 onto the page 1 expense grid because they are on
consecutive pages and their columns line up (`tables/stitching.py:1084-1115`). The FY07 Q3 page 2
check therefore runs on table 2, row 35, under a hypothesis called `items_since_physical_page_break`
(`qcmr-cash.yml:713-717`). In FY18 Q2, FY19 Q1 and FY25 Q3 the reviewed lifecycle sits in table
1, so revenue and expense came out as one extracted table there (`qcmr-cash.yml:641-690`).
Normalization then re-splits by section text (`normalization.py:546-636`).

**Simplest reliable rule.** Pages: in the whole QCMR PDF, the pages whose top two lines contain
"CASH FLOW PROJECTIONS", longest contiguous run, expect exactly two. Page 1 regions: cut at the
two printed captions (REVENUES, EXPENSES AND OBLIGATIONS, with the cid and ANO variants), fail if
either is missing. The lifecycle rows sit at the bottom of the expense region. Page 2 is its own
table. Never join page 2 to page 1. No table-finder priors are needed.

## 5. Arithmetic that holds

All checks run on one-decimal millions. Each printed number is modelled as independently rounded
to nearest 0.1, with a strict bound of 0.05 times (operands plus one). For a twelve-month sum this
is 0.65, so a residual of 0.6 passes (`tables/checks.py:84-92`, `qcmr-cash.yml:50-58`).

| Relation | Declared today | Source breaks it |
|---|---|---|
| Row: Total = sum of 12 months (revenue, expense and flow rows) | 3 reviewed records, rest inferred (`qcmr-cash.yml:388-475`) | FY07 Q4 wage tax: months sum 1,165.9, Total prints 1,185.9 (`release-notes/data/2026.07.31.yml` known issues) |
| Row, legacy: Budget Revenues = Total + Accrued + Under (Over) | FY07 Q4 (`qcmr-cash.yml:476-490`) | none recorded |
| Row, middle: Estimated Revenues = Total + Accrued | inferred | FY12 Q4 endpoints imply 30.6 accrued (`qcmr-cash.yml:727-731`) |
| Row, modern: Estimated Revenues = Total + Accrued + Not Accrued | FY25 Q2 (`qcmr-cash.yml:491-506`) | FY15 Q1 and FY18 Q3 show the error in both directions (`qcmr-cash.yml:761-767, 999-1001`) |
| Row, expense: estimate = Total + Vouchers Payable + Encumbrances (+ Mergers) | not declared | unknown |
| Column: Total Current Revenue = sum of revenue line items, memo rows excluded | inferred | 10 editions (table below) |
| Column: Other Governments = CY + PY; Other Governments-PICA = PICA Debt Service + PICA City Account | `qcmr-cash.yml:65-71` | none recorded |
| Column: Current Year Appropriation = expense line items | via `promote_subtotals` (`qcmr-cash.yml:63-64`) | none recorded; FY07 Q3 November sums 235.4 (`CASES.md:29`) |
| Column: TOTAL CASH RECEIPTS and TOTAL DISBURSEMENTS from their parts | inferred, composition not declared | unknown |
| Column: CLOSING = Opening + Excess + TRANS, TRANS only where printed; blank TRANS is not zero | 12 records over 8 editions (`qcmr-cash.yml:507-694`) | none recorded |
| Column: page 2 TOTAL OPERATING FUNDS, TOTAL CAPITAL FUNDS, TOTAL FUND EQUITY | inferred | FY07 Q3 April: leaves 760.6, prints 782.6 (`qcmr-cash.yml:695-721`) |
| Chain: Opening(month m+1) = Closing(month m); FY start = July Opening; FY end = June Closing | not declared | unknown |
| Cross-edition: June Closing of Q4 = July Opening of next FY Q1; actual months agree across editions of one FY | not declared | unknown; revisions are expected |
| Cross-table: page 1 CLOSING BALANCE vs page 2 General | not declared | unknown |

Acknowledged source errors in Total Current Revenue and page 2 (11 records):

| Edition | Column | Printed vs contributors | Line |
|---|---|---|---|
| FY07 Q3 p2 | April TOTAL OPERATING FUNDS | 782.6 vs 760.6 | `qcmr-cash.yml:696` |
| FY07 Q4 | January, June, annual | -20.0, -0.9, -20.0 | `qcmr-cash.yml:888` |
| FY12 Q4 | Accrued | 55.4 vs 30.5 | `qcmr-cash.yml:722` |
| FY15 Q1 | Accrued and estimate | 73.5 vs 83.2; residuals -9.7 and 10.3 | `qcmr-cash.yml:756` |
| FY15 Q2 | Accrued | 73.5 vs 83.2 | `qcmr-cash.yml:790` |
| FY15 Q3 | Accrued | 71.2 vs 90.3 | `qcmr-cash.yml:823` |
| FY16 Q2 | Accrued | 49.8 vs 64.0 | `qcmr-cash.yml:921` |
| FY16 Q3 | Accrued | 49.1 vs 8.7 | `qcmr-cash.yml:858` |
| FY16 Q4 | Accrued | 53.2 vs 7.8 | `qcmr-cash.yml:945` |
| FY18 Q2 | Not Accrued | omits displayed (20.3) BIRT | `qcmr-cash.yml:971` |
| FY18 Q3 | Not Accrued | 32.9 vs 4.0 | `qcmr-cash.yml:995` |

Discrepancies deliberately left open, not acknowledged: FY08 Q1 July and June Total Current
Revenue (`qcmr-cash.yml:416-417`); FY08 Q2 May (`:446-447`); FY16 Q4 a 0.1 estimate difference
(`:951-952`); FY19 Q1 a 0.1 revenue endpoint (`:675-676`); FY25 Q3 a nonnumeric revenue mark
(`:693-694`).

All review records for the family live inline in `config/layouts/qcmr-cash.yml`:

| Kind | Count | Editions |
|---|---|---|
| Source arithmetic acknowledgments (`acknowledge_totals`) | 11 | listed above |
| Reviewed word-source preference (`reviewed_value_sources`) | 1 record, 3 cells | FY07 Q4 |
| Reviewed fixed-decimal cells | 34 | FY07 Q3 (25 revenue, 8 expense), FY08 Q1 (1) |
| Reviewed column identities (`reviewed_column_sums`) | 5 | FY07 Q3, FY07 Q4, FY08 Q1, FY08 Q2, FY25 Q2 |
| Reviewed row identities (`reviewed_row_sums`) | 12 | FY07 Q3, FY08 Q1, Q3, Q4 (2 each); FY10 Q1, FY18 Q2, FY19 Q1, FY25 Q3 |
| Edition date override | 1 | FY14 Q2 (`report_editions.json:5-11`) |
| Edition-scoped OCR aliases | 8 | FY07 Q4 (`config/entities.yml:4507-4558`) |

## 6. Row labels and entities

The registry has 55 cash entities, all scoped to `qcmr_cash_*` only, with 119 alias lines
(`config/entities.yml:1753-2264`). Labels are stable in meaning but not in spelling. Variation
comes from three sources:

- Publisher renames: Property Taxes to Real Estate Tax; Business Privilege Tax to Business Income
  and Receipts Tax; dated "Collection of 6-30-06/Govt." to "Collection of prior year(s) revenue";
  "Advances, Subsidies", "Advances & Miscellaneous Payments", "Advances & Misc. Pmts. / Labor
  Obligations", "Other Adj. Provision for Labor Obligations"; "Prior Yr. Expenditures against
  Encumbrances" to "Prior Year Encumbrances"; TRANS to TRAN.
- OCR damage: "Really Transfer Tax", "Business Prlvllege Tax", "Lacaly Generated Nan-tax",
  "Other Govemmants-PICA", "Hospltal", "Capltal", "Contributions, lndemn~ies", "Current Year
  Aoorooriation", "TOTAL OPERATING FUND~", and FY12 Q3 "Burchase of Services"
  (`config/entities.yml:1789-2237, 4686-4695`).
- Welded or wrapped labels: "Excess (Def) of Receipts over Disbursements" wraps onto two lines,
  so "over Disbursements" or "Disbursements" alone must resolve; welded forms such as "TOTAL
  CASH RECEIPTS Other fund balance adjustments" and "Pension Employee of" are parser artifacts
  (`config/entities.yml:1937, 1978, 2005, 2118-2121`).

Parent links exist only for the memo breakdowns: CY and PY under Other Governments, Debt Service
and City Account under PICA, Tax to PICA under the gross wage row (`config/entities.yml:1859-1903`).
"Purchase of Services" and "Payments to Other Funds" are declared as section qualifiers
(`config/entities.yml:4684-4703`).

The same taxes appear in monthly City collections under different entity ids
(`phl_real_estate_tax`, `phl_birt` at `config/entities.yml:127-172`). No succession or link joins
them to the `phl_cash_*` entities. Cash receipts and collections are different bases, so a link
would need a declared relation, not an alias.

## 7. Values

- Unit "Amounts in Millions", one printed decimal, published as USD with multiplier 1,000,000
  (`config/semantics.yml:1777-1795`, `config/release_contracts.yml:33-53`). The contract sets
  `source_decimal_scale: 4` although the page prints one decimal; the reason is not written down.
- Negatives print in parentheses, for example "(20.3)" and "(150)" read as (15.0)
  (`qcmr-cash.yml:130, 975`). Minus signs also occur, for example the page 2 Other Funds leaf
  "-11.0" (`qcmr-cash.yml:700-704`).
- Explicit zeros "0.0" are printed, for example TRANS in FY19 Q1 and FY25 Q3
  (`qcmr-cash.yml:674-675, 692-693`). A blank TRANS cell means no transfer was printed and is not
  a zero for checks (`qcmr-cash.yml:522-525`).
- Dashes and nonnumeric marks stay as source text and are not zero
  (`release-notes/data/2026.08.02.yml:15-20`). FY25 Q3 has a nonnumeric mark in the revenue grid.
- A whole physical column can be printed but empty, as in FY26 Q1 (`tests/test_qcmr_semantics.py:430-476`).
- Sparse rows (for example the wage row with blank Accrued and Not Accrued) defeated the old
  right-to-left role assignment and put the annual value in June in 19 editions
  (`release-notes/data/2026.07.29.yml:13-41`).
- OCR defeated amount parsing in early scans: dropped or substituted decimal points ("2918" for
  291.8, "266 1", "(29 1)", "67: 3", "69,2") and decayed digits such as "1o4.o"
  (`qcmr-cash.yml:89-387`, `normalization.py:561-568`).
- The page title uses non-breaking spaces (`qcmr.py:175-177`).

## 8. Editions and revisions

Each quarterly edition reprints all twelve months of the fiscal year. Months through the quarter
cutoff are actual and later months are projected. Default cutoffs: Q1 projects October to June,
Q2 January to June, Q3 April to June, Q4 none (`config/semantics.yml:1720-1741`). The old code
assigns actual or projected from these tags, not from anything printed
(`normalization.py:637-646`).

Seven legacy editions report one more actual month than the default, and FY08 Q4 still projects
June (`config/semantics.yml:1742-1776`). The same July value therefore appears in up to four
editions, and they are snapshots, not additive (`docs/site/guides/series.md:35-45`). The old
repo keeps every edition and lets the reader choose; there is no "latest actual wins" rule
(`docs/site/guides/series.md:269-273`).

`qcmr_cash_fy14_q2` is filed as Q2 but prints "Projection as of March 31, 2014" and carries the
Q3 cutoff (`packages/gov-budget-data/src/gov_budget_data/data/report_editions.json:5-11`). The
release keeps `report_period=Q2` and sets the as-of date to 2014-03-31. Whether it is byte-equal
to the FY14 Q3 cut file cannot be checked here. In effect FY14 has two Q3 snapshots and no Q2.
There is no printed-period quarantine for QCMR; that gate exists only for monthly collections
(`revenue_collections.py:85, 680`).

## 9. Quirk ledger

| Id | What happens in the document | Old handling | Kind |
|---|---|---|---|
| QCASH-Q01 | Cash pages are found by "CASH FLOW PROJECTIONS" in the top two lines; title uses non-breaking spaces | `qcmr.py:72-86, 172-180` | inherent |
| QCASH-Q02 | Contents page repeats the title; true run is the longest contiguous one | `qcmr.py:183-219` | inherent |
| QCASH-Q03 | Infographics share the listing category; revised attachments are appended later | `qcmr.py:382-395` | inherent |
| QCASH-Q04 | Same asset served from admin and www hosts | `phila_source_sync.py:26-30` | inherent |
| QCASH-Q05 | Period is printed as "PERIOD ENDING"; listing date must agree | `qcmr.py:152-163`, `phila_source_sync.py:55-56` | inherent |
| QCASH-Q06 | Only FY2022 onward can be split automatically; older cash files were cut by hand with no URL | `phila_source_sync.py:176-179`, `config/source_sync.yml:3-5` | artifact (cut PDFs and a splitter written for the modern layout). Whether older full reports carry the same header is unsure; settle by running the page rule over archived full reports |
| QCASH-Q07 | FY14 Q2 file prints the Q3 date and cutoff | `report_editions.json:5-11`, `config/semantics.yml:2007-2011` | inherent. Settle whether a true Q2 exists by checking the publisher listing |
| QCASH-Q08 | FY25 Q3 edition was missing from the corpus | `release-notes/data/2026.07.31.yml:13-29` | inherent (archive completeness) |
| QCASH-Q09 | Page 1 stacks a revenue grid over an expense grid of a different width | `qcmr-cash.yml:4-14`, `geometric_backend.py:891-965` | inherent |
| QCASH-Q10 | From FY14 a table finder sees only narrow ruled fragments; the span path uses them | `qcmr-cash.yml:4-9`, `geometric_backend.py:147-166, 967-1016` | artifact (pdfplumber table priors as region evidence) |
| QCASH-Q11 | Structured table boxes clip the expense tail (Opening, CLOSING) | `qcmr-cash.yml:10-12`, `geometric_backend.py:202-226, 845-857` | artifact (table priors) |
| QCASH-Q12 | Expense caption band sits right under TOTAL CASH RECEIPTS; a fixed lookback swallowed that total | `geometric_backend.py:119-138` | artifact (fixed header lookback) |
| QCASH-Q13 | Final endpoint columns print closer than the page whitespace threshold | `geometric_backend.py:229-257, 937-944` | inherent |
| QCASH-Q14 | FY23 Q1 and Q2 broken font: `E(cid:121)PENSES`, or "E PENSES"; OCR reads AND as ANO | `qcmr-cash.yml:15-18`, `geometric_backend.py:576-588` | inherent |
| QCASH-Q15 | A tall word bridges two baselines so labels weld: FY08 Q1, FY08 Q4, FY14 Q1 | `qcmr-cash.yml:19-26`, `geometric_backend.py:614-630` | artifact (phrase merge before baseline grouping). The tall word is real |
| QCASH-Q16 | FY08 Q4 margin debris "co ~" bridges Long-Term Debt and Interfund Charges | `qcmr-cash.yml:27-31`, `geometric_backend.py:738-746` | inherent (debris); the regroup switch is artifact |
| QCASH-Q17 | Numeric-only rows and a "CASH FLOW PROJECTIONS" row leak into tables | `qcmr-cash.yml:32-37`, `layouts.py:1164-1169` | artifact (whole-page line capture) |
| QCASH-Q18 | FY08 Q2 raw Textract makes a right-margin "68.9" into a row label | `qcmr-cash.yml:1019-1023`, `tests/test_qcmr_cash_source_acknowledgments.py:146-197` | unsure. Render FY08 Q2 page 1 to see whether 68.9 is printed margin ink or OCR debris |
| QCASH-Q19 | Early Textract grids weld three sparse zero rows into one band; eight explicit zeros restored in four reports | `qcmr-cash.yml:38-49`, `tables/reconciliation_rows.py:412-416`, `config/entities.yml:1948-1951` | artifact (Textract table grid); the adjacent sparse zero rows are inherent |
| QCASH-Q20 | One printed decimal in millions; rounding mode not stated | `qcmr-cash.yml:50-58`, `tables/checks.py:84-92` | inherent |
| QCASH-Q21 | Textract drops or swaps the decimal separator: 33 FY07 Q3 cells, FY08 Q1 "69,2" | `qcmr-cash.yml:89-387`, `tables/reconciliation_values.py:172-232` | inherent for scans |
| QCASH-Q22 | FY07 Q4: Textract reads 65.8, 108.7, 1,165.9; page prints 85.8, 109.7, 1,185.9. The native word layer has the right digits. Labels arrive garbled from an OCR layer, source not stated | `qcmr-cash.yml:72-88`, `docs/value-contract-vertical-slice-acceptance.md:22-24` | inherent |
| QCASH-Q23 | Textract's wrong FY07 Q4 annual 1,165.9 makes the row and column foot; the printed value breaks both | `qcmr-cash.yml:86-88, 894-902` | inherent. A score-based source choice picks the wrong digit |
| QCASH-Q24 | FY07 Q4 OCR label corruption ("Property Tull", "Opening Bai.nee") | `config/entities.yml:4507-4558` | inherent |
| QCASH-Q25 | Family-wide OCR label variants, including FY12 Q3 "Burchase" | `config/entities.yml:1789-2237, 4686-4695`, `config/semantics.yml:1494, 1906` | inherent |
| QCASH-Q26 | One scan OCRs the "Mergers" header as "mergere" | `config/semantics.yml:1484-1487` | inherent |
| QCASH-Q27 | Rows named Total are line items; Current Year Appropriation is an unlabeled subtotal | `qcmr-cash.yml:59-64`, `CASES.md:29` | inherent |
| QCASH-Q28 | Memo breakdowns printed beside their combined row: gross wage and Tax to PICA; CY and PY; PICA Debt Service and City Account | `qcmr-cash.yml:1024-1058` | inherent |
| QCASH-Q29 | FY10 Q3 abbreviates the gross label and drops "Total" from the net wage row | `qcmr-cash.yml:1030-1039` | inherent |
| QCASH-Q30 | Component identities CY + PY and Debt Service + City Account | `qcmr-cash.yml:65-71`, `tables/reconciliation_assertions.py:41-110` | inherent |
| QCASH-Q31 | FY25 Q2 prints no net wage row, only gross and the PICA deduction | `release-notes/data/2026.07.31.yml:44-56` | inherent |
| QCASH-Q32 | Revenue grid has three column eras (16, 15, 16 measures) | `config/semantics.yml:1351-1364, 1822-1832, 2031-2044` | inherent |
| QCASH-Q33 | Expense grid has two column eras (17 with Mergers, then 16) | `config/semantics.yml:1443-1483, 1904-1941` | inherent |
| QCASH-Q34 | A 15-column extraction of a modern revenue grid must fail, not be read as the middle era | `config/semantics.yml:2035-2037`, `tests/test_qcmr_semantics.py:412-427` | inherent |
| QCASH-Q35 | A printed but empty physical column (FY26 Q1) | `tests/test_qcmr_semantics.py:430-476` | inherent |
| QCASH-Q36 | Sparse rows shifted the annual value into June in 19 editions | `release-notes/data/2026.07.29.yml:13-41`, `normalization.py:550-592` | artifact (role assignment by count from the right). Sparse rows are inherent |
| QCASH-Q37 | Thirteenth column means annual sum on flows, FY start on Opening, FY end on Closing | `config/semantics.yml:1522-1617`, `temporal_contracts.json:151-163` | inherent |
| QCASH-Q38 | Page 2 is a 12-month grid with no total; its caption is damaged or missing in some editions | `config/semantics.yml:1489-1521` | inherent |
| QCASH-Q39 | Stitching joins page 2 to the page 1 expense grid | `qcmr-cash.yml:713-717`, `tables/stitching.py:1084-1115` | artifact (positional page stitching) |
| QCASH-Q40 | Revenue and expense come out as one extracted table in some modern editions | `qcmr-cash.yml:641-690`, `normalization.py:546-549` | artifact (region detection) |
| QCASH-Q41 | Actual vs projected follows the quarter cutoff, with 8 edition overrides | `config/semantics.yml:1720-1776, 2007-2011` | inherent. Unsure whether the page marks the cutoff; settle by rendering FY09 Q1 and FY10 Q2 headers |
| QCASH-Q42 | Each month reprinted in up to four editions; snapshots, not additive | `docs/site/guides/series.md:35-45` | inherent |
| QCASH-Q43 | CLOSING = Opening + Excess + TRANS; blank TRANS is not zero | `qcmr-cash.yml:507-694` | inherent |
| QCASH-Q44 | Revenue endpoint identity changes by era | `qcmr-cash.yml:476-506` | inherent |
| QCASH-Q45 | Row Total = sum of months within rounding (1,215.9 vs printed 1,215.8 in FY08 Q2) | `qcmr-cash.yml:388-475` | inherent |
| QCASH-Q46 | Publisher arithmetic errors in 10 editions, 11 records | `qcmr-cash.yml:695-1018` | inherent |
| QCASH-Q47 | Some discrepancies are left open on purpose, so acknowledgments must be narrow | `qcmr-cash.yml:416-417, 446-447, 675-676, 693-694, 951-952` | inherent |
| QCASH-Q48 | Acknowledgments bind to table index, row index, column index, hypothesis name and fingerprints; FY12 Q4 drifted | `qcmr-cash.yml:742-755`, `tests/test_qcmr_cash_source_acknowledgments.py:200-249`, `docs/investigations/release-readiness-policy/README.md:72`, `config/layouts.yml:5` | artifact (engine coordinates as identity). Total Current Revenue sits on rows 12 to 18 across editions, which is inherent |
| QCASH-Q49 | Residuals stored as binary floats (40.400000000000006, -14.200000000000003) | `qcmr-cash.yml:860, 922` | artifact (float money) |
| QCASH-Q50 | Word source chosen per edition by reconciliation score; FY25 Q2 bound to raw Textract | `qcmr-cash.yml:491-492`, `tests/test_status.py:1037-1050` | artifact (score-based selection). The need for OCR on scans is inherent |
| QCASH-Q51 | Unit is millions; multiplier 1,000,000; source scale declared as 4 | `config/semantics.yml:1777-1795`, `config/release_contracts.yml:33-53` | inherent unit; the scale of 4 is unsure (find why it is not 1) |
| QCASH-Q52 | Dashes and nonnumeric marks are not zero | `release-notes/data/2026.08.02.yml:15-20` | inherent |
| QCASH-Q53 | Negatives in parentheses and with a minus sign | `qcmr-cash.yml:130, 700-704, 975` | inherent |
| QCASH-Q54 | Label renames across eras | `config/entities.yml:1753-2148` | inherent |
| QCASH-Q55 | Two-line label "Excess (Def) of Receipts / over Disbursements"; welded variants | `config/entities.yml:2113-2123`, `config/semantics.yml:1524` | inherent wrap; welded forms are artifact (phrase merge) |
| QCASH-Q56 | "Purchase of Services" and "Payments to Other Funds" act as section qualifiers | `config/entities.yml:4684-4703`, `tests/test_entities.py:1749-1765` | unsure. Render a modern expense grid to see what rows sit under these headings |
| QCASH-Q57 | Funds appear mid-series on page 2 | `release-notes/data/2026.07.31.yml:34-40` | inherent |
| QCASH-Q58 | FY11 Q2 CLOSING BALANCE loses November and June to OCR decay | `tests/test_qcmr_semantics.py:620-662`, `normalization.py:561-580` | inherent for scans |
| QCASH-Q59 | Exact Decimal values are enforced only for cash and monthly City | `config/release_contracts.yml:4-6` | artifact |
| QCASH-Q60 | Release notes say seven FY07 Q4 cells were corrected; config holds three. A fixture names an FY07 Q4 August fixed-decimal cell not in config | `release-notes/data/2026.07.29.yml:108-110`, `docs/value-contract-vertical-slice-acceptance.md:25-29` | unsure. Diff the last release's value-evidence ledger for FY07 Q4 |
| QCASH-Q61 | Catalog says 79 documents; FY07 Q3 to FY26 Q3 is 77 quarters | `docs/site/data/index.md:420` | unsure. List the cut files or the release manifest |

## 10. Old code that serves this family

| Job | File | Lines | Keep as code or as knowledge |
|---|---|---|---|
| Acquisition | `qcmr.py` | 435 | Code: header-band page rule, longest run, period parsing, feed filtering. Drop the PDF splitter. |
| Acquisition | `phila_source_sync.py` | 231 (shared) | Knowledge: host aliasing and listing-vs-PDF period check. |
| Layout | `config/layouts/qcmr-cash.yml` | 1,058 | Knowledge: every review record becomes a page-cited acknowledgment or a parser parameter. |
| Layout model | `layouts.py` (cash-only models 406-758, options 1083-1131) | about 400 of 1,661 | Knowledge. |
| Parsing | `parsers/geometric_backend.py` (cash paths 119-257, 838-1016) | about 300 of 1,083 | Code idea only: split at ordered captions, per-section columns, densest-row witness. |
| Parsing | `tables/fused_columns.py`, stitching | 1,491 and more | Knowledge: cash shows that page stitching must be explicit. |
| Semantics | `config/semantics.yml` 1351-2245 | 895 | Knowledge: column lists per era, row-role layouts, cutoffs, unit. |
| Entities | `config/entities.yml` 1753-2264, 4507-4558, 4684-4703 | about 580 | Data: move as the cash label map. |
| Checks | `tables/reconciliation_values.py`, `tables/reconciliation_assertions.py`, `tables/checks.py` | 902, 643, 1,357 | Code: the rounding bound at `checks.py:80-100`. Rest is knowledge. |
| Editions | `report_editions.json`, `temporal_contracts.json` (cash block) | 13, about 40 | Data. |
| Tests | `tests/test_qcmr_semantics.py`, `tests/test_qcmr_cash_source_acknowledgments.py`, `tests/test_qcmr.py` | 683, 434, 336 | Knowledge: the pinned values (FY11 Q1, FY14 Q2, FY22 Q1, FY25 Q1 and Q4, FY26 Q2 and Q3 wage rows) are good golden cases. |

## 11. The least a parser needs

Inputs: the whole QCMR PDF by SHA-256, its period-ending date, and per edition a word source
(text layer or Textract words). For FY07 Q4, both, chosen cell by cell by a reviewed record.

Steps:

1. Find the two cash pages by the header rule in section 4. Fail if not exactly two.
2. Read the printed as-of date and quarter. Fail if it disagrees with the listing. Record both.
3. Page 1: cut at the REVENUES and EXPENSES AND OBLIGATIONS captions. Group words into rows by
   baseline, not by tolerance clusters that can bridge rows.
4. Read the column header of each grid. Pick the era from header tokens. Check that the era
   agrees with the fiscal year range.
5. Assign each value to a column by x-position against that grid's header, never by counting
   from the right. Keep blanks as blanks.
6. Parse values as Decimal one-decimal millions. Parentheses and minus are negative. Keep dashes
   and marks as text. Apply reviewed fixed-decimal readings only where a record names the cell.
7. Map labels to entities through the cash label map. Mark memo rows. Unmatched labels fail.
8. Page 2: a separate 12-month table of funds.
9. Emit long rows: edition, as-of date, grid, entity, target month or measure, actual or
   projected, source text, value.

Era parameters: revenue endpoint columns (4, 3, 4 names); expense endpoint columns (5 or 4);
page 2 caption; cutoff overrides for 8 editions; memo-row labels; the FY07 Q3, FY07 Q4, FY08 Q1
cell records.

Checks to declare: row Total = months; revenue endpoint identity per era; expense endpoint
identity (to be confirmed); Total Current Revenue and the receipts, disbursement and
appropriation subtotals; the two component sums; the closing balance identity with blank TRANS
excluded; page 2 totals; Opening(m+1) = Closing(m). All under the strict 0.05 per term bound.
Warn-level cross-edition checks: Q4 June close equals next Q1 July open.

## 12. Unknowns

- Which editions are scans, which have a native word layer, and which word source each used.
- Whether the garbled FY07 Q4 labels come from Textract or from the native layer.
  The selection file is not in git.
- The exact first edition of each column era and each label rename.
- Whether the page marks actual and projected months, or only the cutoff date.
- Whether a true FY14 Q2 edition exists, and whether the held file equals FY14 Q3.
- Why the catalog counts 79 editions, and why the FY07 Q4 correction count is seven.
- The composition of TOTAL CASH RECEIPTS and TOTAL DISBURSEMENTS and the expense endpoint identity.
- Whether page 1 CLOSING BALANCE agrees with page 2 General.
- Whether the FY08 Q2 "68.9" is printed ink.
- Whether older full QCMR reports carry the same "CASH FLOW PROJECTIONS" header band.
