# VAL: words, values and evidence across every family in scope

Paths are shortened by dropping `packages/gov-budget-etl/src/gov_budget_etl/`. Config paths start at `config/`. Every count below comes from a script run over the YAML at commit 49b59ea, or from the line cited. No PDF was opened. Sections 1 to 6 answer the six questions; sections 9 to 12 follow the dossier template.

## 1. Word sources

### 1.1 Where the choice is recorded today

The word source per edition is not declared anywhere in git. It is chosen after the fact by ranking each backend's reconciliation results. The winner is written to `artifacts/validation/authoritative_artifacts.json`, which is not in the checkout.

- The ranking key is assertion inventory, then retained row count, then readiness, then a fixed backend preference, then pass ratios (`reconciliation_status.py:393-433`). The preference order is `geometric`, `textract_geometric`, `textract`, `llm_geometric` (`reconciliation_status.py:38-43`).
- The persisted record holds only `document_id`, `backend` and an optional empty reason (`artifact_selection.py:88-117`).
- `config/layouts.yml` and the per-family layout files never name a word source for a whole edition. They name a parser only inside individual review records (`parser_name`, `primary_parser`, `evidence_parser`).

So arithmetic picks the word source. That is the mechanism that would have picked the wrong source for QCMR cash FY07 Q4 (section 1.3).

### 1.2 What is known per family

The table lists every edition whose word source can be read from config, tests or the audit sample. "Text layer" is the `geometric` backend. "Textract words" is `textract_geometric` (Textract words placed by the geometric pipeline, with Textract table boxes as priors, `parsers/registry.py:26-35`). "Textract grid" is raw `textract`, which keeps Textract's own cell grid.

| Family | Editions and source | Where recorded |
|---|---|---|
| QCMR cash | FY07 Q3, FY08 Q1 to Q3: Textract words. FY07 Q4, FY09 Q2, FY25 Q2: Textract grid. FY08 Q4, FY10 Q1, FY12 Q4, FY18 Q2, FY19 Q1, FY25 Q3: text layer | `qcmr-cash.yml:72-74, 89-501, 509-690`; audit cases S21, S22 |
| QCMR positions | FY08 Q2, FY08 Q3: Textract words | audit cases S27, S28 |
| QCMR personal services | FY08 to FY13 named the "scan era"; FY14 Q4: text layer | `qcmr-personal-services.yml:2-11`; audit S25, S26 |
| QCMR obligations (O-2) | FY13 Q3: Textract grid | audit S23, S24 |
| Monthly collections, City and School | every sampled edition: text layer | audit S03 to S06 |
| Wage tax by industry | 2023-12 is "scan-only"; 2020-08 text layer | `semantics.yml:3771`; tests |
| Sales tax, BIRT, residency, realty transfer | every sampled edition: text layer | audit S07 to S12 |
| Budget in Brief | FY15: Textract words; FY09: text layer; some editions are scans ("Scan OCR can omit the terminal period") | audit S01, S02; `page_types.yml:512, 531` |
| Supplemental reports | FY04, FY21, FY23: text layer | audit S19, S20, S31, S32 |

Audit cases are rows of `docs/investigations/unverified-row-audit/CASES.md:9-36`. The full per-edition list exists only in the missing selection file.

### 1.3 Known cases where a word source was wrong

| Case | What went wrong | Record |
|---|---|---|
| QCMR cash FY07 Q4, Wage row, December, May, annual | Textract read 65.8, 108.7, 1,165.9; the text layer has 85.8, 109.7, 1,185.9. The Textract digits "happen to improve arithmetic" | `qcmr-cash.yml:72-88`; `docs/value-contract-vertical-slice-acceptance.md:22-24` |
| QCMR cash FY07 Q3, 33 cells; FY08 Q1, 1 cell | Textract dropped or replaced the decimal separator: `2100`, `266 1`, `69,2`, `67: 3`, `(29 1)` | `qcmr-cash.yml:89-387` |
| School collections 2016-04 | Overprinted text layer loses three Prior-row amounts | `collections-monthly.yml:76-93` |
| School collections 2016-11 | Overprinted text layer drops two amounts and reads 7,500,000 as 77,500,000 | `collections-monthly.yml:94-108` |
| QCMR cash FY23 Q1, Q2 | Damaged font: `E(cid:121)PENSES` | `qcmr-cash.yml:14-18` |
| QCMR cash scans | OCR label damage: "Mergere", "Hosp.tal", "lndemn~ies", "1o4.o" | `semantics.yml:1484-1487`; E09 report |

The FY07 Q4 case is the only recorded OCR digit misread where totals improved. It is not the only possible one. A one-decimal check with 12 contributors admits a residual of 0.6 (`tables/checks.py:86-92`), so a wrong tenths digit passes.

### 1.4 What a word must carry

Today `WordBox` holds text, box, confidence, font name, font size and writing direction (`models.py:279-292`). The page lives on the table (`row_pages`), the source on the table (`parser_name`), and the file hash nowhere near the word. Raw Textract grid cells carry no words and no per-cell confidence (`parsers/textract_backend.py:278-297`).

