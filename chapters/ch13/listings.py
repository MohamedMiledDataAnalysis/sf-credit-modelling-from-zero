"""
Factor Models

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch13/listings.py
"""

# --- Listing 13.1 ------------------------------------
import numpy as np
import pandas as pd
from scipy.stats import norm

rng = np.random.default_rng(13)
n_years = 1_000_000
bad = rng.random(n_years) < 0.5
pd_year = np.where(bad, 0.05, 0.01)
loan1 = rng.random(n_years) < pd_year
loan2 = rng.random(n_years) < pd_year
print(f"P(loan 1 defaults): {loan1.mean():.4f}")
print(f"P(both default):    {(loan1 & loan2).mean():.5f}")

# --- Listing 13.2 ------------------------------------
pd_loan, rho = 0.02, 0.15
threshold = norm.ppf(pd_loan)
z, eps = -1.5, -1.8
asset = np.sqrt(rho) * z + np.sqrt(1 - rho) * eps
print(f"threshold {threshold:.3f}, asset value {asset:.3f}")
print("defaults:", asset < threshold)

# --- Listing 13.3 ------------------------------------
def conditional_pd(pd_, rho, z):
    """Default probability given the systematic factor Z = z."""
    top = norm.ppf(pd_) - np.sqrt(rho) * np.asarray(z)
    return norm.cdf(top / np.sqrt(1 - rho))

for z in [-2, 0, 2]:
    print(f"z = {z:+d}: {conditional_pd(0.02, 0.15, z):.2%}")

# --- Listing 13.4 ------------------------------------
import matplotlib.pyplot as plt

z_grid = np.linspace(-3.5, 3.5, 200)
for r in [0.05, 0.15, 0.30]:
    plt.plot(z_grid, 100 * conditional_pd(0.02, r, z_grid),
             label=f"rho = {r}")
plt.xlabel("Systematic factor z (low = bad year)")
plt.ylabel("Conditional PD (%)")
plt.title("A PD of 2% on average, very different by year")
plt.legend()
plt.savefig("figures/ch13_conditional_pd.png")

# --- Listing 13.5 ------------------------------------
def vasicek_cdf(x, pd_, rho):
    """P(pool default rate <= x) for a large pool."""
    top = np.sqrt(1 - rho) * norm.ppf(x) - norm.ppf(pd_)
    return norm.cdf(top / np.sqrt(rho))

def vasicek_quantile(q, pd_, rho):
    """Pool default rate not exceeded with probability q."""
    top = norm.ppf(pd_) + np.sqrt(rho) * norm.ppf(q)
    return float(norm.cdf(top / np.sqrt(1 - rho)))

dr_999 = vasicek_quantile(0.999, 0.02, 0.15)
print(f"99.9% default rate: {dr_999:.2%}")
check = vasicek_cdf(dr_999, 0.02, 0.15)
print(f"check, cdf at it:   {check:.4f}")

# --- Listing 13.6 ------------------------------------
def estimate_rho_moments(default_rates):
    """Method-of-moments estimate of (pd, rho)."""
    dr = np.clip(np.asarray(default_rates, dtype=float),
                 1e-6, 1 - 1e-6)
    y = norm.ppf(dr)
    v = y.var(ddof=1)
    rho = v / (1 + v)
    pd_ = norm.cdf(y.mean() * np.sqrt(1 - rho))
    return float(pd_), float(rho)

toy_rates = norm.cdf([-2.4, -2.0, -1.8, -2.2])
pd_hat, rho_hat = estimate_rho_moments(toy_rates)
print(f"pd {pd_hat:.4f}, rho {rho_hat:.4f}")

# --- Listing 13.7 ------------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
months = pd.PeriodIndex(perf["period"], freq="M")
perf["quarter"] = months.asfreq("Q").astype(str)
alive = perf.groupby("quarter")["loan_id"].nunique()
new_def = (perf["status"] == "DEF").groupby(
    perf["quarter"]).sum()
quarterly = pd.DataFrame({"alive": alive, "defaults": new_def})
quarterly["dr"] = quarterly["defaults"] / quarterly["alive"]
print(quarterly.head(6).round(5))

