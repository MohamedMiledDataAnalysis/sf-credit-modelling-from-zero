"""
Validation and Documentation in LaTeX

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch21/listings.py
"""

# --- Listing 21.1 ------------------------------------
import numpy as np
import pandas as pd
from sfrating import rollrate

perf = pd.read_csv("data/rmbs_performance.csv.gz")
perf = rollrate.add_previous_status(perf)
periods = sorted(perf["period"].unique())
train = [p for p in periods if p < "2023"]
test = [p for p in periods if p >= "2023"]
print(len(train), "training months,", len(test), "test months")

# --- Listing 21.2 ------------------------------------
dec22 = perf[perf["period"] == "2022-12"]
alive = dec22[~dec22["status"].isin(["DEF", "PRE"])]
start = alive["status"].value_counts(normalize=True)
M_train = rollrate.transition_matrix(perf, train)
M_test = rollrate.transition_matrix(perf, test)
pred_out = rollrate.project(M_train, start, 24)["DEF"].iloc[-1]
pred_in = rollrate.project(M_test, start, 24)["DEF"].iloc[-1]
late = perf[(perf["period"] >= "2023")
            & (perf["status"] == "DEF")]
actual = late["loan_id"].nunique() / len(alive)
print(f"Loans alive at Dec 2022: {len(alive):,}")
print(f"Out-of-sample (2020-22 matrix): {pred_out:.2%}")
print(f"In-sample (2023-24 matrix):     {pred_in:.2%}")
print(f"Actual 2023-24:                 {actual:.2%}")

# --- Listing 21.3 ------------------------------------
import statsmodels.api as sm
from sfrating import pd_model

loans = pd.read_csv("data/rmbs_loans.csv")
dflt = pd.read_csv("data/rmbs_defaults.csv")
early = dflt.loc[dflt["default_period"] < "2023", "loan_id"]
late_ids = dflt.loc[dflt["default_period"] >= "2023", "loan_id"]

X_all = sm.add_constant(
    pd_model.prepare_features(loans).astype(float))
y_train = loans["loan_id"].isin(early).astype(int)
pd_fit = sm.Logit(y_train, X_all).fit(disp=0)

test_loans = loans[loans["loan_id"].isin(alive["loan_id"])]
y_test = test_loans["loan_id"].isin(late_ids).astype(int)
print(len(test_loans), "test loans,", y_test.sum(), "defaults")

# --- Listing 21.4 ------------------------------------
X_test = sm.add_constant(
    pd_model.prepare_features(test_loans).astype(float),
    has_constant="add")
pd_3y = pd_fit.predict(X_test)
pd_2y = 1 - (1 - pd_model.annualise(pd_3y, 3)) ** 2
gini_in = pd_model.gini(y_train, pd_fit.predict(X_all))
gini_out = pd_model.gini(y_test, pd_2y)
print(f"Gini in-sample {gini_in:.3f}, "
      f"out-of-sample {gini_out:.3f}")
print(f"Predicted 2-year PD {pd_2y.mean():.2%}, "
      f"actual {y_test.mean():.2%}")

# --- Listing 21.5 ------------------------------------
from scipy import stats

k = int(y_test.sum())
n = len(y_test)
test_result = stats.binomtest(k, n, pd_2y.mean())
print(f"Expected {n * pd_2y.mean():.0f}, observed {k}")
print(f"p-value {test_result.pvalue:.1e}")

from sfrating import vasicek
rho = 0.075  # Chapter 13's estimate for Thamesbridge
p_corr = vasicek.vasicek_cdf(k / n, pd_2y.mean(), rho)
print(f"P(rate <= observed), rho {rho}: {p_corr:.3f}")

# --- Listing 21.6 ------------------------------------
import matplotlib.pyplot as plt

calib = pd.DataFrame({"pd": np.asarray(pd_2y),
                      "default": y_test.to_numpy()})
calib["decile"] = pd.qcut(calib["pd"], 10, labels=False) + 1
table = calib.groupby("decile")[["pd", "default"]].mean()
print((table * 100).round(2))

fig, ax = plt.subplots()
ax.plot(table.index, table["pd"] * 100, marker="o",
        label="Predicted")
ax.plot(table.index, table["default"] * 100, marker="s",
        label="Observed")
ax.set_xticks(range(1, 11))
ax.set_xlabel("Decile of predicted PD (1 = lowest)")
ax.set_ylabel("Two-year default rate (%)")
ax.set_title("Out-of-sample calibration, 2023-2024")
ax.legend()
plt.savefig("figures/ch21_calibration.png")

# --- Listing 21.7 ------------------------------------
from sfrating import survival

dur = survival.rmbs_durations(perf[perf["period"] < "2023"])
km = survival.kaplan_meier(dur["duration"], dur["event"])
s36 = survival.survival_at(km, 36)
km_2y = 1 - s36 ** (24 / 36)
bench = pd.Series({"Roll-rate": pred_out,
                   "Logistic PD": pd_2y.mean(),
                   "Kaplan-Meier": km_2y,
                   "Actual": actual})
print((bench * 100).round(2).to_string())

# --- Listing 21.8 ------------------------------------
edges = np.quantile(loans["credit_score"],
                    np.linspace(0, 1, 11))
edges[0], edges[-1] = -np.inf, np.inf
e = pd.cut(loans["credit_score"], edges).value_counts(
    normalize=True, sort=False)
