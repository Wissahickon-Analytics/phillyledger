"""The closed lists that say what a published column means (design section 2.2).

No table logic lives here. A table module describes each column with these words in its
`measures`, `DEFINITIONS` gives each member its one line for the release manifest, and
`test_closed_lists_are_pinned` pins every list, so a new word is a reviewed change (hard rule 6).
"""

from enum import StrEnum
from types import MappingProxyType


class Kind(StrEnum):
    """What sort of number a column holds. A BUDGET always has a `Version`."""

    ACTUAL = "actual"
    BUDGET = "budget"
    PROJECTION = "projection"


class Version(StrEnum):
    """Which budget a BUDGET column holds. Every other column is NONE."""

    NONE = "none"
    ADOPTED = "adopted"
    REVISED = "revised"
    PROPOSED = "proposed"
    TARGET = "target"


class Window(StrEnum):
    """The span of days a column covers, which also gives its year a fiscal or calendar basis.

    `periods.fiscal_period` holds the basis of each window. "As of a date" is no window: a level
    is read at the end of its window (`measures.Basis`).
    """

    MONTH = "month"
    QUARTER = "quarter"
    FISCAL_YTD = "fiscal_ytd"
    CALENDAR_YTD = "calendar_ytd"
    FISCAL_YEAR = "fiscal_year"
    CALENDAR_YEAR = "calendar_year"
    TAX_YEAR = "tax_year"


class How(StrEnum):
    """How the publisher computed a column from the operand columns it names, in their order."""

    DIFFERENCE = "difference"
    PERCENT_CHANGE = "percent_change"
    RATIO = "ratio"
    SHARE = "share"
    ANNUAL_GROWTH = "annual_growth"


class Dim(StrEnum):
    """A slice that a column carries, such as one fund of a table that prints each fund."""

    FUND = "fund"
    RESIDENCY = "residency"
    TAX_BASE = "tax_base"


class Quantity(StrEnum):
    """What a column counts when it is not what its table mainly counts."""

    OBLIGATIONS = "obligations"
    EXPENDITURES = "expenditures"
    ENCUMBRANCES = "encumbrances"
    NOT_FINANCED = "not_financed"
    ENCUMBERED_AUTHORIZATIONS = "encumbered_authorizations"
    AUTHORIZATIONS_MERGED = "authorizations_merged"
    CASH = "cash"
    BUDGET_BASIS = "budget_basis"
    ACCRUALS = "accruals"
    NOT_ACCRUED = "not_accrued"
    VOUCHERS_PAYABLE = "vouchers_payable"
    MERGERS = "mergers"
    TRANSACTIONS = "transactions"
    ACCOUNTS = "accounts"


ALL = "all"
DIM_VALUES: MappingProxyType[Dim, tuple[str, ...]] = MappingProxyType(
    {
        Dim.RESIDENCY: ("resident", "nonresident", ALL),
        Dim.TAX_BASE: ("net_income", "gross_receipts", ALL),
    }
)
DEFINITIONS: MappingProxyType[str, str] = MappingProxyType(
    {
        "kind.actual": "A recorded result.",
        "kind.budget": "An amount authorized or planned, with the version of the budget it is.",
        "kind.projection": "The publisher's forecast for a window that has not closed.",
        "version.none": "Not a budget amount.",
        "version.adopted": "The budget as first enacted, printed as Adopted or Original.",
        "version.revised": (
            "The budget as changed after adoption, at the edition's date, printed as Final or "
            "Revised."
        ),
        "version.proposed": "The Mayor's proposed budget, before City Council acts on it.",
        "version.target": (
            "The administration's target, printed as Target Budget or YTD Target Plan."
        ),
        "window.month": "One calendar month.",
        "window.quarter": (
            "One quarter of the fiscal year: July to September, October to December, January to "
            "March or April to June."
        ),
        "window.fiscal_ytd": "From July 1 to the end of the edition's period.",
        "window.calendar_ytd": "From January 1 to the end of the edition's period.",
        "window.fiscal_year": "The City's fiscal year, from July 1 to June 30.",
        "window.calendar_year": "A calendar year, from January 1 to December 31.",
        "window.tax_year": "The tax year that a return is filed for.",
        "how.difference": "The first operand minus each later operand.",
        "how.percent_change": "The first operand less the second, as a percent of the second.",
        "how.ratio": "The first operand as a percent of the second.",
        "how.share": "The part, as a percent of the whole that the one operand holds.",
        "how.annual_growth": (
            "The compound yearly rate of growth from the second operand to the first."
        ),
        "dim.fund": "The fund: a fund id of the registry, or all for every fund.",
        "dim.residency": "Whether the taxpayer is a resident: resident, nonresident or all.",
        "dim.tax_base": "The base of the tax: net_income, gross_receipts or all.",
        "quantity.obligations": "Expenditures plus encumbrances.",
        "quantity.expenditures": "Amounts spent.",
        "quantity.encumbrances": "Amounts committed and not yet spent.",
        "quantity.not_financed": "Capital authorizations with no financing yet.",
        "quantity.encumbered_authorizations": (
            "Encumbered capital authorizations, printed as Beginning or Ending Encumbered "
            "Authorizations."
        ),
        "quantity.authorizations_merged": (
            "Capital authorizations merged, printed as Financed Authorizations Merged."
        ),
        "quantity.cash": "Cash received, before accruals.",
        "quantity.budget_basis": "The amount as the budget counts it: cash plus accruals.",
        "quantity.accruals": "Amounts accrued to the year and not yet received as cash.",
        "quantity.not_accrued": "The amount printed as Not Accrued in the QCMR cash report.",
        "quantity.vouchers_payable": (
            "The amount printed as Vouchers Payable in the QCMR cash report."
        ),
        "quantity.mergers": (
            "The amount printed as Mergers in the QCMR cash report of FY2007 to FY2010."
        ),
        "quantity.transactions": "Recorded deed transfers, printed as Records.",
        "quantity.accounts": "Taxpayer accounts or filers.",
    }
)
