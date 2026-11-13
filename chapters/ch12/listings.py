"""
Survival Models

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch12/listings.py
"""

# --- Listing 12.1 ------------------------------------
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

toy = pd.DataFrame({
    "loan": list("ABCDEFGH"),
    "duration": [3, 5, 5, 8, 10, 12, 12, 12],
    "event":    [1, 0, 1, 0, 1, 0, 0, 0]})

s = 1.0
for t in sorted(toy.loc[toy["event"] == 1, "duration"]):
    at_risk = (toy["duration"] >= t).sum()
    ended = toy["duration"] == t
    defaults_t = (ended & (toy["event"] == 1)).sum()
    s = s * (1 - defaults_t / at_risk)
    print(f"month {t:2d}: at risk {at_risk},"
          f" defaults {defaults_t},"
          f" S = {s:.4f}")

# --- Listing 12.2 ------------------------------------
from sfrating import survival

perf = pd.read_csv("data/rmbs_performance.csv.gz")
dur = survival.rmbs_durations(perf)
print(dur.head(3))
print(f"Loans: {len(dur)}, defaults: {dur['event'].sum()}")
print(f"Censored before month 60: "
      f"{((dur['event'] == 0) & (dur['duration'] < 60)).sum()}")

# --- Listing 12.3 ------------------------------------
km = survival.kaplan_meier(dur["duration"], dur["event"])
print(km.head(4).round(6))
for t in [12, 24, 36, 60]:
    pd_t = 1 - survival.survival_at(km, t)
    print(f"Lifetime PD to month {t}: {pd_t:.2%}")

# --- Listing 12.4 ------------------------------------
from lifelines import KaplanMeierFitter

kmf = KaplanMeierFitter()
kmf.fit(dur["duration"], event_observed=dur["event"])
check = 1 - kmf.survival_function_at_times([12, 24, 60])
print(check.round(6).to_string())

ax = kmf.plot_survival_function(legend=False)
ax.set_xlabel("Months since cut-off")
ax.set_ylabel("Share not defaulted")
ax.set_title("Kaplan-Meier survival, Thamesbridge pool")
plt.savefig("figures/ch12_km_pool.png")

# --- Listing 12.5 ------------------------------------
loans = pd.read_csv("data/rmbs_loans.csv")
dur = dur.merge(loans[["loan_id", "current_ltv"]],
                on="loan_id")
high = dur[dur["current_ltv"] > 80]
low = dur[dur["current_ltv"] <= 80]
for name, g in [("LTV ≤ 80", low), ("LTV > 80", high)]:
    k = survival.kaplan_meier(g["duration"], g["event"])
    pd60 = 1 - survival.survival_at(k, 60)
    print(f"{name}: {len(g)} loans, 5-year PD {pd60:.2%}")

# --- Listing 12.6 ------------------------------------
from lifelines.statistics import logrank_test

test = logrank_test(low["duration"], high["duration"],
                    event_observed_A=low["event"],
                    event_observed_B=high["event"])
print(f"Statistic: {test.test_statistic:.1f}")
print(f"p-value:   {test.p_value:.2e}")

# --- Listing 12.7 ------------------------------------
from lifelines import CoxPHFitter

auto = pd.read_csv("data/auto_loans.csv")
print(auto["outcome"].value_counts().to_string())
auto["used"] = (auto["vehicle"] == "Used").astype(int)
cols = ["months_observed", "default", "credit_score",
        "used", "deposit_pct", "apr"]
cox = CoxPHFitter()
cox.fit(auto[cols], duration_col="months_observed",
        event_col="default")
print(cox.summary[["coef", "exp(coef)", "p"]].round(4))

# --- Listing 12.8 ------------------------------------
print(f"Concordance: {cox.concordance_index_:.3f}")

# --- Listing 12.9 ------------------------------------
from lifelines.statistics import proportional_hazard_test

ph = proportional_hazard_test(cox, auto[cols],
                              time_transform="rank")
print(ph.summary[["test_statistic", "p"]].round(3))

# --- Listing 12.10 -----------------------------------
dur["ltv_group"] = pd.cut(dur["current_ltv"],
                          [0, 60, 80, 100],
                          labels=["≤60", "60–80", ">80"])
print(dur.groupby("ltv_group", observed=True).agg(
    loans=("loan_id", "size"),
    defaults=("event", "sum")))

# --- Listing 12.11 -----------------------------------
plt.figure()
for name, g in dur.groupby("ltv_group", observed=True):
    kmf = KaplanMeierFitter(label=f"LTV {name}")
    kmf.fit(g["duration"], event_observed=g["event"])
    curve = 1 - kmf.survival_function_
    plt.step(curve.index, curve.iloc[:, 0] * 100,
             where="post", label=f"LTV {name}")
    pd60 = 1 - kmf.survival_function_at_times(60).iloc[0]
    print(f"LTV {name:>5}: 5-year PD {pd60:.2%}")
plt.xlabel("Months since cut-off")
plt.ylabel("Lifetime PD (%)")
plt.title("Higher LTV, earlier and more defaults")
plt.legend()
plt.savefig("figures/ch12_km_ltv.png")

