# Step 5: deviations from the design

What step 5 changed in `docs/design.md`, and why. The design holds each rule as it now stands,
so read this file only to learn why the design says what it says. Each entry: what changed,
why, the run that shows it, and the design section updated. Fact, shape and answer numbers refer
to `docs/plans/step-05.md`.

- **Step 5 builds decision 14 alone, and four decisions move** (November 27, 2026, the Plan
  run). Design section 16 had decisions 13, 15, 16 and 17 built at step 5. Read with the step 4
  reader, the two grid pages of Table P-1 in each of the 20 archived reports hold 11,740 number
  words, and `lex_cell` gives every one as an `Amount` (fact 11). No page prints `n/a`, U+2010
  or `#DIV/0!`, no row holds two numbers in one lane (fact 4), and no label ends in a bare
  digit. Twelve editions do print a raised mark that `group_lines` puts on a line of its own
  (fact 7), which is decision 14. The owner was shown 11,620 and 16, which were wrong, and the
  plan and decision 18 say so. The pages that print the other cases are in reports the
  archive does not hold yet, so step 5 could size none of those rules on a word fixture. Shown
  this, the owner chose "Only 14 now (Recommended)" (answer 1, decision 18). Each of the four is
  built at the first step whose pages print its case. Rows 13, 15, 16 and 17 of section 16 stay
  as the owner saw them on November 23. Design sections 3.1, 16, 16.2 and 16.3.
- **The three details of decision 14 are confirmed** (November 27, 2026, the Plan run). Section
  16.3 held them as a proposal. In the 12 editions that print one, each of the 32 raised marks
  has its bottom edge inside the span of exactly one line and is under 0.7 of that line's median
  word height (fact 7). The owner chose "Confirm as proposed (Recommended)" (answer 2, decision
  19). The Codex review of the plan then found that the rule also moves the lone digit of a
  margin page number onto its row, on 14 pages (fact 9). Shown that result and the two corrected
  counts, the owner answered "Answers stand". Design sections 16 and 16.3.
- **`RawRow.bold` joins the pinned `bool` fields, and `Commerce` is a seam** (November 27, 2026,
  the Plan run). The owner chose "Pin it as a page fact (Recommended)" (answer 3, decision 20)
  and "Yes, two entities (Recommended)" (answer 4, decision 21). The FY2024 grid prints the
  footnote "In FY23 and prior, positions for the Department of Aviation was reported under the
  Department of Commerce." (fact 10), and `Commerce` reads 690 actual in FY2023 Q4 and 77 in
  FY2024 Q1 (fact 13). S5-B changes section 11.4 when it builds `RawRow`. Design section 16.
- **Two lines no longer name step 5** (November 27, 2026, the Plan run). Section 4 said that the
  step 5 plan decides when `LocalCache` joins `Deps`. Step 5 adds no command, so it joins at the
  step that builds `run_parse` (shape 20). Section 4.2 said that `load_records` arrives at step
  5. No record exists for the 20 editions, so each loader lands with its first record (shape
  17). Design sections 4 and 4.2.
- **Decision 14 moves 54 words, and two step 2 properties are restated** (November 27, 2026, S5-A).
  The plan said the rule moves the 32 marks and the 14 grid-page margin digits and no other word of
  the 56 fixture pages. Built in `group_lines`, it also moves the two margin digits of the sideways
  page number on page 34 of `2022-06-30`, `2022-09-30` and `2022-12-31` and page 33 of `2023-03-31`.
  Each digit is 4.45 points high with its bottom at 306.00 or 310.45, inside the span of the prose
  line `Note for FY.. Q.:`, which runs from 305.06 to 315.06 with a median height of 10.00, and both
  join it. The Plan session's count skipped the pages with no body row. These are commentary pages,
  reported and not parsed, so no value, label or row changes. The step 2 tests
  `test_a_line_never_spans_more_than_the_tolerance` and
  `test_a_word_within_the_tolerance_never_opens_a_line` held every word of a line to the tolerance,
  which a raised mark with its bottom 4.2 points above its label's cannot meet. They now hold for
  the words the rule does not move, which a reference of the step 2 rule finds. Those words of a
  line span at most the tolerance, and they keep the lines the step 2 rule gives them. The lead's
  probe on the held PDFs found the 54, and
  `test_only_the_54_pinned_words_leave_the_lines_of_the_step_2_rule` pins them by ref. The owner
  chose "Build as confirmed (Recommended)" (decision 19). The bottoms of the step 2 lines rise
  strictly from line to line, so no two share a bottom, the tie of section 16.3 cannot occur, and
  the rule needs no code for it. Design sections 3.1 and 16.
