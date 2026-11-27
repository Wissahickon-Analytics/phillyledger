# Build step 5 plan

Build step 5 of `docs/design.md` section 15 reads Table P-1, full-time positions by department,
from the 20 archived QCMR reports of FY2022 Q1 to FY2026 Q4. It builds the kit's path from lines
to a table, the department part of the registry, the row schemas, the column vocabulary and the
positions parser. It publishes nothing. The work is for step 6, which checks and releases these
tables, and for the owner, who lands each pull request. Six pull requests stack in the order S5-A
to S5-F.

The step's check: "the 20 editions parse with no BLOCK finding. The no-ink-lost property holds on
their fixtures. Each department label resolves through the registry, and the schema carries none.
The ten positions columns have ten different descriptions, and the catalog test fails when two are
made equal. Paired fixtures on both sides of each entity seam in the range resolve to different
entities: "Streets" in FY2025 Q4 is Streets with Sanitation, and in FY2026 Q1 it is Streets."

## Track

Full track (`docs/plans/README.md`, "Which track a step runs on"). The parser decides the label,
the row key and the column each number is filed under.

## What a look found

All of this is from November 27, 2026, on Python 3.12.15 with pdfplumber 0.11.10. "The held
folder" is `/Users/nhand/DataProjects/phillyledger-held/qcmr-city`. Each of its 20 report files,
`qcmr-2021-09-30.pdf` to `qcmr-2026-06-30.pdf`, has a sha256 that is on one line of the index, so
these are the archived bytes. Words and rules are those of `PdfPlumberReader().words` on each
whole file, and lines are those of `group_lines`. A "grid page" prints the ten-column table. A
"body row" is a line with ten number words.

1. **Every file has one run of `TABLE P-1` pages and two grid pages.** Sixteen runs open with a
   commentary page, rotation 0 and 255 to 295 words. Each grid page is 792 by 612 with rotation
   90. Page 2 of every file, the table of contents, prints `Table P-1` on a later line and not in
   its two-line band. No other page prints it outside the band.

   | Edition | Commentary | Grid | Rows | Edition | Commentary | Grid | Rows |
   |---|---|---|---|---|---|---|---|
   | `2021-09-30` | none | 35, 36 | 58 | `2024-03-31` | 31 | 32, 33 | 57 |
   | `2021-12-31` | none | 34, 35 | 58 | `2024-06-30` | 31 | 32, 33 | 59 |
   | `2022-03-31` | none | 35, 36 | 56 | `2024-09-30` | 32 | 33, 34 | 58 |
   | `2022-06-30` | 34 | 35, 36 | 56 | `2024-12-31` | 33 | 34, 35 | 58 |
   | `2022-09-30` | 34 | 35, 36 | 58 | `2025-03-31` | 32 | 33, 34 | 58 |
   | `2022-12-31` | 34 | 35, 36 | 58 | `2025-06-30` | 30 | 31, 32 | 58 |
   | `2023-03-31` | 33 | 34, 35 | 58 | `2025-09-30` | 34 | 35, 36 | 63 |
   | `2023-06-30` | 31 | 32, 33 | 58 | `2025-12-31` | 35 | 36, 37 | 63 |
   | `2023-09-30` | 32 | 33, 34 | 57 | `2026-03-31` | 35 | 36, 37 | 63 |
   | `2023-12-31` | none | 32, 33 | 57 | `2026-06-30` | 32 | 33, 34 | 63 |

   "Rows" counts the body rows of both grid pages, 1,174 in all. The 19 counts through
   `2026-03-31` equal the row counts of the old repo's release 2026.07.31, which holds no FY2026
   Q4. The held folder also holds `qcmr-2026-09-30.pdf`, which is not indexed.
2. **The header is the same nine lines on all 40 grid pages.** Lines 1 to 5 are the title and
   the period. Line 6 is `FISCAL YEAR 2025 FISCAL YEAR 2026`, with the edition's years. Line 7
   is `YEAR END ACTUAL ADOPTED BUDGET MONTH END ACTUAL MONTH END`. Line 8 is
   `Department ACTUAL (OVER)`. Line 9 is `General Other Total`, three times, then
   `UNDER BUDGET`. The group captions are in capitals and the fund captions are not. `(OVER)` and
   `UNDER` are on two lines.
3. **No commentary page prints a grid caption.** None of the 16 prints `YEAR END ACTUAL`,
   `ADOPTED BUDGET`, `MONTH END ACTUAL` or `(OVER)`. The prose of three that were read prints
   `adopted`, `General`, `Other` and `Total` in lower or title case.
4. **The right edges of the number words make ten lanes on all 40 pages.** Within a lane the
   edges spread at most 3.82 points, and two lanes are at least 50.5 points apart. No body row
   holds two number words in one lane, and the nearest two number words are 29.46 points apart.
5. **The vertical rules bound the caption groups, not the columns.** Every grid page draws
   vertical rules at six x positions, such as 44.2, 214.8, 370.7, 526.9, 682.8 and 747.4. They
   make a label area and four bands: three bands of three fund columns, and the tenth column.
   The positions differ by up to 1.7 points between editions. On the eight grid pages of
   `2021-09-30`, `2022-03-31`, `2024-06-30` and `2026-06-30`, all six rules cross header lines 7
   to 9, a rule is drawn in up to three touching pieces, and on the second grid page the four
   inner rules stop above the `TOTAL ALL FUNDS` row.
