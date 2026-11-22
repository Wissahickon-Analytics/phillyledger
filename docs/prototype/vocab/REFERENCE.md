### QCMR positions (P-1)

| Printed column | Name | Description |
|---|---|---|
| Year-End Actual: General | `prior_general` | actual; level at end of fiscal year, 1 yr back; fund phl_fund_general |
| Year-End Actual: Other | `prior_other` | actual; level at end of fiscal year, 1 yr back; fund phl_fund_other |
| Year-End Actual: Total | `prior_total` | actual; level at end of fiscal year, 1 yr back; fund all |
| Adopted Budget: General | `adopted_general` | budget, adopted; level at end of fiscal year; fund phl_fund_general |
| Adopted Budget: Other | `adopted_other` | budget, adopted; level at end of fiscal year; fund phl_fund_other |
| Adopted Budget: Total | `adopted_total` | budget, adopted; level at end of fiscal year; fund all |
| Month End Actual: General | `actual_general` | actual; level at end of quarter; fund phl_fund_general |
| Month End Actual: Other | `actual_other` | actual; level at end of quarter; fund phl_fund_other |
| Month End Actual: Total | `actual_total` | actual; level at end of quarter; fund all |
| (Over) Under Budget | `over_under` | `adopted_total` minus `actual_total` |

### QCMR obligations (O-2)

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Prior Year Actual | `prior_actual` | actual; fiscal year, 1 yr back (provisional) | all |
| YTD Target Plan | `ytd_target` | budget, target; fiscal to date | nine |
| YTD Actual | `ytd_actual` | actual; fiscal to date | nine |
| YTD (Over) Under Target | `ytd_variance` | `ytd_target` minus `ytd_actual` | nine |
| Adopted Budget | `adopted` | budget, adopted; fiscal year | all |
| Target Budget | `target` | budget, target; fiscal year | all |
| Current Projection | `projection` | projection; fiscal year | all |
| Projection (Over) Under Adopted | `projection_vs_adopted` | `adopted` minus `projection` | all |
| Projection (Over) Under Target | `projection_vs_target` | `target` minus `projection` | all |

### QCMR personal services (O-3)

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Year-End Actual (FY-3) | `actual_fy3` | actual; fiscal year, 3 yr back | all |
| Year-End Actual (FY-2) | `actual_fy2` | actual; fiscal year, 2 yr back | all |
| Unaudited Actual | `unaudited_actual` | actual; fiscal year, 1 yr back | in_year |
| YTD Target Plan | `ytd_target` | budget, target; fiscal to date | in_year |
| YTD Actual | `ytd_actual` | actual; fiscal to date | in_year |
| YTD (Over) Under Target | `ytd_variance` | `ytd_target` minus `ytd_actual` | in_year |
| Adopted Budget | `adopted` | budget, adopted; fiscal year | all |
| Target Budget | `target` | budget, target; fiscal year | all |
| Year-End Projection | `projection` | projection; fiscal year | all |
| Projection (Over) Under Adopted | `projection_vs_adopted` | `adopted` minus `projection` | all |
| Projection (Over) Under Target | `projection_vs_target` | `target` minus `projection` | all |
| Year-End Actual (FY-1) | `actual_fy1` | actual; fiscal year, 1 yr back | year_end |

On the Full-Time Positions rows every column is a count of positions at a point in time, not dollars. Row overrides say so.

### QCMR cash, revenue grid

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| July to September | `m01` to `m03` | actual; fiscal months 1 to 3 | all |
| October to June | `m04` to `m12` | actual or projection by cutoff; fiscal months 4 to 12 | all |
| Total | `total` | actual or projection by cutoff; fiscal year | all |
| Accrued | `accrued` | actual or projection by cutoff; fiscal year; accruals (provisional) | all |
| Under (Over) Revenues | `under_over` | `budget` minus `total` minus `accrued` (provisional) | legacy |
| Budget Revenues | `budget` | budget, adopted; fiscal year; budget basis (provisional) | legacy |
| Estimated Revenues | `estimate` | projection; fiscal year; budget basis (provisional) | middle, modern |
| Not Accrued | `not_accrued` | actual or projection by cutoff; fiscal year; not accrued (provisional) | modern |

