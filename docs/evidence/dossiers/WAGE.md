# WAGE: Wage Tax by industry and Wage Tax by resident status

Two report series from the Revenue Department share one industry hierarchy. The industry series (`collections_wage_tax_industry`) has 107 documents from January 2014 to March 2026. The residency series (`collections_wage_tax_residency`) has 4 rolling documents covering calendar years 2019 to 2023.

Paths below drop `packages/gov-budget-etl/src/gov_budget_etl/`. "Notebook" means `notebooks/wage_tax_industry_trends.ipynb`, cited by 0-based cell. Nothing here was checked against a PDF; the checkout has none.

**The typed subsets.** The industry catalog lists five: `wage_tax_cytd`, `wage_tax_fytd`, `wage_tax_fytd_report_period`, `wage_tax_quarter`, `wage_tax_report_period` (`docs/site/data/index.md:279-283`). A sixth page type, `wage_tax_secondary_period`, is declared (`config/page_types.yml:929-931`) but has no published subset. The residency catalog lists `wage_tax_residency_summary` and `wage_tax_residency_detail` (`docs/site/data/index.md:311-312`).

The five industry subsets are not five kinds of table. They mix the printed table number with the period. `wage_tax_fytd` and `wage_tax_fytd_report_period` are both fiscal year to date. `wage_tax_report_period` is one month in the monthly era but holds July to September in some September reports (notebook cell 6). A new design should type by period kind (month, quarter, calendar YTD, fiscal YTD) and keep the table number as evidence.

## 1. Documents

| | Industry | Residency |
|---|---|---|
| Listing | One page per year, `phila.gov/documents/<year>-wage-tax-by-industry/`; 2016 is `wage-tax-by-industry/` (`wage_tax_industry.py:90-93`) | One page, `documents/wage-tax-collections-by-resident-and-non-resident/` (`wage_tax_residency.py:24`) |
| Link form | Titled anchor plus an icon-only anchor with the same URL (`phila_media.py:386-390`) | Same |
| Cadence | Monthly to February 2021, quarter end from March 2021 (`temporal_contracts.json:67-101`) | Irregular, one rolling report per year end |
| Span | 2014_01 to 2026_03, 107 documents (`docs/site/data/index.md:266`) | 2020_12, 2021_12, 2022_12, 2023_12 (`release-notes/data/2026.07.26.yml:42-45`) |
| Local key | Ending calendar month, `<YYYY>_<MM>` (`wage_tax_industry.py:52-55`) | Ending calendar year, `<YYYY>_12` (`wage_tax_residency.py:39-42`) |
| Pages | September reports are one page (notebook cell 6); the FY2026 July to June report is three pages (`docs/philly-source-monitoring-audit-2026-09-11.md:55-57`). Chart pages carry no table title | Summary on page 1, detail on page 2; the 2021 to 2023 report is one page (`config/page_types.yml:957-960`) |

The count 86 monthly plus 21 quarterly equals 107, which fits a gap-free run. The notebook confirms 49 of 49 quarters from 2014 Q1 to 2026 Q1 (cell 14).

**Scans.** Text-layer status is not recorded in any config file. One comment says the December 2023 industry release is scan only (`config/semantics.yml:3771`). For every other edition the text-layer status cannot be read from the checkout. Alias spellings in the entity registry ("DNovors", "Food & Bevera ge") show that some labels came through OCR or a damaged text layer (`config/entities.yml:3518, 3553`).

**Industry page years.** Older pages use calendar years ("January 2014 Wage Taxes", `tests/test_wage_tax_industry.py:41-44`). Newer pages use fiscal years ("July to September FY2026", `:50-58`). The CLI and source sync pick the current page by fiscal year (`commands/collections.py:231`, `phila_source_sync.py:205`). The year of the switch is not known.

## 2. Tables

### Industry analytical table

