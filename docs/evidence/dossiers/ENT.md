# ENT: Row identity and entities across all families

Scope: the four QCMR tables, monthly City and School collections, the five tax detail families, Budget in Brief and the supplemental reports. Out of scope families (budget detail, Five Year Plan, PA General Fund) appear only where they share entities with these.

Evidence is config, code, tests, release notes and docs at commit 49b59ea. Counts come from loading `config/entities.yml` with the repo's own `normalize_entity_label`; the scripts are in `/home/claude/scratch/v2/ent_tools/`. Paths drop `packages/gov-budget-etl/src/gov_budget_etl/`. No PDF and no resolved artifact was available, so nothing here is checked against a printed page.

This dossier replaces template sections 1 to 8 with the six questions asked. Sections 9 to 12 keep their template numbers.

## 1. Kinds of row identity

There are about ten kinds of row identity, and only departments, funds and expenditure classes have an official code. Everything else is identified by its printed label inside one table.

`config/entities.yml` holds 474 entities in eight dimensions (`entities.py:41-51`). 409 touch an in-scope family. 405 touch QCMR or collections. 4 more touch only Budget in Brief or the supplemental report, such as Civic Center. The other 65 serve PA and budget detail only. Every entity is scoped to families by fnmatch patterns on document ids; none is global.

| Kind | Entities in scope | Families that use it | Printed variants (name plus aliases) | Most variants on one entity | Official code |
|---|---|---|---|---|---|
| Department or agency | 99 (78 top level, 21 children with `parent_id`) | positions 71, obligations 93, personal services 72, Budget in Brief 99, supplemental 81, monthly City 4 | 394 (355 after normalization) | 17, Office of Behavioral Health | department number for 60 of 99 (`entities.yml:4441-4506`) |
| Sub-department appropriation line | 10 (`other` dimension) | obligations 10, Budget in Brief 6, personal services 1 | 20 | 3 | none |
| Fund | 16 in `entities.yml` (11 cash, 5 City) plus 17 in `config/funds.yml` | QCMR cash, monthly City, Budget in Brief (through `funds.yml`) | 38 in `entities.yml`; `funds.yml` adds 36 aliases | 4 | fund code in `funds.yml` with `code_history` |
| Tax or revenue line | 72 (36 tax, 36 revenue category) | monthly City 45, monthly School 8, QCMR cash 18, sales tax 1 | 213 | 13, cash "Collection of Prior Year(s) Revenue" | none |
| Industry or sector | 113 (57 industry, 56 sub-industry) | wage industry and residency share 52, BIRT 34, sales tax 27 | 137 | 3 | none found |
| RTT classification | 38 plus 6 RTT rollups | realty transfer tax | 67 | 4 | legacy class codes in labels, such as "(88-2)" |
| Expenditure class | 10 in QCMR cash; 10 class labels as Budget in Brief qualifiers; supplemental class rows unresolved | QCMR cash, Budget in Brief, supplemental, personal services ("Class 100") | 35 for cash; Budget in Brief labels never merged | 6 | major class codes 100 to 900 (`config/audit.yml:40-46`), not in the entity registry |
| Cash-flow line | 10 (5 revenue category, 5 rollup: opening, closing, TRAN, excess, current year appropriation) | QCMR cash | 34 | 5 | none |
| Capital project or category | 0 | supplemental capital tables only | not resolved | n/a | none known |
| Reporting unit (total, subtotal, combined scope) | 38 rollups plus 2 combined-scope organizations | every family | 122 | 17, sales tax FAMIS comparator | none |

Notes on the table:

- 66 of the 658 in-scope aliases normalize to the entity's own name and do nothing. About 169 are a strict prefix of another label on the same entity, which is column-edge truncation. 16 carry a fused line number ("24 First Judicial District", "I Records"). 5 carry a fused banner or class text. The rest are renames, spelling, total forms and OCR damage, which a heuristic cannot separate (`ent_tools/a6.py`).
- Expenditure classes are filed under the `revenue_category` dimension (`entities.yml:2008-2010`). The dimension list has no class or cash-flow type (`entities.py:41-51`).
- Scoped aliases add 11 edition-bound labels (`entities.yml:4507-4587`). Qualifier rules add 47 labels in 15 rules (`entities.yml:4588-4708`).
- Budget in Brief revenue schedule and fund summary rows, and supplemental revenue, fund and capital rows, carry no subject entity at all. Their identity today is the printed label plus page context (fund, agency banner, schedule id).

## 2. The same real thing in several families

A shared id already exists for departments, and it works because one entity lists every family. Taxes, funds and industries do not share ids: one real tax or fund has two to four ids.

### Departments

58 department entities list all of Budget in Brief, budget detail, QCMR obligations, positions, personal services and the supplemental report. 4 more add monthly City collections. The row grain differs by family.

| Family | Where the department sits | Grain |
|---|---|---|
| QCMR positions | row label | all funds, by fund column |
| QCMR obligations | row label | General Fund only |
| QCMR personal services | section heading over three metric rows | General Fund, class 100 |
| Budget in Brief obligation history | running section heading; rows are classes | General Fund |
| Budget in Brief revenue schedule | bold agency banner inside a fund schedule | one fund |
| Supplemental agency by class | section heading ending in ":" | one fund per page |
| Monthly City collections | row label HEALTH, SHERIFF, RECORDS, STREETS | revenue collected, not spending |

A shared department id is possible and worth keeping. It is the join users ask for, and the old repo already enforces one department label to one id per jurisdiction (`entities.py:520-531`). But it identifies the organization, not a comparable series.