### QCMR cash, expense grid

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| July to September | `m01` to `m03` | actual; fiscal months 1 to 3 | all |
| October to June | `m04` to `m12` | actual or projection by cutoff; fiscal months 4 to 12 | all |
| Total | `total` | actual or projection by cutoff; fiscal year | all |
| Vouchers Payable | `vouchers_payable` | actual or projection by cutoff; fiscal year; vouchers payable (provisional) | all |
| Encumbrances | `encumbrances` | actual or projection by cutoff; fiscal year; encumbrances (provisional) | all |
| Mergers | `mergers` | actual or projection by cutoff; fiscal year; mergers (provisional) | with_mergers |
| Budget Obligations | `budget` | budget, adopted; fiscal year; budget basis (provisional) | with_mergers |
| Estimated Obligations | `estimate` | projection; fiscal year; budget basis (provisional) | no_mergers |

### QCMR cash, balance rows

| Printed column | Name | Description |
|---|---|---|
| July to September | `m01` to `m03` | actual; fiscal months 1 to 3 |
| October to June | `m04` to `m12` | actual or projection by cutoff; fiscal months 4 to 12 |
| Thirteenth column | `total` | actual or projection by cutoff; fiscal year |

Opening Balance and CLOSING BALANCE are levels in every column. A month's opening balance is the level at the end of the month before, so July's is last June's close. The thirteenth column is the year's opening or closing level. Row overrides say so.

### QCMR cash, fund balances (page 2)

| Printed column | Name | Description |
|---|---|---|
| July to September | `m01` to `m03` | actual; level at end of fiscal months 1 to 3 |
| October to June | `m04` to `m12` | actual or projection by cutoff; level at end of fiscal months 4 to 12 |

### Monthly City collections

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Prior Year Final | `prior_year_final` | actual; fiscal year, 1 yr back | all |
| Prior Year Budget | `prior_year_budget` | budget, adopted; fiscal year, 1 yr back (provisional) | all |
| Budget Estimate | `budget` | budget, adopted; fiscal year | all |
| Current Estimates (March) | `current_estimate` | projection; fiscal year (provisional) | all |
| Revised Budget Estimate | `revised_budget` | budget, revised; fiscal year | all |
| Month of (this year) | `month` | actual; month | all |
| Month of (last year) | `month_prior` | actual; month, 1 yr back | all |
| July to month (this year) | `fytd` | actual; fiscal to date | all |
| July to month (last year) | `fytd_prior` | actual; fiscal to date, 1 yr back | all |
| FYTD Increase (Decrease) | `increase` | `fytd` minus `fytd_prior` | all |
| Necessary to Meet Budget Estimates | `remaining` | `budget` or `revised_budget` minus `fytd` | all |
| Pct. of Budget Collected | `pct` | `fytd` as % of `budget` or `revised_budget` | all |
| FYTD Before Accruals (this year) | `fytd_pre_accrual` | actual; fiscal to date; cash (provisional) | june_close |
| Net Accruals (this year) | `net_accrual` | actual; fiscal to date; accruals | june_close |
| FYTD Before Accruals (last year) | `fytd_prior_pre_accrual` | actual; fiscal to date, 1 yr back; cash (provisional) | june_close |
| Net Accruals (last year) | `net_accrual_prior` | actual; fiscal to date, 1 yr back; accruals | june_close |

