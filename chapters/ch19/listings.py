"""
The Cashflow Model and the Waterfall

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch19/listings.py
"""

# --- Listing 19.1 ------------------------------------
def scheduled_principal(balance, monthly_rate, months_left):
    growth = (1 + monthly_rate) ** months_left
    return balance * monthly_rate / (growth - 1)

print(round(scheduled_principal(1000, 0.01, 2), 2))
print(round(scheduled_principal(1000 - 497.51, 0.01, 1), 2))

# --- Listing 19.2 ------------------------------------
def cpr_to_smm(cpr):
    return 1 - (1 - cpr) ** (1 / 12)

for cpr in [0.05, 0.10, 0.20]:
    smm = cpr_to_smm(cpr)
    back = 1 - (1 - smm) ** 12
    print(f"CPR {cpr:.0%}  SMM {smm:.4%}  check {back:.0%}")

# --- Listing 19.3 ------------------------------------
import numpy as np

def monthly_timing(annual_shares):
    a = np.asarray(annual_shares, dtype=float)
    a = a / a.sum()              # shares must add to 1
    return np.repeat(a / 12, 12) # 12 equal months a year

curve = monthly_timing([0.20, 0.25, 0.20, 0.15, 0.10, 0.10])
print(len(curve), round(curve.sum(), 10))
print((6_000_000 * curve[[0, 12, 24]]).round(0))

# --- Listing 19.4 ------------------------------------
# (not executed in the book)
# for t in range(months):
#     start = bal
#     defaults = min(cum_default * balance * curve[t], start)
#     perf = start - defaults
#     sched = perf * r / ((1 + r) ** (remaining_term - t) - 1)
#     prepay = (perf - sched) * cpr_to_smm(cpr)
#     bal = perf - sched - prepay
#     pending_rec[t + recovery_lag] += defaults * (1 - severity)
#     pending_loss[t + recovery_lag] += defaults * severity

# --- Listing 19.5 ------------------------------------
import pandas as pd
from sfrating import cashflow

pool = cashflow.project_pool(100_000_000, remaining_term=240,
                             cum_default=0.06, severity=0.30,
                             cpr=0.10)
view = pool.set_index("month")[["defaults",
    "scheduled_principal", "prepayments", "recoveries",
    "losses"]]
view.columns = ["default", "sched", "prepay", "recov", "loss"]
print((view.loc[[1, 2, 16, 17]] / 1e3).round(1))

# --- Listing 19.6 ------------------------------------
out = (pool["scheduled_principal"].sum()
       + pool["prepayments"].sum() + pool["defaults"].sum()
       + pool["closing_balance"].iloc[-1])
print(f"Accounted for: £{out:,.2f}")
print(f"Lost: £{pool['losses'].sum():,.0f}")

# --- Listing 19.7 ------------------------------------
toy_deal = {
    "pool_balance": 100_000_000,
    "reserve_fund_target_pct": 0.02,
    "senior_fees_bps_per_year": 24,
    "tranches": [
        {"class": "A", "balance": 90e6, "margin_pct": 0.6},
        {"class": "B", "balance": 6e6, "margin_pct": 1.2},
        {"class": "Z", "balance": 4e6, "margin_pct": None}]}
toy_pool = pd.DataFrame({
    "month": [1, 2],
    "opening_balance": [100e6, 98e6], "defaults": [0, 0],
    "scheduled_principal": [2e5, 2e5],
    "prepayments": [8e5, 8e5],
    "recoveries": [7e5, 0], "losses": [3e5, 0]})
res = cashflow.run_waterfall(toy_pool, toy_deal, sonia_pct=3.0,
                             pool_spread_pct=3.0)
show = ["revenue", "fees", "int_A", "int_B", "pdl_cure",
        "reserve", "residual", "bal_A"]
print(res["ledger"][show].T.round(0))

# --- Listing 19.8 ------------------------------------
led = res["ledger"]
reserve_before = np.r_[2_000_000, led["reserve"].iloc[:-1]]
cash_in = led["revenue"] + reserve_before
cash_out = (led["fees"] + led["int_A"] + led["int_B"]
            + led["pdl_cure"] + led["reserve"]
            + led["residual"])
print("Revenue gap:", (cash_in - cash_out).abs().max())
notes = led[["bal_A", "bal_B", "bal_Z"]].sum(axis=1)
paid = np.r_[100e6, notes.iloc[:-1]] - notes
received = (toy_pool["scheduled_principal"]
            + toy_pool["prepayments"]
            + toy_pool["recoveries"] + led["pdl_cure"])
