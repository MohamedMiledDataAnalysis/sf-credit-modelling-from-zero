"""
CMBS

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch16/listings.py
"""

# --- Listing 16.1 ------------------------------------
import numpy as np
import pandas as pd

def property_value(noi, cap_rate):
    """Value = NOI / cap rate (cap rate as a decimal)."""
    return noi / cap_rate

for cap in [0.05, 0.06, 0.07, 0.08]:
    value = property_value(1_200_000, cap)
    print(f"cap rate {cap:.0%}: value £{value / 1e6:.2f}m")

# --- Listing 16.2 ------------------------------------
cmbs_df = pd.read_csv("data/cmbs_loans.csv")
debt_service = (cmbs_df["loan_balance"]
                * cmbs_df["interest_rate"] / 100)
my_dscr = cmbs_df["noi"] / debt_service
print(cmbs_df.shape)
print(cmbs_df[["loan_id", "property_type", "ltv",
               "dscr"]].head(3))
print("Largest gap with file DSCR:",
      round((my_dscr - cmbs_df["dscr"]).abs().max(), 3))

# --- Listing 16.3 ------------------------------------
outcomes = cmbs_df[["term_default",
                    "maturity_default"]].sum()
print(outcomes)
print("Term years:",
      cmbs_df["term_years"].value_counts().to_dict())
print("Lowest DSCR at origination:", cmbs_df["dscr"].min())

# --- Listing 16.4 ------------------------------------
cmbs_df["cap_rate"] = (cmbs_df["noi"]
                       / cmbs_df["property_value"])
by_type = cmbs_df.groupby("property_type").agg(
    loans=("loan_id", "size"),
    balance_m=("loan_balance", "sum"),
    cap_rate=("cap_rate", "mean"),
    maturity_def=("maturity_default", "sum"))
by_type["balance_m"] = (by_type["balance_m"] / 1e6).round(1)
by_type["cap_rate"] = (by_type["cap_rate"] * 100).round(2)
print(by_type)

# --- Listing 16.5 ------------------------------------
def stressed_value(noi, cap_rate, haircut, cap_shift):
    """Value after an NOI haircut and a cap rate shift."""
    return noi * (1 - haircut) / (cap_rate + cap_shift)

v_s = stressed_value(1_200_000, 0.06, 0.10, 0.01)
print(f"Stressed value: £{v_s / 1e6:.2f}m")
print(f"Fall in value: {1 - v_s / 20_000_000:.1%}")

# --- Listing 16.6 ------------------------------------
def refinances(balance, noi, cap_rate, haircut, cap_shift,
               refi_rate=0.065, max_ltv=0.80, min_dscr=1.25):
    value = stressed_value(noi, cap_rate, haircut, cap_shift)
    ltv = balance / value
    cover = noi * (1 - haircut) / (balance * refi_rate)
    return ltv, cover, (ltv <= max_ltv) and (cover >= min_dscr)

ltv, cover, ok = refinances(13e6, 1.2e6, 0.06, 0.10, 0.01)
print(f"LTV {ltv:.1%}, DSCR {cover:.2f}, refinances: {ok}")

# --- Listing 16.7 ------------------------------------
def loss_severity(balance, value_s, cost_share=0.15):
    recovery = (1 - cost_share) * value_s
    return np.maximum(0.0, 1 - recovery / balance)

print(loss_severity(13e6, np.array([15.43e6, 12e6])).round(3))

# --- Listing 16.8 ------------------------------------
weights = (cmbs_df["loan_balance"]
           / cmbs_df["loan_balance"].sum())
herfindahl = (weights ** 2).sum()
print(f"Herfindahl index: {herfindahl:.4f}")
print(f"Effective number of loans: {1 / herfindahl:.1f}")
top10 = weights.sort_values(ascending=False).head(10).sum()
print(f"Share of the ten largest loans: {top10:.1%}")

# --- Listing 16.9 ------------------------------------
import matplotlib.pyplot as plt

sorted_w = weights.sort_values(ascending=False).to_numpy()
cum_share = np.cumsum(sorted_w) * 100
rank = np.arange(1, len(sorted_w) + 1)
plt.plot(rank, cum_share, label="Our pool")
plt.plot(rank, rank / len(rank) * 100, linestyle="--",
         label="120 equal loans")
plt.xlabel("Number of loans, largest first")
plt.ylabel("Share of pool balance (%)")
plt.title("A few large loans carry much of the pool")
plt.legend(loc="lower right")
plt.savefig("figures/ch16_concentration.png")

# --- Listing 16.10 -----------------------------------
from sfrating import cmbs

bal = cmbs_df["loan_balance"]
total = bal.sum()
wa_ltv = (cmbs_df["ltv"] * bal).sum() / total
wa_dscr = (cmbs_df["dscr"] * bal).sum() / total
print(f"Loans: {len(cmbs_df)}, balance £{total / 1e6:,.1f}m")
print(f"WA LTV {wa_ltv:.1f}%, WA DSCR {wa_dscr:.2f}")
print(f"Largest loan: {bal.max() / total:.2%} of the pool")

