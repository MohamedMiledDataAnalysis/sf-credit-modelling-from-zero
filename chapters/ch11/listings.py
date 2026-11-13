"""
Roll-Rate Models

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch11/listings.py
"""

# --- Listing 11.1 ------------------------------------
import pandas as pd

february = (["C"] * 950) + (["30"] * 40) + (["PRE"] * 10)
moves = pd.DataFrame({"jan": "C", "feb": february})
print(moves["feb"].value_counts(normalize=True))

# --- Listing 11.2 ------------------------------------
import numpy as np

states = ["C", "30", "DEF"]
P_toy = pd.DataFrame(
    [[0.96, 0.04, 0.00],
     [0.50, 0.20, 0.30],
     [0.00, 0.00, 1.00]],
    index=states, columns=states)
print(P_toy)
print("Row sums:", P_toy.sum(axis=1).tolist())

# --- Listing 11.3 ------------------------------------
tape = pd.DataFrame({
    "loan_id": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
    "period": ["2020-01", "2020-02", "2020-03"] * 3,
    "status": ["C", "C", "30",
               "C", "30", "60",
               "C", "C", "PRE"]})
tape = tape.sort_values(["loan_id", "period"])
tape["prev_status"] = (tape.groupby("loan_id")["status"]
                       .shift(1))
print(tape)

# --- Listing 11.4 ------------------------------------
tape["prev_status"] = tape["prev_status"].fillna("C")
counts = pd.crosstab(tape["prev_status"], tape["status"])
print(counts)

# --- Listing 11.5 ------------------------------------
toy_matrix = counts.div(counts.sum(axis=1), axis=0)
print(toy_matrix.round(3))

# --- Listing 11.6 ------------------------------------
v = np.array([1000.0, 0.0, 0.0])
P = P_toy.to_numpy()
for month in [1, 2]:
    v = v @ P
    print(month, v.round(1))

# --- Listing 11.7 ------------------------------------
P12 = np.linalg.matrix_power(P, 12)
print((np.array([1.0, 0.0, 0.0]) @ P12).round(4))

# --- Listing 11.8 ------------------------------------
import matplotlib.pyplot as plt

v = np.array([1.0, 0.0, 0.0])
path = []
for month in range(61):
    path.append(v[2])          # share in DEF
    v = v @ P
print(f"After 24 months: {path[24]:.2%}")
print(f"After 60 months: {path[60]:.2%}")

plt.plot(range(61), [100 * x for x in path])
plt.xlabel("Months")
plt.ylabel("Cumulative default (%)")
plt.title("Toy pool: the default share only rises")
plt.savefig("figures/ch11_toy_cumulative.png")

# --- Listing 11.9 ------------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
perf = perf.sort_values(["loan_id", "period"])
perf["prev_status"] = (perf.groupby("loan_id")["status"]
                       .shift(1).fillna("C"))
print(perf.shape)
print(perf[["loan_id", "period", "prev_status",
            "status"]].head(4))

# --- Listing 11.10 -----------------------------------
STATES = ["C", "30", "60", "90", "DEF", "PRE"]
counts = pd.crosstab(perf["prev_status"], perf["status"])
counts = counts.reindex(index=STATES, columns=STATES,
                        fill_value=0)
print(counts)

# --- Listing 11.11 -----------------------------------
matrix = counts.astype(float)
for s in ["DEF", "PRE"]:
    matrix.loc[s] = 0.0
    matrix.loc[s, s] = 1.0
matrix = matrix.div(matrix.sum(axis=1), axis=0)
print(matrix.round(4))
print("Rows add to 1:", np.allclose(matrix.sum(axis=1), 1))

# --- Listing 11.12 -----------------------------------
P_real = matrix.to_numpy()
v = np.zeros(6)
v[0] = 1.0                       # all loans current
history = [v]
for month in range(60):
    v = v @ P_real
    history.append(v)
proj = pd.DataFrame(history, columns=STATES)
print(proj.loc[[12, 24, 60], ["C", "DEF", "PRE"]].round(4))

# --- Listing 11.13 -----------------------------------
n_loans = perf["loan_id"].nunique()
actual = (perf["status"] == "DEF").sum() / n_loans
print(f"Model, 60 months:  {proj.loc[60, 'DEF']:.2%}")
print(f"Actual, 60 months: {actual:.2%}")