6. **A centered group caption does not overlap its three lanes.** On page 33 of `2026-06-30`,
   `YEAR END ACTUAL` spans x 258 to 328, and its lanes span 215 to 263, 263 to 315 and 315 to
   367. Stacked by overlap, as design section 3.1 has `bind_columns` do, the three lanes read
   `FISCAL YEAR General`, `FISCAL YEAR 2025 YEAR END ACTUAL Other` and `2025 ACTUAL Total`. The
   words inside each band of fact 5, from line 6 down, hold that band's whole group caption on
   all 40 pages.
7. **Twelve editions print a raised mark that leaves its row.** Through `2023-06-30` the `(1)`
   after `Human Services` has the label's size and line, about 2 points after `Services`. From
   `2023-09-30` it is 4.92 points high beside a label of 7.44, with its bottom about 4.2 points
   above the label's. The line tolerance is 2.60, so `group_lines` makes it a line of its own,
   and `has_values` is true for that line. `2023-09-30` to `2024-06-30` print two marks, `(1)`
   after `Aviation` and `(2)` after `Human Services`. The mark that opens each footnote below the
   rows is raised the same way. The 12 editions from `2023-09-30` print 32 raised marks. Each is
   under 0.7 of the median word height of exactly one line whose span holds its bottom edge, and
   that line is its row or its footnote. The four pages measured give 0.66.
8. **A label ends at least 38.94 points before its first number**, on the eight grid pages of
   `2021-09-30`, `2024-06-30`, `2025-09-30` and `2026-06-30`. The longest label is
   `Office of Behavioral Hlth & Intellectual disAbility`.
9. **Seven editions print a sideways page number in the left margin**, `2021-09-30` to
   `2023-03-31`, on all 14 of their grid pages, at `x0` 12.83 or 5.63. The reader gives it as two
   words. The first, `2`, is a line of its own. The second joins a body row as its first word, as
   in `5 First Judicial District` and `6 Records`. Each digit is 4.45 points high, and the
   bottom edge of the `2` is inside the span of that row, so the rule of decision 14 puts both
   digits on the row. Those 14 digits and the 32 marks of fact 7 are the only words of the 56
   pages that the rule moves. From `2023-06-30` each grid page ends with a page number, `23` to
   `28`, as a line of one word.
10. **Below the rows, a page prints footnotes and one notice.** A footnote reads `(1) Positions
    have been transferred to the Grants Revenue Fund. ...` on one line, and from `2023-09-30` its
    mark is raised (fact 7). The FY2024 editions add `In FY23 and prior, positions for the
    Department of Aviation was reported under the Department of Commerce.` Every grid page then
    prints one line that starts `NOTE: The material in this report is preliminary`. On the second
    grid page, `TOTAL ALL FUNDS` is the last row.
11. **Every body row has ten number words, and each reads as a count.** `lex_cell` gives an
    `Amount` for all 11,740 of them. Forty-seven are negative, in parentheses, all in the tenth
    column. One of those is `(1)`, on the `Water,Sewer & Stormwater Rate Board` row of
    `2025-06-30`.
12. **The 20 editions print 62 labels.** Fifty are in all 20. Three parents, `District
    Attorney - Total`, `Fire - Total` and `Police - Total`, each have a `Civilian` and a
    `Uniform` row under them. The parents are bold and those six rows are not. The labels that
    change:

    | Label | Editions that print it |
    |---|---|
    | `Fleet Management`, then `Fleet Services` | `2021-09-30` alone, then all later ones |
    | `City Representative` | 11: all but `2022-03-31`, `2022-06-30`, `2023-09-30` to `2024-03-31`, and `2024-09-30` to `2025-06-30` |
    | `Office of Arts and Culture`, then `Creative Philadelphia` | The first in 9: all through `2024-12-31` but `2022-03-31`, `2022-06-30`, and `2023-09-30` to `2024-03-31`. The second from `2025-03-31` |
    | `Office of Children and Families`, then `Office of Education` | through `2024-06-30`, then from `2024-09-30` |
    | `Aviation` | from `2023-09-30` |
    | `Citizens Police Oversight Commission`, `Mayor's Office-Neighborhood Comm. Act. Ctrs.`, `Office of Public Safety`, `Sanitation` | from `2025-09-30` |

    No page says where the positions of a row are counted in an edition that does not print it.
13. **Two labels change what they cover.** `Streets` reads 1,652, 674 and 2,326 actual in
    `2025-06-30`. In `2025-09-30` it reads 0, 674 and 674 in its prior-year columns, and the new
    `Sanitation` row reads 1,652, 0 and 1,652. `Commerce` reads 690 actual in `2023-06-30`. In
    `2023-09-30` it reads 77 actual beside the new `Aviation` row, and its prior-year columns
    still read 690 while Aviation's read 0. The footnote of fact 10 says why.
14. **The old repo has no row schema for this table.** Its department spellings are in
    `config/entities.yml`, each with `families` patterns in place of year ranges. It keeps one
    `Commerce` entity, and files `Streets` under `phl_rollup_streets_and_sanitation` through
    FY2025.
15. **The prototype has the catalog rules for one table and no `DEFINITIONS`.** `check_decl` in
    `docs/prototype/vocab/test_vocab.py`, lines 24 to 68, holds the rules of design section 11.2
    that read one table's columns. It has no rule that compares a check's operands.

## The owner's answers

The owner answered four questions in the Plan session on November 27, 2026. Each row quotes what
he was shown and the option he picked. Design section 16 holds them as decisions 18 to 21.

