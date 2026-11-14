"""
Production: Tests, Packaging and AWS

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch22/listings.py
"""

# --- Listing 22.1 ------------------------------------
from pathlib import Path
import sfrating

CAPSTONE = Path(sfrating.__file__).resolve().parents[1]
print("Version:", sfrating.__version__)
print("Package folder:", CAPSTONE.name + "/sfrating")
modules = sorted(p.stem for p in
                 (CAPSTONE / "sfrating").glob("*.py"))
print(len(modules), "files:", ", ".join(modules[:6]), "...")

# --- Listing 22.2 ------------------------------------
import numpy as np
import pytest
from sfrating.pd_model import annualise

def test_annualise_known_answer():
    assert annualise(0.40951, 5) == pytest.approx(0.10)

def test_annualise_one_year_is_unchanged():
    assert annualise(0.03, 1) == pytest.approx(0.03)

test_annualise_known_answer()
test_annualise_one_year_is_unchanged()
print("Both tests passed")

# --- Listing 22.3 ------------------------------------
def annualise_wrong(pd_horizon, years):
    return pd_horizon / years            # the bug

try:
    assert annualise_wrong(0.40951, 5) == pytest.approx(0.10)
except AssertionError:
    print("Test failed: got", annualise_wrong(0.40951, 5))

# --- Listing 22.4 ------------------------------------
import os
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "-q",
     "-p", "no:cacheprovider", "tests"],
    cwd=CAPSTONE, capture_output=True, text=True,
    env={**os.environ, "COLUMNS": "60"})
print(result.stdout.strip().splitlines()[-1])
print("Exit code:", result.returncode)

# --- Listing 22.5 ------------------------------------
print(0.1 + 0.2 == 0.3)
print(f"{0.1 + 0.2:.20f}")
print(0.1 + 0.2 == pytest.approx(0.3))

# --- Listing 22.6 ------------------------------------
from sfrating import rmbs

MVD = np.arange(0, 80, 5)                # 0%, 5%, ..., 75%

def test_severity_bounded_and_rising():
    sev = rmbs.loss_severity(150_000, 200_000, 3.0, MVD)
    assert np.all((sev >= 0) & (sev <= 1))
    assert np.all(np.diff(sev) >= 0)

test_severity_bounded_and_rising()       # silent if it passes
sev = rmbs.loss_severity(150_000, 200_000, 3.0, MVD)
print("Severity at 0%, 25%, 45% decline:",
      sev[[0, 5, 9]].round(4))

# --- Listing 22.7 ------------------------------------
from sfrating import cashflow, data

deal = data.load_deal()
pool = cashflow.project_pool(deal["pool_balance"], 284,
                             cum_default=0.10, severity=0.30,
                             cpr=0.10)
res = cashflow.run_waterfall(pool, deal, sonia_pct=3.0)
ledger = res["ledger"]
classes = [t["class"] for t in deal["tranches"]]
reserve0 = (deal["reserve_fund_target_pct"]
            * deal["pool_balance"])

# --- Listing 22.8 ------------------------------------
cash_in = (ledger["revenue"].sum() + reserve0
           + pool[["scheduled_principal", "prepayments",
                   "recoveries"]].to_numpy().sum())
interest = ledger[[f"int_{c}" for c in classes
                   if c != "Z"]].to_numpy().sum()
principal = sum(t["balance"] for t in deal["tranches"]) - sum(
    ledger[f"bal_{c}"].iloc[-1] for c in classes)
cash_out = (ledger["fees"].sum() + interest
            + ledger["residual"].sum()
            + ledger["reserve"].iloc[-1] + principal)
print(f"Cash in:    £{cash_in:,.2f}")
print(f"Cash out:   £{cash_out:,.2f}")
print(f"Difference: £{cash_in - cash_out:,.6f}")

