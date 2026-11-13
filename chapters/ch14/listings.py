"""
The Pool Loss Distribution and Rating Stresses

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch14/listings.py
"""

# --- Listing 14.1 ------------------------------------
import sys
sys.path.insert(0, "capstone")
import numpy as np
import pandas as pd
from scipy.stats import norm
from sfrating import pd_model, vasicek

loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
model = pd_model.fit_pd_model(loans, defaults)
pd_5y = pd_model.predict_pd(model, loans).to_numpy()
ead = loans["current_balance"].to_numpy()
weights = ead / ead.sum()
lgd = (defaults["loss"].sum()
       / defaults["exposure_at_default"].sum())
pool_pd = (weights * pd_5y).sum()
print(f"balance-weighted 5-year PD: {pool_pd:.2%}")
print(f"LGD:                        {lgd:.2%}")
print(f"expected loss:              {pool_pd * lgd:.3%}")

# --- Listing 14.2 ------------------------------------
def pool_loss_distribution(pd_annual, lgd, ead, rho, years=5,
                           n_sims=20_000, seed=0):
    """Simulated cumulative pool loss over the horizon."""
    pd_h = 1 - (1 - np.asarray(pd_annual, dtype=float)) ** years
    return vasicek.simulate_portfolio_losses(
        pd_h, lgd, ead, rho, n_sims=n_sims, seed=seed)

pd_annual = pd_model.annualise(pd_5y, 5)
losses = pool_loss_distribution(pd_annual, lgd, ead, 0.075,
                                n_sims=10_000, seed=14)
print(f"scenarios: {losses.size}")
print(f"mean loss: {losses.mean():.3%}")

# --- Listing 14.3 ------------------------------------
import matplotlib.pyplot as plt

plt.hist(100 * losses, bins=80)
plt.xlabel("Five-year pool loss (% of pool)")
plt.ylabel("Number of scenarios")
plt.title("Thamesbridge pool loss, rho = 0.075")
plt.savefig("figures/ch14_loss_hist.png")

# --- Listing 14.4 ------------------------------------
def loss_quantiles(losses, levels=(0.5, 0.9, 0.95, 0.99,
                                   0.995, 0.999)):
    losses = np.asarray(losses)
    return pd.Series({q: float(np.quantile(losses, q))
                      for q in levels}, name="loss")

def expected_shortfall(losses, q):
    """Average loss in the worst (1 - q) share of scenarios."""
    losses = np.sort(np.asarray(losses))
    cut = np.quantile(losses, q)
    return float(losses[losses >= cut].mean())

toy = np.array([0.2, 0.3, 0.3, 0.4, 0.4, 0.5, 0.6, 0.8,
                1.1, 2.4])
print(f"mean {toy.mean():.2f}")
print(f"q80  {np.quantile(toy, 0.8):.2f}")
print(f"ES80 {expected_shortfall(toy, 0.8):.2f}")

# --- Listing 14.5 ------------------------------------
print((100 * loss_quantiles(losses)).round(3).to_string())
es_99 = expected_shortfall(losses, 0.99)
print(f"ES at 99%: {100 * es_99:.3f}")

# --- Listing 14.6 ------------------------------------
stresses = pd.read_csv("data/rating_stresses.csv")
short = stresses.rename(columns={
    "target_loss_quantile": "quantile",
    "default_multiple": "multiple",
    "market_value_decline_pct": "mvd_pct"})
print(short[["rating", "quantile", "multiple",
             "mvd_pct"]].to_string(index=False))

# --- Listing 14.7 ------------------------------------
def large_pool_loss(q, pd_, lgd, weights, rho):
    """Pool loss at quantile q for a very large pool."""
    z_bad = -norm.ppf(q)
    p_cond = vasicek.conditional_pd(pd_, rho, z_bad)
    return float((weights * lgd * p_cond).sum())

for q in [0.99, 0.999]:
    sim = np.quantile(losses, q)
    lp = large_pool_loss(q, pd_5y, lgd, weights, 0.075)
    print(f"q={q}: simulated {sim:.3%}, large pool {lp:.3%}")

# --- Listing 14.8 ------------------------------------
import json

with open("data/rmbs_deal.json") as f:
    deal = json.load(f)
reserve = deal["reserve_fund_target_pct"]
below = 1.0
deal_ce = {}
for tranche in deal["tranches"]:
    below -= tranche["share_of_pool"]
    deal_ce[tranche["class"]] = below + reserve
print(pd.Series(deal_ce).map("{:.1%}".format).to_string())

# --- Listing 14.9 ------------------------------------
required = pd.DataFrame(index=stresses["rating"])
quantiles = stresses["target_loss_quantile"]
for rho in [0.075, 0.15]:
    required[f"rho_{rho}"] = [
        large_pool_loss(q, pd_5y, lgd, weights, rho)
        for q in quantiles]
print((100 * required).round(2))

# --- Listing 14.10 -----------------------------------
FSD, COSTS = 0.20, 0.045

def simple_severity(balance, value, mvd_pct):
    proceeds = value * (1 - mvd_pct / 100) * (1 - FSD - COSTS)
    return np.clip(balance - proceeds, 0, None) / balance

print(f"{simple_severity(150_000, 200_000, 45):.1%}")

# --- Listing 14.11 -----------------------------------
value = loans["property_value"].to_numpy()
stress_rows = []
for _, s in stresses.iterrows():
    freq = np.clip(pd_5y * s["default_multiple"], 0, 1)
    mvd = s["market_value_decline_pct"]
    sev = simple_severity(ead, value, mvd)
    wa_freq = (weights * freq).sum()
    loss = (weights * freq * sev).sum()
    stress_rows.append({"rating": s["rating"],
                        "freq": wa_freq,
                        "severity": loss / wa_freq,
                        "loss": loss})
