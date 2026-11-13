"""
Capstone: A Full Rating Model on GitHub

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch23/listings.py
"""

# --- Listing 23.1 ------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sfrating import (cashflow, data, pd_model, rating,
                      report, rmbs, rollrate, survival,
                      vasicek)
import sfrating
print("sfrating version", sfrating.__version__)

# --- Listing 23.2 ------------------------------------
loans = data.load_loans()
perf = data.load_performance()
defaults = data.load_defaults()
deal = data.load_deal()
stresses = data.load_rating_stresses()

tranche_total = sum(t["balance"] for t in deal["tranches"])
def_ids = perf.loc[perf["status"] == "DEF", "loan_id"]
checks = {
    "10,000 unique loans": loans["loan_id"].is_unique
                           and len(loans) == 10_000,
    "no missing values": not loans.isna().any().any(),
    "tape = deal pool balance": np.isclose(
        loans["current_balance"].sum(), deal["pool_balance"]),
    "tranches = pool balance": np.isclose(
        tranche_total, deal["pool_balance"]),
    "defaults match performance": set(defaults["loan_id"])
                                  == set(def_ids),
}
for name, ok in checks.items():
    print(f"{name:28s} {'OK' if ok else 'FAILED'}")

# --- Listing 23.3 ------------------------------------
pool = loans["current_balance"].sum()
w = loans["current_balance"] / pool
print(f"Pool balance:        £{pool / 1e6:,.1f} m")
wa_ltv = (w * loans["original_ltv"]).sum()
wa_rate = (w * loans["interest_rate"]).sum()
print(f"WA original LTV:     {wa_ltv:.1f}%")
print(f"WA interest rate:    {wa_rate:.2f}%")
print(f"Defaults (5 years):  {len(defaults)} loans")

# --- Listing 23.4 ------------------------------------
model = pd_model.fit_pd_model(loans, defaults)
base_pd = pd_model.predict_pd(model, loans)
flag = pd_model.default_flag(loans, defaults)
print(model.params.round(4).to_string())

# --- Listing 23.5 ------------------------------------
pool_pd = (w * base_pd).sum()
gini = pd_model.gini(flag, base_pd)
print(f"Gini:                      {gini:.3f}")
print(f"Mean predicted 5-year PD:  {base_pd.mean():.2%}")
print(f"Observed 5-year default:   {flag.mean():.2%}")
print(f"Balance-weighted PD:       {pool_pd:.2%}")
quintile = pd.qcut(base_pd, 5, labels=[1, 2, 3, 4, 5])
calib = pd.DataFrame({"predicted": base_pd, "actual": flag})
print(calib.groupby(quintile, observed=True).mean().round(4))

# --- Listing 23.6 ------------------------------------
matrix = rollrate.transition_matrix(perf)
proj = rollrate.project(matrix, {"C": 1.0}, 60)
dur = survival.rmbs_durations(perf)
km = survival.kaplan_meier(dur["duration"], dur["event"])

estimates = {
    "Observed (count)": len(defaults) / len(loans),
    "Roll-rate model": proj["DEF"].iloc[60],
    "Kaplan-Meier": 1 - survival.survival_at(km, 60)}
for name, value in estimates.items():
    print(f"{name:18s} {value:.2%}")

# --- Listing 23.7 ------------------------------------
months = np.arange(61)
def_month = (perf[perf["status"] == "DEF"]
             .groupby("period").size().cumsum())
observed = np.concatenate([[0], def_month.reindex(
    sorted(perf["period"].unique())).ffill().fillna(0)
    .to_numpy() / len(loans)])
km_curve = [1 - survival.survival_at(km, t) for t in months]

plt.plot(months, 100 * observed, label="Observed")
plt.plot(months, 100 * proj["DEF"], "--", label="Roll-rate")
plt.plot(months, 100 * np.array(km_curve), ":",
         label="Kaplan-Meier (no prepayment)")
plt.xlabel("Months since cut-off")
plt.ylabel("Cumulative default (%)")
plt.title("Three estimates of the pool's default rate")
plt.legend()
plt.savefig("figures/ch23_default_curves.png")