### Monthly School collections

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Prior Year Final | `prior_year_final` | actual; fiscal year, 1 yr back | all |
| Prior Year Budget | `prior_year_budget` | budget, adopted; fiscal year, 1 yr back (provisional) | all |
| Budget Estimate | `budget` | budget, adopted; fiscal year | all |
| Current Estimates (March) | `current_estimate` | projection; fiscal year (provisional) | all |
| Revised Budget Estimate | `revised_budget` | budget, revised; fiscal year | all |
| Month of (this year) | `month` | actual; month | all |
| Month of (last year) | `month_prior` | actual; month, 1 yr back | all |
| Month Increase (Decrease) | `month_increase` | `month` minus `month_prior` | all |
| July to month (this year) | `fytd` | actual; fiscal to date | all |
| July to month (last year) | `fytd_prior` | actual; fiscal to date, 1 yr back | all |
| FYTD Increase (Decrease) | `increase` | `fytd` minus `fytd_prior` | all |
| Necessary to Meet Budget Estimates | `remaining` | `budget` or `revised_budget` minus `fytd` | all |
| Pct. of Budget Collected | `pct` | `fytd` as % of `budget` or `revised_budget` | all |
| FYTD Before Accruals (this year) | `fytd_pre_accrual` | actual; fiscal to date; cash (provisional) | june_close |
| Net Accruals (this year) | `net_accrual` | actual; fiscal to date; accruals | june_close |
| FYTD Before Accruals (last year) | `fytd_prior_pre_accrual` | actual; fiscal to date, 1 yr back; cash (provisional) | june_close |
| Net Accruals (last year) | `net_accrual_prior` | actual; fiscal to date, 1 yr back; accruals | june_close |

### Wage tax by industry

| Printed column | Name | Description |
|---|---|---|
| Current period $ | `current` | actual; the window the table title names |
| Prior year $ | `prior1` | actual; the window the table title names, 1 yr back |
| Prior 2 $ | `prior2` | actual; the window the table title names, 2 yr back |
| Prior 3 $ | `prior3` | actual; the window the table title names, 3 yr back |
| Current vs prior % | `pct_current` | % change, `current` over `prior1` |
| Prior vs prior 2 % | `pct_prior1` | % change, `prior1` over `prior2` |
| Prior 2 vs prior 3 % | `pct_prior2` | % change, `prior2` over `prior3` |
| 3-year annualized % | `annualized` | yearly growth, `prior3` to `current` |
| Current minus prior $ | `change` | `current` minus `prior1` |

### Wage tax by residency, summary

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Nonresident share % (year 0) | `nonresident_share_y0` | share of `combined_y0` (nonresident) | all |
| Resident share % (year 0) | `resident_share_y0` | share of `combined_y0` (resident) | all |
| Combined $ (year 0) | `combined_y0` | actual; calendar year; all | all |
| Nonresident share % (year -1) | `nonresident_share_y1` | share of `combined_y1` (nonresident) | all |
| Resident share % (year -1) | `resident_share_y1` | share of `combined_y1` (resident) | all |
| Combined $ (year -1) | `combined_y1` | actual; calendar year, 1 yr back; all | all |
| Change in nonresident share (0 vs -1) | `nonresident_share_change_y0` | `nonresident_share_y0` minus `nonresident_share_y1` (provisional) | all |
| Change in resident share (0 vs -1) | `resident_share_change_y0` | `resident_share_y0` minus `resident_share_y1` (provisional) | all |
| Change in combined $ (0 vs -1) | `combined_change_y0` | `combined_y0` minus `combined_y1` (provisional) | all |
| Change in combined % (0 vs -1) | `combined_pct_y0` | % change, `combined_y0` over `combined_y1` (provisional) | all |
| Nonresident share % (year -2) | `nonresident_share_y2` | share of `combined_y2` (nonresident) | rolling |
| Resident share % (year -2) | `resident_share_y2` | share of `combined_y2` (resident) | rolling |
| Combined $ (year -2) | `combined_y2` | actual; calendar year, 2 yr back; all | rolling |
| Change in nonresident share (-1 vs -2) | `nonresident_share_change_y1` | `nonresident_share_y1` minus `nonresident_share_y2` (provisional) | rolling |
| Change in resident share (-1 vs -2) | `resident_share_change_y1` | `resident_share_y1` minus `resident_share_y2` (provisional) | rolling |
| Change in combined $ (-1 vs -2) | `combined_change_y1` | `combined_y1` minus `combined_y2` (provisional) | rolling |
| Change in combined % (-1 vs -2) | `combined_pct_y1` | % change, `combined_y1` over `combined_y2` (provisional) | rolling |

