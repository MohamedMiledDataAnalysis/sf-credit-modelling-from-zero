"""
pandas and the Loan Tape

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch04/listings.py
"""

# --- Listing 04.1 ------------------------------------
import numpy as np
import pandas as pd

loans = pd.read_csv("data/rmbs_loans.csv")
print(loans.shape)
print(loans[["loan_id", "current_balance",
             "current_ltv", "region"]].head())

# --- Listing 04.2 ------------------------------------
loans.info(verbose=False)
print(loans.dtypes.value_counts())

# --- Listing 04.3 ------------------------------------
cols = ["current_balance", "current_ltv", "interest_rate"]
print(loans[cols].describe().round(2))

# --- Listing 04.4 ------------------------------------
balance = loans["current_balance"]
print(type(balance).__name__, round(balance.sum() / 1e6, 1))

# --- Listing 04.5 ------------------------------------
high_ltv = loans[loans["current_ltv"] > 90]
print(len(high_ltv), round(high_ltv["current_balance"].sum()
                           / balance.sum() * 100, 2))

# --- Listing 04.6 ------------------------------------
btl_london = loans[(loans["occupancy"] == "Buy-to-let")
                   & (loans["region"] == "London")]
south = loans[loans["region"].isin(["London", "South East"])]
print(len(btl_london), len(south))

# --- Listing 04.7 ------------------------------------
print(loans.loc[loans["current_balance"] > 800000,
                ["loan_id", "current_balance", "region"]])

# --- Listing 04.8 ------------------------------------
loans["balance_m"] = loans["current_balance"] / 1e6
loans["paid_down"] = 1 - (loans["current_balance"]
                          / loans["original_balance"])
print(loans[["loan_id", "balance_m",
             "paid_down"]].head(3).round(4))

# --- Listing 04.9 ------------------------------------
largest = loans.sort_values("current_balance",
                            ascending=False)
top20 = largest.head(20)["current_balance"].sum()
print(f"Top 20 loans: {top20 / balance.sum():.2%} of pool")

# --- Listing 04.10 -----------------------------------
print(loans["repayment_type"].value_counts())
print(loans["property_type"].value_counts(normalize=True)
      .round(4))

# --- Listing 04.11 -----------------------------------
by_type = loans.groupby("repayment_type")["current_balance"]
print((by_type.sum() / 1e6).round(1))
print((by_type.sum() / balance.sum()).round(4))

# --- Listing 04.12 -----------------------------------
summary = loans.groupby("occupancy").agg(
    loans=("loan_id", "count"),
    balance_m=("balance_m", "sum"),
    avg_ltv=("current_ltv", "mean"))
print(summary.round(2))

# --- Listing 04.13 -----------------------------------
toy = pd.DataFrame({"balance": [100000, 100000, 400000],
                    "ltv": [50, 60, 90]})
print(round(np.average(toy["ltv"], weights=toy["balance"]), 1))

# --- Listing 04.14 -----------------------------------
def wa(group, column, weight="current_balance"):
    return np.average(group[column], weights=group[weight])

print(round(wa(loans, "current_ltv"), 2))
print(loans.groupby("occupancy")
      .apply(wa, "current_ltv", include_groups=False)
      .round(2))

# --- Listing 04.15 -----------------------------------
edges = [0, 50, 60, 70, 80, 90, 100]
test = pd.Series([45.0, 50.0, 50.1, 60.0, 95.0])
print(pd.cut(test, edges).astype(str).tolist())

# --- Listing 04.16 -----------------------------------
labels = ["<=50", "50-60", "60-70", "70-80", "80-90", ">90"]
loans["ltv_band"] = pd.cut(loans["current_ltv"], edges,
                           labels=labels)
print(loans["ltv_band"].value_counts(sort=False))

# --- Listing 04.17 -----------------------------------
strat = loans.groupby("ltv_band", observed=True).agg(
    loans=("loan_id", "count"),
    balance_m=("balance_m", "sum"))
pool_m = balance.sum() / 1e6     # whole pool, £ million
strat["pct_balance"] = 100 * strat["balance_m"] / pool_m
strat["wa_rate"] = (loans.groupby("ltv_band", observed=True)
                    .apply(wa, "interest_rate",
                           include_groups=False))
print(strat.round(2))
print("Total check:", round(strat["pct_balance"].sum(), 6))

# --- Listing 04.18 -----------------------------------
loans = pd.read_csv("data/rmbs_loans.csv",
                    parse_dates=["origination_date",
                                 "product_end_date"])