- **Row:** one industry, one sub-industry, or one of two closing totals.
- **Rows:** 22 industries and 30 sub-industries (notebook cell 5), then "Total from Taxpayer Database (TIPS/PRISM)" and "Total from City's Accounting System (FAMIS)". About 54 rows.
- **Hierarchy:** six industries are followed by their sub-industries as sibling rows (`config/layouts/collections-tax-details.yml:28-40`). Manufacturing has 7, Health and Social Services 5, Education 3, Professional Services 6, Other Sectors 5, Government 4 (`config/entities.yml:3494-3687`).
- **Columns, left to right** (reversed from `config/semantics.yml:3734-3753`): current period $, prior year $, prior 2 $, prior 3 $, Current vs prior %, Prior vs prior 2 %, Prior 2 vs prior 3 %, 3-year annualized %, Current minus prior $. Nine value columns in every era (`min_amount_columns: 9`, `:3733`).
- **Header:** the title names the table number and period. Year captions sit above the region the old engine detects, so they are never read as cells (`config/semantics.yml:3761-3769`).
- **Totals:** in some legacy tables both totals sit in a ruled box below footnotes (`config/layouts/collections-tax-details.yml:53-56`).
- **Size:** 144,781 value rows over 107 documents (`docs/site/data/index.md:268`). That is about 1,350 values per document, or two to three tables. This is an inference.
- **Multi-page:** no evidence that one table spans pages.

### Residency summary and detail

- **Row:** 22 industries, 30 sub-industries and "Total": 53 rows (`config/layouts/collections-tax-details.yml:70` puts Total at row index 52).
- **Summary columns:** per year, nonresident share %, resident share %, combined $; then change columns. Year blocks run newest first.
- **Detail columns:** per year, distinct accounts, nonresident $, nonresident %, resident $, resident %, combined $.
- The column order is my reversal of the right-to-left lists in `config/semantics.yml:3351-3373, 3392-3445, 3491-3525, 3550-3606`. The acknowledgment column indices agree with it (`config/layouts/collections-tax-details.yml:68, 90, 123, 144`).

## 3. Format eras

| Series | Era | Editions | What changes | Evidence |
|---|---|---|---|---|
| Industry | Monthly | 2014_01 to 2021_02 | Table 1 is the month. Table 2 is FYTD, CYTD or quarter. Some reports add Table 3 (CYTD, "January thru March") and Table 4 ("2nd Quarter (Apr, May, Jun)") | `temporal_contracts.json:67-89`; `config/page_types.yml:906-920`; `tests/test_page_types.py:562-567` |
| Industry | Quarterly | 2021_03 to 2026_03 | Table 1 is the quarter, or FYTD for July to September and July to December reports. FYTD then appears only in the header line "NAICS Sector / Industry Group FYTD 2025 FYTD 2024" | `config/page_types.yml:921-928`; `tests/test_page_types.py:549-556` |
| Industry | Label | Unknown years | Database total reads TIPS, then PRISM/TIPS, then PRISM | `config/entities.yml:3369-3373` |
| Industry | Label | Unknown years | "Manufacturing (includes headquarter offices)" gains "& factories" | `config/entities.yml:3423-3427` |
| Industry | Single edition | 2023_12 | Scan only; Table 2 header misprints the quarter as "Oct-Dec 2024" | `config/semantics.yml:3771-3776` |
| Industry | Single edition | 2024_09 | July to September is labelled FYTD 2025 | notebook cell 14 |
| Residency | First | 2020_12 (2019 to 2020) | Summary 10 columns, detail 16 columns, both with 4 change columns | `config/semantics.yml:3350-3373, 3490-3541` |
| Residency | Rolling three-year | 2021_12, 2022_12 | Summary 17 columns (3 years, 2 change periods); detail 18 columns, no change columns | `config/semantics.yml:3391-3445, 3549-3606` |
| Residency | Summary only | 2023_12 (2021 to 2023) | One page; no detail grid | `config/page_types.yml:957-960`; `config/semantics.yml:3459-3469` |

## 4. Finding the table

Today every page is typed by its title, using the first matching rule in declared order (`page_types.py:1171-1183`). The marker pattern `__wage_tax_no_marker__` never matches; it exists only because the classifier expects a marker (`config/page_types.yml:904, 963`). Pages with no matching title, such as chart pages, are evidence only (`:935`; `tests/test_page_types.py:594-602`).

The table region is found by whitespace consensus. The trailing total box is rejoined by a ruled-box detector (`tables/region_detection.py:331-414`, switched on by `config/layouts/collections-tax-details.yml:56`). Pages of the same type are pooled and stitched (`page_table_scoping.py:543-552`).