### Wage tax by residency, detail

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Distinct accounts (year 0) | `accounts_y0` | actual; calendar year; accounts | all |
| Nonresident $ (year 0) | `nonresident_y0` | actual; calendar year; nonresident | all |
| Nonresident % (year 0) | `nonresident_pct_y0` | `nonresident_y0` as % of `combined_y0` | all |
| Resident $ (year 0) | `resident_y0` | actual; calendar year; resident | all |
| Resident % (year 0) | `resident_pct_y0` | `resident_y0` as % of `combined_y0` | all |
| Combined $ (year 0) | `combined_y0` | actual; calendar year; all | all |
| Distinct accounts (year -1) | `accounts_y1` | actual; calendar year, 1 yr back; accounts | all |
| Nonresident $ (year -1) | `nonresident_y1` | actual; calendar year, 1 yr back; nonresident | all |
| Nonresident % (year -1) | `nonresident_pct_y1` | `nonresident_y1` as % of `combined_y1` | all |
| Resident $ (year -1) | `resident_y1` | actual; calendar year, 1 yr back; resident | all |
| Resident % (year -1) | `resident_pct_y1` | `resident_y1` as % of `combined_y1` | all |
| Combined $ (year -1) | `combined_y1` | actual; calendar year, 1 yr back; all | all |
| Change: accounts | `accounts_change` | `accounts_y0` minus `accounts_y1` (provisional) | first |
| Change: nonresident $ | `nonresident_change` | `nonresident_y0` minus `nonresident_y1` (provisional) | first |
| Change: resident $ | `resident_change` | `resident_y0` minus `resident_y1` (provisional) | first |
| Change: combined $ | `combined_change` | `combined_y0` minus `combined_y1` (provisional) | first |
| Distinct accounts (year -2) | `accounts_y2` | actual; calendar year, 2 yr back; accounts | rolling |
| Nonresident $ (year -2) | `nonresident_y2` | actual; calendar year, 2 yr back; nonresident | rolling |
| Nonresident % (year -2) | `nonresident_pct_y2` | `nonresident_y2` as % of `combined_y2` | rolling |
| Resident $ (year -2) | `resident_y2` | actual; calendar year, 2 yr back; resident | rolling |
| Resident % (year -2) | `resident_pct_y2` | `resident_y2` as % of `combined_y2` | rolling |
| Combined $ (year -2) | `combined_y2` | actual; calendar year, 2 yr back; all | rolling |

### BIRT by sector

| Printed column | Name | Description |
|---|---|---|
| Accounts (leading tax year) | `accounts` | actual; tax year; accounts |
| Net income | `net_income` | actual; tax year; net income |
| Gross receipts | `gross_receipts` | actual; tax year; gross receipts |
| Total | `total` | actual; tax year; all |
| Accounts (prior tax year) | `accounts_prior` | actual; tax year, 1 yr back; accounts |
| Net income | `net_income_prior` | actual; tax year, 1 yr back; net income |
| Gross receipts | `gross_receipts_prior` | actual; tax year, 1 yr back; gross receipts |
| Total | `total_prior` | actual; tax year, 1 yr back; all |

### Sales tax by sector

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Entity count | `entities` | actual; fiscal year; accounts (provisional) | all |
| Local tax | `local_tax` | actual; fiscal year | all |
| Percent of total | `share` | share of `local_tax` | all |
| Local tax FY-1 | `local_tax_prior1` | actual; fiscal year, 1 yr back | eleven |
| Local tax FY-2 | `local_tax_prior2` | actual; fiscal year, 2 yr back | eleven |
| Local tax FY-3 | `local_tax_prior3` | actual; fiscal year, 3 yr back | eleven |
| % current vs prior | `pct_current` | % change, `local_tax` over `local_tax_prior1` | eleven |
| % prior vs prior 2 | `pct_prior1` | % change, `local_tax_prior1` over `local_tax_prior2` | eleven |
| % prior 2 vs prior 3 | `pct_prior2` | % change, `local_tax_prior2` over `local_tax_prior3` | eleven |
| 3-year annualized % | `annualized` | yearly growth, `local_tax_prior3` to `local_tax` | eleven |
| Current minus prior $ | `change` | `local_tax` minus `local_tax_prior1` | eleven |

