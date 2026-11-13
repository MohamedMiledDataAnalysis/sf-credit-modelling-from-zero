# Structured Finance Credit Modelling from Zero — companion repository

Code, data and the finished capstone model for the book
**_Structured Finance Credit Modelling from Zero: From Absolute Beginner to Rating Agency Quant, Step by Step in Python_** by Mohamed Miled.

The book takes you from no programming and no finance to building, testing and documenting
the default and loss models used to rate RMBS, CMBS, ABS and CLO tranches, one idea at a time.

## What is here

```
data/                   every dataset used in the book (synthetic, seeded)
  README_DATA.md        what every file and column means
scripts/
  generate_data.py      the program that creates the data (seed 2026)
chapters/
  ch00/ … ch24/         every code listing of each chapter, in the order of the book
sql/
  athena/               Athena tables and queries (Chapter 22)
  sqlserver/            SQL Server (T-SQL) scripts: tables, BULK INSERT, queries
capstone/
  sfrating/             the finished teaching rating model, built chapter by chapter
  tests/                its unit tests (pytest)
  run_rating.py         run the whole model end to end
  pyproject.toml        package definition
figures/, outputs/      empty: the charts and reports the code saves
.github/workflows/      GitHub Actions: tests on every push (Chapter 22)
requirements.txt        Python libraries
```

## Quick start

```bash
git clone https://github.com/mohamedmileddataanalysis/sf-credit-modelling-from-zero.git
cd sf-credit-modelling-from-zero
python -m venv .venv                     # macOS / Linux: python3 -m venv .venv
.venv\Scripts\Activate.ps1               # Windows PowerShell
source .venv/bin/activate                # macOS / Linux
python -m pip install -r requirements.txt
python -m pip install -e capstone
python chapters/ch11/listings.py         # run one chapter's listings
python -m pytest capstone/tests          # run the tests
```

Python 3.12 or later is recommended (3.11 is the minimum tested). If PowerShell refuses to run
`Activate.ps1`, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once.

Run every script from the repository root, so that the paths `data/…` and `figures/…` resolve.

## The data

All borrowers, loans, obligors, the originator (Thamesbridge Building Society) and the
transaction (Thamesbridge Mortgages No. 1 plc) are fictional. Rating levels, stresses and
default tables are illustrative teaching values; they are not the criteria of any credit
rating agency and must not be used to rate, buy or sell any security.

`data/README_DATA.md` describes every file and column, and ends with how to open the files
in Excel (the performance file is gzip-compressed and must be unzipped first).

To regenerate the data exactly:

```bash
python scripts/generate_data.py
```

The files come out byte for byte identical to the ones in the repository.

## The capstone package `sfrating`

| module | chapter | what it does |
|---|---|---|
| data | 4 | load every dataset |
| pd_model | 6, 10 | logistic PD model, Gini, expected loss |
| numerics | 7 | bisection, Newton, trapezoid, Simpson |
| merton | 9 | structural model of default |
| rollrate | 11 | Markov roll-rate model |
| survival | 12 | Kaplan–Meier time to default |
| vasicek | 13 | one-factor model, copula simulation |
| loss_dist | 14 | pool loss distribution |
| rmbs | 15 | rating-level default frequency and severity |
| cmbs | 16 | DSCR, LTV, refinancing test |
| abs_auto | 17 | static-pool loss curves |
| clo | 18 | diversity score, binomial expansion |
| cashflow | 19 | pool cashflows and waterfall |
| rating | 20 | rating scenarios and assignment |
| report | 21 | LaTeX model report |

## Licence

Code: MIT licence (see `LICENSE`). The book text is © 2026 Mohamed Miled, all rights reserved,
and is not part of this repository.
