"""
ABS: Auto Loans and Credit Cards

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch17/listings.py
"""

# --- Listing 17.1 ------------------------------------
import numpy as np
import pandas as pd

tri = pd.DataFrame({6: [0.8, 0.9, 1.0],
                    12: [2.0, 2.2, 2.4],
                    18: [3.0, 3.3, np.nan],
                    24: [3.6, np.nan, np.nan]},
                   index=["V1", "V2", "V3"])
cols = list(tri.columns)
for a, b in zip(cols[:-1], cols[1:]):
    both = tri[a].notna() & tri[b].notna()
    factor = tri.loc[both, b].sum() / tri.loc[both, a].sum()
    tri[b] = tri[b].fillna(tri[a] * factor)
print(tri.round(2))

# --- Listing 17.2 ------------------------------------
auto = pd.read_csv("data/auto_loans.csv")
print(auto.shape)
print(auto["outcome"].value_counts().to_string())
print(auto[["product", "vehicle", "months_observed",
            "outcome"]].head(3))

# --- Listing 17.3 ------------------------------------
from sfrating import abs_auto

curve = abs_auto.cumulative_default_curve(auto, horizon=60)
print(curve.iloc[[11, 23, 35, 47, 59]].round(4).to_string())

# --- Listing 17.4 ------------------------------------
import matplotlib.pyplot as plt

for vehicle, group in auto.groupby("vehicle"):
    c = abs_auto.cumulative_default_curve(group, horizon=48)
    plt.plot(c["month"], c["cumulative_default"] * 100,
             label=vehicle)
plt.xlabel("Months on book")
plt.ylabel("Cumulative default (%)")
plt.title("Used-car agreements default more often")
plt.legend()
plt.savefig("figures/ch17_new_used_curves.png")

# --- Listing 17.5 ------------------------------------
trusted = curve[(curve["month"] >= 25) & (curve["month"] <= 36)]
hazard = trusted["defaults"].sum() / trusted["at_risk"].sum()
s36 = 1 - curve.loc[curve["month"] == 36,
                    "cumulative_default"].item()
cd48_extended = 1 - s36 * (1 - hazard) ** 12
cd48_observed = curve.loc[curve["month"] == 48,
                          "cumulative_default"].item()
print(f"Monthly hazard, months 25-36: {hazard:.4%}")
print(f"CD(48) extended from month 36: {cd48_extended:.2%}")
print(f"CD(48) observed (907 at risk): {cd48_observed:.2%}")

# --- Listing 17.6 ------------------------------------
stresses = pd.read_csv("data/rating_stresses.csv")
base = abs_auto.base_case_loss(0.14, 0.50)
for _, row in stresses.head(3).iterrows():
    loss = abs_auto.stressed_loss(base,
                                  row["default_multiple"])
    print(f"{row['rating']:4s} x{row['default_multiple']:.1f}"
          f" -> {loss:.1%}")

# --- Listing 17.7 ------------------------------------
def simulate_cards(n_accounts=20_000, months=24, apr=0.22,
                   pd_month=0.004, pay_scale=1.0, seed=17):
    rng = np.random.default_rng(seed)
    balance = rng.lognormal(np.log(1_500), 0.8, n_accounts)
    pay_share = rng.beta(2, 10, n_accounts) * pay_scale
    closed = np.zeros(n_accounts, dtype=bool)
    rows = []
    for month in range(1, months + 1):
        opening = balance.sum()
        interest = balance * apr / 12
        default = ~closed & (rng.random(n_accounts) < pd_month)
        closed = closed | default
        payment = interest + pay_share * balance
        spend = rng.exponential(250, n_accounts)
        rows.append((month, opening, interest[~closed].sum(),
                     payment[~closed].sum(),
                     balance[default].sum()))
        balance = np.where(closed, 0.0,
                           balance + interest - payment + spend)
    return pd.DataFrame(rows, columns=["month", "opening",
                        "finance", "collections", "charge_off"])

# --- Listing 17.8 ------------------------------------
def card_measures(sim, coupon=0.05, servicing=0.02):
    out = pd.DataFrame({"month": sim["month"]})
    out["yield"] = sim["finance"] * 12 / sim["opening"]
    out["charge_off"] = sim["charge_off"] * 12 / sim["opening"]
    out["payment_rate"] = sim["collections"] / sim["opening"]
    out["excess"] = (out["yield"] - out["charge_off"]
                     - coupon - servicing)
    return out

base_cards = card_measures(simulate_cards())
print(base_cards.iloc[[0, 11, 23]].round(4).to_string())
print(base_cards.drop(columns="month").mean().round(4)
      .to_string())

# --- Listing 17.9 ------------------------------------
def extended_cd(df, last_trusted=36, target=48, window=12):
    c = abs_auto.cumulative_default_curve(df, horizon=target)
    first = last_trusted - window + 1
    part = c[(c["month"] >= first)
             & (c["month"] <= last_trusted)]
    h = part["defaults"].sum() / part["at_risk"].sum()
    s = 1 - c.loc[c["month"] == last_trusted,
                  "cumulative_default"].item()
    return 1 - s * (1 - h) ** (target - last_trusted)

cd = auto.groupby("vehicle").apply(extended_cd,
                                   include_groups=False)
print(cd.round(4).to_string())

