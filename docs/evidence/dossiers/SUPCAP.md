# SUPCAP: Philadelphia supplemental reports, capital tables and the documents

Family: `phila_supplemental_report`, FY2003 to FY2024, 10 documents. This dossier covers the
three capital tables (`supplemental_capital_activity`, `supplemental_capital_prior`,
`supplemental_capital_summary`) and the report as a document. The six operating and revenue
tables are covered elsewhere. Paths drop `packages/gov-budget-etl/src/gov_budget_etl/`.
"yml" alone means `config/layouts/supplemental-report.yml`.

The checkout has no PDFs and no artifacts. Everything below comes from config, code, tests,
docs, release notes and acknowledgment records. Each claim marked "unverified" needs a PDF.

## 1. Documents

**What the report is.** The City's audited "Supplemental Report of Revenues and Obligations",
published by the Office of the Director of Finance (`docs/philly-source-monitoring-audit-2026-09-11.md:8,42`).
One PDF per fiscal year. The operating part is Schedules I-A to I-O and Exhibit I-A. The capital
part is Schedule II-A (capital summary) and Schedule II-A-1 (capital activity)
(yml:906, 947; `docs/investigations/unverified-row-audit/source-observations.json:22-23`).
The schedule for the prior-years capital statement is not recorded anywhere.

**Editions in the corpus.** Ten files under `data/phila/supplemental-report/FY<yy>.pdf`
(`tests/test_audit.py:1020`, `docs/investigations/unverified-row-audit/CASES.md:27`).

| Edition | SHA-256 (prefix) | Where recorded | Pages known to hold content |
|---|---|---|---|
| FY03 | 050d09fe4211 | yml:869 | p32 (I-D-5) |
| FY04 | not recorded | CASES.md:27 | p83 = printed 74 (II-A-1) |
| FY05 | d1001cdd126b | yml:28 | p75 to p84 (II-A-1, grand total on p84) |
| FY10 | b1fa884e591c | yml:391 | p21, 22, 24 (I-D-2), p77 (I-O-1) |
| FY15 | e87c1aeeca41 | yml:298 | p59 (I-J-1) |
| FY20 | c76260bc0b4a | yml:145 | p12 (I-C), 23, 32, 51 to 53, 77 = printed 69 |
| FY21 | edbf962eaf78 | yml:77 | p29 = printed 21, p49, 51, 75 = printed 67, 76, p87 (II-A) |
| FY22 | 00ebb3acdd78 | yml:101 | p25, 49, 51 |
| FY23 | ae4800ec4c32 | yml:124 | p25, 53, 57, p93 = printed 85 (II-A), p96 = printed 88 (II-A-1) |
| FY24 | 500479016b4f | yml:208 | p51, 52, 53 |

**Missing years.** FY2006 to FY2009, FY2011 to FY2014 and FY2016 to FY2019 are absent:
12 of the 22 years. Nothing in the repo says why. `config/admin.yml:1-10` declares no expected
documents and gives this family no source monitor or coverage note, unlike QCMR. A notebook
says the reports "are available at milestone years rather than as a continuous annual run"
(`notebooks/philadelphia_budget_trends.ipynb`, supplemental markdown cell). No source backs
that claim. The five consecutive editions FY20 to FY24 contradict it. The pattern
(03, 04, 05, 10, 15, 20 to 24) looks like a manual sample, not a publisher gap. Unverified.

**How the PDFs entered.** No module acquires this family. `grep -i supplement` over
`phila_media.py`, `documents.py`, `source_catalog.py` and `publisher_sources.py` returns nothing.
The monitoring audit says "No dedicated detector/acquirer; generic import is available"
(`docs/philly-source-monitoring-audit-2026-09-11.md:42`). The generic path is
`gbd import-source <pdf> <dest> --url ...` (`commands/evidence.py:65-131`, `source_import.py:1`),
which writes the PDF and a SHA-bound provenance sidecar. Whether the 10 files have sidecars is
not recorded. The scheduled sync excludes the family (`docs/source-sync.md:31-32`). The git
history is one squashed commit, so it shows nothing.

