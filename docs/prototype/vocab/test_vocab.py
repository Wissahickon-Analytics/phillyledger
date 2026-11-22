"""Run: python3 test_vocab.py. Checks every declared column and writes COLUMNS.md."""

from __future__ import annotations

import sys
from collections import Counter
from datetime import date

from measures import (Basis, Derived, MeasureSet, NotPublished, Scope, Stated, describe, measure_for,
                      period_of, subject_of)
from tables import (BIB_ADOPTED, BIB_PROPOSED, DECLS, JUL_2024, MAR_2022, Q1_FY09_CASH, Q1_FY25,
                    Q1_FY25_CASH, Q2_FY24, Q4_FY24, Decl)
from vocab import ALL, DIM_VALUES, FUND_IDS, Dim, How, Kind, Quantity, Version, Window


def by_name(ms: MeasureSet) -> dict[str, object]:
    return {c.column: c for c in ms.columns}


def find(table: str, era: str) -> Decl:
    return next(d for d in DECLS if d.table == table and d.era == era)


def check_decl(d: Decl) -> None:
    names = [c for c, _ in d.captions]
    assert len(names) == len(set(names)), (d.table, d.era, "duplicate column name")
    assert d.provisional <= set(names), (d.table, d.era, "provisional name not in layout",
                                         sorted(d.provisional - set(names)))
    for s in d.scopes:
        ms = d.measures(s)
        got = [c.column for c in ms.columns]
        assert got == names, (d.table, d.era, "columns differ from captions", got, names)
        # 1. no two published columns share a description
        seen: dict[tuple[object, ...], str] = {}
        for c in ms.columns:
            if isinstance(c.meaning, NotPublished):
                continue
            key = describe(c.meaning)
            assert key not in seen, (d.table, d.era, "same description", seen[key], c.column)
            seen[key] = c.column
        # 2. every operand of a derived column is a published column of the same table
        published = {c.column for c in ms.columns if not isinstance(c.meaning, NotPublished)}
        for c in ms.columns:
            if isinstance(c.meaning, Derived):
                missing = [o for o in c.meaning.of if o not in published]
                assert not missing, (d.table, d.era, c.column, "operand not a published column", missing)
        # 3. dimension values are from the closed lists
        for c in ms.columns:
            dims = getattr(c.meaning, "dims", ())
            for dim, value in dims:
                if dim is Dim.FUND:
                    assert value == ALL or value in FUND_IDS, (c.column, value)
                else:
                    assert value in DIM_VALUES[dim], (c.column, dim, value)
        # 4. a row override names a declared column, and two overrides of one column never
        #    match the same row: their matches must disagree on some key part
        for r in ms.rows:
            assert r.column in names, (d.table, r.column)
        for i, a in enumerate(ms.rows):
            for b in ms.rows[i + 1:]:
                if a.column == b.column:
                    da, db = dict(a.match), dict(b.match)
                    assert any(k in db and db[k] != v for k, v in da.items()), (d.table, a.match, b.match)
        # 5. a derived column's unit follows its kind of derivation
        for c in ms.columns:
            if isinstance(c.meaning, Derived) and c.meaning.how in (How.PERCENT_CHANGE, How.RATIO, How.SHARE,
                                                                   How.ANNUAL_GROWTH):
                assert c.unit == "percent", (d.table, c.column, c.unit)


def subject(table: str, era: str, s: Scope, column: str):
    return subject_of(by_name(find(table, era).measures(s))[column], s)   # type: ignore[arg-type]


def test_pinned_lists() -> None:
    # literal lists: a new word fails here and needs a reviewed edit and a definition
    assert [k.value for k in Kind] == ["actual", "budget", "projection"]
    assert [v.value for v in Version] == ["none", "adopted", "revised", "proposed", "target"]
    assert [w.value for w in Window] == ["month", "quarter", "fiscal_ytd", "calendar_ytd",
                                         "fiscal_year", "calendar_year", "tax_year"]
    assert [h.value for h in How] == ["difference", "percent_change", "ratio", "share", "annual_growth"]
    assert [x.value for x in Dim] == ["fund", "residency", "tax_base"]
    assert len(Quantity) == 14