# --- Listing 13.8 ------------------------------------
dr_q = quarterly["dr"].iloc[1:]
pd_q, rho_q = estimate_rho_moments(dr_q)
print(f"quarters used: {len(dr_q)}")
print(f"quarterly PD:  {pd_q:.4%}")
print(f"rho estimate:  {rho_q:.3f}")
with_q1 = estimate_rho_moments(quarterly["dr"])[1]
print(f"rho if 2020Q1 is kept: {with_q1:.3f}")

# --- Listing 13.9 ------------------------------------
from scipy.optimize import minimize

def vasicek_nll(params, rates):
    p, r = params
    if not (0 < p < 1 and 0 < r < 1):
        return 1e10                 # outside the allowed range
    y = norm.ppf(rates)
    log_f = (0.5 * np.log((1 - r) / r) + 0.5 * y**2
             - (np.sqrt(1 - r) * y - norm.ppf(p))**2 / (2 * r))
    return -log_f.sum()

fit = minimize(vasicek_nll, x0=[0.004, 0.1], args=(dr_q,),
               method="Nelder-Mead")
print(f"MLE: pd {fit.x[0]:.4%}, rho {fit.x[1]:.3f}")

# --- Listing 13.10 -----------------------------------
import sys
sys.path.insert(0, "capstone")
from sfrating import pd_model

loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
model = pd_model.fit_pd_model(loans, defaults)
pd_5y = pd_model.predict_pd(model, loans).to_numpy()
balance = loans["current_balance"].to_numpy()
print(f"average 5-year PD: {pd_5y.mean():.2%}")
print(f"PD range: {pd_5y.min():.2%} to {pd_5y.max():.2%}")

# --- Listing 13.11 -----------------------------------
def simulate_default_rates(pd_, weights, rho, n_sims, seed):
    """Balance share defaulting in each simulated scenario."""
    rng = np.random.default_rng(seed)
    threshold = norm.ppf(pd_)
    out = np.empty(n_sims)
    for k in range(n_sims):
        z = rng.standard_normal()
        eps = rng.standard_normal(pd_.size)
        asset = np.sqrt(rho) * z + np.sqrt(1 - rho) * eps
        out[k] = weights[asset < threshold].sum()
    return out

weights = balance / balance.sum()
sim_dr = simulate_default_rates(pd_5y, weights, 0.15,
                                n_sims=4_000, seed=1)
print(f"mean:  {sim_dr.mean():.2%}")
print(f"99.9%: {np.quantile(sim_dr, 0.999):.2%}")

# --- Listing 13.12 -----------------------------------
pd_avg = np.average(pd_5y, weights=balance)
formula = vasicek_quantile(0.999, pd_avg, 0.15)
print(f"formula, average PD: {formula:.2%}")

# --- Listing 13.13 -----------------------------------
rows = []
for r in [0.01, 0.075, 0.15, 0.30]:
    rows.append({"rho": r,
                 "median": vasicek_quantile(0.5, pd_avg, r),
                 "q99": vasicek_quantile(0.99, pd_avg, r),
                 "q999": vasicek_quantile(0.999, pd_avg, r)})
print((pd.DataFrame(rows).set_index("rho") * 100).round(2))

# --- Listing 13.14 -----------------------------------
x_grid = np.linspace(0.001, 0.35, 400)
for r in [0.01, 0.075, 0.15, 0.30]:
    cdf = vasicek_cdf(x_grid, pd_avg, r)
    density = np.gradient(cdf, x_grid)
    plt.plot(100 * x_grid, density / 100, label=f"rho = {r}")
plt.xlabel("Five-year pool default rate (%)")
plt.ylabel("Density (per %)")
plt.title("Same average, different tails")
plt.legend()
plt.savefig("figures/ch13_rho_tails.png")

# --- Listing 13.15 -----------------------------------
macro = pd.read_csv("data/macro.csv")
macro_m = pd.PeriodIndex(macro["period"], freq="M")
macro["quarter"] = macro_m.asfreq("Q").astype(str)
factor_q = macro.groupby("quarter")["credit_factor"].mean()
lagged = factor_q.shift(1).loc[dr_q.index]
probit = pd.Series(norm.ppf(dr_q), index=dr_q.index)
corr = np.corrcoef(lagged, probit)[0, 1]
print(f"correlation, probit DR vs lagged factor: {corr:.2f}")

