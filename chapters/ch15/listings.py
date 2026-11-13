"""
RMBS

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch15/listings.py
"""

# --- Listing 15.1 ------------------------------------
import sys
sys.path.insert(0, "capstone")
import numpy as np
import pandas as pd
from sfrating import pd_model

loans = pd.read_csv("data/rmbs_loans.csv")
balance = loans["current_balance"]
weights = balance / balance.sum()
for col in ["repayment_type", "occupancy", "employment",
            "fixed_rate_years"]:
    share = balance.groupby(loans[col]).sum() / balance.sum()
    print(col, (100 * share).round(1).to_dict())

# --- Listing 15.2 ------------------------------------
for col in ["current_ltv", "loan_to_income", "interest_rate"]:
    wa = (weights * loans[col]).sum()
    print(f"weighted average {col}: {wa:.2f}")

# --- Listing 15.3 ------------------------------------
smm = 1.2 / (100 - 0.3)
cpr = 1 - (1 - smm) ** 12
print(f"SMM {smm:.4%}, CPR {cpr:.2%}")

# --- Listing 15.4 ------------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
cols = ["opening_balance", "principal_paid", "prepayment"]
totals = perf[cols].sum()
smm_all = totals["prepayment"] / (totals["opening_balance"]
                                  - totals["principal_paid"])
cpr_all = 1 - (1 - smm_all) ** 12
print(f"average SMM {smm_all:.4%}, CPR {cpr_all:.2%}")

# --- Listing 15.5 ------------------------------------
end = loans.set_index("loan_id")["product_end_date"].str[:7]
months = pd.PeriodIndex(perf["period"], freq="M")
ends = pd.PeriodIndex(perf["loan_id"].map(end), freq="M")
perf["to_end"] = (months.year - ends.year) * 12 + (
    months.month - ends.month)
window = perf[perf["to_end"].between(-6, 12)]
by_month = window.groupby("to_end")[cols].sum()
by_month["smm"] = by_month["prepayment"] / (
    by_month["opening_balance"] - by_month["principal_paid"])
print((100 * by_month["smm"].loc[-2:4]).round(2).to_string())

# --- Listing 15.6 ------------------------------------
import matplotlib.pyplot as plt

plt.bar(by_month.index, 100 * by_month["smm"])
plt.xticks(range(-6, 13, 2))
plt.xlabel("Months since the end of the fixed-rate period")
plt.ylabel("SMM (%)")
plt.title("Borrowers refinance when the fixed rate ends")
plt.savefig("figures/ch15_product_end.png")

# --- Listing 15.7 ------------------------------------
defaults = pd.read_csv("data/rmbs_defaults.csv")
bands = pd.cut(defaults["indexed_ltv_at_default"],
               [0, 70, 80, 90, 200],
               labels=["<=70", "70-80", "80-90", ">90"])
table = defaults.groupby(bands, observed=True).agg(
    loans=("loss_severity", "size"),
    severity=("loss_severity", "mean"))
print(table.round(4))
print("months to sale:",
      defaults["recovery_lag_months"].mean().round(1))

# --- Listing 15.8 ------------------------------------
plt.figure()
plt.scatter(defaults["indexed_ltv_at_default"],
            100 * defaults["loss_severity"], s=8)
plt.xlabel("Indexed LTV at default (%)")
plt.ylabel("Loss severity (%)")
plt.title("Severity starts where the equity runs out")
plt.savefig("figures/ch15_severity_ltv.png")

# --- Listing 15.9 ------------------------------------
FORCED_SALE_DISCOUNT = 0.20
SALE_COSTS_PCT = 0.045
FIXED_COSTS = 3_500.0
ACCRUED_MONTHS = 15

def loss_severity(balance, value, rate_pct, mvd_pct,
                  fsd=FORCED_SALE_DISCOUNT):
    """Loss severity per loan after a market value decline."""
    balance = np.asarray(balance, dtype=float)
    value = np.asarray(value, dtype=float)
    stressed = value * (1 - mvd_pct / 100)
    accrual = np.asarray(rate_pct) / 100 / 12 * ACCRUED_MONTHS
    exposure = balance * (1 + accrual)
    proceeds = (stressed * (1 - fsd)
                - (SALE_COSTS_PCT * stressed + FIXED_COSTS))
    proceeds = np.clip(proceeds, 0, None)
    loss = np.clip(exposure - proceeds, 0, None)
    return loss / exposure

