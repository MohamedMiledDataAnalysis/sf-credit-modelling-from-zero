"""
Probability from Zero

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch05/listings.py
"""

# --- Listing 05.1 ------------------------------------
import numpy as np
import pandas as pd

loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
tape = loans.merge(defaults[["loan_id", "default_period"]],
                   on="loan_id", how="left")
tape["D"] = tape["default_period"].notna()
print(len(tape), tape["D"].sum(), tape["D"].mean())

# --- Listing 05.2 ------------------------------------
import matplotlib.pyplot as plt

rng = np.random.default_rng(5)
picks = rng.integers(0, len(tape), size=20000)
is_default = tape["D"].to_numpy()[picks]
running = np.cumsum(is_default) / np.arange(1, 20001)
for n in [10, 100, 1000, 20000]:
    print(f"after {n:>6} picks: {running[n - 1]:.4f}")

plt.plot(np.arange(1, 20001), running)
plt.axhline(0.054, color="#C9A227", linestyle="--")
plt.xscale("log")
plt.xlabel("Number of random picks (log scale)")
plt.ylabel("Share of defaulted picks")
plt.title("The share settles down to the probability")
plt.savefig("figures/ch05_long_run.png")

# --- Listing 05.3 ------------------------------------
I = tape["repayment_type"] == "Interest-only"
B = tape["occupancy"] == "Buy-to-let"
p_I, p_B, p_IB = I.mean(), B.mean(), (I & B).mean()
print(p_I, p_B, p_IB)
print("Rule:  ", round(p_I + p_B - p_IB, 4))
print("Direct:", (I | B).mean())

# --- Listing 05.4 ------------------------------------
rng = np.random.default_rng(11)
loan1 = rng.uniform(size=100000) < 0.05
loan2 = rng.uniform(size=100000) < 0.05
print("Both default:", (loan1 & loan2).mean())
print("At least one:", (loan1 | loan2).mean())

# --- Listing 05.5 ------------------------------------
print("If independent:", round(p_I * p_B, 4))
print("Observed:      ", round(p_IB, 4))

# --- Listing 05.6 ------------------------------------
print(round(tape.loc[I, "D"].mean(), 4))
print(tape.groupby("repayment_type")["D"].mean().round(4))

# --- Listing 05.7 ------------------------------------
p_D = tape["D"].mean()
p_I_given_D = tape.loc[tape["D"], "repayment_type"].eq(
    "Interest-only").mean()
print(round(p_I_given_D, 4))
print("Bayes: ", round(p_I_given_D * p_D / p_I, 4))
print("Direct:", round(tape.loc[I, "D"].mean(), 4))

# --- Listing 05.8 ------------------------------------
from scipy import stats

print(stats.binom.pmf([0, 1, 2, 3], n=3, p=0.1).round(4))
print(stats.binom.mean(3, 0.1), stats.binom.var(3, 0.1))

# --- Listing 05.9 ------------------------------------
n_loans, p = 1000, 0.02
rng = np.random.default_rng(21)
years = 50000
draws = rng.uniform(size=(years, n_loans)) < p
N = draws.sum(axis=1)          # defaults in each year
print(f"Simulated mean {N.mean():.3f}, var {N.var():.3f}")
print(f"Formula   mean {n_loans * p:.3f}, "
      f"var {n_loans * p * (1 - p):.3f}")
print(f"P(N > 30): sim {np.mean(N > 30):.4f}, "
      f"formula {stats.binom.sf(30, n_loans, p):.4f}")

# --- Listing 05.10 -----------------------------------
k = np.arange(0, 45)
sim_share = np.bincount(N, minlength=45)[:45] / years
plt.bar(k, sim_share, label="Simulation", color="#C9A227")
plt.plot(k, stats.binom.pmf(k, n_loans, p), "o-",
         markersize=3, label="Binomial formula")
plt.xlabel("Defaults in a year (pool of 1,000 loans)")
plt.ylabel("Probability")
plt.title("Binomial: simulation and formula agree")
plt.legend()
plt.savefig("figures/ch05_binomial.png")

# --- Listing 05.11 -----------------------------------
rng = np.random.default_rng(3)
loss = np.where(rng.uniform(size=1_000_000) < 0.02,
                50000.0, 0.0)
print(f"mean £{loss.mean():,.0f}, sd £{loss.std():,.0f}")

# --- Listing 05.12 -----------------------------------
from scipy.stats import norm

print(round(norm.cdf(1.0), 4), round(norm.cdf(-1.645), 4))
print(round(norm.ppf(0.99), 4))

# --- Listing 05.13 -----------------------------------
mu, sigma = 0.02, 0.08
z = (np.log(0.9) - mu) / sigma
print(round(z, 4), round(norm.cdf(z), 4))
rng = np.random.default_rng(8)
price = 100 * np.exp(rng.normal(mu, sigma, size=500000))
print(round(np.mean(price < 90), 4))

# --- Listing 05.14 -----------------------------------
tape["year"] = tape["default_period"].str[:4]
print(tape["year"].value_counts().sort_index().to_string())

# --- Listing 05.15 -----------------------------------
rng = np.random.default_rng(13)
years, n_loans = 50000, 1000
bad = rng.uniform(size=years) < 0.5
p_year = np.where(bad, 0.04, 0.01)
N_mix = rng.binomial(n_loans, p_year)
N_ind = rng.binomial(n_loans, 0.025, size=years)
for name, x in [("independent", N_ind), ("good/bad", N_mix)]:
    print(f"{name:12s} mean {x.mean():6.2f}  "
          f"sd {x.std():5.2f}  P(N>40) {np.mean(x > 40):.4f}")