# --- Listing 22.9 ------------------------------------
# (not executed in the book)
# def parse_args(argv=None):
#     p = argparse.ArgumentParser(
#         description="Thamesbridge rating model")
#     p.add_argument("--data-dir",
#                    default=os.environ.get("SFCM_DATA", "data"))
#     p.add_argument("--output-dir", default="outputs")
#     p.add_argument("--sonia", type=float, default=3.0)
#     p.add_argument("--cprs", type=float, nargs="+",
#                    default=[0.05, 0.20])
#     p.add_argument("--severity-factor", type=float,
#                    default=1.0)
#     return p.parse_args(argv)

# --- Listing 22.10 -----------------------------------
# (not executed in the book)
# log = logging.getLogger("run_rating")
# log.info("loaded %d loans, pool balance GBP %.1f m",
#          len(loans), loans["current_balance"].sum() / 1e6)

# --- Listing 22.11 -----------------------------------
run = subprocess.run(
    [sys.executable, str(CAPSTONE / "run_rating.py"),
     "--output-dir", "outputs"],
    capture_output=True, text=True)
for line in run.stderr.strip().splitlines():
    print(line.replace("INFO run_rating: ", "INFO "))
print("Exit code:", run.returncode)

# --- Listing 22.12 -----------------------------------
import time
import pandas as pd
loans = data.load_loans()

start = time.perf_counter()
sev_loop = [rmbs.loss_severity(b, v, r, 45)
            for b, v, r in zip(loans["current_balance"],
                               loans["property_value"],
                               loans["interest_rate"])]
t_loop = time.perf_counter() - start

start = time.perf_counter()
sev_vec = rmbs.loss_severity(loans["current_balance"],
                             loans["property_value"],
                             loans["interest_rate"], 45)
t_vec = time.perf_counter() - start
print("Same results:", np.allclose(sev_loop, sev_vec))
print(f"Vectorised is {t_loop / t_vec:,.0f} times faster")

# --- Listing 22.13 -----------------------------------
import sys
sys.path.insert(0, str(CAPSTONE))
import run_rating
from sfrating import pd_model, rating

stages = {}
t0 = time.perf_counter()
defaults = data.load_defaults()
model = pd_model.fit_pd_model(loans, defaults)
base_pd = pd_model.predict_pd(model, loans)
stages["PD model"] = time.perf_counter() - t0
t0 = time.perf_counter()
levels = rmbs.rating_level_losses(
    loans, base_pd, data.load_rating_stresses())
stages["rating levels"] = time.perf_counter() - t0
t0 = time.perf_counter()
results = rating.scenario_results(deal, levels, 284)
stages["cashflow scenarios"] = time.perf_counter() - t0
total = sum(stages.values())
for name, t in stages.items():
    print(f"{name:20s} {t / total:6.1%} of the time")

# --- Listing 22.14 -----------------------------------
import hashlib
from sfrating import vasicek

def simulate(seed):
    return vasicek.simulate_portfolio_losses(
        [0.02] * 50, 0.4, 1.0, 0.15, n_sims=2_000, seed=seed)

a, b = simulate(7), simulate(7)
print("Same seed, identical results:", np.array_equal(a, b))
tape = Path("data/rmbs_loans.csv").read_bytes()
digest = hashlib.sha256(tape).hexdigest()
print("Loan tape SHA-256:", digest[:16])

# --- Listing 22.15 -----------------------------------
strat_sql = """
SELECT ltv_band, COUNT(*) AS loans,
       ROUND(SUM(current_balance) / 1e6, 1) AS balance_m,
       ROUND(SUM(current_balance * interest_rate)
             / SUM(current_balance), 3) AS wa_rate
FROM (SELECT *,
             CASE WHEN current_ltv < 60 THEN '1: below 60'
                  WHEN current_ltv < 75 THEN '2: 60 to 75'
                  WHEN current_ltv < 85 THEN '3: 75 to 85'
                  ELSE '4: 85 and above' END AS ltv_band
      FROM dbo.loans) AS banded
GROUP BY ltv_band
ORDER BY ltv_band
"""

