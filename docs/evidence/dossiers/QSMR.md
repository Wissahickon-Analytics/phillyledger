# QSMR dossier (held out from the designers)

Everything here was seen via web fetch on November 21, 2026. The fetch passes PDF text through
a small model, so structure is probably right and every number must be confirmed against the
PDFs. Two editions were read: FY2016 Q2 (period ended December 31, 2015) and FY2023 Q4 (period
ended June 30, 2023). The FY2023 Q4 text was cut off partway through P-2, so its SM tables are
known only from the table of contents. No old code or config exists for this report.

## 1. Documents

- Publisher: School District of Philadelphia, Office of Finance. Title: "Quarterly School
  Manager Report". PDFs sit under `philasd.org/budget/wp-content/uploads/sites/96/<year>/<month>/`.
- Cadence: quarterly. The District's budget calendar says Q4 of the prior year is released in
  August, Q1 in November, Q2 in February and Q3 in May.
- Editions found by search: FY2016 Q2 and Q3, FY2017 Q3, FY2019 Q1, Q3 and Q4, FY2020 Q2,
  FY2021 Q4, FY2022 Q1 to Q4, FY2023 Q1 to Q4. No listing page was found. Editions after
  FY2023 were not found by search and may live under a different path.
- File names are irregular: `FY16-Q2-QSMR-Report_FINAL.pdf`, `QSMR-FY-2017-Q3_FINAL.pdf`,
  `QSMR-Reports_FY-2020-Q2_Web-Version.pdf`, `FY23-Q2-QSMR-w-ADA-2.pdf`. The upload folder
  date is the posting date, not the period. FY2016 files sit in a 2017 folder.
- Both editions read have a text layer. One table (P-1 in FY2016 Q2) extracts scrambled.
- Size: 38 numbered pages in FY2016 Q2, 51 in FY2023 Q4, plus a cover and roman-numbered
  front matter.

## 2. Tables

| Code | Title | A row is | Pages | Units |
|---|---|---|---|---|
| OF-1 | Operating Funds summary | a revenue or expenditure category, or a fund balance step; rows numbered | 1 | dollars |
| OF-2 | Revenue Detail | a revenue line, grouped by fund under each revenue class | 2 | dollars |
| OF-3 | Functional Expenditure Summary | a department or function, in sections A to G | 3 to 5 | dollars |
| CF-1 | Adopted Cash Flow | a cash-flow line, 19 rows, one column per month | 1 | thousands |
| CF-2 | Year-to-date Cash Flow | same rows, monthly actuals plus budget and variance | 1 | thousands |
| CF-3 | Vendor Payments over $100,000 | a vendor, sorted by amount | 6 to 14 | dollars |
| P-1 | Position Summary | a budget group or a staffing group | 1 to 2 | FTE |
| P-2 | Vacancy Listing by School | a school, grouped by network | 5 to 7 | FTE or count |
| SM-1 | Debt Service Schedule | a bond series | 1 | dollars |
| SM-4a | Major Grant Funds Summary | a grant fund | 1 | FTE and dollars |
| SM-5 | Title I School-by-School Budget and Spend | a school (not read) | 4 | not read |
| SM-6 | Minority and Women Business Enterprise Participation | not read | 1 | not read |

SM-2 (capital projects), SM-3 (allocation methodology), SM-4b (grant descriptions) and SM-7
(open data) are prose or lists, not tables.

## 3. Format eras (from two editions only)

| Feature | FY2016 Q2 | FY2023 Q4 |
|---|---|---|
| Supplementary codes | AR-1, AR-2a, AR-2b, AR-3; debt and capital have no code | SM-1 to SM-7 |
| Table order | OF, P, CF | OF, CF, P |
| OF value columns | prior year actual, adopted budget, year-to-date actual, percent of budget | amended budget, current projection, over (under), two prior year actuals |
| OF-3 row label | three-digit department code and name | department or function name |
| P-1 columns | four measures repeated for Operating, Categorical and Total (12 value columns) | four measures once |
| P-1 negatives | minus sign | parentheses |
| P-2 columns | network, school, code, grade level, high needs, site selection, vacancies | network, school, code, grade level, vacancy text, number of vacancies |
| P-2 networks | 1 to 9 plus Autonomy, Innovation, Opportunity, Turnaround | 1 to 13 plus Acceleration and Innovation |
| P-2 total row | "TOTAL VACANCIES" | none seen |
| CF-3 columns | vendor number, name, amount | name and amount, printed two vendors to a line |
| Title I by school | absent | SM-5 |

Search results show the AR codes had become SM codes by FY2016 Q3.

## 4. Finding the table

Each table page carries its code and title in the page header, and the table of contents lists
code, title and page. Titles in the contents can differ from the page title (CF-3). Section
divider pages, the cover and the disclaimer are unnumbered.

## 5. Arithmetic that should hold

- OF tables: subtotals and totals are sums of their lines. Over (under) is projection minus
  budget. Percent of budget is actual divided by budget. OF-3 section totals equal OF-1 rows.
- CF-1 and CF-2: ending balance is beginning balance plus receipts minus disbursements.
  Balance including notes is ending balance plus notes outstanding. In CF-2 the variance sign
  flips: actual minus budget for receipts, budget minus actual for disbursements.