# --- Listing 13.16 -----------------------------------
fig, ax = plt.subplots()
ax.scatter(lagged, probit)
ax.set_xlabel("Credit factor, previous quarter (high = bad)")
ax.set_ylabel("Probit of quarterly default rate")
ax.set_title("Defaults follow the systematic factor")
plt.savefig("figures/ch13_factor_link.png")

# --- Listing 13.17 -----------------------------------
labels = list(dr_q.index)
plt.figure()
plt.plot(range(len(dr_q)), 100 * dr_q.to_numpy(), marker="o")
plt.xticks(range(0, len(dr_q), 4), labels[::4])
plt.ylabel("Quarterly default rate (%)")
plt.title("Thamesbridge: one downturn in 19 quarters")
plt.savefig("figures/ch13_quarterly_dr.png")

# --- Listing 13.18 -----------------------------------
rng = np.random.default_rng(2024)
n_alive = quarterly["alive"].iloc[1:].to_numpy()
estimates = []
for rep in range(1_000):
    z = rng.standard_normal(len(n_alive))
    p_cond = conditional_pd(pd_q, rho_q, z)
    n_def = rng.binomial(n_alive, p_cond)
    estimates.append(estimate_rho_moments(n_def / n_alive)[1])
low, high = np.quantile(estimates, [0.05, 0.95])
print(f"90% of estimates between {low:.3f} and {high:.3f}")

# --- Listing 13.19 -----------------------------------
from sfrating import vasicek

for r in [round(rho_q, 3), 0.15]:
    sims = vasicek.simulate_portfolio_losses(
        pd_5y, 1.0, balance, r, n_sims=4_000, seed=7)
    print(f"rho {r:.3f}: mean {sims.mean():.2%}, "
          f"99% {np.quantile(sims, 0.99):.2%}")

# --- Listing 13.20 -----------------------------------
print(f"{norm.cdf(-1.438):.4f}")
print(f"{vasicek_quantile(0.99, 0.01, 0.20):.4f}")

# --- Listing 13.21 -----------------------------------
perf["year"] = perf["period"].str[:4]
alive_y = perf.groupby("year")["loan_id"].nunique()
def_y = (perf["status"] == "DEF").groupby(perf["year"]).sum()
dr_y = def_y / alive_y
print((100 * dr_y).round(2).to_string())
pd_y, rho_y = estimate_rho_moments(dr_y)
print(f"annual rho estimate: {rho_y:.3f}")

# --- Listing 13.22 -----------------------------------
for r in [0.075, 0.15]:
    p_exceed = 1 - vasicek_cdf(0.15, pd_avg, r)
    print(f"rho {r}: P(DR > 15%) = {p_exceed:.3%}")

# --- Listing 13.23 -----------------------------------
rng = np.random.default_rng(6)
z = rng.standard_normal(200_000)
dr_sim = conditional_pd(0.03, 0.12, z)
v = norm.ppf(dr_sim).var()
print(f"simulated variance: {v:.4f}")
print(f"theory rho/(1-rho): {0.12 / 0.88:.4f}")
print(f"rho recovered:      {v / (1 + v):.4f}")

# --- Listing 13.24 -----------------------------------
# (not executed in the book)
# def simulate_portfolio_losses(pd, lgd, ead, rho, n_sims=10_000,
#                               seed=0, batch=1_000):
#     rng = np.random.default_rng(seed)
#     pd = np.asarray(pd, dtype=float)
#     lgd = np.broadcast_to(np.asarray(lgd, float), pd.shape)
#     ead = np.broadcast_to(np.asarray(ead, float), pd.shape)
#     threshold = norm.ppf(pd)
#     total = ead.sum()
#     out = np.empty(n_sims)
#     done = 0
#     while done < n_sims:
#         m = min(batch, n_sims - done)
#         z = rng.standard_normal((m, 1))
#         e = rng.standard_normal((m, pd.size))
#         x = np.sqrt(rho) * z + np.sqrt(1 - rho) * e
#         out[done:done + m] = (
#             (x < threshold) * (lgd * ead)).sum(axis=1) / total
#         done += m
#     return out

# --- Listing 13.25 -----------------------------------
print(round(vasicek.vasicek_quantile(0.999, 0.02, 0.15), 4))
print(round(vasicek.estimate_rho_moments(dr_q)[1], 3))
