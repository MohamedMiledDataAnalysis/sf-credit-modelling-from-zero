"""
Monte Carlo Simulation

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch08/listings.py
"""

# --- Listing 08.1 ------------------------------------
import numpy as np
import pandas as pd
from scipy.stats import norm, binom

rng = np.random.default_rng(8)
for n_darts in [10, 1_000, 100_000, 10_000_000]:
    x = rng.random(n_darts)
    y = rng.random(n_darts)
    inside = (x ** 2 + y ** 2 <= 1).mean()
    print(f"{n_darts:>10,} darts: pi = {4 * inside:.5f}")

# --- Listing 08.2 ------------------------------------
exposure, median_value, sigma = 180_000, 200_000, 0.25

def loan_loss(z):
    sale_value = median_value * np.exp(sigma * z)
    return np.maximum(exposure - sale_value, 0)

rng = np.random.default_rng(8)
z = rng.standard_normal(100_000)
losses = loan_loss(z)
print(f"Monte Carlo EL: {losses.mean():,.2f}")
print(f"Share with a loss: {(losses > 0).mean():.4f}")

# --- Listing 08.3 ------------------------------------
for n_sims in [1_000, 10_000, 100_000]:
    sample = losses[:n_sims]
    se = sample.std(ddof=1) / np.sqrt(n_sims)
    print(f"N = {n_sims:>7,}: EL = {sample.mean():8,.0f}"
          f"  SE = {se:6,.0f}  95% CI +/- {1.96 * se:6,.0f}")

# --- Listing 08.4 ------------------------------------
import matplotlib.pyplot as plt

n_axis = np.arange(1, 20_001)
running_mean = np.cumsum(losses[:20_000]) / n_axis
s_full = losses.std(ddof=1)
band = 1.96 * s_full / np.sqrt(n_axis)
plt.plot(n_axis, running_mean, label="Running Monte Carlo mean")
plt.fill_between(n_axis, 8821.69 - band, 8821.69 + band,
                 color="#C9A227", alpha=0.3,
                 label="True EL +/- 1.96 SE")
plt.axhline(8821.69, color="#B03A2E", linewidth=0.8)
plt.ylim(6000, 12000)
plt.xscale("log")
plt.xlabel("Number of simulations N (log scale)")
plt.ylabel("Expected loss (£)")
plt.title("The estimate settles at the rate 1/sqrt(N)")
plt.legend(loc="upper right")
plt.savefig("figures/ch08_convergence.png")

# --- Listing 08.5 ------------------------------------
n_loans, pd_loan, n_sims = 100, 0.02, 100_000
rng = np.random.default_rng(42)
u = rng.random((n_sims, n_loans))
defaults_per_sim = (u < pd_loan).sum(axis=1)

ks = np.arange(6)
simulated = [(defaults_per_sim == k).mean() for k in ks]
formula = binom.pmf(ks, n_loans, pd_loan)
table = pd.DataFrame({"simulated": simulated,
                      "binomial": formula}, index=ks)
print(table.round(4))
print(f"Mean defaults: {defaults_per_sim.mean():.4f}")

# --- Listing 08.6 ------------------------------------
def simulate_defaults(n_loans, pd_loan, rho, n_sims, seed):
    rng = np.random.default_rng(seed)
    threshold = norm.ppf(pd_loan)
    z = rng.standard_normal((n_sims, 1))       # shared
    eps = rng.standard_normal((n_sims, n_loans))  # own
    x = np.sqrt(rho) * z + np.sqrt(1 - rho) * eps
    return (x < threshold).sum(axis=1)

indep = simulate_defaults(100, 0.02, 0.0, 100_000, seed=1)
corr = simulate_defaults(100, 0.02, 0.2, 100_000, seed=1)
for name, k in [("rho = 0  ", indep), ("rho = 0.2", corr)]:
    print(f"{name}: mean {k.mean():.3f}, sd {k.std():.3f}, "
          f"P(K >= 8) = {(k >= 8).mean():.4f}")