- **`PageLines` carries the page's rules** (November 27, 2026, S5-B). `cut_pages` takes
  `PageLines`, and the bands of shape 4 need the rules, so `page_lines` copies them from the
  `Page`. The field defaults to `()`, as `Page.rules` does (shape 2).
  `test_page_lines_carry_the_rules_of_the_page`. Design sections 2.1 and 3.1.
- **Lanes come from values, and rules give bands** (November 27, 2026, S5-B). The design had
  `cut_pages` call `lanes_from_rules` when a page has vertical rules. The six rules of each
  P-1 grid page bound a label area and four groups, not ten columns (fact 5), so lanes always
  come from values and `lanes_from_rules` gives the bands. It joins pieces of one rule under 1
  point apart, and reads only the region's top and bottom, since the outer P-1 rules lie
  outside the words of the last header line (shape 3). On all 40 grid fixtures the rules that
  cross the last header line give five lanes, and `test_touching_pieces_of_a_rule_count_as_one_rule`
  proves the join. Design section 3.1.
- **A column with a group binds by its rule band** (November 27, 2026, S5-B). `ColumnSpec`
  gains `group`, and `bind_columns` takes the bands as a fourth parameter. A band's caption is
  the header words whose middle is in it, and a grouped column is a candidate only for a lane
  whose right edge is in a band that prints its group. A centered group caption is whole over
  none of its three lanes (fact 6), and binding three equal fund captions by order would pass
  a page that swaps two groups (shape 4). `test_two_groups_that_trade_places_bind_to_no_wrong_name`
  gives `columns_out_of_order` for the swap. An empty group is refused, as an empty caption is.
  Design sections 2.1, 3.1 and 5.1.
- **The P-1 captions are written as the pages print them** (November 27, 2026, S5-B). Shape 5
  as planned. Design section 5.1 gave the group captions in title case, `Year.?End\s+Actual`,
  `Adopted` and `Month.?End\s+Actual`, the tenth column `\(Over\)\s*Under`, and the era the
  signature `Adopted` and `\(Over\)\s*Under`. The 40 grid pages print the group captions and
  `(OVER)` in capitals (fact 2). So the group captions are now `YEAR\s+END\s+ACTUAL`,
  `ADOPTED\s+BUDGET` and `MONTH\s+END\s+ACTUAL`, the tenth column is `\(OVER\)\s*UNDER`, and
  the signature is the three group captions and `\(OVER\)`. Run on the 40 grid fixtures, no
  title-case regex of the old section 5.1 is found in a page's text or a lane's caption, so
  with the old era `cut_pages` takes every page for commentary and gives `no_grid_page`. The
  four new signature regexes are found in all 40 headers and in none of the 16 commentary
  fixtures, and each new caption is found in its bound lane's caption on all 40.
  `test_the_ten_columns_bind_left_to_right_under_the_group_each_band_prints`. Design section
  5.1.
- **A lane runs from the lane before it** (November 27, 2026, S5-B). The design left a lane's
  width open. A lane of the value words' own extent misses captions: the tenth P-1 column
  prints `UNDER` at x 685.5 to 711.9 over numbers from 729.8 to 743.5 (page 33 of
  `2026-06-30`). So a lane runs from the right edge of the lane before it to its own rightmost
  edge, and a word is in a lane by its right edge.
  `test_right_edges_cluster_into_lanes_that_meet` and the 40-fixture binding test show it.
  Design sections 2.1 and 3.1.