A word in the new design needs, at least:
- the SHA-256 of the publisher file and the 1-based page in that file;
- the box in PDF points with the page size and rotation it was measured in;
- the verbatim text, before any cleaning;
- the source: text layer with the PDF library version, or Textract with API configuration and render dpi (300 today, `parsers/textract_backend.py:349, 392`);
- confidence for OCR words, which two old repairs read (`tables/numeric_value_recovery.py:336-505`, thresholds 0.85 and 0.94);
- font name and size for text-layer words, since BiB revenue schedules take the owning agency from bold rows (`page_types.yml:575`);
- a stable word index on the page, and a parent index when cleanup splits a word.

Splits matter because dot-leader removal and fused-suffix splitting invent boxes by character count (`tables/text_cleaning.py:195-274`).

## 2. From words to cells

The old code runs one shared pipeline: words, cleanup, lines, line repair, column lanes, rows, then family-specific row and table repairs. Family layout options switch steps on. This table maps each step to the families that need it.

| Step | Old code | Families that need it |
|---|---|---|
| Drop `$`, dot leaders, split label fused to amount | `tables/text_cleaning.py:183-274` | all text-layer families |
| Words to lines, phrase merge | `tables/line_grouping.py:1-384` | all |
| Deskew with Textract table boxes as row prior | `tables/line_grouping.py:49-258`, `tables/region_detection.py:583-644` | QCMR scans only |
| Baseline guard on phrase merge | `qcmr-cash.yml:19-26` | QCMR cash FY08 Q1, FY08 Q4, FY14 Q1 only |
| Orphan amount lines, overprint twins, welded duplicates | `tables/line_repair.py:101-464` | monthly collections mainly |
| Labels printed above amounts | `collections-monthly.yml:18-26` | City collections 2014 to Nov 2015 |
| Column lanes by gap voting | `tables/region_detection.py:65-258`, `tables/column_detection.py` | all non-ruled tables |
| Ruled grid rebin from drawn rules | `tables/rule_grid.py`, `page_types.yml:567, 581, 815, 818` | BiB fund summary and revenue schedule; supplemental agency and fund by class |
| Split stacked grids at captions | `qcmr-cash.yml:4-18`; supplemental zone titles `page_types.yml:771-791` | QCMR cash page 1; older supplemental pages |
| Trailing ruled total box | `parsers/geometric_backend.py:510` | personal services, sales tax, wage by industry and residency |
| Bridge two-row region gaps | `supplemental-report.yml:961`, `parsers/geometric_backend.py:499` | supplemental |
| Drop LINE NO. margin | `budget-in-brief.yml:21-25`, `tables/reconciliation_rows.py:402` | BiB ruled schedules |
| Split two amounts in one cell | `tables/amounts.py:159-204`, `tables/fused_columns.py` | all |
| Stitch across pages | `tables/stitching.py` | positions (2 pages), personal services (about 15), City collections (4), BiB obligation history (8, `page_types.yml:552-555`), supplemental continued schedules |
| Header and column roles | `semantics.yml` per profile, `semantics.py` | all |

Steps every family needs: word cleanup, line grouping, a lane or ruled grid, rows with their source words, header roles and page stitching. Steps that exist for one family:
- deskew priors and baseline guards (QCMR scans);
- welded zero rows (`qcmr-cash.yml:38-49`, cash);
- labels above amounts (early City collections);
- margin line numbers (BiB) and region bridging (supplemental).

The earlier reading said the ruled grid never runs for QCMR or collections. That stays true, but BiB and the supplemental reports use it, so it is in scope now. Supplemental short tables fuse "110,626,142.01 92.31" without the drawn rules (`page_types.yml:793-796`).

## 3. Amounts

### 3.1 Formats printed, by family

| Format | Example | Families | Old handling |
|---|---|---|---|
| Thousands commas | `1,234,567` | all | `tables/amounts.py:31` strict grouping |
| One decimal in millions | `11.6`, `(3.0)` | QCMR cash | `semantics.yml` `fixed_multiplier: 1000000` |
| Cents | `828,904.89` | supplemental | `semantics.yml` "Amounts in USD" |
| Thousands, unit printed on page | "Amounts in Thousands" | BiB ruled schedules | `page_types.yml:511-514`, multiplier 1000 |
| Whole dollars | `44,646,313` | collections, O-2, tax details, BiB obligation history | fixed multiplier 1 |
| Counts | positions, records, accounts, entities | positions, personal services rows, RTT, BIRT, sales, residency | per column or per row label |
| Mixed units in one grid | "Full-Time Positions" rows are counts, "Class 100" rows are dollars | personal services | `semantics.yml` `value_scale_rules` with `row_label_patterns` |
| Parentheses negative | `(5,678)`, `(12.3%)` | all | `tables/amounts.py:35` |
| Leading minus or dash glyph | `-4.5`, en dash then `7`, `-11.0` | QCMR cash, collections | `tables/amounts.py:13-14` |
| Signed currency | `$-61,397,587`, `-$61,397,587` | collections | see VAL-Q22 |
| Dash placeholder | `-`, `--`, en dash, em dash | all | see section 3.3 |
| N/A | `N/A` | City collections 2024-04 on, PILOT | `tables/classification.py:154` |
| Percent with sign | `12.3%`, `69%`, `26.6%` | tax details, school collections | parsed as 12.3, not 0.123 |
| Bare percent | `74.98` | supplemental activity statements | statistical guess, `tables/reconciliation_columns.py:69-104` |
| Footnote mark | `242,096*`, `2.8 \``, `TOTAL TAX REVENUE *` | collections, tax details | `tables/amounts.py:25` |
| Kerning split | `1 37,332,523`, `67,215,504.0 0` | collections text layers | joined, `tables/amounts.py:76-88` |
| Spaces after commas | `10, 936, 234 (1, 130, 698)` | text layers | partition, `tables/amounts.py:159-204` |
| Amount fused to label | `TAX434,605,553`, `408,491,218 NET PROFITS TAX` | collections | `tables/text_cleaning.py:14-20`, `tables/amounts.py:215-257` |
| OCR decimal loss | `2100`, `266 1`, `69,2`, `67: 3` | QCMR cash scans | section 4 |
| OCR letters | `B`, `O`, `Q`, `D`, `&`, `(59.8j`, `:` | QCMR scans | section 4 |
| Rounded inside an exact table | FY09 BiB General Fund total printed to the nearest thousand | BiB | `budget-in-brief.yml:223-225` |

