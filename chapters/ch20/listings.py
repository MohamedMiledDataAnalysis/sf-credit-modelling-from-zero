"""
Tranche Loss, Credit Enhancement and Rating Levels

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch20/listings.py
"""

# --- Listing 20.1 ------------------------------------
import json
import numpy as np
import pandas as pd
from sfrating import cashflow

with open("data/rmbs_deal.json") as f:
    deal = json.load(f)
ce = cashflow.credit_enhancement(deal)
print((ce.set_index("class") * 100).round(2))

# --- Listing 20.2 ------------------------------------
from sfrating import pd_model, rmbs

loans = pd.read_csv("data/rmbs_loans.csv")
dflt = pd.read_csv("data/rmbs_defaults.csv")
stresses = pd.read_csv("data/rating_stresses.csv")
model = pd_model.fit_pd_model(loans, dflt)
base_pd = pd_model.predict_pd(model, loans)
levels = rmbs.rating_level_losses(loans, base_pd, stresses)
print(levels.round(4).to_string(index=False))

# --- Listing 20.3 ------------------------------------
w = loans["current_balance"] / loans["current_balance"].sum()
term = int(round((w * loans["remaining_term_months"]).sum()))
print("Remaining term:", term, "months")

# --- Listing 20.4 ------------------------------------
aaa = levels.set_index("rating").loc["AAA"]
pool = cashflow.project_pool(
    deal["pool_balance"], term,
    cum_default=aaa["default_frequency"],
    severity=aaa["loss_severity"], cpr=0.05)
res = cashflow.run_waterfall(pool, deal, sonia_pct=3.0)
for c, loss in res["tranche_loss"].items():
    month = res["first_interest_shortfall"][c]
    print(c, f"principal loss {loss:.2%}",
          "| first shortfall", month)

# --- Listing 20.5 ------------------------------------
from sfrating import rating

results = rating.scenario_results(deal, levels, term)
print(results.shape)
grid = results.pivot_table(index=["rating", "cpr"],
                           columns="class",
                           values="principal_loss", sort=False)
print((grid * 100).round(1))

# --- Listing 20.6 ------------------------------------
import matplotlib.pyplot as plt

grid_df = np.linspace(0, 0.40, 41)
curves = {c: [] for c in "ABCDEZ"}
for d in grid_df:
    p = cashflow.project_pool(deal["pool_balance"], term,
                              cum_default=d,
                              severity=aaa["loss_severity"],
                              cpr=0.05)
    r = cashflow.run_waterfall(p, deal, sonia_pct=3.0)
    for c in curves:
        curves[c].append(r["tranche_loss"][c])
fig, ax = plt.subplots()
for c, losses in curves.items():
    ax.plot(grid_df * 100, np.array(losses) * 100,
            label=f"Class {c}")
ax.set_xlabel("Cumulative default frequency (%)")
ax.set_ylabel("Tranche loss (%)")
ax.set_title("Losses climb the capital structure")
ax.legend(loc="center right", fontsize=8)
plt.savefig("figures/ch20_tranche_loss_curves.png")

# --- Listing 20.7 ------------------------------------
e_bbb = results[(results["class"] == "E")
                & (results["rating"] == "BBB")]
print(e_bbb.to_string(index=False))

# --- Listing 20.8 ------------------------------------
bbb = levels.set_index("rating").loc["BBB"]
p_bbb = cashflow.project_pool(
    deal["pool_balance"], term,
    cum_default=bbb["default_frequency"],
    severity=bbb["loss_severity"], cpr=0.20)
r_bbb = cashflow.run_waterfall(p_bbb, deal, sonia_pct=3.0)
unpaid = r_bbb["interest_shortfall"]["E"]
print(f"Class E interest never paid: £{unpaid / 1e6:.2f} m")

# --- Listing 20.9 ------------------------------------
# (not executed in the book)
# for r in RATING_ORDER:               # AAA, AA, A, BBB, BB, B
#     s = g[g["rating"] == r]
#     if s.empty:                      # .all() of nothing is True
#         continue
#     ok = (s["principal_loss"] <= tol).all()
#     if c in TIMELY_INTEREST:         # {"A", "B"}
#         ok = ok and not s["interest_shortfall"].any()
#     if ok:
#         out[c] = r
#         break

# --- Listing 20.10 -----------------------------------
ratings = rating.assign_ratings(results)
print(ratings.to_string())

# --- Listing 20.11 -----------------------------------
from sfrating import numerics

def tranche_loss(cls, d, severity, cpr):
    p = cashflow.project_pool(deal["pool_balance"], term,
                              cum_default=d, severity=severity,
                              cpr=cpr)
    r = cashflow.run_waterfall(p, deal, sonia_pct=3.0)
    return r["tranche_loss"][cls]

def break_even(cls, severity, cpr):
    f = lambda d: tranche_loss(cls, d, severity, cpr) - 1e-6
    return numerics.bisection(f, 0.0, 1.0, tol=1e-5)

print(f"Class A: {break_even('A', 0.45, 0.05):.2%}")