- **A number beside a label word seeds no lane** (November 27, 2026, S5-B). Shape 7, with
  cells. A lane is seeded by a cell: a run of words, each closer than the line's median word
  height to the word on its left, that holds a value word and no other word with a letter. A
  value word opens a new run when the open run holds one, unless it is a raised digit after
  the word before it, which `lex_cell` reads as a mark, so no cell holds two amounts. A mark
  beside a label is in its label's run. Shape 7 as planned took a `$` for label text, so in
  `Tax $ 2.8 1` (VAL-Q28) the raised `1` seeded the only lane and `lex_cell` read 1 (Codex
  finding 1 on pull request 55). The first fix let a run join any close words. On page 1 of
  the January 2018 School collections report, `106,224,545` stands 4.75 points before
  `80,348,931` against a median word height of 7.20, so both went into the FY2017 cell and
  FY2018 was empty (Codex's read of that fix). With that review's layout, each amount now
  lands under its own year with no finding, and `Tax $ 2.8 1` reads 2.8 with the mark `1`. On
  the 40 grid fixtures the 24 marks in row labels stand 1.27 to 2.06 points after `Services`
  or `Aviation`, the smallest gap from a label to its first number is 38.94 points, on
  `Office of Behavioral Hlth & Intellectual disAbility` in `2021-09-30`, and two cells of a
  row stand at least 29.46 points apart, against a median word height of 7.44 on every row.
  Lanes cluster by the median cell height, and the widest lane spreads 3.82 points
  (`over_under`, page 32 of `2024-06-30`). A dump of every binding and raw row of the 40
  pages is the same under this rule, the first fix and the rule as planned.
  `test_a_mark_beside_a_label_seeds_no_lane`,
  `test_a_dollar_sign_and_a_raised_mark_cut_into_the_cell_of_their_number`,
  `test_a_dash_after_a_dollar_sign_cuts_into_one_cell` and
  `test_two_amounts_that_stand_close_seed_two_lanes_and_cut_into_two_cells`. Design section
  3.1.
- **`cut_pages` reads commentary and every page's era** (November 27, 2026, S5-B). Shape 6 as
  planned. The design chose the era once from the first page. Now every grid page's header must
  choose the same era, so a later page that lost a caption stops the table as the first does,
  and a page that names another era gives `eras_differ_by_page`. A page that `positional`
  names is a grid page whatever it prints, since its header is illegible. The tests of
  `test_pipeline.py` prove each outcome. Design section 3.1.
- **`Layout` names its table** (November 27, 2026, S5-B). A finding of `cut_pages` needs the
  subject `<doc sha8>:<table>`, and `cut_pages` already has four parameters, the most the shape
  test allows. So `Layout` gains `table`, the sha comes from the pages' words, and `cut_pages`
  sets the subject and page of each finding of `choose_era` and the binders, whose subject is
  an era's name. The design's parser examples pass `TABLE`. Design sections 2.1, 3.1, 5 and 11.3.
- **An era needs a signature** (November 27, 2026, S5-B). Under shape 6 an era with no
  signature regex makes every page commentary, so `Era` refuses it.
  `test_an_era_needs_a_signature_distinct_names_and_a_required_column`. Design section 2.1.
- **Step 2 of `bind_columns` waits** (November 27, 2026, S5-B). The design adds an empty lane
  for a required caption printed over no values (QCASH-Q35). No P-1 page prints that case, and
  where to put the lane needs a real page, so it is built at the step that parses the first page
  that prints it, as decision 18 does for decisions 13, 15, 16 and 17. `docs/plan-notes.md`
  holds the note for the step 8 plan. Design section 3.1.
- **The finding codes of the cut** (November 27, 2026, S5-B). The design named
  `table_not_found`, `several_runs`, `column_unbound` and `columns_differ_by_page`. This pull
  request names `era_not_found`, `several_eras` and `era_out_of_range` for `choose_era`;
  `columns_tie`, `lane_unclaimed` and `columns_out_of_order` for `bind_columns`, which reports
  the first of the tie, the unbound column, the unclaimed lane and the order, so a missing
  required caption is `column_unbound`; `lane_count_differs` for `bind_by_position`; and
  `commentary_page` (WARN), `commentary_after_grid`, `no_grid_page` and `eras_differ_by_page`
  for `cut_pages`. Each has a test in `test_columns.py`, `test_pages.py` or `test_pipeline.py`.
  Design section 3.1.
- **`slice_body` keeps every line, and `RawRow` keeps every column** (November 27, 2026, S5-B).
  Shape 8 as planned: a body line of only prefix words, such as the page number at the foot
  from `2023-06-30`, and every line below the stop line are furniture. A `RawRow` lists every
  column of its binding, with no words for one the page does not print, and `has_values` is
  true when a lane holds a word of the row. `RawRow.bold` is None when the row has no label
  word. Design section 2.1.
- **`RawRow.bold` is pinned, and the kit imports `date`** (November 27, 2026, S5-B). Shapes 11
  and 12 as planned: `test_bool_fields_are_page_facts_only` expects `("RawRow", "bold")`
  beside `("Word", "bold")`, and `datetime.date` joins the pin of `tests/test_purity.py`.
  Design sections 2, 11.1 and 11.4.
- **`low_confidence` joins `UnreadableReason`, and `Column.printed` joins the pinned `bool`
  fields** (November 27, 2026, S5-C). Shape 13 as planned: the floor rule of `assemble` gives
  the new reason, so its pin in `test_closed_lists_are_pinned` changes with the list (hard rule
  6). S5-C creates `Column`, and `test_bool_fields_are_page_facts_only` expects
  `("Column", "printed")`. Design sections 2.1 and 11.4.
- **The confidence floor reads only a cell that lexes as an `Amount`** (November 27, 2026, S5-C).
  Design section 3.1 had "an OCR value word under the confidence floor" become `Unreadable`,
  and a value word is also a dash or N/A. `assemble` applies readings before the floor, and
  `apply_reading` takes only an `Amount` or an `Unreadable`, so a dash under the floor could
  never be cleared by a reading. Section 8.3 says such words need a reading "before they lex
  as a number". No P-1 page is OCR, and `docs/plan-notes.md` leaves the dash and N/A case to the
  step 7 plan. `test_an_ocr_number_under_the_confidence_floor_is_low_confidence_until_a_reading_reads_it`
  holds a word at 94.9 to the floor of 95 and one at 95.0 clear of it. The answer was taken on
  November 27, 2026 while the owner was away, under his standing permission of November 27, and
  he has not seen the question. Design section 3.1.
- **How `match_rows` keeps its blocks** (November 27, 2026, S5-C). The design had a row with
  children in the schema open a block, and a row match "only when `within` is the open
  block". A block that only `within` names must open too, and a `Civilian` printed after an
  unknown line under `Police - Total` still belongs to Police. So a row opens a block when a
  definition names its key as `parent` or `within`, a matched row closes the blocks above its
  home (its `within`, else its `parent`), and an unmatched row closes none. `within` must be
  open. A probe that matched the 40 grid fixtures against a schema built from their own labels
  put all 120 `Civilian` and `Uniform` rows under their parent. Design section 3.1.
- **A wrapped label joins only a row of its page** (November 27, 2026, S5-C). Joined across a
  page break, a row's cells would lie on a page other than its own, and `assemble` hands
  `reading_for` the words of the row's page. Both lines are then `unknown_row`.
  `test_a_label_only_line_never_joins_a_row_on_the_next_page`. Design section 3.1.
- **The finding codes and subjects of rows and assembly** (November 27, 2026, S5-C). Section 7.3
  named the four row outcomes. This pull request adds `truncated_label` (WARN) for a prefix
  match, `stray_value` (BLOCK) and `stray_word` (WARN), and in `assemble`
  `duplicate_dash_rule`, `unreadable_cell`, `duplicate_key` and `dangling_parent`. Two dash
  rules on one dash block, as two readings do (`duplicate_reading`). `stray_findings` takes raw
  rows and no table name, so its subject is `<doc sha8>:stray:<printed label>`, as the reading
  findings use `<doc sha8>:reading:<id>`. Each code has a test in `test_rows.py` or
  `test_assemble.py`. Design section 3.1.
- **Four choices the design left open** (November 27, 2026, S5-C). `Row.label_words` holds the
  line number words and then the label words, the words of `Label.printed`, so every printed
  word of a row has a place in the table. A dash rule names itself on a `Dash` only when it
  sets ZERO, which keeps the `Dash` block true, and a record is in `used` only when it changed
  a cell. `starts_known_row` takes a line whose `normalize_label` text is a schema label or
  starts with one and a space. Tests in `test_assemble.py` and `test_rows.py`. Design sections
  2.1 and 3.1.
- **The ink property names its places** (November 27, 2026, S5-C). Section 11.2 listed a cell, a
  label, a prefix, furniture, and a stray-word or unknown-row finding. A header line is a place
  too, as clause C2 of the plan says, and an `ambiguous_row` finding names its raw row as
  `unknown_row` does. `misplaced` in `packages/checkedtables/tests/ink.py` counts the places, and
  says how a finding names a word or a row. The 100 pages that
  `test_no_ink_is_lost_on_a_generated_table_page` draws under the project's Hypothesis profile
  hold 681 raw rows, 174 unknown rows, 104 breakdown rows, 34 wrapped labels, 424 stray words
  and 35 OCR pages, and every word has one place. The probe above found none of the 18,541
  words of the 40 grid fixtures out of place.
  Design section 11.2.
- **A column's caption is the words on the header lines that bind it** (November 27 and 28,
  2026, S5-C fix rounds). `Column.caption`, which the release publishes as `caption_printed`, was
  the first page's lane caption: every header word over the lane, title lines included. On all
  20 P-1 editions some caption held title words, such as `TABLE P-1 CITY MANAGERS FULL TIME
  POSITIONS ALL FUNDS PERIOD ENDING JUNE ADOPTED General` for `adopted_general` on page 33 of
  `2026-06-30` (finding 1 of the Codex review). The first fix round kept only the words that the
  column's regexes matched, which dropped caption words too: the tenth P-1 column read
  `(OVER) UNDER`, and two columns of one regex, such as `month` and `month_prior` of section
  5.3, both read `MONTH OF` (finding 1 of Codex's read of that round). Now the new field
  `Binding.captions` holds, for each column bound by caption, its band's words on the header
  lines that its group regex matches, then its lane's words from the first header line that its
  caption regex matches to the last, and `assemble` captions each column with them. On all 40
  grid fixtures the page prints `MONTH END`, `ACTUAL (OVER)` and `UNDER BUDGET` over the tenth
  column, so the `over_under` regex of section 5.1 now starts at `MONTH`, and the tenth column
  reads `MONTH END ACTUAL (OVER) UNDER BUDGET`. The era, the lanes, the label edge and the raw
  rows of the 40 grid fixtures are the same at `d8ba4cb`, at `aab6e72` and after.
  `test_each_p1_caption_is_printed_over_its_column_and_holds_no_title_or_fiscal_year` in
  `tests/test_p1_captions.py`, and
  `test_two_columns_of_one_caption_regex_each_keep_the_period_printed_under_it`. The answer was
  taken on November 28, 2026 while the owner was away, under his standing permission of
  November 27, and he has not seen the question. Design sections 2.1, 3.1 and 5.1.
- **The registry loads from each file's text, and a loader refuses with `Refused`** (November 28,
  2026, S5-D). Shape 16 as planned. The design gave `load_registry` no signature, so it takes
  each file's path and text, as `load_records` does, and gives each record's first problem as a
  BLOCK finding. A file holds arrays of tables named by the `EntityKind` values, then `[[alias]]`
  and `[[relation]]`. `load.py` also holds the record readers that `rowschemas` shares, which is
  most of why it counts 147 lines against 110. `Resolved`, `Unknown`, `Ambiguous` and
  `Resolution` join `resolve` at step 8 (shape 14). `test_registry.py` and
  `test_rowschemas.py`. Design sections 2.2, 3.2 and 12.3.