No family is known to print a trailing minus (`123-`) or a plus sign. The lexer rejects both. Superscript footnote digits are not stripped (`1,234¹` returns None).

### 3.2 Probe results

I ran a byte-identical copy of `tables/amounts.py` (diffed against the checkout) on 55 inputs. The surprising results:

| Input | `parse_amount` | `parse_decimal` |
|---|---|---|
| `12 345` | 12345.0 | 12345 |
| `1 2` | 12.0 | 12 |
| `12 345 678` | 12345678.0 | 12345678 |
| `12, 345` | 12345.0 | 12345 |
| `-$61,397,587` | None | -61397587 |
| `-`, `--`, em dash | 0.0 | None |
| `---` | None | None |
| `- 0` | -0.0 | -0 |
| `(12.3%)` | -12.3 | -12.3 |
| `+12.3%`, `123-`, `.5`, `$(1,234)` | None | None |
| `1,234 5` | None (split gives `1,234`, `5`) | None |

`12 345` is the known defect. The cause is `.replace(" ", "")` at `tables/amounts.py:123` and 145, which `_contains_separate_amount_tokens` allows when no token has a comma or point (`tables/amounts.py:64-66`). Two count cells in one lane become one unprinted number.

#### 3.2.1 Acceptance inputs for the new lexer

Section 3.2 prints 16 of the probe's 55 inputs, with the old results only, and no file holds the other 39 inputs or any new result. The owner decided on November 23, 2026 that this table is the acceptance set for the probe clause of build step 2, with the words "[u]se your list, but make row 4 unreadable." Design section 16 records it as decision 12. Rows 1 to 16 are the inputs of section 3.2. Rows 17 to 52 are the examples of the table in section 3.1, in its order, and rows 53 to 55 are examples from sections 1.3 and 2. These 39 were chosen from the examples this dossier prints. They are not the 39 inputs that the original probe ran.

Each input is split on spaces into words, and the new lexer (`checkedtables.lex.lex_cell`) reads the words as one cell of a text layer in one of four columns. The old results come from a copy of `tables/amounts.py` that `cmp` reports identical to the reference checkout on November 23, 2026. `tests/test_evidence.py` fails when this table differs from `PROBES` in `packages/checkedtables/tests/test_val_probe.py`, and `test_val_probe_inputs_give_documented_results` fails when the lexer gives another new result.

| Key | Column |
|---|---|
| M | money, decimals as printed |
| M1 | money, one decimal, the QCMR cash format |
| C | count, no decimals |
| P | percent, decimals as printed, the sign optional |

