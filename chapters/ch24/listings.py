"""
Interview Questions and Final Exam

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch24/listings.py
"""

# --- Listing 24.1 ------------------------------------
import numpy as np
import pandas as pd
from scipy.stats import binom, norm
from sfrating import (abs_auto, cashflow, clo, cmbs, data,
                      numerics, pd_model, rating, rmbs,
                      survival, vasicek)

print("Q1 ", round(1 - 0.98 * 0.97, 4))
print("Q2 ", round(0.024 / (0.024 + 0.048), 4))
print("Q3 ", round(binom.pmf(0, 10, 0.1), 4),
      round(1 - binom.cdf(1, 10, 0.1), 4))
print("Q5 ", round(float(pd_model.annualise(0.10, 5)), 4))
r = 0.03 / 12
print("Q6 ", round(150_000 * r / (1 - (1 + r) ** -300), 2))
km = survival.kaplan_meier([2, 3, 4, 4, 6, 8],
                           [1, 0, 1, 1, 0, 0])
print("Q9 ", km["survival"].round(4).tolist())
print("Q11", round(float(rmbs.loss_severity(
    180_000, 240_000, 4.0, 30)), 4))
print("Q13", round(vasicek.vasicek_quantile(0.999, 0.02,
                                            0.15), 4))

# --- Listing 24.2 ------------------------------------
loans = data.load_loans()
w = loans["current_balance"] / loans["current_balance"].sum()
wa_ltv = (w * loans["current_ltv"]).sum()
high = w[loans["current_ltv"] > 80].sum()
print(f"WA current LTV {wa_ltv:.2f}%, above 80%: {high:.2%}")

# --- Listing 24.3 ------------------------------------
defaults = data.load_defaults()
flag = pd_model.default_flag(loans, defaults)
se = loans["employment"] == "Self-employed"
p1, p0 = flag[se].mean(), flag[~se].mean()
std_err = np.sqrt(p1 * (1 - p1) / se.sum()
                  + p0 * (1 - p0) / (~se).sum())
diff = p1 - p0
low, high = diff - 1.96 * std_err, diff + 1.96 * std_err
print(f"self-employed {p1:.2%}, employed {p0:.2%}")
print(f"difference {diff:.2%}, 95% CI [{low:.2%}, {high:.2%}]")

# --- Listing 24.4 ------------------------------------
perf = data.load_performance()
y24 = perf[perf["period"].str.startswith("2024")]
by_month = y24.groupby("period")[
    ["prepayment", "opening_balance", "principal_paid"]].sum()
smm = by_month["prepayment"] / (by_month["opening_balance"]
                                - by_month["principal_paid"])
cpr = 1 - (1 - smm.mean()) ** 12
print(f"average SMM {smm.mean():.4%}, CPR {cpr:.2%}")

# --- Listing 24.5 ------------------------------------
gini_score = pd_model.gini(flag, -loans["credit_score"])
print(f"Gini of credit score alone: {gini_score:.3f}")

# --- Listing 24.6 ------------------------------------
area = numerics.simpson(norm.pdf, -1.96, 1.96, n=100)
print(f"{area:.6f}")

# --- Listing 24.7 ------------------------------------
rates = vasicek.simulate_portfolio_losses(
    [0.02] * 100, 1.0, 1.0, 0.20, n_sims=20_000, seed=24)
q99 = np.quantile(rates, 0.99)
print(f"mean {rates.mean():.2%}, 99th percentile {q99:.2%}")
large = vasicek.vasicek_quantile(0.99, 0.02, 0.2)
print(f"large pool: {large:.2%}")

# --- Listing 24.8 ------------------------------------
cm = data.load_cmbs()
cap = cm["noi"] / cm["property_value"] + 0.01
refi = cmbs.refinance_test(cm["loan_balance"], cm["noi"], cap)
fail = ~refi["refinances"]
bal_share = cm.loc[fail, "loan_balance"].sum() / cm[
    "loan_balance"].sum()
print(f"fail: {fail.mean():.2%} of loans, "
      f"{bal_share:.2%} of balance")

# --- Listing 24.9 ------------------------------------
auto = data.load_auto()
for vehicle in ["New", "Used"]:
    group = auto[auto["vehicle"] == vehicle]
    curve = abs_auto.cumulative_default_curve(group, 60)
    cd = curve.set_index("month")["cumulative_default"]
    rec = group.loc[group["default"] == 1,
                    "recovery_rate_if_default"].mean()
    loss = abs_auto.base_case_loss(cd[60], rec)
    print(f"{vehicle}: 36m {cd[36]:.2%}, 60m {cd[60]:.2%}, "
          f"recovery {rec:.2%}, loss {loss:.2%}")

# --- Listing 24.10 -----------------------------------
pf = data.load_clo()
p1 = clo.weighted_average(pf["one_year_pd"], pf["par"])
D = int(round(clo.diversity_score(pf["par"], pf["industry"])))
rec = clo.weighted_average(pf["recovery_assumption"], pf["par"])
p5 = 1 - (1 - p1) ** 5
dist = clo.bet_loss_distribution(D, p5, 1 - rec)
el = clo.tranche_expected_loss(dist, 0.08, 0.12)
print(f"WA PD {p1:.2%}, D {D}, recovery {rec:.2%}")
print(f"5-year PD {p5:.2%}, tranche 8-12% EL {el:.2%}")

# --- Listing 24.11 -----------------------------------
levels = rmbs.rating_level_losses(
    loans, pd_model.predict_pd(
        pd_model.fit_pd_model(loans, defaults), loans),
    data.load_rating_stresses())
bbb = levels.set_index("rating").loc["BBB"]
deal = data.load_deal()

def class_e_loses(spread):
    worst = 0.0
    for cpr in (0.05, 0.20):
        pool = cashflow.project_pool(
            deal["pool_balance"], 285,
            cum_default=bbb["default_frequency"],
            severity=bbb["loss_severity"], cpr=cpr)
        res = cashflow.run_waterfall(pool, deal, sonia_pct=3.0,
                                     pool_spread_pct=spread)
        worst = max(worst, res["tranche_loss"]["E"])
    return 1.0 if worst > 1e-6 else -1.0

s_star = numerics.bisection(class_e_loses, 1.00, 1.60,
                            tol=0.001)
print(f"break-even pool spread: {s_star:.2f}%")