- Obligations is General Fund; positions is all funds; the supplemental report is per fund.
- Child lines differ: obligations prints Finance-Indemnities and reserves beside Finance (`entities.yml:3266-3269`); Budget in Brief prints retired units at zero beside the parent (`entities.yml:2610-2614`).
- One agreement is recorded by hand. The FY26 QCMR "Office of Public Safety-Base" equals the Budget in Brief total (`entities.yml:2562-2563`). No check encodes it.
- Comparing the supplemental report with budget detail needed 23 rollups, 1 dated fold and 4 fund-scoped folds (`config/audit.yml:47-97`). Any cross-family department check will need the same kind of folds.

The department list is also shared with budget detail, which stays in gov-budget-data. One repo must own it.

### Taxes and revenue lines

One tax has up to four ids, and Budget in Brief has none.

| Tax | Monthly City | Monthly School | QCMR cash | Tax detail report | Budget in Brief revenue schedule |
|---|---|---|---|---|---|
| Real Estate Tax | `phl_real_estate_tax` | `phl_school_real_estate` | `phl_cash_real_estate_tax` | none | label only |
| BIRT | `phl_birt` | none | `phl_cash_birt` | `phl_birt_sector_total` | label only |
| Sales Tax | `phl_sales_tax` | none | `phl_cash_sales_tax` | `phl_total_sales_tax`, `phl_sales_tax_famis` | label only |
| Realty Transfer | `phl_real_estate_transfer_tax` | none | `phl_cash_realty_transfer` | `phl_rtt_total_records` | label only |
| Wage, Earnings, Net Profits | 6 city and PICA ids plus 3 combined rollups | `phl_school_income_tax` is a different tax | `phl_cash_wage_earnings_np` and gross | `phl_wage_tax_industry_total` | label only |

A shared tax id is possible: the list of real taxes is about 25 and stable. It is worth it only as a concept link, not as a series key. The bases differ. Collections are monthly cash receipts and QCMR cash is a cash-flow projection. Budget in Brief is budget and estimate. The sector reports are annual with two totals of their own (`entities.yml:3365-3372`). No check in the repo compares a tax across families. Naming the concept costs little and lets a reader find every series for one tax.

### Funds

Funds have three identity systems, and the General Fund has four ids.

| Fund | `funds.yml` | QCMR cash entity | Monthly City entity | Other |
|---|---|---|---|---|
| General | `phl_fund_general` | `phl_cash_fund_general` | none | `phl_general_fund` (rollup, City and Budget in Brief); `phl_obligations_general_fund_total` (rollup, obligations) |
| Grants Revenue | `phl_fund_grants_revenue` | `phl_cash_fund_grants` | `phl_grants_revenue` | |
| Community Development | `phl_fund_community_development` | `phl_cash_fund_community_dev` | `phl_community_development` | |
| Acute Care Hospital | `phl_fund_acute_care_hospital` | `phl_cash_fund_hospital_assessment` | `phl_acute_care_assessment` | |
| Housing Trust, Budget Stabilization, Transportation | one each | one each | none | |
| Capital Improvement | none | `phl_cash_fund_capital_improvement` | `phl_capital_improvement` | |

`funds.yml` is read only by budget detail gold and the Budget in Brief assertions (`funds.py` callers: `gold_funds.py:56`, `resolved_assertions.py:733-755`). A shared fund id is possible because funds have official codes, and it is clearly worth it. The row meaning still differs. A QCMR cash fund row is a cash balance. A City collections fund row is revenue into the fund. A Budget in Brief fund is page context.

### Industries

Wage tax by industry and by residency share one hierarchy, 52 entities, which is right: it is one taxonomy (`entities.yml:3355-3359`). BIRT, sales tax and wage tax use different sector lists. 14 sector names repeat across them, such as "Construction" and "Insurance". The lists still differ: wage tax has "Transportation and Warehousing", BIRT has "Transportation and Storage". No NAICS codes were found in config. A shared id across these taxonomies is not supported by the evidence.

### Expenditure classes

Classes appear in four places:

- QCMR cash: Payroll, Employee Benefits, Pension, Purchase of Services and six more.
- Budget in Brief obligation history: Personal Services, Pers. Svcs.-Emp.Benefits and eight more.
- Supplemental agency and fund statements: rows such as "900 Advances and Other Miscellaneous Payments" (`tests/test_resolution.py:3419-3440`).
- Personal services: "Class 100 Total Oblig./Approp."

 The City's major class codes are 100, 200, 300, 400, 500, 700, 800 and 900 (`audit.yml:40-46`). A class id with the code is worth having for Budget in Brief and the supplemental report. QCMR cash does not map one to one: it splits class 100 into payroll, benefits and pension.

## 3. Renames, merges, splits and reorganizations recorded

Organizational change is recorded in six different places, and only one of them has the shape of an event. Most renames are undated aliases.