| # | Input | Old `parse_amount` | Old `parse_decimal` | Column | New result |
|---|---|---|---|---|---|
| 1 | `12 345` | `12345.0` | `12345` | C | `Unreadable two_tokens` |
| 2 | `1 2` | `12.0` | `12` | C | `Unreadable two_tokens` |
| 3 | `12 345 678` | `12345678.0` | `12345678` | C | `Unreadable two_tokens` |
| 4 | `12, 345` | `12345.0` | `12345` | M | `Unreadable two_tokens` |
| 5 | `-$61,397,587` | `None` | `-61397587` | M | `Amount -61397587` |
| 6 | `-` | `0.0` | `None` | M | `Dash no_value` |
| 7 | `--` | `0.0` | `None` | M | `Dash no_value` |
| 8 | `—` | `0.0` | `None` | M | `Dash no_value` |
| 9 | `---` | `None` | `None` | M | `Unreadable not_a_number` |
| 10 | `- 0` | `-0.0` | `-0` | M | `Unreadable two_tokens` |
| 11 | `(12.3%)` | `-12.3` | `-12.3` | P | `Amount -12.3` |
| 12 | `+12.3%` | `None` | `None` | P | `Unreadable sign` |
| 13 | `123-` | `None` | `None` | M | `Unreadable sign` |
| 14 | `.5` | `None` | `None` | M | `Unreadable grouping` |
| 15 | `$(1,234)` | `None` | `None` | M | `Amount -1234` |
| 16 | `1,234 5` | `None` | `None` | M | `Unreadable two_tokens` |
| 17 | `1,234,567` | `1234567.0` | `1234567` | M | `Amount 1234567` |
| 18 | `11.6` | `11.6` | `11.6` | M1 | `Amount 11.6` |
| 19 | `(3.0)` | `-3.0` | `-3.0` | M1 | `Amount -3.0` |
| 20 | `828,904.89` | `828904.89` | `828904.89` | M | `Amount 828904.89` |
| 21 | `44,646,313` | `44646313.0` | `44646313` | M | `Amount 44646313` |
| 22 | `(5,678)` | `-5678.0` | `-5678` | M | `Amount -5678` |
| 23 | `-4.5` | `-4.5` | `-4.5` | M1 | `Amount -4.5` |
| 24 | `–7` | `-7.0` | `-7` | M | `Amount -7` |
| 25 | `-11.0` | `-11.0` | `-11.0` | M1 | `Amount -11.0` |
| 26 | `$-61,397,587` | `-61397587.0` | `-61397587` | M | `Amount -61397587` |
| 27 | `–` | `0.0` | `None` | M | `Dash no_value` |
| 28 | `N/A` | `None` | `None` | M | `NotApplicable` |
| 29 | `12.3%` | `12.3` | `12.3` | P | `Amount 12.3` |
| 30 | `69%` | `69.0` | `69` | P | `Amount 69` |
| 31 | `26.6%` | `26.6` | `26.6` | P | `Amount 26.6` |
| 32 | `74.98` | `74.98` | `74.98` | P | `Amount 74.98` |
| 33 | `242,096*` | `242096.0` | `242096` | M | `Amount 242096 marks *` |
| 34 | `` 2.8 ` `` | `2.8` | `2.8` | M1 | `` Amount 2.8 marks ` `` |
| 35 | `TOTAL TAX REVENUE *` | `None` | `None` | M | `Unreadable not_a_number` |
| 36 | `1 37,332,523` | `137332523.0` | `137332523` | M | `Amount 137332523` |
| 37 | `67,215,504.0 0` | `67215504.0` | `67215504.00` | M | `Amount 67215504.00` |
| 38 | `10, 936, 234 (1, 130, 698)` | `None` | `None` | M | `Unreadable two_tokens` |
| 39 | `TAX434,605,553` | `None` | `None` | M | `Unreadable not_a_number` |
| 40 | `408,491,218 NET PROFITS TAX` | `None` | `None` | M | `Unreadable not_a_number` |
| 41 | `2100` | `2100.0` | `2100` | M1 | `Unreadable decimals` |
| 42 | `266 1` | `2661.0` | `2661` | M1 | `Unreadable two_tokens` |
| 43 | `69,2` | `None` | `None` | M1 | `Unreadable grouping` |
| 44 | `67: 3` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 45 | `B` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 46 | `O` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 47 | `Q` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 48 | `D` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 49 | `&` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 50 | `(59.8j` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 51 | `:` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 52 | `1,234¹` | `None` | `None` | M | `Amount 1234 marks ¹` |
| 53 | `(29 1)` | `-291.0` | `-291` | M1 | `Unreadable two_tokens` |
| 54 | `1o4.o` | `None` | `None` | M1 | `Unreadable not_a_number` |
| 55 | `110,626,142.01 92.31` | `None` | `None` | M | `Unreadable two_tokens` |

### 3.3 Three lexers and two dash meanings

There are three amount readers. `tables/amounts.py:91` serves page parsing, `tables/classification.py:25-41` adds `-$` support, and `parse_decimal` (`tables/amounts.py:137`) serves Decimal export. The classification wrapper says the page lexer was not widened because that "would invalidate every page" (`tables/classification.py:28-30`). That is a cache and fingerprint cost, not a document fact.

A dash means different things by family and column:
- City collections August 2026: dash means zero, confirmed by the maintainer (`collections-monthly-city-2026-08.yml:3-5`).
- School collections August 2026: dash means zero for one cell (`collections-monthly.yml:35-50`).
- Sales tax entity counts, supplemental encumbrances and appropriations: dash means no value (audit S09, S10, S19, S31).
- BiB FY15 prints `--` in a compensation subtotal, meaning unresolved (audit S01).
- City collections hold 3,146 dashes across 14 roles; one checked cell does not settle them all (`docs/value-contract-vertical-slice-acceptance.md:52-70`).

The page lexer returns 0.0 for `-` and `--` "to locate its column" and every export caller must re-check with `is_source_dash` (`tables/amounts.py:16-20, 96-98`). Classification treats any run of dashes as a dash (`tables/classification.py:157`), while the lexer treats `---` as text.

## 4. Value recovery

### 4.1 What runs

Ten paths can make a cell's value differ from a direct parse of its text. They run in `tables/reconcile.py:474-590` and `1290-1310`, then a gate resets every value that is not marked verified (`tables/reconcile.py:1390-1420`, `tables/reconciliation_values.py:855-902`). Verification is decided in `tables/reconciliation_values.py:418-815`.

### 4.2 Which satisfy "a published number must come from words on the page"