roll_sql = """
WITH moves AS (
  SELECT period, status,
         LAG(status) OVER (PARTITION BY loan_id
                           ORDER BY period) AS prev
  FROM dbo.performance)
SELECT LEFT(period, 4) AS [year],
       ROUND(100.0 * SUM(CASE WHEN status = '30'
                              THEN 1 ELSE 0 END)
             / COUNT(*), 3) AS c_to_30_pct
FROM moves
WHERE COALESCE(prev, 'C') = 'C'
GROUP BY LEFT(period, 4)
ORDER BY [year]
"""

# --- Listing 22.16 -----------------------------------
import sqlite3

con = sqlite3.connect(":memory:")
con.execute("ATTACH DATABASE ':memory:' AS dbo")
con.create_function("LEFT", 2, lambda s, n: s[:n])
files = {"loans": "data/rmbs_loans.csv",
         "performance": "data/rmbs_performance.csv.gz"}
for table, path in files.items():
    pd.read_csv(path).to_sql("tmp", con, index=False)
    con.execute(f"CREATE TABLE dbo.{table} AS "
                "SELECT * FROM tmp")
    con.execute("DROP TABLE tmp")
print(pd.read_sql(strat_sql, con).to_string(index=False))
print(pd.read_sql(roll_sql, con).to_string(index=False))

# --- Listing 22.17 -----------------------------------
# (not executed in the book)
# from sqlalchemy import create_engine, text

# engine = create_engine(
#     "mssql+pyodbc://@localhost/Thamesbridge"
#     "?driver=ODBC+Driver+18+for+SQL+Server"
#     "&trusted_connection=yes&TrustServerCertificate=yes")
# query = text("SELECT loan_id, current_balance, current_ltv "
#              "FROM dbo.loans WHERE region = :region")
# london = pd.read_sql(query, engine,
#                      params={"region": "London"})

# --- Listing 22.18 -----------------------------------
filter_sql = """
SELECT loan_id, region, current_balance AS balance,
       current_ltv AS ltv
FROM dbo.loans
WHERE current_ltv BETWEEN 85 AND 95
  AND repayment_type = 'Interest-only'
  AND region IN ('London', 'South East')
  AND loan_id LIKE 'TB00%'
ORDER BY current_balance DESC
LIMIT 3
"""
print(pd.read_sql(filter_sql, con).to_string(index=False))

# --- Listing 22.19 -----------------------------------
having_sql = """
SELECT property_type AS prop, repayment_type AS repay,
       COUNT(*)                             AS loans,
       ROUND(SUM(current_balance) / 1e6, 1) AS bal_m,
       ROUND(AVG(current_ltv), 1)           AS ltv,
       MIN(credit_score)                    AS min_sc,
       MAX(credit_score)                    AS max_sc
FROM dbo.loans
WHERE occupancy = 'Owner-occupied'
GROUP BY property_type, repayment_type
HAVING COUNT(*) >= 300
ORDER BY loans DESC
"""
print(pd.read_sql(having_sql, con).to_string(index=False))

# --- Listing 22.20 -----------------------------------
con.execute("PRAGMA foreign_keys = ON")
con.executescript("""
CREATE TABLE loan_k (
  loan_id      TEXT NOT NULL PRIMARY KEY,
  current_ltv  REAL NOT NULL
               CHECK (current_ltv BETWEEN 0 AND 200)
);
CREATE TABLE perf_k (
  loan_id TEXT NOT NULL REFERENCES loan_k (loan_id),
  period  TEXT NOT NULL,
  status  TEXT NOT NULL CHECK (status IN
          ('C','30','60','90','DEF','PRE')),
  PRIMARY KEY (loan_id, period)
);
INSERT INTO loan_k VALUES ('TB000001', 42.1);
""")
tests = {
    "duplicate loan": "INSERT INTO loan_k VALUES "
                      "('TB000001', 50)",
    "LTV of 250": "INSERT INTO loan_k VALUES ('TB000002', 250)",
    "unknown loan": "INSERT INTO perf_k VALUES "
                    "('TB999999', '2020-01', 'C')",
    "bad status": "INSERT INTO perf_k VALUES "
                  "('TB000001', '2020-01', 'LATE')",
}
for name, sql in tests.items():
    try:
        con.execute(sql)
        print(f"{name:15s} accepted")
    except sqlite3.IntegrityError as err:
        rule = str(err).split(":")[0]   # the rule's name
        print(f"{name:15s} refused: {rule}")