| What | Where recorded | Date | Kind |
|---|---|---|---|
| Fairmount Park and Recreation merge into Parks and Recreation | `entities.yml:4710-4719` succession, with a value check (12.6M + 33.6M, then 49.8M) | effective FY2011 | merger event |
| PA Public Welfare renamed Human Services | `entities.yml:4720-4730` | FY2016 | out of scope |
| Department number 66: Office of Education, then Office of Children and Families, then Education again | `entities.yml:4492-4494` code validity | to FY2020; FY2021 to FY2024; from FY2025 | dated code |
| Same seam as a comparison fold | `audit.yml:74-79` | FY2020 to FY2024 | fold |
| Fund code 15: Budget Stabilization, later Demolition; Budget Stabilization becomes 01-011 | `funds.yml:59-74` | 15 to FY2020; 01-011 from FY2021; Demolition 15 from FY2023 | dated code |
| "Streets" means the department, then Streets including Sanitation | `entities.yml:1545-1565` edition patterns | department FY08 to FY13 and FY26; combined FY18 to FY25 (positions) | edition scope |
| Sanitation printed as its own department in personal services | `config/layouts/qcmr-personal-services.yml:2-8` | FY08 to FY13 | layout comment |
| Retired Office of Planning and Development printed beside new code-72 Planning & Development | `entities.yml:1302-1305` | FY18 | two entities, no event |
| Office of Prison Oversight established from Office of Public Safety | `entities.yml:2576-2579` | FY2026 | comment |
| OPS-* sub-blocks under Office of Public Safety | `qcmr-personal-services.yml:108-111` | FY26 | layout comment |
| FY21 personal services prints "Office of Children & Families / Human Services" | `entities.yml:937-938` | FY21 | alias of Human Services |
| Housing and Community Development reported under Planning & Development in fund 12; City Representative under Commerce in fund 7; Aviation under Commerce in fund 9; Sinking Fund Commission under P&D in fund 12 | `audit.yml:81-97` | undated except the FY2020 note | fund-scoped fold |
| 23 child lines and Recreation, Fairmount Park, Community Schools and Pre-K folded into parents | `audit.yml:47-70` | undated | fold |
| RTT 2024 apartment and condominium splits kept apart from legacy classes | `entities.yml:3886-3890` | 2024 | deliberately no event |
| Wage tax database total renamed PRISM, PRISM/TIPS, TIPS | `entities.yml:3369-3372` | undated | aliases |

Renames carried only as undated aliases include:

- Business Privilege Tax to BIRT (`entities.yml:1807`), and Sweetened Beverage Tax;
- Mayor's Office of Community Services to Community Empowerment and Opportunity;
- Emergency Shelter Services and Supportive Housing to Homeless Services;
- Division of Technology and Information Services to Innovation and Technology;
- Personnel to Human Resources; Fleet Services and Fleet Management;
- Creative Philadelphia and Arts and Culture; BH/MR to Behavioral Health;
- Office of Community Development to Housing and Community Development.

None has a date. The registry cannot say which name was printed in which year.

## 4. How labels are matched today, and how it went wrong

Matching is exact on a normalized label inside a scope, with "one candidate or nothing", and failure is silent.

### The mechanism

1. `normalize_entity_label` removes `(cid:N)` glyphs, trailing comma-grouped amounts, single-digit edge markers and `(N)` references, casefolds, turns `&` into "and" and drops punctuation (`entities.py:78-98`). Two-digit bare prefixes stay ("10 COMMUNITY DEVELOPMENT").
2. The resolver keeps entities whose `families` patterns match the document id (`entities.py:885-898`), then filters by optional `table_types` and `row_kinds` (`entities.py:986-1003`).
3. A scoped alias bound to an edition outranks ordinary aliases (`entities.py:981-984`).
4. It returns an id only if exactly one candidate survives (`entities.py:1004`). Unknown and ambiguous both become null (`resolution.py:483-484`).
5. The resolve stage joins ids on (label, table_type, row_kind) (`resolution.py:556-567`), then applies qualifier rules (`resolution.py:594-600`, 1714-2019). A qualifier row takes its parent's id and records `entity_qualifier` (`resolution.py:2015`).
6. Sub-industry rows read as line items are relabelled component from the catalog dimension (`resolution.py:887-920`).
7. Organization (`org_entity_id`) comes from page context for Budget in Brief and the supplemental report (`config/page_types.yml:545-549, 751`), and from the entity's parent otherwise (`resolution.py:1277-1365`). Organization lookup ignores family scope and searches the whole jurisdiction (`entities.py:1115-1138`).
8. Funds go through a separate registry: scope patterns first ("All Funds", "General/Grants Revenue"), then name, then code by fiscal year (`funds.py:256-303`).

Semantic profiles (68 in `config/semantics.yml`) do not match row labels. They assign column roles. Row identity lives entirely in `entities.yml`, the qualifier rules, page-type context fields and `funds.yml`.

### What went wrong, with evidence