| # | What he was shown | His choice |
|---|---|---|
| 1 | "Design section 16 says decisions 13, 15, 16 and 17 are built at step 5, with decision 14. A probe of all 20 archived reports found that Table P-1 needs only decision 14: all 11,620 value words read as numbers, no cell needs a reviewed reading, no page prints n/a, U+2010 or #DIV/0!, no two numbers share a column, and no label ends in a bare digit. Which decisions should step 5 build?" The option: "Step 5 builds decision 14 and proves it on the 16 editions that print a raised mark. Decisions 13, 15, 16 and 17 each move to the first step whose pages print the case, and are sized there on word fixtures of real pages. Step 5 cannot hold those fixtures, because the reports that print the cases are not archived yet. I reword the four rows of section 16 and the pointers in section 3.1. Step 5 is six pull requests." | "Only 14 now (Recommended)" |
| 2 | "Decision 14 lets a small raised word join the line whose vertical span holds its bottom edge. Section 16.3 proposes three details you have not confirmed: (1) the span holds the edge when the line's top is above it and the line's bottom is at or below it; (2) small means under 0.7 of that line's median word height; (3) a word that two lines hold joins the one whose bottom is nearer, and stays a line of its own on a tie. On the archived pages, 16 editions print raised marks, each mark is 0.66 of its line's height, and exactly one line holds each. Confirm the three details?" The option: "Step 5 builds decision 14 with the three details of section 16.3, and the row of section 16.3 is marked confirmed with your words." | "Confirm as proposed (Recommended)" |
| 3 | "The kit pins its bool fields to Word.bold and Column.printed (design section 11.4). Step 5 creates RawRow, which the design gives a field bold: bool \| None, true when all the label's words are bold. On the P-1 pages the three parent rows are bold and their Civilian and Uniform rows are not, but no P-1 rule reads the field. What should step 5 do with RawRow.bold?" The option: "RawRow.bold is built as designed and joins the pinned set beside Word.bold and Column.printed. Section 11.4 changes in the same pull request. It is a fact read from the page, like the other two." | "Pin it as a page fact (Recommended)" |
| 4 | "From FY2024 Q1, Table P-1 prints an Aviation row with this footnote: "In FY23 and prior, positions for the Department of Aviation was reported under the Department of Commerce." So the label Commerce covers Commerce and Aviation through FY2023 Q4 (690 positions) and Commerce alone after (77). The old release keeps one Commerce entity throughout. Is Commerce an entity seam like Streets, which the step 5 check tests with paired fixtures?" The option: "Through FY2023 Q4 the row is a group entity, Commerce with Aviation, with its own row key. From FY2024 Q1 it is the Commerce department. A paired-fixture test covers FY2023 Q4 and FY2024 Q1, as for Streets. One thing stays as printed: in the four FY2024 editions the Commerce row's prior-year columns still hold the combined FY2023 number, and Aviation's are 0. I leave that for the step 6 plan." | "Yes, two entities (Recommended)" |

Two numbers in what he was shown were wrong, and the Codex review found both. Questions 1 and 2
said that 16 editions print a raised mark. Twelve do (fact 7), and 16 is the count of commentary
pages. Question 1 said 11,620 value words. The count is 11,740 (fact 11). A rerun on the held
files gave 12 and 11,740. Every value word still reads as a number, and every raised mark still
has one line to join. One result is new since he answered: the rule of decision 14 also moves
the lone margin digit of 14 pages onto its row (fact 9, shape 9). He was shown the two
corrected counts and that result in the same session and asked "Do your four answers stand with
the corrected counts, or do you want to revisit one?" He answered "Answers stand".

Question 1 said "the four rows of section 16". The rows stay as the owner saw them on November
23, and decision 18 says where each is built now. The other option of question 1 was to build all
five at step 5 on pages that tests build, in eight pull requests. The other options of question 3
were to leave the field out until a rule reads it, and to keep it and stop the shape test from
counting `RawRow`. The other option of question 4 was one `Commerce` entity in all 20 editions,
with a registry record that Aviation was reported under it.

This pull request records the four answers in design section 16 and marks decision 14 confirmed
in section 16.3. It rewords the lines of sections 3.1, 4, 4.2, 16.2 and 16.3 that named step 5
for work that step 5 no longer does. `docs/deviations/step-05.md` records it.

## Clauses

Root tests are in `tests/`. "The fixture folder" is `packages/datadesk/tests/fixtures/words/`.

