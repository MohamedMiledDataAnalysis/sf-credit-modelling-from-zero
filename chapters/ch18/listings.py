"""
CLOs

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch18/listings.py
"""

# --- Listing 18.1 ------------------------------------
import numpy as np
import pandas as pd

clo_df = pd.read_csv("data/clo_portfolio.csv")
print(clo_df.shape)
print(f"Total par: £{clo_df['par'].sum() / 1e6:,.1f}m")
print(clo_df[["obligor", "industry", "rating",
              "par"]].head(3))
print(clo_df["rating"].value_counts().to_string())

# --- Listing 18.2 ------------------------------------
from sfrating import clo

table = pd.read_csv("data/rating_default_table.csv")
wal = clo.weighted_average(clo_df["years_to_maturity"],
                           clo_df["par"])
print(f"Weighted average life: {wal:.2f} years")
horizon = int(round(wal))
pd_h = (table[table["horizon_years"] == horizon]
        .set_index("rating")["cumulative_pd"])
clo_df["pd_life"] = clo_df["rating"].map(pd_h)
print(pd_h.round(4).to_string())

# --- Listing 18.3 ------------------------------------
wapd = clo.weighted_average(clo_df["pd_life"], clo_df["par"])
was = clo.weighted_average(clo_df["spread_pct"],
                           clo_df["par"])
warr = clo.weighted_average(clo_df["recovery_assumption"],
                            clo_df["par"])
wapd_1y = clo.weighted_average(clo_df["one_year_pd"],
                               clo_df["par"])
print(f"WA default probability (1y): {wapd_1y:.2%}")
print(f"WA default probability ({horizon}y): {wapd:.2%}")
print(f"WA spread: {was:.2f}%   WA recovery: {warr:.2%}")
ccc = clo_df["rating"] == "CCC"
ccc_share = (clo_df.loc[ccc, "par"] * clo_df.loc[ccc, "pd_life"]
             ).sum() / (clo_df["par"] * clo_df["pd_life"]).sum()
ccc_par = clo_df.loc[ccc, "par"].sum() / clo_df["par"].sum()
print(f"CCC share of par: {ccc_par:.2%}")
print(f"Share of WAPD from CCC loans: {ccc_share:.1%}")

# --- Listing 18.4 ------------------------------------
toy = pd.DataFrame({"par": [10, 10, 10, 10],
                    "industry": ["Software"] * 3 + ["Media"]})
print(round(clo.diversity_score(toy["par"],
                                toy["industry"]), 2))
diversity = clo.diversity_score(clo_df["par"],
                                clo_df["industry"])
print(f"Portfolio diversity score: {diversity:.1f}")

# --- Listing 18.5 ------------------------------------
small = clo.bet_loss_distribution(4, 0.10, 0.60)
print(small.round(4).to_string(index=False))
el = (small["probability"] * small["portfolio_loss"]).sum()
print(f"Expected loss: {el:.4f}")

# --- Listing 18.6 ------------------------------------
print(f"{clo.tranche_expected_loss(small, 0.10, 0.30):.4f}")

# --- Listing 18.7 ------------------------------------
from sfrating import vasicek

lgd = 1 - clo_df["recovery_assumption"]
loss_1f = vasicek.simulate_portfolio_losses(
    clo_df["pd_life"], lgd, clo_df["par"], rho=0.20,
    n_sims=50_000, seed=18)
print(f"Mean loss: {loss_1f.mean():.2%}")

# --- Listing 18.8 ------------------------------------
from scipy.stats import norm

def simulate_industry_losses(pd_i, lgd_i, par_i, industry,
                             rho_g, rho_s, n_sims, seed):
    rng = np.random.default_rng(seed)
    names, idx = np.unique(industry, return_inverse=True)
    threshold = norm.ppf(pd_i)
    loss_if_default = lgd_i * par_i / par_i.sum()
    out = np.empty(n_sims)
    for start in range(0, n_sims, 1_000):
        m = min(1_000, n_sims - start)
        z = rng.standard_normal((m, 1))
        z_ind = rng.standard_normal((m, len(names)))[:, idx]
        eps = rng.standard_normal((m, len(pd_i)))
        x = (np.sqrt(rho_g) * z + np.sqrt(rho_s) * z_ind
             + np.sqrt(1 - rho_g - rho_s) * eps)
        out[start:start + m] = (x < threshold) @ loss_if_default
    return out

