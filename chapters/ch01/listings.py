"""
What a Rating Agency Quant Does

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch01/listings.py
"""

# --- Listing 01.1 ------------------------------------
import pandas as pd

table = pd.read_csv("data/rating_default_table.csv")
five_years = table[table["horizon_years"] == 5]
main = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
five_years = five_years[five_years["rating"].isin(main)]
print(five_years[["rating", "cumulative_pd"]].to_string(
    index=False))

# --- Listing 01.2 ------------------------------------
import matplotlib.pyplot as plt

plt.bar(five_years["rating"], 100 * five_years["cumulative_pd"])
plt.yscale("log")
plt.ylabel("5-year default probability (%)")
plt.title("Illustrative default probability by rating")
plt.savefig("figures/ch01_rating_scale.png")

# --- Listing 01.3 ------------------------------------
loans = pd.read_csv("data/rmbs_loans.csv")
print(loans.shape)

# --- Listing 01.4 ------------------------------------
print(loans[["loan_id", "current_balance",
             "current_ltv", "region"]].head(3))

# --- Listing 01.5 ------------------------------------
pool_balance = loans["current_balance"].sum()
average_ltv = loans["current_ltv"].mean()
print(f"Pool balance: £{pool_balance / 1e6:,.1f} m")
print(f"Average LTV:  {average_ltv:.1f}%")

# --- Listing 01.6 ------------------------------------
n_loans = len(loans)
average_balance = pool_balance / n_loans
print(f"Loans:           {n_loans:,}")
print(f"Pool balance:    £{pool_balance / 1e6:,.1f} m")
print(f"Average balance: £{average_balance:,.0f}")
largest = loans["current_balance"].max()
print(f"Largest loan:    £{largest:,.0f}")

# --- Listing 01.7 ------------------------------------
high_ltv = (loans["current_ltv"] > 80).mean()
repayment = loans["repayment_type"]
interest_only = (repayment == "Interest-only").mean()
buy_to_let = (loans["occupancy"] == "Buy-to-let").mean()
print(f"LTV above 80%:  {high_ltv:.1%}")
print(f"Interest-only:  {interest_only:.1%}")
print(f"Buy-to-let:     {buy_to_let:.1%}")

# --- Listing 01.8 ------------------------------------
defaults = pd.read_csv("data/rmbs_defaults.csv")
exposure = defaults["exposure_at_default"].sum()
loss = defaults["loss"].sum()
print(f"Defaulted loans:     {len(defaults)}")
print(f"Exposure / pool:     {exposure / pool_balance:.2%}")
print(f"Loss / exposure:     {loss / exposure:.2%}")
print(f"Loss / pool:         {loss / pool_balance:.2%}")

# --- Listing 01.9 ------------------------------------
btl = loans[loans["occupancy"] == "Buy-to-let"]
btl_balance = btl["current_balance"].sum()
print(f"Buy-to-let balance: £{btl_balance / 1e6:,.1f} m")
print(f"Share of pool:      {btl_balance / pool_balance:.1%}")

# --- Listing 01.10 -----------------------------------
ten = table[table["horizon_years"] == 10]
aaa = ten[ten["rating"] == "AAA"]["cumulative_pd"].iloc[0]
bbb = ten[ten["rating"] == "BBB"]["cumulative_pd"].iloc[0]
print(f"AAA 10-year PD: {aaa:.2%}")
print(f"BBB 10-year PD: {bbb:.2%}")
print(f"Ratio: {bbb / aaa:.1f}")

# --- Listing 01.11 -----------------------------------
p = 0.02
none = (1 - p) ** 10
one = 10 * p * (1 - p) ** 9
two = 45 * p ** 2 * (1 - p) ** 8
print(f"P(at least 3 defaults) = {1 - none - one - two:.5f}")

# --- Listing 01.12 -----------------------------------
# (not executed in the book)
# import pandas as pd

# loans = pd.read_csv("data/rmbs_loans.csv")
# pool_balance = loans["current_balance"].sum()
# print(f"Loans:        {len(loans):,}")
# print(f"Pool balance: £{pool_balance / 1e6:,.1f} m")
# print(f"Average LTV:  {loans['current_ltv'].mean():.1f}%")
