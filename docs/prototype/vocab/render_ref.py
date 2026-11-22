"""Render the column reference from the tested declarations, merging layouts with equal descriptions."""
from __future__ import annotations
import re
from measures import Basis, Derived, NotPublished, Stated
from tables import DECLS
from vocab import How, Kind

TITLES = {
    "qcmr_positions": "QCMR positions (P-1)", "qcmr_obligations": "QCMR obligations (O-2)",
    "qcmr_personal_services": "QCMR personal services (O-3)", "qcmr_cash_revenue": "QCMR cash, revenue grid",
    "qcmr_cash_expense": "QCMR cash, expense grid", "qcmr_cash_lifecycle": "QCMR cash, balance rows",
    "qcmr_cash_balances": "QCMR cash, fund balances (page 2)", "collections_city": "Monthly City collections",
    "collections_school": "Monthly School collections", "wage_industry": "Wage tax by industry",
    "wage_residency_summary": "Wage tax by residency, summary", "wage_residency_detail": "Wage tax by residency, detail",
    "birt": "BIRT by sector", "sales": "Sales tax by sector", "rtt": "Realty transfer tax",
    "bib_history": "Budget in Brief, General Fund obligation history", "bib_fund_summary": "Budget in Brief, fund summary",
    "bib_revenue_schedule": "Budget in Brief, revenue schedules", "supp_activity": "Supplemental, appropriation activity",
    "supp_revenues": "Supplemental, net revenues", "supp_capital_activity": "Supplemental, capital activity",
    "supp_capital_prior": "Supplemental, capital prior years", "supp_capital_summary": "Supplemental, capital summary",
    "qsmr_operating": "QSMR operating funds (held out)", "qsmr_cash_adopted": "QSMR adopted cash flow (held out)",
    "qsmr_positions": "QSMR positions (held out)", "qsmr_vendor_payments": "QSMR vendor payments (held out)",
}
HOW = {How.DIFFERENCE: "{0} minus {1}", How.PERCENT_CHANGE: "% change, {0} over {1}",
       How.RATIO: "{0} as % of {1}", How.SHARE: "share of {0}", How.ANNUAL_GROWTH: "yearly growth, {1} to {0}"}


def describe(meanings, bases) -> str:
    ms = list(dict.fromkeys(meanings))
    m0 = ms[0]
    if isinstance(m0, NotPublished):
        return "not published: " + m0.reason
    if isinstance(m0, Derived):
        ofs = [m.of for m in ms]
        parts = []
        for i in range(len(m0.of)):
            alts = list(dict.fromkeys(o[i] for o in ofs))
            parts.append(" or ".join(f"`{a}`" for a in alts))
        text = " minus ".join(parts) if m0.how is How.DIFFERENCE else HOW[m0.how].format(*parts)
        dims = ", ".join(f"{v}" for d, v in m0.dims)
        return text + (f" ({dims})" if dims else "")
    kinds = sorted(dict.fromkeys(m.kind for m in ms), key=list(Kind).index)
    versions = list(dict.fromkeys(m.version for m in ms))
    if len(kinds) > 1:
        kind = " or ".join(k.value for k in kinds) + " by cutoff"
    elif kinds[0] is Kind.BUDGET:
        kind = "budget, " + " or ".join(v.value for v in versions) + (" by book" if len(versions) > 1 else "")
    else:
        kind = kinds[0].value
    w = m0.window.value.replace("_", " ").replace("ytd", "to date")
    if len({m.window for m in ms}) > 1:
        w = "the window the table title names"
    if m0.month is not None:
        w = f"fiscal month {m0.month}" if len({m.month for m in ms}) == 1 else "a month of the quarter"
    if Basis.POINT in bases:
        w = "level at end of " + w
    if m0.year:
        w += f", {abs(m0.year)} yr back"
    extra = []
    if m0.quantity:
        extra.append(m0.quantity.value.replace("_", " "))
    extra += [v.replace("_", " ") if d.value != "fund" else f"fund {v}" for d, v in m0.dims]
    return f"{kind}; {w}" + (f"; {', '.join(extra)}" if extra else "")


def render(held_out: bool) -> str:
    out = []
    tables = list(dict.fromkeys(d.table for d in DECLS if d.held_out == held_out))
    for t in tables:
        decls = [d for d in DECLS if d.table == t]
        rows: dict[tuple[str, str], dict] = {}
        for d in decls:
            caps = dict(d.captions)
            per_col: dict[str, list] = {}
            bases: dict[str, set] = {}
            for s in d.scopes:
                for c in d.measures(s).columns:
                    per_col.setdefault(c.column, []).append(c.meaning)
                    bases.setdefault(c.column, set()).add(c.basis)
            for name, _ in d.captions:
                desc = describe(per_col[name], bases[name])
                key = (name, desc)
                r = rows.setdefault(key, {"caption": caps[name], "eras": [], "prov": False})
                r["eras"].append(d.era)
                r["prov"] |= name in d.provisional
        multi = len(decls) > 1
        out.append(f"### {TITLES[t]}\n")
        head = "| Printed column | Name | Description |" + (" Layouts |" if multi else "")
        out.append(head)
        out.append("|---|---|---|" + ("---|" if multi else ""))
        items = list(rows.items())
        merged = []
        for (name, desc), r in items:
            m = re.fullmatch(r"m(\d\d)", name)
            if m and merged and merged[-1][2] is not None:
                pname, pdesc, prange, pr = merged[-1]
                key = re.sub(r"fiscal month \d+", "fiscal month N", desc)
                if key == re.sub(r"fiscal month \d+", "fiscal month N", pdesc) and pr["eras"] == r["eras"]:
                    merged[-1] = (pname, pdesc, (prange[0], int(m.group(1))), pr)
                    continue
            merged.append((name, desc, (int(m.group(1)),) * 2 if m else None, r))
        MONTHS = ("July", "August", "September", "October", "November", "December",
                  "January", "February", "March", "April", "May", "June")
        rendered = []
        for name, desc, rng, r in merged:
            if rng and rng[0] != rng[1]:
                a, b = rng
                r = dict(r, caption=f"{MONTHS[a - 1]} to {MONTHS[b - 1]}")
                name = f"m{a:02d}` to `m{b:02d}"
                desc = re.sub(r"fiscal month \d+", f"fiscal months {a} to {b}", desc)
            rendered.append((name, desc, r))
        for name, desc, r in rendered:
            flag = " (provisional)" if r["prov"] else ""
            line = f"| {r['caption']} | `{name}` | {desc}{flag} |"
            if multi:
                eras = r["eras"]
                line += (" all |" if len(eras) == len(decls) else f" {', '.join(eras)} |")
            out.append(line)
        if t == "qcmr_cash_lifecycle":
            out.append("")
            out.append("Opening Balance and CLOSING BALANCE are levels in every column. A month's opening "
                       "balance is the level at the end of the month before, so July's is last June's close. "
                       "The thirteenth column is the year's opening or closing level. Row overrides say so.")
        if t == "qcmr_personal_services":
            out.append("")
            out.append("On the Full-Time Positions rows every column is a count of positions at a point in "
                       "time, not dollars. Row overrides say so.")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    body = render(False)
    held = render(True)
    open("REFERENCE.md", "w").write(body + "\n## Held out: QSMR\n\n" + held)
    print(len(body), len(held))