- **A row's labels have one home in its type** (November 28, 2026, S5-D). `RowSource.labels` is
  `RegistryLabels | SchemaLabels`, so no row value holds both an entity and labels, and
  `load_row_schema` refuses a file that writes both with `rowschema_entity_with_labels` (clause
  C3b). An entity row with no `forms` prints its name alone. A row's period holds an edition
  when it holds the edition's period end, and `""` leaves an end open.
  `test_an_entity_row_with_labels_is_refused` fails with the refusal taken out. Design section
  3.2.
- **The positions rows are bounded by the 20 editions** (November 28, 2026, S5-D). Design section
  5.1 gave Streets the periods FY2008 to FY2013 and FY2018 to FY2025 from QPOS-Q12. A row that
  some of the 20 editions do not print now has periods that start at the first quarter that
  prints it, and end open when FY2026 Q4 prints it, so an older edition has neither Streets row
  until step 7 reads it. Matched against these schemas, all 1,174 cut rows of the 40 grid
  fixtures match one row each with no finding, and each edition's schema has the row count of
  fact 1. `test_every_cut_row_of_the_40_grid_pages_matches_one_schema_row`. Design section 5.1.
- **A group has no name** (November 28, 2026, S5-D). The old `config/entities.yml` names the
  rollup `Streets (including Sanitation)`, which none of the 20 editions prints. A group's P-1
  label is a table-scoped alias, and every spelling that the positions rows take from the files
  is a label that a grid fixture prints:
  `test_every_spelling_the_positions_rows_take_from_the_files_is_printed_on_a_grid_page`. Design
  sections 2.2 and 7.2.