Simplest reliable rule: one table per page. Find the page by a title line starting "Table N: ... Wage Tax by Industry", or "Wage Tax by Industry for Calendar Years ... Summary Page / Detail Page". Read the period kind from the title words, and from the header line when the title has none. The table runs from the first industry label ("Arts, Entertainment...") through the last total label, skipping footnote lines.

## 5. Arithmetic that holds

| Relation | Scope | Declared today | Known source breaks |
|---|---|---|---|
| Sum of 22 industry rows = TIPS/PRISM total, every dollar column | Industry | Yes, total check (`config/layouts/collections-tax-details.yml:45-49`) | None recorded |
| FAMIS total is a comparator, not a sum | Industry | Demoted to line item (`:50-51`) | Not a check |
| Parent industry = sum of its sub-industries | Both | No. Components are only kept out of sums (`tables/reconciliation_rows.py:273-330`) | 2022_03: Health and Education components carry equal and opposite residuals, $15.98M FYTD and $10.24M quarter (notebook cell 14) |
| Current minus prior = current $ less prior $ | Industry | No | Unknown |
| Rates match the dollar columns after rounding | Industry | No. Percent columns are excluded (`:52`; `tables/reconciliation_columns.py:70-105`) | Unknown |
| Sum of industry rows = Total, each $ and account column | Residency | Yes | 2020 combined total +112,762 and 2019 combined total -448, repeated in later editions. The 2020 edition's account totals are off by -11,545 (2020) and -11,451 (2019) |
| Resident share + nonresident share = 100 | Residency | No | None seen in two samples (`docs/investigations/unverified-row-audit/source-observations.json:14-15`) |
| Resident $ + nonresident $ = combined $ | Residency detail | No | Unknown |
| Overlapping year agrees across editions | Residency | No; newest edition wins | Combined totals repeat exactly. Account totals for 2019 and 2020 appear restated in 2021_12, since its detail check passes there (inferred from `:141-161`) |
| Prior-year columns agree with the earlier edition's current column | Industry | No | Later editions carry "slightly revised comparison values" (notebook cell 14). 2023_12 Table 2 values recur in the next release (`config/semantics.yml:3772-3773`) |
| Three monthly values sum to the quarter; FYTD(m) = FYTD(m-1) + month(m) | Industry | No | Unknown |

**Acknowledgment records.** There are six, all `acknowledge_totals` (vertical total residuals), all residency. Industry has none. Neither series has reviewed-cell records.

| Edition | Table | Acknowledged cells | Lines |
|---|---|---|---|
| 2020_12 | summary | 2 (2020 $, 2019 $) | `config/layouts/collections-tax-details.yml:64-86` |
| 2020_12 | detail | 4 (2020 accounts and $, 2019 accounts and $) | `:87-111` |
| 2021_12 | summary | 2 | `:120-140` |
| 2021_12 | detail | 2 | `:141-161` |
| 2022_12 | summary | 1 (2020 $) | `:170-190` |
| 2022_12 | detail | 1 (2020 $) | `:191-211` |

That is 12 acknowledged cells from 4 root source discrepancies. A new design that adds the parent and component check must also acknowledge the 2022_03 case.

## 6. Row labels and entities

The registry has 55 entities: 22 industries, 30 sub-industries with `parent_id`, and 3 totals (`config/entities.yml:3360-3687`). It lists 14 aliases. All 52 industry and sub-industry entities appear in all 107 industry reports (notebook cell 5). Residency shows only two label variants: a truncated schools label and a spaced federal label. No renames, merges or splits appear in either series.

| Kind | Labels | Lines |
|---|---|---|
| Real wording change | Manufacturing "& factories"; TIPS, PRISM/TIPS, PRISM | `config/entities.yml:3369-3373, 3426-3427` |
| Publisher spelling | "Metal Manaufacturing", "Health Practioners" | `:3532, 3552` |
| Truncated | "Elementary, Secondary Schools (except public" | `:3587` |
| Doubled text layer | "Nursing&Personal Nursing & Personal CareFacilities Care Facilities", "Total from Taxpayer p y Database ( (TIPS) )" | `:3567, 3373` |
| OCR or split words | "DNovors", "Food & Bevera ge", "Gov 't ... Offic e) seenote" | `:3553, 3518, 3680` |
| Footnote mark in label | "Federal Gov't (includes US Post Office) see note" | `:3679` |