loans["balance_m"] = loans["current_balance"] / 1e6
loans["ltv_band"] = pd.cut(loans["current_ltv"], edges,
                           labels=labels)
vintage = loans["origination_date"].dt.year
print(vintage.value_counts().sort_index())
print(loans["origination_date"].max().date())

# --- Listing 04.19 -----------------------------------
cutoff = pd.Timestamp("2019-12-31")
months_to_reset = ((loans["product_end_date"] - cutoff)
                   .dt.days / 30.44).round()
print((months_to_reset.between(1, 12)).sum())

# --- Listing 04.20 -----------------------------------
defaults = pd.read_csv("data/rmbs_defaults.csv")
print(defaults.shape)
tape = loans.merge(defaults[["loan_id", "default_period",
                             "loss"]],
                   on="loan_id", how="left")
print(tape.shape)
print(tape[["loan_id", "default_period", "loss"]].head(3))

# --- Listing 04.21 -----------------------------------
print(tape["loss"].isna().sum())
tape["defaulted"] = tape["default_period"].notna()
tape["loss"] = tape["loss"].fillna(0.0)
total_loss_m = tape["loss"].sum() / 1e6
print(tape["defaulted"].sum(), round(total_loss_m, 2))

# --- Listing 04.22 -----------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
perf = perf.sort_values(["loan_id", "period"])
perf["prev_status"] = (perf.groupby("loan_id")["status"]
                       .shift(1))
print(perf[["loan_id", "period", "status",
            "prev_status"]].head(3))

# --- Listing 04.23 -----------------------------------
pivot = tape.pivot_table(index="ltv_band",
                         columns="repayment_type",
                         values="defaulted", aggfunc="mean",
                         observed=True)
print((100 * pivot).round(2))

# --- Listing 04.24 -----------------------------------
import matplotlib.pyplot as plt

loans["current_ltv"].plot.hist(bins=40)
plt.xlabel("Current LTV (%)")
plt.ylabel("Number of loans")
plt.title("Current LTV of the Thamesbridge pool")
plt.savefig("figures/ch04_ltv_hist.png")

# --- Listing 04.25 -----------------------------------
rate_by_band = (tape.groupby("ltv_band", observed=True)
                ["defaulted"].mean() * 100)
rate_by_band.plot.bar(rot=0)
plt.xlabel("Current LTV band (%)")
plt.ylabel("Loans defaulted 2020-24 (%)")
plt.title("Default rate rises with LTV")
plt.savefig("figures/ch04_default_by_ltv.png")
print(rate_by_band.round(2).to_string())

# --- Listing 04.26 -----------------------------------
total = loans["current_balance"].sum()
pool = {
    "Number of loans": len(loans),
    "Balance (£m)": total / 1e6,
    "Average balance (£)": loans["current_balance"].mean(),
    "WA current LTV (%)": wa(loans, "current_ltv"),
    "WA interest rate (%)": wa(loans, "interest_rate"),
    "WA seasoning (months)": wa(loans, "seasoning_months"),
    "WA remaining term (months)":
        wa(loans, "remaining_term_months"),
    "WA loan-to-income": wa(loans, "loan_to_income"),
}
for col, value in [("repayment_type", "Interest-only"),
                   ("occupancy", "Buy-to-let"),
                   ("employment", "Self-employed")]:
    mask = loans[col] == value
    share = loans.loc[mask, "current_balance"].sum() / total
    pool[f"{value} (% bal)"] = 100 * share
print(pd.Series(pool).round(2).to_string())

# --- Listing 04.27 -----------------------------------
def stratify(df, column, edges=None, labels=None):
    data = df.copy()
    key = column
    if edges is not None:
        key = column + "_band"
        data[key] = pd.cut(data[column], edges, labels=labels)
    grouped = data.groupby(key, observed=True)
    table = grouped.agg(loans=("loan_id", "count"),
                        balance_m=("balance_m", "sum"))
    table["pct_bal"] = 100 * table["balance_m"] / (
        table["balance_m"].sum())
    for c, name in [("current_ltv", "wa_ltv"),
                    ("interest_rate", "wa_rate")]:
        table[name] = grouped.apply(wa, c,
                                    include_groups=False)
    return table.round(2)

# --- Listing 04.28 -----------------------------------
rate_edges = [0, 1.0, 1.5, 2.0, 2.5, 4.0]
rate_labels = ["<=1.0", "1.0-1.5", "1.5-2.0", "2.0-2.5", ">2.5"]
print(stratify(loans, "interest_rate", rate_edges,
               rate_labels))