stress_table = pd.DataFrame(stress_rows).set_index("rating")
print((100 * stress_table).round(2))

# --- Listing 14.12 -----------------------------------
base_pd = (weights * pd_5y).sum()
implied = pd.DataFrame(index=stress_table.index)
for rho in [0.075, 0.15]:
    implied[f"rho_{rho}"] = [
        large_pool_loss(q, pd_5y, 1.0, weights, rho) / base_pd
        for q in stresses["target_loss_quantile"]]
implied["table"] = stresses["default_multiple"].to_numpy()
print(implied.round(2))

# --- Listing 14.13 -----------------------------------
combo = []
for _, s in stresses.iterrows():
    mvd = s["market_value_decline_pct"]
    sev = simple_severity(ead, value, mvd)
    sev_def = (weights * pd_5y * sev).sum() / base_pd
    dr = large_pool_loss(s["target_loss_quantile"], pd_5y, 1.0,
                         weights, 0.075)
    combo.append({"rating": s["rating"], "factor_dr": dr,
                  "stressed_sev": sev_def,
                  "loss": dr * sev_def})
combo = pd.DataFrame(combo).set_index("rating")
combo["stress_approach"] = stress_table["loss"]
print((100 * combo).round(2))

# --- Listing 14.14 -----------------------------------
target = {"A": "AAA", "B": "AA", "C": "A", "D": "BBB",
          "E": "BB"}
summary = pd.DataFrame({
    "rating": list(target.values()),
    "deal_ce": [deal_ce[c] for c in target],
    "need_stress": [stress_table.loc[r, "loss"]
                    for r in target.values()],
    "need_factor": [combo.loc[r, "loss"]
                    for r in target.values()]},
    index=list(target))
print((100 * summary.drop(columns="rating")).round(2))

# --- Listing 14.15 -----------------------------------
need = summary[["need_stress", "need_factor"]].max(axis=1)
summary["cushion"] = summary["deal_ce"] - need
print((100 * summary["cushion"]).round(2).to_string())

# --- Listing 14.16 -----------------------------------
x = np.arange(len(summary))
plt.figure()
plt.bar(x, 100 * summary["deal_ce"], width=0.55,
        label="Deal credit enhancement")
plt.scatter(x, 100 * need, color="#B03A2E", zorder=3,
            label="Required at target rating")
labels = [f"{c}\n{r}" for c, r in target.items()]
plt.xticks(x, labels)
plt.ylabel("% of pool")
plt.title("Thamesbridge: protection versus requirement")
plt.legend()
plt.savefig("figures/ch14_ce_vs_required.png")

# --- Listing 14.17 -----------------------------------
ex = np.array([0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.5, 0.7,
               1.0, 3.6])
print(f"{ex.mean():.2f} {np.quantile(ex, 0.9):.2f} "
      f"{expected_shortfall(ex, 0.9):.2f}")

# --- Listing 14.18 -----------------------------------
sev = simple_severity(180_000, 240_000, 32)
print(f"severity {sev:.2%}, loss {0.12 * sev:.2%}")

# --- Listing 14.19 -----------------------------------
lp = large_pool_loss(0.9999, pd_5y, lgd, weights, 0.075)
print(f"large pool: {lp:.3%}")
for seed in [1, 2, 3]:
    run = pool_loss_distribution(pd_annual, lgd, ead, 0.075,
                                 n_sims=10_000, seed=seed)
    print(f"seed {seed}: {np.quantile(run, 0.9999):.3%}")

# --- Listing 14.20 -----------------------------------
for rho in [0.075, 0.15]:
    run = pool_loss_distribution(pd_annual, lgd, ead, rho,
                                 n_sims=10_000, seed=5)
    print(f"rho {rho}: mean {run.mean():.3%}, "
          f"ES99 {expected_shortfall(run, 0.99):.3%}")

# --- Listing 14.21 -----------------------------------
from scipy.optimize import brentq

def gap(rho):
    dr = large_pool_loss(0.9999, pd_5y, 1.0, weights, rho)
    return dr / base_pd - 5.0

rho_aaa = brentq(gap, 0.075, 0.15)
print(f"implied rho for a AAA multiple of 5: {rho_aaa:.4f}")

# --- Listing 14.22 -----------------------------------
# (not executed in the book)
# """Pool loss distribution and loss at a confidence level."""
# import numpy as np
# import pandas as pd

# from .vasicek import simulate_portfolio_losses


# def loss_quantiles(losses, levels=(0.5, 0.9, 0.95, 0.99,
#                                    0.995, 0.999)):
#     losses = np.asarray(losses)
#     return pd.Series({q: float(np.quantile(losses, q))
#                       for q in levels}, name="loss")


# def expected_shortfall(losses, q):
#     """Average loss in the worst (1 - q) share of scenarios."""
#     losses = np.sort(np.asarray(losses))
#     cut = np.quantile(losses, q)
#     return float(losses[losses >= cut].mean())


# def pool_loss_distribution(pd_annual, lgd, ead, rho, years=5,
#                            n_sims=20_000, seed=0):
#     """Simulated cumulative pool loss over the horizon."""
#     pd_h = 1 - (1 - np.asarray(pd_annual, dtype=float)) ** years
#     return simulate_portfolio_losses(pd_h, lgd, ead, rho,
#                                      n_sims=n_sims, seed=seed)

# --- Listing 14.23 -----------------------------------
from sfrating import loss_dist
pkg = loss_dist.pool_loss_distribution(
    pd_annual, lgd, ead, 0.075, n_sims=10_000, seed=14)
print(np.allclose(pkg, losses))
print(f"{loss_dist.expected_shortfall(pkg, 0.99):.4%}")