Entities are scoped to these two families so "Education" and "Insurance" do not collide with agencies (`:3355-3359`). The same hierarchy is shared by both series (`families:` on every entry). Citywide wage tax appears in monthly City collections and QCMR cash, on a different basis (`config/entities.yml:2-27, 1763-1779`). No cross-family identity is declared.

## 7. Values

- Dollars are whole USD; scale 1 (`config/semantics.yml:3720-3723, 3338-3341`).
- Shares and rates are percent. The old engine detects them as bare decimals bounded near 100, which suggests some print without a % sign (`config/layouts/collections-tax-details.yml:52`; `tables/reconciliation_columns.py:70-105`). That suggestion is an inference.
- Distinct accounts are a count, additive across industries in 2021_12 and 2022_12 (`config/semantics.yml:3482-3485`).
- Negative format, dashes and blank cells: nothing in the config or tests is specific to this family. Unknown.
- Footnotes sit between the body and the total box in legacy tables (`config/layouts/collections-tax-details.yml:53-55`). The residency federal footnote concerns 2020 and 2019 government data (`source-observations.json:15`).

## 8. Editions and revisions

- **Reused URLs.** phila.gov replaced the bytes at an attachment URL and linked it from a newer annual page. The older page then points at the newer report (`wage_tax_industry.py:158-165`). Two editions were recovered from the Wayback Machine: 2022 Q4 and 2024 Q1 (notebook cell 14).
- **The guard.** All listing pages are scanned. The newest `page_year` keeps the URL and older listings become aliases (`wage_tax_industry.py:166-183`). Each alias is recovered from the earliest Wayback capture whose text names "wage tax by industry", the title months and the FYTD year (`:239-266`).
- **Guard placement.** Only the CLI runs it (`commands/collections.py:233-291`). Source sync builds each page separately with no dedupe or recovery (`phila_source_sync.py:93-102`). A reused URL then fails the in-PDF period check (`wage_tax_industry.py:288-290`) instead of being recovered.
- **Timestamp is not the period.** The FY2026 July to June report sits at a URL stamped 20250211 (`docs/philly-source-monitoring-audit-2026-09-11.md:55-58`).
- **Same-period revisions.** On one listing the last link wins (`wage_tax_industry.py:136-148`; `wage_tax_residency.py:63-66`). No real revised attachment is named anywhere; the tests use invented ones.
- **Industry overlap.** Later editions restate prior-year comparison columns. No canonical rule exists; the status is `unresolved` (`config/semantics.yml:3715, 3779, 3811`).
- **Residency overlap.** The rule is newest edition per value year. Summary: 2019 from 2021_12, 2020 from 2022_12, 2021 to 2023 from 2023_12. Detail: 2019 from 2021_12, 2020 to 2022 from 2022_12. 2020_12 is evidence only (`config/semantics.yml:3346-3349, 3390, 3452, 3463, 3486, 3548, 3613`).

## 9. Quirk ledger