# --- Listing 12.12 -----------------------------------
ends = [0, 12, 24, 36, 48, 60]
cum = [1 - survival.survival_at(km, t) for t in ends]
per_year = np.diff(cum)
timing = pd.DataFrame({
    "year": [1, 2, 3, 4, 5],
    "default_in_year": per_year,
    "share_of_5y": per_year / cum[-1]})
print(timing.round(4).to_string(index=False))

# --- Listing 12.13 -----------------------------------
observed = dur["event"].mean()
print(f"Observed share defaulted:      {observed:.2%}")
print(f"Kaplan-Meier lifetime PD (5y): {cum[-1]:.2%}")

# --- Listing 12.14 -----------------------------------
km_ex = survival.kaplan_meier([6, 9, 9, 15, 24, 24],
                              [1, 0, 1, 1, 0, 0])
print(km_ex.round(4))

# --- Listing 12.15 -----------------------------------
x = np.array([650, 1, 5, 12])
y = np.array([750, 0, 20, 8])
beta = cox.params_[["credit_score", "used",
                    "deposit_pct", "apr"]].to_numpy()
print(f"Hazard ratio X/Y: {np.exp(beta @ (x - y)):.2f}")

# --- Listing 12.16 -----------------------------------
groups = {}
for name, g in auto.groupby("product"):
    k = KaplanMeierFitter().fit(
        g["months_observed"], event_observed=g["default"])
    groups[name] = g
    pd36 = 1 - k.survival_function_at_times(36).iloc[0]
    print(f"{name}: {len(g)} loans, 36-month PD {pd36:.2%}")
hp, pcp = groups["HP"], groups["PCP"]
lr = logrank_test(hp["months_observed"], pcp["months_observed"],
                  event_observed_A=hp["default"],
                  event_observed_B=pcp["default"])
print(f"Log-rank p-value: {lr.p_value:.3f}")

# --- Listing 12.17 -----------------------------------
rm = dur.merge(loans[["loan_id", "credit_score",
                      "repayment_type", "occupancy"]],
               on="loan_id")
rm["interest_only"] = (rm["repayment_type"]
                       == "Interest-only").astype(int)
rm["buy_to_let"] = (rm["occupancy"]
                    == "Buy-to-let").astype(int)
cox_rm = CoxPHFitter().fit(
    rm[["duration", "event", "credit_score", "current_ltv",
        "interest_only", "buy_to_let"]],
    duration_col="duration", event_col="event")
print(cox_rm.summary[["exp(coef)", "p"]].round(4))

# --- Listing 12.18 -----------------------------------
from sfrating.pd_model import fit_pd_model

defaults = pd.read_csv("data/rmbs_defaults.csv")
logit = fit_pd_model(loans, defaults)
print(logit.pvalues[["interest_only", "buy_to_let"]]
      .round(4).to_string())
print(rm.groupby("interest_only")["current_ltv"].mean()
      .round(1).to_string())

# --- Listing 12.19 -----------------------------------
months = np.arange(1, 61)
n_at_risk = np.array([(dur["duration"] >= m).sum()
                      for m in months])
d_def = np.array([((dur["duration"] == m)
                   & (dur["event"] == 1)).sum()
                  for m in months])
exits = np.array([((dur["duration"] == m)
                   & ((dur["event"] == 1) | (m < 60))).sum()
                  for m in months])
s_all = np.cumprod(1 - exits / n_at_risk)
s_before = np.concatenate([[1.0], s_all[:-1]])
cif = np.cumsum(s_before * d_def / n_at_risk)
s_km = np.cumprod(1 - d_def / n_at_risk)
print(f"Cumulative incidence at 60: {cif[-1]:.2%}")
print(f"Kaplan-Meier PD at 60:      {1 - s_km[-1]:.2%}")

# --- Listing 12.20 -----------------------------------
# (not executed in the book)
# def rmbs_durations(perf):
#     """One row per loan: months observed and default flag.
#     Prepaid loans and loans alive at the end are censored."""
#     last = perf.sort_values("period").groupby("loan_id").tail(1)
#     months = perf.groupby("loan_id").size()
#     out = pd.DataFrame({"loan_id": last["loan_id"].to_numpy(),
#                         "status": last["status"].to_numpy()})
#     out["duration"] = months.reindex(out["loan_id"]).to_numpy()
#     out["event"] = (out["status"] == "DEF").astype(int)
#     return out[["loan_id", "duration", "event"]]

# def kaplan_meier(duration, event):
#     d = pd.DataFrame({"t": np.asarray(duration),
#                       "e": np.asarray(event)})
#     times = np.sort(d.loc[d["e"] == 1, "t"].unique())
#     rows, s = [], 1.0
#     for t in times:
#         at_risk = int((d["t"] >= t).sum())
#         events = int(((d["t"] == t) & (d["e"] == 1)).sum())
#         s *= 1 - events / at_risk
#         rows.append((t, at_risk, events, s))
#     return pd.DataFrame(rows, columns=["time", "at_risk",
#                                        "events", "survival"])