# --- Listing 18.9 ------------------------------------
loss_ind = simulate_industry_losses(
    clo_df["pd_life"].to_numpy(), lgd.to_numpy(),
    clo_df["par"].to_numpy(), clo_df["industry"].to_numpy(),
    rho_g=0.10, rho_s=0.15, n_sims=50_000, seed=18)
print(f"Mean loss: {loss_ind.mean():.2%}")
exact_el = ((clo_df["par"] * clo_df["pd_life"] * lgd).sum()
            / clo_df["par"].sum())
print(f"Exact expected loss: {exact_el:.2%}")

# --- Listing 18.10 -----------------------------------
tranches = pd.DataFrame({
    "tranche": ["AAA", "AA", "A", "BBB", "BB", "Equity"],
    "attach": [0.38, 0.27, 0.21, 0.15, 0.10, 0.00],
    "detach": [1.00, 0.38, 0.27, 0.21, 0.15, 0.10]})
print(tranches.to_string(index=False))

# --- Listing 18.11 -----------------------------------
D = int(round(diversity))
wa_lgd = clo.weighted_average(lgd, clo_df["par"])
bet = clo.bet_loss_distribution(D, wapd, wa_lgd)
print(f"D = {D}, p = {wapd:.4f}, LGD = {wa_lgd:.4f}")
bet_mean = (bet["probability"] * bet["portfolio_loss"]).sum()
print(f"BET mean loss: {bet_mean:.2%}")

# --- Listing 18.12 -----------------------------------
def sim_tranche_el(losses, a, d):
    hit = np.clip(losses - a, 0, d - a) / (d - a)
    return hit.mean()

rows = []
for t in tranches.itertuples():
    rows.append({
        "tranche": t.tranche,
        "BET": clo.tranche_expected_loss(bet, t.attach,
                                         t.detach),
        "1-factor": sim_tranche_el(loss_1f, t.attach, t.detach),
        "industry": sim_tranche_el(loss_ind, t.attach,
                                   t.detach)})
compare = pd.DataFrame(rows).set_index("tranche")
print((compare * 100).round(3))

# --- Listing 18.13 -----------------------------------
bet_cdf = bet["probability"].cumsum()
qs = [0.95, 0.99, 0.999]
bet_q = [bet.loc[bet_cdf >= q, "portfolio_loss"].iloc[0]
         for q in qs]
tails = pd.DataFrame({
    "BET": bet_q,
    "1-factor": np.quantile(loss_1f, qs),
    "industry": np.quantile(loss_ind, qs)}, index=qs)
print((tails * 100).round(2))

# --- Listing 18.14 -----------------------------------
import matplotlib.pyplot as plt

grid = np.linspace(0, 0.30, 121)
bet_exceed = [bet.loc[bet["portfolio_loss"] > x,
                      "probability"].sum() for x in grid]
plt.semilogy(grid * 100, np.maximum(bet_exceed, 1e-6),
             label="BET (D = 76)")
for name, sims in [("One factor, rho 0.20", loss_1f),
                   ("Industry, 0.10 / 0.25", loss_ind)]:
    exceed = [(sims > x).mean() for x in grid]
    plt.semilogy(grid * 100, np.maximum(exceed, 1e-6),
                 label=name)
plt.ylim(1e-5, 1.5)
plt.xlabel("Portfolio loss (% of par)")
plt.ylabel("Probability loss exceeds x")
plt.title("The BET has a much thinner tail")
plt.legend(loc="upper right")
plt.savefig("figures/ch18_tail_comparison.png")

# --- Listing 18.15 -----------------------------------
par0 = clo_df["par"].sum()
defaulted = clo_df["rating"] == "CCC"
adjusted = (clo_df.loc[~defaulted, "par"].sum()
            + (clo_df.loc[defaulted, "par"]
               * clo_df.loc[defaulted, "recovery_assumption"]
               ).sum())