- **A whole-year name is a label of editions that do not print it** (November 28, 2026,
  S5-D). The plan's S5-D section says each label of fact 12 is a label of the schemas of the
  editions that print it "and of no other". Shape 14 keeps the other spelling a name for the
  whole fiscal year, so `Fleet Services` is a label of `2021-09-30`, and `Office of Arts and
  Culture` of `2025-03-31` and `2025-06-30`, which print `Fleet Management` and `Creative
  Philadelphia`. Either spelling gives the row its one key. The test names those three pairs
  and requires the same row to hold the spelling the edition prints. `Creative Philadelphia` is
  also a name from FY2026, so its alias names the two FY2025 files alone.
  `test_each_label_that_changes_is_a_label_of_the_editions_that_print_it`. Design section 7.2.
- **The TOML loaders are written by hand** (November 28, 2026, S5-D). Section 8.7 of
  `docs/principles.md` leaves pydantic for `datadesk` to the owner at the step that builds the
  TOML loaders, from a run of a hand-written and a strict pydantic loader on the same TOML. The
  answer was taken on November 28, 2026 while the owner was away, under his standing permission
  of November 27, and he has not seen the question. The loaders are written by hand, as
  `load_catalog` and `parse_index` are, and typer stays below 0.29. The run was not made:
  `uv run --offline --no-project --with pydantic` fails because the uv cache holds no pydantic,
  and the session made no download. The two cases of pull request 38 are refused as findings:
  `id_not_a_string` and `member_not_a_string` in `test_registry.py`. Section 8.7 is unchanged.