print("Principal gap:", (paid - received).abs().max())

# --- Listing 19.9 ------------------------------------
import json
loans = pd.read_csv("data/rmbs_loans.csv")
with open("data/rmbs_deal.json") as f:
    deal = json.load(f)
w = loans["current_balance"] / loans["current_balance"].sum()
term = int(round((w * loans["remaining_term_months"]).sum()))
rate = (w * loans["interest_rate"]).sum()
print(f"Pool balance: £{deal['pool_balance']:,.0f}")
print(f"Remaining term: {term} months, rate {rate:.2f}%")

# --- Listing 19.10 -----------------------------------
dflt = pd.read_csv("data/rmbs_defaults.csv")
perf = pd.read_csv("data/rmbs_performance.csv.gz")
pool0 = deal["pool_balance"]
base_df = dflt["balance_at_default"].sum() / pool0
base_ls = dflt["loss"].sum() / dflt["exposure_at_default"].sum()
monthly = perf.groupby("period")[["opening_balance",
                                  "prepayment"]].sum()
smm = (monthly["prepayment"]
       / monthly["opening_balance"]).mean()
base_cpr = 1 - (1 - smm) ** 12
print(f"Default frequency {base_df:.2%}")
print(f"Severity {base_ls:.2%}")
print(f"SMM {smm:.4%}, CPR {base_cpr:.2%}")

# --- Listing 19.11 -----------------------------------
pool = cashflow.project_pool(deal["pool_balance"], term,
                             cum_default=base_df,
                             severity=base_ls, cpr=base_cpr)
print(len(pool), "months")
totals = pool[["scheduled_principal", "prepayments",
               "defaults", "recoveries", "losses"]].sum()
print((totals / 1e6).round(1).to_string())

# --- Listing 19.12 -----------------------------------
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(pool["month"], pool["scheduled_principal"] / 1e6,
        label="Scheduled principal")
ax.plot(pool["month"], pool["prepayments"] / 1e6,
        label="Prepayments")
ax.plot(pool["month"], pool["defaults"] / 1e6, label="Defaults")
ax.plot(pool["month"], pool["recoveries"] / 1e6,
        label="Recoveries")
ax.set_xlabel("Month")
ax.set_ylabel("£ million per month")
ax.set_title("Thamesbridge base case: pool cashflows")
ax.legend()
plt.savefig("figures/ch19_pool_cashflows.png")

# --- Listing 19.13 -----------------------------------
res = cashflow.run_waterfall(pool, deal, sonia_pct=3.0)
led = res["ledger"]
for c in res["tranche_loss"]:
    print(c, f"loss {res['tranche_loss'][c]:.2%}",
          "shortfall month", res["first_interest_shortfall"][c])
print(f"Largest PDL balance: £{led['pdl_balance'].max():,.0f}")

# --- Listing 19.14 -----------------------------------
reserve0 = deal["reserve_fund_target_pct"] * pool0
below = led.loc[led["reserve"] < reserve0 - 1, "month"]
a_paid = led.loc[led["bal_A"] < 1, "month"].min()
print(f"Reserve target: £{reserve0:,.0f}")
print(f"Lowest reserve: £{led['reserve'].min():,.0f}")
print("Below target from month", below.min())
print("Class A repaid in month", a_paid)

# --- Listing 19.15 -----------------------------------
cols = ["revenue", "fees", "int_A", "int_E", "pdl_cure",
        "residual"]
print((led.loc[[0, 29], cols] / 1e3).round(0).T)

# --- Listing 19.16 -----------------------------------
classes = [t["class"] for t in deal["tranches"]]
before = np.r_[reserve0, led["reserve"].iloc[:-1]]
int_cols = [f"int_{c}" for c in classes if c != "Z"]
ints = led[int_cols].sum(axis=1)
gap_rev = (led["revenue"] + before - led["fees"] - ints
           - led["pdl_cure"] - led["reserve"] - led["residual"])
notes = led[[f"bal_{c}" for c in classes]].sum(axis=1)
paid = np.r_[deal["pool_balance"], notes.iloc[:-1]] - notes
got = (pool["scheduled_principal"] + pool["prepayments"]
       + pool["recoveries"] + led["pdl_cure"])
print(f"Max revenue gap:   £{gap_rev.abs().max():.6f}")
print(f"Max principal gap: £{(paid - got).abs().max():.2f}")