**Publisher listing.** The audit names the Finance reports page and its document-finder feed,
post 151831, as the listing (`docs/philly-source-monitoring-audit-2026-09-11.md:90-91,139-141`).
QCMR and budget detail read the same feed (`qcmr.py:48-53`, `budget_details.py:46`,
`phila_source_sync.py:23`). The category title for the supplemental report is not recorded.
Whether the feed lists the missing years is not recorded. The FY2025 edition was seen at
`admin.phila.gov/media/20260828133324/2025-Supplemental-Report-Final.pdf`, publisher date
August 28, 2026, 123 pages, cover "fiscal year ended June 30, 2025", missing locally
(audit doc lines 42, 61-62). Lag from year end to posting is therefore about 14 months for FY2025.
A notebook says "February following the fiscal year" (`notebooks/audited_vs_books.ipynb`, first cell).
The two claims disagree.

**Scans and text layers.** No config entry routes this family to Textract or to the LLM tier.
`grep textract config/` hits only QCMR cash. Every cited extraction for this family names
the `geometric` backend, which reads pdfplumber words: FY04, FY21, FY23
(`CASES.md:27-28,44-45`) and FY20 (`docs/investigations/release-readiness-policy/trace_cases.py:21`).
The FY10 acknowledgment uses `items_since_bold_parent_section` (yml:433), which needs font
weight, so FY10 has a text layer with fonts (`tables/totals.py:1846-1879`).
FY03, FY05, FY15, FY22 and FY24 have no recorded backend. Old editions use all-caps titles
(`tests/test_page_types.py:825,869-871`), which says nothing about scanning. The phrase
"These scans" at `config/page_types.yml:735` refers to the regexes, not to scanned pages.

**Page count and table pages.** Only FY2025 has a recorded page count (123). PDF page
numbers run 8 or 9 ahead of printed folios (FY04 +9, FY20, FY21, FY23 +8). Capital
schedules follow the operating schedules: summary near p87 to p93, activity from p75 (FY05)
or p96 (FY23) to an unknown end page.

## 2. Tables

All three are typed by statement title and stitched into one grid per document
(`config/semantics.yml:711,776,815`; `tests/test_supplemental_capital_semantics.py:8-18`).

**supplemental_capital_activity** (Schedule II-A-1). Title "Statement of Capital Budget
Activity", or "STATEMENT OF 2005 CAPITAL BUDGET ACTIVITY" with the year (`config/page_types.yml:722`;
`tests/test_page_types.py:823-826`). A row is one capital project or project-year inside a budget
agency. Nine money columns, left to right: Original Authorizations, Net Adjustments, Final
Authorizations, Amount Not Financed, Net Available, Encumbrances, Expenditures, Total
Obligations, Ending Net Available (`config/semantics.yml:712-731`). Newer editions add a leading
numeric column (budget year or project number) before the nine (`semantics.yml:700-702`;
`tests/test_semantics.py:194-195` uses 10 numeric columns). Hierarchy: budget agency banner,
category banner such as "Buildings and Facilities-Other", project rows, "Subtotal <category>:",
agency subtotal, then "Totals - All Budget Agencies" (yml:11,33). Size: FY05 runs PDF p75 to p84
with row index 725 on the grand total (yml:38). One FY23 department subtotal sums 223
project rows (`CASES.md:28`). Project labels: "Runway 17-35 Restoration of Crown and
Grade-FY2001" in FY04, codes like "07-ITEF-CD8" in FY23 (`source-observations.json:22-23`).

**supplemental_capital_prior.** Title "Statement of Prior Years' Activity" or "Statement of
Prior Years' Capital Budget Activity" (`page_types.yml:719`; `tests/test_page_types.py:822`).
Four money columns: Beginning Encumbered Authorizations, Expenditures, Financed Authorizations
Merged, Ending Encumbered Authorizations, after one or more leading budget-year values
(`semantics.yml:769-786`; `tests/test_semantics.py:192-193` uses columns 1,3,4,5,7). No
acknowledgment, test page or render exists for this table. Row grain, hierarchy and size are
unknown.