| Path | Digits from | Who picks | Rule met? |
|---|---|---|---|
| Reviewed fixed-decimal cell, 34 records (`tables/reconciliation_values.py:488-518`) | OCR word digits plus declared scale, checked by a person against the page | reviewer | Yes, if the record binds hash, page, box and word text |
| Reviewed value source, 1 record (`qcmr-cash.yml:72-88`) | text-layer word | reviewer | Yes |
| Column-proven fixed scale: `2100` read as 210.0 when the column itself shows one decimal (`tables/value_recovery.py:307-349`) | page digits; only the decimal point is placed | declared format | Yes, if the scale is declared per column and the word has the right digit count |
| Amount fused to label or beside a dash (`tables/numeric_value_recovery.py:45-108`; `tables/reconciliation_values.py:755-793`) | page digits | lexer | Yes |
| Two amounts split from one cell (`tables/amounts.py:159-204`) | page digits | lexer | Yes |
| Alternate word source chosen per cell because it reconciles (`tables/reconciliation_values.py:727-750`, `tables/value_recovery.py:502-576`) | page words | arithmetic | Digits yes; the choice is the FY07 Q4 hazard |
| Letter-for-digit map, `B` to 8, `O`/`D`/`Q` to 0, `&` to 6 (`tables/value_recovery.py:46-58, 289-304, 334-335`) | a guessed digit | fixed table, no review | No |
| Integer confusables `b`, `o`, `q` under a proven integer format (`tables/numeric_value_recovery.py:227-243`; `tables/reconciliation_values.py:567-590`) | a guessed digit | fixed table | No |
| One unknown letter tried as 0 to 9, arithmetic picks, rounding receipt verifies (`tables/value_recovery.py:270-286`; `tables/reconciliation_values.py:637-661`) | arithmetic | arithmetic | No |
| Low-confidence digit or sign changed to close a residual (`tables/numeric_value_recovery.py:336-505`), additive and exact-integer identity repairs (`557-617`, `800-917`) | arithmetic | arithmetic | No, but reset by the final gate unless an alternate word matches |

The last row is safe today only because of the gate. The two "No" rows with a fixed table pass the gate: they are recorded as `FORMAT_INTERPRETATION` with `value_verified=True` (`tables/reconciliation_values.py:567-584, 600-626`). The arithmetic-picked letter passes whenever a rounding receipt exists (`tables/reconciliation_values.py:656-661`).

The `2100` example shows the line. Reading `2100` as 210.0 uses only printed digits and a declared format, so it passes. Reading `85.8` as 65.8 because the total then ties writes a number the page does not show, so it fails.

## 5. Checks and acknowledgments

### 5.1 Records by family and kind

There are 215 `acknowledge_totals` records in scope. The earlier count of 174 covered QCMR and collections only; BiB adds 9 and the supplemental reports add 32. I classified each record by reading its `reason`. "Source arithmetic" means printed parts do not add to a printed total. "Source typo" means one printed cell is blank, repeated or misplaced. "Layout exception" means the check does not fit how the table is meant to add. "Extraction" means the parser, not the page, is wrong.

| Family | Records | Source arithmetic | Source typo | Layout exception | Extraction | No fingerprint |
|---|---:|---:|---:|---:|---:|---:|
| QCMR cash | 11 | 11 | 0 | 0 | 0 | 0 |
| QCMR positions | 7 | 7 | 0 | 0 | 0 | 6 |
| QCMR personal services | 2 | 2 | 0 | 0 | 0 | 2 |
| Monthly City and School collections | 77 | 70 | 2 | 3 | 2 | 62 |
| City collections August 2026 | 63 | 0 | 0 | 63 | 0 | 0 |
| Tax details (residency 6, BIRT 2, RTT 6) | 14 | 13 | 1 | 0 | 0 | 2 |
| Budget in Brief | 9 | 7 | 2 | 0 | 0 | 6 |
| Supplemental reports | 32 | 24 | 3 | 4 | 1 | 24 |
| Total | 215 | 134 | 8 | 70 | 3 | 102 |

Named members of the small kinds:
- Source typo, collections and tax: City 2018-03 blank total; City 2020-06 June total; RTT 2025-03 repeats current tax as the difference.
- Source typo, BiB and supplemental: BiB FY10 repeats 244,500; BiB FY26 leaves a change blank; supplemental FY20, FY22, FY23 print a dash on a subtotal.
- Layout exception, collections: School 2026-08 dash; City 2016-02 unitemized 5,700,000 (2 records); City 2026-08 dash columns (63).
- Layout exception, supplemental: FY05 letter-coded adjustments; FY21 cross-page FAMIS scope; FY20 self-balancing Grants fund; FY23 subtotal without the reporting year.
- Extraction: School 2016-04 and 2016-11 overprint; supplemental FY05 continued block lost 4,100,000 in stitching.

No `acknowledge_totals` record is an OCR record. OCR knowledge lives in other record types:

| Record type | Count | Family | Kind |
|---|---:|---|---|
| `reviewed_fixed_decimal_cells` | 34 (33 FY07 Q3, 1 FY08 Q1) | QCMR cash | OCR |
| `reviewed_value_sources` | 1 (FY07 Q4) | QCMR cash | OCR |
| `reviewed_column_sums` | 5 | QCMR cash | declared check |
| `reviewed_row_sums` | 12 | QCMR cash | declared check |
| `welded_zero_row_splits` | 2 | QCMR cash | OCR layout |
| `nonapplicable_operands` | 1 (City 2024-04 Parking, Valet) | collections | layout exception |
| `exclude_export_row_patterns` | 1 (City 2023-07 orphan `(359,304,205)`) | collections | source debris |
| `resolved_assertions.yml` discrepancies | 8 records, 26 cells (6 misprint, 2 omission) | BiB cross-table | source |

