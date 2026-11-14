"""
Stochastic Calculus

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch09/listings.py
"""

# --- Listing 09.1 ------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

rng = np.random.default_rng(9)
steps = rng.choice([-1, 1], size=(10_000, 100))
positions = steps.cumsum(axis=1)       # S_1 ... S_100
final = positions[:, -1]
print(f"Mean of S_100:     {final.mean():.3f}")
print(f"Variance of S_100: {final.var():.1f}")

# --- Listing 09.2 ------------------------------------
T, n_steps = 1.0, 250                  # one year, daily steps
dt = T / n_steps
rng = np.random.default_rng(1)
dW = rng.normal(0, np.sqrt(dt), size=(5, n_steps))
W = np.hstack([np.zeros((5, 1)), dW.cumsum(axis=1)])
times = np.linspace(0, T, n_steps + 1)

for path in W:
    plt.plot(times, path, linewidth=0.9)
plt.axhline(0, color="grey", linewidth=0.6)
plt.xlabel("Time (years)")
plt.ylabel("$W_t$")
plt.title("Five paths of Brownian motion")
plt.savefig("figures/ch09_brownian_paths.png")

# --- Listing 09.3 ------------------------------------
rng = np.random.default_rng(2)
dW = rng.normal(0, np.sqrt(dt), size=(20_000, n_steps))
W = dW.cumsum(axis=1)                  # W at dt, 2dt, ..., 1
for t in [0.25, 0.5, 1.0]:
    col = int(round(t / dt)) - 1       # column of time t
    print(f"t = {t:4}: variance of W_t = {W[:, col].var():.3f}")

# --- Listing 09.4 ------------------------------------
def gbm_euler(V0, mu, sigma, T, n_steps, n_paths, seed):
    """GBM paths built step by step: V *= 1 + return."""
    rng = np.random.default_rng(seed)
    dt = T / n_steps
    V = np.full(n_paths, float(V0))
    path = [V.copy()]
    for _ in range(n_steps):
        Z = rng.standard_normal(n_paths)
        V = V * (1 + mu * dt + sigma * np.sqrt(dt) * Z)
        path.append(V.copy())
    return np.array(path).T            # shape (paths, steps+1)

houses = gbm_euler(200_000, 0.03, 0.10, 5, 60, 6, seed=3)
print((houses[:, -1] / 1000).round(1))  # £ thousands, year 5

# --- Listing 09.5 ------------------------------------
months = np.arange(61) / 12
for path in houses:
    plt.plot(months, path / 1000, linewidth=0.9)
plt.xlabel("Years")
plt.ylabel("House value (£ thousands)")
plt.title("Six houses, same start, same drift and volatility")
plt.savefig("figures/ch09_gbm_houses.png")

# --- Listing 09.6 ------------------------------------
rng = np.random.default_rng(4)
for n in [10, 100, 10_000]:
    dW = rng.normal(0, np.sqrt(1 / n), size=(1000, n))
    qv = (dW ** 2).sum(axis=1)         # sum of squared steps
    print(f"{n:6d} steps: mean {qv.mean():.4f},"
          f" sd {qv.std():.4f}")

# --- Listing 09.7 ------------------------------------
mu, sigma = 0.05, 0.40
V = gbm_euler(100, mu, sigma, 1.0, 250, 20_000, seed=5)
log_growth = np.log(V[:, -1] / 100)
print(f"Mean log growth, simulated: {log_growth.mean():.4f}")
print(f"mu - sigma^2/2:             {mu - sigma**2 / 2:.4f}")
print(f"Mean of V_T, simulated:     {V[:, -1].mean():.2f}")
print(f"100 * exp(mu):              {100 * np.exp(mu):.2f}")
below = (V[:, -1] < 100).mean()
print(f"Share ending below 100:     {below:.1%}")

# --- Listing 09.8 ------------------------------------
from scipy.stats import norm

def distance_to_default(V, D, mu, sigma, T):
    drift = (mu - 0.5 * sigma ** 2) * T
    return (np.log(V / D) + drift) / (sigma * np.sqrt(T))

dd = distance_to_default(100, 80, 0.05, 0.25, 1.0)
print(f"DD = {dd:.4f}, PD = {norm.cdf(-dd):.4%}")

# --- Listing 09.9 ------------------------------------
rng = np.random.default_rng(6)
W_T = rng.normal(0, 1.0, size=200_000)      # T = 1
V_T = 100 * np.exp((0.05 - 0.5 * 0.25**2) + 0.25 * W_T)
pd_sim = (V_T < 80).mean()
se = np.sqrt(pd_sim * (1 - pd_sim) / 200_000)
print(f"Simulated PD: {pd_sim:.4%} (standard error {se:.4%})")

# --- Listing 09.10 -----------------------------------
macro = pd.read_csv("data/macro.csv")
log_ret = np.log(macro["hpi"]).diff().dropna()
sigma_index = log_ret.std() * np.sqrt(12)
print(f"Index volatility: {sigma_index:.2%} a year")