| Id | What happens in the document | Old handling | Kind |
|---|---|---|---|
| WAGE-Q01 | Industry listings are one page per year; 2016 uses an unprefixed slug | `wage_tax_industry.py:90-93` | inherent |
| WAGE-Q02 | Page year is calendar in old pages and fiscal in new ones | `commands/collections.py:231`; `phila_source_sync.py:205` | inherent |
| WAGE-Q03 | Each link appears twice; the icon anchor is untitled | `phila_media.py:386-390` | inherent |
| WAGE-Q04 | Oldest files are named `Wage_YYYYMM.pdf` | `wage_tax_industry.py:32, 113-115` | inherent |
| WAGE-Q05 | Modern filenames omit the year; the title holds it | `wage_tax_industry.py:96-128` | inherent |
| WAGE-Q06 | FY2026 Q1 is titled July to September but named July to June | `wage_tax_industry.py:105-110`; `tests/test_wage_tax_industry.py:89-98` | inherent |
| WAGE-Q07 | "FY2026" titles put July to December in calendar 2025 | `wage_tax_industry.py:119-121` | inherent |
| WAGE-Q08 | Unrelated PDFs can share the listing page | `wage_tax_industry.py:141-143`; `wage_tax_residency.py:70-74` | inherent |
| WAGE-Q09 | A corrected attachment may follow the original for one period | `wage_tax_industry.py:136-148`; `wage_tax_residency.py:63-80` | unsure: no real case is named; a listing archive would settle it |
| WAGE-Q10 | A media URL was reused with new bytes; old pages point at the newer report (2022_12, 2024_03) | `wage_tax_industry.py:158-183` | inherent |
| WAGE-Q11 | Lost editions survive only in the Wayback Machine | `wage_tax_industry.py:186-266`; `commands/collections.py:265-291` | inherent |
| WAGE-Q12 | Reuse guard lives only in the CLI; source sync skips it | `commands/collections.py:233-291`; `phila_source_sync.py:93-102` | artifact: per-command orchestration |
| WAGE-Q13 | URL timestamp predates the report it serves | `docs/philly-source-monitoring-audit-2026-09-11.md:55-58` | inherent |
| WAGE-Q14 | Downloaded bytes must state the listed period inside the PDF | `wage_tax_industry.py:239-253, 288-290` | inherent |
| WAGE-Q15 | The period validator needs a text layer; 2023_12 is scan only | `wage_tax_industry.py:226-236` | unsure: run the validator on the 2023_12 bytes |
| WAGE-Q16 | `--list` once downloaded Wayback PDFs | fixed at `commands/collections.py:266`; `tests/test_cli_workorders.py:112-135` | artifact: alias block ran before the list check |
| WAGE-Q17 | Validation once ran after replacing the file | fixed at `wage_tax_industry.py:283-303` | artifact: path-keyed install |
| WAGE-Q18 | Residency ingest has no in-PDF check | `wage_tax_residency.py:99-111` | artifact: copied ingest helper |
| WAGE-Q19 | Monthly era to 2021_02, quarter ends from 2021_03 | `temporal_contracts.json:67-101` | inherent |
| WAGE-Q20 | 2021_03 may be a month or a quarter; the notebook sums it as a month | notebook cell 6; `temporal_contracts.json:91-93` | unsure: read the 2021_03 title |
| WAGE-Q21 | Temporal contracts stop at 2026 and name roles the family lacks | `temporal_contracts.json:72-75, 93` | artifact: copied contract |
| WAGE-Q22 | Chart pages have no table title | `config/page_types.yml:897-899, 935` | inherent |
| WAGE-Q23 | Table numbers change meaning by era | `config/page_types.yml:899-934` | inherent |
| WAGE-Q24 | Table 1 is FYTD in July to September and July to December reports; only the header says FYTD | `config/page_types.yml:921-925` | inherent |
| WAGE-Q25 | Title spacing and wording vary ("Industry-", "thru", "2nd Quarter (Apr, May, Jun)") | `config/page_types.yml:915-920` | inherent |
| WAGE-Q26 | Bare "Table 2" maps to an unpublished type | `config/page_types.yml:929-931`; `config/semantics.yml:3816` | unsure: list page titles across the corpus |
| WAGE-Q27 | Five typed subsets mix table number and period | `config/page_types.yml:906-934` | artifact: types named by table slot |
| WAGE-Q28 | Marker pattern that never matches | `config/page_types.yml:904, 963` | artifact: QCMR marker classifier |
| WAGE-Q29 | Two tables of the same type in one PDF would be pooled | `page_table_scoping.py:543-552` | unsure: check whether any edition has two quarter or two CYTD tables |
| WAGE-Q30 | Year captions fall outside the detected region | `config/semantics.yml:3761-3769, 3379-3385` | artifact: geometric region starts at first data row |
| WAGE-Q31 | 2023_12 Table 2 prints "Oct-Dec 2024" for Oct-Dec 2023 | `config/semantics.yml:3771-3808` | inherent |
| WAGE-Q32 | The misprint needs a whole profile copy to be visible | `config/semantics.yml:3777-3808`; `tests/test_semantics.py:287-298` | artifact: no per-edition note |
| WAGE-Q33 | 2024_09 labels July to September as FYTD 2025 | notebook cell 14 | inherent |
| WAGE-Q34 | FYTD tables use the July to June year; quarter and CYTD use the calendar year | `config/semantics.yml:3732`; `normalization.py:651-654` | inherent |
| WAGE-Q35 | A printed FYTD range may contradict the assigned year | `normalization.py:234-250`; `semantics.py:226-260` | inherent |
| WAGE-Q36 | Totals sit in a ruled box below footnotes | `config/layouts/collections-tax-details.yml:53-56`; `tables/region_detection.py:331-414` | inherent |
| WAGE-Q37 | Percent columns may print without % | `config/layouts/collections-tax-details.yml:52`; `tables/reconciliation_columns.py:70-105` | unsure: inspect a page |
| WAGE-Q38 | Six parents followed by sibling sub-industry rows | `config/layouts/collections-tax-details.yml:28-40`; `tables/reconciliation_rows.py:273-330` | inherent |
| WAGE-Q39 | Sub-industries are published as their own series | `config/layouts/collections-tax-details.yml:41-44` | inherent |
| WAGE-Q40 | Two closing totals; FAMIS does not sum the rows | `config/layouts/collections-tax-details.yml:45-51` | inherent |
| WAGE-Q41 | Database total label changes TIPS, PRISM/TIPS, PRISM | `config/entities.yml:3369-3373` | inherent |
| WAGE-Q42 | Manufacturing label changes | `config/entities.yml:3423-3427` | inherent |
| WAGE-Q43 | Labels damaged by doubled text, OCR or truncation | `config/entities.yml:3518, 3553, 3567, 3587, 3680` | unsure: doubled text is inherent; OCR spellings depend on the OCR run |
| WAGE-Q44 | Footnote mark inside a label ("see note") | `config/entities.yml:3679-3680` | inherent |
| WAGE-Q45 | Generic labels collide with agency names | `config/entities.yml:3355-3359` | inherent |
| WAGE-Q46 | 2022_03 Health and Education components miss their parents by equal and opposite amounts | not handled; notebook cell 14 | inherent |
| WAGE-Q47 | Later industry editions restate prior-year columns | `config/semantics.yml:3715`; notebook cell 14 | inherent |
| WAGE-Q48 | Wage tax comment sits above the realty profile | `config/semantics.yml:2830-2834` | artifact |
| WAGE-Q49 | Residency reports overlap by calendar year | `wage_tax_residency.py:3-13`; `tests/test_wage_tax_residency.py:33-58` | inherent |
| WAGE-Q50 | Residency titles list years in either order ("2020, 2019") | `wage_tax_residency.py:50-58` | inherent |
| WAGE-Q51 | Residency page title says "by Industry", not residency | `config/page_types.yml:967, 970` | inherent |
| WAGE-Q52 | Residency column count differs by edition | `config/semantics.yml:3350, 3391, 3490, 3549` | inherent |
| WAGE-Q53 | Year per column given by right-to-left offsets, not the header | `config/semantics.yml:3373, 3428-3445, 3588-3606` | artifact: header years not read |
| WAGE-Q54 | 2023 edition has no detail page | `config/page_types.yml:957-960` | inherent |
| WAGE-Q55 | Newest edition supplies each year | `config/semantics.yml:3346-3349, 3390, 3452, 3463, 3548, 3613` | inherent |
| WAGE-Q56 | 2020 combined total +112,762, repeated in three editions | `config/layouts/collections-tax-details.yml:64-211` | inherent |
| WAGE-Q57 | 2019 combined total -448, repeated in two editions | `config/layouts/collections-tax-details.yml:64-161` | inherent |
| WAGE-Q58 | 2020 edition account totals off by -11,545 and -11,451 | `config/layouts/collections-tax-details.yml:87-111` | inherent |
| WAGE-Q59 | Per-edition layout profiles repeat five settings to carry acks | `config/layouts/collections-tax-details.yml:57-63, 112-118, 162-168` | artifact: no profile inheritance |
| WAGE-Q60 | Acks pinned by row, column and table index, hypothesis name and fingerprints | `config/layouts/collections-tax-details.yml:64-211` | artifact: engine identity scheme |
| WAGE-Q61 | 2022_12 detail Total sits at row 53, elsewhere 52 | `config/layouts/collections-tax-details.yml:175, 196` | unsure: look at the 2022_12 detail page |
| WAGE-Q62 | Residency catalog says FY2021 to FY2023 and monthly; the data are calendar 2019 to 2023, annual | `docs/site/data/index.md:42, 298` | artifact: generic fiscal-year catalog |
| WAGE-Q63 | Industry monitoring starts 2026; older completeness unknown | `config/source_sync.yml:11-12`; `config/admin.yml:35` | artifact |

