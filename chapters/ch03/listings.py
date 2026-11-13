"""
Python from Zero for Quants

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch03/listings.py
"""

# --- Listing 03.1 ------------------------------------
print(200000 * 0.03)

# --- Listing 03.2 ------------------------------------
balance = 200000       # pounds outstanding
annual_rate = 0.03     # 3% a year, written as a decimal
yearly_interest = balance * annual_rate
print(yearly_interest)

# --- Listing 03.3 ------------------------------------
balance = balance - 5000   # a repayment of £5,000
print(balance)

# --- Listing 03.4 ------------------------------------
monthly_rate = annual_rate / 12
print(monthly_rate)
print((1 + monthly_rate) ** 12)
print(type(360), type(monthly_rate))

# --- Listing 03.5 ------------------------------------
loan_id = "TB000001"
region = "Wales"
print(loan_id, "is in", region)

# --- Listing 03.6 ------------------------------------
balance = 195000
monthly_rate = 0.0025
print(f"Loan {loan_id}: balance £{balance:,.2f}")
print(f"Monthly rate {monthly_rate:.2%}")

# --- Listing 03.7 ------------------------------------
balances = [150000, 220000, 95000, 310000]
print(len(balances))
print(balances[0], balances[3])
print(sum(balances))

# --- Listing 03.8 ------------------------------------
loan = {"loan_id": "TB000001",
        "balance": 76371.26,
        "annual_rate": 0.0163,
        "months_left": 236}
print(loan["balance"])
loan["region"] = "East of England"
print(len(loan), "region" in loan)

# --- Listing 03.9 ------------------------------------
ltv = 92.0
if ltv > 90:
    band = "above 90%"
elif ltv > 75:
    band = "75% to 90%"
else:
    band = "75% or below"
print(band)

# --- Listing 03.10 -----------------------------------
total = 0
for b in balances:
    total = total + b
print(total)

# --- Listing 03.11 -----------------------------------
balance = 1000.0
for month in range(1, 4):
    interest = balance * 0.0025
    balance = balance + interest
    print(f"Month {month}: interest {interest:.4f}, "
          f"balance {balance:.4f}")

# --- Listing 03.12 -----------------------------------
def monthly_payment(balance, annual_rate, months):
    """Level payment that repays `balance` in `months`."""
    r = annual_rate / 12
    return balance * r / (1 - (1 + r) ** (-months))

print(round(monthly_payment(1000, 0.12, 2), 2))
print(round(monthly_payment(200000, 0.03, 300), 2))

# --- Listing 03.13 -----------------------------------
def payment(balance, annual_rate, months, repayment_type):
    if repayment_type == "Interest-only":
        return balance * annual_rate / 12
    return monthly_payment(balance, annual_rate, months)

print(round(payment(131400, 0.0266, 292, "Interest-only"), 2))

# --- Listing 03.14 -----------------------------------
import traceback
try:
    rate = 0.03
    print(200000 * rte)
except NameError:
    print(traceback.format_exc())

# --- Listing 03.15 -----------------------------------
import math
print(math.sqrt(0.04), math.log(1.03))

# --- Listing 03.16 -----------------------------------
import numpy as np

balances = np.array([150000, 220000, 95000, 310000])
rates = np.array([0.0163, 0.0179, 0.0266, 0.0210])
monthly_interest = balances * rates / 12
print(monthly_interest.round(2))

# --- Listing 03.17 -----------------------------------
print(np.sum(balances), np.mean(balances))
print(round(np.std(balances), 2))
print(np.max(rates), np.argmax(rates))

# --- Listing 03.18 -----------------------------------
high_rate = rates > 0.02
print(high_rate)
print(balances[high_rate])
print(f"{np.sum(balances[high_rate]) / np.sum(balances):.2%}")

# --- Listing 03.19 -----------------------------------
rng = np.random.default_rng(42)
print(rng.uniform(0, 1, size=4).round(4))
rng = np.random.default_rng(42)
print(rng.uniform(0, 1, size=4).round(4))

# --- Listing 03.20 -----------------------------------
rng = np.random.default_rng(7)
draws = rng.uniform(0, 1, size=10000)
defaults = draws < 0.02
print(np.sum(defaults), f"{np.mean(defaults):.2%}")

# --- Listing 03.21 -----------------------------------
B, annual_rate, n = 200000.0, 0.03, 300
r = annual_rate / 12
M = monthly_payment(B, annual_rate, n)

balance = B
closing = []
interest_paid = []
for month in range(1, n + 1):
    interest = balance * r
    principal = M - interest
    balance = balance - principal
    closing.append(balance)
    interest_paid.append(interest)
print(f"Payment £{M:,.2f}")
print(f"After 12 months £{closing[11]:,.2f}")
print(f"Final balance £{abs(closing[-1]):.6f}")
print(f"Total interest £{sum(interest_paid):,.2f}")