# --- Listing 20.12 -----------------------------------
for c in ["A", "B", "C", "D", "E", "Z"]:
    be = break_even(c, 0.45, 0.05)
    row = ce.set_index("class").loc[c]
    print(f"{c}: CE {row['credit_enhancement']:6.2%}"
          f"  CE/0.45 {row['credit_enhancement'] / 0.45:6.2%}"
          f"  model {be:6.2%}")

# --- Listing 20.13 -----------------------------------
pack = pd.DataFrame({
    "CE %": (ce.set_index("class")["credit_enhancement"]
             * 100).round(2),
    "target": {t["class"]: t["target_rating_illustrative"]
               for t in deal["tranches"]},
    "model": ratings})
print(pack)

# --- Listing 20.14 -----------------------------------
lv = levels.set_index("rating")
rows = []
for c, r in ratings.items():
    sev = lv.loc[r, "loss_severity"]
    be = break_even(c, sev, 0.20)
    rows.append({"class": c, "rating": r,
                 "level DF %": round(100 * lv.loc[r,
                                     "default_frequency"], 2),
                 "break-even %": round(100 * be, 2)})
cushion = pd.DataFrame(rows).set_index("class")
cushion["cushion"] = (cushion["break-even %"]
                      - cushion["level DF %"]).round(2)
print(cushion)

# --- Listing 20.15 -----------------------------------
sev_up = levels.copy()
sev_up["loss_severity"] = (sev_up["loss_severity"]
                           * 1.10).clip(upper=1.0)
res_up = rating.scenario_results(deal, sev_up, term)
compare = pd.DataFrame({"base": ratings,
                        "severity +10%":
                        rating.assign_ratings(res_up)})
print(compare)

# --- Listing 20.16 -----------------------------------
fig, ax = plt.subplots()
x = np.arange(len(cushion))
ax.bar(x - 0.2, cushion["level DF %"], width=0.4,
       label="Level default frequency")
ax.bar(x + 0.2, cushion["break-even %"], width=0.4,
       label="Break-even default rate")
ax.set_xticks(x)
ax.set_xticklabels([f"{c}\n{r}" for c, r in
                    cushion["rating"].items()])
ax.set_ylabel("Default frequency (%)")
ax.set_title("Each class against its own rating level")
ax.legend(loc="upper right")
plt.savefig("figures/ch20_cushion.png")

# --- Listing 20.17 -----------------------------------
print(f"{0.065 / 0.3330:.2%}")
print(f"{break_even('C', 0.3330, 0.05):.2%}")

# --- Listing 20.18 -----------------------------------
sev_20 = levels.copy()
sev_20["loss_severity"] = (sev_20["loss_severity"]
                           * 1.20).clip(upper=1.0)
res_20 = rating.scenario_results(deal, sev_20, term)
compare["severity +20%"] = rating.assign_ratings(res_20)
print(compare)

# --- Listing 20.19 -----------------------------------
for c, lev in [("A", "AAA"), ("B", "AA"), ("E", "BBB")]:
    s = res_20[(res_20["class"] == c)
               & (res_20["rating"] == lev)]
    print(s[["rating", "cpr", "class", "principal_loss",
             "interest_shortfall"]].to_string(index=False,
                                             header=False))

# --- Listing 20.20 -----------------------------------
res_30 = rating.scenario_results(deal, levels, term,
                                 cprs=(0.05, 0.30))
compare["fast CPR 30%"] = rating.assign_ratings(res_30)
print(compare[["base", "fast CPR 30%"]])

# --- Listing 20.21 -----------------------------------
import copy

def deal_with_bigger_c(extra):
    d = copy.deepcopy(deal)
    pool_bal = d["pool_balance"]
    for t in d["tranches"]:
        if t["class"] == "A":
            t["share_of_pool"] -= extra
        if t["class"] == "C":
            t["share_of_pool"] += extra
        t["balance"] = t["share_of_pool"] * pool_bal
    return d

for extra in np.arange(0.0025, 0.0301, 0.0025):
    d2 = deal_with_bigger_c(extra)
    r2 = rating.assign_ratings(
        rating.scenario_results(d2, levels, term))
    if r2["B"] == "AAA":
        print(f"Class C +{extra:.2%}: B is AAA;",
              "C is", r2["C"])
        break

# --- Listing 20.22 -----------------------------------
# (not executed in the book)
# RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B"]
# TIMELY_INTEREST = {"A", "B"}

# for _, lv in level_losses.iterrows():
#     for cpr in cprs:
#         pool = project_pool(
#             deal["pool_balance"], remaining_term,
#             cum_default=lv["default_frequency"],
#             severity=lv["loss_severity"], cpr=cpr,
#             timing=timing, annuity_rate_pct=annuity_rate_pct)
#         res = run_waterfall(pool, deal, sonia_pct=sonia_pct)
#         for c, loss in res["tranche_loss"].items():
#             short = res["first_interest_shortfall"][c]
#             rows.append({
#                 "rating": lv["rating"], "cpr": cpr,
#                 "class": c, "principal_loss": loss,
#                 "interest_shortfall": short is not None})

# --- Listing 20.23 -----------------------------------
print(" ".join(f"{c}:{r}" for c, r in ratings.items()))