| # | Clause | Owner | Test that proves it |
|---|---|---|---|
| C1 | The 20 editions parse with no BLOCK finding | S5-E | `test_each_edition_parses_with_no_block_finding` in `tests/test_qcmr_positions.py`, and `test_each_held_report_parses_whole` in `tests/test_held_reports.py` |
| C2 | The no-ink-lost property holds on their fixtures | S5-E | `test_no_ink_is_lost_on_any_grid_page` in `tests/test_qcmr_positions.py` |
| C3a | Each department label resolves through the registry | S5-E | `test_each_department_label_is_a_registry_label` in `tests/test_qcmr_positions.py` |
| C3b | The schema carries none | S5-D | `test_the_positions_schema_spells_no_department` and `test_a_department_spelled_in_a_form_fails_the_schema_test` in `tests/test_registry_data.py`, and `test_an_entity_row_with_labels_is_refused` in `packages/datadesk/tests/core/test_rowschemas.py` |
| C4a | The ten positions columns have ten different descriptions | S5-F | `test_the_ten_positions_columns_have_ten_descriptions` in `tests/test_table_catalog.py` |
| C4b | The catalog test fails when two are made equal | S5-F | `test_two_equal_descriptions_fail_the_catalog_rules` in `tests/test_table_catalog.py` |
| C5 | Paired fixtures on both sides of each entity seam in the range resolve to different entities | S5-E | `test_streets_is_two_entities_across_fy2026` and `test_commerce_is_two_entities_across_fy2024` in `tests/test_qcmr_positions.py` |
| L1 | From the step's list: a page with the `TABLE P-1` band and no grid captions is commentary, reported and not parsed | S5-E | `test_a_commentary_page_is_reported_and_not_parsed` in `tests/test_qcmr_positions.py` |
| L2 | From decision 14: proven on a word fixture of the page that holds "Human Services (1)" | S5-A | `test_every_raised_mark_joins_its_line_on_the_grid_pages` in `tests/test_p1_pages.py` |

C1 has two tests. The first builds, for each edition, a `Document` from the fixtures of its run:
the commentary page where fact 1 lists one, then the two grid pages. It requires a `Parsed` with
one table, no finding of severity BLOCK, the two grid pages as the table's pages, and the row
count of fact 1. A drop pattern that removed a row would still pass C2, and the row count stops
it. The second test takes its 20 editions from the index, never from a folder listing. For each
it finds the file of that sha in the folder that `DATADESK_HELD_PDFS` names, and fails when one
is missing. It parses the whole report, so `find_runs` reads every page, the table of contents
among them, and makes the same five requirements as the first test. It skips with a message when
the variable is unset, as in CI. The S5-E owner runs it on the held folder and records the run in
the pull request.

C2's test takes each of the 40 grid pages through `parse` and through the cut that `parse`
makes. Every word ref of the page must be in exactly one place: a header line, a furniture line,
a prefix, the label or a cell of an assembled row, a stray that a finding names, or a raw row
that an `unknown_row` finding names. So a cell that assembly emptied fails it, and so does a
stray with no finding. The kit's property test of the same rule on generated pages lands in
S5-C, and both tests use one helper. The helper has two tests of its own: a ref taken out fails
it, and a ref counted twice fails it.

C3a's test reads each parsed table. A row with an entity must have a label whose `norm` is the
normalized form of a name from `labels_for(registry, entity, scope)` for that edition, put
through one of the row's `forms`, so `Police - Total` comes from the name `Police`. Every `item`
and `subtotal` row has an entity. A row with none is a `breakdown` row, whose parent has one, or
the root, whose parent is `None`. C3b's first test reads `data/rows/qcmr_positions.toml`. No row
with an `entity` has `labels`. Every label in the file is `Civilian`, `Uniform` or `TOTAL ALL
FUNDS`. Every form is `{name}` or `{name} - Total`. The second test puts `{name} Police` among a
row's forms in a copy of the file and requires the first test's rule to fail.

C4a's test looks the table up with `entry("qcmr_positions")`. It requires the ten column names
of design section 5.1, in order, a published meaning for each, and ten different descriptions.
The prototype's rule skips a column that is `NotPublished`, so two such columns would pass it.
C4b's test runs the same function on a copy of the entry in which `adopted_other` has the
description of `adopted_general`, and requires the report to name both columns.

C5's tests parse `qcmr_2025_06_30_p32` and `qcmr_2025_09_30_p36` for `Streets`, and
`qcmr_2023_06_30_p32` and `qcmr_2023_09_30_p33` for `Commerce`, each with the other grid page of
its edition. Each requires the row key and the entity on both sides: `group=streets_with_sanitation`
then `dept=phl_dept_streets`, and `group=commerce_with_aviation` then `dept=phl_dept_commerce`.

## Shapes the design leaves open

The Build sessions skip `how` and `architect`, so this plan names what the design does not. The
pull request that builds a shape records it in `docs/design.md` and in
`docs/deviations/step-05.md` (hard rule 7).

1. **Decision 14** (answer 2). In `group_lines`, a word under 0.7 of a line's median word height
   joins that line when the line's top is above the word's bottom edge and the line's bottom is
   at or below it. A word that two lines hold joins the one whose bottom is nearer, and stays a
   line of its own on a tie. Every other word groups as it does today. On the 56 pages the rule
   moves the 32 marks of fact 7 and the 14 margin digits of fact 9, and no other word.
2. **`PageLines` carries the page's rules.** `cut_pages` takes `PageLines`, and shape 4 needs the
   rules. `page_lines` copies them from the `Page`.
3. **Lanes come from values.** `cut_pages` calls `lanes_from_values` on every page. The design
   has it call `lanes_from_rules` "when the page has vertical rules", and the P-1 rules bound
   groups (fact 5). The first table whose rules bound its columns, at step 11 or 12, adds that
   choice as a field the table declares. `lanes_from_rules` counts touching pieces of one rule
   as one rule.
4. **A group caption binds by its rule band.** `ColumnSpec` gains `group: str | None = None`, a
   regex for the caption over a group of columns. The bands of a page are the lanes between the
   vertical rules that cross its last header line. A band's caption is the header words whose
   horizontal center is in the band, top to bottom. `bind_columns(era, header, lanes, bands)`
   takes a spec with a group as a candidate for a lane only when the group regex finds the
   caption of the band that holds the lane. A spec with a group and no such band is a
   `column_unbound` finding. `caption` is still searched in the words that overlap the lane.
   Binding by the order of three equal fund captions would pass a page that swaps two groups,
   and the review of November 22 asked for evidence of each name (design section 18.1).