# --- Listing 04.29 -----------------------------------
by_region = stratify(loans, "region")
print(by_region.sort_values("pct_bal", ascending=False)
      .head(6))

# --- Listing 04.30 -----------------------------------
for name, table in [("rate", stratify(loans, "interest_rate",
                                      rate_edges, rate_labels)),
                    ("region", by_region)]:
    print(name, table["loans"].sum(),
          round(table["balance_m"].sum(), 1))

# --- Listing 04.31 -----------------------------------
pack = {"ltv": stratify(loans, "current_ltv", edges, labels),
        "rate": stratify(loans, "interest_rate", rate_edges,
                         rate_labels),
        "region": by_region}
for name, table in pack.items():
    table.to_csv(f"outputs/ch04_strat_{name}.csv")
print(sorted(pack))

# --- Listing 04.32 -----------------------------------
sub = pd.DataFrame({"bal": [200000, 50000, 150000, 100000],
                    "rate": [2.0, 3.0, 1.5, 2.5]})
print(sub["rate"].mean(),
      np.average(sub["rate"], weights=sub["bal"]))

# --- Listing 04.33 -----------------------------------
x = pd.Series([60.0, 60.01, 80.0, 0.0, 100.0])
print(pd.cut(x, [0, 60, 80, 100],
             labels=["0-60", "60-80", "80-100"]).tolist())

# --- Listing 04.34 -----------------------------------
reg = tape.groupby("region").agg(
    loans=("loan_id", "count"),
    defaults=("defaulted", "sum"),
    rate_pct=("defaulted", "mean"),
    loss_k=("loss", "sum"))
reg["rate_pct"] = 100 * reg["rate_pct"]
reg["loss_k"] = reg["loss_k"] / 1000
print(reg.sort_values("rate_pct", ascending=False)
      .head(5).round(2))

# --- Listing 04.35 -----------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
perf["arrears"] = perf["status"].isin(["30", "60", "90"])
dec = perf[perf["period"] == "2021-12"]
by_count = dec["arrears"].mean()
by_bal = (dec.loc[dec["arrears"], "opening_balance"].sum()
          / dec["opening_balance"].sum())
print(f"Dec 2021: {by_count:.3%} by count, "
      f"{by_bal:.3%} by balance")

# --- Listing 04.36 -----------------------------------
perf["arrears_bal"] = (perf["opening_balance"]
                       * perf["arrears"])
monthly = perf.groupby("period")[["arrears_bal",
                                  "opening_balance"]].sum()
share = monthly["arrears_bal"] / monthly["opening_balance"]
print(share.idxmax(), f"{share.max():.3%}")

# --- Listing 04.37 -----------------------------------
lti_edges = [0, 3.0, 3.5, 4.0, 5.0]
lti_labels = ["<=3.0", "3.0-3.5", "3.5-4.0", ">4.0"]
lti = stratify(tape, "loan_to_income", lti_edges, lti_labels)
tape["lti_band"] = pd.cut(tape["loan_to_income"], lti_edges,
                          labels=lti_labels)
lti["def_pct"] = (100 * tape.groupby("lti_band", observed=True)
                  ["defaulted"].mean()).round(2)
print(lti[["pct_bal", "wa_ltv", "def_pct"]])

# --- Listing 04.38 -----------------------------------
cross = tape.pivot_table(index="ltv_band", columns="lti_band",
                         values="defaulted", aggfunc="mean",
                         observed=True)
print((100 * cross).round(1))

# --- Listing 04.39 -----------------------------------
# (not executed in the book)
# import json
# import os
# from pathlib import Path

# import pandas as pd

# DATA_DIR = Path(os.environ.get("SFCM_DATA", "data"))


# def _path(name: str) -> Path:
#     return DATA_DIR / name


# def load_loans() -> pd.DataFrame:
#     """Static loan tape of the Thamesbridge pool at cut-off."""
#     return pd.read_csv(_path("rmbs_loans.csv"),
#                        parse_dates=["origination_date",
#                                     "product_end_date"])


# def load_defaults() -> pd.DataFrame:
#     """One row per defaulted loan with exposure, recovery
#     and loss."""
#     return pd.read_csv(_path("rmbs_defaults.csv"))

# --- Listing 04.40 -----------------------------------
from sfrating import data
check = data.load_loans()
pool_m = check["current_balance"].sum() / 1e6
print(check.shape, round(pool_m, 1))
print(len(data.load_defaults()), data.load_deal()["deal_name"])
