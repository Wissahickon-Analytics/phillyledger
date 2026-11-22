"""Every in-scope column, declared with the vocabulary. One function per table, as a table module would have.

Each entry of DECLS is (table, era, captions, measures function, sample scopes, provisional column names).
`captions` maps a column name to the printed caption, in print order.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal
from typing import Callable

from measures import (Basis, Derived, Meaning, MeasureSet, MeasureSpec, NotPublished, Period,
                      RowMeasure, Scope, Stated, fiscal_month, fiscal_year_of)
from vocab import ALL, Dim, How, Kind, Quantity, Version, Window

ONE = Decimal(1)


def spec(column: str, meaning: Meaning, unit: str = "USD", scale: Decimal = ONE,
         basis: Basis = Basis.FLOW) -> MeasureSpec:
    return MeasureSpec(column, meaning, unit, scale, basis)


def pct(column: str, meaning: Meaning) -> MeasureSpec:
    return MeasureSpec(column, meaning, "percent", ONE, Basis.FLOW)


def scope(start: date, end: date, stage: str = "none", instance: tuple[tuple[str, str], ...] = (),
          printed: frozenset[str] = frozenset(), actual_through: date | None = None) -> Scope:
    return Scope(Period(start, end), stage, instance, printed, actual_through or end)


@dataclass(frozen=True)
class Decl:
    table: str
    era: str
    captions: tuple[tuple[str, str], ...]
    measures: Callable[[Scope], MeasureSet]
    scopes: tuple[Scope, ...]
    provisional: frozenset[str] = frozenset()
    held_out: bool = False


# ----------------------------------------------------------------------------- QCMR positions
_FUND = {"general": "phl_fund_general", "other": "phl_fund_other", "total": ALL}
_P1_GROUP = {
    "prior": Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1),       # level at the end of last year
    "adopted": Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED),
    "actual": Stated(Kind.ACTUAL, Window.QUARTER),                   # level at the quarter end
}


def qcmr_positions(s: Scope) -> MeasureSet:
    def count(column: str, meaning: Meaning) -> MeasureSpec:
        return spec(column, meaning, unit="positions", basis=Basis.POINT)
    fund_columns = tuple(
        count(f"{g}_{f}", replace(_P1_GROUP[g], dims=((Dim.FUND, _FUND[f]),)))
        for g in _P1_GROUP for f in _FUND)
    variance = count("over_under", Derived(How.DIFFERENCE, of=("adopted_total", "actual_total")))
    return MeasureSet((*fund_columns, variance))


_P1_CAPS = tuple(
    (f"{g}_{f}", f"{gc}: {fc}")
    for g, gc in (("prior", "Year-End Actual"), ("adopted", "Adopted Budget"), ("actual", "Month End Actual"))
    for f, fc in (("general", "General"), ("other", "Other"), ("total", "Total"))
) + (("over_under", "(Over) Under Budget"),)

Q2_FY24 = scope(date(2023, 10, 1), date(2023, 12, 31))
Q4_FY24 = scope(date(2024, 4, 1), date(2024, 6, 30))
Q4_FY26 = scope(date(2026, 4, 1), date(2026, 6, 30))
Q1_FY25 = scope(date(2024, 7, 1), date(2024, 9, 30))


# ----------------------------------------------------------------------------- QCMR O-2 and O-3
def _projection_block() -> tuple[MeasureSpec, ...]:
    return (
        spec("adopted", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED)),
        spec("target", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.TARGET)),
        spec("projection", Stated(Kind.PROJECTION, Window.FISCAL_YEAR)),
        spec("projection_vs_adopted", Derived(How.DIFFERENCE, of=("adopted", "projection"))),
        spec("projection_vs_target", Derived(How.DIFFERENCE, of=("target", "projection"))),
    )


def _ytd_block() -> tuple[MeasureSpec, ...]:
    return (
        spec("ytd_target", Stated(Kind.BUDGET, Window.FISCAL_YTD, version=Version.TARGET)),
        spec("ytd_actual", Stated(Kind.ACTUAL, Window.FISCAL_YTD)),
        spec("ytd_variance", Derived(How.DIFFERENCE, of=("ytd_target", "ytd_actual"))),
    )


def qcmr_obligations(s: Scope) -> MeasureSet:
    return MeasureSet((spec("prior_actual", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1)),
                       *_ytd_block(), *_projection_block()))


_O2_CAPS = (("prior_actual", "Prior Year Actual"), ("ytd_target", "YTD Target Plan"),
            ("ytd_actual", "YTD Actual"), ("ytd_variance", "YTD (Over) Under Target"),
            ("adopted", "Adopted Budget"), ("target", "Target Budget"),
            ("projection", "Current Projection"),
            ("projection_vs_adopted", "Projection (Over) Under Adopted"),
            ("projection_vs_target", "Projection (Over) Under Target"))


def _prior_actuals(names: tuple[str, ...]) -> tuple[MeasureSpec, ...]:
    return tuple(spec(n, Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-k))
                 for n, k in zip(names, (3, 2, 1)))


_POSITIONS_ROW = (("metric", "positions"),)    # "Full-Time Positions" under the same headers


def _positions_rows(columns: tuple[MeasureSpec, ...]) -> tuple[RowMeasure, ...]:
    """O-3 prints counts and dollars under one header; the positions rows are counts."""
    return tuple(RowMeasure(_POSITIONS_ROW, c.column, replace(c, unit="positions", basis=Basis.POINT))
                 for c in columns)


def qcmr_ps_in_year(s: Scope) -> MeasureSet:
    cols = (*_prior_actuals(("actual_fy3", "actual_fy2", "unaudited_actual")),
            *_ytd_block(), *_projection_block())
    return MeasureSet(cols, rows=_positions_rows(cols))


def qcmr_ps_year_end(s: Scope) -> MeasureSet:
    cols = (*_prior_actuals(("actual_fy3", "actual_fy2", "actual_fy1")), *_projection_block())
    return MeasureSet(cols, rows=_positions_rows(cols))


def qcmr_obligations_year_end(s: Scope) -> MeasureSet:
    """FY2026 Q4 prints six columns: no YTD block."""
    return MeasureSet((spec("prior_actual", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1)),
                       *_projection_block()))


_O2_YEAR_END_CAPS = (("prior_actual", "Prior Year Actual"), ("adopted", "Adopted Budget"),
                     ("target", "Target Budget"), ("projection", "Current Projection"),
                     ("projection_vs_adopted", "Projection (Over) Under Adopted"),
                     ("projection_vs_target", "Projection (Over) Under Target"))


_O3_TAIL = (("adopted", "Adopted Budget"), ("target", "Target Budget"),
            ("projection", "Year-End Projection"),
            ("projection_vs_adopted", "Projection (Over) Under Adopted"),
            ("projection_vs_target", "Projection (Over) Under Target"))
_O3_IN_YEAR_CAPS = (("actual_fy3", "Year-End Actual (FY-3)"), ("actual_fy2", "Year-End Actual (FY-2)"),
                    ("unaudited_actual", "Unaudited Actual"), ("ytd_target", "YTD Target Plan"),
                    ("ytd_actual", "YTD Actual"), ("ytd_variance", "YTD (Over) Under Target"),
                    *_O3_TAIL)
_O3_YEAR_END_CAPS = (("actual_fy3", "Year-End Actual (FY-3)"), ("actual_fy2", "Year-End Actual (FY-2)"),
                     ("actual_fy1", "Year-End Actual (FY-1)"), *_O3_TAIL)


# ----------------------------------------------------------------------------- QCMR cash
_MILLIONS = Decimal(1_000_000)
_MONTH_NAMES = ("July", "August", "September", "October", "November", "December",
                "January", "February", "March", "April", "May", "June")


_BUDGET_BASIS_ESTIMATE = Stated(Kind.PROJECTION, Window.FISCAL_YEAR, quantity=Quantity.BUDGET_BASIS)
_BUDGET_BASIS_BUDGET = Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED,
                              quantity=Quantity.BUDGET_BASIS)


def _by_cutoff(s: Scope, window_end: date) -> Kind:
    return Kind.ACTUAL if window_end <= s.actual_through else Kind.PROJECTION


def _cash_months(s: Scope, basis: Basis = Basis.FLOW) -> tuple[MeasureSpec, ...]:
    fy = fiscal_year_of(s.period.end)
    return tuple(
        spec(f"m{m:02d}", Stated(_by_cutoff(s, fiscal_month(fy, m).end), Window.MONTH, month=m),
             scale=_MILLIONS, basis=basis)
        for m in range(1, 13))


def _cash_year(s: Scope, column: str, quantity: Quantity | None = None) -> MeasureSpec:
    year_end = fiscal_month(fiscal_year_of(s.period.end), 12).end
    return spec(column, Stated(_by_cutoff(s, year_end), Window.FISCAL_YEAR, quantity=quantity),
                scale=_MILLIONS)


def _cash_revenue(era: str) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        head = (*_cash_months(s), _cash_year(s, "total"),
                _cash_year(s, "accrued", Quantity.ACCRUALS))
        if era == "legacy":
            tail: tuple[MeasureSpec, ...] = (
                spec("under_over", Derived(How.DIFFERENCE, of=("budget", "total", "accrued")), scale=_MILLIONS),
                spec("budget", _BUDGET_BASIS_BUDGET, scale=_MILLIONS))
        elif era == "middle":
            tail = (spec("estimate", _BUDGET_BASIS_ESTIMATE, scale=_MILLIONS),)
        else:
            tail = (_cash_year(s, "not_accrued", Quantity.NOT_ACCRUED),
                    spec("estimate", _BUDGET_BASIS_ESTIMATE, scale=_MILLIONS))
        return MeasureSet((*head, *tail))
    return measures


def _cash_expense(era: str) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        head = (*_cash_months(s), _cash_year(s, "total"),
                _cash_year(s, "vouchers_payable", Quantity.VOUCHERS_PAYABLE),
                _cash_year(s, "encumbrances", Quantity.ENCUMBRANCES))
        if era == "with_mergers":
            tail: tuple[MeasureSpec, ...] = (
                _cash_year(s, "mergers", Quantity.MERGERS),
                spec("budget", _BUDGET_BASIS_BUDGET, scale=_MILLIONS))
        else:
            tail = (spec("estimate", _BUDGET_BASIS_ESTIMATE, scale=_MILLIONS),)
        return MeasureSet((*head, *tail))
    return measures


_OPENING = (("grid", "lifecycle"), ("line", "opening_balance"))
_CLOSING = (("grid", "lifecycle"), ("line", "closing_balance"))


def _level_at_end_of(s: Scope, fiscal_m: int, year: int) -> MeasureSpec:
    """A cash level at the end of fiscal month m, `year` years back from the edition."""
    fy = fiscal_year_of(s.period.end) + year
    kind = _by_cutoff(s, fiscal_month(fy, fiscal_m).end)
    return spec("", Stated(kind, Window.MONTH, year=year, month=fiscal_m), scale=_MILLIONS, basis=Basis.POINT)


def qcmr_cash_lifecycle(s: Scope) -> MeasureSet:
    """Excess and TRANS are flows. Opening and CLOSING BALANCE are levels in every column.

    Opening Balance for fiscal month m is the level at the end of month m - 1, so July's opening
    balance is last June's close. The thirteenth column is the year's opening or closing level."""
    rows: list[RowMeasure] = []
    for m in range(1, 13):
        col = f"m{m:02d}"
        prev = _level_at_end_of(s, 12, -1) if m == 1 else _level_at_end_of(s, m - 1, 0)
        rows.append(RowMeasure(_OPENING, col, replace(prev, column=col)))
        rows.append(RowMeasure(_CLOSING, col, replace(_level_at_end_of(s, m, 0), column=col)))
    rows.append(RowMeasure(_OPENING, "total", replace(_level_at_end_of(s, 12, -1), column="total")))
    rows.append(RowMeasure(_CLOSING, "total", replace(_level_at_end_of(s, 12, 0), column="total")))
    return MeasureSet((*_cash_months(s), _cash_year(s, "total")), rows=tuple(rows))


def qcmr_cash_balances(s: Scope) -> MeasureSet:
    return MeasureSet(_cash_months(s, basis=Basis.POINT))


_MONTH_CAPS = tuple((f"m{i + 1:02d}", n) for i, n in enumerate(_MONTH_NAMES))
Q1_FY25_CASH = scope(date(2024, 7, 1), date(2024, 9, 30))
Q4_FY24_CASH = scope(date(2024, 4, 1), date(2024, 6, 30))
Q1_FY09_CASH = scope(date(2008, 7, 1), date(2008, 9, 30), actual_through=date(2008, 10, 31))  # one more month


# ----------------------------------------------------------------------------- monthly collections
def _collections(school: bool, close: bool) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        base = "revised_budget" if "revised_budget" in s.printed else "budget"
        head = (
            spec("prior_year_final", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1)),
            spec("prior_year_budget", Stated(Kind.BUDGET, Window.FISCAL_YEAR, year=-1,
                                             version=Version.ADOPTED)),
            spec("budget", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED)),
            spec("current_estimate", Stated(Kind.PROJECTION, Window.FISCAL_YEAR)),
            spec("revised_budget", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.REVISED)),
            spec("month", Stated(Kind.ACTUAL, Window.MONTH)),
            spec("month_prior", Stated(Kind.ACTUAL, Window.MONTH, year=-1)),
        )
        if school:
            head = (*head, spec("month_increase", Derived(How.DIFFERENCE, of=("month", "month_prior"))))
        fytd: tuple[MeasureSpec, ...] = (
            spec("fytd", Stated(Kind.ACTUAL, Window.FISCAL_YTD)),
            spec("fytd_prior", Stated(Kind.ACTUAL, Window.FISCAL_YTD, year=-1)),
        )
        if close:
            fytd = (
                spec("fytd_pre_accrual", Stated(Kind.ACTUAL, Window.FISCAL_YTD, quantity=Quantity.CASH)),
                spec("net_accrual", Stated(Kind.ACTUAL, Window.FISCAL_YTD, quantity=Quantity.ACCRUALS)),
                fytd[0],
                spec("fytd_prior_pre_accrual", Stated(Kind.ACTUAL, Window.FISCAL_YTD, year=-1,
                                                      quantity=Quantity.CASH)),
                spec("net_accrual_prior", Stated(Kind.ACTUAL, Window.FISCAL_YTD, year=-1,
                                                 quantity=Quantity.ACCRUALS)),
                fytd[1],
            )
        tail = (
            spec("increase", Derived(How.DIFFERENCE, of=("fytd", "fytd_prior"))),
            spec("remaining", Derived(How.DIFFERENCE, of=(base, "fytd"))),
            pct("pct", Derived(How.RATIO, of=("fytd", base))),
        )
        return MeasureSet((*head, *fytd, *tail))
    return measures


_COLL_HEAD = (("prior_year_final", "Prior Year Final"), ("prior_year_budget", "Prior Year Budget"),
              ("budget", "Budget Estimate"), ("current_estimate", "Current Estimates (March)"),
              ("revised_budget", "Revised Budget Estimate"), ("month", "Month of (this year)"),
              ("month_prior", "Month of (last year)"))
_COLL_TAIL = (("increase", "FYTD Increase (Decrease)"), ("remaining", "Necessary to Meet Budget Estimates"),
              ("pct", "Pct. of Budget Collected"))
_COLL_FYTD = (("fytd", "July to month (this year)"), ("fytd_prior", "July to month (last year)"))
_COLL_CLOSE = (("fytd_pre_accrual", "FYTD Before Accruals (this year)"), ("net_accrual", "Net Accruals (this year)"),
               ("fytd", "July to June (this year)"),
               ("fytd_prior_pre_accrual", "FYTD Before Accruals (last year)"),
               ("net_accrual_prior", "Net Accruals (last year)"), ("fytd_prior", "July to June (last year)"))
_SCHOOL_EXTRA = (("month_increase", "Month Increase (Decrease)"),)
JUL_2024 = scope(date(2024, 7, 1), date(2024, 7, 31))
MAR_2022 = scope(date(2022, 3, 1), date(2022, 3, 31), printed=frozenset({"revised_budget"}))
JUN_2024 = scope(date(2024, 6, 1), date(2024, 6, 30))
JUN_2022 = scope(date(2022, 6, 1), date(2022, 6, 30), printed=frozenset({"revised_budget"}))


# ----------------------------------------------------------------------------- wage tax
def wage_industry(s: Scope) -> MeasureSet:
    w = Window(s.part("window"))
    return MeasureSet((
        spec("current", Stated(Kind.ACTUAL, w)),
        spec("prior1", Stated(Kind.ACTUAL, w, year=-1)),
        spec("prior2", Stated(Kind.ACTUAL, w, year=-2)),
        spec("prior3", Stated(Kind.ACTUAL, w, year=-3)),
        pct("pct_current", Derived(How.PERCENT_CHANGE, of=("current", "prior1"))),
        pct("pct_prior1", Derived(How.PERCENT_CHANGE, of=("prior1", "prior2"))),
        pct("pct_prior2", Derived(How.PERCENT_CHANGE, of=("prior2", "prior3"))),
        pct("annualized", Derived(How.ANNUAL_GROWTH, of=("current", "prior3"))),
        spec("change", Derived(How.DIFFERENCE, of=("current", "prior1"))),
    ))


_WAGE_CAPS = (("current", "Current period $"), ("prior1", "Prior year $"), ("prior2", "Prior 2 $"),
              ("prior3", "Prior 3 $"), ("pct_current", "Current vs prior %"),
              ("pct_prior1", "Prior vs prior 2 %"), ("pct_prior2", "Prior 2 vs prior 3 %"),
              ("annualized", "3-year annualized %"), ("change", "Current minus prior $"))
_WAGE_SCOPES = tuple(scope(date(2024, 7, 1), date(2024, 9, 30), instance=(("window", w.value),))
                     for w in (Window.MONTH, Window.QUARTER, Window.CALENDAR_YTD, Window.FISCAL_YTD))


def _res(value: str) -> tuple[tuple[Dim, str], ...]:
    return ((Dim.RESIDENCY, value),)


def _residency_summary(years: int) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        out: list[MeasureSpec] = []
        for k in range(years):
            y = f"y{k}"
            out += [
                pct(f"nonresident_share_{y}", Derived(How.SHARE, of=(f"combined_{y}",), dims=_res("nonresident"))),
                pct(f"resident_share_{y}", Derived(How.SHARE, of=(f"combined_{y}",), dims=_res("resident"))),
                spec(f"combined_{y}", Stated(Kind.ACTUAL, Window.CALENDAR_YEAR, year=-k, dims=_res(ALL))),
            ]
        for k in range(years - 1):
            a, b = f"y{k}", f"y{k + 1}"
            out += [
                pct(f"nonresident_share_change_{a}", Derived(How.DIFFERENCE, of=(f"nonresident_share_{a}", f"nonresident_share_{b}"))),
                pct(f"resident_share_change_{a}", Derived(How.DIFFERENCE, of=(f"resident_share_{a}", f"resident_share_{b}"))),
                spec(f"combined_change_{a}", Derived(How.DIFFERENCE, of=(f"combined_{a}", f"combined_{b}"))),
                pct(f"combined_pct_{a}", Derived(How.PERCENT_CHANGE, of=(f"combined_{a}", f"combined_{b}"))),
            ]
        return MeasureSet(tuple(out))
    return measures


def _residency_detail(years: int, changes: bool) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        out: list[MeasureSpec] = []
        for k in range(years):
            y = f"y{k}"
            cy = dict(window=Window.CALENDAR_YEAR, year=-k)
            out += [
                spec(f"accounts_{y}", Stated(Kind.ACTUAL, quantity=Quantity.ACCOUNTS, **cy), unit="accounts"),
                spec(f"nonresident_{y}", Stated(Kind.ACTUAL, dims=_res("nonresident"), **cy)),
                pct(f"nonresident_pct_{y}", Derived(How.RATIO, of=(f"nonresident_{y}", f"combined_{y}"))),
                spec(f"resident_{y}", Stated(Kind.ACTUAL, dims=_res("resident"), **cy)),
                pct(f"resident_pct_{y}", Derived(How.RATIO, of=(f"resident_{y}", f"combined_{y}"))),
                spec(f"combined_{y}", Stated(Kind.ACTUAL, dims=_res(ALL), **cy)),
            ]
        if changes:
            out += [
                spec("accounts_change", Derived(How.DIFFERENCE, of=("accounts_y0", "accounts_y1")), unit="accounts"),
                spec("nonresident_change", Derived(How.DIFFERENCE, of=("nonresident_y0", "nonresident_y1"))),
                spec("resident_change", Derived(How.DIFFERENCE, of=("resident_y0", "resident_y1"))),
                spec("combined_change", Derived(How.DIFFERENCE, of=("combined_y0", "combined_y1"))),
            ]
        return MeasureSet(tuple(out))
    return measures


def _res_summary_caps(years: int) -> tuple[tuple[str, str], ...]:
    caps: list[tuple[str, str]] = []
    for k in range(years):
        caps += [(f"nonresident_share_y{k}", f"Nonresident share % (year {-k})"),
                 (f"resident_share_y{k}", f"Resident share % (year {-k})"),
                 (f"combined_y{k}", f"Combined $ (year {-k})")]
    for k in range(years - 1):
        caps += [(f"nonresident_share_change_y{k}", f"Change in nonresident share ({-k} vs {-k - 1})"),
                 (f"resident_share_change_y{k}", f"Change in resident share ({-k} vs {-k - 1})"),
                 (f"combined_change_y{k}", f"Change in combined $ ({-k} vs {-k - 1})"),
                 (f"combined_pct_y{k}", f"Change in combined % ({-k} vs {-k - 1})")]
    return tuple(caps)


def _res_detail_caps(years: int, changes: bool) -> tuple[tuple[str, str], ...]:
    caps: list[tuple[str, str]] = []
    for k in range(years):
        caps += [(f"accounts_y{k}", f"Distinct accounts (year {-k})"),
                 (f"nonresident_y{k}", f"Nonresident $ (year {-k})"),
                 (f"nonresident_pct_y{k}", f"Nonresident % (year {-k})"),
                 (f"resident_y{k}", f"Resident $ (year {-k})"),
                 (f"resident_pct_y{k}", f"Resident % (year {-k})"),
                 (f"combined_y{k}", f"Combined $ (year {-k})")]
    if changes:
        caps += [("accounts_change", "Change: accounts"), ("nonresident_change", "Change: nonresident $"),
                 ("resident_change", "Change: resident $"), ("combined_change", "Change: combined $")]
    return tuple(caps)


CY2020 = scope(date(2020, 1, 1), date(2020, 12, 31))
CY2022 = scope(date(2022, 1, 1), date(2022, 12, 31))


# ----------------------------------------------------------------------------- BIRT and sales
def birt(s: Scope) -> MeasureSet:
    lead = int(s.part("tax_year")) - s.period.end.year           # the page's leading tax year

    def half(suffix: str, year: int) -> tuple[MeasureSpec, ...]:
        ty = dict(window=Window.TAX_YEAR, year=year)
        base = lambda v: ((Dim.TAX_BASE, v),)                    # noqa: E731
        return (
            spec(f"accounts{suffix}", Stated(Kind.ACTUAL, quantity=Quantity.ACCOUNTS, **ty), unit="accounts"),
            spec(f"net_income{suffix}", Stated(Kind.ACTUAL, dims=base("net_income"), **ty)),
            spec(f"gross_receipts{suffix}", Stated(Kind.ACTUAL, dims=base("gross_receipts"), **ty)),
            spec(f"total{suffix}", Stated(Kind.ACTUAL, dims=base(ALL), **ty)),
        )
    return MeasureSet((*half("", lead), *half("_prior", lead - 1)))


_BIRT_CAPS = (("accounts", "Accounts (leading tax year)"), ("net_income", "Net income"),
              ("gross_receipts", "Gross receipts"), ("total", "Total"),
              ("accounts_prior", "Accounts (prior tax year)"), ("net_income_prior", "Net income"),
              ("gross_receipts_prior", "Gross receipts"), ("total_prior", "Total"))
BIRT_2022 = scope(date(2018, 1, 1), date(2022, 12, 31), instance=(("tax_year", "2022"),))
BIRT_2020 = scope(date(2018, 1, 1), date(2022, 12, 31), instance=(("tax_year", "2020"),))


def _sales(era: str) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        fy = dict(window=Window.FISCAL_YEAR)
        head = (
            spec("entities", Stated(Kind.ACTUAL, quantity=Quantity.ACCOUNTS, **fy), unit="accounts"),
            spec("local_tax", Stated(Kind.ACTUAL, **fy)),
            pct("share", Derived(How.SHARE, of=("local_tax",))),
        )
        if era == "three":
            return MeasureSet(head)
        return MeasureSet((
            *head,
            *(spec(f"local_tax_prior{k}", Stated(Kind.ACTUAL, year=-k, **fy))
              for k in (1, 2, 3)),
            pct("pct_current", Derived(How.PERCENT_CHANGE, of=("local_tax", "local_tax_prior1"))),
            pct("pct_prior1", Derived(How.PERCENT_CHANGE, of=("local_tax_prior1", "local_tax_prior2"))),
            pct("pct_prior2", Derived(How.PERCENT_CHANGE, of=("local_tax_prior2", "local_tax_prior3"))),
            pct("annualized", Derived(How.ANNUAL_GROWTH, of=("local_tax", "local_tax_prior3"))),
            spec("change", Derived(How.DIFFERENCE, of=("local_tax", "local_tax_prior1"))),
        ))
    return measures


_SALES3_CAPS = (("entities", "Entity count"), ("local_tax", "Local tax"), ("share", "Percent of total"))
_SALES11_CAPS = (*_SALES3_CAPS, ("local_tax_prior1", "Local tax FY-1"), ("local_tax_prior2", "Local tax FY-2"),
                 ("local_tax_prior3", "Local tax FY-3"), ("pct_current", "% current vs prior"),
                 ("pct_prior1", "% prior vs prior 2"), ("pct_prior2", "% prior 2 vs prior 3"),
                 ("annualized", "3-year annualized %"), ("change", "Current minus prior $"))
FY2018 = scope(date(2017, 7, 1), date(2018, 6, 30))


# ----------------------------------------------------------------------------- realty transfer tax
def _pair(name: str, meaning: Stated) -> tuple[MeasureSpec, MeasureSpec]:
    return (spec(f"records{name}", replace(meaning, quantity=Quantity.TRANSACTIONS), unit="transactions"),
            spec(f"tax{name}", meaning))


def _derived_pair(name: str, how: How, a: str, b: str) -> tuple[MeasureSpec, MeasureSpec]:
    make = pct if how is How.PERCENT_CHANGE else spec
    records = make(f"records{name}", Derived(how, of=(f"records{a}", f"records{b}")))
    if how is How.DIFFERENCE:
        records = replace(records, unit="transactions")
    return (records, make(f"tax{name}", Derived(how, of=(f"tax{a}", f"tax{b}"))))


def _rtt_comparison(window: Window) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        return MeasureSet((
            *_pair("", Stated(Kind.ACTUAL, window)),
            *_pair("_prior", Stated(Kind.ACTUAL, window, year=-1)),
            *_derived_pair("_change", How.DIFFERENCE, "", "_prior"),
            *_derived_pair("_pct", How.PERCENT_CHANGE, "", "_prior"),
        ))
    return measures


def rtt_monthly_grid(s: Scope) -> MeasureSet:
    last = (s.period.end.month - 7) % 12 + 1                     # fiscal month of the quarter's last month
    months = tuple(
        m for i, fm in enumerate((last - 2, last - 1, last), start=1)
        for m in _pair(f"_m{i}", Stated(Kind.ACTUAL, Window.MONTH, month=fm)))
    return MeasureSet((*months, *_pair("_quarter", Stated(Kind.ACTUAL, Window.QUARTER))))


def rtt_monthly_comparison(s: Scope) -> MeasureSet:
    return MeasureSet((
        *_pair("", Stated(Kind.ACTUAL, Window.MONTH)),
        *_pair("_prior1", Stated(Kind.ACTUAL, Window.MONTH, year=-1)),
        *_pair("_prior2", Stated(Kind.ACTUAL, Window.MONTH, year=-2)),
        *_derived_pair("_change1", How.DIFFERENCE, "", "_prior1"),
        *_derived_pair("_change2", How.DIFFERENCE, "", "_prior2"),
        *_derived_pair("_pct1", How.PERCENT_CHANGE, "", "_prior1"),
        *_derived_pair("_pct2", How.PERCENT_CHANGE, "", "_prior2"),
    ))


def _pair_caps(name: str, text: str) -> tuple[tuple[str, str], ...]:
    return ((f"records{name}", f"Records: {text}"), (f"tax{name}", f"Local tax: {text}"))


_RTT_COMP_CAPS = (*_pair_caps("", "current"), *_pair_caps("_prior", "prior year"),
                  *_pair_caps("_change", "change"), *_pair_caps("_pct", "percent change"))
_RTT_GRID_CAPS = (*_pair_caps("_m1", "month 1"), *_pair_caps("_m2", "month 2"),
                  *_pair_caps("_m3", "month 3"), *_pair_caps("_quarter", "quarter"))
_RTT_MC_CAPS = (*_pair_caps("", "month"), *_pair_caps("_prior1", "same month, 1 year earlier"),
                *_pair_caps("_prior2", "same month, 2 years earlier"),
                *_pair_caps("_change1", "change vs 1 year"), *_pair_caps("_change2", "change vs 2 years"),
                *_pair_caps("_pct1", "percent vs 1 year"), *_pair_caps("_pct2", "percent vs 2 years"))
Q_MAR_2023 = scope(date(2023, 1, 1), date(2023, 3, 31))
M_MAR_2020 = scope(date(2020, 3, 1), date(2020, 3, 31))
Q_JUN_2023 = scope(date(2023, 4, 1), date(2023, 6, 30))
Q_DEC_2023 = scope(date(2023, 10, 1), date(2023, 12, 31))


# ----------------------------------------------------------------------------- Budget in Brief
def _bib_budget(s: Scope) -> Stated:
    version = Version.PROPOSED if s.stage == "proposed" else Version.ADOPTED
    return Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=version)


def _bib_history(era: str) -> Callable[[Scope], MeasureSet]:
    def measures(s: Scope) -> MeasureSet:
        prior_actual = spec("prior_actual", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-2))
        prior_adopted = spec("prior_adopted", Stated(Kind.BUDGET, Window.FISCAL_YEAR, year=-1,
                                                     version=Version.ADOPTED))
        estimate = spec("estimate", Stated(Kind.PROJECTION, Window.FISCAL_YEAR, year=-1))
        budget = spec("budget", _bib_budget(s))
        budget_increase = spec("budget_increase", Derived(How.DIFFERENCE, of=("budget", "estimate")))
        if era == "five":
            return MeasureSet((
                prior_actual,
                spec("estimate_increase", Derived(How.DIFFERENCE, of=("estimate", "prior_actual"))),
                estimate, budget_increase, budget))
        estimate_increase = spec("estimate_increase",
                                 Derived(How.DIFFERENCE, of=("estimate", "prior_adopted")))
        if era == "six":
            return MeasureSet((prior_actual, prior_adopted, estimate_increase, estimate,
                               budget_increase, budget))
        return MeasureSet((
            prior_actual,
            spec("prior_increase", Derived(How.DIFFERENCE, of=("prior_adopted", "prior_actual"))),
            prior_adopted, estimate_increase, estimate, budget_increase, budget))
    return measures


_K = Decimal(1000)


def bib_statement(s: Scope) -> MeasureSet:
    return MeasureSet((
        spec("actual", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-2), scale=_K),
        spec("original_budget", Stated(Kind.BUDGET, Window.FISCAL_YEAR, year=-1, version=Version.ADOPTED),
             scale=_K),
        spec("current_estimate", Stated(Kind.PROJECTION, Window.FISCAL_YEAR, year=-1), scale=_K),
        spec("budget", _bib_budget(s), scale=_K),
        spec("increase", Derived(How.DIFFERENCE, of=("budget", "current_estimate")), scale=_K),
        pct("percent", Derived(How.PERCENT_CHANGE, of=("budget", "current_estimate"))),
    ))


_BIB5_CAPS = (("prior_actual", "Actual (FY-2)"), ("estimate_increase", "Increase (Decrease), estimate"),
              ("estimate", "Estimated Obligations (FY-1)"),
              ("budget_increase", "Increase (Decrease), budget"), ("budget", "Budget (FY)"))
_BIB6_CAPS = (_BIB5_CAPS[0], ("prior_adopted", "Adopted Budget (FY-1)"), *_BIB5_CAPS[1:])
_BIB7_CAPS = (_BIB5_CAPS[0], ("prior_increase", "Increase (Decrease), prior"), *_BIB6_CAPS[1:])
_BIB_STMT_CAPS = (("actual", "Actual (FY-2)"), ("original_budget", "Original Budget (FY-1)"),
                  ("current_estimate", "Current Estimate (FY-1)"), ("budget", "Budget (FY)"),
                  ("increase", "Increase (Decrease) Amount"), ("percent", "Percent"))
BIB_ADOPTED = scope(date(2025, 7, 1), date(2026, 6, 30), stage="adopted")
BIB_PROPOSED = scope(date(2025, 7, 1), date(2026, 6, 30), stage="proposed")


# ----------------------------------------------------------------------------- supplemental reports
def supp_activity(s: Scope) -> MeasureSet:
    fy = dict(window=Window.FISCAL_YEAR)
    unknown = NotPublished("no meaning established for this column; read one page first")
    return MeasureSet((
        spec("original", Stated(Kind.BUDGET, version=Version.ADOPTED, **fy)),
        spec("final", Stated(Kind.BUDGET, version=Version.REVISED, **fy)),
        spec("encumbrances", Stated(Kind.ACTUAL, quantity=Quantity.ENCUMBRANCES, **fy)),
        spec("famis", unknown),
        spec("adjustments", NotPublished("no meaning established for 'Fd BAL/AP Adjs'; read one page first")),
        spec("expenditures", Stated(Kind.ACTUAL, quantity=Quantity.EXPENDITURES, **fy)),
        spec("obligations", Stated(Kind.ACTUAL, **fy)),
        spec("unencumbered", Derived(How.DIFFERENCE, of=("final", "obligations"))),
        pct("percent", Derived(How.RATIO, of=("obligations", "final"))),
    ))


def supp_revenues(s: Scope) -> MeasureSet:
    fy = dict(window=Window.FISCAL_YEAR)
    return MeasureSet((
        spec("original", Stated(Kind.BUDGET, version=Version.ADOPTED, **fy)),
        spec("final", Stated(Kind.BUDGET, version=Version.REVISED, **fy)),
        spec("actual", Stated(Kind.ACTUAL, **fy)),
        pct("percent", Derived(How.RATIO, of=("actual", "final"))),
        spec("prior_actual", Stated(Kind.ACTUAL, year=-1, **fy)),
        spec("increase", Derived(How.DIFFERENCE, of=("actual", "prior_actual"))),
    ))


def supp_capital_activity(s: Scope) -> MeasureSet:
    fy = dict(window=Window.FISCAL_YEAR)
    return MeasureSet((
        spec("original", Stated(Kind.BUDGET, version=Version.ADOPTED, **fy)),
        spec("net_adjustments", Derived(How.DIFFERENCE, of=("final", "original"))),
        spec("final", Stated(Kind.BUDGET, version=Version.REVISED, **fy)),
        spec("not_financed", Stated(Kind.ACTUAL, quantity=Quantity.NOT_FINANCED, **fy)),
        spec("net_available", Derived(How.DIFFERENCE, of=("final", "not_financed"))),
        spec("encumbrances", Stated(Kind.ACTUAL, quantity=Quantity.ENCUMBRANCES, **fy)),
        spec("expenditures", Stated(Kind.ACTUAL, quantity=Quantity.EXPENDITURES, **fy)),
        spec("obligations", Stated(Kind.ACTUAL, quantity=Quantity.OBLIGATIONS, **fy)),
        spec("ending_net_available", Derived(How.DIFFERENCE, of=("net_available", "obligations"))),
    ))


def supp_capital_prior(s: Scope) -> MeasureSet:
    fy = dict(window=Window.FISCAL_YEAR)
    enc = Quantity.ENCUMBERED_AUTHORIZATIONS
    return MeasureSet((
        spec("beginning_encumbered", Stated(Kind.ACTUAL, year=-1, quantity=enc, **fy), basis=Basis.POINT),
        spec("expenditures", Stated(Kind.ACTUAL, quantity=Quantity.EXPENDITURES, **fy)),
        spec("merged", Stated(Kind.ACTUAL, quantity=Quantity.AUTHORIZATIONS_MERGED, **fy)),
        spec("ending_encumbered", Stated(Kind.ACTUAL, quantity=enc, **fy), basis=Basis.POINT),
    ))


def supp_capital_summary(s: Scope) -> MeasureSet:
    fy = dict(window=Window.FISCAL_YEAR)
    return MeasureSet((
        spec("adjusted_available", Stated(Kind.BUDGET, version=Version.REVISED, **fy)),
        spec("expenditures", Stated(Kind.ACTUAL, quantity=Quantity.EXPENDITURES, **fy)),
        spec("encumbrances", Stated(Kind.ACTUAL, quantity=Quantity.ENCUMBRANCES, **fy)),
        spec("obligations", Stated(Kind.ACTUAL, quantity=Quantity.OBLIGATIONS, **fy)),
        spec("merged", Stated(Kind.ACTUAL, quantity=Quantity.AUTHORIZATIONS_MERGED, **fy)),
    ))


_SUPP_ACT_CAPS = (("original", "Original Appropriations"), ("final", "Final Appropriations"),
                  ("encumbrances", "Encumbrances"), ("famis", "FAMIS"), ("adjustments", "Fd BAL/AP Adjs"),
                  ("expenditures", "Expenditures"), ("obligations", "Total Obligations"),
                  ("unencumbered", "Unencumbered Balance"),
                  ("percent", "Percent of Total Obligations to Appropriations"))
_SUPP_REV_CAPS = (("original", "Original Budget Estimate"), ("final", "Final Budget Estimate"),
                  ("actual", "Actual"), ("percent", "Percent Collected"),
                  ("prior_actual", "Prior Year Actual"), ("increase", "Increase (Decrease)"))
_CAP_ACT_CAPS = (("original", "Original Authorizations"), ("net_adjustments", "Net Adjustments"),
                 ("final", "Final Authorizations"), ("not_financed", "Amount Not Financed"),
                 ("net_available", "Net Available"), ("encumbrances", "Encumbrances"),
                 ("expenditures", "Expenditures"), ("obligations", "Total Obligations"),
                 ("ending_net_available", "Ending Net Available"))
_CAP_PRIOR_CAPS = (("beginning_encumbered", "Beginning Encumbered Authorizations"),
                   ("expenditures", "Expenditures"), ("merged", "Financed Authorizations Merged"),
                   ("ending_encumbered", "Ending Encumbered Authorizations"))
_CAP_SUM_CAPS = (("adjusted_available", "Adjusted Authorizations Available"),
                 ("expenditures", "Expenditures"), ("encumbrances", "Encumbrances"),
                 ("obligations", "Total Obligations"),
                 ("merged", "Financed Authorizations Merged During the Period"))
FY2024 = scope(date(2023, 7, 1), date(2024, 6, 30))


# ----------------------------------------------------------------------------- held out: QSMR
_SD_FUND = {"operating": "sdp_fund_operating", "categorical": "sdp_fund_categorical", "total": ALL}


def qsmr_of_2016(s: Scope) -> MeasureSet:
    return MeasureSet((
        spec("prior_actual", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1)),
        spec("adopted", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED)),
        spec("ytd_actual", Stated(Kind.ACTUAL, Window.FISCAL_YTD)),
        pct("pct_of_budget", Derived(How.RATIO, of=("ytd_actual", "adopted"))),
    ))


def qsmr_of_2023(s: Scope) -> MeasureSet:
    """FY2023 Q4 OF-1, as Codex read it from the District PDF: no adopted column, and the
    variance is projection minus amended (Local Tax: 1,531,107,781 - 1,502,781,017 = +28,326,764)."""
    return MeasureSet((
        spec("amended", Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.REVISED)),
        spec("projection", Stated(Kind.PROJECTION, Window.FISCAL_YEAR)),
        spec("over_under", Derived(How.DIFFERENCE, of=("projection", "amended"))),
        spec("actual_fy1", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1)),
        spec("actual_fy2", Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-2)),
    ))


def qsmr_cash_adopted(s: Scope) -> MeasureSet:
    return MeasureSet(tuple(
        spec(f"m{m:02d}", Stated(Kind.BUDGET, Window.MONTH, month=m, version=Version.ADOPTED), scale=_K)
        for m in range(1, 13)))


def qsmr_positions_2016(s: Scope) -> MeasureSet:
    groups = {
        "prior": Stated(Kind.ACTUAL, Window.FISCAL_YEAR, year=-1),
        "adopted": Stated(Kind.BUDGET, Window.FISCAL_YEAR, version=Version.ADOPTED),
        "actual": Stated(Kind.ACTUAL, Window.QUARTER),
    }
    cols = [spec(f"{g}_{f}", replace(groups[g], dims=((Dim.FUND, _SD_FUND[f]),)), unit="fte", basis=Basis.POINT)
            for f in _SD_FUND for g in groups]
    cols += [spec(f"variance_{f}", Derived(How.DIFFERENCE, of=(f"adopted_{f}", f"actual_{f}")), unit="fte",
                  basis=Basis.POINT) for f in _SD_FUND]
    return MeasureSet(tuple(cols))


def qsmr_vendor_payments(s: Scope) -> MeasureSet:
    return MeasureSet((spec("amount", Stated(Kind.ACTUAL, Window.FISCAL_YTD)),))


_QSMR_OF16_CAPS = (("prior_actual", "Prior year actual"), ("adopted", "Adopted budget"),
                   ("ytd_actual", "Year-to-date actual"), ("pct_of_budget", "Percent of budget"))
_QSMR_OF23_CAPS = (("amended", "Amended budget"), ("projection", "Current projection"),
                   ("over_under", "Over (under)"), ("actual_fy1", "Prior year actual (FY-1)"),
                   ("actual_fy2", "Prior year actual (FY-2)"))
_QSMR_P1_CAPS = tuple((f"{g}_{f}", f"{gc}: {fc}")
                      for f, fc in (("operating", "Operating"), ("categorical", "Categorical"), ("total", "Total"))
                      for g, gc in (("prior", "Prior year actual"), ("adopted", "Adopted budget"),
                                    ("actual", "Quarter-end actual"))
                      ) + tuple((f"variance_{f}", f"Variance: {fc}")
                                for f, fc in (("operating", "Operating"), ("categorical", "Categorical"),
                                              ("total", "Total")))
SD_Q2_FY16 = scope(date(2015, 10, 1), date(2015, 12, 31))


# ----------------------------------------------------------------------------- the list
_CASH_REV_TAIL = {
    "legacy": (("total", "Total"), ("accrued", "Accrued"), ("under_over", "Under (Over) Revenues"),
               ("budget", "Budget Revenues")),
    "middle": (("total", "Total"), ("accrued", "Accrued"), ("estimate", "Estimated Revenues")),
    "modern": (("total", "Total"), ("accrued", "Accrued"), ("not_accrued", "Not Accrued"),
               ("estimate", "Estimated Revenues")),
}
_CASH_EXP_TAIL = {
    "with_mergers": (("total", "Total"), ("vouchers_payable", "Vouchers Payable"),
                     ("encumbrances", "Encumbrances"), ("mergers", "Mergers"),
                     ("budget", "Budget Obligations")),
    "no_mergers": (("total", "Total"), ("vouchers_payable", "Vouchers Payable"),
                   ("encumbrances", "Encumbrances"), ("estimate", "Estimated Obligations")),
}
_CASH_SCOPES = (Q1_FY25_CASH, Q4_FY24_CASH, Q1_FY09_CASH)

DECLS: tuple[Decl, ...] = (
    Decl("qcmr_positions", "p1_ten_columns", _P1_CAPS, qcmr_positions, (Q2_FY24, Q4_FY24, Q1_FY25)),
    Decl("qcmr_obligations", "nine", _O2_CAPS, qcmr_obligations, (Q2_FY24, Q4_FY24, Q1_FY25)),
    Decl("qcmr_obligations", "year_end", _O2_YEAR_END_CAPS, qcmr_obligations_year_end, (Q4_FY26,),
         provisional=frozenset({"prior_actual"})),
    Decl("qcmr_personal_services", "in_year", _O3_IN_YEAR_CAPS, qcmr_ps_in_year, (Q2_FY24,)),
    Decl("qcmr_personal_services", "year_end", _O3_YEAR_END_CAPS, qcmr_ps_year_end, (Q4_FY24,)),
    *(Decl("qcmr_cash_revenue", era, (*_MONTH_CAPS, *tail), _cash_revenue(era), _CASH_SCOPES,
           provisional=frozenset(c for c, _ in tail) - {"total"})
      for era, tail in _CASH_REV_TAIL.items()),
    *(Decl("qcmr_cash_expense", era, (*_MONTH_CAPS, *tail), _cash_expense(era), _CASH_SCOPES,
           provisional=frozenset(c for c, _ in tail) - {"total"})
      for era, tail in _CASH_EXP_TAIL.items()),
    Decl("qcmr_cash_lifecycle", "rows", (*_MONTH_CAPS, ("total", "Thirteenth column")),
         qcmr_cash_lifecycle, _CASH_SCOPES),
    Decl("qcmr_cash_balances", "fund_balances", _MONTH_CAPS, qcmr_cash_balances, _CASH_SCOPES),
    Decl("collections_city", "ordinary", (*_COLL_HEAD, *_COLL_FYTD, *_COLL_TAIL),
         _collections(school=False, close=False), (JUL_2024, MAR_2022),
         provisional=frozenset({"prior_year_budget", "current_estimate"})),
    Decl("collections_city", "june_close", (*_COLL_HEAD, *_COLL_CLOSE, *_COLL_TAIL),
         _collections(school=False, close=True), (JUN_2024, JUN_2022),
         provisional=frozenset({"prior_year_budget", "current_estimate", "fytd_pre_accrual",
                                "fytd_prior_pre_accrual"})),
    Decl("collections_school", "ordinary", (*_COLL_HEAD, *_SCHOOL_EXTRA, *_COLL_FYTD, *_COLL_TAIL),
         _collections(school=True, close=False), (JUL_2024, MAR_2022),
         provisional=frozenset({"prior_year_budget", "current_estimate"})),
    Decl("collections_school", "june_close", (*_COLL_HEAD, *_SCHOOL_EXTRA, *_COLL_CLOSE, *_COLL_TAIL),
         _collections(school=True, close=True), (JUN_2024, JUN_2022),
         provisional=frozenset({"prior_year_budget", "current_estimate", "fytd_pre_accrual",
                                "fytd_prior_pre_accrual"})),
    Decl("wage_industry", "nine", _WAGE_CAPS, wage_industry, _WAGE_SCOPES),
    Decl("wage_residency_summary", "first", _res_summary_caps(2), _residency_summary(2), (CY2020,),
         provisional=frozenset(c for c, _ in _res_summary_caps(2) if "change" in c or "pct" in c)),
    Decl("wage_residency_summary", "rolling", _res_summary_caps(3), _residency_summary(3), (CY2022,),
         provisional=frozenset(c for c, _ in _res_summary_caps(3) if "change" in c or "pct" in c)),
    Decl("wage_residency_detail", "first", _res_detail_caps(2, True), _residency_detail(2, True), (CY2020,),
         provisional=frozenset({"accounts_change", "nonresident_change", "resident_change", "combined_change"})),
    Decl("wage_residency_detail", "rolling", _res_detail_caps(3, False), _residency_detail(3, False), (CY2022,)),
    Decl("birt", "two_halves", _BIRT_CAPS, birt, (BIRT_2022, BIRT_2020)),
    Decl("sales", "three", _SALES3_CAPS, _sales("three"), (FY2018,), provisional=frozenset({"entities"})),
    Decl("sales", "eleven", _SALES11_CAPS, _sales("eleven"), (FY2018,), provisional=frozenset({"entities"})),
    Decl("rtt", "monthly_grid", _RTT_GRID_CAPS, rtt_monthly_grid, (Q_MAR_2023, Q_DEC_2023)),
    Decl("rtt", "monthly_comparison", _RTT_MC_CAPS, rtt_monthly_comparison, (M_MAR_2020,),
         provisional=frozenset({"records_change2", "tax_change2", "records_pct2", "tax_pct2"})),
    Decl("rtt", "quarter", _RTT_COMP_CAPS, _rtt_comparison(Window.QUARTER), (Q_MAR_2023,)),
    Decl("rtt", "fytd", _RTT_COMP_CAPS, _rtt_comparison(Window.FISCAL_YTD), (Q_MAR_2023,)),
    Decl("rtt", "fiscal_year", _RTT_COMP_CAPS, _rtt_comparison(Window.FISCAL_YEAR), (Q_JUN_2023,)),
    Decl("rtt", "calendar_year", _RTT_COMP_CAPS, _rtt_comparison(Window.CALENDAR_YEAR), (Q_DEC_2023,)),
    Decl("bib_history", "five", _BIB5_CAPS, _bib_history("five"), (BIB_ADOPTED, BIB_PROPOSED)),
    Decl("bib_history", "six", _BIB6_CAPS, _bib_history("six"), (BIB_ADOPTED, BIB_PROPOSED)),
    Decl("bib_history", "seven", _BIB7_CAPS, _bib_history("seven"), (BIB_ADOPTED, BIB_PROPOSED)),
    Decl("bib_fund_summary", "ruled", _BIB_STMT_CAPS, bib_statement, (BIB_ADOPTED, BIB_PROPOSED),
         provisional=frozenset({"percent"})),
    Decl("bib_revenue_schedule", "ruled", _BIB_STMT_CAPS, bib_statement, (BIB_ADOPTED, BIB_PROPOSED),
         provisional=frozenset({"percent"})),
    Decl("supp_activity", "seven", _SUPP_ACT_CAPS, supp_activity, (FY2024,)),
    Decl("supp_revenues", "net_revenue", _SUPP_REV_CAPS, supp_revenues, (FY2024,)),
    Decl("supp_capital_activity", "nine", _CAP_ACT_CAPS, supp_capital_activity, (FY2024,),
         provisional=frozenset({"not_financed", "net_available", "ending_net_available"})),
    Decl("supp_capital_prior", "four", _CAP_PRIOR_CAPS, supp_capital_prior, (FY2024,),
         provisional=frozenset(c for c, _ in _CAP_PRIOR_CAPS)),
    Decl("supp_capital_summary", "five", _CAP_SUM_CAPS, supp_capital_summary, (FY2024,),
         provisional=frozenset({"adjusted_available", "merged"})),
    Decl("qsmr_operating", "of_2016", _QSMR_OF16_CAPS, qsmr_of_2016, (SD_Q2_FY16,), held_out=True),
    Decl("qsmr_operating", "of_2023", _QSMR_OF23_CAPS, qsmr_of_2023, (SD_Q2_FY16,), held_out=True),
    Decl("qsmr_cash_adopted", "cf1", _MONTH_CAPS, qsmr_cash_adopted, (SD_Q2_FY16,), held_out=True),
    Decl("qsmr_positions", "p1_2016", _QSMR_P1_CAPS, qsmr_positions_2016, (SD_Q2_FY16,), held_out=True),
    Decl("qsmr_vendor_payments", "cf3", (("amount", "Amount"),), qsmr_vendor_payments, (SD_Q2_FY16,),
         held_out=True),
)