**supplemental_capital_summary** (Schedule II-A). Title "Summary Statement of Capital Budget
Activity" (`page_types.yml:716`). A row is one budget year within a fund group. Columns: budget
year (numeric, leftmost), then Adjusted Authorizations Available, Expenditures, Encumbrances,
Total Obligations, Financed Authorizations Merged During the Period (`semantics.yml:816-827`;
`tests/test_semantics.py:196-199`). The header carries a date such as "6-30-21"
(yml:906). Rows run in strictly descending budget years from the reporting year to about 1998
(FY21 ends at 1998, yml:908). Then a subtotal ("Subtotal Funds:"), the Industrial & Commercial
Development Fund printed as N/A, and an all-funds total (yml:939-941). About 28 rows: the
subtotal is row 27 in FY21 and FY23 (yml:921,957).

## 3. Format eras

| Era | Editions | Evidence | What changes |
|---|---|---|---|
| Caps headers | FY03 to about FY05 | `tests/test_page_types.py:869-875` | "CITY OF PHILADELPHIA", fund in caps, "(Amounts in USD) Schedule I-D-5" on its own line |
| Title-case headers | FY10 onward (FY10, FY24 tested) | `tests/test_page_types.py:838-860,883-899` | "City of Philadelphia Schedule I-D-2"; units beside the period |
| Year in activity title | FY05 at least | `tests/test_page_types.py:825` | "STATEMENT OF 2005 CAPITAL BUDGET ACTIVITY" |
| Prior title short form | edition unknown | `tests/test_page_types.py:822` | "Statement of Prior Years' Activity" without "Capital Budget" |
| Activity without leading column | FY04, FY05 | yml:14,36 (Original is column 1); `CASES.md:27` (encumbrance is c6) | Project year sits in the label ("-FY2001") |
| Activity with leading column | FY23, test for FY24 | `CASES.md:28` (Amount Not Financed is c5); `tests/test_semantics.py:194` | Leading numeric column before the nine measures; project codes |
| Summary units missing | "later" editions | `tests/test_semantics.py:1926-1931` | No unit context captured on capital summary pages |
| Summary title variant | none seen | `page_types.yml:716` | Single title |

The FY10, FY15 and FY20 activity layouts are not recorded. The switch between the two
activity eras lies somewhere between FY05 and FY23.

## 4. Finding the table

**Today.** Each page is parsed. No page prints a marker code, so `marker_line_pattern` is a
dummy (`page_types.yml:685`). The page type comes from the first declared title regex that matches
any line, case-insensitive, in declaration order (`page_types.py:1171-1184`). Pages with no title
(cover, contents, notes) fall to `default_extract: evidence_only`, parsed but never stitched
(`page_types.yml:723`; `page_types.py:71`). Within a page, `split_zones` cuts at each title so
stacked statements on old pages do not pool (`page_types.yml:771-791`). Region detection uses
whitespace consensus with a two-row bridge (yml:961; `parsers/geometric_backend.py:1025-1027`).
Pages of one type stitch into one grid; sparse pages are re-binned onto the densest page's
columns (`stitching_stage.py:579-580`; `tables/stitching.py:917-946`). Header context
(entity, schedule, title, period, units, fund) is read from the lines above the rule
(`page_types.yml:730-747`).

**Simplest reliable rule.** A capital page is one whose header block holds one of three titles
and a "Schedule II-A" or "Schedule II-A-1" locator. Pages run contiguously from the first
title match to the last. The table region starts below the column caption rows and ends above
the folio "- N -". Columns are fixed per era from the caption words, not detected per page.
No LLM and no Textract are needed on the evidence available. That holds for FY04, FY05, FY21 and
FY23 capital pages and is unverified for the other six editions.

