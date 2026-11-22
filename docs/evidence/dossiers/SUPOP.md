# SUPOP: Supplemental financial reports, operating and revenue tables

Family: `phila_supplemental_report`, the City's audited "Supplemental Report of Revenues and
Obligations". Six tables in scope: `supplemental_agency_by_class`, `supplemental_fund_by_class`,
`supplemental_summary_activity`, `supplemental_summary_revenues`, `supplemental_revenues`,
`supplemental_revenues_by_source`. The three capital tables and acquisition belong to another
dossier. Shared layout mechanics are covered here in full.

Paths are shortened by dropping `packages/gov-budget-etl/src/gov_budget_etl/`. Config paths
start at `config/`. The checkout has no PDFs and no artifacts, so every fact about the documents
comes from config comments, acknowledgment records, tests, docs and one notebook output.

## 1. Documents

The corpus holds 10 editions at milestone years only: FY2003, FY2004, FY2005, FY2010, FY2015,
FY2020, FY2021, FY2022, FY2023, FY2024. The list comes from the cached output of
`notebooks/philadelphia_budget_trends.ipynb` (one "Total Operating Funds" row per edition) and
matches the catalog line "FY2003 to 2024, 10 source documents" (`docs/site/data/index.md:181-191`).
A FY2025 edition was published on August 28, 2026 and is not in the corpus
(`docs/philly-source-monitoring-audit-2026-09-11.md:42,61`). There is no FY2026 edition; the
`phila_supplemental_report_fy26` ids in tests are synthetic (`tests/test_resolution.py:2097`).

Cadence is annual, one PDF per fiscal year, published after the audit. The gaps (FY2006 to
FY2009, FY2011 to FY2014, FY2016 to FY2019) are corpus coverage, not parse failures.

Text layer. Every recorded parse of this family is the `geometric` backend over pdfplumber
words: the four audit cases (`docs/investigations/unverified-row-audit/CASES.md:27,28,44,45`),
the readiness case (`docs/investigations/release-readiness-policy/README.md:95`), and the
audit default backend. No config names Textract or an LLM backend for this family (grep of
`config/` for `textract` hits only QCMR cash and entities). Two code comments mention a
"decayed PDF text layer" that drops spaces and moves subtotal labels
(`tables/row_repairs.py:1143-1150`, `:1179-1182`), but they do not name an edition. No record
says any edition is a scan. Not verified: whether FY2003 to FY2005 have a clean text layer.

Page layout. Operating schedules are numbered "I" and capital schedules "II". Each operating
fund gets a letter: General Fund is I-D, Grants Revenue I-I, Community Development I-J (FY15),
Water I-N (FY21) or I-O (FY10). Within a fund: `-1` or `-2` is the net revenue statement,
`-3` or `-4` the agency by class statement, `-5` prior years' encumbrances. Known pages:

| Statement | Edition and PDF page | Source |
|---|---|---|
| Exhibit I-A, Summary Statement of Net Revenues by Fund | FY10 p11 | `tests/test_page_types.py:883-900` |
| Schedule I-C, Summary Statement of Appropriation Activity by Fund | FY20 p12, FY24 p12 | `layouts/supplemental-report.yml:326-334`; notebook |
| I-D-2 General Fund Statement of Net Revenue | FY10 pp21-24, FY20 p23, FY24 p22 | yml:438-524, 347-376; test_page_types.py:838-860 |
| I-D-4 General Fund agency by class | FY20 pp27-28, FY22 and FY23 p25 | `audit.yml:153-197`; yml:84-129 |
| I-D-5 prior years' encumbrances (not published) | FY03 p32, FY20 p32 | yml:818-885 |
| I-I-1 Grants Revenue Fund net revenue | FY20 to FY24 pp49-53 | yml:130-223, 557-817 |
| I-I-3 Grants Revenue Fund agency by class | FY23 p57 | yml:224-256 |
| I-J-1 Community Development net revenue | FY15 p59 | yml:285-312 |
| Water agency by class | FY20 pp77-78, FY21 pp75-76 (I-N-3) | `audit.yml:174,227`; yml:55-83 |
| I-O-1 Water Operating Fund net revenue | FY10 p77 | yml:405-437, 525-556 |
| Capital schedules II-A, II-A-1 | FY05 pp75-84, FY21 p87, FY23 p93 | yml:10-54, 886-960 |

