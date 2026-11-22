# BIB: Philadelphia Budget in Brief, adopted and proposed

Paths are shortened by dropping `packages/gov-budget-etl/src/gov_budget_etl/`. Test paths are
under `packages/gov-budget-etl/tests/`. The checkout holds no PDFs and no artifacts, so every
claim about a page comes from config, tests, docs or acknowledgment records.

## 1. Documents

The Budget in Brief is an annual book from the Office of the Director of Finance, listed in
the City document finder for post 151831 under one category, "Budget in Brief", that mixes
adopted and proposed editions (`budget_in_brief.py:32-37`, `budget_in_brief.py:3-6`).

- **Stage comes from the visible title only.** "Adopted" and "Approved" both mean adopted.
  "Proposed" means proposed. A title with both is rejected, a title with neither is skipped
  (`budget_in_brief.py:61-76`, `test_budget_in_brief.py:88-104`).
- **Filenames lie.** At least one proposed edition has "approved" in its filename
  (`budget_in_brief.py:64-66`; the test at `test_budget_in_brief.py:73-86` uses FY2011 as
  the example, which may or may not be the real case).
- **Fiscal year** is the single `FY\s*\d{2,4}` value across title and filename; two values
  fail (`budget_in_brief.py:79-88`).
- Storage today is `phila/budget-in-brief/<stage>/FY##.pdf` (`budget_in_brief.py:151-157`).

| Dataset | Editions in the catalog | What the corpus holds |
|---|---|---|
| `budget_in_brief_adopted` | FY2006 to FY2027, 22 documents (`docs/site/data/index.md:61-65`) | FY2009 to FY2027 are full, SHA-bound publisher books. FY2006, FY2007 and FY2008 are obligation-history excerpts that "predate the full-book catalog or were originally acquired as obligation-history excerpts" (`config/semantics.yml:1150-1154`, `config/page_types.yml:464-468`). |
| `budget_in_brief_proposed` | FY2022 to FY2027, 6 documents (`docs/site/data/index.md:91-95`) | All six are obligation-history excerpts, "explicitly onboarded" (`config/page_types.yml:466`). Test pages are numbered 1 to 7 (`test_page_types.py:1092-1165`). |

**Text layer.** FY2011 to FY2015 adopted are image-only scans that need Textract
(`README.md:342-348`). The tests confirm OCR traces in FY2011, FY2012 and FY2015
(`test_page_types.py:1012-1060`, `1289-1311`). FY2009 was read with the geometric parser on
the PDF text layer (`docs/investigations/unverified-row-audit/CASES.md:10`). FY2015 was read
with `textract_geometric` (`CASES.md:9`). No file records the text layer per edition; the
README sentence is the only record. The text layer of FY2006 to FY2008, FY2016 to FY2027 and
the proposed excerpts is not recorded; the absence of OCR quirks suggests text PDFs.

**Pages.** A full book is about 80 to 90 pages. Narrative and chart pages come first. The
fund statements start near page 17 (General Fund summary, `config/resolved_assertions.yml:256`,
`416`), each fund summary followed by its revenue schedules. The All Funds statement sits near
page 76 to 79. The obligation history appendix comes last, about eight pages
(`config/page_types.yml:552`): FY2009 pages 75 to 80, FY2010 pages 80 to 81 for the General
Fund total, FY2027 Finance on page 82 and the General Fund total on page 87
(`config/layouts/budget-in-brief.yml:190-192,222,258`; `archive/documentation/try.md:59,111-120`;
`notebooks/philadelphia_budget_trends.ipynb` cell 11 output).

## 2. Tables

### General Fund obligation history (adopted FY2006 to FY2027, proposed FY2022 to FY2027)

A row is one spending class within one department, or a department total.

- **Rows.** A department name is a value-less section heading. Under it come class lines:
  Personal Services, Pers. Svcs.-Emp.Benefits, Purchase of Services, Materials, Supplies &
  Equip., Contrib., Indemnities & Taxes, Payments to Other Funds, Advances and Other Misc.
  Payments (also "Advances & Miscellaneous Payments"), Debt Service, then "Total"
  (`config/entities.yml:4665-4677`). The last row is "Total, General Fund"
  (`config/page_types.yml:556-560`).
