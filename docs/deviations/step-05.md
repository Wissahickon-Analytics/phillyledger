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
