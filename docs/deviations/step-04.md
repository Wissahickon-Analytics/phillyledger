# Step 4: deviations from the design

What step 4 changed in `docs/design.md`, and why. The design holds each rule as it now stands,
so read this file only to learn why the design says what it says. Each entry: what changed,
why, the run that shows it, and the design section updated. Fact and shape numbers refer to
`docs/plans/step-04.md`.

- **Step 4: no font repair, and the check names the pages** (November 25, 2026, the Plan run).
  The design had the PDF adapter port `repair_cid_words`, and its check spoke of "all 20 grid
  pages with font codes" and of "the repaired digits". `page.extract_words()` of pdfplumber
  0.11.10 on every page of the 20 archived files returned no word that holds `(cid:` (fact 1).
  The codes are in the old repo's cut copies and the owner's older whole copies, which have other
  shas, and the Codex review of November 22 surveyed the cut copies (fact 2). The old repair also
  tries offsets 0 to 64 and scores each on English words, a search over hypotheses, which hard
  rule 4 of `CLAUDE.md` forbids. Shown this, the owner chose "Leave it out (Recommended)" (answer
  1). The
  step's list drops the repair. Its check now reads "On the 20 P-1 grid pages of FY2023 Q1 to
  FY2025 Q2, no word holds `(cid:`, and a rendered crop of each page's first and last department
  rows matches the extracted digits." The paragraph above the list says that the archive prints
  no font code, and counts 16 commentary pages where it said six (fact 8). Design sections 15,
  18.1 and 18.5.