## 5. Arithmetic that holds

| Check | Table | Evidence it holds | Source breaks it |
|---|---|---|---|
| Original + Net Adjustments = Final | activity | yml:44-46 (FY05 grand total exact) | none recorded |
| Final - Amount Not Financed = Net Available | activity | S19, S20 rows consistent (`source-observations.json:22-23`) | unverified |
| Encumbrances + Expenditures = Total Obligations | activity, summary | yml:897-899, 938-939 | none recorded |
| Net Available - Total Obligations = Ending Net Available | activity | assumed from captions | unverified |
| Project rows sum to category subtotal, including fragments continued across a page | activity | yml:18 hypothesis | FY05 Original, 4,100,000 (yml:11-32) |
| Agency subtotals sum to "Totals - All Budget Agencies" | activity | yml:40 | FY05 Net Adjustments, 7,000,000 (yml:33-54) |
| Beginning - Expenditures - Merged = Ending | prior | assumed from captions | unverified |
| Prior-year rows (excluding reporting year) sum to subtotal | summary | yml:893-910, 933-950 | FY21 Encumbrances omits 1998 row, 5,949.17 |
| Subtotal + ICDF (N/A) = all-funds total | summary | yml:939-941 | none recorded |
| Summary reporting-year row vs activity grand total | cross-table | not checked by old code | unknown |
| Summary budget-year rows across editions | cross-edition | not checked by old code | unknown |

Today all horizontal identities are inferred from the data, not declared
(`tables/reconcile.py:843-875`; `tables/reconciliation_columns.py:336-372`).

**Acknowledgment records for capital tables: 4 of the family's 32.**

| Kind | Count | Records |
|---|---|---|
| Source arithmetic defect (summary) | 1 | FY21 p87 Encumbrances (yml:886-923) |
| Engine scope failure recorded as a residual (summary) | 1 | FY23 p93, three columns (yml:924-960) |
| Cross-page continuation limitation (activity) | 1 | FY05 p75 Original (yml:11-32) |
| Sparse letter-coded column limitation (activity) | 1 | FY05 p84 Net Adjustments (yml:33-54) |

None of the four carries evidence or check fingerprints. The family's other 28 records
cover operating and revenue tables: 21 revenues, 4 agency by class, 2 encumbrances by
agency, 1 summary activity.

## 6. Row labels and entities

Activity rows take their department from the agency banner: `entity_context_field: section`
(`page_types.yml:751`). 82 entities in `config/entities.yml` list `phila_supplemental_report_*`,
all departments shared with QCMR, budget detail and Budget in Brief (example lines 591-603).
No entity exists for a capital project, category or budget year. Project labels change form
between eras (Q25). The capital funds named in the summary, such as Industrial & Commercial
Development Fund, have no supplemental-scoped entity. The Capital Improvement and PICA Capital
fund entities exist (`entities.yml:510-556`) but their family scoping was not checked.
Distinct label counts are unknown without artifacts.

## 7. Values

- Whole USD with cents in the summary ("527,746,509.35", yml:948). FY05 activity amounts end in
  000 (yml:21-22, 53). Whether FY05 prints whole dollars or rounds is unverified.
- Units: "(Amounts in USD)" in the header context (`page_types.yml:732-737`). The capital
  summary profile has no unit scale and publishes no unit (`semantics.yml:808-839`).
- A dash is a blank, never a zero (`CASES.md:27,44`). Entire historical rows can be dashes
  (`tables/reconciliation_periods.py:130-141`; `release-notes/data/2026.07.29.yml:108-109`).
- "N/A" fills the Industrial & Commercial Development Fund row (yml:941).
- Negatives print in parentheses in this report ("(745.35)", yml:839). Capital negatives are
  not observed.
- Net Adjustments in FY05 carry letter codes beside some values (yml:43).
- Budget years print as plain integers in a numeric column and must not be summed
  (`tables/reconciliation_columns.py:225-263`).

## 8. Editions and revisions