# --- Listing 23.8 ------------------------------------
levels = rmbs.rating_level_losses(loans, base_pd, stresses)
print(levels.round(4).to_string(index=False))

# --- Listing 23.9 ------------------------------------
perf["quarter"] = (pd.PeriodIndex(perf["period"], freq="M")
                   .asfreq("Q").astype(str))
by_q = perf.groupby("quarter").agg(
    alive=("loan_id", "nunique"),
    defaults=("status", lambda s: (s == "DEF").sum()))
quarterly_dr = (by_q["defaults"] / by_q["alive"]).iloc[1:]
pd_q, rho = vasicek.estimate_rho_moments(quarterly_dr)
print(f"Quarters used: {len(quarterly_dr)}, rho = {rho:.4f}")

# --- Listing 23.10 -----------------------------------
check = levels[["rating", "default_frequency"]].copy()
check["quantile"] = stresses["target_loss_quantile"]
check["one_factor"] = [vasicek.vasicek_quantile(q, pool_pd, rho)
                       for q in check["quantile"]]
print(check.round(4).to_string(index=False))

# --- Listing 23.11 -----------------------------------
term = int(round(np.average(loans["remaining_term_months"],
                            weights=loans["current_balance"])))
results = rating.scenario_results(deal, levels,
                                  remaining_term=term)
print("Remaining term:", term, "months;",
      len(results), "rows")

# --- Listing 23.12 -----------------------------------
worst = results.pivot_table(index="rating", columns="class",
                            values="principal_loss",
                            aggfunc="max")
worst = worst.reindex(rating.RATING_ORDER)
print((100 * worst).round(1))

# --- Listing 23.13 -----------------------------------
model_ratings = rating.assign_ratings(results)
targets = {t["class"]: t["target_rating_illustrative"]
           for t in deal["tranches"]}
ce = cashflow.credit_enhancement(deal).set_index("class")
summary = pd.DataFrame({
    "CE": (100 * ce["credit_enhancement"]).round(1),
    "target": pd.Series(targets),
    "model": model_ratings})
print(summary)

# --- Listing 23.14 -----------------------------------
classes = ["A", "B", "C", "D", "E"]
loss_by_level = levels.set_index("rating")["pool_loss"]
model_level = loss_by_level[model_ratings[classes]].to_numpy()
x = np.arange(len(classes))
plt.bar(x, 100 * ce.loc[classes, "credit_enhancement"],
        width=0.55, label="Credit enhancement")
plt.scatter(x, 100 * np.array(model_level), color="#C9A227",
            zorder=3, s=60, label="Pool loss at model rating")
plt.xticks(x, [f"{c}\n{r}" for c, r in
               zip(classes, model_ratings[classes])])
plt.ylabel("% of pool balance")
plt.title("Credit enhancement and the loss each class survives")
plt.legend()
plt.savefig("figures/ch23_ce_vs_loss.png")

# --- Listing 23.15 -----------------------------------
bbb = levels[levels["rating"] == "BBB"].iloc[0]
for cpr in (0.05, 0.20):
    p = cashflow.project_pool(
        deal["pool_balance"], term,
        cum_default=bbb["default_frequency"],
        severity=bbb["loss_severity"], cpr=cpr)
    led = cashflow.run_waterfall(p, deal, sonia_pct=3.0)
    ledger = led["ledger"]
    losses = p["losses"].sum() / 1e6
    cured = ledger["pdl_cure"].sum() / 1e6
    left = ledger["pdl_balance"].iloc[-1] / 1e6
    z_loss = led["tranche_loss"]["Z"]
    print(f"CPR {cpr:.0%}: losses £{losses:.1f} m, cured "
          f"£{cured:.1f} m, left £{left:.1f} m, Z {z_loss:.1%}")

# --- Listing 23.16 -----------------------------------
def latex_safe(df):
    return df.rename(columns=lambda c: c.replace("_", " "))

ratings_table = (model_ratings.rename_axis("class")
                 .reset_index())