- **A rows file holds no `label_editions`** (November 28, 2026, the S5-D fix round). Design
  section 6.1 named `label_editions` among the fields of `datadesk/data/rows/<table>.toml`, and
  `RowSource` in section 3.2 has no such field, so `load_row_schema` refuses it with
  `rowschema_unknown_field`. Step 5 binds no table line's label to a file: the two P-1 spellings
  that change inside a year are registry aliases with shas (shape 14). Section 6.1 now names
  `periods` and `absent_editions` alone, and the note for the step 9 plan keeps MSCH-Q23. A
  one-row schema that writes `label_editions = []` is refused with `rowschema_unknown_field`, as
  the `unknown_field` case of `test_load_row_schema_refuses_text_that_breaks_a_rule` refuses
  another field. Design section 6.1.
- **`parse` takes its drop patterns from the schema** (November 28, 2026, S5-E). The sketch of
  design section 5.1 passed `_FURNITURE`, whose `^Notes?:` does not match the printed `NOTE:`
  (finding 4 of the Fable read of pull request 58). With that list as the drop, each of the 20
  editions gives one BLOCK `unknown_row` for the notice under the rows of its first grid page.
  The schema's `drop` holds `^\(\d+\)\s` and `^NOTE:` (shape 10), and `parse` passes it. The
  sketch's title patterns are cut too: the body starts at the first row, so the title lines
  are header. `test_the_footnotes_and_the_notice_are_furniture_and_no_finding_names_them`.
  Design section 5.1.