Several records describe one root defect. City TOTAL GENERAL FUND AND PICA is overstated in 23 editions from 2017-01 to 2019-08. The stale 63,969,133 recurs from 2020-09 to 2021-06. The residency +112,762 recurs in 2020, 2021 and 2022 releases, and the BiB District Attorney 222,029 in FY08 and FY09.

### 5.2 How records are keyed

An `acknowledge_totals` record matches when all of these agree (`layouts.py:84-123`, `covers` at `263-330`):
- the profile's document id glob and the record's `label_pattern` glob;
- `table_types`, `table_indices`, `row_indices` and `expected_column_indices`, all parser ordinals;
- `hypotheses`, the reconciler's name for the sum shape, such as `items_since_related_section+verified_subtotal_coverage+declared_difference_identity`;
- `expected_residuals` within `residual_tolerance`, stored as floats (FY16 Q3 cash stores `40.400000000000006`);
- `evidence`: document id, source SHA-256, pages and assertion page;
- two fingerprints over raw cell dumps, boxes and parser name (`tables/checks.py:777-837`).

Reviewed cells add `parser_name`, `column_index` and `extraction_text` (`layouts.py:481-530`). BiB cross-table records are keyed by meaning instead: document, fund entity, revenue category, column role and value year (`resolved_assertions.yml:139-417`). They carry no source hash.

### 5.3 Why 72 of 174 are inert, and 102 of 215

`can_cover_live_assertions` returns False unless both fingerprints are present (`layouts.py:214-231`), and `covers` returns False at once in that case (`layouts.py:279-281`). The root flag `acknowledgment_fingerprint_migration_complete: false` (`config/layouts.yml:5`) records that the backfill never finished. A fingerprint can only be computed from a parse run, which the records written before the field existed never got.

The fingerprinted records are fragile too. They hash raw cells with boxes and parser name, so any change to geometry unbinds them. Corpus-wide, 282 of 398 acknowledgments need review: 209 drifted and 73 unobserved (`docs/analysis-readiness-0.4.1-status.md:165`). The 398 equals the 215 in scope plus 179 budget detail and 4 PA records. None of the old keys survives a new parser, so every record must be re-keyed by re-observation.

## 6. Evidence

### 6.1 What a published row should carry

For a reader to open the page and see the number, each value needs:
- the publisher file's SHA-256 and its URL in the public archive;
- the 1-based page in that file, not in a cut section;
- the box of the value's words, in PDF points, with the page size;
- the verbatim word texts and their source (text layer or Textract);
- the method (direct, declared format, reviewed) and the review record id when not direct;
- the check outcomes and acknowledgment ids that cover the row.

### 6.2 What the old release carries

Each fact row carries `document_id`, `source_page`, `table_index`, `row_index`, `column_index`, `parser_name`, `source_text`, `extraction_text`, `value_method`, `value_verified`, `human_reviewed` and `value_evidence_id` (`fact_schema.py:13-68`). It carries no box, no word list and no hash. The hash sits in the manifest's source catalog (`release.py:203-208`).

For QCMR the hash is of the cut section PDF. The publisher hash and page are kept only when the section is one page (`qcmr.py:302-312`, `release_packaging.py:1145-1150`). Positions and personal services rows cannot be traced to a page of the publisher file. Boxes appear only on alternate candidates inside receipts for non-direct values (`value_provenance.py:71-85`, `release_value_evidence.py:314-317`).

## 9. Quirk ledger

