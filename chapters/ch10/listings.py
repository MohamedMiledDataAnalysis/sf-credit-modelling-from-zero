"""
PD, LGD, EAD and Expected Loss

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch10/listings.py
"""

# --- Listing 10.1 ------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
loans["defaulted"] = loans["loan_id"].isin(
    defaults["loan_id"]).astype(int)
print(f"Five-year default rate: "
      f"{loans['defaulted'].mean():.2%}")
for col in ["repayment_type", "occupancy", "employment"]:
    rates = loans.groupby(col)["defaulted"].mean()
    print(rates.round(4).to_string(), "\n")

# --- Listing 10.2 ------------------------------------
loans["cohort"] = loans["origination_date"].str[:4]
cohorts = loans.groupby("cohort")["defaulted"].agg(
    loans="size", default_rate="mean")
print(cohorts.round(4))

# --- Listing 10.3 ------------------------------------
def annualise(pd_horizon, years):
    """Constant annual PD giving the same cumulative PD."""
    return 1 - (1 - np.asarray(pd_horizon)) ** (1 / years)

p_annual = annualise(0.054, 5)
print(f"Annual PD: {p_annual:.4%}")
print(f"Back to 5 years: {1 - (1 - p_annual) ** 5:.4%}")

# --- Listing 10.4 ------------------------------------
first = defaults.iloc[0]
cols = ["balance_at_default", "accrued_interest",
        "exposure_at_default", "sale_value",
        "forced_sale_discount", "sale_costs",
        "recovery", "loss", "loss_severity"]
print(first[cols].to_string())

# --- Listing 10.5 ------------------------------------
sev = defaults["loss_severity"]
print(f"Defaults with zero loss: {(sev == 0).mean():.1%}")
print(f"Mean severity (by count): {sev.mean():.2%}")
weighted = (defaults["loss"].sum()
            / defaults["exposure_at_default"].sum())
print(f"Severity weighted by exposure: {weighted:.2%}")

plt.hist(sev * 100, bins=30)
plt.xlabel("Loss severity (%)")
plt.ylabel("Number of defaults")
plt.title("Half of defaults lose nothing")
plt.savefig("figures/ch10_severity_hist.png")

# --- Listing 10.6 ------------------------------------
bands = [0, 60, 70, 80, 90, 120]
defaults["ltv_band"] = pd.cut(
    defaults["indexed_ltv_at_default"], bands)
by_band = defaults.groupby("ltv_band", observed=True).agg(
    defaults=("loan_id", "size"),
    mean_severity=("loss_severity", "mean"),
    discount=("forced_sale_discount", "mean"))
print(by_band.round(4))

# --- Listing 10.7 ------------------------------------
accrued_share = (defaults["accrued_interest"].sum()
                 / defaults["balance_at_default"].sum())
print(f"Accrued interest / balance: {accrued_share:.2%}")
print(f"Average recovery lag: "
      f"{defaults['recovery_lag_months'].mean():.1f} months")

# --- Listing 10.8 ------------------------------------
def expected_loss(pd_, lgd, ead):
    """Expected loss in pounds: sum of PD x LGD x EAD."""
    return float(np.sum(np.asarray(pd_) * np.asarray(lgd)
                        * np.asarray(ead)))

pd_toy = [0.02, 0.05, 0.15]
lgd_toy = [0.00, 0.10, 0.30]
ead_toy = [150_000, 200_000, 250_000]
el_true = expected_loss(pd_toy, lgd_toy, ead_toy)
el_short = np.mean(pd_toy) * np.mean(lgd_toy) * sum(ead_toy)
print(f"Loan by loan: £{el_true:,.0f}")
print(f"Shortcut:     £{el_short:,.0f}")

# --- Listing 10.9 ------------------------------------
from sfrating.pd_model import (fit_pd_model, predict_pd,
                               gini)

model = fit_pd_model(loans, defaults)
loans["pd_5y"] = predict_pd(model, loans)
print(f"Average 5-year PD: {loans['pd_5y'].mean():.2%}")
print(f"Gini: {gini(loans['defaulted'], loans['pd_5y']):.3f}")

# --- Listing 10.10 -----------------------------------
ltv_bands = [0, 60, 70, 80, 90, 100]
merged = defaults[["loan_id", "loss_severity"]].merge(
    loans[["loan_id", "current_ltv"]], on="loan_id")
merged["band"] = pd.cut(merged["current_ltv"], ltv_bands)
lgd_by_band = (merged.groupby("band", observed=True)
               ["loss_severity"].mean())