def test_review_fixes() -> None:
    from tables import Q1_FY25_CASH, Q4_FY26
    # legacy cash: Under (Over) = Budget - Total - Accrued
    legacy = by_name(find("qcmr_cash_revenue", "legacy").measures(Q1_FY25_CASH))
    assert legacy["under_over"].meaning.of == ("budget", "total", "accrued")              # type: ignore[attr-defined]
    # O-3: the positions rows are counts at a point, the dollar rows are not
    o3 = find("qcmr_personal_services", "in_year").measures(Q2_FY24)
    pos = measure_for(o3, (("metric", "positions"), ("section", "phl_dept_police")), "adopted")
    usd = measure_for(o3, (("metric", "class_100"), ("section", "phl_dept_police")), "adopted")
    assert (pos.unit, pos.basis, usd.unit, usd.basis) == ("positions", Basis.POINT, "USD", Basis.FLOW)
    # cash: a month's opening balance is the previous month's closing balance
    life = find("qcmr_cash_lifecycle", "rows").measures(Q1_FY25_CASH)
    opening = (("grid", "lifecycle"), ("line", "opening_balance"))
    closing = (("grid", "lifecycle"), ("line", "closing_balance"))
    for m in range(2, 13):
        o = subject_of(measure_for(life, opening, f"m{m:02d}"), Q1_FY25_CASH)
        c = subject_of(measure_for(life, closing, f"m{m - 1:02d}"), Q1_FY25_CASH)
        assert o == c, m
    july_open = subject_of(measure_for(life, opening, "m01"), Q1_FY25_CASH)
    assert july_open is not None and july_open.end == date(2024, 6, 30)
    assert measure_for(life, closing, "m05").basis is Basis.POINT
    # QSMR OF-1 FY2023: projection minus amended, no adopted column
    of23 = by_name(find("qsmr_operating", "of_2023").measures(Q4_FY26))
    assert "adopted" not in of23 and of23["over_under"].meaning.of == ("projection", "amended")  # type: ignore[attr-defined]
    # O-2 FY2026 Q4 prints six columns
    assert len(find("qcmr_obligations", "year_end").captions) == 6


def test_matching() -> None:
    # a quarter-end count is the same fact as next year's "Year-End Actual" when the quarter is Q4
    assert subject("qcmr_positions", "p1_ten_columns", Q4_FY24, "actual_total") == \
        subject("qcmr_positions", "p1_ten_columns", Q1_FY25, "prior_total")
    assert subject("qcmr_positions", "p1_ten_columns", Q2_FY24, "actual_total") != \
        subject("qcmr_positions", "p1_ten_columns", Q1_FY25, "prior_total")
    # Q4 year to date is the same span as next year's prior-year actual
    assert subject("qcmr_obligations", "nine", Q4_FY24, "ytd_actual") == \
        subject("qcmr_obligations", "nine", Q1_FY25, "prior_actual")
    # the adopted budget is one subject in every quarter of the fiscal year
    assert subject("qcmr_obligations", "nine", Q2_FY24, "adopted") == \
        subject("qcmr_obligations", "nine", Q4_FY24, "adopted")
    # the three columns the old repo filed under one role are three subjects
    o2 = [subject("qcmr_obligations", "nine", Q2_FY24, c) for c in ("ytd_target", "adopted", "target")]
    assert len(set(o2)) == 3
    # July: the month and the fiscal year to date cover the same days
    assert subject("collections_city", "ordinary", JUL_2024, "month") == \
        subject("collections_city", "ordinary", JUL_2024, "fytd")
    assert subject("collections_city", "ordinary", MAR_2022, "month") != \
        subject("collections_city", "ordinary", MAR_2022, "fytd")
    # the denominator of percent collected follows what the edition prints
    city = find("collections_city", "ordinary")
    assert by_name(city.measures(JUL_2024))["pct"].meaning.of == ("fytd", "budget")           # type: ignore[attr-defined]
    assert by_name(city.measures(MAR_2022))["pct"].meaning.of == ("fytd", "revised_budget")   # type: ignore[attr-defined]
    # cash months switch from actual to projection at the edition's cutoff
    rev = find("qcmr_cash_revenue", "modern")
    q1 = by_name(rev.measures(Q1_FY25_CASH))
    assert [q1[f"m{m:02d}"].meaning.kind for m in (1, 3, 4, 12)] == \
        [Kind.ACTUAL, Kind.ACTUAL, Kind.PROJECTION, Kind.PROJECTION]                            # type: ignore[attr-defined]
    assert q1["total"].meaning.kind is Kind.PROJECTION                                           # type: ignore[attr-defined]
    fy09 = by_name(find("qcmr_cash_revenue", "legacy").measures(Q1_FY09_CASH))
    assert fy09["m04"].meaning.kind is Kind.ACTUAL and fy09["m05"].meaning.kind is Kind.PROJECTION   # type: ignore[attr-defined]
    # October projected in the Q1 edition is not the same subject as October actual
    assert subject("qcmr_cash_revenue", "modern", Q1_FY25_CASH, "m04").kind is Kind.PROJECTION
    # the budget column of a proposed book is a proposed budget
    hist = find("bib_history", "six")
    assert by_name(hist.measures(BIB_ADOPTED))["budget"].meaning.version is Version.ADOPTED     # type: ignore[attr-defined]
    assert by_name(hist.measures(BIB_PROPOSED))["budget"].meaning.version is Version.PROPOSED   # type: ignore[attr-defined]
    # the fiscal-year basis of a window: FY2026 July to December is calendar 2025
    s = find("wage_industry", "nine").scopes[3]
    spec = by_name(find("wage_industry", "nine").measures(s))["current"]
    assert period_of(spec.meaning, s).start == date(2024, 7, 1)                                  # type: ignore[arg-type]