# --- Listing 22.21 -----------------------------------
con.executescript("""
INSERT INTO loan_k (loan_id, current_ltv)
VALUES ('TB000002', 60.1), ('TB000003', 92.0);
UPDATE loan_k SET current_ltv = 88.5
WHERE loan_id = 'TB000003';
DELETE FROM loan_k WHERE current_ltv < 50;
""")
print(pd.read_sql("SELECT * FROM loan_k", con)
      .to_string(index=False))

# --- Listing 22.22 -----------------------------------
con.executescript("""
ALTER TABLE loan_k ADD COLUMN high_ltv INTEGER DEFAULT 0;
UPDATE loan_k SET high_ltv = 1 WHERE current_ltv > 80;
""")
print(pd.read_sql("SELECT * FROM loan_k", con)
      .to_string(index=False))

# --- Listing 22.23 -----------------------------------
region_sql = """
SELECT l.region,
       COUNT(*) AS loans,
       SUM(CASE WHEN d.loan_id IS NOT NULL
                THEN 1 ELSE 0 END) AS defaults,
       ROUND(100.0 * SUM(CASE WHEN d.loan_id IS NOT NULL
                              THEN 1 ELSE 0 END)
             / COUNT(*), 2) AS default_pct
FROM dbo.loans AS l
LEFT JOIN (SELECT loan_id FROM dbo.performance
           WHERE status = 'DEF') AS d
       ON d.loan_id = l.loan_id
GROUP BY l.region
ORDER BY default_pct DESC
LIMIT 5
"""
print(pd.read_sql(region_sql, con).to_string(index=False))

# --- Listing 22.24 -----------------------------------
orphan_sql = """
SELECT COUNT(*) AS loans_without_performance
FROM dbo.loans AS l
LEFT JOIN dbo.performance AS p ON p.loan_id = l.loan_id
WHERE p.loan_id IS NULL
"""
print(pd.read_sql(orphan_sql, con).to_string(index=False))

# --- Listing 22.25 -----------------------------------
full_sql = """
SELECT reconciliation, COUNT(*) AS loans
FROM (SELECT CASE WHEN d.loan_id IS NULL
                  THEN 'only in Jan 2024'
                  WHEN j.loan_id IS NULL
                  THEN 'only in Dec 2023'
                  ELSE 'in both' END AS reconciliation
      FROM (SELECT loan_id FROM dbo.performance
            WHERE period = '2023-12') AS d
      FULL OUTER JOIN
           (SELECT loan_id FROM dbo.performance
            WHERE period = '2024-01') AS j
        ON j.loan_id = d.loan_id) AS r
GROUP BY reconciliation
"""
print(pd.read_sql(full_sql, con).to_string(index=False))

# --- Listing 22.26 -----------------------------------
union_sql = """
SELECT 'defaulted' AS outcome, COUNT(*) AS loans,
       ROUND(SUM(default_balance) / 1e6, 1) AS balance_m
FROM dbo.performance WHERE status = 'DEF'
UNION ALL
SELECT 'prepaid', COUNT(*), ROUND(SUM(prepayment) / 1e6, 1)
FROM dbo.performance WHERE status = 'PRE'
"""
print(pd.read_sql(union_sql, con).to_string(index=False))

# --- Listing 22.27 -----------------------------------
cte_sql = """
WITH ever60 AS (
  SELECT DISTINCT loan_id FROM dbo.performance
  WHERE status IN ('60', '90')),
defaulted AS (
  SELECT loan_id FROM dbo.performance WHERE status = 'DEF')
SELECT COUNT(*) AS ever_60,
       SUM(CASE WHEN d.loan_id IS NOT NULL
                THEN 1 ELSE 0 END) AS later_default
FROM ever60 AS e
LEFT JOIN defaulted AS d ON d.loan_id = e.loan_id
"""
print(pd.read_sql(cte_sql, con).to_string(index=False))