- CF-3: subtotal plus "other payments" equals the grand total.
- P-1: groups sum to "School District Total". Difference is filled minus projected. In the
  2016 layout, Total is Operating plus Categorical.
- Debt service: total is principal plus interest.
- Sources break these by one unit in several places (OF-3 total, debt service, grants total,
  CF-2 variances, P-1 differences). These look like rounding of hidden decimals.

## 6. Row labels and entities

- Schools carry a name and a four-digit code. About 220 schools in FY2016 Q2 (rough count).
  Networks were renumbered and regrouped between 2016 and 2023.
- Departments in OF-3 had three-digit codes in 2016, not sequential, with gaps.
- Vendors: a vendor number in 2016 (charter vendors start with "C"), name only in 2023.
  Names are cut at about 30 characters. A vendor can appear more than once under different
  numbers. Charter schools appear as vendors.
- Funds: General Fund, Intermediate Unit Fund, Debt Service Fund. None is a City fund.
- Two subtotal rows in OF-2 carry the same wrong label, "TOTAL - LOCAL NON TAX REVENUE", for
  the Intermediate Unit and Debt Service blocks. A label alone cannot identify them.

## 7. Values

- Dollars in most tables, thousands in cash flow, FTE in positions. FTE and vacancy counts are
  fractional (0.2, 0.6, 2.4).
- Negatives in parentheses in most places, a minus sign in P-1 (2016) and in some percents.
- Zero prints as a dash, as "0" or as "0.00%". "NA" where a percent has no meaning. A dash can
  mean zero or blank.
- P-2 in 2023 has a free-text cell that lists position titles with counts in parentheses and
  wraps over several lines. "None" marks no vacancies.
- Entries marked "VOID" appear in the vendor list.

## 8. Editions and revisions

Each report restates the prior year: unaudited actuals in early quarters, audited later.
Quarterly projections are revised each quarter. No reissued edition was seen, but file names
such as `FY23-Q2-QSMR-w-ADA-2.pdf` suggest replaced uploads.

## 9. Quirk ledger

| Id | What happens in the document | Kind |
|---|---|---|
| QSMR-Q01 | No listing page found; file names and upload folders follow no rule | inherent |
| QSMR-Q02 | Table codes changed from AR to SM, and table order changed | inherent |
| QSMR-Q03 | OF value columns changed from actual and percent to projection and variance | inherent |
| QSMR-Q04 | Row numbers are printed in the margin, with gaps (2016) and duplicates (2023) | inherent |
| QSMR-Q05 | Two subtotal rows share one wrong label, so position in the block is the only key | inherent |
| QSMR-Q06 | Section subtotals are labeled "Sum:" and one-line sections have none | inherent |
| QSMR-Q07 | Totals differ from the sum of parts by one unit from rounding | inherent |
| QSMR-Q08 | CF-2 variance sign depends on whether the row is a receipt or a disbursement | inherent |
| QSMR-Q09 | Cash flow is in thousands while every other table is in dollars | inherent |
| QSMR-Q10 | CF-3 prints two vendors per line in 2023 and one per line with a vendor number in 2016 | inherent |
| QSMR-Q11 | CF-3 runs 6 to 14 pages, has an open-ended row set, truncated names and duplicate vendors | inherent |
| QSMR-Q12 | P-1 has 12 value columns under three spanning headers in 2016 and 4 columns in 2023 | inherent |
| QSMR-Q13 | P-1 text layer extracts scrambled in 2016 | unsure: needs the PDF |
| QSMR-Q14 | FTE counts are fractional, so a count column cannot be integer-only | inherent |
| QSMR-Q15 | P-2 network label prints only on the first row of each group | inherent |
| QSMR-Q16 | P-2 has a wrapped free-text cell with embedded counts in 2023 | inherent |
| QSMR-Q17 | P-2 rows are schools, an open set that changes each year, keyed by a four-digit code | inherent |
| QSMR-Q18 | Negative style differs by table and by era: parentheses, minus sign | inherent |
| QSMR-Q19 | A dash means zero in some cells and blank in others | inherent |
| QSMR-Q20 | A footnote says filled teacher counts include staff on leave; notes sit under tables | inherent |
| QSMR-Q21 | The contents title and the page title of a table can differ | inherent |
| QSMR-Q22 | Each edition restates prior-year figures, unaudited then audited | inherent |

## 10. Old code that serves this family

None.

## 11. The least a parser needs

Find each table by its code in the page header. Read row labels and value columns by era. For
fixed-row tables (OF-1, CF-1, CF-2, P-1), match rows to a declared list. For open-row tables
(OF-2 lines, OF-3 departments, CF-3 vendors, P-2 schools, SM-5 schools), accept any row and
carry a key from the page (code, or label plus block). Declare the sums in section 5 with a
one-unit tolerance where the source rounds. Carry units per table.

## 12. Unknowns

Editions before FY2016 and after FY2023. Whether any edition is a scan. The structure of SM-5
and SM-6. Whether P-1 in 2016 is readable from word positions. Exact school counts. Whether
row numbers are stable enough to use as keys within an era.