| Defect or incident | Evidence | Effect |
|---|---|---|
| YAML flow lists split at the comma: three sales tax sub-industries each claim "retail" | `entities.yml:3783, 3808, 3821`; loading gives `['Computer and s oftware stores', 'retail']` | The intended kerned labels never match; a bare "Retail" row has four claimants and resolves to nothing. The registry accepts this (`entities.py:486-493`). Only "Total Retail" is tested (`tests/test_entities.py:1450-1460`). |
| Release notes say every collection family has zero unresolved row identities | `release-notes/data/2026.07.31.yml:74-75` | Contradicts the defect above unless no edition prints the kerned form. Not verifiable here. |
| Footnote-decorated department names left ids null | `release-notes/data/2026.07.24.1.yml:26-28` | Fixed by normalization and a refresh. |
| Budget in Brief rows lacked the General Fund subject id | `release-notes/data/2026.07.28.yml:12-19` | Added later without changing values. |
| OCR variants of Purchase of Services split one cash series | `release-notes/data/2026.07.31.yml:43-49`; `entities.yml:4686-4688` | One-report series seam, closed by a qualifier alias. |
| Hotel Fund and School PILOT edition seams | `release-notes/data/2026.07.31.yml:87-90`; `entities.yml:4569-4587` | Closed by scoped aliases. |
| Resolution fingerprint omitted `dimension`; BIRT industry and sub-industry changes left stale artifacts | `docs/code-review-fix-workorders-2026-08-01.md:53-65`; now included at `entities.py:747` | Fixed. A caching artifact. |
| Qualifier stale-entity bug (M22): a placeholder row skipped section-group bookkeeping, so CURRENT YEAR rows under an unresolved tax went to the previous tax | `docs/code-review-fix-workorders-2026-08-01.md:380-390`; bookkeeping now precedes the `continue` at `resolution.py:1822-1844` | Fixed by reading. |
| 145 identity-loss flags on 24 PA totals after a correct ownership change | `docs/analysis-readiness-0.4.1-status.md:5-12` | Out-of-scope family, but shows the regression gate cannot tell a correction from a loss. |
| Edition misprints stored as global aliases | "Office of Human Services" on Human Resources (`entities.yml:1266-1267`); "Community Engagement and Opportunity" (`entities.yml:1070-1071`); RTT "Non-residential" on General Commercial for one January 2020 edition (`entities.yml:3904-3906`) | Each can capture a different row in another edition. This contradicts the file's own rule for scoped OCR repairs (`entities.yml:4508-4510`). |
| Out-of-scope aliases leak into in-scope families | Finance carries "Director of Finance: 100 Personal Services" (`entities.yml:821`) and every Finance alias applies to QCMR, Budget in Brief and supplemental | One entity, one alias list, many families. |
| Supplemental identity requirement can never fire | `identity_required_from_fiscal_year: 2025` (`page_types.yml:755-756`); last edition FY2024 | No supplemental row is ever required to carry an id. |
| Fairmount Park and Recreation scoped to `qcmr_*` | `entities.yml:2537-2541, 2552-2556` | Applies to QCMR cash too. Harmless today. |
| Positions FY14 to FY17 print no row labelled "Streets" | 27 + 32 = 59 of 75 reports (`tests/test_qcmr_positions_continuity.py:551-553`); patterns skip FY14 to FY17 (`entities.yml:1548-1550, 1564-1565`) | Label used in those 16 reports unknown. |
| Possible duplicate key in personal services | "MDO-Base" is an alias of the Managing Director department (`entities.yml:1034`), while the layout says MDO-* blocks print beside the parent (`qcmr-personal-services.yml:100-107`) | Two blocks could get one (entity, qualifier) key. No check looks for duplicate keys in a table. |
| Regression gate keyed on ordinals | Observation key includes `table_index`, `row_index`, `column_index` (`identity_quality.py:53-64`); flags only id to null (`identity_quality.py:522-543`) | A re-extraction that shifts rows escapes comparison; an id that changes to another id is not flagged. |

Two scoping rules exist only in tests or not at all. The Budget in Brief class qualifier rule has no table or row-kind scope (`entities.yml:4665-4678`). The unit test models a rule scoped to obligation-history totals (`tests/test_resolution.py:2083-2120`). Whether "Total" rows in fund summaries pick up department ids cannot be checked without artifacts.

## 5. Reporting units that are not real entities

Reporting units are told apart by at least seven mechanisms, none of which says "this is a group of these members".

| Unit | Examples | How the old code tells it apart |
|---|---|---|
| Totals and subtotals | TOTAL GENERAL FUND AND PICA, TOTAL TAX REVENUE, TOTAL ALL FUNDS, sales tax "Subtotal" | `rollup` dimension (43 in scope) plus classified `row_kind` |
| A subtotal that is the parent entity | sales tax "Total Retail" is Retail (`entities.yml:3764`); BIRT "Manufacturing, subtotal" is Manufacturing (`entities.yml:4248`) | alias on the parent industry |
| Combined reporting scopes | "City Rep. / Commerce", "Streets (including Sanitation)" | `rollup` plus the `organization_entity_ids` allowlist (`entities.yml:4430-4435`) |
| Combined labels folded into one member | "Commerce/City Representative" (`entities.yml:771`), "Office of Children & Families / Human Services" (`entities.yml:938`), "Human Relations Commission/Fair Housing Commission" (`entities.yml:919`) | plain alias; no rule says why these differ from the line above |
| Fund scopes | All Funds, General plus Grants Revenue | `funds.yml:87-96` name patterns, checked before fund names |
| Report-wide totals after the last section | Budget in Brief "Total, General Fund" | `entity_context_exclude_patterns` (`page_types.yml:556-560`) |
| Divisions not to be summed | about 30 personal services sections such as Highways, MDO-*, OPS-* | `metric_grid_exclude_sections` (`qcmr-personal-services.yml:96-137`); no entity |
| Residual categories | All Other Taxes, All Other Sectors, Unclassified, Other Funds, Unassigned, Other Sectors | ordinary entities; nothing marks them residual |
| Comparators and memo rows | sales tax FAMIS total, wage tax FAMIS total, RTT data-file comparisons | rollup entities, and `memo_items` in layouts |
| Supplemental subtotals | "Totals - All Budget Agencies", "Subtotal Funds:", "Subtotal Mayor's Office of Community Services:" | no entity; acknowledged by `label_pattern` (`config/layouts/supplemental-report.yml`) |

The `rollup` dimension mixes true sums, comparators (FAMIS) and organizations (the two combined scopes). `phl_general_fund` is a rollup that also stands for a fund. Some totals are entities and some are not, by family.

## 6. The earlier proposal, judged

The proposal fits QCMR and collections well and fits Budget in Brief and the supplemental report only in part. Those two families key rows by context, carry open row sets, and need relations the proposal does not name.

### Row schema per table and era

Supported for closed tables:

- Many tables have short, stable row lists: QCMR positions (71 departments, 3 rollups), QCMR cash (55 lines), monthly City (70) and School (10). BIRT (35), sales tax (31), wage tax (55) and RTT (44) are the same.
- Matching during parsing removes the largest piece of old code. The parser knows the parent of "Civilian" and "CURRENT YEAR". So 489 lines of qualifier inference (`resolution.py:1531-2019`) become a declared parent.
- Edition-bound rows fit naturally: 11 scoped aliases, "Streets" by era, the FY12 Q3 "Burchase".
- "A missing or unexpected row fails" closes two gaps the old code has: no duplicate-key check, and no check for a dropped row.

Not supported as stated:

- QCMR obligations and personal services gain and lose departments often (OPS FY26, Prison Oversight FY26, OCF FY21 to FY24, CPOC). A closed list per era needs many eras. Better: the schema declares the row grammar, and department rows must resolve to a registry department valid in that fiscal year.
- Budget in Brief obligation history covers 28 documents, FY06 to FY27. It has about 99 departments, retired units, wrapped names and edition-specific footnote numbers. "Missing row fails" is wrong there, because departments legitimately end. "Unexpected row fails" still holds.
- Budget in Brief revenue schedules and the supplemental revenue and capital tables are open sets. Row indices reach 725 in one supplemental table (`config/layouts/supplemental-report.yml:38`). A per-era list of every revenue source or capital line is not maintainable. The schema there has to be a grammar of row kinds: agency banner, class line with a three-digit code, "Subtotal X:", grand total. The printed label is the key inside (fund, agency).
- Row keys in these families are composite. A Budget in Brief obligation row is (department from the section, class). A revenue schedule row is (fund code, schedule id, agency banner, label). A supplemental row is (fund banner, agency section, class code). The proposal's "parent" covers this only if parent may come from page context.
- One key must span two tables. The Budget in Brief cross-table check needs "Revenue from Other Funds of the City" and "Revenue from Other Funds" to be one key (`resolved_assertions.yml:56-60`).

### A small global registry

Supported:

- The truly shared kinds are few: about 110 departments and child lines, 17 funds, 8 classes, and about 25 tax concepts. Industries (113), RTT classes (44) and cash lines (20) are single-family and belong in their table's schema. That is a small registry.
- Official codes exist for departments (60 of 99, one reused), funds (with code history) and classes. Dated codes already work (`entities.yml:4492-4494`, `funds.yml:63-74`).
- Merge and split events have a working shape (`entities.py:418-463`) and a reader that refuses to splice across a split (`gov_budget_data/lineage.py:47-86`).

Not supported as stated:

- "Dated names" do not exist anywhere in the config. Every rename is an undated alias. Building them is research, not porting.
- 18 top-level departments have no code (historical units such as Civic Center, Camp William Penn, Tax Reform Commission). Ids cannot rest on codes alone.
- The reorganizations in `audit.yml` are not merges or splits. They say "reported under X, only in fund 12" or "only from FY2020 to FY2024". The registry needs a third relation, reported-under, scoped by fund and years.
- Funds need one registry, not three. The proposal is silent on funds as context rather than rows.

### Reporting units as named groups

Supported for combined scopes, fund scopes and the excluded personal services divisions. It is not enough alone. Some totals are the parent entity's own value ("Total Retail"). Some groups have no printed members ("TOTAL TAX", cash "Other Funds"). A group needs three forms: a sum of named members, a parent's own total, and an opaque printed group. Residual categories need a flag, because their composition changes between eras.

### Plain data files with a lint

Strongly supported. Every config defect found here is one a lint catches:

- the same normalized label claimed twice in an overlapping scope (the "retail" defect);
- YAML flow lists containing commas;
- an edition-specific alias with no edition scope ("Office of Human Services", RTT "Non-residential");
- an alias equal to its own name after normalization (66 cases);
- a gate year past the last edition (`page_types.yml:755-756`);
- a catch-all family pattern on a department (`qcmr_*`).

## 9. Quirk ledger