Each edition is a single audited statement for one fiscal year. No reissue, overlap or reused
URL is recorded for this family. The summary restates every prior budget year in each edition,
so budget year 2015 appears in every later edition with updated cumulative values (inferred
from yml:906-908). The old code has no canonical-value rule across editions for capital
tables. Fiscal year comes from the file name, not from the printed period
(`documents.py:150-155`). Capital tables were published (`docs/site/data/index.md:201-209`)
but excluded from the readiness scope (`config/readiness.yml:20-24`;
`release-notes/data/2026.08.02.yml:80-83`).

## 9. Quirk ledger

| Id | What happens in the document | Where the old code handles it | Kind |
|---|---|---|---|
| SUPCAP-Q01 | No acquirer; PDFs entered by hand or by `import-source`. Listing is the Finance document-finder feed, post 151831 | `commands/evidence.py:65-131`; audit doc:42,90-91 | inherent |
| SUPCAP-Q02 | 12 of 22 years absent (FY06 to 09, FY11 to 14, FY16 to 19); reason unrecorded | `config/admin.yml:3-10` declares nothing | unsure: read the feed's supplemental category |
| SUPCAP-Q03 | Fiscal year taken from file name FY24.pdf; printed "For the Fiscal Year Ended June 30, YYYY" never checked | `documents.py:150-155` | artifact: identity from paths |
| SUPCAP-Q04 | Next edition posts about 14 months after year end; FY2025 is 123 pages | audit doc:42,61-62 | inherent |
| SUPCAP-Q05 | PDF page = printed folio + 8 or 9; folio prints as "- N -" | `page_types.yml:766` | inherent |
| SUPCAP-Q06 | No marker code; the statement title is the only page type signal | `page_types.yml:683-722`; `page_types.py:1145-1149` | inherent |
| SUPCAP-Q07 | Title variants: year in activity title, caps, prior title with or without "Capital Budget", straight or curly apostrophe | `page_types.yml:719,722`; `tests/test_page_types.py:811-836` | inherent |
| SUPCAP-Q08 | Type chosen by first matching rule in list order; comments warn order matters | `page_types.yml:681-682`; `page_types.py:1179-1183` | artifact: regex search over every line |
| SUPCAP-Q09 | Cover, contents and note pages carry no title | `page_types.yml:723` | inherent |
| SUPCAP-Q10 | Older reports stack several statements on one page | `page_types.yml:771-786` | unsure: whether any capital page stacks |
| SUPCAP-Q11 | Two header layouts: caps with units and schedule on one line, then title case with units beside the period | `page_types.yml:730-737`; tests 838-881 | inherent |
| SUPCAP-Q12 | Capital statements print no fund banner | `page_types.yml:798-812` | inherent |
| SUPCAP-Q13 | Capital summary pages lose or lack unit context; table published unitless | `semantics.yml:808-839`; `tests/test_semantics.py:1926-1931` | unsure: render a late summary page header |
| SUPCAP-Q14 | Activity gains a leading numeric column in a later era | `semantics.yml:700-702`; yml:14 vs `CASES.md:28` | inherent; era boundary unknown |
| SUPCAP-Q15 | Roles mapped from the right edge, leading columns left unknown | `semantics.yml:712-731,777,816` | artifact: no per-era column declaration |
| SUPCAP-Q16 | Sparse page detects one fewer column; fragments re-binned onto densest page | `semantics.yml:703-706,711`; `stitching_stage.py:579-580`; `tables/stitching.py:917` | artifact: whitespace column detection |
| SUPCAP-Q17 | Two value-less banners (agency, category) sit between money rows | yml:911-915,961; `parsers/geometric_backend.py:1025-1027` | artifact of region detection; the stacked banners are inherent |
| SUPCAP-Q18 | `bridge_region_gaps` is documented as unsafe for stacked Philly schedules, yet set for a family with stacked pages | `layouts.py:1066-1073` vs `page_types.yml:771-773` | artifact |
| SUPCAP-Q19 | Comment about the bridge sits inside the FY21 acknowledgment | yml:911-915 | artifact: round-trip YAML writer |
| SUPCAP-Q20 | Category banner reprinted after a page break; one subtotal closes both fragments | `tables/totals.py:1370-1428`; yml:18 | inherent |
| SUPCAP-Q21 | FY05 "Subtotal Buildings and Facilities-Other:" Original 22,711,000 printed, 18,611,000 summed | yml:11-32 | unsure: render p74 and p75 and list every Original cell |
| SUPCAP-Q22 | FY05 Net Adjustments column sparse and letter-coded; grand total 7,000,000 not reproducible | yml:33-54 | unsure: list p75 to p84 adjustment cells with their codes |
| SUPCAP-Q23 | Three-level hierarchy: agency, category, project; "Subtotal X:" colon labels; "Totals - All Budget Agencies" | yml:11,33; `page_types.yml:751` | inherent |
| SUPCAP-Q24 | Very long blocks: 223 projects in one FY23 department; 726 rows in FY05 | `CASES.md:28`; yml:38 | inherent |
| SUPCAP-Q25 | Project label form changes: name with "-FY2001" suffix, then codes like "07-ITEF-CD8" | `source-observations.json:22-23` | inherent |
| SUPCAP-Q26 | Same project in several fiscal-year rows; sums can coincide | `tables/implicit_subtotals.py:219-248` | unsure: whether this family caused the guard |
| SUPCAP-Q27 | Project year in a label is not the report year | `CASES.md:27` | inherent |
| SUPCAP-Q28 | Dash means blank, not zero | `CASES.md:27,44` | inherent |
| SUPCAP-Q29 | Summary subtotal excludes the reporting-year row | yml:8-9; `tables/reconciliation_periods.py:73-198`; `tables/reconcile.py:281-298` | inherent |
| SUPCAP-Q30 | Reporting year read from a header date "6-30-21" | `tables/reconciliation_periods.py:25-61` | inherent |
| SUPCAP-Q31 | Budget year prints as both label and numeric cell | `tables/reconciliation_periods.py:64-70`; `tables/reconciliation_columns.py:225-263` | inherent |
| SUPCAP-Q32 | Summary subtotal may carry no printed label; old code synthesizes "Subtotal <section>" | `tables/reconciliation_periods.py:176-191`; `tests/test_reporting_period_subtotals.py:39` | unsure: render FY23 p93 |
| SUPCAP-Q33 | An empty historical year collapses to one dash and must not break the year run | `tables/reconciliation_periods.py:130-141`; tests 73-99 | inherent |
| SUPCAP-Q34 | Industrial & Commercial Development Fund prints N/A; all-funds total repeats the subtotal | yml:939-941 | inherent |
| SUPCAP-Q35 | FY21 Encumbrances subtotal omits the 1998 row (5,949.17) | yml:886-923; `tests/test_supplemental_source_acknowledgments.py:122-129` | inherent |
| SUPCAP-Q36 | FY23 subtotal correctly excludes 2023 but is acknowledged as a defect | yml:924-960; `tests/test_supplemental_source_acknowledgments.py:145-158` | artifact: period inference did not fire, probably because the N/A row, not a section, follows (`reconciliation_periods.py:122`) |
| SUPCAP-Q37 | Horizontal identities inferred from data | `tables/reconcile.py:843-875`; `tables/reconciliation_columns.py:336-372` | artifact |
| SUPCAP-Q38 | Role names disagree with captions ("Financed Authorizations Merged" maps to `net_authorization_adjustments`; acknowledgments say "Adjusted Financed Authorizations") | `semantics.yml:817,823`; yml:896 | artifact |
| SUPCAP-Q39 | Acknowledgments keyed by table and row ordinals and hypothesis names | yml:15-18,37-40,919-923,956-960; `tests/test_supplemental_source_acknowledgments.py:283-344` | artifact |
| SUPCAP-Q40 | Capital acknowledgments have no fingerprints | yml:10-54,886-960 | artifact |
| SUPCAP-Q41 | Capital tables published but outside the readiness scope | `config/readiness.yml:20-24` | unsure: run declared checks on all 10 editions |
| SUPCAP-Q42 | Report also holds three statement types never published: encumbrances by agency, summary encumbrances, non-budgeted obligations NOTE | `semantics.yml:3973-3986`; `page_types.yml:699-713,791` | inherent: pages must be recognized and skipped |
| SUPCAP-Q43 | Text layer present (geometric backend) in every cited edition; no Textract or LLM config | `CASES.md:27-28,44-45`; `trace_cases.py:21`; yml:433 | inherent for FY04, FY10, FY20, FY21, FY23; unsure for the rest |