print(f"{loss_severity(150_000, 200_000, 2.0, 45):.4f}")

# --- Listing 15.10 -----------------------------------
d = defaults.merge(loans, on="loan_id")
sev0 = loss_severity(d["current_balance"], d["property_value"],
                     d["interest_rate"], 0)
w0 = d["current_balance"] / d["current_balance"].sum()
realised = defaults["loss"].sum() / defaults[
    "exposure_at_default"].sum()
print(f"formula, no MVD: {(w0 * sev0).sum():.2%}")
print(f"realised:        {realised:.2%}")
fsd_mean = defaults["forced_sale_discount"].mean()
print(f"average realised forced-sale discount: {fsd_mean:.1%}")

# --- Listing 15.11 -----------------------------------
model = pd_model.fit_pd_model(loans, defaults)
base_pd = pd_model.predict_pd(model, loans)
stresses = pd.read_csv("data/rating_stresses.csv")
for _, s in stresses.iterrows():
    ff = np.clip(base_pd * s["default_multiple"], 0, 1)
    capped = (base_pd * s["default_multiple"] > 1).mean()
    wa_ff = (weights * ff).sum()
    print(f"{s['rating']:>3}: WA FF {wa_ff:.2%}, "
          f"loans capped {capped:.2%}")

# --- Listing 15.12 -----------------------------------
def rating_level_losses(loans, base_pd, stresses,
                        value_col="property_value"):
    """WAFF, WALS and pool loss for every rating level."""
    bal = loans["current_balance"].to_numpy()
    w = bal / bal.sum()
    rows = []
    for _, s in stresses.iterrows():
        multiple = s["default_multiple"]
        ff = np.clip(np.asarray(base_pd) * multiple, 0, 1)
        ls = loss_severity(bal, loans[value_col],
                           loans["interest_rate"],
                           s["market_value_decline_pct"])
        wa_ff = float((w * ff).sum())
        loss = float((w * ff * ls).sum())
        wa_ls = loss / wa_ff if wa_ff > 0 else 0.0
        rows.append({"rating": s["rating"],
                     "default_frequency": wa_ff,
                     "loss_severity": wa_ls, "pool_loss": loss})
    return pd.DataFrame(rows)

levels = rating_level_losses(loans, base_pd, stresses)
print((100 * levels.set_index("rating")).round(2))

# --- Listing 15.13 -----------------------------------
x = np.arange(len(levels))
fig, ax = plt.subplots()
ax.bar(x - 0.2, 100 * levels["default_frequency"], width=0.4,
       label="WAFF")
ax.bar(x + 0.2, 100 * levels["loss_severity"], width=0.4,
       label="WALS")
ax.plot(x, 100 * levels["pool_loss"], color="#B03A2E",
        marker="o", label="Pool loss")
ax.set_xticks(x, levels["rating"])
ax.set_ylabel("Per cent")
ax.set_title("Frequency, severity and loss by rating level")
ax.legend()
plt.savefig("figures/ch15_rating_levels.png")

# --- Listing 15.14 -----------------------------------
segments = {"Interest-only": loans["repayment_type"]
            == "Interest-only",
            "Buy-to-let": loans["occupancy"] == "Buy-to-let",
            "Self-employed": loans["employment"]
            == "Self-employed"}
rows = []
for name, mask in segments.items():
    for label, m in [(name, mask), ("not " + name, ~mask)]:
        res = rating_level_losses(loans[m], base_pd[m],
                                  stresses).set_index("rating")
        rows.append({"segment": label,
                     "AAA": res.loc["AAA", "pool_loss"],
                     "BBB": res.loc["BBB", "pool_loss"]})
print((pd.DataFrame(rows).set_index("segment") * 100).round(2))