# --- Listing 22.28 -----------------------------------
latest_sql = """
WITH ranked AS (
  SELECT loan_id, period, status, closing_balance,
         ROW_NUMBER() OVER (PARTITION BY loan_id
                            ORDER BY period DESC) AS rn
  FROM dbo.performance)
SELECT status, COUNT(*) AS loans
FROM ranked
WHERE rn = 1
GROUP BY status
ORDER BY loans DESC
"""
print(pd.read_sql(latest_sql, con).to_string(index=False))

# --- Listing 22.29 -----------------------------------
running_sql = """
WITH monthly AS (
  SELECT period, SUM(default_balance) AS defaulted
  FROM dbo.performance GROUP BY period),
running AS (
  SELECT period,
         SUM(defaulted) OVER (ORDER BY period) AS cumulative
  FROM monthly)
SELECT period, ROUND(cumulative / 1e6, 1) AS cumulative_m
FROM running
WHERE period IN ('2020-12', '2021-12', '2022-12',
                 '2023-12', '2024-12')
"""
print(pd.read_sql(running_sql, con).to_string(index=False))

# --- Listing 22.30 -----------------------------------
con.executescript("""
DROP VIEW IF EXISTS dbo.v_snapshot;
CREATE VIEW dbo.v_snapshot AS
WITH ranked AS (
  SELECT p.*, ROW_NUMBER() OVER (PARTITION BY loan_id
                                 ORDER BY period DESC) AS rn
  FROM dbo.performance AS p)
SELECT loan_id, period, status, closing_balance
FROM ranked WHERE rn = 1;
""")
live_sql = """
SELECT COUNT(*) AS live_loans,
       ROUND(SUM(closing_balance) / 1e6, 1) AS balance_m
FROM dbo.v_snapshot
WHERE status NOT IN ('DEF', 'PRE')
"""
print(pd.read_sql(live_sql, con).to_string(index=False))

# --- Listing 22.31 -----------------------------------
plan_sql = ("EXPLAIN QUERY PLAN SELECT COUNT(*) "
            "FROM dbo.performance WHERE period = '2022-06'")
def plan():
    detail = con.execute(plan_sql).fetchall()[0][-1]
    print(detail.replace(" USING", "\n    USING"))

plan()
con.execute("CREATE INDEX dbo.ix_perf_period "
            "ON performance (period)")
plan()

# --- Listing 22.32 -----------------------------------
dq_sql = """
SELECT
 (SELECT COUNT(*) FROM (SELECT loan_id, period
    FROM dbo.performance GROUP BY loan_id, period
    HAVING COUNT(*) > 1) AS k) AS duplicate_keys,
 (SELECT COUNT(*) FROM dbo.performance AS p
    LEFT JOIN dbo.loans AS l ON l.loan_id = p.loan_id
    WHERE l.loan_id IS NULL) AS orphan_rows,
 (SELECT COUNT(*) FROM dbo.performance
    WHERE ABS(opening_balance - principal_paid - prepayment
              - default_balance - closing_balance) > 0.015
   ) AS roll_forward_breaks
"""
print(pd.read_sql(dq_sql, con).to_string(index=False))

# --- Listing 22.33 -----------------------------------
arrears_sql = """
SELECT period,
       ROUND(100.0 * SUM(CASE WHEN status IN ('30','60','90')
                              THEN 1 ELSE 0 END)
             / COUNT(*), 2) AS arrears_pct
FROM performance
WHERE status NOT IN ('DEF', 'PRE')
  AND period IN ('2020-06','2021-06','2022-06','2023-06')
GROUP BY period
ORDER BY period
"""
pd.read_csv("data/rmbs_performance.csv.gz").to_sql(
    "performance", con, index=False)
print(pd.read_sql(arrears_sql, con).to_string(index=False))

# --- Listing 22.34 -----------------------------------
# (not executed in the book)
# import awswrangler as wr
# arrears = wr.athena.read_sql_query(arrears_sql,
#                                    database="thamesbridge")