5. **The P-1 captions, as the pages print them** (fact 2). The era's signature is
   `YEAR\s+END\s+ACTUAL`, `ADOPTED\s+BUDGET`, `MONTH\s+END\s+ACTUAL` and `\(OVER\)`, each on one
   header line, and a commentary page prints none of the first, third and fourth (fact 3). The
   nine fund columns have the captions `General`, `Other` and `Total` and the three group
   captions. The tenth has `\(OVER\)\s*UNDER` and no group. The regexes of design section 5.1
   are in title case and fail on all 40 pages.
6. **The run starts at the first page with captions.** A page of the run is commentary when its
   text holds no signature regex of any era. `cut_pages` does not cut a commentary page that
   comes before the first grid page, and gives one WARN finding for it, `commentary_page`. It
   chooses the era from the first page that is not commentary. A page that holds some of an
   era's signature and not all of it stops the table, first page or not, and so does a
   commentary page after a grid page. So a grid page that lost one caption is never taken for
   commentary.
7. **A number beside a label word is label text.** In `lanes_from_values`, a number word that
   stands closer than its line's median word height to a word on its left that is not a number
   seeds no lane. A `(1)` after `Services` is about 2 points away, the first value of a row at
   least 38.94, and the median height 7.44 (facts 7 and 8). `cut_line` then puts the mark left
   of `label_right`, and `parse_label` takes it off the label.
8. **What is furniture.** `slice_body` also returns as furniture each line below the stop line
   and each body line that holds only prefix words. So the notice below `TOTAL ALL FUNDS` and
   the page number at the foot (fact 9) have a place in the ink count.
9. **The margin page numbers leave by the prefix rule.** Shape 1 puts both digits of a margin
   page number on one row (fact 9). The design's `prefix` of `(?:\d{1,2}|I)` takes both off the
   row before lanes are found, so the row's `Label.text` is right, and `Label.printed` and the
   row's prefix keep the digits. The note in `docs/plan-notes.md` proposed dropping the digits
   before lines are grouped. That needs a new kit rule, and the kit already has this one. Which
   label field a release prints is for the step 6 plan.
10. **The P-1 body.** It starts at the first known row and stops at `TOTAL ALL FUNDS`. Its drop
    patterns take a line that starts with `(N)` and a space, and the `NOTE:` line (fact 10).
    Shape 1 joins each raised footnote mark to its footnote, so the first pattern finds it.
11. **`RawRow.bold` is pinned** (answer 3). `test_bool_fields_are_page_facts_only` expects
    `("RawRow", "bold")` from S5-B and `("Column", "printed")` from S5-C.
12. **The kit imports `date`.** `Era.expected` and `cut_pages` take dates, so `datetime` joins
    the kit's outside modules in design section 11.1 and the pin in `tests/test_purity.py`.
13. **`low_confidence` joins `UnreadableReason`** in S5-C, which builds the floor rule of
    `assemble`, with the pin and design section 11.4 (hard rule 6). `assemble` passes the words
    of the cut page to `reading_for` (the note in `docs/plan-notes.md`). `apply_reading` and
    `transliteration_ok` do not change (answer 1).
14. **The registry at step 5.** `core/registry/model.py`, `load.py` and `labels_for` in
    `resolve.py`. `resolve`, `resolve_fund` and `normalize_printed_code` wait for the first
    grammar table, at step 8, and `lint_registry` for step 13, as section 15 says. A label that
    two rows claim in one edition is an `ambiguous_row` finding of `match_rows`, which C1
    reads. The data is the entities that the 62 labels of fact 12 need: `departments.toml`,
    `groups.toml`, `aliases/qcmr_positions.toml`, and `funds.toml` with `phl_fund_general` and
    `phl_fund_other`, which the fund columns name. A department keeps its id from the old
    `config/entities.yml`. The two groups of shape 15 do not: the old file calls the first
    `phl_rollup_streets_and_sanitation` and has no second. A name's range is whole fiscal years,
    and two spellings change inside a year: `Fleet Management` prints in FY2022 Q1 alone, and
    `Creative Philadelphia` starts at FY2025 Q3. Each of those two is an alias with the shas of
    its editions, so `Fleet Management` is no label of `2021-12-31` and `Creative Philadelphia`
    none of `2024-12-31`.
15. **The seams** (answer 4, fact 13). `phl_group_streets_sanitation` under the key
    `group=streets_with_sanitation` through `2025-06-30`, then `dept=phl_dept_streets`, as in
    design section 5.1. `phl_group_commerce_aviation` under `group=commerce_with_aviation`
    through `2023-06-30`, then `dept=phl_dept_commerce`. A row that some editions do not print
    (fact 12) has `periods` for the editions that do.