# --- Listing 08.7 ------------------------------------
bins = np.arange(0, 16)
share_i = [(indep == k).mean() for k in bins]
share_c = [(corr == k).mean() for k in bins]
plt.figure()
plt.bar(bins - 0.2, share_i, width=0.4, label="Independent")
plt.bar(bins + 0.2, share_c, width=0.4, label="rho = 0.2")
plt.xlabel("Number of defaults among 100 loans")
plt.ylabel("Probability")
plt.title("Same average, fatter tail")
plt.legend()
plt.savefig("figures/ch08_correlation.png")

# --- Listing 08.8 ------------------------------------
rng = np.random.default_rng(8)
z_all = rng.standard_normal(100_000)
plain = loan_loss(z_all)

z_half = z_all[:50_000]
pairs = 0.5 * (loan_loss(z_half) + loan_loss(-z_half))

se_plain = plain.std(ddof=1) / np.sqrt(plain.size)
se_anti = pairs.std(ddof=1) / np.sqrt(pairs.size)
print(f"Plain:      {plain.mean():,.0f}  SE {se_plain:.1f}")
print(f"Antithetic: {pairs.mean():,.0f}  SE {se_anti:.1f}")
print(f"Variance ratio: {(se_plain / se_anti) ** 2:.2f}")

# --- Listing 08.9 ------------------------------------
plain_v = median_value * np.exp(sigma * z_all)
pairs_v = 0.5 * median_value * (np.exp(sigma * z_half)
                                + np.exp(-sigma * z_half))
ratio = (plain_v.var(ddof=1) / plain_v.size) / (
    pairs_v.var(ddof=1) / pairs_v.size)
print(f"Variance ratio for the sale value: {ratio:.1f}")

# --- Listing 08.10 -----------------------------------
a = np.random.default_rng(2026).standard_normal(3)
b = np.random.default_rng(2026).standard_normal(3)
c = np.random.default_rng(2027).standard_normal(3)
print(a.round(4))
print(b.round(4))
print(c.round(4))

# --- Listing 08.11 -----------------------------------
child_seeds = np.random.SeedSequence(2026).spawn(2)
rng_default = np.random.default_rng(child_seeds[0])
rng_prepay = np.random.default_rng(child_seeds[1])
print(rng_default.random(2).round(4),
      rng_prepay.random(2).round(4))

# --- Listing 08.12 -----------------------------------
toy_losses = np.array([0.2, 0.3, 0.3, 0.4, 0.5, 0.5, 0.6,
                       0.8, 1.1, 2.0])

def loss_quantiles(losses, levels=(0.5, 0.9, 0.95, 0.99)):
    losses = np.asarray(losses)
    return pd.Series({q: float(np.quantile(losses, q))
                      for q in levels}, name="loss")

def expected_shortfall(losses, q):
    losses = np.asarray(losses)
    cut = np.quantile(losses, q)
    return float(losses[losses >= cut].mean())

print(f"mean {toy_losses.mean():.2f}")
print(f"q90  {np.quantile(toy_losses, 0.9):.2f}")
print(f"ES90 {expected_shortfall(toy_losses, 0.9):.2f}")

# --- Listing 08.13 -----------------------------------
# (not executed in the book)
# for sim in range(10_000):
#     rng = np.random.default_rng(42)
#     z = rng.standard_normal()

# --- Listing 08.14 -----------------------------------
from sfrating import pd_model

loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
model = pd_model.fit_pd_model(loans, defaults)
pd_5y = pd_model.predict_pd(model, loans).to_numpy()
severity = (defaults["loss"].sum()
            / defaults["exposure_at_default"].sum())
ead = loans["current_balance"].to_numpy()
el_formula = np.sum(pd_5y * severity * ead) / ead.sum()
print(f"Mean PD {pd_5y.mean():.4f}, severity {severity:.4f}")
print(f"Expected loss (formula): {el_formula:.4%} of the pool")

# --- Listing 08.15 -----------------------------------
def simulate_pool_losses(pd_, lgd, ead, rho, n_sims, seed,
                         batch=500):
    # pd_ (array of PDs), not pd, which is the name of pandas
    rng = np.random.default_rng(seed)
    threshold = norm.ppf(pd_)
    loss_if_default = lgd * ead
    out = []
    for start in range(0, n_sims, batch):
        m = min(batch, n_sims - start)
        z = rng.standard_normal((m, 1))
        eps = rng.standard_normal((m, pd_.size))
        x = np.sqrt(rho) * z + np.sqrt(1 - rho) * eps
        out.append((x < threshold) @ loss_if_default)
    return np.concatenate(out) / ead.sum()