### Realty transfer tax

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Records: month 1 | `records_m1` | actual; a month of the quarter; transactions | monthly_grid |
| Local tax: month 1 | `tax_m1` | actual; a month of the quarter | monthly_grid |
| Records: month 2 | `records_m2` | actual; a month of the quarter; transactions | monthly_grid |
| Local tax: month 2 | `tax_m2` | actual; a month of the quarter | monthly_grid |
| Records: month 3 | `records_m3` | actual; a month of the quarter; transactions | monthly_grid |
| Local tax: month 3 | `tax_m3` | actual; a month of the quarter | monthly_grid |
| Records: quarter | `records_quarter` | actual; quarter; transactions | monthly_grid |
| Local tax: quarter | `tax_quarter` | actual; quarter | monthly_grid |
| Records: month | `records` | actual; month; transactions | monthly_comparison |
| Local tax: month | `tax` | actual; month | monthly_comparison |
| Records: same month, 1 year earlier | `records_prior1` | actual; month, 1 yr back; transactions | monthly_comparison |
| Local tax: same month, 1 year earlier | `tax_prior1` | actual; month, 1 yr back | monthly_comparison |
| Records: same month, 2 years earlier | `records_prior2` | actual; month, 2 yr back; transactions | monthly_comparison |
| Local tax: same month, 2 years earlier | `tax_prior2` | actual; month, 2 yr back | monthly_comparison |
| Records: change vs 1 year | `records_change1` | `records` minus `records_prior1` | monthly_comparison |
| Local tax: change vs 1 year | `tax_change1` | `tax` minus `tax_prior1` | monthly_comparison |
| Records: change vs 2 years | `records_change2` | `records` minus `records_prior2` (provisional) | monthly_comparison |
| Local tax: change vs 2 years | `tax_change2` | `tax` minus `tax_prior2` (provisional) | monthly_comparison |
| Records: percent vs 1 year | `records_pct1` | % change, `records` over `records_prior1` | monthly_comparison |
| Local tax: percent vs 1 year | `tax_pct1` | % change, `tax` over `tax_prior1` | monthly_comparison |
| Records: percent vs 2 years | `records_pct2` | % change, `records` over `records_prior2` (provisional) | monthly_comparison |
| Local tax: percent vs 2 years | `tax_pct2` | % change, `tax` over `tax_prior2` (provisional) | monthly_comparison |
| Records: current | `records` | actual; quarter; transactions | quarter |
| Local tax: current | `tax` | actual; quarter | quarter |
| Records: prior year | `records_prior` | actual; quarter, 1 yr back; transactions | quarter |
| Local tax: prior year | `tax_prior` | actual; quarter, 1 yr back | quarter |
| Records: change | `records_change` | `records` minus `records_prior` | quarter, fytd, fiscal_year, calendar_year |
| Local tax: change | `tax_change` | `tax` minus `tax_prior` | quarter, fytd, fiscal_year, calendar_year |
| Records: percent change | `records_pct` | % change, `records` over `records_prior` | quarter, fytd, fiscal_year, calendar_year |
| Local tax: percent change | `tax_pct` | % change, `tax` over `tax_prior` | quarter, fytd, fiscal_year, calendar_year |
| Records: current | `records` | actual; fiscal to date; transactions | fytd |
| Local tax: current | `tax` | actual; fiscal to date | fytd |
| Records: prior year | `records_prior` | actual; fiscal to date, 1 yr back; transactions | fytd |
| Local tax: prior year | `tax_prior` | actual; fiscal to date, 1 yr back | fytd |
| Records: current | `records` | actual; fiscal year; transactions | fiscal_year |
| Local tax: current | `tax` | actual; fiscal year | fiscal_year |
| Records: prior year | `records_prior` | actual; fiscal year, 1 yr back; transactions | fiscal_year |
| Local tax: prior year | `tax_prior` | actual; fiscal year, 1 yr back | fiscal_year |
| Records: current | `records` | actual; calendar year; transactions | calendar_year |
| Local tax: current | `tax` | actual; calendar year | calendar_year |
| Records: prior year | `records_prior` | actual; calendar year, 1 yr back; transactions | calendar_year |
| Local tax: prior year | `tax_prior` | actual; calendar year, 1 yr back | calendar_year |