print(lgd_by_band.round(4).to_string())

loans["band"] = pd.cut(loans["current_ltv"], ltv_bands)
loans["lgd"] = loans["band"].map(lgd_by_band).astype(float)

# --- Listing 10.11 -----------------------------------
monthly_rate = loans["interest_rate"] / 100 / 12
loans["ead"] = (loans["current_balance"]
               * (1 + monthly_rate * 15))
print(f"Pool balance: £{loans['current_balance'].sum():,.0f}")
print(f"Pool EAD:     £{loans['ead'].sum():,.0f}")

# --- Listing 10.12 -----------------------------------
loans["el"] = loans["pd_5y"] * loans["lgd"] * loans["ead"]
el_pool = expected_loss(loans["pd_5y"], loans["lgd"],
                        loans["ead"])
balance = loans["current_balance"].sum()
print(f"Expected loss: £{el_pool:,.0f}"
      f" ({el_pool / balance:.3%} of balance)")
naive = (loans["pd_5y"].mean() * loans["lgd"].mean()
         * loans["ead"].sum())
print(f"Product of averages: £{naive:,.0f}")
print(f"Realised loss: £{defaults['loss'].sum():,.0f}")

# --- Listing 10.13 -----------------------------------
by_band = loans.groupby("band", observed=True).agg(
    balance_m=("current_balance", "sum"),
    el_k=("el", "sum"))
by_band["balance_m"] = by_band["balance_m"] / 1e6
by_band["el_k"] = by_band["el_k"] / 1e3
by_band["el_share"] = by_band["el_k"] / by_band["el_k"].sum()
print(by_band.round(3))

# --- Listing 10.14 -----------------------------------
loss_if_default = loans["lgd"] * loans["ead"]
ul_loans = loss_if_default * np.sqrt(
    loans["pd_5y"] * (1 - loans["pd_5y"]))
ul_indep = np.sqrt((ul_loans ** 2).sum())
print(f"UL if loans were independent: £{ul_indep:,.0f}")
print(f"UL / EL: {ul_indep / el_pool:.2f}")

# --- Listing 10.15 -----------------------------------
print(f"{annualise(0.06, 3):.4%}")
print(f"{1 - 0.99 ** 5:.4%}")

# --- Listing 10.16 -----------------------------------
occ = loans.groupby("occupancy").agg(
    loans=("loan_id", "size"),
    balance_m=("current_balance", "sum"),
    pd_5y=("pd_5y", "mean"),
    observed=("defaulted", "mean"),
    el=("el", "sum"))
occ["balance_m"] = occ["balance_m"] / 1e6
occ["el_pct"] = occ["el"] / (occ["balance_m"] * 1e6)
print(occ.drop(columns="el").round(4).T)

# --- Listing 10.17 -----------------------------------
stressed_ltv = (loans["current_balance"]
                / (loans["property_value"] * 0.85) * 100)
capped = stressed_ltv.clip(upper=99.9)   # top band
band_s = pd.cut(capped, ltv_bands)
lgd_s = band_s.map(lgd_by_band).astype(float)
el_s = expected_loss(loans["pd_5y"], lgd_s, loans["ead"])
print(f"Stressed EL: £{el_s:,.0f}")
print(f"Factor: {el_s / el_pool:.2f}")

# --- Listing 10.18 -----------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
perf["year"] = perf["period"].str[:4]
alive = perf.groupby("year")["loan_id"].nunique()
defs = perf[perf["status"] == "DEF"].groupby("year").size()
yearly = pd.DataFrame({"alive": alive, "defaults": defs})
yearly["rate"] = yearly["defaults"] / yearly["alive"]
print(yearly.round(4))

# --- Listing 10.19 -----------------------------------
# (not executed in the book)
# def annualise(pd_horizon, years: float):
#     """Constant annual default rate giving the same
#     cumulative probability."""
#     return 1 - (1 - np.asarray(pd_horizon)) ** (1 / years)


# def expected_loss(pd, lgd, ead) -> float:
#     """Expected loss in currency: sum of PD x LGD x EAD."""
#     return float(np.sum(np.asarray(pd) * np.asarray(lgd)
#                         * np.asarray(ead)))

# --- Listing 10.20 -----------------------------------
from sfrating import pd_model
print(f"{pd_model.annualise(0.054, 5):.4%}")
el_check = pd_model.expected_loss(loans["pd_5y"], loans["lgd"],
                                  loans["ead"])
print(f"£{el_check:,.0f}")