## 10. Old code that serves this family

| Job | File and lines | Size | Keep as |
|---|---|---|---|
| Acquisition | `wage_tax_industry.py` | 304 | Code: title period parse, alias detection, Wayback recovery, in-PDF check |
| Acquisition | `wage_tax_residency.py` | 111 | Code: year-range parse (50-80); rest replaced by the archive |
| Acquisition | `commands/collections.py:197-366` | 170 | Knowledge: the guard's order (scan all pages, dedupe, recover); its logic belongs in `watch` |
| Acquisition | `phila_source_sync.py:93-102, 117-126` | 20 | Knowledge only |
| Acquisition | `phila_media.py:361-399` | 39 | Code: titled-link parser |
| Page typing | `config/page_types.yml:897-935, 957-971` | 54 | Knowledge: title patterns and order |
| Layout | `config/layouts/collections-tax-details.yml:26-223` | 198 | Knowledge: hierarchy, two totals, 6 acks as page-cited records |
| Semantics | `config/semantics.yml:3326-3619, 3713-3843` | 425 | Knowledge: column order, units, year offsets, canonical years |
| Entities | `config/entities.yml:3355-3687` | 333 | Data: moves almost whole |
| Temporal | `temporal_contracts.json:67-113` | 47 | Knowledge only |
| Engine | `tables/reconciliation_rows.py:273-330`, `tables/reconciliation_columns.py:70-105`, `tables/region_detection.py:331-414` | about 175 | Knowledge: components, percent exclusion, total box |
| Tests | `test_wage_tax_industry.py` 267, `test_wage_tax_residency.py` 141 | 408 | Code: listing and recovery tests move with the module |
| Tests | parts of `test_page_types.py`, `test_semantics.py`, `test_entities.py`, `test_phila_source_sync.py`, `test_cli_workorders.py` | about 180 | Knowledge: their title strings become parser fixtures |