### Budget in Brief, General Fund obligation history

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Actual (FY-2) | `prior_actual` | actual; fiscal year, 2 yr back | all |
| Increase (Decrease), estimate | `estimate_increase` | `estimate` minus `prior_actual` | five |
| Estimated Obligations (FY-1) | `estimate` | projection; fiscal year, 1 yr back | all |
| Increase (Decrease), budget | `budget_increase` | `budget` minus `estimate` | all |
| Budget (FY) | `budget` | budget, adopted or proposed by book; fiscal year | all |
| Adopted Budget (FY-1) | `prior_adopted` | budget, adopted; fiscal year, 1 yr back | six, seven |
| Increase (Decrease), estimate | `estimate_increase` | `estimate` minus `prior_adopted` | six, seven |
| Increase (Decrease), prior | `prior_increase` | `prior_adopted` minus `prior_actual` | seven |

### Budget in Brief, fund summary

| Printed column | Name | Description |
|---|---|---|
| Actual (FY-2) | `actual` | actual; fiscal year, 2 yr back |
| Original Budget (FY-1) | `original_budget` | budget, adopted; fiscal year, 1 yr back |
| Current Estimate (FY-1) | `current_estimate` | projection; fiscal year, 1 yr back |
| Budget (FY) | `budget` | budget, adopted or proposed by book; fiscal year |
| Increase (Decrease) Amount | `increase` | `budget` minus `current_estimate` |
| Percent | `percent` | % change, `budget` over `current_estimate` (provisional) |

### Budget in Brief, revenue schedules

| Printed column | Name | Description |
|---|---|---|
| Actual (FY-2) | `actual` | actual; fiscal year, 2 yr back |
| Original Budget (FY-1) | `original_budget` | budget, adopted; fiscal year, 1 yr back |
| Current Estimate (FY-1) | `current_estimate` | projection; fiscal year, 1 yr back |
| Budget (FY) | `budget` | budget, adopted or proposed by book; fiscal year |
| Increase (Decrease) Amount | `increase` | `budget` minus `current_estimate` |
| Percent | `percent` | % change, `budget` over `current_estimate` (provisional) |

### Supplemental, appropriation activity

| Printed column | Name | Description |
|---|---|---|
| Original Appropriations | `original` | budget, adopted; fiscal year |
| Final Appropriations | `final` | budget, revised; fiscal year |
| Encumbrances | `encumbrances` | actual; fiscal year; encumbrances |
| FAMIS | `famis` | not published: no meaning established for this column; read one page first |
| Fd BAL/AP Adjs | `adjustments` | not published: no meaning established for 'Fd BAL/AP Adjs'; read one page first |
| Expenditures | `expenditures` | actual; fiscal year; expenditures |
| Total Obligations | `obligations` | actual; fiscal year |
| Unencumbered Balance | `unencumbered` | `final` minus `obligations` |
| Percent of Total Obligations to Appropriations | `percent` | `obligations` as % of `final` |

### Supplemental, net revenues

| Printed column | Name | Description |
|---|---|---|
| Original Budget Estimate | `original` | budget, adopted; fiscal year |
| Final Budget Estimate | `final` | budget, revised; fiscal year |
| Actual | `actual` | actual; fiscal year |
| Percent Collected | `percent` | `actual` as % of `final` |
| Prior Year Actual | `prior_actual` | actual; fiscal year, 1 yr back |
| Increase (Decrease) | `increase` | `actual` minus `prior_actual` |

### Supplemental, capital activity

| Printed column | Name | Description |
|---|---|---|
| Original Authorizations | `original` | budget, adopted; fiscal year |
| Net Adjustments | `net_adjustments` | `final` minus `original` |
| Final Authorizations | `final` | budget, revised; fiscal year |
| Amount Not Financed | `not_financed` | actual; fiscal year; not financed (provisional) |
| Net Available | `net_available` | `final` minus `not_financed` (provisional) |
| Encumbrances | `encumbrances` | actual; fiscal year; encumbrances |
| Expenditures | `expenditures` | actual; fiscal year; expenditures |
| Total Obligations | `obligations` | actual; fiscal year; obligations |
| Ending Net Available | `ending_net_available` | `net_available` minus `obligations` (provisional) |