# --- Listing 22.35 -----------------------------------
EXPECTED = {"A": "AAA", "B": "AA", "C": "A",
            "D": "BBB", "E": "BBB", "Z": "BB"}

def test_thamesbridge_ratings_unchanged():
    args = run_rating.parse_args(["--output-dir", "outputs"])
    out = run_rating.run(args)
    assert out["ratings"].to_dict() == EXPECTED
    assert out["remaining_term"] == 284

test_thamesbridge_ratings_unchanged()
print("Regression test passed")
levels_csv = pd.read_csv("outputs/rating_levels.csv")
print(levels_csv.round(4).to_string(index=False))

# --- Listing 22.36 -----------------------------------
runs = {"base": [],
        "severity +10%": ["--severity-factor", "1.1"],
        "severity +20%": ["--severity-factor", "1.2"],
        "CPR 2% and 30%": ["--cprs", "0.02", "0.30"]}
table = {}
for name, opts in runs.items():
    args = run_rating.parse_args(
        ["--output-dir", "outputs/sens"] + opts)
    table[name] = run_rating.run(args)["ratings"]
print(pd.DataFrame(table).T.to_string())

# --- Listing 22.37 -----------------------------------
print(0.1000005 == pytest.approx(0.1))
print(1_730_141_808.32 == pytest.approx(1_730_141_810))
print(1e-9 == pytest.approx(0))

# --- Listing 22.38 -----------------------------------
QS = [0.90, 0.95, 0.98, 0.995, 0.999, 0.9999]

def test_vasicek_quantile_increases_with_q():
    x = [vasicek.vasicek_quantile(q, 0.02, 0.15) for q in QS]
    assert np.all(np.diff(x) > 0)

def test_vasicek_no_correlation_gives_pd():
    x = vasicek.vasicek_quantile(0.999, 0.02, 1e-8)
    assert x == pytest.approx(0.02, abs=1e-3)

test_vasicek_quantile_increases_with_q()
test_vasicek_no_correlation_gives_pd()
print("Both passed; quantiles:")
x = [vasicek.vasicek_quantile(q, 0.02, 0.15) for q in QS]
print(np.round(x, 4))

# --- Listing 22.39 -----------------------------------
def test_rating_level_losses_ordered():
    lv = rmbs.rating_level_losses(
        loans, base_pd, data.load_rating_stresses())
    assert np.all(np.diff(lv["pool_loss"]) < 0)
    product = lv["default_frequency"] * lv["loss_severity"]
    assert np.allclose(product, lv["pool_loss"])

test_rating_level_losses_ordered()
lv = rmbs.rating_level_losses(
    loans, base_pd, data.load_rating_stresses())
print("Passed:", lv["pool_loss"].round(4).tolist())

# --- Listing 22.40 -----------------------------------
import platform

def run_fingerprint(data_dir="data"):
    fp = {"sfrating": sfrating.__version__,
          "python": platform.python_version(),
          "pandas": pd.__version__,
          "numpy": np.__version__}
    for f in sorted(Path(data_dir).rglob("*.*")):
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        fp[f.relative_to(data_dir).as_posix()] = digest[:16]
    return fp

fp = run_fingerprint()
for key in ["sfrating", "rmbs_loans.csv",
            "rating_stresses.csv"]:
    print(f"{key:20s} {fp[key]}")
print(len(fp), "entries")

# --- Listing 22.41 -----------------------------------
defaults_sql = """
SELECT LEFT(period, 4) AS [year],
       COUNT(*) AS defaults,
       ROUND(SUM(default_balance) / 1e6, 1) AS balance_m
FROM dbo.performance
WHERE status = 'DEF'
GROUP BY LEFT(period, 4)
ORDER BY [year]
"""
print(pd.read_sql(defaults_sql, con).to_string(index=False))

perf22 = pd.read_csv("data/rmbs_performance.csv.gz")
dft = perf22[perf22["status"] == "DEF"]
check = dft.groupby(dft["period"].str[:4]).agg(
    defaults=("loan_id", "count"),
    balance_m=("default_balance", "sum"))
check["balance_m"] = (check["balance_m"] / 1e6).round(1)
print(check)
