"""datadesk/core/vocab.py: the closed lists that describe a published column. No table logic."""

from __future__ import annotations

from enum import StrEnum


class Kind(StrEnum):
    ACTUAL = "actual"            # a recorded result
    BUDGET = "budget"            # an authorized or planned amount; always has a Version
    PROJECTION = "projection"    # the publisher's forecast for a window that has not closed


class Version(StrEnum):
    NONE = "none"                # every column that is not a budget
    ADOPTED = "adopted"          # as first enacted: "Adopted", "Original"
    REVISED = "revised"          # as changed after adoption, at the edition's date: "Final", "Revised"
    PROPOSED = "proposed"        # the Mayor's proposal, before Council acts
    TARGET = "target"            # the administration's spending target: "Target Budget", "YTD Target Plan"


class Window(StrEnum):
    MONTH = "month"
    QUARTER = "quarter"
    FISCAL_YTD = "fiscal_ytd"        # July 1 to the end of the edition's period
    CALENDAR_YTD = "calendar_ytd"    # January 1 to the end of the edition's period
    FISCAL_YEAR = "fiscal_year"      # July 1 to June 30
    CALENDAR_YEAR = "calendar_year"
    TAX_YEAR = "tax_year"            # BIRT: the tax year the return is filed for


class How(StrEnum):
    DIFFERENCE = "difference"            # of[0] minus each later operand
    PERCENT_CHANGE = "percent_change"    # 100 x (of[0] - of[1]) / of[1]
    RATIO = "ratio"                      # 100 x of[0] / of[1]
    SHARE = "share"                      # 100 x part / whole; of[0] is the column that holds the whole
    ANNUAL_GROWTH = "annual_growth"      # compound yearly rate from of[1] to of[0]


class Dim(StrEnum):
    FUND = "fund"                # a registry fund or fund group id, or ALL
    RESIDENCY = "residency"      # resident, nonresident, ALL
    TAX_BASE = "tax_base"        # net_income, gross_receipts, ALL


ALL = "all"
DIM_VALUES = {
    Dim.RESIDENCY: ("resident", "nonresident", ALL),
    Dim.TAX_BASE: ("net_income", "gross_receipts", ALL),
}                                # Dim.FUND values are checked against the registry instead


class Quantity(StrEnum):
    """Set on a column that counts something other than what its table mainly counts."""

    OBLIGATIONS = "obligations"                  # expenditures plus encumbrances (capital tables)
    EXPENDITURES = "expenditures"
    ENCUMBRANCES = "encumbrances"
    NOT_FINANCED = "not_financed"                # capital authorizations with no financing yet
    ENCUMBERED_AUTHORIZATIONS = "encumbered_authorizations"   # capital, prior years' statement
    AUTHORIZATIONS_MERGED = "authorizations_merged"           # capital, "Financed Authorizations Merged"
    CASH = "cash"                                # cash received, before accruals (collections June close)
    BUDGET_BASIS = "budget_basis"                # the amount as the budget counts it: cash plus accruals
    ACCRUALS = "accruals"                        # accrued to the year, not yet cash
    NOT_ACCRUED = "not_accrued"                  # QCMR cash, FY2017 on
    VOUCHERS_PAYABLE = "vouchers_payable"
    MERGERS = "mergers"                          # QCMR cash expense grid, FY2007 to FY2010
    TRANSACTIONS = "transactions"                # recorded deed transfers ("Records")
    ACCOUNTS = "accounts"                        # taxpayer accounts or filers


FUND_IDS = frozenset({           # stand-in for the registry's fund entities
    "phl_fund_general", "phl_fund_other", "sdp_fund_operating", "sdp_fund_categorical",
})