| Id | What happens | Old handling | Kind |
|---|---|---|---|
| VAL-Q01 | Word source per edition chosen by arithmetic rank, stored outside git | `reconciliation_status.py:393-433`; `artifact_selection.py:88-117` | artifact: multi-backend authority selection |
| VAL-Q02 | QCMR cash FY07 Q4: Textract digits wrong and tie better; text layer right | `qcmr-cash.yml:72-88` | inherent |
| VAL-Q03 | School 2016-04, 2016-11: overprinted text layer loses amounts, reads 77,500,000 | `collections-monthly.yml:76-108` | inherent |
| VAL-Q04 | Raw Textract grid cells have no words or cell confidence; cash FY07 Q4, FY09 Q2, FY25 Q2, O-2 FY13 Q3 use it | `parsers/textract_backend.py:278-297` | artifact: grid backend |
| VAL-Q05 | Damaged font `E(cid:121)PENSES` in cash FY23 Q1, Q2 | `qcmr-cash.yml:14-18` | inherent |
| VAL-Q06 | Scans in QCMR cash, personal services FY08 to FY13, BiB, wage tax industry 2023-12 | `qcmr-personal-services.yml:2-11`; `page_types.yml:531`; `semantics.yml:3771` | inherent |
| VAL-Q07 | OCR output depends on render dpi (300) and API config | `parsers/textract_backend.py:349, 392, 488` | inherent |
| VAL-Q08 | Leader and fused-suffix splits invent boxes by character count | `tables/text_cleaning.py:195-274` | inherent need; boxes are approximations |
| VAL-Q09 | Standalone `$` words dropped before regions | `tables/text_cleaning.py:183-192` | inherent |
| VAL-Q10 | Bare integers weld into label phrases | `tables/line_grouping.py:14-22` | artifact: label-first phrase merge |
| VAL-Q11 | Orphan merge drops displaced bare integers | `tables/line_repair.py:250-253` | artifact |
| VAL-Q12 | Cash page 1 stacks two grids; split at captions | `qcmr-cash.yml:4-18` | inherent |
| VAL-Q13 | Baseline guard needed on three cash editions | `qcmr-cash.yml:19-26` | unsure: try the guard on all editions |
| VAL-Q14 | Grand total in a ruled box below footnotes | `qcmr-personal-services.yml:92-96`; `collections-tax-details.yml:25, 53-56` | inherent |
| VAL-Q15 | Ruled forms need rebin from drawn rules; short supplemental tables fuse `110,626,142.01 92.31` | `page_types.yml:567, 581, 793-818` | inherent |
| VAL-Q16 | BiB LINE NO. margin; FY09 labels still carry `23 29` | `budget-in-brief.yml:21-25`; `resolved_assertions.yml` FY09 keys | inherent |
| VAL-Q17 | Labels above amounts, City 2014 to Nov 2015 | `collections-monthly.yml:18-26` | inherent |
| VAL-Q18 | Region gaps bridged on supplemental pages | `supplemental-report.yml:961` | artifact: consensus region detection |
| VAL-Q19 | Totals on a later page than contributors (positions, City, BiB 8 pages, supplemental) | `tables/stitching.py`; `page_types.yml:552-555` | inherent |
| VAL-Q20 | Cash page 2 all-funds joined to page 1 expense grid | `qcmr-cash.yml:705-717` | artifact: automatic stitching |
| VAL-Q21 | `12 345`, `1 2`, `12, 345` join into one number | `tables/amounts.py:54-88, 123` | artifact (defect); kerning splits are inherent |
| VAL-Q22 | Three lexers disagree on `-$` | `tables/amounts.py:35, 146`; `tables/classification.py:25-41` | artifact: cache invalidation fear |
| VAL-Q23 | Dash is 0.0 in one lexer, None in another; `---` differs | `tables/amounts.py:16-20`; `tables/classification.py:157` | artifact |
| VAL-Q24 | Dash meaning varies by family, column and era | section 3.3 | inherent |
| VAL-Q25 | N/A leaves an operand only by explicit record | `collections-monthly.yml:2-17`; `layouts.py:704-716` | inherent |
| VAL-Q26 | Trailing minus and plus sign rejected | `tables/amounts.py:35` | unsure: no PDF seen |
| VAL-Q27 | Percent parsed as 12.3, unit lost; bare `74.98` found by statistics | `tables/reconciliation_columns.py:69-104`; `supplemental-report.yml:2-5` | inherent (bare); artifact (detection) |
| VAL-Q28 | Footnote marks stripped; superscript digits not | `tables/amounts.py:21-25` | inherent |
| VAL-Q29 | Units: millions, thousands from page text, dollars, cents, counts | `semantics.yml` value scales | inherent |
| VAL-Q30 | Personal services grid mixes counts and dollars by row | `semantics.yml` `qcmr_personal_services` `value_scale_rules` | inherent |
| VAL-Q31 | BiB FY09 total rounded to thousands in a dollar table | `budget-in-brief.yml:223-225` | inherent |
| VAL-Q32 | Values held as float; Decimal only for cash and City collections | `tables/amounts.py:91`; `docs/value-contract-vertical-slice-acceptance.md:75-76` | artifact |
| VAL-Q33 | Two amounts in one cell, spaces after commas | `tables/amounts.py:159-204` | inherent |
| VAL-Q34 | Amount fused with label text, either side | `tables/amounts.py:215-257`; `tables/text_cleaning.py:14-20` | inherent |
| VAL-Q35 | OCR drops decimal: `2100`, `266 1`, `69,2`, `67: 3`, `(29 1)` | `qcmr-cash.yml:89-387`; `tables/value_recovery.py:224-286` | inherent |
| VAL-Q36 | OCR letters and `(59.8j` | `tables/value_recovery.py:32-58` | inherent; repair policy artifact |
| VAL-Q37 | Orphan negating amount below a total, City 2023-07 | `collections-monthly.yml:27-34` | inherent |
| VAL-Q38 | Arithmetic-picked digit verified by rounding receipt | `tables/reconciliation_values.py:637-661` | artifact; breaks the owner's rule |
| VAL-Q39 | Letter map verified with no review | `tables/value_recovery.py:334-335`; `tables/reconciliation_values.py:567-626` | artifact; breaks the owner's rule |
| VAL-Q40 | Arithmetic chooses between word sources per cell | `tables/reconciliation_values.py:727-750` | artifact |
| VAL-Q41 | Arithmetic-only repairs made, then reset | `tables/reconcile.py:1390-1420` | artifact |
| VAL-Q42 | Acks keyed by parser ordinals and hypothesis names | `layouts.py:84-123` | artifact |
| VAL-Q43 | 102 of 215 acks inert without fingerprints | `layouts.py:214-231, 279-281`; `layouts.yml:5` | artifact |
| VAL-Q44 | Fingerprints hash boxes and parser name, so drift on any change | `tables/checks.py:777-837` | artifact |
| VAL-Q45 | Residuals stored as drifting floats | `qcmr-cash.yml` FY16 Q3; `supplemental-report.yml` FY10 | artifact |
| VAL-Q46 | One root defect repeated across editions | section 5.1 | inherent |
| VAL-Q47 | 63 records for one edition's dashes | `collections-monthly-city-2026-08.yml:3-5` | artifact: dash defaults to unknown |
| VAL-Q48 | BiB cross-table records keyed by meaning, no hash | `resolved_assertions.yml:136-417` | inherent knowledge; hash missing is artifact |
| VAL-Q49 | One-decimal bound 0.65 strict; exact for counts | `tables/checks.py:63-99`; `layouts.py:1617-1630` | inherent |
| VAL-Q50 | Supplemental subtotal excludes the reporting year, FY23 still acknowledged | `supplemental-report.yml:8-9` | inherent |
| VAL-Q51 | Fact rows carry no box, words or hash | `fact_schema.py:13-68` | artifact |
| VAL-Q52 | QCMR pages refer to cut PDFs; publisher page lost for multi-page sections | `qcmr.py:302-312` | artifact: cutting at ingest |