# --- Listing 08.16 -----------------------------------
results = {}
for rho in [0.0, 0.10]:
    results[rho] = simulate_pool_losses(pd_5y, severity, ead,
                                        rho, 5_000, seed=2026)
summary = pd.DataFrame({
    rho: {"mean": r.mean(),
          "SE of mean": r.std(ddof=1) / np.sqrt(r.size),
          "q50": np.quantile(r, 0.50),
          "q99": np.quantile(r, 0.99),
          "ES99": expected_shortfall(r, 0.99)}
    for rho, r in results.items()})
summary.columns = ["rho 0", "rho 0.10"]
print((100 * summary).round(4))

# --- Listing 08.17 -----------------------------------
plt.figure()
plt.hist(100 * results[0.10], bins=80, density=True,
         alpha=0.8, label="rho = 0.10")
plt.hist(100 * results[0.0], bins=20, density=True,
         alpha=0.8, label="rho = 0")
q99 = 100 * np.quantile(results[0.10], 0.99)
plt.axvline(q99, color="#B03A2E", linestyle="--",
            label="99% quantile, rho = 0.10")
plt.xlim(0, 2.6)
plt.xlabel("Five-year pool loss (% of balance)")
plt.ylabel("Density")
plt.title("Thamesbridge pool loss distribution")
plt.legend(loc="upper right")
plt.savefig("figures/ch08_pool_losses.png")

# --- Listing 08.18 -----------------------------------
realised = defaults["loss"].sum() / ead.sum()
share_below = (results[0.10] <= realised).mean()
print(f"Realised loss: {realised:.4%}")
print(f"Correlated scenarios below it: {share_below:.1%}")

# --- Listing 08.19 -----------------------------------
k50 = simulate_defaults(50, 0.03, 0.0, 200_000, seed=3)
print(f"formula {0.97 ** 50:.4f}, "
      f"simulated {(k50 == 0).mean():.4f}")

# --- Listing 08.20 -----------------------------------
ex3 = [4, 1, 7, 2, 3, 9, 2, 5, 1, 6]
print(np.mean(ex3), np.quantile(ex3, 0.8),
      expected_shortfall(ex3, 0.8))

# --- Listing 08.21 -----------------------------------
io = (loans["repayment_type"] == "Interest-only").to_numpy()
pd_io = pd_5y[io]
rng = np.random.default_rng(84)
sim_io = np.zeros(20_000, dtype=int)
for start in range(0, 20_000, 2_000):
    u = rng.random((2_000, pd_io.size))
    sim_io[start:start + 2_000] = (u < pd_io).sum(axis=1)
print(f"Expected defaults: {pd_io.sum():.1f}")
print(f"Simulated 5%-95%: {np.quantile(sim_io, [0.05, 0.95])}")
print(f"P(K >= 177): {(sim_io >= 177).mean():.3f}")

# --- Listing 08.22 -----------------------------------
rows = {}
for rho in [0.0, 0.05, 0.10, 0.20]:
    r = simulate_pool_losses(pd_5y, severity, ead, rho,
                             2_000, seed=85)
    rows[rho] = {"mean %": 100 * r.mean(),
                 "q99 %": 100 * np.quantile(r, 0.99)}
print(pd.DataFrame(rows).T.round(3))

# --- Listing 08.23 -----------------------------------
r10 = results[0.10]
p_hat = (r10 > 0.015).mean()
se_p = np.sqrt(p_hat * (1 - p_hat) / r10.size)
print(f"P(loss > 1.5%) = {p_hat:.4f}  SE {se_p:.4f}")

# --- Listing 08.24 -----------------------------------
# (not executed in the book)
# def expected_shortfall(losses, q):
#     """Average loss in the worst (1 - q) share of scenarios."""
#     losses = np.asarray(losses)
#     cut = np.quantile(losses, q)
#     return float(losses[losses >= cut].mean())

# --- Listing 08.25 -----------------------------------
r0 = results[0.0]
gap = abs(r0.mean() - el_formula)
se0 = r0.std(ddof=1) / np.sqrt(r0.size)
print(f"gap {gap:.2e}, 2 SE {2 * se0:.2e}, ok: {gap < 2 * se0}")
