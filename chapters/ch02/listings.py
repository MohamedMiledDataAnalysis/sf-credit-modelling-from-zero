"""
One Securitisation Deal, End to End

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch02/listings.py
"""

# --- Listing 02.1 ------------------------------------
import json

with open("data/rmbs_deal.json") as f:
    deal = json.load(f)
print(deal["deal_name"])
print(f"Pool balance: £{deal['pool_balance'] / 1e6:,.1f} m")
print("Principal paid:", deal["principal_waterfall"])

# --- Listing 02.2 ------------------------------------
for t in deal["tranches"]:
    margin = t["margin_pct"]
    margin_text = "none" if margin is None else f"{margin:.2f}%"
    size = t["balance"] / 1e6
    print(f"{t['class']}  {t['share_of_pool']:6.1%}  "
          f"£{size:8,.1f} m  margin {margin_text}")

# --- Listing 02.3 ------------------------------------
reserve = deal["reserve_fund_target_pct"]
below = 1.0
for t in deal["tranches"]:
    below = below - t["share_of_pool"]
    ce = below + reserve
    print(f"{t['class']}: subordination {below:6.2%}, "
          f"CE {ce:6.2%}")

# --- Listing 02.4 ------------------------------------
def pay_in_order(available, items):
    paid = {}
    for name, due in items:
        payment = min(available, due)
        paid[name] = payment
        available = available - payment
    return paid, available

# --- Listing 02.5 ------------------------------------
items = [("fees", 15_000), ("int A", 220_000),
         ("int B", 15_000), ("int C", 15_000),
         ("int D", 15_000), ("int E", 10_000),
         ("loss cover", 150_000), ("reserve", 1_500_000)]
paid, residual = pay_in_order(300_000 + 1_500_000, items)
for name, amount in paid.items():
    print(f"{name:11s} £{amount:>11,.0f}")
print(f"{'residual':11s} £{residual:>11,.0f}")

# --- Listing 02.6 ------------------------------------
def allocate_loss(pool_loss, tranches):
    remaining = pool_loss
    class_loss = {}
    for t in reversed(tranches):
        absorbed = min(remaining, t["share_of_pool"])
        class_loss[t["class"]] = absorbed / t["share_of_pool"]
        remaining = remaining - absorbed
    return class_loss

# --- Listing 02.7 ------------------------------------
names = [t["class"] for t in deal["tranches"]]
print("Pool loss " + "".join(f"{c:>8s}" for c in names))
for pool_loss in [0.02, 0.05, 0.10, 0.15]:
    lost = allocate_loss(pool_loss, deal["tranches"])
    row = "".join(f"{lost[c]:8.0%}" for c in names)
    print(f"{pool_loss:9.0%} {row}")

# --- Listing 02.8 ------------------------------------
pool = deal["pool_balance"]
below = 1.0
ce_by_class = {}
for t in deal["tranches"]:
    below = below - t["share_of_pool"]
    ce = below + reserve
    ce_by_class[t["class"]] = ce
    print(f"{t['class']}  size £{t['balance'] / 1e6:7,.1f} m  "
          f"CE {ce:6.2%} = £{ce * pool / 1e6:6.1f} m")

# --- Listing 02.9 ------------------------------------
import pandas as pd

defaults = pd.read_csv("data/rmbs_defaults.csv")
realised = defaults["loss"].sum() / pool
print(f"Realised five-year loss: {realised:.3%} of the pool")

# --- Listing 02.10 -----------------------------------
for name, ce in ce_by_class.items():
    print(f"{name}: withstands {ce / realised:5.1f} x the "
          f"realised loss")

# --- Listing 02.11 -----------------------------------
month = [("fees", 15_000), ("int A", 220_000),
         ("int B", 15_000), ("int C", 15_000),
         ("int D", 15_000), ("int E", 10_000),
         ("loss cover", 400_000), ("reserve", 1_500_000)]
paid, residual = pay_in_order(100_000 + 1_500_000, month)
print(f"Reserve fund at month end: £{paid['reserve']:,.0f}")
print(f"Residual: £{residual:,.0f}")

# --- Listing 02.12 -----------------------------------
total = 0.0
for t in deal["tranches"]:
    total = total + t["balance"]
print(f"Sum of classes: £{total:,.2f}")
print(f"Pool balance:   £{deal['pool_balance']:,.2f}")
print(f"Difference:     £{total - deal['pool_balance']:,.2f}")

# --- Listing 02.13 -----------------------------------
principal = 50_000_000
pool_after = pool - principal
for rule in ["sequential", "pro rata"]:
    if rule == "sequential":
        to_a = min(principal, deal["tranches"][0]["balance"])
    else:
        to_a = principal * deal["tranches"][0]["share_of_pool"]
    a_after = deal["tranches"][0]["balance"] - to_a
    sub_a = (pool_after - a_after) / pool_after
    print(f"{rule:10s} A receives £{to_a / 1e6:5.1f} m, "
          f"A subordination {sub_a:.2%}")

# --- Listing 02.14 -----------------------------------
no_reserve = allocate_loss(0.07, deal["tranches"])["C"]
with_reserve = allocate_loss(0.07 - reserve,
                             deal["tranches"])["C"]
print(f"Class C loss, no reserve fund:   {no_reserve:.1%}")
print(f"Class C loss, with reserve fund: {with_reserve:.1%}")

# --- Listing 02.15 -----------------------------------
# (not executed in the book)
# import json

# with open("data/rmbs_deal.json") as f:
#     deal = json.load(f)

# reserve = deal["reserve_fund_target_pct"]
# below = 1.0
# for t in deal["tranches"]:
#     below = below - t["share_of_pool"]
#     print(f"{t['class']}  size {t['share_of_pool']:6.2%}  "
#           f"CE {below + reserve:6.2%}")