# --- Listing 03.22 -----------------------------------
k = np.arange(1, n + 1)             # 1, 2, ..., 300
growth = (1 + r) ** k
closing_np = B * growth - M * (growth - 1) / r
gap = np.max(np.abs(closing_np - np.array(closing)))
print(f"After 12 months £{closing_np[11]:,.2f}")
print(f"Largest gap loop vs formula: £{gap:.8f}")

# --- Listing 03.23 -----------------------------------
import matplotlib.pyplot as plt

interest_np = np.concatenate(([B], closing_np[:-1])) * r
principal_np = M - interest_np
plt.plot(k / 12, interest_np, label="Interest")
plt.plot(k / 12, principal_np, label="Principal")
plt.xlabel("Years since start")
plt.ylabel("£ per month")
plt.title("Each payment shifts from interest to principal")
plt.legend()
plt.savefig("figures/ch03_payment_split.png")
print(f"Interest, first month £{interest_np[0]:.2f}")
print(f"Interest, last month  £{interest_np[-1]:.2f}")

# --- Listing 03.24 -----------------------------------
import pandas as pd

loans = pd.read_csv("data/rmbs_loans.csv")
perf = pd.read_csv("data/rmbs_performance.csv.gz")
jan = perf[perf["period"] == "2020-01"]
print(len(loans), len(jan))
same_order = np.array_equal(loans["loan_id"].to_numpy(),
                            jan["loan_id"].to_numpy())
print("Same loan order:", same_order)

# --- Listing 03.25 -----------------------------------
B = loans["current_balance"].to_numpy()
rate = loans["interest_rate"].to_numpy() / 100   # % to decimal
n = loans["remaining_term_months"].to_numpy()
is_io = loans["repayment_type"].to_numpy() == "Interest-only"
print(f"Interest-only loans: {np.sum(is_io)}")

# --- Listing 03.26 -----------------------------------
repay_pay = monthly_payment(B, rate, n)
io_pay = B * rate / 12
our_payment = np.where(is_io, io_pay, repay_pay)
print(our_payment[:3].round(2))
print(f"Pool total £{np.sum(our_payment):,.2f} per month")

# --- Listing 03.27 -----------------------------------
servicer = jan["scheduled_payment"].to_numpy()
diff = np.abs(our_payment - servicer)
print(f"Largest difference: £{np.max(diff):.4f}")
print("Loans differing by over 1p:", np.sum(diff > 0.01))

# --- Listing 03.28 -----------------------------------
end_year = loans["product_end_date"].str[:4].to_numpy()
resets = end_year == "2020"
new_rate = np.where(resets, rate + 0.02, rate)
new_repay = monthly_payment(B, new_rate, n)
new_payment = np.where(is_io, B * new_rate / 12, new_repay)
extra = np.sum(new_payment) - np.sum(our_payment)
print(f"Loans resetting: {np.sum(resets)}")
print(f"Extra per month: £{extra:,.0f}")
print(f"Rise: {extra / np.sum(our_payment):.1%}")

# --- Listing 03.29 -----------------------------------
# (not executed in the book)
# balances = [100, 200, 300, 400]
# for i in range(3):
#     print(i, balances[i] * 2)

# --- Listing 03.30 -----------------------------------
balances_list = [100, 200, 300, 400]
try:
    for i in range(5):
        print(i, balances_list[i] * 2)
except IndexError as err:
    print("IndexError:", err)

# --- Listing 03.31 -----------------------------------
print(round(monthly_payment(12000, 0.06, 12), 2))

# --- Listing 03.32 -----------------------------------
def total_interest(balance, annual_rate, months):
    m = monthly_payment(balance, annual_rate, months)
    return months * m - balance

for years in [25, 35]:
    t = total_interest(200000, 0.03, years * 12)
    m = monthly_payment(200000, 0.03, years * 12)
    print(f"{years} years: payment £{m:,.2f}, "
          f"interest £{t:,.0f}")

# --- Listing 03.33 -----------------------------------
io_share = np.sum(B[is_io]) / np.sum(B)
wa_rate = np.sum(B * rate) / np.sum(B)
print(f"Interest-only share of balance: {io_share:.2%}")
print(f"Weighted average rate: {wa_rate:.3%}")
print(f"Plain average rate:    {np.mean(rate):.3%}")
print("Loans at 2.5% or more:", np.sum(rate >= 0.025))

# --- Listing 03.34 -----------------------------------
r, n = 0.03 / 12, 300
exact = 900 * (1 - (1 + r) ** (-n)) / r
print(f"Formula: £{exact:,.2f}")

loan_size = 100000
while monthly_payment(loan_size + 100, 0.03, n) <= 900:
    loan_size = loan_size + 100
print(f"Search:  £{loan_size:,}")

# --- Listing 03.35 -----------------------------------
# (not executed in the book)
# assert round(monthly_payment(1000, 0.12, 2), 2) == 507.51
# assert abs(closing_np[-1]) < 1e-6        # schedule ends at 0
# assert np.max(diff) < 0.01               # matches servicer