## 10. Old code that serves this family

| Job | File and lines | Keep as |
|---|---|---|
| Acquisition | `source_import.py` (669), `commands/evidence.py:65-131` | Knowledge: SHA-bound sidecar idea only |
| Page typing | `config/page_types.yml:676-823` (148) | Knowledge: titles, header regexes, furniture lines |
| Semantics | `config/semantics.yml:699-839` (141), `3973-3986` | Knowledge: column captions and order |
| Acknowledgments | yml capital records 10-54, 886-960 (about 120) | Knowledge: four page-cited cases to restate |
| Period scope | `tables/reconciliation_periods.py` (205) | Knowledge: the rule, not the inference |
| Continued sections | `tables/totals.py:1370-1428` (59) | Knowledge |
| Grid reunion | `tables/stitching.py:917-` , `stitching_stage.py:579` | Neither: disappears with declared columns |
| Tests | `test_supplemental_capital_semantics.py` (18), `test_supplemental_source_acknowledgments.py` (359), `test_reporting_period_subtotals.py` (174), `test_page_types.py:811-881` | Knowledge: the title and header strings make good fixtures |

No code here moves as is.

## 11. The least a parser needs

1. Input: one PDF by SHA-256, its fiscal year read from the printed "For the Fiscal Year Ended
   June 30, YYYY" line and checked against the catalog entry.