# --- Listing 19.17 -----------------------------------
note_sum = sum(t["balance"] for t in deal["tranches"])
print(f"Notes minus pool: £{note_sum - pool0:.2f}")

# --- Listing 19.18 -----------------------------------
fig, ax = plt.subplots()
ax.stackplot(led["month"],
             [led[f"bal_{c}"] / 1e6 for c in classes],
             labels=[f"Class {c}" for c in classes])
ax.set_xlabel("Month")
ax.set_ylabel("£ million")
ax.set_title("Note balances: Class A is repaid first")
ax.legend(loc="upper right", ncol=2)
plt.savefig("figures/ch19_note_balances.png")

# --- Listing 19.19 -----------------------------------
print(f"{cashflow.cpr_to_smm(0.15):.3%}")
print(f"{1 - (1 - 0.015) ** 12:.2%}")

# --- Listing 19.20 -----------------------------------
one = pd.DataFrame({"month": [1], "opening_balance": [80e6],
    "defaults": [0], "scheduled_principal": [0],
    "prepayments": [0], "recoveries": [0], "losses": [5e5]})
deal2 = {**toy_deal, "tranches": [
    {"class": "A", "balance": 80e6, "margin_pct": 0.6},
    {"class": "B", "balance": 6e6, "margin_pct": 1.2},
    {"class": "Z", "balance": 4e6, "margin_pct": None}]}
r2 = cashflow.run_waterfall(one, deal2, 3.0, 3.0)["ledger"]
print(r2[["revenue", "fees", "int_A", "int_B", "pdl_cure",
          "reserve", "residual"]].T.round(0))

# --- Listing 19.21 -----------------------------------
p3 = cashflow.project_pool(200e6, 240, cum_default=0.12,
                           severity=0.40, cpr=0.10)
print(p3.loc[p3["month"] == 14, "defaults"].round(0).item())
print(p3.loc[p3["month"] == 29, "losses"].round(0).item())

# --- Listing 19.22 -----------------------------------
for lag in [6, 24]:
    p = cashflow.project_pool(deal["pool_balance"], term,
                              cum_default=base_df,
                              severity=base_ls, cpr=base_cpr,
                              recovery_lag=lag)
    lg = cashflow.run_waterfall(p, deal, 3.0)["ledger"]
    max_pdl = lg["pdl_balance"].max()
    resid = lg["residual"].sum() / 1e6
    print(f"lag {lag:2d}: max PDL £{max_pdl:,.0f}, "
          f"residual £{resid:,.1f} m")

# --- Listing 19.23 -----------------------------------
p5 = cashflow.project_pool(deal["pool_balance"], term,
                           cum_default=0.15, severity=0.35,
                           cpr=0.10)
r5 = cashflow.run_waterfall(p5, deal, sonia_pct=3.0)
l5 = r5["ledger"]
first_pdl = l5.loc[l5["pdl_balance"] > 1, "month"].min()
first_res = l5.loc[l5["reserve"] < reserve0 - 1, "month"].min()
print("First month with PDL:", first_pdl)
print("First month reserve below target:", first_res)
print(f"Max PDL £{l5['pdl_balance'].max() / 1e6:.1f} m")
for c, loss in r5["tranche_loss"].items():
    print(c, f"{loss:.2%}", end="  ")
print()

# --- Listing 19.24 -----------------------------------
# (not executed in the book)
# avail = revenue + reserve
# reserve = 0.0
# fees = min(avail, m["opening_balance"] * fee_rate)
# avail -= fees
# for c in classes:                     # A, B, C, D, E
#     if c == "Z":
#         continue
#     due = bal[c] * (sonia_pct + margin[c]) / 100 / 12 + short[c]
#     pay = min(avail, due)
#     avail -= pay
#     short[c] = due - pay              # unpaid interest carried
# pdl += m["losses"]
# cure = min(avail, pdl)
# avail -= cure
# pdl -= cure
# reserve = min(avail, reserve_target)
# avail -= reserve
# residual = avail
# prin = (m["scheduled_principal"] + m["prepayments"]
#         + m["recoveries"] + cure)
# for c in classes:                     # sequential principal
#     pay = min(prin, bal[c])
#     bal[c] -= pay
#     prin -= pay

# --- Listing 19.25 -----------------------------------
r = cashflow.run_waterfall(toy_pool, toy_deal, 3.0, 3.0)
print(round(r["ledger"].loc[0, "reserve"]),
      round(r["ledger"].loc[0, "bal_A"]))