## 10. Old code that serves this subject

| Job | Files (lines) | Keep as code | Keep as knowledge |
|---|---|---|---|
| Word sources | `parsers/pdfplumber_backend.py` (476), `parsers/textract_backend.py` (495), `parsers/registry.py` (94), `reconciliation_status.py` (520), `artifact_selection.py` (765) | Text-layer extraction and Textract response mapping | Backend ranking: replace with a declared source per edition |
| Word cleanup | `tables/text_cleaning.py` (274) | Currency, leaders, fused suffix | cid repair cannot fix `E(cid:121)PENSES` |
| Geometry | `tables/line_grouping.py` (384), `tables/line_repair.py` (464), `tables/region_detection.py` (644), `tables/column_detection.py` (45), `tables/row_detection.py` (411), `tables/rule_grid.py` (1,366), `tables/stitching.py` (1,125), `tables/fused_columns.py` (1,491), `tables/row_repairs.py` (1,319) | Lines, gap voting, ruled rebin, row building | Which family needs which repair (section 2) |
| Amounts | `tables/amounts.py` (278) | Strict grouping, paired parentheses, split sequences | Fix VAL-Q21 to Q23 first |
| Recovery | `tables/value_recovery.py` (854), `tables/numeric_value_recovery.py` (917), `tables/reconciliation_values.py` (902) | Column-proven fixed-scale reader | Everything arithmetic-driven |
| Checks and acks | `tables/checks.py` (1,357), `tables/reconciliation_acknowledgments.py` (889), `layouts.py` (1,661), `acknowledgments.py` (1,115), `acknowledgment_identity.py` (71), `resolved_assertions.py` (1,747) | Decimal rounding bound | 215 ack reasons and the BiB semantic key shape |
| Evidence | `models.py` (582), `tables/source_evidence.py` (29), `value_provenance.py` (935), `release_value_evidence.py` (932), `fact_schema.py` (195) | `source_words_match_text` | Method enum, receipt fields |

## 11. The least a design needs

1. Inputs: the publisher PDF by SHA-256, a page range found in place, and a declared word source per edition (text layer or Textract words). No raw Textract grid.
2. Extract words with hash, page, box, text, source, confidence and font. Keep raw words; cleanup produces child words that point to their parent.
3. Where a page has both sources, compare numeric tokens by position. Any unreviewed difference blocks.
4. Build lines and lanes, or rebin a ruled grid for BiB and supplemental forms. Count tables run in a strict mode: one word per numeric cell, no joining of bare integers.
5. Stitch only pages the parser names. Read headers into declared column roles per era.
6. Lex each cell into a typed state: number (Decimal, with its unit and scale), dash, N/A, blank or unreadable. Keep the token. A dash becomes zero only under a rule declared per table, column role and era.
7. Apply only word-based value rules: a declared per-column fixed scale, fused-amount separation, and page-cited reviewed cells. Never pick a digit or a word source from arithmetic.
8. Declare checks per table and era: row sums, column sums, same-label rollups and cross-table equalities, each with a rounding increment or exact. Counts are exact.
9. Match failures to acknowledgments keyed by file hash, page, check id, row label, column role and the residual as a decimal string. An unused acknowledgment fails the release.
10. Write each value with hash, page, box, word ids, source, method and review id.

Parameters that differ by era: word source, unit and scale, column roles, dash rule, ruled or lane layout, and stitch pages.

## 12. Unknowns

- The full per-edition word-source list. It lives in `artifacts/validation/authoritative_artifacts.json`, which is not in git.
- Which BiB and supplemental editions are scans. The config says some are, without names.
- Whether any family prints a trailing minus, a plus sign or superscript footnote digits.
- How many other OCR tenths-digit errors hide inside tolerance on scanned QCMR cash.
- Whether a dash means zero in City collections editions before August 2026.
- Whether the 102 fingerprinted acknowledgments still match today's parses; the corpus-wide status says 209 of 398 drifted.
- Whether the original publisher PDFs exist for QCMR sections cut before FY2022, which decides whether pages can be cited in the publisher file.
- My kind labels for the 215 acknowledgments come from their review text, not from the pages.
