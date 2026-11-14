# The datasets

Every file is **synthetic**: the originators (Thamesbridge Building Society, Wessex Motor
Finance Limited), the transactions, the borrowers and the obligors are fictional. Rating
tables and stresses are illustrative teaching values, not the criteria of any rating agency.

## Two layers, as in real work

**`data/raw/` — the input files, in the formats they arrive in at work.** These are the
only data files stored in the repository.

| folder | files | real-world format |
|---|---|---|
| `uk_rmbs/` | `THAMESBRIDGE_RRE_2019-12-31.zip` | FCA underlying exposure report, zipped XML (message DRAFT3auth.099.001.04, XML schemas v1.3.2), residential real estate: field codes RREL1–RREL84 and RREC1–RREC23, no-data codes ND1–ND5 |
| | `Thamesbridge_originator_additional_data_2019-12-31.xlsx` | fields outside the template (bureau score) |
| | `Thamesbridge_deal_summary.xlsx` | term sheet summary: transaction and notes |
| | `servicer_monthly/Thamesbridge_servicer_report_YYYY-MM.xlsx` (60 files) | monthly loan-level servicer report with a title block |
| | `Thamesbridge_losses_and_recoveries_2024-12.xlsx` | defaults, possessions and recoveries report |
| | `Thamesbridge_investor_report_2024-12.xlsx` | investor report template (Annex 12: IVSS, IVSR, IVSF sections) |
| `economic/` | `BoE_IUMASOIA_monthly_average_SONIA.csv` | Bank of England Database export |
| | `ONS_MGSX_unemployment_rate.csv` | ONS time-series download (8 metadata rows) |
| | `UK-HPI-full-file-2024-12.csv` | HM Land Registry UK House Price Index full file (first ten columns) |
| | `internal_credit_cycle_index.csv` | internal model input |
| `uk_auto/` | `WESSEX_AUTO_2024-12-31.zip` + additional data | FCA underlying exposure report, zipped XML, automobile: AUTL1–AUTL84; a revolving pool (closing 30 June 2023, later loans added in the month they are made) |
| `cmbs/` | `CMBS_servicer_loan_history_2024-12.xlsx` | servicer loan history report |
| `clo/` | `CLO_trustee_report_2024-12.xlsx` | trustee report, collateral portfolio |
| `assumptions/` | `rating_assumptions.xlsx` | rating criteria tables (default table by rating and year, stresses) |

`data/raw/data_dictionary.xlsx` documents every field: code, name, format, the code lists
(for example RREL69 `PERF`, `ARRE`, `DFLT`, `RDMD`), the no-data codes and the model column
each field feeds.

