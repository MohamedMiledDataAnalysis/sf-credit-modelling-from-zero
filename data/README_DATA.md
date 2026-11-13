# The datasets

Every file in this folder is **synthetic**. It was produced by `scripts/generate_data.py`
with the seed 2026, so running the script again gives identical files. The originator
(Thamesbridge Building Society), the transaction (Thamesbridge Mortgages No. 1 plc), the
borrowers and the obligors are fictional. Rating tables and stresses are illustrative
teaching values, not the criteria of any rating agency.

## rmbs_loans.csv — the loan tape at the cut-off date (10,000 rows)

Cut-off date 31 December 2019. Every loan is current (no arrears) at the cut-off date.

| column | meaning |
|---|---|
| loan_id | TB000001 … TB010000 |
| origination_date | first day of the month the loan was made |
| original_balance | amount lent (£) |
| current_balance | balance outstanding at the cut-off date (£) |
| property_value | valuation at origination (£) |
| original_ltv, current_ltv | loan-to-value at origination and at cut-off (%) |
| interest_rate | current interest rate (% per year) |
| fixed_rate_years, product_end_date | length and end of the fixed-rate product |
| term_months, remaining_term_months, seasoning_months | contractual term, months left, months since origination |
| repayment_type | Repayment or Interest-only |
| occupancy | Owner-occupied or Buy-to-let |
| property_type | House, Flat or Bungalow |
| region | twelve UK regions |
| employment | Employed or Self-employed |
| income, loan_to_income | gross annual income (£) and original balance / income |
| credit_score | bureau-style score, 0–999 |

## rmbs_performance.csv.gz — monthly performance (449,052 rows)

One row per loan per month from 2020-01 to 2024-12 while the loan is alive. The month in which
a loan defaults (status DEF) or repays in full (status PRE) is included; after that the loan
has no more rows.

| column | meaning |
|---|---|
| loan_id | links to rmbs_loans.csv |
| period | month, YYYY-MM |
| status | C (current), 30, 60, 90 (days past due), DEF (default: 120+ days past due), PRE (prepaid) |
| opening_balance, closing_balance | balance at the start and end of the month (£) |
| scheduled_payment | contractual monthly payment (£) |
| principal_paid, interest_due | principal repaid and interest due this month (£) |
| prepayment | balance repaid early this month (£) |
| default_balance | balance written into default this month (£) |

## rmbs_defaults.csv — one row per defaulted loan (540 rows)

Exposure at default (balance plus accrued interest during the recovery period), the sale
of the property after `recovery_lag_months`, the recovery, the loss and the loss severity
(loss / exposure).

| column | meaning |
|---|---|
| loan_id | links to rmbs_loans.csv |
| default_period | month of default, YYYY-MM |
| months_since_origination | age of the loan at default |
| balance_at_default | balance written into default (£) |
| indexed_value_at_default, indexed_ltv_at_default | property value indexed by `hpi` (£) and balance / value (%) |
| recovery_lag_months | months from default to the sale of the property (9–21) |
| forced_sale_discount | discount of the sale price to the indexed value (share) |
| sale_value | indexed property value in the month of sale, before the discount (£) |
| sale_costs | 4.5% of `sale_value` plus £3,500 |
| accrued_interest | interest accrued on the balance during the recovery lag (£) |
| exposure_at_default | balance_at_default + accrued_interest (£) |
| recovery | sale_value × (1 − forced_sale_discount) − sale_costs, capped at the exposure, floored at 0 (£); the file rounds the discount to 3 decimals, so recomputing gives up to £231 of difference |
| loss, loss_severity | exposure − recovery (£) and loss / exposure |

## macro.csv — monthly economy (60 rows)

period (YYYY-MM, 2020-01 to 2024-12), unemployment_rate (%), hpi (house price index,
100 = December 2019, the cut-off date), sonia (overnight rate, %),
credit_factor (standardised systematic credit factor: high = bad times).

## rmbs_deal.json — capital structure

Classes A (88%), B (4%), C (3%), D (2.5%), E (1.5%), Z (1%) of the pool balance, margins over
SONIA, a 1.5% reserve fund funded by a subordinated loan from the originator, sequential
principal payments, and excess spread used to cure losses.

## cmbs_loans.csv — 120 commercial real estate loans

Property type, value, balance, LTV, interest rate, net operating income (NOI), DSCR, term,
NOI and value after a stress period, LTV at maturity, term default and maturity default
flags, loss severity.

## auto_loans.csv — 8,000 car finance loans (survival format)

PCP or HP, new or used vehicle, credit score, amount, term, deposit, APR, months observed,
outcome (default, prepaid or censored), default flag, recovery rate if defaulted.

## clo_portfolio.csv — 150 leveraged loans

Obligor, industry, rating, par, spread (%), years to maturity, recovery assumption, one-year
probability of default from `rating_default_table.csv`.

## rating_default_table.csv and rating_stresses.csv

Illustrative cumulative default probabilities by rating and horizon (1–10 years), and
illustrative rating-level stresses (default multiple, market value decline, prepayment
stress, target loss quantile) used by the teaching model in Chapters 14, 15 and 20.

## Opening the files in Excel

The CSV files are plain ASCII text (no £ signs; amounts are in £ without a symbol), with
commas between fields, a full stop as decimal point and line-feed line endings. Excel opens
them, with four points to know.

* **rmbs_performance.csv.gz is compressed.** Excel cannot open a `.gz` file. The Python code
  reads it as it is; to look at it in Excel, unzip a copy into `outputs/` (ignored by Git),
  not into `data/`, because the data fingerprint of Chapter 22 hashes every file in `data/`.
  From the repository root, on any system:
  `python -c "import pandas as pd; pd.read_csv('data/rmbs_performance.csv.gz').to_csv('outputs/rmbs_performance.csv', index=False)"`.
  Without Python: copy the `.gz` file into `outputs/`, then double-click the copy in Finder
  (macOS) or open it with 7-Zip and choose *Extract here* (Windows). The unzipped file is
  29.8 MB with 449,053 lines (header included), below Excel's limit of 1,048,576 rows.
  Keep the `.gz` file in `data/`: the code reads it.
* **Months become dates.** Excel turns `period` and `default_period` (`2020-01`) into the
  date 1 January 2020 and displays it as `Jan-20` or `01/01/2020`, depending on your settings.
  `origination_date` and `product_end_date` (`2014-08-01`) also become dates, shown in your
  regional format. To keep the text, use *Data → From Text/CSV*, click *Transform Data*, and
  set those columns to *Text* before loading.
* **Commas as decimal separator.** If your computer's region uses a comma for decimals (France,
  Germany, Spain, …), double-clicking a CSV puts each row in one cell, and `0.054` is read as
  text. Before importing, set *Data → Get Data → Query Options → Current Workbook → Regional
  Settings → Locale* to *English (United Kingdom)*; then use *Data → From
  Text/CSV* with *Comma* as delimiter.
* **Never save over the originals.** Saving from Excel rewrites dates in your regional format
  and drops trailing zeros (`14900.0` becomes `14900`), so the files no longer match the book's
  hashes and `2020-01` may no longer parse. Use *File → Save As* under a new name outside `data/`,
  or restore a file with `git checkout -- data/FILE`.

Nothing else is lost: identifiers are text with a letter prefix (`TB000001`, `AU00001`,
`CM0001`, `Obligor 001`), so no leading zeros disappear; no number has more than 10 significant
digits, within Excel's 15; and the largest file, rmbs_loans.csv, has 10,001 lines.