| Id | What happens in the documents | Where the old code handles it | Kind |
|---|---|---|---|
| ENT-Q01 | One printed label names different things in different datasets: 27 normalized labels have more than one id. "Licenses & Inspections" is a City revenue line and a QCMR department; "Real Estate Tax" has three ids. | `entities.py:253-258, 282-286, 885-898` | inherent |
| ENT-Q02 | One label changes meaning by era in one table: positions "Streets" is the department in FY08 to FY13 and FY26, Streets including Sanitation in FY18 to FY25. | `entities.yml:1545-1565` | inherent |
| ENT-Q03 | One label, different entity by table in one document: RTT "Other Vacant Land" in property and location tables. | `entities.yml:3886-3888`; `entities.py:259-263` | inherent |
| ENT-Q04 | One label, different entity by row role: BIRT "Other Services" is a component and a standalone sector; the "**2" marker that separates them is stripped. | `entities.yml:4229-4233`; `entities.py:264-267` | inherent |
| ENT-Q05 | One-edition relabels: June 2025 City prints TOTAL HOTEL FUND as "HOTEL TAX"; June 2020 School prints PILOTs as "MISCELLANEOUS NON TAX REVENUES". | `entities.yml:4569-4587`; `entities.py:981-984` | inherent |
| ENT-Q06 | OCR-damaged labels on scans: 8 FY07 Q4 cash labels ("Property Tull"); FY12 Q3 "Burchase of Services". | `entities.yml:4508-4558, 4686-4688` | inherent |
| ENT-Q07 | Footnote marks on labels change by edition: "Human Services (1)", "Office of Public Safety (9)" in Budget in Brief and "(7)" in QCMR, "Sheriff 2", "**1". | `entities.py:56-61, 78-98` | inherent |
| ENT-Q08 | Printed line numbers fuse into labels: QCMR recap "24 First Judicial District", "I Records"; Budget in Brief LINE NO. margin. | `entities.yml:852-855`; `config/layouts/budget-in-brief.yml:21-25, 176-178, 239-241` | inherent |
| ENT-Q09 | Labels cut at the column edge in monthly City: "TOTAL PICA AND CITY WAGE TA"; about 169 aliases are prefixes. | `entities.yml:25-28` and many aliases | unsure: settle by checking whether the PDF text layer itself is cut |
| ENT-Q10 | Kerning breaks inside words in sales tax: "Car and truc k rental", "Department s tores, retail". | `entities.yml:3727, 3743, 3783, 3808, 3821` | unsure: same test as ENT-Q09 |
| ENT-Q11 | Three sales tax aliases split at the comma; each sub-industry claims "retail"; the registry accepts four claimants. | `entities.yml:3783, 3808, 3821`; `entities.py:486-493` | artifact: YAML alias lists with no same-scope duplicate lint |
| ENT-Q12 | Rows that name a breakdown, not an entity: positions Civilian and Uniform (with fused numbers "23 Civilian"); collections CURRENT YEAR, PRIOR YEAR(S); suffix forms "REAL ESTATE: CURRENT"; school truncations C to CURREN and P to PRI. | `entities.yml:4589-4656`; `entities.py:126-233` | inherent |
| ENT-Q13 | Parent and qualifier fused in one cell: "SCHOOL INCOME TAX CURRENT YEAR", "USE AND OCCUPANCY TAX CURRENT YEAR COLLECTIONS". | `resolution.py:1551-1620` | inherent |
| ENT-Q14 | A value-less heading carries CURRENT or PRIOR and the next "-" row carries the amounts (BIRT block). | `resolution.py:1832-1844, 1944-1952` | inherent |
| ENT-Q15 | An amount-bearing parent row sits directly above its current and prior rows inside a coarse "OTHER TAXES" section. | `resolution.py:1923-1933` | inherent |
| ENT-Q16 | A wrapped section heading: one fragment unreadable must not erase the other; contradictory fragments clear the parent. | `resolution.py:1953-1975` | inherent |
| ENT-Q17 | Personal services: three metric rows under each department section, some matched only through organization aliases. | `entities.yml:4657-4664`; `resolution.py:1921-1922` | inherent |
| ENT-Q18 | QCMR cash: "Purchase of Services" and "Payments to Other Funds" repeat under different sections. | `entities.yml:4684-4703` | inherent |
| ENT-Q19 | Budget in Brief obligation rows are (department section, class). Class labels have no canonical form, so "Advances and Other Misc. Payments" and "Advances & Miscellaneous Payments" stay different. | `entities.yml:4665-4678`; `entities.py:110-123` | inherent for the pair; artifact for the unmerged spellings |
| ENT-Q20 | The Budget in Brief class qualifier rule has no table or row-kind scope; the test models a scoped rule. | `entities.yml:4665-4678`; `tests/test_resolution.py:2083-2120` | unsure: settle with resolved fund-summary rows |
| ENT-Q21 | Sub-department appropriation lines print beside the department (Finance-Indemnities, OIT-Base, Streets-Disposal, reserves) and are separate series. | `entities.yml:3266-3354`; `resolution.py:1277-1365` | inherent |
| ENT-Q22 | "X-Base" lines are modelled two ways: MDO-Base and Office of Public Safety-Base are aliases of the department; OIT-Base is a child entity. | `entities.yml:1034, 2562-2564, 3270-3279` | artifact: hand curation with no rule |
| ENT-Q23 | Child lines use two dimensions: "Finance: Refunds" is a department with a parent, "Finance - Indemnities" is `other`. | `entities.yml:3280-3290` and the Finance children | artifact |
| ENT-Q24 | Combined labels are handled two ways: two are rollup organizations, three are aliases of one member. | `entities.yml:4430-4435, 771, 919, 938` | unsure: settle by checking values against neighbours in those editions |
| ENT-Q25 | Monthly City prints departmental revenue rows HEALTH, SHERIFF, RECORDS, STREETS; they get department ids, while LICENSES & INSPECTIONS gets a revenue entity. | `entities.yml:1450-1464, 483-492`; `collections-monthly-city-2026-08.yml:703-748` | artifact: dimension conflation |
| ENT-Q26 | Three fund registries; four ids for the General Fund. | `funds.yml`; `entities.yml:369-377, 2149-2156, 3250-3257` | artifact |
| ENT-Q27 | Fund codes are reused over time: 15 is Budget Stabilization to FY2020 and Demolition from FY2023; Budget Stabilization is 01-011 from FY2021. | `funds.yml:59-74`; `funds.py:148-171` | inherent |
| ENT-Q28 | Department number 66 moves between Education and Children and Families. | `entities.yml:4492-4494`; `audit.yml:74-79` | inherent |
| ENT-Q29 | Fund codes print padded or composite ("010", "060", "01-011"). | `funds.py:23-35` | inherent |
| ENT-Q30 | A fund banner can disagree with its code; the name wins and the conflict is kept. | `funds.py:282-303` | inherent |
| ENT-Q31 | "All Funds" and "General/Grants Revenue" are scopes, not funds. | `funds.yml:87-96`; `funds.py:256-264` | inherent |
| ENT-Q32 | Single-agency funds print no agency banner; the fund banner is the department (HealthChoices Behavioral Health, Water Residual), and fund names are department aliases. | `page_types.yml:743-747`; `resolution.py:1012-1036`; `entities.yml:1152, 1599` | inherent |
| ENT-Q33 | Budget in Brief revenue schedule banners carry a category suffix ("State:", "Federal"); bold banners set the owner, plain ones refine it. | `page_types.yml:573-579`; `resolution.py:1157-1274` | inherent |
| ENT-Q34 | Budget in Brief section text fuses the table banner (FY2011 "Obligation History Fiscal Years 2009 - 2011 City Planning", FY2015) or wraps a name over two lines (Prison Oversight). | `entities.yml:716-718, 1094-1095, 2576-2579` | unsure for fused banners (extraction or print); inherent for the wrap |
| ENT-Q35 | Budget in Brief "Total, General Fund" follows the last department with no new heading. | `page_types.yml:556-560`; `resolution.py:1087-1116` | inherent |
| ENT-Q36 | Budget in Brief fund summary and revenue schedule spell one category two ways ("... of the City"). | `resolved_assertions.yml:56-60` | inherent |
| ENT-Q37 | One fund statement prints "June 30 of Prior Fiscal Year" where all others print "or". | `resolved_assertions.yml:120-125` | inherent |
| ENT-Q38 | Budget in Brief acknowledgment keys are normalized labels that include fused numbers and wrap fragments ("... prior fiscal year 23 29", "june 30 of prior fiscal year"). | `resolved_assertions.yml:268-285, 337-348` | artifact: label-text keys |
| ENT-Q39 | Retired units stay in Budget in Brief obligation history at zero beside the parent. | `entities.yml:2610-2614` | inherent |
| ENT-Q40 | FY18 prints the retired Office of Planning and Development beside new code-72 Planning & Development. | `entities.yml:1302-1305`; `tests/test_entities.py:2478-2489` | inherent |
| ENT-Q41 | New and moved agencies: Office of Prison Oversight and OPS-* blocks from FY26; Sanitation standalone in personal services FY08 to FY13. | `entities.yml:2576-2579`; `qcmr-personal-services.yml:2-8, 108-111` | inherent |
| ENT-Q42 | About 30 personal services division sections have no entity and must not be summed into citywide totals. | `qcmr-personal-services.yml:12-46, 96-137` | inherent |
| ENT-Q43 | Fairmount Park and Recreation merged into Parks and Recreation, effective FY2011. | `entities.yml:4710-4719` | inherent |
| ENT-Q44 | Reorganizations recorded as comparison folds: 23 rollups, 1 dated fold, 4 fund-scoped folds. | `audit.yml:47-97` | inherent facts in an artifact location |
| ENT-Q45 | Edition misprints stored as global aliases ("Office of Human Services", "Community Engagement and Opportunity", "CITY COMMSISSIONERS OFFICE", RTT "Non-residential"). | `entities.yml:686-687, 1070-1071, 1266-1267, 3904-3906` | artifact: aliases cannot carry an edition |
| ENT-Q46 | Aliases from budget detail apply in every family of the entity (": 100 Personal Services" forms). | `entities.yml:821`; `entities.py:288-292` | artifact |
| ENT-Q47 | Fairmount Park and Recreation are scoped by the `qcmr_*` catch-all. | `entities.yml:2537-2541, 2552-2556` | artifact |
| ENT-Q48 | Two different totals in one table: taxpayer database total (PRISM, TIPS) and accounting system total (FAMIS); sales tax FAMIS comparator prints its year in the label. | `entities.yml:3365-3372, 3863-3884` | inherent |
| ENT-Q49 | RTT 2024 class splits are kept apart from the legacy classes, with no event. | `entities.yml:3886-3890`; `tests/test_entities.py:1513-1524` | inherent |
| ENT-Q50 | Sub-industry indentation is lost, so sub-industries classify as line items and are relabelled from the catalog. | `resolution.py:887-920` | unsure: settle by checking indentation in the word boxes |
| ENT-Q51 | Industry taxonomies differ by tax; 14 sector names repeat across them with different definitions. | `entities.yml:3355-3359, 3688-3691, 4229-4233` | inherent |
| ENT-Q52 | Some subtotal rows are the parent entity ("Total Retail", "Manufacturing, subtotal"), others are rollups. | `entities.yml:3764, 4248, 3250-3257` | inherent |
| ENT-Q53 | Residual categories (All Other Taxes, Unclassified, Other Funds, Unassigned) look like ordinary entities. | `entities.yml` throughout | inherent |
| ENT-Q54 | Monthly School wraps "TOTAL U&O TAX COLLECTIONS &" and "SETTLEMENTS" over two rows. | `entities.yml:1686` | inherent |
| ENT-Q55 | Unknown and ambiguous labels publish with a null id and enter a review queue; nothing blocks QCMR or collections. | `entities.py:1004`; `resolution.py:483-484` | artifact |
| ENT-Q56 | The registry accepts two scoped claimants of one label and the resolver returns nothing. | `entities.py:486-493, 532-539` | artifact |
| ENT-Q57 | The supplemental identity requirement starts at FY2025, after the last edition. | `page_types.yml:755-756` | artifact |
| ENT-Q58 | The identity regression gate keys rows on ordinals and flags only id to null. | `identity_quality.py:53-64, 522-543` | artifact |
| ENT-Q59 | The resolution fingerprint once omitted `dimension`, leaving stale BIRT artifacts. | `entities.py:747` (fixed) | artifact: staleness cache |
| ENT-Q60 | A placeholder row once skipped section-group bookkeeping and misattributed qualifiers (M22). | `resolution.py:1822-1844` (fixed) | artifact: inferred section state |
| ENT-Q61 | No check that two rows of one table get the same key; MDO-Base and the MDO block may collide. | none; `entities.yml:1034`; `qcmr-personal-services.yml:100-107` | unsure: settle with one personal services edition |
| ENT-Q62 | Expenditure classes and cash-flow lines are filed as `revenue_category`. | `entities.yml:2008-2010`; `entities.py:41-51` | artifact |
| ENT-Q63 | 66 in-scope aliases equal their entity's name after normalization. | `entities.yml` throughout | artifact |
| ENT-Q64 | Positions FY14 to FY17 print some other label for Streets; no entity pattern covers those years. | `entities.yml:1548-1550, 1564-1565`; `tests/test_qcmr_positions_continuity.py:551-553` | unsure: settle with one FY15 positions page |
| ENT-Q65 | Department ids are shared with budget detail, which stays in the old repo. | all 89 budget-detail entities are also in-scope entities (`ent_tools/a2.py`); `entities.py:520-531` | inherent to the repo split |
| ENT-Q66 | Organization lookup ignores family scope, so a section in any family can resolve through any family's alias. | `entities.py:1115-1138` | artifact |
| ENT-Q67 | The fiscal-year cash label for prior-year collections prints the date: "Collection of 6-30-06/Govt." and later years. | `entities.yml` `phl_cash_prior_year_revenue` aliases | inherent |

