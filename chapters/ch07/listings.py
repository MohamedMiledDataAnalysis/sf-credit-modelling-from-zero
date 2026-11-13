"""
Numerical Methods

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch07/listings.py
"""

# --- Listing 07.1 ------------------------------------
import numpy as np
import pandas as pd
from scipy.stats import norm

def bisection(f, a, b, tol=1e-10, max_iter=200):
    """Root of f in [a, b]; f(a), f(b) of opposite signs."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("f(a) and f(b) must differ in sign")
    for _ in range(max_iter):
        m = (a + b) / 2
        fm = f(m)
        if fm == 0 or (b - a) / 2 < tol:
            return m
        if fa * fm < 0:          # sign change in left half
            b, fb = m, fm
        else:                    # sign change in right half
            a, fa = m, fm
    return (a + b) / 2

# --- Listing 07.2 ------------------------------------
def f_cum(p):
    return 1 - (1 - p) ** 5 - 0.054

root = bisection(f_cum, 0.0, 0.05)
exact = 1 - (1 - 0.054) ** (1 / 5)
print(f"Bisection:   {root:.10f}")
print(f"Closed form: {exact:.10f}")

# --- Listing 07.3 ------------------------------------
def newton(f, df, x0, tol=1e-12, max_iter=50):
    """Newton-Raphson iteration from the starting point x0."""
    x = x0
    for _ in range(max_iter):
        step = f(x) / df(x)
        x -= step
        if abs(step) < tol:
            return x
    raise RuntimeError("Newton did not converge")

def df_cum(p):
    return 5 * (1 - p) ** 4

x = 0.01
for n in range(1, 5):
    x = x - f_cum(x) / df_cum(x)
    error = abs(x - exact)
    print(f"step {n}: p = {x:.15f}  error = {error:.1e}")

# --- Listing 07.4 ------------------------------------
def payment(balance, r, n):
    return balance * r / (1 - (1 + r) ** -n)

def g(r):
    return payment(200_000, r, 300) - 1_100

def numerical_slope(f, h=1e-7):
    return lambda x: (f(x + h) - f(x - h)) / (2 * h)

r_bis = bisection(g, 0.0001, 0.02)
r_newt = newton(g, numerical_slope(g), 0.005)
print(f"Bisection: {r_bis:.8f} per month")
print(f"Newton:    {r_newt:.8f} per month")
print(f"Annual rate: {12 * r_newt:.4%}")

# --- Listing 07.5 ------------------------------------
from scipy import optimize

r_brent = optimize.brentq(g, 0.0001, 0.02, xtol=1e-14)
r_scipy_newton = optimize.newton(g, 0.005)
print(f"brentq: {r_brent:.8f}")
print(f"newton: {r_scipy_newton:.8f}")

# --- Listing 07.6 ------------------------------------
def trapezoid(f, a, b, n=1000):
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return h * (y[0] / 2 + y[1:-1].sum() + y[-1] / 2)

def simpson(f, a, b, n=1000):
    if n % 2:
        n += 1                    # Simpson needs an even n
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return h / 3 * (y[0] + 4 * y[1:-1:2].sum()
                    + 2 * y[2:-1:2].sum() + y[-1])

# --- Listing 07.7 ------------------------------------
exact_area = norm.cdf(1) - norm.cdf(0)
print(" n   trapezoid error   Simpson error")
for n in [2, 4, 8, 16]:
    e_t = abs(trapezoid(norm.pdf, 0, 1, n) - exact_area)
    e_s = abs(simpson(norm.pdf, 0, 1, n) - exact_area)
    print(f"{n:2d}   {e_t:.2e}          {e_s:.2e}")

# --- Listing 07.8 ------------------------------------
import matplotlib.pyplot as plt

xs = np.linspace(-0.2, 1.2, 200)
grid = np.linspace(0, 1, 5)
plt.plot(xs, norm.pdf(xs), label="Normal density")
plt.fill_between(grid, norm.pdf(grid), alpha=0.3,
                 color="#C9A227", label="4 trapezoids")
for x0 in grid:
    plt.vlines(x0, 0, norm.pdf(x0), color="#C9A227")
plt.ylim(0, 0.45)
plt.xlabel("x")
plt.title("Trapezoid rule with 4 strips on [0, 1]")
plt.legend(loc="lower left")
plt.savefig("figures/ch07_trapezoid.png")

# --- Listing 07.9 ------------------------------------
exposure, median_value, sigma = 180_000, 200_000, 0.25
z_star = np.log(exposure / median_value) / sigma

def loss_times_density(z):
    value = median_value * np.exp(sigma * z)
    return np.maximum(exposure - value, 0) * norm.pdf(z)

print(f"z* = {z_star:.6f}, P(loss) = {norm.cdf(z_star):.4f}")
for n in [10, 100, 1000]:
    print(f"Simpson n={n:4d}: "
          f"{simpson(loss_times_density, -8, z_star, n):,.2f}")

# --- Listing 07.10 -----------------------------------
from scipy import integrate

el_quad, err_est = integrate.quad(loss_times_density,
                                  -8, z_star)
print(f"quad: {el_quad:,.2f}  (error estimate {err_est:.1e})")
print(f"Loss severity: {el_quad / exposure:.2%}")

# --- Listing 07.11 -----------------------------------
k, n = 540, 10_000

def neg_log_lik(p):
    return -(k * np.log(p) + (n - k) * np.log(1 - p))

res = optimize.minimize_scalar(neg_log_lik,
                               bounds=(1e-6, 0.5),
                               method="bounded")
print(f"MLE: {res.x:.6f}   k/n: {k / n:.6f}")

# --- Listing 07.12 -----------------------------------
grid_p = np.linspace(0.03, 0.08, 200)
plt.plot(100 * grid_p, neg_log_lik(grid_p))
plt.axvline(100 * res.x, color="#C9A227", linestyle="--",
            label=f"minimum at {res.x:.2%}")
plt.xlabel("Five-year default probability p (%)")
plt.ylabel("Negative log-likelihood")
plt.title("Maximum likelihood: the bottom of the curve")
plt.legend()
plt.savefig("figures/ch07_likelihood.png")

# --- Listing 07.13 -----------------------------------
loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
y = loans["loan_id"].isin(defaults["loan_id"]).to_numpy()
score = loans["credit_score"].to_numpy() / 100   # scaled

def neg_ll(beta, x):
    p = 1 / (1 + np.exp(-(beta[0] + beta[1] * x)))
    return -np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))

def neg_ll_grad(beta, x):
    resid = y - 1 / (1 + np.exp(-(beta[0] + beta[1] * x)))
    return -np.array([resid.sum(), (resid * x).sum()])

fit = optimize.minimize(neg_ll, x0=[0.0, 0.0], args=(score,),
                        jac=neg_ll_grad, method="BFGS")
print(fit.success, fit.nit, "iterations")
print("beta0 =", round(fit.x[0], 4),
      " beta1 per point =", round(fit.x[1] / 100, 6))

# --- Listing 07.14 -----------------------------------
print(0.1 + 0.2 == 0.3)
print(f"{0.1 + 0.2:.20f}")
print(np.isclose(0.1 + 0.2, 0.3))
print("machine epsilon:", np.finfo(float).eps)

# --- Listing 07.15 -----------------------------------
p_tiny = 1e-12
naive = 1 - (1 - p_tiny) ** (1 / 5)
stable = -np.expm1(np.log1p(-p_tiny) / 5)
print(f"naive:  {naive:.6e}")
print(f"stable: {stable:.6e}   true: {p_tiny / 5:.6e}")

# --- Listing 07.16 -----------------------------------
import json

n_def = len(defaults)
n_loans = len(loans)
cum_5y = n_def / n_loans
target = lambda p: 1 - (1 - p) ** 5 - cum_5y
slope = lambda p: 5 * (1 - p) ** 4
observed_d = newton(target, slope, 0.01)
print(f"5-year default rate: {cum_5y:.2%}")
print(f"Annual default rate: {observed_d:.4%}")

# --- Listing 07.17 -----------------------------------
severity = (defaults["loss"].sum()
            / defaults["exposure_at_default"].sum())
with open("data/rmbs_deal.json") as f:
    deal = json.load(f)
reserve = deal["reserve_fund_target_pct"]
shares = {t["class"]: t["share_of_pool"]
          for t in deal["tranches"]}
classes = list(shares)               # A, B, C, D, E, Z
ce = {}
for i, c in enumerate(classes):
    below = sum(shares[x] for x in classes[i + 1:])
    ce[c] = below + reserve
print(f"Observed severity: {severity:.2%}")
print(pd.Series(ce).map("{:.1%}".format).to_string())

# --- Listing 07.18 -----------------------------------
def net_loss(d, sev, spread=0.01, years=5):
    balance, total = 1.0, 0.0
    for year in range(years):
        defaulted = d * balance
        total += max(0.0, sev * defaulted - spread * balance)
        balance -= defaulted
    return total

print(f"{net_loss(observed_d, severity):.4%}")
print(f"{net_loss(0.30, severity):.4%}")

# --- Listing 07.19 -----------------------------------
def break_even(sev):
    out = {}
    for c in classes:
        f = lambda d: net_loss(d, sev) - ce[c]
        try:
            out[c] = bisection(f, 0.0, 1.0)
        except ValueError:
            out[c] = np.nan          # never loses
    return pd.Series(out)

base = break_even(severity)
print(base.round(4).to_string())

# --- Listing 07.20 -----------------------------------
stressed = break_even(0.40)
check = [optimize.brentq(
    lambda d, c=c: net_loss(d, 0.40) - ce[c], 0, 1)
    for c in classes]
table = pd.DataFrame({"CE": pd.Series(ce),
                      "break-even d": stressed,
                      "multiple": stressed / observed_d})
print(table.round(4))
print("brentq agrees:", np.allclose(stressed, check))

# --- Listing 07.21 -----------------------------------
grid_d = np.linspace(0, 0.14, 300)
losses = [net_loss(d, 0.40) for d in grid_d]
plt.figure()
plt.plot(100 * grid_d, 100 * np.array(losses),
         label="Net loss to the notes")
for c in ["A", "D", "Z"]:
    plt.axhline(100 * ce[c], color="#B03A2E", linewidth=0.8,
                linestyle="--")
    plt.text(0.3, 100 * ce[c] + 0.3, f"CE of Class {c}",
             fontsize=7, color="#B03A2E")
plt.xlabel("Annual default rate d (%)")
plt.ylabel("Five-year loss (% of pool)")
plt.title("Break-even: where the curve meets the CE")
plt.legend(loc="lower right")
plt.savefig("figures/ch07_break_even.png")

# --- Listing 07.22 -----------------------------------
f71 = lambda p: 1 - (1 - p) ** 3 - 0.10
print(round(bisection(f71, 0, 0.1), 6),
      round(1 - 0.9 ** (1 / 3), 6))

# --- Listing 07.23 -----------------------------------
ll = lambda p: 3 * np.log(p) + 37 * np.log(1 - p)
print(round(ll(0.075), 6), round(ll(0.05), 6))

# --- Listing 07.24 -----------------------------------
perf = pd.read_csv("data/rmbs_performance.csv.gz")
row = perf[(perf["loan_id"] == "TB000002")
           & (perf["period"] == "2020-01")].iloc[0]
term = loans.loc[loans["loan_id"] == "TB000002",
                 "remaining_term_months"].iloc[0]
bal, pay = row["opening_balance"], row["scheduled_payment"]
h_rate = lambda r: payment(bal, r, term) - pay
r_month = newton(h_rate, numerical_slope(h_rate), 0.005)
rate_tape = loans.loc[loans["loan_id"] == "TB000002",
                      "interest_rate"].iloc[0]
print(f"balance {bal:,.2f}, payment {pay:,.2f}, term {term}")
print(f"Implied: {12 * r_month:.4%}  tape: {rate_tape}%")

# --- Listing 07.25 -----------------------------------
import statsmodels.api as sm

ltv = loans["original_ltv"].to_numpy() / 100

fit_ltv = optimize.minimize(neg_ll, [0.0, 0.0], args=(ltv,),
                            jac=neg_ll_grad, method="BFGS")
sm_fit = sm.Logit(y.astype(int),
                  sm.add_constant(ltv)).fit(disp=0)
print("success:", fit_ltv.success)
print("minimize:   ", fit_ltv.x.round(4))
print("statsmodels:", sm_fit.params.round(4))

# --- Listing 07.26 -----------------------------------
price = 0.97 * bal
h_yield = lambda r: payment(price, r, term) - pay
y_month = optimize.brentq(h_yield, 1e-6, 0.05)
print(f"Yield: {12 * y_month:.4%} per year "
      f"(coupon {rate_tape}%)")
print(payment(price, 0.0, term))

# --- Listing 07.27 -----------------------------------
# (not executed in the book)
# """Numerical methods written by hand (Chapter 7)."""
# from typing import Callable
# import numpy as np

# def bisection(f: Callable[[float], float], a: float, b: float,
#               tol: float = 1e-10, max_iter: int = 200) -> float:
#     """Root of f in [a, b]; f(a), f(b) of opposite signs."""

# --- Listing 07.28 -----------------------------------
from sfrating import numerics
print(f"{numerics.bisection(f_cum, 0.0, 0.05):.8f}")
print(f"{numerics.simpson(norm.pdf, 0, 1, 16):.8f}")