# --- Listing 16.11 -----------------------------------
scenarios = {"BBB": (0.10, 0.005), "AAA": (0.20, 0.010)}
COST_SHARE = 0.15

# --- Listing 16.12 -----------------------------------
results = {}
for name, (haircut, shift) in scenarios.items():
    test = cmbs.refinance_test(bal, cmbs_df["noi"],
                               cmbs_df["cap_rate"] + shift,
                               noi_haircut=haircut)
    fails = ~test["refinances"].to_numpy()
    sev = loss_severity(bal.to_numpy(),
                        test["stressed_value"].to_numpy(),
                        COST_SHARE)
    loss = bal.to_numpy() * sev * fails
    results[name] = (fails, loss)
    print(f"{name}: {fails.sum()} loans fail, "
          f"{bal[fails].sum() / total:.1%} of balance")
    print(f"     {(loss > 0).sum()} loans lose money, "
          f"pool loss {loss.sum() / total:.2%}")

# --- Listing 16.13 -----------------------------------
fails, loss = results["AAA"]
table = pd.DataFrame({"type": cmbs_df["property_type"],
                      "balance": bal, "fail_bal": bal * fails,
                      "loss": loss})
by = table.groupby("type").sum()
by["fail_share"] = (by["fail_bal"] / by["balance"]).round(3)
by["loss_share"] = (by["loss"] / by["balance"]).round(3)
print(by[["fail_share", "loss_share"]])

# --- Listing 16.14 -----------------------------------
check = cmbs.refinance_test(bal,
                            cmbs_df["noi_after_stress_period"],
                            cmbs_df["cap_rate"] + 0.005,
                            noi_haircut=0.0)
print(pd.crosstab(check["refinances"],
                  cmbs_df["maturity_default"],
                  rownames=["passes test"],
                  colnames=["maturity default"]))

# --- Listing 16.15 -----------------------------------
noi = 4.0e6 - 0.8e6
value = property_value(noi, 0.08)
print(f"Value £{value / 1e6:.1f}m, LTV {26e6 / value:.0%}")
print(f"DSCR {noi / (26e6 * 0.055):.2f}, "
      f"debt yield {noi / 26e6:.1%}")

# --- Listing 16.16 -----------------------------------
haircut, shift = scenarios["BBB"]
low_rate = cmbs.refinance_test(bal, cmbs_df["noi"],
                               cmbs_df["cap_rate"] + shift,
                               noi_haircut=haircut,
                               refi_rate=0.055)
fail_low = ~low_rate["refinances"]
print(f"{fail_low.sum()} loans fail, "
      f"{bal[fail_low].sum() / total:.1%} of balance")
print("Fail LTV test:", (low_rate["stressed_ltv"] > 0.8).sum())
print("Fail DSCR test:", (low_rate["refi_dscr"] < 1.25).sum())

# --- Listing 16.17 -----------------------------------
def effective_number(balances):
    w = balances / balances.sum()
    return 1 / (w ** 2).sum()

eff = cmbs_df.groupby("property_type")["loan_balance"].agg(
    ["size", effective_number])
eff["ratio"] = eff["effective_number"] / eff["size"]
print(eff.round(3))

# --- Listing 16.18 -----------------------------------
shifts = np.arange(0, 0.0201, 0.0005)
shares = []
for s in shifts:
    t = cmbs.refinance_test(bal, cmbs_df["noi"],
                            cmbs_df["cap_rate"] + s,
                            noi_haircut=0.10)
    shares.append(bal[~t["refinances"]].sum() / total)
shares = np.array(shares)
first = shifts[np.argmax(shares > 0.75)]
print(f"First shift above 75%: {first * 100:.2f} points")
print(f"Failing share there: {shares[shares > 0.75][0]:.1%}")

# --- Listing 16.19 -----------------------------------
# (not executed in the book)
# def stressed_value(noi, cap_rate, noi_haircut=0.0):
#     """Property value = stressed NOI / stressed cap rate."""
#     return (np.asarray(noi, dtype=float) * (1 - noi_haircut)
#             / np.asarray(cap_rate, dtype=float))

# def refinance_test(balance, noi, cap_rate, noi_haircut=0.10,
#                    refi_rate=0.065, max_ltv=0.80,
#                    min_dscr=1.25) -> pd.DataFrame:
#     value = stressed_value(noi, cap_rate, noi_haircut)
#     noi_s = np.asarray(noi, dtype=float) * (1 - noi_haircut)
#     ltv = np.asarray(balance, dtype=float) / value
#     cover = noi_s / (np.asarray(balance, dtype=float)
#                      * refi_rate)
#     return pd.DataFrame({
#         "stressed_value": value, "stressed_ltv": ltv,
#         "refi_dscr": cover,
#         "refinances": (ltv <= max_ltv) & (cover >= min_dscr)})

# --- Listing 16.20 -----------------------------------
row = cmbs.refinance_test([13e6], [1.2e6], [0.07],
                          noi_haircut=0.10)
print(row[["stressed_ltv", "refi_dscr",
           "refinances"]].round(3).to_string())
