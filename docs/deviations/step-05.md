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
  line `Note for FY.. Q.:`, which runs from 305.06 to 315.06 with a median height of 10.00, so both
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
