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