def phrase(meaning: object, basis: Basis) -> tuple[str, str, str, str]:
    """(kind, time, counts or slice, computed from) for the reference table."""
    if isinstance(meaning, NotPublished):
        return ("not published", "", "", meaning.reason)
    if isinstance(meaning, Derived):
        if meaning.how is How.DIFFERENCE:
            return ("difference", "", ", ".join(f"{d.value} = {v}" for d, v in meaning.dims),
                    " minus ".join(f"`{o}`" for o in meaning.of))
        how = {How.PERCENT_CHANGE: "percent change, {0} over {1}",
               How.RATIO: "{0} as a percent of {1}", How.SHARE: "share of {0}",
               How.ANNUAL_GROWTH: "yearly growth rate, {1} to {0}"}[meaning.how]
        dims = ", ".join(f"{d.value} = {v}" for d, v in meaning.dims)
        return (meaning.how.value.replace("_", " "), "", dims,
                how.format(*(f"`{o}`" for o in meaning.of)))
    assert isinstance(meaning, Stated)
    kind = meaning.kind.value + (f", {meaning.version.value}" if meaning.kind is Kind.BUDGET else "")
    window = meaning.window.value.replace("_", " ")
    if meaning.month is not None:
        window = f"fiscal month {meaning.month}"
    if basis is Basis.POINT:
        window = f"level at end of {window}"
    time = window + (f", {abs(meaning.year)} year{'s' if abs(meaning.year) > 1 else ''} back" if meaning.year else "")
    what = [meaning.quantity.value.replace("_", " ")] if meaning.quantity else []
    what += [f"{d.value} = {v}" for d, v in meaning.dims]
    return (kind, time, ", ".join(what), "")


def render() -> str:
    out: list[str] = []
    for d in DECLS:
        s = d.scopes[0]
        ms = d.measures(s)
        tag = " (held out)" if d.held_out else ""
        out.append(f"### `{d.table}`, era `{d.era}`{tag}\n")
        out.append("| Printed column | Name | Kind | Time | Counts or slice | Computed from | |")
        out.append("|---|---|---|---|---|---|---|")
        caps = dict(d.captions)
        for c in ms.columns:
            kind, time, what, of = phrase(c.meaning, c.basis)
            flag = "provisional" if c.column in d.provisional else ""
            out.append(f"| {caps[c.column]} | `{c.column}` | {kind} | {time} | {what} | {of} | {flag} |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    for d in DECLS:
        check_decl(d)
    test_matching()
    test_pinned_lists()
    test_review_fixes()
    in_scope = [d for d in DECLS if not d.held_out]
    held = [d for d in DECLS if d.held_out]
    cols = sum(len(d.captions) for d in in_scope)
    prov = sum(len(d.provisional) for d in in_scope)
    kinds: Counter[str] = Counter()
    used_q: set[Quantity] = set()
    used_w: set[Window] = set()
    used_v: set[Version] = set()
    used_h: set[How] = set()
    held_q: set[Quantity] = set()
    not_published = 0
    for d in DECLS:
        for s in d.scopes:
            for c in d.measures(s).columns:
                m = c.meaning
                if isinstance(m, Stated):
                    (held_q if d.held_out else used_q).update({m.quantity} - {None})   # type: ignore[arg-type]
                    if not d.held_out:
                        used_w.add(m.window); used_v.add(m.version)
                elif isinstance(m, Derived) and not d.held_out:
                    used_h.add(m.how)
        if not d.held_out:
            for c in d.measures(d.scopes[0]).columns:
                m = c.meaning
                if isinstance(m, NotPublished):
                    not_published += 1; kinds["not published"] += 1
                elif isinstance(m, Derived):
                    kinds["derived: " + m.how.value] += 1
                else:
                    kinds[m.kind.value] += 1
    assert used_q == set(Quantity), set(Quantity) - used_q
    assert used_w == set(Window), set(Window) - used_w
    assert used_v == set(Version), set(Version) - used_v
    assert used_h == set(How), set(How) - used_h
    assert held_q <= used_q, held_q - used_q
    tables = sorted({d.table for d in in_scope})
    print(f"in scope: {len(tables)} column sets, {len(in_scope)} eras, {cols} columns, "
          f"{sum(len(d.scopes) for d in in_scope)} sample editions")
    print(f"provisional: {prov} columns; not published: {not_published}")
    print("kinds:", dict(sorted(kinds.items())))
    print(f"held out: {len(held)} eras, {sum(len(d.captions) for d in held)} columns, "
          f"new list members needed: {sorted(q.value for q in held_q - used_q)}")
    print("list sizes:", {k: len(v) for k, v in (("Kind", Kind), ("Version", Version), ("Window", Window),
                                                  ("How", How), ("Dim", Dim), ("Quantity", Quantity))})
    if "--write" in sys.argv:
        with open("COLUMNS.md", "w") as f:
            f.write(render())
        print("wrote COLUMNS.md")
    print("all checks passed")


if __name__ == "__main__":
    main()