# --- Listing 05.16 -----------------------------------
bins = np.arange(0, 75)
plt.hist(N_ind, bins=bins, density=True, alpha=0.8,
         label="Independent, p = 2.5%")
plt.hist(N_mix, bins=bins, density=True, alpha=0.6,
         label="Good/bad years, average 2.5%")
plt.xlabel("Defaults in a year (pool of 1,000 loans)")
plt.ylabel("Probability")
plt.title("Same average, very different tails")
plt.legend()
plt.savefig("figures/ch05_clustering.png")

# --- Listing 05.17 -----------------------------------
m = 2_000_000                       # simulated years
p_m = np.where(rng.uniform(size=m) < 0.5, 0.04, 0.01)
x1 = rng.uniform(size=m) < p_m      # loan 1 defaults
x2 = rng.uniform(size=m) < p_m      # loan 2, same year
print(round(np.corrcoef(x1, x2)[0, 1], 4))

# --- Listing 05.18 -----------------------------------
features = {"Interest-only": I, "Buy-to-let": B,
            "Self-employed": tape["employment"]
            == "Self-employed"}
for name, mask in features.items():
    p_given = tape.loc[mask, "D"].mean()
    p_not = tape.loc[~mask, "D"].mean()
    print(f"{name:14s} P(D|yes) {p_given:.4f}  "
          f"P(D|no) {p_not:.4f}")

# --- Listing 05.19 -----------------------------------
combo = tape.groupby([I.rename("IO"), B.rename("BTL")])["D"]
print(combo.agg(["count", "mean"]).round(4))

# --- Listing 05.20 -----------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
perf["year"] = perf["period"].str[:4]
alive = perf.groupby("year")["loan_id"].nunique()
yearly = tape["year"].value_counts().sort_index()
p_year = (yearly / alive).mean()
print(f"Average yearly default probability {p_year:.4%}")
table = pd.DataFrame({"alive": alive, "defaults": yearly})
table["binom_mean"] = (alive * p_year).round(1)
table["binom_sd"] = np.sqrt(alive * p_year
                            * (1 - p_year)).round(1)
print(table)

# --- Listing 05.21 -----------------------------------
n21 = alive["2021"]
print(f"P(N >= 200) = {stats.binom.sf(199, n21, p_year):.2e}")
z = (yearly["2021"] - n21 * p_year) / np.sqrt(
    n21 * p_year * (1 - p_year))
print(f"2021 is {z:.1f} standard deviations above the mean")

# --- Listing 05.22 -----------------------------------
print(stats.binom.pmf([0, 1], 4, 0.05).round(4))
print(stats.binom.mean(4, 0.05), stats.binom.var(4, 0.05))

# --- Listing 05.23 -----------------------------------
rng = np.random.default_rng(17)
D_sim = rng.uniform(size=1_000_000) < 0.02
flag_prob = np.where(D_sim, 0.80, 0.05)
F_sim = rng.uniform(size=1_000_000) < flag_prob
print(round(D_sim[F_sim].mean(), 4))

# --- Listing 05.24 -----------------------------------
S = tape["employment"] == "Self-employed"
D = tape["D"]
for name, a, b in [("D and S", D, S), ("S and BTL", S, B)]:
    print(f"{name:10s} observed {(a & b).mean():.4f}  "
          f"product {a.mean() * b.mean():.4f}")

# --- Listing 05.25 -----------------------------------
n, p = 10000, 0.054
exact = stats.binom.sf(599, n, p)
mean, sd = n * p, np.sqrt(n * p * (1 - p))
approx = norm.sf((599.5 - mean) / sd)
rng = np.random.default_rng(99)
sim = np.mean(rng.binomial(n, p, size=200000) >= 600)
print(f"mean {mean:.0f}, sd {sd:.2f}")
print(f"exact {exact:.6f}  normal {approx:.6f}  "
      f"sim {sim:.6f}")

# --- Listing 05.26 -----------------------------------
rng = np.random.default_rng(23)
m, p, rho = 1_000_000, 0.05, 0.2
x1 = rng.uniform(size=m) < p
own = rng.uniform(size=m) < p
copy = rng.uniform(size=m) < rho
x2 = np.where(copy, x1, own)
print(f"P(both) {np.mean(x1 & x2):.4f}")
print(f"P(x2)   {x2.mean():.4f}")
print(f"corr    {np.corrcoef(x1, x2)[0, 1]:.4f}")

# --- Listing 05.27 -----------------------------------
# (not executed in the book)
# import numpy as np
# from scipy import stats

# def prob_both_default(p, rho):
#     """P(two loans both default), equal PDs, correlation rho."""
#     return p ** 2 + rho * p * (1 - p)

# def binomial_tail(n, p, k):
#     """P(at least k defaults) in n independent loans."""
#     return stats.binom.sf(k - 1, n, p)

# rng = np.random.default_rng(2026)
# x = rng.binomial(1000, 0.02, size=200000)
# sim_tail = np.mean(x >= 30)
# assert abs(sim_tail - binomial_tail(1000, 0.02, 30)) < 0.002
# assert prob_both_default(0.05, 0.0) == 0.05 ** 2