16. **A loader's refusal has a type.** `load_registry` and `load_row_schema` return their value
    or `Refused(findings)`, a frozen dataclass in `core/registry/load.py` that `rowschemas`
    imports, and each caller ends its `match` in `assert_never` (`docs/principles.md`, section
    8.3). The design gives `tuple[Finding, ...]`. `parse` tells `PageRun` from `Finding` with
    `match`, where the design writes `isinstance`. Step 5 changes neither `core/catalog.py` nor
    `core/domain.py`, so `load_catalog` keeps its tuple, and the edition id, the `listed_at`
    stamp and the URLs keep their `str` (`docs/progress.md`, "What the type rules leave for later
    steps").
17. **Records at step 5.** `core/context.py` as designed. `core/records.py` gains `TablePages`,
    `declared_run` and `illegible_pages`, which `parse` calls with no record. No loader is
    built, because no record exists for these 20 editions (fact 11). Each loader lands with its
    first record. Tests build a `ParseContext` from the data files and empty records.
18. **The table catalog without checks.** `TableEntry` has `name`, `dataset`, `series`, `parse`,
    `eras` and `measures`. `checks_for` and `checks/dsl.py` are step 6's, whose check is the
    first to name a check. S5-F adds the DSL to step 6's list in design section 15.
19. **The catalog rules at step 5.** The rules of design section 11.2 as one function that
    returns its complaints, so C4b can call it. It also requires each caption, group and
    signature regex to compile and each `decimals` to be `None` or at least 0 (the note
    "Constructor checks the kit does not make"). Two rules wait. The one that compares a
    check's operands needs the DSL, at step 6. "Every `Quantity` member is used by at least one
    table" cannot hold with one table, and joins at the step that builds the last table.
20. **No shell part.** Step 5 adds no command. `LocalCache` joins `Deps` at the step that builds
    `run_parse`.
21. **The port of `measures.py` takes the design's names.** The prototype differs from design
    sections 2.2 and 3.2 in four places, and the design wins in each. `describe` becomes
    `description`. `measure_for` takes a `RowKey`. `Scope` holds `edition`, `table`, `printed`
    and `actual_through`, where the prototype holds a period, a stage and an instance.
    `scope_for` returns the scope and the ids of the notes it used. The port uses the `Period`
    of `core/domain.py` and adds no second one.

## Pull requests

One GitHub stack, bottom first. Each pull request also touches `docs/design.md`,
`docs/deviations/step-05.md`, `docs/progress.md` and `docs/plan-notes.md` for what it builds, the
field and list pins of `packages/checkedtables/tests/test_library_shape.py` for the kit types it
creates, and `tests/test_purity.py` for the outside names its pure modules import. The stack
keeps one writer on those files. Paths below drop `packages/` and the `src` folders.

### S5-A, `step-05/a-raised-marks`: the other fixtures, and a raised mark joins its line

Builds on `main`. `feat(checkedtables): join a small raised word to the line that holds it`.

- Files: 36 new files in the fixture folder, `datadesk/tests/fixtures/p1.py`,
  `checkedtables/lines.py`, `checkedtables/tests/test_lines.py`, `tests/test_p1_pages.py`,
  `tests/test_word_fixtures.py`.
- Writes, with `datadesk fixture`, the two grid pages of the ten editions that have none and the
  16 commentary pages (fact 1). `p1.py` holds the table of fact 1 as a literal, and every later
  test reads its pages and row counts from it.
- Owns L2. Proves shape 1 on built pages, one test for each detail and one for a word of full
  size that stays on its own line. Proves on the fixtures that each of the 32 raised marks of
  fact 7 is on the line of its row or its footnote, in the 12 editions from `2023-09-30`, with
  `Human Services (1)` on page 33 of `2026-06-30` among them, and that no line of a grid page is
  a lone `(N)`. Proves that on the 14 pages of fact 9 both margin digits are on one row's line.
  Proves, by word ref, that no other word of the 56 fixture pages changes its line.
- Runs, each recorded in the pull request. `datadesk fixture` reads the archive on R2 from an
  empty word cache, as `uv run --env-file /Users/nhand/DataProjects/phillyledger/.env datadesk
  fixture <sha> <pages>` from the worktree (`docs/progress.md`, "The archive bucket from a
  worktree"). `test_each_word_fixture_regenerates_byte_identical` runs on the held folder. The
  20 fixtures of step 4 keep their bytes, and the tests of `tests/test_row_crops.py` pass
  unchanged.

### S5-B, `step-05/b-cut`: from lines to raw rows

Builds on S5-A. `feat(checkedtables): cut a table's pages into raw rows by caption`.

- Files: `checkedtables/pages.py`, `columns.py`, `pipeline.py`, `rows.py` for `RawRow` alone,
  `lines.py` for shape 2, their tests, `datadesk/core/tables/qcmr_positions.py` for `TABLE`,
  `COLUMNS` and `ERAS`, `tests/test_p1_pages.py`.
- Builds the three modules as design sections 2.1 and 3.1 give them, with shapes 2 to 8, 11
  and 12.
- Proves on built pages: `find_runs` and `only_run` for no run, one and two. `choose_era` for
  no era, two eras and a date outside the range. A missing required caption is `column_unbound`
  (the test of design section 11.3). Two groups that trade places bind to no wrong name. A
  mark beside a label seeds no lane. A page that binds other columns than the first gives
  `columns_differ_by_page`. A commentary page first gives one WARN and is not cut. A first grid
  page that lost one signature caption, before an intact second one, stops the table.
  `bind_by_position` binds only a page that the caller names.
- Proves on the 40 grid fixtures, with the module's `ERAS`: ten lanes, four bands, and the ten
  columns bound left to right with the group each band prints. Each body row cuts to a label
  and ten cells of one word, and no stray.

### S5-C, `step-05/c-rows`: rows, the table and assembly

Builds on S5-B. `feat(checkedtables): match rows to a schema and assemble a table`.

- Files: `checkedtables/table.py`, `rows.py`, `assemble.py`, `kinds.py`, their tests,
  `checkedtables/tests/ink.py` for the helper of C2.
- Builds `RowKind`, `Additivity`, `TableId`, `Column`, `Row` and `Table`, the rest of `rows.py`,
  and `assemble`, as designed, with shape 13.
- Proves by example each outcome of design section 7.3 for a closed table: `unknown_row`,
  `ambiguous_row`, `duplicate_row` and `missing_row`. A row matches only inside its `within`
  block, so `Civilian` under three parents gives three keys. An exact match beats a prefix. A
  dash rule and a reading change a cell and are named in `used`. An unreadable cell with no
  reading blocks. An OCR word under the floor is `low_confidence`.
- Proves with Hypothesis that no ink is lost on a generated table page, through assembly, with
  the helper and its two tests of C2. The rule of design section 11.2 on a total with no parts
  has an exception that names two checks, so it waits for the coverage of step 6.

### S5-D, `step-05/d-registry`: the registry and the row schema

Builds on S5-C. `feat(datadesk): keep department spellings in a registry and rows in a schema`.

- Files: `datadesk/core/registry/`, `datadesk/core/rowschemas.py`, `datadesk/core/domain.py`,
  the data files of shape 14, `datadesk/data/rows/qcmr_positions.toml`,
  `datadesk/tests/core/test_registry.py`, `test_rowschemas.py`, `tests/test_registry_data.py`,
  the root `pyproject.toml` if import-linter needs the new package named.
- Owns C3b. Proves on literal TOML: a name outside its fiscal years gives no label. An alias
  holds only in its tables, its years and its editions. `forms` builds `Police - Total` from the
  registry name. A row outside its `periods` leaves the schema. An entity row with labels, a
  sha that is not one, and text that is not TOML are each `Refused`.
- Proves on the data files: every file loads. The schema of each edition has the row count of
  fact 1, with `Civilian` and `Uniform` under each of the three parents. Each label of the table
  in fact 12 is a label of the schemas of the editions that the table lists, and of no other.
  The two aliases of shape 14 hold in their editions alone. The schema of `2025-06-30` holds the
  Streets group and that of `2025-09-30` the department, and the same for Commerce at
  `2023-06-30` and `2023-09-30`.
- The owner of this pull request may match the cut rows of the fixtures against its schemas to
  get the data right. The clause tests through `parse` are S5-E's.

### S5-E, `step-05/e-positions`: the positions parser

Builds on S5-D. `feat(datadesk): parse QCMR Table P-1 from the whole report`.

- Files: `datadesk/core/context.py`, `datadesk/core/records.py`,
  `datadesk/core/tables/qcmr_positions.py`, `datadesk/tests/core/test_records.py`,
  `tests/test_qcmr_positions.py`, `tests/test_held_reports.py`.
- Owns C1, C2, C3a, C5 and L1. Builds `parse` as design section 5.1 gives it, with shapes 9, 10,
  16 and 17. L1's test requires one `commentary_page` finding that names the page in each of the
  16 editions of fact 1, and none in the other four.
- Also proves on the fixtures: the 14 rows of fact 9 have a label with no digit in `Label.text`
  and both margin digits in their prefix. The `(1)` of `2025-06-30` is the cell -1 and no mark
  (fact 11). Each of the three parents has its two children as `breakdown` rows, every other
  row hangs under `line=total_all_funds`, and that row has no parent. On every first grid page
  the footnotes and the notice are furniture, and no finding names them.
- Shows, in the pull request, C1's first test failing when a required row is taken out of a copy
  of one fixture.

### S5-F, `step-05/f-vocabulary`: what each column means

Builds on S5-E. `feat(datadesk): describe each positions column in the closed vocabulary`.

- Files: `datadesk/core/vocab.py`, `measures.py`, `periods.py`, `tables/catalog.py`,
  `tables/qcmr_positions.py` for `measures`, `datadesk/tests/core/test_vocab.py`,
  `test_measures.py`, `tests/test_table_catalog.py`.
- Owns C4a and C4b. Ports `vocab.py` and `measures.py` from `docs/prototype/vocab/`, never
  importing from it, with `DEFINITIONS`, shapes 18, 19 and 21, and the six list pins in
  `test_closed_lists_are_pinned`.
- Proves, through `entry("qcmr_positions").measures` with a `Scope` that `scope_for` builds and
  the fund ids of `funds.toml`: a budget with no version and a version on an actual are
  refused. The quarter-end count of FY2024 Q4 and the prior-year count of FY2025 Q1 are one
  subject, and that of FY2024 Q2 is another. An operand that is not a column fails the catalog
  rules, and so does a fund id that the registry lacks.
- Sets the step's row in `docs/progress.md`.

## Risks to probe

1. **Shape 1 changes `group_lines` for every page.** S5-A shows the step 2 tests unchanged. The
   probe applied the rule to the lines that `group_lines` makes today, and S5-A builds it inside
   the grouping. If any word but the 32 marks and the 14 margin digits changes its line on the 56
   fixture pages, S5-A stops for the owner.
2. **Bands need drawn rules.** A scan has none, so a spec with a group cannot bind there
   (shape 4). The note for step 7 says so.
3. **The limit of shape 7 is sized on one table.** It sits between about 2 and 38.94 points here.
   A later table with tighter columns fails with a missing value, never with a wrong one.
4. **Facts 5 and 8 rest on eight pages each.** S5-B proves the bands and the lanes on all 40. A
   page whose rules do not cross its last header line, or whose label ends within 7.44 points
   of its first number, stops the pull request for the owner.
5. **The registry data is typed from the old file.** A wrong year range shows as `missing_row`
   or `unknown_row` on a fixture in S5-D, and the row counts of fact 1 are a second check.
6. **Codex's sandbox reads neither R2 nor the held folder.** The owner agent records the runs
   of S5-A and of C1's second test (`docs/plans/README.md`, "How a pull request is verified").
7. **Sizes.** Design section 12 estimates 1,210 lines for the six kit modules, of which 77 are
   built, at most 620 for the registry and the row schemas, and 440 for `vocab.py`,
   `measures.py` and `tables/catalog.py`. S5-B and S5-C are the two largest diffs. A module that
   runs well past its estimate is said so in `docs/progress.md`.

## Notes this plan leaves

`docs/plan-notes.md` changes in this pull request. The two notes on the reading rule now name
the plan of the step that builds decision 13, the note on join shape 1 names the step that builds
decision 16, and the note on `extract_words` names step 6. New notes: for step 6, the label
field a release prints (shape 9), the FY2024 prior-year columns of `Commerce` (answer 4), the
two group ids that the old release lacks (shape 14), the rows that some editions do not print
(fact 12), the check DSL with the catalog rule that needs it (shapes 18 and 19), and the rule
on a total with no parts. For step 7, that a group needs rule bands (shape 4), that the leading
digits of seven text-layer editions are margin page numbers (fact 9) while QPOS-Q10 leaves
those of the scans open, and that the captions of shape 5 are those of FY2022 to FY2026. For
the step that builds the last table, the catalog rule on `Quantity` (shape 19). Each Build
session removes the notes it acts on.

## Codex review

Codex reviewed commit `939383d4` on November 27, 2026. Its report is
`.codex-review/step-05-plan-939383d4.md`. It raised fourteen findings, six as blocking. Each was
checked against a run on the held files, the fixtures or the quoted lines. All fourteen held,
and the plan above is revised for each. Finding 10 is answered with the alias that Codex names
on one side of each change, and not on both, with the reason.

| # | Finding | How it was confirmed | What changed |
|---|---|---|---|
| 1 | The rule of decision 14 also joins the lone margin `2`, which met S5-A's own stop | Rerun on all 56 pages: the rule moves 32 marks and 14 margin digits, each to one line, and no other word | Fact 9, shapes 1, 8 and 9, S5-A and risk 1. The step 7 note claims only the seven text-layer editions |
| 2 | Twelve editions print a raised mark, not 16. The cells are 11,740 and the negatives 47. The fixtures are 56, not 76 | Rerun: 1,174 rows, 11,740 `Amount`, 47 negatives in the tenth column, 12 editions with a mark on a line of its own | Facts 1, 7 and 11, the paragraph under the owner's answers, S5-A, risk 1, and the rows of decisions 18 and 19 in the design |
| 3 | C3a refused `Police - Total` and its `Civilian` row | Design section 5.1: the parent's label comes from `forms`, and the child's key has a `dept` part and no entity | C3a reads the forms, and S5-D counts `Civilian` under three parents |
| 4 | C3b passed with a department spelled in `forms` | The test read `labels` alone | C3b lists the forms the file may hold, and a second test plants one |
| 5 | C2 stopped before assembly, took a stray with no finding, and its shown failure would not fail | Design section 11.2 names the finding, and shape 8 makes the notice furniture | C2 reads the assembled rows and the findings, the helper has two tests, and S5-E proves the notice apart |
| 6 | C4a passed with two columns that are `NotPublished` | `test_vocab.py`, line 36, skips such a column | C4a requires ten names, ten published meanings and ten descriptions, through `entry` |
| 7 | The whole-report test took its inputs from a folder that holds 21 PDFs | `ls` of the held folder: 21 | C1's second test takes the 20 editions from the index and fails on a missing file |
| 8 | A first grid page that lost one caption would be taken for commentary | Shape 6 as written | Shape 6: commentary holds no signature regex at all. None of the 16 pages does (fact 3). S5-B tests the damaged page |
| 9 | The rule on a total with no parts needs the check DSL | Design section 11.2 names `ColumnSum` and `CellsEqual` in its exception | S5-C drops it, and the step 6 note takes it |
| 10 | A fiscal-year range cannot mark a spelling that changes inside a year | `Dated` holds `first_fy` and `last_fy` alone. Fleet changes inside FY2022 and Arts inside FY2025 | Shape 14 and S5-D: the spelling that prints for part of a year is an alias with shas. The other spelling of the same entity stays a name for the whole year, since either one gives the same key |
| 11 | `Refused` in `core/domain.py` would bring that file's waiting type work into step 5 | `docs/progress.md`, lines 60 to 69, and `domain.py`, lines 52, 100 and 101 | Shape 16: `Refused` is in `core/registry/load.py` |
| 12 | The port of `measures.py` did not name what changes from the prototype | `measures.py` of the prototype, lines 100, 186 and 199, beside design sections 2.2 and 3.2 | Shape 21 and S5-F |
| 13 | Two new ids have no match in the old release | `config/entities.yml` of the old repo, lines 765 and 1557 | Shape 14 and the step 6 note |
| 14 | S5-A did not say how its R2 run gets its keys | `docs/progress.md`, "The archive bucket from a worktree" | S5-A names the command |