- **A first row of counts that the schema lacks is a row, never header** (November 28, 2026,
  S5-E). The sketch started the body at `starts_known_row(schema)`, so a page whose first
  printed row the schema lacks put that row in the header with no finding (follow-up 7 of pull
  request 57).
  The body now also starts at a line that ends with a count for each column. No header line of
  the 40 grid pages ends so (fact 2), and `parse` gives equal results for the 20 editions under
  both rules. With `Auditing` renamed `Zoo` on page 33 of `2026-06-30`, the sketch's rule gives one
  BLOCK `missing_row` and puts the row in the header, and this rule also gives `unknown_row`
  for `Zoo (City Controller's Office)` on page 33.
  `test_a_first_row_that_the_schema_lacks_is_an_unknown_row_and_never_header` fails under the
  sketch's rule. Design section 5.1.
- **`parse` matches its unions** (November 28, 2026, S5-E). `parse` tells `PageRun` and
  `CutPages` from `Finding` with `match` and `assert_never`, where the sketch wrote
  `isinstance` (shape 16). Design section 5.1.
- **`ParseContext` derives its period and fiscal year, and checks its records** (November 28,
  2026, S5-E). Shape 17 builds `core/context.py` as designed. The design gave `period` and
  `fiscal_year` as fields beside `version`, which a builder could set apart from it, so they are
  properties of `version` (`docs/principles.md`, section 8.3). The constructor refuses two
  schemas of one table, since `schema` would take the first, and a note, a `TablePages` record
  or a reading of another sha, since `declared_run` reads no sha. `Failed` refuses findings with
  no BLOCK one. `test_context.py`. Design section 2.2.
- **`TablePages`, `declared_run` and `illegible_pages`** (November 28, 2026, S5-E). Shape 17 as
  planned: `parse` calls both functions with no record, and no loader is built. A `TablePages`
  record refuses a first page under 1 and a last page before its first. `declared_run` raises
  `ValueError` when two records name one table, and the note for the step 7 plan asks its
  records loader to refuse such a pair. A HEADER_ILLEGIBLE note on no page names no page.
  `test_records.py`. Design sections 2.2 and 3.2.
- **`Parsed` carries the cut of each table** (November 28, 2026, the S5-E fix round). Design
  section 2.2 gave `Parsed` the tables, the findings and the used ids, and none of them holds
  the header and furniture lines. So the test of clause C2 built a cut of its own with a public
  `layout`, and a word that `parse` lost before its cut was placed by the test's cut. With
  `parse` dropping the `NOTE:` line of each of the 40 grid pages, the test passed and 960 words
  were in no place (blocker 1 of Codex's review of pull request 59). `Parsed.cuts` now holds the
  cut each table was assembled from, and the constructor refuses a table with no cut. The test
  counts the ink of that cut, and fails under the same mutant. `layout` is private again, since
  no test rebuilds the cut, and the sketches of sections 5.2, 5.3 and 5.5 pass their cuts. No
  codec of a parse result is built yet. `test_no_ink_is_lost_on_any_grid_page` and
  `test_a_parsed_table_needs_its_cut`. Design sections 2.2, 5.1, 5.2, 5.3 and 5.5.
- **C3a's test reads the printed labels against a table of its own** (November 28, 2026, the
  S5-E second fix round). This changes no design section. The first fix round's test compared
  registry spellings with `row.label.norm`, the field the matcher used, so `Law` and `Water`
  swapped after normalization in `parse_label` passed it (finding 1 of Codex's read of that
  round), and so did `Law` and `Prisons` traded in `departments.toml` (finding 3 of the Fable
  read). The test now reads each entity row's label from the fixture page's words by the row's
  `label_words`, without the margin words left of the first rule and without a footnote mark.
  That label with the row's entity must be in a literal table of 61 pairs, 8 of them scoped by
  edition, and the registry files must write it under that id. A script built the table from
  the fixture words and the registry files. Its pairs equal those that `parse` gives, and 59 of
  the 61 are a name or alias of the same id in the old `config/entities.yml`, which lacks the
  two group ids. Under each of those two mutants, and under `Finance` and `Revenue` swapped in
  `labels_for`, the test fails. The first round's rewrite of the plan's C3a paragraph is
  undone, since no pull request still to be built reads it (`docs/plans/README.md`).
  `test_each_department_label_is_a_registry_label`.