2. Find capital pages: header holds one of three titles (Q07) and a Schedule II-A or II-A-1
   locator. Skip every other page (Q42).
3. Drop furniture: city line, title, period line, units line, "- N -" folio.
4. Pick the era from the caption words: activity with or without a leading column (Q14).
5. Bin words into fixed columns for that era. Keep labels and banners as text.
6. Classify rows: agency banner, category banner (reprinted after breaks, Q20), project,
   "Subtotal ...:", "Totals - All Budget Agencies"; for the summary, year rows, subtotal, N/A
   row, all-funds total.
7. Parse amounts: commas, cents, parentheses, dash as null, N/A as null, letter codes kept apart
   from the number (Q22).
8. Emit typed rows with page, agency, category, project label, budget year, and nine, four or five
   measures.
9. Declare checks: the horizontal identities of section 5; category, agency and grand totals for
   activity; prior-years-only subtotal for summary; subtotal plus ICDF for the all-funds row.
10. Acknowledge, by page and label: FY05 p75 and p84 (if confirmed as source facts), FY21 p87.
    FY23 p93 needs no acknowledgment under a declared prior-years rule.

Parameters by era: caps or title-case header, leading activity column yes or no, prior title form.
The hardest of the three is capital activity: longest, two column eras, continued sections, and
both open unknowns.

## 12. Unknowns

- Which editions the Finance feed lists, and why 12 years are missing.
- Whether FY03, FY05, FY15, FY22 and FY24 have a text layer on capital pages.
- The year the activity table gains its leading column, and what that column holds.
- Everything about `supplemental_capital_prior`: schedule, grain, hierarchy, identities.
- Whether the FY05 residuals are source defects or lost cells.
- Whether capital summary pages print units, and whether its subtotal prints a label.
- Page ranges and row counts of capital tables in each edition.
- Whether the summary's current-year row agrees with the activity grand total.