# --- Listing 11.14 -----------------------------------
def matrix_for(df, year):
    sub = df[df["period"].str.startswith(year)]
    c = pd.crosstab(sub["prev_status"], sub["status"])
    c = c.reindex(index=STATES, columns=STATES,
                  fill_value=0).astype(float)
    for s in ["DEF", "PRE"]:
        c.loc[s] = 0.0
        c.loc[s, s] = 1.0
    return c.div(c.sum(axis=1), axis=0)

start = np.array([1.0, 0, 0, 0, 0, 0])
for year in ["2021", "2024"]:
    M = matrix_for(perf, year).to_numpy()
    v24 = start @ np.linalg.matrix_power(M, 24)
    print(year, f"24-month default: {v24[4]:.2%}")

# --- Listing 11.15 -----------------------------------
v = np.array([600.0, 400.0, 0.0])
for month in [1, 2]:
    v = v @ P_toy.to_numpy()
    print(month, v.round(2))

# --- Listing 11.16 -----------------------------------
bal_counts = pd.crosstab(perf["prev_status"], perf["status"],
                         values=perf["opening_balance"],
                         aggfunc="sum")
bal_counts = bal_counts.reindex(index=STATES, columns=STATES,
                                fill_value=0).fillna(0.0)
for s in ["DEF", "PRE"]:
    bal_counts.loc[s] = 0.0
    bal_counts.loc[s, s] = 1.0
bal_matrix = bal_counts.div(bal_counts.sum(axis=1), axis=0)
print(f"C to 30 by count:   {matrix.loc['C', '30']:.4%}")
print(f"C to 30 by balance: {bal_matrix.loc['C', '30']:.4%}")

# --- Listing 11.17 -----------------------------------
v60 = np.array([0, 0, 1.0, 0, 0, 0])
v12 = v60 @ np.linalg.matrix_power(P_real, 12)
print(f"Defaulted within 12 months: {v12[4]:.2%}")
print(f"Current after 12 months:    {v12[0]:.2%}")

# --- Listing 11.18 -----------------------------------
stressed = matrix.copy()
worse = [("C", "30"), ("30", "60"), ("60", "90"),
         ("90", "DEF")]
cures = {"30": ["C"], "60": ["C", "30"], "90": ["C", "60"]}
for a, b in worse:
    extra = stressed.loc[a, b] * 0.5
    stressed.loc[a, b] += extra
    if a == "C":
        stressed.loc["C", "C"] -= extra   # fewer stay current
    else:
        share = stressed.loc[a, cures[a]]
        stressed.loc[a, cures[a]] -= extra * share / share.sum()
print("Rows add to 1:", np.allclose(stressed.sum(axis=1), 1))
print("Smallest entry:", round(stressed.to_numpy().min(), 4))

# --- Listing 11.19 -----------------------------------
stressed = matrix.copy()
for a, b in worse:
    if a == "C":
        extra = stressed.loc[a, b] * 0.5
        stressed.loc["C", "C"] -= extra
    else:
        available = stressed.loc[a, cures[a]].sum()
        extra = min(stressed.loc[a, b] * 0.5, available)
        share = stressed.loc[a, cures[a]]
        stressed.loc[a, cures[a]] -= extra * share / available
    stressed.loc[a, b] += extra
print("Rows add to 1:", np.allclose(stressed.sum(axis=1), 1))
print("Smallest entry:", round(stressed.to_numpy().min(), 4))
print(stressed.loc["90"].round(4).to_string())
for name, M in [("base", matrix), ("stressed", stressed)]:
    v24 = start @ np.linalg.matrix_power(M.to_numpy(), 24)
    print(f"{name:9s} 24-month default: {v24[4]:.2%}")

# --- Listing 11.20 -----------------------------------
# (not executed in the book)
# STATES = ["C", "30", "60", "90", "DEF", "PRE"]
# ABSORBING = ["DEF", "PRE"]

# def transition_matrix(perf, periods=None):
#     counts = transition_counts(perf, periods).astype(float)
#     for s in STATES:
#         if s in ABSORBING or counts.loc[s].sum() == 0:
#             counts.loc[s] = 0.0
#             counts.loc[s, s] = 1.0
#     return counts.div(counts.sum(axis=1), axis=0)

# --- Listing 11.21 -----------------------------------
from sfrating import rollrate
M = rollrate.transition_matrix(perf)
print(f"{rollrate.cumulative_default_rate(M, 60):.2%}")