Both XML reports validate against the FCA schema `DRAFT3auth.099.001.04_1.3.2.xsd` with no
error. The schema is not stored here: download *XML schemas and validation rules* from the
FCA securitisation page (https://www.fca.org.uk/markets/securitisation) and run
`fca_xml.validate(report, xsd)` from `scripts/fca_xml.py`. `scripts/fca_xml_paths.csv` gives
the XML path, the allowed no-data codes and the FCA validation rule of every field; it was
taken from the FCA validation rules workbook v1.3.2. `prepare_data.py` applies those
validation rules each time it runs. The LEIs are fictional, so the GLEIF look-up rule cannot
pass and is not applied.

The values in the templates are synthetic; the field codes, formats and code lists are those
of the templates. The economic files copy the layouts of the public downloads; their values
are synthetic and the ONS file says so in its title row.

**`data/*.csv`, `data/*.json` — the model tables**, built by

```bash
python scripts/prepare_data.py
```

Run it once after cloning (it prints nothing for a few minutes, then one summary line). It reads the XML reports, applies the FCA validation rules, decodes the template codes with
the data dictionary, checks formats and no-data codes, joins the loan and collateral sections,
stacks the 60 servicer reports, reconciles the last report with the investor report and
writes the tables below. These tables are not stored in the repository, because they are
outputs of the preparation step.

`scripts/generate_data.py` (seed 2026) created the raw files. Running it again rebuilds them,
and `prepare_data.py` then gives model tables byte for byte identical to the ones used in
the book. The Excel files record the date they were saved, so their bytes differ between
runs while their contents do not.

## rmbs_loans.csv — the loan tape at the cut-off date (10,000 rows)

Cut-off date 31 December 2019. Every loan is current (no arrears) at the cut-off date. The
pool balance is £1,730,141,807.95 (£1,730.1 million).

**Interest rates.** Each mortgage pays its initial fixed rate until `product_end_date`, then
the reversion rate, Bank Rate + 3.75%. Bank Rate is 0.75% from August 2018, so at the cut-off
date 4,875 loans (48.75%) are past their fixed period and pay 4.50% (0.75% + 3.75%); these
include the loans whose fixed rate ended on 1 December 2019. The other 5,125 pay their fixed
rate (0.90% to 3.41%). From origination to the cut-off date the
instalment is recalculated each month at the rate in force, so `current_balance` reflects the
higher rate after reversion.

| column | meaning |
|---|---|
| loan_id | TB000001 … TB010000 |
| origination_date | first day of the month the loan was made |
| original_balance | amount lent (£) |
| current_balance | balance outstanding at the cut-off date (£) |
| property_value | valuation at origination (£) |
| original_ltv, current_ltv | loan-to-value at origination and at cut-off (%) |
| interest_rate | rate in force at the cut-off date (% per year): the fixed rate, or 4.50% after reversion |
| fixed_rate_years, product_end_date | length and end of the fixed-rate product |
| term_months, remaining_term_months, seasoning_months | contractual term, months left, months since origination |
| repayment_type | Repayment or Interest-only |
| occupancy | Owner-occupied or Buy-to-let |
| property_type | House, Flat or Bungalow |
| region | twelve UK regions |
| employment | Employed or Self-employed |
| income, loan_to_income | gross annual income (£) and original balance / income |
| credit_score | bureau-style score, 0–999 |

## rmbs_performance.csv.gz — monthly performance (450,834 rows)

One row per loan per month from 2020-01 to 2024-12 while the loan is alive. The month in which
a loan defaults (status DEF) or repays in full (status PRE) is included; after that the loan
has no more rows. Over the 60 months 555 loans default and 3,758 repay in full.

Bank Rate stays at 0.75% in January and February 2020, so the reversion rate is 4.50% in
those two months. From March 2020 the reversion rate is the `sonia` series of `macro.csv` +
3.75%, month by month (3.85% while SONIA is 0.10%). The scheduled payment is recalculated every month from the opening balance, the rate
in force and the remaining term (interest only for interest-only loans). When a loan reverts,
the rise of its payment over the payment at the fixed rate (the payment shock) raises its
monthly probability of falling into arrears.

| column | meaning |
|---|---|
| loan_id | links to rmbs_loans.csv |
| period | month, YYYY-MM |
| status | C (current), 30, 60, 90 (days past due), DEF (default: 120+ days past due), PRE (prepaid) |
| opening_balance, closing_balance | balance at the start and end of the month (£) |
| scheduled_payment | contractual monthly payment at this month's rate (£) |
| principal_paid, interest_due | principal repaid and interest due this month (£) |
| prepayment | balance repaid early this month (£) |
| default_balance | balance written into default this month (£) |

## rmbs_defaults.csv — one row per defaulted loan (555 rows)

Exposure at default (balance plus accrued interest during the recovery period), the sale
of the property after `recovery_lag_months`, the recovery, the loss and the loss severity
(loss / exposure). For 52 defaults the sale month falls after December 2024: the losses
report marks them `Property Sold` = `N`, values the sale at the December 2024 index and
gives the servicer's estimated recovery and loss. `prepare_data.py` drops that flag.

| column | meaning |
|---|---|
| loan_id | links to rmbs_loans.csv |
| default_period | month of default, YYYY-MM |
| months_since_origination | age of the loan at default (months from origination to the default month) |
| balance_at_default | balance written into default (£) |
| indexed_value_at_default, indexed_ltv_at_default | property value indexed by `hpi` (£) and balance / value (%) |
| recovery_lag_months | months from default to the sale of the property (9–21) |
| forced_sale_discount | discount of the sale price to the indexed value (share) |
| sale_value | indexed property value in the month of sale, before the discount (£) |
| sale_costs | 4.5% of `sale_value` plus £3,500 |
| accrued_interest | interest accrued on the balance during the recovery lag (£) |
| exposure_at_default | balance_at_default + accrued_interest (£) |
| recovery | sale_value × (1 − forced_sale_discount) − sale_costs, capped at the exposure, floored at 0 (£); the file rounds the discount to 3 decimals, so recomputing gives up to £243 of difference |
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
  (macOS) or open it with 7-Zip and choose *7-Zip → Extract Here* (Windows). The unzipped file is
  30.1 MB with 450,835 lines (header included), below Excel's limit of 1,048,576 rows.
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
  or rebuild every model table with `python scripts/prepare_data.py`.

Nothing else is lost: identifiers are text with a letter prefix (`TB000001`, `AU00001`,
`CM0001`, `Obligor 001`), so no leading zeros disappear; no number has more than 10 significant
digits, within Excel's 15; and the largest file, rmbs_loans.csv, has 10,001 lines.