# --- Listing 15.15 -----------------------------------
aaa_loss = levels.set_index("rating").loc["AAA", "pool_loss"]
for name, mask in segments.items():
    res = rating_level_losses(loans[mask], base_pd[mask],
                              stresses).set_index("rating")
    share = weights[mask].sum()
    part = share * res.loc["AAA", "pool_loss"]
    print(f"{name:14s} balance {share:.1%}, "
          f"AAA loss share {part / aaa_loss:.1%}")

# --- Listing 15.16 -----------------------------------
import json
from sfrating import rmbs

levels_pkg = rmbs.rating_level_losses(loans, base_pd, stresses)
same = np.allclose(levels_pkg["pool_loss"], levels["pool_loss"])
print("package matches chapter:", same)

# --- Listing 15.17 -----------------------------------
with open("data/rmbs_deal.json") as f:
    deal = json.load(f)
below = 1.0
rows = []
loss_by_rating = levels_pkg.set_index("rating")["pool_loss"]
for t in deal["tranches"][:-1]:          # class Z is not rated
    below -= t["share_of_pool"]
    ce = below + deal["reserve_fund_target_pct"]
    rating = t["target_rating_illustrative"]
    loss = loss_by_rating[rating]
    rows.append({"class": t["class"], "target": rating,
                 "ce": round(100 * ce, 2),
                 "loss": round(100 * loss, 2),
                 "cushion": round(100 * (ce - loss), 2)})
print(pd.DataFrame(rows).to_string(index=False))

# --- Listing 15.18 -----------------------------------
perf["year"] = perf["period"].str[:4]
yearly = perf.groupby("year")[cols].sum()
smm_y = yearly["prepayment"] / (yearly["opening_balance"]
                                - yearly["principal_paid"])
print((100 * (1 - (1 - smm_y) ** 12)).round(2).to_string())

# --- Listing 15.19 -----------------------------------
smm_ex = 2 / 159.5
print(f"SMM {smm_ex:.4%}, CPR {1 - (1 - smm_ex)**12:.2%}")
print(f"SMM for CPR 10%: {1 - 0.9 ** (1 / 12):.4%}")

# --- Listing 15.20 -----------------------------------
print(f"{loss_severity(120_000, 150_000, 3.0, 25):.2%}")

# --- Listing 15.21 -----------------------------------
high = loans["original_ltv"] > 80
for label, m in [("LTV > 80", high), ("LTV <= 80", ~high)]:
    res = rating_level_losses(loans[m], base_pd[m], stresses)
    aaa = res.set_index("rating").loc["AAA"]
    print(f"{label:9s} share {weights[m].sum():.1%} "
          f"FF {aaa['default_frequency']:.2%} "
          f"LS {aaa['loss_severity']:.2%} "
          f"loss {aaa['pool_loss']:.2%}")

# --- Listing 15.22 -----------------------------------
base_levels = levels.set_index("rating")["pool_loss"]
FORCED_SALE_DISCOUNT = 0.30

def loss_severity(balance, value, rate_pct, mvd_pct,
                  fsd=None):
    fsd = FORCED_SALE_DISCOUNT if fsd is None else fsd
    return rmbs.loss_severity(balance, value, rate_pct,
                              mvd_pct, fsd=fsd)

harsh = rating_level_losses(loans, base_pd, stresses)
harsh = harsh.set_index("rating")["pool_loss"]
for r in ["AAA", "BBB"]:
    print(f"{r}: {base_levels[r]:.2%} -> {harsh[r]:.2%}")
FORCED_SALE_DISCOUNT = 0.20

# --- Listing 15.23 -----------------------------------
from scipy.optimize import brentq

aaa_row = stresses[stresses["rating"] == "AAA"].copy()

def aaa_gap(mvd):
    aaa_row["market_value_decline_pct"] = mvd
    res = rmbs.rating_level_losses(loans, base_pd, aaa_row)
    return res["pool_loss"].iloc[0] - 0.135

mvd_star = brentq(aaa_gap, 45, 70)
print(f"break-even AAA MVD: {mvd_star:.1f}%")

# --- Listing 15.24 -----------------------------------
print(round(rmbs.loss_severity(150_000, 200_000, 2.0, 45), 4))
aaa = rmbs.rating_level_losses(loans, base_pd, stresses).iloc[0]
print(aaa.drop("rating").astype(float).round(4).to_string())