a = pd.cut(test_loans["credit_score"], edges).value_counts(
    normalize=True, sort=False)
psi = ((a - e) * np.log(a / e)).sum()
print(f"PSI of credit score: {psi:.4f}")

# --- Listing 21.9 ------------------------------------
import json
from sfrating import rmbs, rating, report

with open("data/rmbs_deal.json") as f:
    deal = json.load(f)
stresses = pd.read_csv("data/rating_stresses.csv")
full_pd = pd_model.predict_pd(
    pd_model.fit_pd_model(loans, dflt), loans)
levels = rmbs.rating_level_losses(loans, full_pd, stresses)
w = loans["current_balance"] / loans["current_balance"].sum()
term = int(round((w * loans["remaining_term_months"]).sum()))
ratings = rating.assign_ratings(
    rating.scenario_results(deal, levels, term))
print(" ".join(f"{c}:{r}" for c, r in ratings.items()))

# --- Listing 21.10 -----------------------------------
levels_tex = (levels.set_index("rating") * 100).round(2)
levels_tex.columns = ["Default freq. (\\%)",
                      "Severity (\\%)", "Pool loss (\\%)"]
levels_tex = levels_tex.reset_index().rename(
    columns={"rating": "Level"})
ratings_tex = pd.DataFrame({
    "Class": ratings.index,
    "Target": [t["target_rating_illustrative"]
               for t in deal["tranches"]],
    "Model": ratings.to_numpy()})
print(ratings_tex.to_string(index=False))

# --- Listing 21.11 -----------------------------------
import textwrap

purpose = (
    "This document describes the teaching model used to "
    "assign illustrative ratings to the notes of "
    "Thamesbridge Mortgages No.~1 plc. Loan-level PDs feed "
    "rating-level default frequencies and severities, "
    "which a representative-line cashflow model runs "
    "through the deal waterfall under 5\\% and 20\\% CPR.")
limitations = (
    "The PD model was estimated on 2020--2024, a window "
    "that includes one downturn. Refitted on 2020--2022, "
    f"it predicts {pd_2y.mean():.2%} two-year defaults in "
    f"2023--2024 against {actual:.2%} observed. "
    .replace("%", "\\%")
    + "The pool is modelled as one representative line "
    "with a single default timing curve. Rating stresses "
    "are illustrative teaching values.")
purpose = textwrap.fill(purpose, 60, break_on_hyphens=False)
limitations = textwrap.fill(limitations, 60,
                            break_on_hyphens=False)
print(limitations)

# --- Listing 21.12 -----------------------------------
path = report.write_report(
    "outputs/model_document.tex",
    title="Thamesbridge RMBS Rating Model",
    author="Quantitative Research",
    date="November 2026", purpose=purpose,
    levels=levels_tex, ratings=ratings_tex,
    limitations=limitations)
lines = path.read_text().splitlines()
print(len(lines), "lines written")
print("\n".join(lines[:19]))

# --- Listing 21.13 -----------------------------------
r = stats.binomtest(62, 2500, 0.02)
print(f"p-value {r.pvalue:.3f}")

# --- Listing 21.14 -----------------------------------
for year in ["2021", "2022"]:
    months = [p for p in periods if p.startswith(year)]
    M = rollrate.transition_matrix(perf, months)
    p24 = rollrate.project(M, start, 24)["DEF"].iloc[-1]
    print(f"{year} matrix: {p24:.2%}  (actual {actual:.2%})")

# --- Listing 21.15 -----------------------------------
io_flag = (test_loans["repayment_type"]
           == "Interest-only").to_numpy()
for name, mask in [("Interest-only", io_flag),
                   ("Repayment", ~io_flag)]:
    g = pd_model.gini(y_test[mask], np.asarray(pd_2y)[mask])
    print(f"{name:13s} n={mask.sum():5d}  "
          f"defaults={y_test[mask].sum():3d}  Gini={g:.3f}")

# --- Listing 21.16 -----------------------------------
from sfrating import numerics

lin = X_test.to_numpy() @ pd_fit.params.to_numpy()

def mean_pd_2y(shift):
    p3 = 1 / (1 + np.exp(-(lin + shift)))
    return np.mean(1 - (1 - pd_model.annualise(p3, 3)) ** 2)

shift = numerics.bisection(
    lambda c: mean_pd_2y(c) - actual, -5.0, 5.0)
p3_new = 1 / (1 + np.exp(-(lin + shift)))
pd_new = 1 - (1 - pd_model.annualise(p3_new, 3)) ** 2
print(f"Intercept shift {shift:.4f}")
print(f"Mean PD {pd_new.mean():.2%}, actual {actual:.2%}")
print(f"Gini {pd_model.gini(y_test, pd_new):.3f}")

# --- Listing 21.17 -----------------------------------
# (not executed in the book)
# def table(df, digits=4):
#     return df.to_latex(index=False,
#                        float_format=lambda x: f"{x:.{digits}f}")

# def write_report(path, title, author, date, purpose,
#                  levels, ratings, limitations):
#     text = TEMPLATE % {"title": title, "author": author,
#                        "date": date, "purpose": purpose,
#                        "levels": table(levels),
#                        "ratings": table(ratings),
#                        "limitations": limitations}
#     p = Path(path)
#     p.write_text(text)
#     return p

# --- Listing 21.18 -----------------------------------
print(path.name, path.stat().st_size > 0)