PDF page numbers run 8 ahead of printed page numbers in FY20 and FY23 (PDF p77 is printed p69,
PDF p93 is printed p85: `docs/investigations/release-readiness-policy/README.md:71`;
yml:947). Total page count is not recorded; FY23 has at least 96 PDF pages (CASES.md:28).

## 2. Tables

All six are statements with a fixed column set and a label column. Values are dollars and
cents. Every page repeats the statement title, the fund banner and the column header.

### Activity statements (agency by class, fund by class, summary activity)

Columns, left to right (`config/semantics.yml:597-620`): Original Appropriations, Final
Appropriations, Encumbrances, Expenditures, Total Obligations, Unencumbered Balance, Percent of
Total Obligations to Appropriations. Some tables add FAMIS and "Fd BAL/AP Adjs" after
Encumbrances, giving 9 numeric columns (`semantics.yml:577-582`; see SUPOP-Q15). The column
header spans several lines; its top fragment "Percent of" prints alone (`page_types.yml:767-770`).

- `supplemental_agency_by_class` ("Statement of Budget Agency Appropriation Activity by Major
  Class"). A row is one major class of one budget agency within one fund. Agencies are running
  section banners ending in a colon ("Council:"), followed by class rows (Personal Services,
  Purchase of Services, and so on), then "Subtotal Council:". Class 100 may carry indented
  detail lines that support the class row and are not additive with it (`audit.py:705-708`). A
  small agency may print one amount row with no class breakdown (`audit.py:723-731`). The table
  ends in "Totals" for the fund. It runs over several pages: General Fund I-D-4 spans at least
  pp25 to 28; FY23 Grants I-I-3 reaches stitched row 128; FY21 Water reaches row 83.
- `supplemental_fund_by_class` ("Statement of Appropriation Activity by Major Class"). One row
  per major class for a whole fund, then a total. Short tables. Single-agency funds such as
  HealthChoices Behavioral Health and Water Residual print no agency banner
  (`page_types.yml:743-747`).
- `supplemental_summary_activity` (Schedule I-C). One row per operating fund, group totals such
  as "Total Special Revenue Funds", and the grand row "Total Operating Funds". The page prints
  "Operating Funds" where the fund banner would be and has no fund context
  (`page_types.yml:738-740`, `:801-804`). About one page.

### Revenue statements (net revenues, by major source, summary revenues)

Columns (`semantics.yml:659-672`): Original Budget Estimate, Final Budget Estimate, Actual,
Percent Collected, Prior Year Actual, Increase (Decrease). The period line covers two years:
"For the Fiscal Years Ended June 30, 2024 and 2023" (`tests/test_page_types.py:845-858`).

- `supplemental_revenues` ("Statement of Net Revenue(s)"). One per fund. The deepest hierarchy
  in the family: category banners (Taxes, Locally Generated Non-Tax Revenue, Revenue from Other
  Governments, Revenue from Other Funds), then department banners, then revenue source rows,
  then a department "Sub-Total", then "Total <category>", then "Total Net Revenue(s)". In
  Other Governments each department has Federal and State rows. Parent banners repeat on
  continuation pages and a later Sub-Total can close the whole parent (`tables/totals.py:1370-1428`).
  Sizes: General Fund I-D-2 spans 4 pages and about 430 stitched rows (FY10 rows 293 to 428);
  Grants I-I-1 spans 5 pages and about 155 rows.
- `supplemental_revenues_by_source` ("Statement of Net Revenues by Major Source"). Revenue by
  major source for a fund. Its percent column prints bare (`semantics.yml:649-652`).
- `supplemental_summary_revenues` (Exhibit I-A). One row per operating fund with totals. No
  fund banner (`page_types.yml:801-802`).

Not published but on adjacent pages: prior years' encumbrance statements (by agency and summary),
and a "NOTE:" block of non-budgeted obligations that some activity pages append
(`semantics.yml:3973-3986`; `page_types.yml:787-791`). A parser must cut them out.

Published size: 135,035 rows across 9 typed subsets, all default rows
(`docs/site/data/index.md:190-191`). That count is long format (one row per value) and is not
split by table in the checkout.

## 3. Format eras

| Change | Editions | Evidence |
|---|---|---|
| Header block: units and schedule on one separate line, "(Amounts in USD) Schedule I-D-5"; caps "CITY OF PHILADELPHIA", "GENERAL FUND" | older, shown for FY03 | `page_types.yml:733-737`; `tests/test_page_types.py:862-881` |
| Header block: schedule beside city name, units beside period line | newer, shown for FY24 | `tests/test_page_types.py:838-860` |
| "Exhibit" locator instead of "Schedule" for summaries | FY10 | `tests/test_page_types.py:883-900` |
| Several independent statements stacked on one physical page | "older reports"; editions not named | `page_types.yml:771-773` |
| Title "Summary Statement of Current Year Appropriation Activity by Fund" beside the plain form | not named | `page_types.yml:710`; `tests/test_page_types.py:815-821` |
| Title "Net Revenue" against "Net Revenues" | FY24 prints "Net Revenue" | `page_types.yml:695-698`; test_page_types.py:845 |
| Grand total "Total Net Revenues" (FY10) against "Total Net Revenue" (FY15) | FY10, FY15 | yml:285, 499 |
| FAMIS and "Fd BAL/AP Adjs" columns in activity tables (9 money columns) | FY21 Water Fund; other editions unknown | `semantics.yml:577-582`; CASES.md:45; yml:61-83 |
| Hyphen printed as U+2010 with spaces ("Non (U+2010) Tax", "Sub (U+2010) Total") | FY21 | `tests/test_supplemental_source_acknowledgments.py:219,222` |
| Schedule letters move: Water is I-O in FY10, I-N in FY21 | FY10, FY21 | yml:80, 418 |
| Agency row identity required from FY2025 only | FY2025 onward (no edition yet parsed) | `page_types.yml:752-756` |

The six statement types and their column sets appear in every edition the config mentions. No
record shows a column added or removed outside the FAMIS case. Not verified: the full era map,
since no rule in the config is pinned to a year range except identity.

## 4. Finding the table

Today, in four steps:

1. Page typing by printed title. The profile has no marker codes; the marker pattern is a
   sentinel that never matches (`page_types.yml:685`). Each page is typed by the first declared
   `title_pattern` found on any line, case-insensitive (`page_types.py:1145-1149`,
   `:1171-1184`). Untitled pages default to `evidence_only` and never stitch
   (`page_types.yml:723`). So a continuation page that lost its title would be dropped.
2. Context from header lines: reporting entity, schedule or exhibit, statement title, period,
   unit basis, fund (`page_types.yml:724-747`). Stitching partitions by fund
   (`page_types.yml:748-750`); a page missing its fund gets a page-local key and stitches with
   nothing (`page_types.py:1241-1247`).
3. Repairs: drop furniture lines (`page_types.yml:758-770`), split stacked statements into
   zones by title (`:774-791`), rebuild agency and fund by class pages from drawn vertical rules
   (`:813-818`; `tables/rule_grid.py:820`).
4. Region detection by whitespace column consensus, widened to bridge two incompatible lines
   for this family (`layouts/supplemental-report.yml:961`; `parsers/geometric_backend.py:1025-1027`).

Simplest reliable rule: the statement title on the page names the table, and the fund banner on
the next line names the fund. The table body runs from the column header to the next statement
title, the "NOTE:" line or the page footer. Consecutive pages with the same (title, fund)
continue one table. Activity tables draw a full rule grid, so columns can come from the rules or
from fixed header positions. No page or table classifier is needed, and no LLM step.

## 5. Arithmetic that holds

| Relation | Tables | Source breaks it |
|---|---|---|
| Class rows sum to agency subtotal, per column | agency by class | 3 acks (FY22, FY23 MOCS; FY23 Revenue) |
| Agency subtotals sum to fund "Totals" | agency by class | 1 ack (FY21 Water, see Q30) |
| Class rows sum to fund total | fund by class | 0 acks |
| Encumbrances + Expenditures = Total Obligations, per row | activity | broken inside FY22, FY23 MOCS and FY23 Revenue subtotals |
| Total Obligations + Unencumbered Balance = Final Appropriations | activity | holds even in FY23 Revenue subtotal (yml:239-240) |
| Percent = 100 x Total Obligations / Final Appropriations, 2 decimals | activity | inferred by code at four-fifths agreement (`tables/reconciliation_columns.py:107-120`); not acked |
| Final = Original + adjustments, when the adjustment column exists | activity, FAMIS era | FY21 Water: 9,158.34 gap with blank adjustment (yml:70-73) |
| Funds sum to group totals and "Total Operating Funds" | summary activity | 1 ack (FY20 Grants original excluded) |
| Source rows sum to department Sub-Total, Sub-Totals to category total, categories to Total Net Revenues | revenues | 4 acks on additive columns (FY20 p23; FY20, FY23, FY24 p53 prior actual) |
| Increase (Decrease) = Actual minus Prior Year Actual, per row | revenues | 20 of 21 revenue acks involve this column |
| Percent Collected = Actual / Final Budget Estimate | revenues | not checked by the old code; not verified |
| Summary fund row equals that fund's statement total | summary vs detail | never checked; no cross-table rule names this family (`reconciliation.yml`, `resolved_assertions.yml`) |
| Edition N prior actual equals edition N-1 actual | revenues | never checked. Holds in 3 cases readable from acks: FY21 to FY22 Other Governments 1,207,741,264.06; Grants LGNT FY20 to FY21 47,651,915.36 and FY21 to FY22 64,213,937.30 |

The Increase column is the weakest. Grants Revenue I-I-1 breaks it in FY20, FY21, FY22, FY23
and FY24, on Sub-Totals, local non-tax totals and the Other Governments grand total.

Acknowledgments for this family's six tables: 26 of the 32 in the layout file. The other six
are capital (4) and prior years' encumbrances (2, FY03 and FY20 p32).

| Kind | Count | Records (edition, page) |
|---|---|---|
| Printed change column disagrees with Actual minus Prior Actual or with contributor changes | 17 | FY10 p21, p22, p24 x2, p77 x2; FY15 p59; FY20 p51 x2, p52; FY21 p49 x2, p51; FY22 p49, p51; FY24 p51, p52 |
| Prior actual grand total disagrees with rows, plus change column | 3 | FY20, FY23, FY24 p53 |
| Printed total exceeds displayed contributors | 1 | FY20 p23, +2,000,000 original and final |
| Subtotal prints a dash where its sole contributor has a value | 2 | FY22, FY23 p25 |
| Subtotal with incompatible bases | 1 | FY23 p57 |
| Grand total wider than retained contributors, missing adjustment | 1 | FY21 p76 |
| Group total excludes a self-balancing fund in one column | 1 | FY20 p12 |

By table: revenues 21, agency by class 4, summary activity 1; fund by class, summary revenues and
revenues by source 0. By edition: FY10 6, FY15 1, FY20 6, FY21 4, FY22 3, FY23 3, FY24 3; FY03,
FY04, FY05 none. Only 8 of the 26 carry evidence and check fingerprints; the root sets fingerprint
migration to false (`config/layouts.yml:4-5`). Not verified: whether tables with no ack fully
reconcile today, because no artifacts exist.

## 6. Row labels and entities

Agencies. 81 entity ids list `phila_supplemental_report_*`; all are `department` dimension and
none is specific to this family (parsed from `config/entities.yml`). All 81 also list
`budget_in_brief_*`. 79 also list a QCMR family; Civic Center and Tax Reform Commission list only
Budget in Brief and the supplemental report. 75 also list budget detail. Old agency names fold
into current entities by alias with no succession record: "Mayor's Office of Community Services"
resolves to the Community Empowerment and Opportunity entity, "Mayor's Office of Information
Services" to Innovation and Technology. The registry has only 2 successions, one Philadelphia
merger (Fairmount Park plus Recreation, FY2011; `entities.yml:4709-4716`). One qualifier rule
makes "Personal Services" a class under the running section for this family
(`entities.yml:4679-4682`). Row identity is required only from FY2025
(`page_types.yml:752-756`), which the comment calls legacy identity debt. So FY03 to FY24 agency
labels are not all resolved. The number of distinct labels is not in the checkout.

Classes. Philadelphia's major object classes are 100, 200, 300, 400, 500, 700, 800, 900
(`audit.yml:43`). Class 100 can split into "a) Personal Services" and "b) Employee Benefits"
(`audit.yml:44-46`). Not verified whether supplemental class labels print the code.

Funds. Fund banners resolve through `config/funds.yml` (17 funds, written for budget detail).
Aliases there include "Communtiy Development Fund", a source misspelling (`funds.yml:41`;
`tests/test_audit.py:1124-1133`). Only `audit.py:432-449` resolves supplemental funds. I found
no path that gives published supplemental rows a canonical fund id; they carry the printed
banner. The registry lacks the capital funds and "Industrial & Commercial Development Fund".

Revenue source labels (Real Property Taxes, Gas Works Rental and so on) have no entity entries
for this family.

Relation to QCMR and Budget in Brief. The supplemental report is the audited year-end record of
the same departments, at department by class by fund grain, in dollars and cents.

| Family and table | Grain | Nearest supplemental table | Notes |
|---|---|---|---|
| Budget in Brief `general_fund_obligation_history` | General Fund department, Actual for earlier years | General Fund agency by class subtotals, Total Obligations | thousands, whole dollars in FY26 (`semantics.yml` Budget in Brief profiles) |
| Budget in Brief `operating_fund_summary` | fund, with an Actual column | summary activity, Total Obligations | thousands |
| Budget in Brief `operating_revenue_schedule` | revenue source, Actual | revenues by source, summary revenues | thousands |
| QCMR obligations (O-2) | General Fund department by class, quarterly | General Fund agency by class | Q4 is preliminary; no check exists |

No check ties the supplemental report to QCMR or Budget in Brief today. The audit's
organization folds show the grain traps: Finance sub-entities, Aviation in fund 9 against
Commerce, City Representative in fund 7, Housing and Community Development and Sinking Fund in
fund 12, Finance holding class 100 benefits centrally (`audit.yml:48-108`).

## 7. Values

- Units: "(Amounts in USD)", multiplier 1, two decimals (`semantics.yml:632-646`). Capital and
  appropriation figures are whole dollars in print but share the unit.
- Negatives: parentheses, "(745.35)", "(82,771.67)" (yml:446, 839).
- Dash: no value. Published as null, never zero (CASES.md:27,44). The old lexer reads a lone
  dash as 0.0 for grid finding and gates it later (`tables/amounts.py:91-99`).
- Fused dashes "- -" in FY21 FAMIS cells (`docs/analysis-readiness-0.4.1-status.md:113-114`).
- Percents: bare "74.98" in some activity tables and the by-source table, "%"-suffixed
  elsewhere (yml:2-5; `semantics.yml:649-652`). They must never enter a vertical sum.
- Page footer "- 12 -" and repeated header lines appear inside bodies (`page_types.yml:758-766`).
- Kerning: a trailing decimal digit can split off ("67,215,504.0 0") (`tables/amounts.py:70-76`).
  Not tied to an edition.
- Blank ruled cells are left absent, not marked as blanks (`page_types.yml:815,818`).

## 8. Editions and revisions

Each edition reports one fiscal year of activity. Revenue statements also print the prior year's
actual, so FY N's prior actual overlaps FY N-1's actual. Only FY03 to FY05 and FY20 to FY24 are
consecutive. The FY24 Grants statement repeats the FY23 duplicated prior figure
(yml:211-214). No edition-selection rule exists for this family: no semantics profile picks a
canonical vintage, and the old reader keeps both observations with their `document_id`. No
corrected reissue or reused URL is recorded. Acquisition details are out of scope here.

Against later budget books, FY2020 has six reviewed cell differences, including Water class 800
original appropriation printed as 74,000,000 against 69,000,000 in the FY2021 book
(`audit.yml:142-249`). That comparison stays in gov-budget-data.

## 9. Quirk ledger

| Id | What happens in the document | Old handling | Kind |
|---|---|---|---|
| SUPOP-Q01 | No form code; the printed statement title is the only table identifier. Case varies (caps in FY05). | `page_types.yml:685-722`; `page_types.py:1171-1184` | inherent |
| SUPOP-Q02 | Title variants: "Net Revenue" or "Net Revenues"; "Current Year" inserted in the summary activity title. | `page_types.yml:695-698,710`; `tests/test_page_types.py:811-836` | inherent |
| SUPOP-Q03 | Older editions stack several statements on one page. | `page_types.yml:771-786` (split_zones) | inherent; editions unsure (check FY03 to FY05 pages) |
| SUPOP-Q04 | Activity pages can append a "NOTE:" block of non-budgeted obligations with its own total. | `page_types.yml:787-791,819-823`; `semantics.yml:3981-3986` | inherent |
| SUPOP-Q05 | Prior years' encumbrance statements sit beside in-scope tables; single-agency ones print no total. | `page_types.yml:699-704`; `semantics.yml:3973-3980` | inherent |
| SUPOP-Q06 | Fund is a banner line under "City of Philadelphia"; names end in "Fund"; summary pages print "Operating Funds" instead. | `page_types.yml:738-742,748-750,797-812` | inherent |
| SUPOP-Q07 | Single-agency funds (HealthChoices Behavioral Health, Water Residual) print no agency banner. | `page_types.yml:743-747` | inherent |
| SUPOP-Q08 | Header block layout differs by era; FY10 summaries use "Exhibit". | `page_types.yml:730-737` | inherent |
| SUPOP-Q09 | Schedule letters are not stable across editions. | none (not used as a key) | inherent |
| SUPOP-Q10 | Agencies are colon-ended section banners; subtotals read "Subtotal <Agency>:". | `page_types.yml:679-681,751`; generic section logic | inherent |
| SUPOP-Q11 | Column header spans lines; "Percent of" prints alone and welds onto the first agency banner. | `page_types.yml:767-770` (furniture drop) | inherent (multi-line header); weld is artifact of line grouping |
| SUPOP-Q12 | Utilization or collection percent printed bare on some tables, suffixed on others. | `layouts/supplemental-report.yml:962-968`; `layouts.py:1040-1053`; `tables/reconciliation_columns.py:69-104,1010-1037` | inherent |
| SUPOP-Q13 | Short single-agency tables: whitespace detection fuses the percent into Unencumbered Balance ("110,626,142.01 92.31"). | `page_types.yml:792-796,813-818` (rebin_ruled_grid); `semantics.yml:605-612` (optional_roles) | artifact of whitespace column detection |
| SUPOP-Q14 | Roles assigned right to left; a missing percent column shifts every role ("the Police lesson"). | `semantics.yml:583-590` | artifact of positional role mapping |
| SUPOP-Q15 | FAMIS and "Fd BAL/AP Adjs" columns make 9 numeric columns; FAMIS has no mapped meaning. | `semantics.yml:577-582`; CASES.md:45 | unsure: which editions print them (check each activity header) |
| SUPOP-Q16 | Indented class 100 detail lines under the class row are not additive. | `audit.py:705-708`; `audit.yml:44-46` | inherent; label format unsure |
| SUPOP-Q17 | A small agency prints one amount row with no classes. | `audit.py:723-731` | inherent |
| SUPOP-Q18 | Revenue Sub-Total label sits on the last item's baseline; its amounts print a line below. | `tables/line_repair.py:101`; `tables/row_repairs.py:1138-1206`; `tables/reconciliation_trials.py:236-262`; `tests/test_table_primitives.py:1464-1491` | inherent |
| SUPOP-Q19 | Text layer drops spaces ("PublicHealthSub-Total"). | `tables/row_repairs.py:1179-1184` | unsure: edition not named |
| SUPOP-Q20 | Parent banners repeat on continuation pages; a later Sub-Total closes the whole parent. | `tables/totals.py:1370-1428`; 6 acks name `items_since_continued_section_r*` | inherent |
| SUPOP-Q21 | Some hierarchy is shown only by bold type (FY10 Water). | `tables/totals.py:1846-1872`; yml:433 | inherent |
| SUPOP-Q22 | Two value-less banners in a row (category then department) between money rows. | `layouts/supplemental-report.yml:911-915,961`; `parsers/geometric_backend.py:1025-1027`; `tables/region_detection.py:278-284` | artifact of column-consensus region detection |
| SUPOP-Q23 | An all-dash department Sub-Total sits under live rows of the previous section. | `tables/totals.py:555-574`; `tests/test_classification_total_scopes.py:2594-2625` | inherent (scope is the named section) |
| SUPOP-Q24 | Dash means no value; dash on a total with valued contributors is a source fault. | `tables/amounts.py:91-99`; CASES.md:27,44 | inherent |
| SUPOP-Q25 | Increase (Decrease) is unnumbered and derived; the source breaks it 20 times. | `tables/column_identities.py:262-280`; 20 acks | inherent |
| SUPOP-Q26 | FY23 and FY24 Grants print 6,895,171.96 prior actual on two departments. | yml:161-223 | inherent |
| SUPOP-Q27 | FY20 Total Special Revenue Funds omits Grants Revenue's original appropriation only. | yml:313-346 | inherent; other editions unsure |
| SUPOP-Q28 | FY22 and FY23 MOCS subtotal prints a dash for encumbrances its sole row has. | yml:84-129 | inherent |
| SUPOP-Q29 | FY23 Grants Revenue subtotal mixes bases across columns. | yml:224-256 | inherent |
| SUPOP-Q30 | FY21 Water "Totals": FAMIS residual 365,040,550.73 and a 9,158.34 Final below Original with blank adjustment. | yml:55-83 | unsure: the FAMIS residual may be lost cross-page scope (render p75-76) |
| SUPOP-Q31 | FY20 Other Funds total exceeds its rows by exactly 2,000,000 in two columns. | yml:347-376 | inherent |
| SUPOP-Q32 | FY21 prints hyphens as U+2010 with spaces in labels. | `layouts.py:33-35` (label normalization); test lines 219, 222 | inherent |
| SUPOP-Q33 | Grand total label differs: "Total Net Revenue" and "Total Net Revenues". | yml:285, 499 | inherent |
| SUPOP-Q34 | Fund banner misspelled "Communtiy Development Fund". | `funds.yml:41` | inherent; edition unsure |
| SUPOP-Q35 | Page footers "- N -" and header lines leak into bodies. | `page_types.yml:758-766` | inherent |
| SUPOP-Q36 | Revenue period covers two years, so prior actual overlaps the previous edition. | `page_types.yml:732` | inherent |
| SUPOP-Q37 | PDF page differs from printed page by 8 in FY20 and FY23. | none | inherent |
| SUPOP-Q38 | Editions exist only for 10 milestone years. | none | inherent |
| SUPOP-Q39 | Agency names change across eras (MOCS, MOIS, Office of Housing). | aliases in `entities.yml` | inherent |
| SUPOP-Q40 | FY03 to FY24 agency rows are not all resolvable to an entity. | `page_types.yml:752-756` | unsure: count needs the parsed labels |
| SUPOP-Q41 | Acks keyed to table and row ordinals and to hypothesis names holding row numbers; FY10 rows moved 435 to 427. | `layouts.py:325-346`; `tests/test_supplemental_source_acknowledgments.py:283-345` | artifact of stitched ordinal coordinates |
| SUPOP-Q42 | 18 of 26 acks lack fingerprints, so a release-ready gate would fail. | `config/layouts.yml:4-5`; `layouts.py:1354-1371` | artifact of a half-done migration |
| SUPOP-Q43 | A comment about the region bridge sits inside an ack, 50 lines from its key. | yml:911-915 | artifact of the round-trip YAML writer |
| SUPOP-Q44 | The bridge option is documented as unsafe for stacked tables, yet this family stacks older pages. | `layouts.py:1063-1072` against `page_types.yml:771-773` | unsure: check whether stacked pages share columns |
| SUPOP-Q45 | Percent of Obligations is mapped to `unknown` and not a published measure. | `semantics.yml:597-600,630-631` | unsure: product choice, not a document fact |
| SUPOP-Q46 | FY2020 cells differ from the FY2021 book (Water class 800, 74m against 69m). | `audit.yml:142-249` | inherent (out-of-scope check) |

Not in this ledger: `exclude_reporting_period_from_subtotals` (capital summary only,
yml:8-9; `tables/reconciliation_periods.py`). The capital dossier owns it.

## 10. Old code that serves this family

| Job | Files (lines) | Keep as code or as knowledge |
|---|---|---|
| Page typing and context | `page_types.yml:676-823` (148); `page_types.py` (1,342, shared); `page_classification_stage.py` (312) | Knowledge: the title regexes and header patterns. Code too general. |
| Layout options | `layouts/supplemental-report.yml` (970, of which about 945 are acks); `layouts.py:1000-1073` | Knowledge: the 26 reviewed source faults, re-keyed. |
| Region and grid | `parsers/geometric_backend.py:1025-1027`; `tables/region_detection.py` (644); `tables/rule_grid.py` (1,366); `tables/repairs.py` (168) | Knowledge: rule-grid binning is right for activity pages. |
| Row repairs | `tables/row_repairs.py:1138-1206`; `tables/reconciliation_trials.py:236-262`; `tables/line_repair.py:101` | Knowledge: the label-above-amounts shape. |
| Totals search | `tables/totals.py` (2,907; continued parent, bold parent, vacuous zero); `tables/column_identities.py:262-280`; `tables/reconciliation_identities.py:404-421`; `tables/reconciliation_columns.py:69-104,1010-1037` | Knowledge only. Declared sums replace the search. |
| Semantics | `semantics.yml:576-698,3973-3986` (about 140) | Knowledge: the column names and roles. |
| Identity | `entities.yml` (81 shared entries); `funds.yml` (96); `funds.py` (319) | `resolve_fund` logic is worth keeping in spirit. |
| Cross-publication audit | `audit.py` (2,236); `audit.yml` (249) | Stays in gov-budget-data. Knowledge: folds and grain traps. |
| Readiness | `readiness.yml:20-24` | Knowledge: operating scope excludes capital. |
| Tests | `tests/test_supplemental_source_acknowledgments.py` (359); `tests/test_page_types.py` cases at 811-900, 1004-1011, 1345-1359; `tests/test_audit.py`; `tests/test_classification_total_scopes.py:2594-2625`; `tests/test_table_primitives.py:1464-1491` | Knowledge: real labels, residuals and page numbers become fixtures. |

What leaving the audit out costs. The audit is the only check that ties this family to another
publication: original appropriations and actual obligations against adopted budget books
(`audit.yml:9-38`). With budget detail out of scope, the new repo has no outside check on these
numbers. The in-scope substitutes are Budget in Brief actual columns (section 6), which no code
tries today. Its lessons still apply: organization folds by fund and year, Finance's central
class 100, grants at a different grain (`audit.yml:48-108`).

## 11. The least a parser needs

Inputs: the edition PDF (text layer), its fiscal year, and the declared statement list.

1. For each page, read the title line and the fund line. Skip pages whose title is not one of
   the six statements. Cut "NOTE:" blocks and encumbrance statements out of mixed pages.
2. Group pages into tables by (title, fund), in page order.
3. Find columns: activity tables from drawn rules or the fixed header; revenue tables from the
   header. Bind columns by caption, never by position from the right. Treat FAMIS and adjustment
   columns as optional named columns.
4. Read rows: label, values, bold flag, page. Join a total label printed above its amounts.
   Drop footer and repeated header lines. Normalize hyphen variants in labels.
5. Classify rows by label shape: colon banner, "Subtotal X:", "Sub-Total", "Total ...",
   "Totals", plain item. Track category and department sections, including repeats across pages.
6. Parse values: dollars and cents, parentheses negative, dash as null, percent as its own
   field.
7. Declare checks per table:
   - item rows sum to their section subtotal; subtotals to category totals; totals to the grand row;
   - Encumbrances + Expenditures = Total Obligations; Total Obligations + Unencumbered = Final;
   - Increase = Actual minus Prior Actual (expect acknowledgments, mostly Grants I-I-1);
   - percent = rounded ratio, checked apart from sums;
   - summary fund rows equal each fund statement's total (new, unproven);
   - edition N prior actual equals edition N-1 actual where both exist (new, unproven).
8. Attach acknowledgments by (edition hash, page, row label, column name, residual).
   Port the 26 reviewed faults on that key.

Parameters that differ by era: header block shape, title wording, grand total label, presence
of FAMIS and adjustment columns, stacked pages in older editions, hyphen glyph.

Hardest table: `supplemental_revenues`. It has the deepest hierarchy, multi-page parent
sections, welded subtotal labels, and 21 of the 26 acknowledgments.

## 12. Unknowns

- Which editions print FAMIS and adjustment columns, and what FAMIS means for publication.
- Which editions stack statements on one page, and whether those statements share columns.
- Whether any edition lacks a usable text layer; which edition has the "decayed" layer.
- Whether supplemental class labels print class codes, and how class 100 detail lines read.
- Distinct agency and revenue labels per edition, and how many fail entity resolution.
- Whether tables without acknowledgments reconcile fully today (no artifacts).
- Whether summary rows equal fund statement totals, and whether prior actuals carry forward
  across all consecutive editions.
- Whether FY20's Grants exclusion from Special Revenue totals recurs in other editions.
- Whether the FY21 Water FAMIS residual is a source fault or lost cross-page scope.
- Page counts per edition and the full schedule map.
- The FY2025 edition's layout; identity rules switch on there.