Why the artifact quirks do not arise in a clean design:

- one global alias list per entity: Q45, Q46, Q63, Q66;
- YAML lists with no lint: Q11, Q56;
- resolution after parsing instead of during it: Q55, Q60, Q61;
- ordinal and label-text keys, and a staleness cache: Q38, Q58, Q59;
- hand modelling with no rule: Q22, Q23, Q25, Q26, Q47, Q57, Q62.

## 10. Old code that serves row identity

| File | Lines | Job | Keep as code or as knowledge |
|---|---|---|---|
| `entities.py` | 1,494 | registry model, normalization, resolver, successions, codes, fingerprint | Code: `normalize_entity_label` (78-98), suffix split (225-233), succession shape (418-463), code interval checks (623-660). Knowledge: the rest. |
| `resolution.py` | 2,267 | resolve stage: join, qualifiers, org context, review queue, seam detector | Knowledge: the qualifier cases (1531-2019) become declared parents in parsers; org context rules for Budget in Brief and supplemental. |
| `funds.py` | 319 | fund registry, scopes, code history | Code: `normalize_printed_code`, code interval check, scope-before-name order. |
| `identity_quality.py` | 807 | release identity checks and regression gate | Knowledge: the six issue kinds; the regression idea moves to the row diff with stable keys. |
| `identity_evidence.py` | 82 | cross-section total proofs | Knowledge only; not these families. |
| `resolved_assertions.py` | 1,747 | Budget in Brief cross-table equality | Knowledge: the six acknowledgment lessons in the E10 report; key rows by row key, not label text. |
| `resolution_provenance.py` | 238 | staleness sidecars | Stays. |
| `page_types.py` (entity context parts) | 97 mentions in 1,342 lines | context field, exclusions, hierarchy, identity requirement | Knowledge. |
| `gov_budget_data/entities.py`, `lineage.py` (reader) | 185, 86 | catalog search, lineage, splice refusal | Code: `predecessor_spans` and the split refusal. |
| `config/entities.yml` | 4,730 | 474 entities, 61 codes, 11 scoped aliases, 15 qualifier rules, 2 successions | Data, after the lint and a split into registry and per-table rows. |
| `config/funds.yml` | 96 | 17 funds, 2 scopes | Data. |
| `config/audit.yml` | 249 | class codes, folds | Data for the reported-under relation and class codes. |
| `config/resolved_assertions.yml` | 417 | 2 Budget in Brief assertions, discrepancy records | Knowledge; rekey records. |
| Tests | `test_entities.py` 2,508; `test_resolution.py` 3,803; `test_qcmr_positions_continuity.py` 556; `test_identity_quality.py` 379; `test_successions.py` 250; `test_funds.py` 158 | | Knowledge: the named label cases are fixtures for row schemas. |