- **Size.** The General Fund total sits at row 373 (FY2008, FY2009) and 376 (FY2010)
  (`config/layouts/budget-in-brief.yml:139,171,233,269`). That implies roughly 35 to 40
  department blocks. This is an inference. The adopted subset holds 27,007 trusted facts
  over 22 editions (notebook cell 1 output); proposed holds 9,267 facts over 6 editions
  (`docs/site/data/index.md:94`).
- **Multi-page.** One continuous table over about eight pages. Department headings run on
  across page breaks. Every page repeats "CITY OF PHILADELPHIA", "GENERAL FUND", "OBLIGATION
  HISTORY" and "FISCAL YEAR" banners (`config/page_types.yml:582-594`). Numbered notes such as
  "(10) New department established in FY26." print under the last department on a page
  (`config/page_types.yml:595-597`, `test_page_types.py:1139-1145`).
- **Columns.** Whole dollars. See the era table in section 3.

### Operating fund summary (adopted FY2009 to FY2027)

One boxed statement per fund, plus an All Funds statement. A row is one line of the fund
statement: revenues by category, obligations by class, surplus or deficit, fund balance.

- **Banner.** "CITY OF PHILADELPHIA SUMMARY OF OPERATING BUDGET", "FISCAL YEARS 2024, 2025,
  AND 2026", "FISCAL 2026 OPERATING BUDGET (Amounts in Thousands)", then a ruled "FUND / NO. /
  TABLE" row such as "General 010 IA" (`test_page_types.py:901-919`). All Funds prints
  "Summary All Funds I" with no fund number (`test_page_types.py:1240-1263`).
- **Columns.** A LINE NO. margin, the label, a supporting-schedule reference column, then
  Actual, Original Budget, Current Estimate, Budget, Increase (Decrease) Amount, Percent
  (`config/semantics.yml:895-948`). Amounts in thousands.
- **Labels carry line formulas**, for example "Total Obligations / Appropriations (19+20)"
  and "Adjusted Fund Balance June 30 or Prior Fiscal Year (23+29)", and long labels wrap onto
  two lines (`test_page_types.py:1186-1190`, `test_resolved_assertions.py:586-600`).
- **Size.** FY2027 has 16 fund statements plus All Funds (`config/resolved_assertions.yml:416`).

### Operating revenue schedule (adopted FY2009 to FY2027)

Supporting schedules that break one revenue category of one fund into sources.