new_ccc = clo_df.loc[clo_df["rating"] == "B-", "par"].sum()
limit = 0.075 * clo_df.loc[~defaulted, "par"].sum()
excess = max(0.0, new_ccc - limit)
adjusted -= excess * (1 - 0.70)        # excess CCC at 70%
print(f"Adjusted par: £{adjusted / 1e6:,.1f}m "
      f"(was £{par0 / 1e6:,.1f}m)")

# --- Listing 18.16 -----------------------------------
rated = tranches.iloc[:5]               # the five rated classes
size = (rated["detach"] - rated["attach"]) * par0
above = size.cumsum().to_numpy()        # class and all above
triggers = [1.50, 1.28, 1.18, 1.10, 1.05]
for name, notes, trig in zip(rated["tranche"], above,
                             triggers):
    ratio = adjusted / notes
    status = "pass" if ratio >= trig else "FAIL"
    print(f"{name:4s} OC {ratio:7.2%} trigger {trig:.0%} "
          f"{status}")

# --- Listing 18.17 -----------------------------------
d3 = clo.bet_loss_distribution(3, 0.2, 0.5)
print(f"{clo.tranche_expected_loss(d3, 0.10, 0.20):.4f}")

# --- Listing 18.18 -----------------------------------
inds = sorted(clo_df["industry"].unique())
group = {name: f"G{k % 5 + 1}" for k, name in enumerate(inds)}
merged = clo_df["industry"].map(group)
d5 = clo.diversity_score(clo_df["par"], merged)
bet5 = clo.bet_loss_distribution(int(round(d5)), wapd, wa_lgd)
print(f"Diversity with 5 industries: {d5:.1f}")
print(f"BB EL: "
      f"{clo.tranche_expected_loss(bet5, 0.10, 0.15):.3%}")

# --- Listing 18.19 -----------------------------------
bb = tranches.set_index("tranche").loc["BB"]
for rho in [0.10, 0.20, 0.30]:
    sims = vasicek.simulate_portfolio_losses(
        clo_df["pd_life"], lgd, clo_df["par"], rho=rho,
        n_sims=50_000, seed=18)
    el_bb = sim_tranche_el(sims, bb["attach"], bb["detach"])
    print(f"rho {rho:.2f}: BB EL {el_bb:.3%}, "
          f"99% loss {np.quantile(sims, 0.99):.2%}")

# --- Listing 18.20 -----------------------------------
target = compare.loc["BB", "1-factor"]
best_d, best_gap = None, np.inf
for d_try in range(2, 77):
    dist = clo.bet_loss_distribution(d_try, wapd, wa_lgd)
    el_try = clo.tranche_expected_loss(dist, 0.10, 0.15)
    gap = abs(el_try - target)
    if gap < best_gap:
        best_d, best_gap, best_el = d_try, gap, el_try
print(f"Copula BB EL: {target:.3%}")
print(f"Closest BET: D = {best_d}, BB EL {best_el:.3%}")

# --- Listing 18.21 -----------------------------------
# (not executed in the book)
# from scipy.stats import binom

# def bet_loss_distribution(diversity, p, lgd):
#     """D independent equal loans, each defaulting with
#     probability p."""
#     k = np.arange(diversity + 1)
#     prob = binom.pmf(k, diversity, p)
#     loss = k / diversity * lgd
#     return pd.DataFrame({"defaults": k, "probability": prob,
#                          "portfolio_loss": loss})

# def tranche_expected_loss(dist, attach, detach):
#     """Expected loss of a tranche as a share of its size."""
#     loss = dist["portfolio_loss"].to_numpy()
#     hit = (np.clip(loss - attach, 0, detach - attach)
#            / (detach - attach))
#     return float((hit * dist["probability"].to_numpy()).sum())

# --- Listing 18.22 -----------------------------------
check = clo.bet_loss_distribution(4, 0.10, 0.60)
print(round(clo.tranche_expected_loss(check, 0.10, 0.30), 4))