## 11. The least a design needs

Inputs: one table's words with page boxes, the edition and fiscal year, and page context (fund banner, schedule id, agency section). Two data files: the shared registry and the table's row schema.

Steps from words to keyed rows:

1. Normalize each label with one function: strip glyph codes, fused amounts, edge footnote marks and `(N)` references; keep a two-digit bare prefix. Read a fused line number or class code as its own field.
2. Assign each row a kind from the table's grammar: section, header, line, total, subtotal, breakdown, memo.
3. Build the row key from the table's declared parts. QCMR positions: (department, breakdown). Collections: (tax, cohort). Budget in Brief obligations: (department from section, class). Revenue schedule: (fund code, schedule id, agency, label). Supplemental: (fund, agency, class code or label).
4. Resolve each key part. Table-local parts match the table's schema for that era. Shared parts (department, fund, class, tax concept) match the registry for that fiscal year.
5. Fail the parse on a row of no declared kind, on a duplicate key, and on a missing row in a closed table. Open tables (revenue detail, capital lines) fail only on unknown kinds and duplicates.
6. Emit the printed label beside the key, always.

Parameters that differ by era:

- closed row lists (positions, cash, collections, sector reports);
- edition-bound spellings and the "Streets" meaning;
- the valid department set, fund code meanings and class spellings.

Checks to declare:

- no normalized label claimed twice in an overlapping (dataset, table, row kind, era);
- every alias names its source edition or era, and an edition-specific spelling is scoped to it;
- no flow-style YAML list holds a comma, or the files are not YAML;
- registry codes and names have non-overlapping date ranges;
- merges, splits and reported-under links reference known ids and dates;
- every row key in a release is unique per table and edition;
- the release diff flags a key whose id changed, not only one that went null;
- a gate year is inside the edition range it governs.

## 12. Unknowns

- How many rows publish with a null `entity_id` today, by family. No resolved artifacts exist here.
- Whether the kerned sales tax labels still occur, which decides whether ENT-Q11 loses data or only leaves dead config.
- What label QCMR positions FY14 to FY17 print for Streets.
- Whether personal services prints both a Managing Director block and an MDO-Base block in one edition.
- Whether "Total" rows in Budget in Brief fund summaries and revenue schedules picked up department ids through the unscoped class rule.
- Whether "23 29" in the FY09 Budget in Brief keys are footnotes or line numbers, given `drop_margin_line_numbers` is set for FY09.
- The real row inventory of the Budget in Brief revenue schedules and the supplemental revenue and capital tables.
- Whether supplemental capital rows are projects or categories.
- Whether fund 12 is the Housing Trust Fund (`funds.yml:46-48`) or the "Development Fund" named in `audit.yml:86-91`.
- Whether truncation and kerning are in the PDF text layer or come from extraction (ENT-Q09, ENT-Q10).
- Whether the tax detail reports print NAICS codes.
- The dates of every rename now held as an alias.