### Supplemental, capital prior years

| Printed column | Name | Description |
|---|---|---|
| Beginning Encumbered Authorizations | `beginning_encumbered` | actual; level at end of fiscal year, 1 yr back; encumbered authorizations (provisional) |
| Expenditures | `expenditures` | actual; fiscal year; expenditures (provisional) |
| Financed Authorizations Merged | `merged` | actual; fiscal year; authorizations merged (provisional) |
| Ending Encumbered Authorizations | `ending_encumbered` | actual; level at end of fiscal year; encumbered authorizations (provisional) |

### Supplemental, capital summary

| Printed column | Name | Description |
|---|---|---|
| Adjusted Authorizations Available | `adjusted_available` | budget, revised; fiscal year (provisional) |
| Expenditures | `expenditures` | actual; fiscal year; expenditures |
| Encumbrances | `encumbrances` | actual; fiscal year; encumbrances |
| Total Obligations | `obligations` | actual; fiscal year; obligations |
| Financed Authorizations Merged During the Period | `merged` | actual; fiscal year; authorizations merged (provisional) |

## Held out: QSMR

### QSMR operating funds (held out)

| Printed column | Name | Description | Layouts |
|---|---|---|---|
| Prior year actual | `prior_actual` | actual; fiscal year, 1 yr back | of_2016 |
| Adopted budget | `adopted` | budget, adopted; fiscal year | of_2016 |
| Year-to-date actual | `ytd_actual` | actual; fiscal to date | of_2016 |
| Percent of budget | `pct_of_budget` | `ytd_actual` as % of `adopted` | of_2016 |
| Amended budget | `amended` | budget, revised; fiscal year | of_2023 |
| Current projection | `projection` | projection; fiscal year | of_2023 |
| Over (under) | `over_under` | `projection` minus `amended` | of_2023 |
| Prior year actual (FY-1) | `actual_fy1` | actual; fiscal year, 1 yr back | of_2023 |
| Prior year actual (FY-2) | `actual_fy2` | actual; fiscal year, 2 yr back | of_2023 |

### QSMR adopted cash flow (held out)

| Printed column | Name | Description |
|---|---|---|
| July to June | `m01` to `m12` | budget, adopted; fiscal months 1 to 12 |

### QSMR positions (held out)

| Printed column | Name | Description |
|---|---|---|
| Prior year actual: Operating | `prior_operating` | actual; level at end of fiscal year, 1 yr back; fund sdp_fund_operating |
| Adopted budget: Operating | `adopted_operating` | budget, adopted; level at end of fiscal year; fund sdp_fund_operating |
| Quarter-end actual: Operating | `actual_operating` | actual; level at end of quarter; fund sdp_fund_operating |
| Prior year actual: Categorical | `prior_categorical` | actual; level at end of fiscal year, 1 yr back; fund sdp_fund_categorical |
| Adopted budget: Categorical | `adopted_categorical` | budget, adopted; level at end of fiscal year; fund sdp_fund_categorical |
| Quarter-end actual: Categorical | `actual_categorical` | actual; level at end of quarter; fund sdp_fund_categorical |
| Prior year actual: Total | `prior_total` | actual; level at end of fiscal year, 1 yr back; fund all |
| Adopted budget: Total | `adopted_total` | budget, adopted; level at end of fiscal year; fund all |
| Quarter-end actual: Total | `actual_total` | actual; level at end of quarter; fund all |
| Variance: Operating | `variance_operating` | `adopted_operating` minus `actual_operating` |
| Variance: Categorical | `variance_categorical` | `adopted_categorical` minus `actual_categorical` |
| Variance: Total | `variance_total` | `adopted_total` minus `actual_total` |

### QSMR vendor payments (held out)

| Printed column | Name | Description |
|---|---|---|
| Amount | `amount` | actual; fiscal to date |