tex = report.write_report(
    "outputs/thamesbridge_model_report.tex",
    title="Thamesbridge Mortgages No. 1: model ratings",
    author="Mohamed Miled", date=r"\today",
    purpose="Teaching rating model for a fictional UK RMBS.",
    levels=latex_safe(levels.round(4)),
    ratings=latex_safe(ratings_table),
    limitations="Illustrative stresses; one representative "
                "line; in-sample PD model.")
lines = tex.read_text().splitlines()
print(len(lines), "lines; section headings:")
headings = [line for line in lines
            if line.startswith(r"\section")]
print("\n".join(headings))

# --- Listing 23.17 -----------------------------------
import sys
from pathlib import Path
CAPSTONE = Path(sfrating.__file__).resolve().parents[1]
sys.path.insert(0, str(CAPSTONE))
import run_rating

args = run_rating.parse_args(["--output-dir", "outputs"])
out = run_rating.run(args)
print("Same ratings as the step-by-step run:",
      out["ratings"].equals(model_ratings))

# --- Listing 23.18 -----------------------------------
def ratings_with_severity(factor):
    lv = levels.copy()
    lv["loss_severity"] *= factor
    lv["pool_loss"] = (lv["default_frequency"]
                       * lv["loss_severity"])
    res = rating.scenario_results(deal, lv, remaining_term=term)
    return rating.assign_ratings(res)

grid = [1.00, 1.05, 1.10, 1.12, 1.14, 1.16, 1.20]
table = pd.DataFrame({f: ratings_with_severity(f)
                      for f in grid})
print(table.T.to_string())

# --- Listing 23.19 -----------------------------------
bbb = levels[levels["rating"] == "BBB"]
for spread in [1.60, 1.40, 1.20, 1.00]:
    losses = []
    for cpr in (0.05, 0.20):
        p = cashflow.project_pool(
            deal["pool_balance"], term,
            cum_default=bbb["default_frequency"].iloc[0],
            severity=bbb["loss_severity"].iloc[0], cpr=cpr)
        r = cashflow.run_waterfall(p, deal, sonia_pct=3.0,
                                   pool_spread_pct=spread)
        losses.append(r["tranche_loss"]["E"])
    print(f"pool spread {spread:.2f}%: worst Class E loss "
          f"{max(losses):.1%}")

# --- Listing 23.20 -----------------------------------
bal = np.array([100_000, 300_000, 100_000])
months_left = np.array([120, 300, 240])
print(months_left.mean(), np.average(months_left, weights=bal))

# --- Listing 23.21 -----------------------------------
io = loans["repayment_type"] == "Interest-only"
for name, mask in [("Interest-only", io), ("Repayment", ~io)]:
    lv = rmbs.rating_level_losses(loans[mask], base_pd[mask],
                                  stresses)
    aaa = lv.iloc[0]
    print(f"{name:13s} {mask.sum():5d} loans  "
          f"DF {aaa['default_frequency']:.2%}  "
          f"LS {aaa['loss_severity']:.2%}  "
          f"loss {aaa['pool_loss']:.2%}")

# --- Listing 23.22 -----------------------------------
def results_markdown(ratings, ce):
    lines = ["| Class | Credit enhancement | Model rating |",
             "|---|---|---|"]
    for c in ["A", "B", "C", "D", "E"]:
        row = f"| {c} | {ce.loc[c]:.1%} | {ratings[c]} |"
        lines.append(row)
    return "\n".join(lines)

print(results_markdown(model_ratings, ce["credit_enhancement"]))

# --- Listing 23.23 -----------------------------------
from sfrating import numerics

aaa = levels[levels["rating"] == "AAA"]

calls = []

def class_a_loses(m):
    calls.append(m)
    lv = aaa.copy()
    lv["default_frequency"] *= m
    res = rating.scenario_results(deal, lv, remaining_term=term)
    loss = res.loc[res["class"] == "A", "principal_loss"].max()
    return 1.0 if loss > 1e-6 else -1.0

m_star = numerics.bisection(class_a_loses, 1.0, 2.0, tol=1e-3)
df_aaa = aaa["default_frequency"].iloc[0]
print(f"Break-even multiple: {m_star:.3f}")
print("Function evaluations:", len(calls))
print(f"AAA default frequency: {df_aaa:.2%} -> "
      f"{m_star * df_aaa:.2%}")