- **Banner.** "SUPPORTING SCHEDULES FOR REVENUES", "FUND NO." with name and number (for
  example "Budget Stabilization 01-011"), then "REVENUE SCHEDULE NO." with category and
  schedule id (for example "Revenue from Other Funds IO-4", "Revenue from Other Governments
  IG-3", "Locally Generated Non-Tax IN-2") (`test_page_types.py:920-940`, `1012-1060`).
- **Rows.** Bold agency banners own blocks of source lines. Non-bold sub-banners ("Federal:",
  "State:", "Other Governments", "Licenses & Permits") refine the source without changing the
  owner (`config/page_types.yml:573-579`). Blocks end in subtotals; the schedule ends in a total
  that repeats a line of the fund summary (`config/resolved_assertions.yml:29-32`).
- **Columns.** Same six measures as the fund summary, no reference column
  (`config/semantics.yml:965-977`). Thousands.
- **Multi-page.** A schedule continues across pages and repeats its banners; pages stitch by
  fund number and schedule id (`config/page_types.yml:539-541`, `568-572`).

## 3. Format eras

| Era | Editions | Obligation history columns | Ruled schedules | Evidence |
|---|---|---|---|---|
| Excerpt | adopted FY2006 to FY2008 | 5: Prior Actual, Estimate Increase, Estimated Obligations, Budget Increase, Budget | not held | `config/semantics.yml:1150-1168`; FY2008 change columns are indices 2 and 4 (`config/layouts/budget-in-brief.yml:133-136`) |
| Text books | adopted FY2009, FY2010 | 5 | yes, with LINE NO. margin | `config/layouts/budget-in-brief.yml:174-178,237-241`; geometric (`CASES.md:10`) |
| Scans | adopted FY2011 to FY2015 | 5 | yes, OCR | `README.md:342-348` |
| Text books | adopted FY2016 to FY2025 | 5 | yes | `config/semantics.yml:1091-1149` |
| Six columns | adopted FY2026, proposed FY2026 | adds Prior Adopted Budget: Prior Actual, Prior Adopted Budget, Estimate Increase, Estimated Obligations, Budget Increase, Budget | yes | `config/semantics.yml:978-1053` |
| Seven columns | adopted and proposed FY2027 | adds Prior Increase between actual and prior adopted | yes | `config/semantics.yml:1054-1090` |
| Proposed five columns | proposed FY2022 to FY2025 | 5 | not held | `config/semantics.yml:1155-1168` |

Other label changes with a known year:

- All Funds caption "Summary All I" in FY2017, "Summary All Funds I" in FY2026, and OCR
  "Summary All -" in FY2015 (`test_page_types.py:1240-1311`). The switch year is unknown.
- Budget Stabilization prints fund 15 through FY2020 and 01-011 from FY2021. Demolition prints
  15 from FY2023 (`config/funds.yml:58-73`).
- Fairmount Park and Recreation merge into Parks and Recreation from FY2011
  (`config/entities.yml`, `successions`).
- New departments appear with footnotes, for example the FY2026 Office of Prison Oversight
  (`test_page_types.py:1142-1143`).

## 4. Finding the table

Today pages are typed by title in one page-type profile, `phila_budget_in_brief_ruled_schedules`
(`config/page_types.yml:469-597`).

- The profile matches an exact allow-list of 25 document ids (`config/page_types.yml:470-495`).
  FY2006 to FY2008 adopted do not match, so their tables stay untyped
  (`test_page_types.py:1062-1070`).
- The profile needs a marker regex, so it declares a dummy that never matches,
  `__bib_no_marker__` (`config/page_types.yml:496`). Typing falls through to titles
  (`page_types.py:1115-1147`), matched case-insensitively (`page_types.py:1171-1186`).
- Titles: `^Obligation History$`, `\bSUMMARY OF OPERATING BUDGET$`,
  `\bSUPPORTING SCHEDULES FOR REVENUES$` (`config/page_types.yml:498-506`). Every other page is
  `evidence_only` (`config/page_types.yml:507`, `test_page_types.py:1313-1328`).
- Context lines give the unit, fund, fund number, table id, revenue category and schedule id
  (`config/page_types.yml:508-538`).

No classifier, LLM step or page-range table is needed. The three titles print on every page of
their form, including continuation pages. The simplest reliable rule is: a page belongs to a
form when one of the three titles appears in its top lines; a schedule's identity is the
(fund number, table id) or (fund number, schedule id) printed in its ruled banner; the
obligation history is every titled page in order. Textract is needed only for FY2011 to FY2015.
The proposed and FY2006 to FY2008 excerpts are cut PDFs; if full books are archived instead,
the same title rule finds the appendix in place.

## 5. Arithmetic that holds

| Relation | Table | Today | How often the source breaks it |
|---|---|---|---|
| Class lines sum to department Total | obligation history | generic total inference | FY2008 and FY2009 District Attorney change columns, FY2010 Refunds change (3 acks) |
| Department Totals sum to Total, General Fund | obligation history | generic | FY2008, FY2009, FY2010 General Fund change columns (3 acks) |
| Change = later column minus earlier column, per row | obligation history, all eras | `declared_difference_identity` hypotheses in acks | same 6 cases; FY2010 prints the estimate 244,500 as the change |
| Budget minus Current Estimate = Increase | fund summary | `row_accounting_identities` (`config/semantics.yml:885-894`) | not recorded |
| Percent = Increase / Current Estimate | fund summary, schedules | none | not checked; 50/779 = 6.4% holds in the test row (`test_page_types.py:1190`) |
| Line formulas in labels, e.g. (19+20), (23+29) | fund summary | none | not checked |
| Detail and subtotals sum to schedule total | revenue schedule | generic, with `group_by_section_header` | FY2022 p54, FY2023 p49, FY2026 p21 (3 acks) |
| Last schedule total = matching summary line | schedule vs summary | `lookup_equals` (`config/resolved_assertions.yml:8-66`) | 5 records, 7 cells |
| Fund summaries sum to All Funds | summary vs summary | `sum_equals` (`config/resolved_assertions.yml:68-132`) | 3 records, 19 cells |
| Edition N Budget = edition N+1 Original Budget (summary) or Prior Adopted Budget (history) | cross-edition | none | unknown |

Acknowledgment records for this family:

| Kind | Count | Where |
|---|---|---|
| Layout total acks, obligation history change columns | 6 (FY2008 x2, FY2009 x2, FY2010 x2) | `config/layouts/budget-in-brief.yml:111-304` |
| Layout total acks, revenue schedules | 3 (FY2022, FY2023, FY2026) | `config/layouts/budget-in-brief.yml:32-110` |
| Cross-table `source_misprint` | 6 records (FY2019, FY2022, FY2023, FY2025, FY2026, FY2027) | `config/resolved_assertions.yml:139-417` |
| Cross-table `source_omission` | 2 records (FY2009, FY2022) | same |
| Total | 9 layout acks, 8 discrepancy records over 26 cells | |

The cross-table engine (`resolved_assertions.py`, 1,747 lines) serves only this family
(`fnmatch` on `family_pattern` at `resolved_assertions.py:321,792`). Its report feeds a status
headline (`status.py:973-986`) and the admin page. No release or trust code reads it; it does
not gate rows.

**The 1.9 percent.** 2,394 of 127,844 adopted facts are withheld (`docs/site/data/index.md:64`).
The checkout holds no release artifacts, so the exact set cannot be listed. A fact is served
only when `table_accounted`, `column_verified` and `value_verified` are all true
(`packages/gov-budget-data/src/gov_budget_data/trust.py:26-53`). Release 2026.07.31 needs reader
0.4.0, while v2 releases need 0.4.1 (`release-notes/data/2026.07.31.yml:6`,
`docs/investigations/release-readiness-policy/README.md:42`), so it may have used the older
`table_reconciled AND headers_verified` rule. Evidence on who fails:

- Proposed (obligation history only) is 100 percent, and adopted obligation history serves
  27,007 facts. The withheld facts most likely sit in fund summaries and revenue schedules.
  This is an inference.
- Both audited withheld cells in this family fail only the table gate (F/T/T):
  FY2015 p37 County Liquid Fuels, where four double-dash operands make a compensation subtotal
  uncheckable; and FY2009 p68 Acute Care Hospital Assessment, a budget cell proved by its own
  row identity that the old accounting did not credit (`CASES.md:9-10`,
  `source-observations.json` S01, S02).
- Dash cells stay null and are withheld by design (audit README, "Correct exclusion of a
  missing value").

So the withheld rows are mostly faithful values in small-fund ruled schedules where dashes
leave a subtotal uncheckable or where a row identity was not credited. No wrong transcription
was found in the sample.

## 6. Row labels and entities

Departments resolve through the shared registry, not a family list.

- 106 entities list `budget_in_brief_*`: 99 departments, 6 "other", 1 rollup
  (`config/entities.yml`, counted). The rollup is `phl_general_fund`, shared with monthly City
  collections (`config/entities.yml:369-377`).
- Department identity comes from the section heading (`entity_context_field: section`) and is
  required for every obligation-history row (`config/page_types.yml:545-549`). Class lines are
  qualifiers under that section (`config/entities.yml:4665-4677`).
- Footnote markers decorate names, for example "Office of Prison Oversight (10)"; they are
  stripped before matching (`entities.py:56-61`, `release-notes/data/2026.07.24.1.yml:26-28`).

**Relation to QCMR obligations and positions.** The same entity ids serve both families. Of 107
entities tagged for QCMR obligations or positions, 99 are also tagged for Budget in Brief.

| Point | Budget in Brief | QCMR |
|---|---|---|
| Grain | department x spending class x 5 to 7 measures | O-2: department x 9 measures, no class split; P-1: positions, no Budget in Brief counterpart |
| Sub-department lines | Finance-Employee Benefits, Finance-Refunds, Public Property-SEPTA Subsidy, Streets-Disposal and others as separate blocks | same lines, same ids (`config/entities.yml:2322` onward) |
| Only here | L&I Demolition, Recreation Stadium Complex (`config/entities.yml:2669,2689`); Civic Center and Tax Reform Commission shared only with supplemental | rollups City Representative and Commerce, Streets and Sanitation; OIT base; Finance federal grant and recession reserves; unassigned |
| General Fund total | `phl_general_fund` | `phl_obligations_general_fund_total` (`config/entities.yml:3250`); both alias "TOTAL GENERAL FUND" |
| Units | whole dollars | whole dollars (`config/semantics.yml:1305-1316`) |

No check compares the two families today (`config/reconciliation.yml` covers only budget
detail). A plausible check is that the Budget in Brief adopted budget for FY N equals the QCMR
FY N "Adopted Budget" per department. This is unverified.

Funds resolve through `config/funds.yml` (17 funds, two scopes). Printed fund numbers carry a
trailing zero (010 General, 080 Grants, 690 Water Residual) and are normalized by
`funds.py:23-36`. Names win over codes (`funds.py:244-249`).

## 7. Values

- Fund summaries and schedules: thousands, declared by the banner "(Amounts in Thousands)" and
  scaled by 1,000 (`config/semantics.yml:951-964`). Obligation history: whole dollars
  (`config/semantics.yml:1010-1021,1139-1149`).
- Percent column: passthrough, optional and sparse; its absence must not shift money roles
  (`config/semantics.yml:949-950`, `test_semantics.py:1730-1745`).
- Double dash "--" in ruled schedules means no value. It stays null, never zero (`CASES.md:9`).
- A blank printed cell exists where a value is due: FY2026 p21 Procurement subtotal leaves its
  change blank (`config/layouts/budget-in-brief.yml:85-110`).
- FY2009 prints the General Fund adopted total rounded to thousands
  (`config/layouts/budget-in-brief.yml:213-225`).
- OCR damage in scans: "/" read as "I", the unit banner split onto two lines, a missing period
  after "FUND NO", the table id read as "-" (section 9).

## 8. Editions and revisions

- One adopted and at most one proposed book per year. Stage and year identity are unique; a
  duplicate listing fails (`budget_in_brief.py:127-131`).
- Adopted and proposed are distinct stages, not vintages of one value
  (`notebooks/philadelphia_budget_trends.ipynb` cell 2).
- Overlap: edition N prints FY N-2 actual, FY N-1 estimate and FY N budget. The fund summary
  also prints FY N-1 original budget, which should repeat edition N-1's budget. FY2026 and
  FY2027 obligation histories add the prior adopted budget. No rule picks a canonical value
  across editions today; each fact keeps its document.
- Restatement exists: the FY2020 book matches the FY2021 detail restatement, not the FY2020
  supplemental report (`config/audit.yml:157-162,194-198`).
- Excerpts and full books share a path. Provenance sidecars decide whether local bytes are the
  catalog edition; replacing needs `--replace-existing` (`commands/budgets.py:147-153,231-244`).

## 9. Quirk ledger

| Id | What happens in the document | Old handling | Kind |
|---|---|---|---|
| BIB-Q01 | Adopted and proposed share one catalog category | `budget_in_brief.py:32-37,112-118` | inherent |
| BIB-Q02 | "Approved" and "as Approved by Council" mean adopted | `budget_in_brief.py:36`; `test_budget_in_brief.py:88-104` | inherent |
| BIB-Q03 | A proposed file is named "approved"; only the title is trusted | `budget_in_brief.py:64-66`; `test_budget_in_brief.py:73-86` | inherent |
| BIB-Q04 | Unstaged titles ("FY2024 Budget in Brief") exist and are skipped | `budget_in_brief.py:116-118`; `test_budget_in_brief.py:61-70` | unsure: whether real listings lack a stage; a catalog snapshot settles it |
| BIB-Q05 | FY in two or four digits across title and filename | `budget_in_brief.py:35,79-88` | inherent |
| BIB-Q06 | Local excerpts sit under the full-book filename | `budget_in_brief.py:8-11`; `commands/budgets.py:147-153` | artifact of path-keyed storage |
| BIB-Q07 | FY2006 to FY2008 adopted held only as obligation-history excerpts | `config/semantics.yml:1150-1168`; `config/resolved_assertions.yml:11-19` | unsure: whether full books exist anywhere |
| BIB-Q08 | Proposed FY2022 to FY2027 held only as excerpts | `config/page_types.yml:466,490-495` | unsure: whether full proposed books are in the catalog |
| BIB-Q09 | Pages have titles but no form code | dummy marker `__bib_no_marker__`, `config/page_types.yml:496` | artifact of the marker-required schema |
| BIB-Q10 | Title case varies | `page_types.py:1171-1186` | inherent |
| BIB-Q11 | Narrative and chart pages outnumber table pages | `config/page_types.yml:507` | inherent |
| BIB-Q12 | Unit declared in a page banner, thousands | `config/page_types.yml:511-514`; `config/semantics.yml:951-964` | inherent |
| BIB-Q13 | OCR splits "(Amounts in Thousands)" onto its own line (FY2011) | `config/page_types.yml:512-514`; `test_page_types.py:1012-1038` | inherent |
| BIB-Q14 | Fund banner has three ruled cells; All Funds has no number | `config/page_types.yml:518-529`; `test_page_types.py:1240-1263` | inherent |
| BIB-Q15 | All Funds caption "Summary All" (FY2017) vs "Summary All Funds" (FY2026) | `config/page_types.yml:526`; `config/resolved_assertions.yml:80,89` | inherent |
| BIB-Q16 | OCR reads the All Funds table id as "-" (FY2015) | `config/page_types.yml:523-526`; `test_page_types.py:1289-1311` | inherent |
| BIB-Q17 | Scan drops the period in "FUND NO." (FY2012) | `config/page_types.yml:530-535`; `test_page_types.py:1040-1060` | inherent |
| BIB-Q18 | Revenue schedule banner gives category and schedule id | `config/page_types.yml:536-538` | inherent |
| BIB-Q19 | One fund summary per box; schedules span pages; history spans about 8 pages | `config/page_types.yml:541,551-572` | inherent |
| BIB-Q20 | Department heading runs across pages; the General Fund total must not inherit the last department | `config/page_types.yml:556-560`; `release-notes/data/2026.07.28.1.yml:45-51` | inherent |
| BIB-Q21 | Revenue schedule owner is the bold agency row; "Federal:", "State:" refine it | `config/page_types.yml:573-579` | inherent |
| BIB-Q22 | Agency banners span several ruled cells and bound subtotals | `config/layouts/budget-in-brief.yml:26-31`; `export.py:1224-1235` | inherent; the option, built for vendor grids (`layouts.py:974-986`), is artifact |
| BIB-Q23 | Repeated banners on every page | `config/page_types.yml:582-594` | inherent |
| BIB-Q24 | Numbered notes "(9) ..." print below the last department | `config/page_types.yml:595-597`; `test_page_types.py:1117-1165` | inherent |
| BIB-Q25 | A wrapped data label starts with "Fiscal Year" | `test_page_types.py:1167-1195` | inherent |
| BIB-Q26 | Ruled boxes with a LINE NO. margin (FY2009 to FY2027) | `config/layouts/budget-in-brief.yml:21-25,176-178,239-241`; `tables/reconciliation_rows.py:402-410` | inherent; per-profile opt-in is artifact |
| BIB-Q27 | FY2008, FY2009, FY2010 need their own layout profiles | first match wins, `layouts.py:1408-1410` | artifact |
| BIB-Q28 | FY2008 acks use `table_types: [null]` | `config/layouts/budget-in-brief.yml:131-132`; `layouts.py:96-103` | artifact of untyped excerpts |
| BIB-Q29 | Fund summary has a schedule-reference column; roles are anchored from the right | `config/semantics.yml:895-898,920,970` | inherent |
| BIB-Q30 | Percent column optional and sparse | `config/semantics.yml:949-950` | inherent |
| BIB-Q31 | Obligation history in whole dollars, schedules in thousands | `config/semantics.yml:951-964,1010-1021` | inherent |
| BIB-Q32 | History grows from 5 to 6 (FY2026) to 7 (FY2027) columns | `config/semantics.yml:978-1090` | inherent |
| BIB-Q33 | Two or three change columns share the role `increase_decrease` | `config/semantics.yml:984-997` | artifact of the role vocabulary |
| BIB-Q34 | History header verification is empty strings | `config/semantics.yml:1004-1009,1134-1138` | unsure: header text per column would settle it |
| BIB-Q35 | Every config lists editions one by one; FY2028 fails closed | `config/semantics.yml:899-918`; `test_semantics.py:1723-1726` | artifact |
| BIB-Q36 | FY2011 to FY2015 are image-only scans | `README.md:342-348` | inherent |
| BIB-Q37 | OCR reads "/" as "I" in "Obligations / Appropriations" | `config/resolved_assertions.yml:116-119` | inherent |
| BIB-Q38 | Labels contain line formulas "(19+20)"; normalized text turns them into "23 29" | `config/resolved_assertions.yml:270-282`; `test_page_types.py:1190` | inherent |
| BIB-Q39 | One fund statement prints "of Prior Fiscal Year", the rest "or" | `config/resolved_assertions.yml:121-125` | inherent |
| BIB-Q40 | Summary says "Revenue from Other Funds of the City"; schedule omits "of the City" | `config/resolved_assertions.yml:56-60` | inherent |
| BIB-Q41 | Advances and Misc. Payments label varies; grand summary splits it across siblings | `config/resolved_assertions.yml:95-106`; `config/entities.yml:4672-4673` | inherent |
| BIB-Q42 | "Subtotal" repeats within one statement | `config/resolved_assertions.yml:107-108` | inherent |
| BIB-Q43 | A schedule has intermediate subtotals; its last total feeds the summary | `config/resolved_assertions.yml:29-32` | inherent |
| BIB-Q44 | Fund numbers print with a trailing zero (010, 690) or composite (01-011) | `funds.py:23-36` | inherent |
| BIB-Q45 | Fund 15 reused: Budget Stabilization to FY2020, Demolition from FY2023 | `config/funds.yml:58-73` | inherent |
| BIB-Q46 | Fund names misspelled ("Communtiy", "Fuelstax") | `config/funds.yml:17,41` | unsure: print or OCR |
| BIB-Q47 | Department names carry footnote markers | `entities.py:56-61` | inherent |
| BIB-Q48 | Sub-department blocks (Finance-Refunds and others) | `config/entities.yml:2322` onward | inherent |
| BIB-Q49 | Fairmount Park and Recreation merge in FY2011 | `config/entities.yml` successions | inherent |
| BIB-Q50 | Double-dash cells in ruled schedules | `CASES.md:9` | inherent |
| BIB-Q51 | FY2026 Procurement subtotal leaves a due change blank | `config/layouts/budget-in-brief.yml:85-110` | inherent |
| BIB-Q52 | FY2009 General Fund adopted total rounded to thousands | `config/layouts/budget-in-brief.yml:213-225` | inherent |
| BIB-Q53 | District Attorney 222,029 omitted from change totals in FY2008, repeated in FY2009 | `config/layouts/budget-in-brief.yml:114-208` | inherent |
| BIB-Q54 | FY2010 change columns contradict endpoints; Refunds change repeats the estimate | `config/layouts/budget-in-brief.yml:243-299` | inherent |
| BIB-Q55 | Revenue schedule totals omit a detail (FY2022) or misprint a subtotal (FY2023) | `config/layouts/budget-in-brief.yml:33-84` | inherent |
| BIB-Q56 | Summary and schedule disagree (FY2019, FY2022, FY2023, FY2026) | `config/resolved_assertions.yml:139-256` | inherent |
| BIB-Q57 | All Funds disagrees with its funds (FY2009, FY2025, FY2027) | `config/resolved_assertions.yml:258-417` | inherent |
| BIB-Q58 | Acks bind table index, row index and fingerprints | `config/layouts/budget-in-brief.yml:51-58,142-145` | artifact |
| BIB-Q59 | Cross-table relations live in a generic engine used by one family, and gate nothing | `resolved_assertions.py:321,792`; `status.py:973-986` | artifact |
| BIB-Q60 | FY2006 to FY2008 excluded from cross-table checks by an exclusion list | `config/resolved_assertions.yml:11-19` | artifact |
| BIB-Q61 | Textract cache keyed by document id and file hash | `parsers/textract_backend.py:408-416` | artifact |
| BIB-Q62 | FY2020 book cited at pages 2, 3 and 8 for obligation data | `config/audit.yml:157-162,194-198` | unsure: an older excerpt or printed page numbers; the FY2020 bytes settle it |

## 10. Old code that serves this family

| Job | File | Lines | Keep as code or as knowledge |
|---|---|---|---|
| Acquisition | `budget_in_brief.py` | 195 | Title-stage and year rules move with changes; path and sidecar logic is knowledge |
| Acquisition | `commands/budgets.py:119-269` | 151 of 609 | Knowledge: year-gap reporting is worth keeping as behavior |
| Acquisition | `publication_stage.py` | 29 | Moves as is (a three-value enum) |
| Page finding | `config/page_types.yml:462-597` | 136 | Knowledge: titles, banner regexes, context rules |
| Layout | `config/layouts/budget-in-brief.yml` | 304 | Knowledge: 9 page-cited defects; ids and fingerprints do not carry |
| Semantics | `config/semantics.yml:883-1168` | 286 | Knowledge: column order per era, units |
| Checks | `config/resolved_assertions.yml` | 417 | Knowledge: 2 relations, 8 discrepancy records, label equivalences |
| Checks | `resolved_assertions.py` | 1,747 | Stays; a declared check per relation replaces it |
| Entities | `config/entities.yml` (106 entries), `config/funds.yml` | 96 | Data moves with changes; shared with QCMR and supplemental |
| Funds | `funds.py` | 319 | Code-normalizer and code-history logic is worth keeping, rewrite smaller |
| Tests | `test_budget_in_brief.py` | 402 | Feed cases move with changes |
| Tests | `test_budget_summary_source_acknowledgments.py` | 355 | Knowledge: residuals and pages |
| Tests | `test_resolved_assertions.py` | 1,955 | Knowledge: OCR slash, partition and null-operand cases |
| Tests | BIB parts of `test_page_types.py:901-1345`, `test_semantics.py:1659-1745` | about 540 | Real banner lines are good fixtures |

## 11. The least a parser needs

1. **Inputs.** The full PDF by SHA-256, its stage and fiscal year from the catalog title, and
   the page words. For FY2011 to FY2015, Textract words for the table pages only.
2. **Find pages.** Keep pages whose top lines match one of three titles. Read the unit banner,
   fund banner and schedule banner from each.
3. **Read ruled grids.** Use the drawn rules for cells. Drop the LINE NO. margin. Keep the
   schedule-reference column apart from values. Join wrapped labels.
4. **Assign columns by era.** History: 5 columns to FY2025, 6 in FY2026, 7 in FY2027; proposed
   follows the same rule by year. Schedules: Actual, Original Budget, Current Estimate, Budget,
   Increase, optional Percent. Check the printed headers, including the year headers.
5. **Assign rows.** Department heading as owner, class line as the item, "Total" and "Total,
   General Fund" as totals; agency banners and sub-banners in revenue schedules; numbered notes
   and repeated banners dropped.
6. **Type values.** Thousands for schedules, dollars for history, percent separately; double
   dash and blank stay null.
7. **Declare checks.** Class lines to department total; departments to General Fund total;
   each change column equals its two endpoints; Budget minus Current Estimate equals Increase;
   label formulas such as (19+20); detail to subtotal to schedule total; schedule total equals
   summary line; funds sum to All Funds. Add a cross-edition check of budget against next
   year's original or prior adopted budget, and a cross-family check against QCMR O-2.
8. **Acknowledge** the 9 layout defects and 26 cross-table cells by page and residual.
9. **Resolve entities** through the shared registry, keyed by section heading; funds by name
   with year-bounded codes.

## 12. Unknowns

- Which 2,394 facts are withheld, and under which trust rule the 2026.07.31 numbers were made.
- Whether full books exist for FY2006 to FY2008 adopted and FY2022 to FY2027 proposed, and
  whether proposed books exist before FY2022.
- Which editions besides FY2011 to FY2015 lack a text layer.
- The exact header text of each obligation-history column, and whether change columns print
  a "Col. x less Col. y" formula.
- The year the All Funds caption changed from "All" to "All Funds".
- How often edition N's budget differs from edition N+1's original or prior adopted budget.
- Whether Budget in Brief adopted budgets equal QCMR O-2 adopted budgets per department.
- Whether the FY2020 page citations in `config/audit.yml` refer to an excerpt.