# --- Listing 09.11 -----------------------------------
loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
V0 = loans["property_value"]
D = loans["current_balance"]
loans["merton_pd"] = norm.cdf(
    -distance_to_default(V0, D, mu=0.02, sigma=0.10, T=5))
loans["defaulted"] = loans["loan_id"].isin(
    defaults["loan_id"]).astype(int)
print(f"Average Merton PD: {loans['merton_pd'].mean():.2%}")
print(f"Observed 5-year default rate: "
      f"{loans['defaulted'].mean():.2%}")

# --- Listing 09.12 -----------------------------------
bands = [0, 60, 70, 80, 90, 100]
loans["ltv_band"] = pd.cut(loans["current_ltv"], bands)
table = loans.groupby("ltv_band", observed=True).agg(
    loans=("loan_id", "size"),
    merton_pd=("merton_pd", "mean"),
    observed=("defaulted", "mean"))
print(table.round(4))

# --- Listing 09.13 -----------------------------------
from scipy.optimize import brentq

observed = loans["defaulted"].mean()
def gap(sigma):
    dd = distance_to_default(V0, D, 0.02, sigma, 5)
    return norm.cdf(-dd).mean() - observed

sigma_fit = brentq(gap, 0.01, 1.0)
print(f"Implied house volatility: {sigma_fit:.2%}")

# --- Listing 09.14 -----------------------------------
loans["merton_fit"] = norm.cdf(
    -distance_to_default(V0, D, 0.02, sigma_fit, 5))
plot = loans.groupby("ltv_band", observed=True)[
    ["merton_fit", "defaulted"]].mean() * 100
x = np.arange(len(plot))
plt.figure()
plt.bar(x - 0.2, plot["merton_fit"], 0.4, label="Merton PD")
plt.bar(x + 0.2, plot["defaulted"], 0.4, label="Observed")
plt.xticks(x, ["<60", "60-70", "70-80", "80-90", "90+"])
plt.xlabel("Current LTV band (%)")
plt.ylabel("5-year default (%)")
plt.title("Merton ranks loans correctly but is too steep")
plt.legend()
plt.savefig("figures/ch09_merton_vs_observed.png")

# --- Listing 09.15 -----------------------------------
dd = distance_to_default(50, 40, 0.04, 0.20, 2.0)
print(f"DD = {dd:.4f}, PD = {norm.cdf(-dd):.4%}")

# --- Listing 09.16 -----------------------------------
rng = np.random.default_rng(94)
dW = rng.normal(0, np.sqrt(2 / 200), size=(20_000, 200))
W = dW.cumsum(axis=1)
W1, W2 = W[:, 99], W[:, -1]
corr = np.corrcoef(W1, W2 - W1)[0, 1]
print(f"corr(W1, W2 - W1) = {corr:.4f}")
print(f"cov(W1, W2)       = {np.cov(W1, W2)[0, 1]:.4f}")

# --- Listing 09.17 -----------------------------------
mu, sigma, n_steps = 0.05, 0.25, 250
dt = 1 / n_steps
rng = np.random.default_rng(95)
dW = rng.normal(0, np.sqrt(dt), size=(20_000, n_steps))
log_V = np.log(100) + np.cumsum(
    (mu - 0.5 * sigma**2) * dt + sigma * dW, axis=1)
V = np.exp(log_V)
print(f"Below D at T:       {(V[:, -1] < 80).mean():.2%}")
print(f"Touch D during year: {(V.min(axis=1) < 80).mean():.2%}")

# --- Listing 09.18 -----------------------------------
target = 0.02
dd_needed = -norm.ppf(target)
ln_D = np.log(100) + (0.05 - 0.5 * 0.30**2) - dd_needed * 0.30
D_algebra = np.exp(ln_D)
print(f"DD needed: {dd_needed:.4f}, D = {D_algebra:.4f}")

D_root = brentq(lambda D: norm.cdf(
    -distance_to_default(100, D, 0.05, 0.30, 1.0)) - target,
    1, 100)
print(f"brentq:    D = {D_root:.4f}")

# --- Listing 09.19 -----------------------------------
# (not executed in the book)
# def distance_to_default(V, D, mu, sigma, T):
#     """Standard deviations between expected log assets
#     and log debt."""
#     return ((np.log(V / D) + (mu - 0.5 * sigma ** 2) * T)
#             / (sigma * np.sqrt(T)))

# def merton_pd(V, D, mu, sigma, T):
#     """Probability that assets end below D at time T."""
#     return float(norm.cdf(
#         -distance_to_default(V, D, mu, sigma, T)))

# --- Listing 09.20 -----------------------------------
from sfrating import merton
print(f"{merton.merton_pd(100, 80, 0.05, 0.25, 1.0):.4%}")
paths = merton.simulate_asset_paths(100, 0.05, 0.25, 1.0,
                                    250, 20_000, seed=0)
print(paths.shape, f"{(paths[:, -1] < 80).mean():.2%}")