## 11. The least a parser needs

Inputs: the PDF bytes, the listing title, the listing page year, and the source (publisher or Wayback).

Industry steps:
1. Read the period from the listing title. Fall back to a `YYYYMM` filename. Check that the PDF text names the same months and FY.
2. On each page, find a "Table N" title. Skip pages without one.
3. Set period kind from the title words; if absent, from a header line containing "FYTD".
4. Take rows from the first industry label to the last total label, rejoining a total box below footnotes.
5. Map each row to one of 55 entities through a family-scoped alias table. Mark sub-industries by parent block.
6. Split nine value columns in fixed order.
7. Set the value year: July to June year for FYTD, calendar year otherwise.

Residency steps:
1. Read the year range from the title, either order.
2. Find the Summary and Detail pages by title.
3. Pick the column layout by edition: 10/16, 17/18, or 17 only.
4. Assign years from the printed headers, newest first.
5. Mark each value year canonical when this is the newest edition that covers it.

Era parameters: page year basis; period kind per table; total label; residency column layout; the 2023_12 header correction.

Checks to declare:
- 22 industries sum to the database total, per dollar column.
- Each parent equals its sub-industries.
- Current minus prior equals the difference of the dollar columns.
- Each rate matches its dollars within rounding.
- Residency: industries sum to Total for dollars and accounts.
- Residency: resident plus nonresident shares equal 100.
- Residency: resident plus nonresident dollars equal combined.
- Repeated residency years match across editions, or carry an acknowledgment.

## 12. Unknowns

- Text-layer status of every edition except 2023_12.
- Whether 2021_03 is a month or a quarter report.
- Which monthly reports carry Tables 3 and 4, and whether Table 2 ever prints without a period word.
- When TIPS became PRISM/TIPS and PRISM, and when the Manufacturing label changed.
- How negatives, dashes and blanks print.
- Whether percents print with a % sign.
- Whether any industry table spans two pages.
- How often the rate and difference columns break, and how large later restatements are.
- Whether the FAMIS total matches City wage tax in the monthly City collections report.
- Which URLs were reused, beyond the two editions the notebook names.
- Whether the current 2023_12 bytes would pass the period validator.
- Why the 2022_12 detail Total sits one row lower.