# --- Listing 17.10 -----------------------------------
defaulted = auto[auto["default"] == 1]
recovery = defaulted.groupby("vehicle").apply(
    lambda g: np.average(g["recovery_rate_if_default"],
                         weights=g["amount_financed"]),
    include_groups=False)
print(recovery.round(4).to_string())

# --- Listing 17.11 -----------------------------------
seg = pd.DataFrame({"cd_48m": cd, "recovery": recovery})
seg["base_cnl"] = abs_auto.base_case_loss(seg["cd_48m"],
                                          seg["recovery"])
seg["weight"] = (auto.groupby("vehicle")["amount_financed"]
                 .sum() / auto["amount_financed"].sum())
pool_base = (seg["base_cnl"] * seg["weight"]).sum()
print(seg.round(4).to_string())
print(f"Pool base-case CNL: {pool_base:.2%}")

# --- Listing 17.12 -----------------------------------
stresses["loss"] = [abs_auto.stressed_loss(pool_base, m)
                    for m in stresses["default_multiple"]]
print(stresses[["rating", "default_multiple",
                "loss"]].round(4).to_string(index=False))

# --- Listing 17.13 -----------------------------------
stress_cards = card_measures(simulate_cards(
    apr=0.18, pd_month=0.012, pay_scale=0.7))
months = base_cards["month"]
plt.figure()
plt.plot(months, base_cards["excess"] * 100, label="Base")
plt.plot(months, stress_cards["excess"] * 100,
         label="Stress")
plt.axhline(0, color="#B03A2E", linewidth=1)
plt.xlabel("Month")
plt.ylabel("Excess spread (% a year)")
plt.title("Stress turns the card pool's excess spread negative")
plt.legend()
plt.savefig("figures/ch17_card_excess.png")
print(stress_cards.drop(columns="month").mean().round(4)
      .to_string())
three_month = stress_cards["excess"].rolling(3).mean()
trigger = stress_cards.loc[three_month < 0, "month"].min()
print("Months with negative excess:",
      (stress_cards["excess"] < 0).sum(), "of 24")
print("Early amortisation trigger hit in month", trigger)

# --- Listing 17.14 -----------------------------------
tri2 = pd.DataFrame({12: [1.5, 1.8, 2.0],
                     24: [2.7, 3.0, np.nan],
                     36: [3.24, np.nan, np.nan]},
                    index=["V1", "V2", "V3"])
for a, b in [(12, 24), (24, 36)]:
    both = tri2[a].notna() & tri2[b].notna()
    f = tri2.loc[both, b].sum() / tri2.loc[both, a].sum()
    tri2[b] = tri2[b].fillna(tri2[a] * f)
print(tri2.round(2))

# --- Listing 17.15 -----------------------------------
for product, group in auto.groupby("product"):
    c = abs_auto.cumulative_default_curve(group, horizon=48)
    cd36 = c.loc[c["month"] == 36, "cumulative_default"].item()
    cd48 = c.loc[c["month"] == 48, "cumulative_default"].item()
    print(f"{product}: CD(36) {cd36:.2%}, CD(48) {cd48:.2%}")

# --- Listing 17.16 -----------------------------------
for mult in [1.5, 2.0, 2.5, 3.0]:
    m = card_measures(simulate_cards(pd_month=0.004 * mult))
    print(f"x{mult}: charge-off {m['charge_off'].mean():.2%},"
          f" excess {m['excess'].mean():.2%}")

# --- Listing 17.17 -----------------------------------
t = auto["months_observed"].to_numpy()
is_def = auto["default"].to_numpy() == 1
is_exit = auto["outcome"].to_numpy() != "censored"
s_all, ci = 1.0, 0.0
for m in range(1, 49):
    at_risk = (t >= m).sum()
    defaults = ((t == m) & is_def).sum()
    exits = ((t == m) & is_exit).sum()
    ci += s_all * defaults / at_risk
    s_all *= 1 - exits / at_risk
print(f"Cumulative incidence, 48m: {ci:.2%}")
print(f"Kaplan-Meier CD, 48m:      {cd48_observed:.2%}")

# --- Listing 17.18 -----------------------------------
# (not executed in the book)
# def cumulative_default_curve(auto, horizon=60):
#     t = auto["months_observed"].to_numpy()
#     e = auto["default"].to_numpy()
#     surv = 1.0
#     rows = []
#     for m in range(1, horizon + 1):
#         at_risk = (t >= m).sum()
#         d = ((t == m) & (e == 1)).sum()
#         if at_risk > 0:
#             surv *= 1 - d / at_risk
#         rows.append((m, int(at_risk), int(d), 1 - surv))
#     return pd.DataFrame(rows, columns=[
#         "month", "at_risk", "defaults", "cumulative_default"])

# def base_case_loss(cum_default, recovery):
#     return cum_default * (1 - recovery)

# def stressed_loss(base_loss, multiple):
#     return base_loss * multiple

# --- Listing 17.19 -----------------------------------
toy = pd.DataFrame({
    "months_observed": [1] * 10 + [2] * 3 + [3] * 87,
    "default": [1] * 2 + [0] * 8 + [1] * 3 + [0] * 87})
toy_curve = abs_auto.cumulative_default_curve(toy, 2)
print(toy_curve.round(4).to_string(index=False))
