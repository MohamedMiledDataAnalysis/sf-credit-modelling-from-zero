"""
Statistics and Regression

Every code listing of this chapter, in the order of the book.
Run from the repository root:  python chapters/ch06/listings.py
"""

# --- Listing 06.1 ------------------------------------
import numpy as np
import pandas as pd
from scipy.stats import norm

loans = pd.read_csv("data/rmbs_loans.csv")
defaults = pd.read_csv("data/rmbs_defaults.csv")
loans["default"] = (loans["loan_id"]
                    .isin(defaults["loan_id"]).astype(int))
k = loans["default"].sum()
n = len(loans)
print(f"k = {k}, n = {n}, p_hat = {k / n:.4f}")

# --- Listing 06.2 ------------------------------------
rng = np.random.default_rng(6)
for draw in range(5):
    sample = loans.sample(500, random_state=rng)
    print(f"Sample {draw + 1}: p_hat = "
          f"{sample['default'].mean():.4f}")

# --- Listing 06.3 ------------------------------------
from statsmodels.stats.proportion import proportion_confint

p_hat = k / n
se = np.sqrt(p_hat * (1 - p_hat) / n)
z = norm.ppf(0.975)
print(f"SE = {se:.6f}")
print(f"95% CI: {p_hat - z * se:.4%} to {p_hat + z * se:.4%}")
low, high = proportion_confint(k, n, alpha=0.05,
                               method="normal")
print(f"statsmodels: {low:.4%} to {high:.4%}")

# --- Listing 06.4 ------------------------------------
from statsmodels.stats.proportion import proportions_ztest

by_emp = loans.groupby("employment")["default"].agg(
    ["sum", "count"])
print(by_emp)
z_stat, p_value = proportions_ztest(by_emp["sum"],
                                    by_emp["count"])
print(f"z = {z_stat:.2f}, p-value = {p_value:.6f}")

# --- Listing 06.5 ------------------------------------
import statsmodels.api as sm

toy = pd.DataFrame({"ltv": [60, 70, 80, 90],
                    "sev": [0.02, 0.06, 0.14, 0.18]})
toy_fit = sm.OLS(toy["sev"], sm.add_constant(toy["ltv"])).fit()
print(toy_fit.params.round(4))

# --- Listing 06.6 ------------------------------------
X = sm.add_constant(defaults["indexed_ltv_at_default"])
ols = sm.OLS(defaults["loss_severity"], X).fit()
table = pd.DataFrame({"coef": ols.params,
                      "std err": ols.bse,
                      "t": ols.tvalues,
                      "p-value": ols.pvalues})
table.index = ["const", "indexed_ltv"]
print(table.round(4))
print(f"R-squared: {ols.rsquared:.3f}")

# --- Listing 06.7 ------------------------------------
import matplotlib.pyplot as plt

grid = np.linspace(25, 105, 50)
plt.scatter(defaults["indexed_ltv_at_default"],
            defaults["loss_severity"], s=8, alpha=0.5,
            label="Defaulted loans")
plt.plot(grid, ols.params.iloc[0] + ols.params.iloc[1] * grid,
         color="#B03A2E", label="OLS line")
plt.axhline(0, color="grey", linewidth=0.8)
plt.xlabel("Indexed LTV at default (%)")
plt.ylabel("Loss severity")
plt.title("Severity rises with LTV, but not as a line")
plt.legend()
plt.savefig("figures/ch06_severity_ltv.png")

# --- Listing 06.8 ------------------------------------
def logistic(x):
    return 1 / (1 + np.exp(-x))

for p in [0.50, 0.20, 0.05]:
    log_odds = np.log(p / (1 - p))
    print(f"p = {p:.2f}  log-odds = {log_odds:7.3f}  "
          f"back = {logistic(log_odds):.2f}")

# --- Listing 06.9 ------------------------------------
X1 = sm.add_constant(loans[["credit_score"]])
logit1 = sm.Logit(loans["default"], X1).fit(disp=0)
print(logit1.params.round(6))

# --- Listing 06.10 -----------------------------------
for score in [700, 850]:
    x = logit1.params["const"] + (logit1.params["credit_score"]
                                  * score)
    print(f"score {score}: PD = {logistic(x):.2%}")

# --- Listing 06.11 -----------------------------------
from sklearn.metrics import roc_auc_score, roc_curve

toy_y = [1, 0, 1, 0, 0]
toy_pd = [0.30, 0.20, 0.10, 0.05, 0.02]
print(f"Toy AUC: {roc_auc_score(toy_y, toy_pd):.3f}")

pd_score = logit1.predict(X1)
auc1 = roc_auc_score(loans["default"], pd_score)
print(f"Credit score model: AUC {auc1:.3f}, "
      f"Gini {2 * auc1 - 1:.3f}")

# --- Listing 06.12 -----------------------------------
fpr, tpr, _ = roc_curve(loans["default"], pd_score)
plt.figure(figsize=(4.2, 3.6))
plt.plot(fpr, tpr, label=f"Credit score (Gini {2*auc1-1:.2f})")
plt.plot([0, 1], [0, 1], linestyle="--", color="grey",
         label="Random ranking")
plt.xlabel("Share of non-defaulters flagged")
plt.ylabel("Share of defaulters caught")
plt.title("ROC curve")
plt.legend(loc="lower right")
plt.savefig("figures/ch06_roc.png")

# --- Listing 06.13 -----------------------------------
check = pd.DataFrame({"pd": pd_score,
                      "default": loans["default"]})
check["decile"] = pd.qcut(check["pd"], 10, labels=False) + 1
calib = check.groupby("decile").agg(
    predicted=("pd", "mean"), observed=("default", "mean"),
    loans=("default", "size"))
print(calib.round(4))

# --- Listing 06.14 -----------------------------------
FEATURES = ["credit_score", "original_ltv", "loan_to_income",
            "interest_only", "self_employed", "buy_to_let",
            "flat"]

def prepare_features(loans):
    X = pd.DataFrame(index=loans.index)
    X["credit_score"] = loans["credit_score"]
    X["original_ltv"] = loans["original_ltv"]
    X["loan_to_income"] = loans["loan_to_income"]
    X["interest_only"] = (loans["repayment_type"]
                          == "Interest-only").astype(int)
    X["self_employed"] = (loans["employment"]
                          == "Self-employed").astype(int)
    X["buy_to_let"] = (loans["occupancy"]
                       == "Buy-to-let").astype(int)
    X["flat"] = (loans["property_type"] == "Flat").astype(int)
    return X[FEATURES]

features = prepare_features(loans)
print(features.mean().round(3))

# --- Listing 06.15 -----------------------------------
def fit_pd_model(loans, defaults):
    X = sm.add_constant(prepare_features(loans).astype(float))
    y = loans["loan_id"].isin(defaults["loan_id"]).astype(int)
    return sm.Logit(y, X).fit(disp=0)

model = fit_pd_model(loans, defaults)
coefs = pd.DataFrame({"coef": model.params,
                      "odds ratio": np.exp(model.params),
                      "p-value": model.pvalues})
print(coefs.round(4))

# --- Listing 06.16 -----------------------------------
def predict_pd(model, loans):
    X = sm.add_constant(prepare_features(loans).astype(float),
                        has_constant="add")
    return pd.Series(model.predict(X), index=loans.index,
                     name="pd_5y")

def gini(y_true, score):
    return 2 * roc_auc_score(y_true, score) - 1

loans["pd_5y"] = predict_pd(model, loans)
print(f"Mean PD:  {loans['pd_5y'].mean():.4f}")
gini_score = gini(loans["default"], pd_score)
gini_full = gini(loans["default"], loans["pd_5y"])
print(f"Gini, credit score only: {gini_score:.3f}")
print(f"Gini, full model:        {gini_full:.3f}")

# --- Listing 06.17 -----------------------------------
check = loans[["pd_5y", "default"]].copy()
check["decile"] = pd.qcut(check["pd_5y"], 10, labels=False) + 1
calib = check.groupby("decile")[["pd_5y", "default"]].mean()
print(calib.round(4))

# --- Listing 06.18 -----------------------------------
plt.figure()
pos = np.arange(1, 11)
plt.bar(pos - 0.2, 100 * calib["pd_5y"], width=0.4,
        label="Predicted")
plt.bar(pos + 0.2, 100 * calib["default"], width=0.4,
        label="Observed")
plt.xticks(pos)
plt.xlabel("Decile of predicted PD (1 = safest)")
plt.ylabel("Five-year default rate (%)")
plt.title("Calibration of the PD model")
plt.legend()
plt.savefig("figures/ch06_calibration.png")

# --- Listing 06.19 -----------------------------------
print(roc_auc_score([1, 0, 1, 0], [0.08, 0.06, 0.04, 0.01]))

# --- Listing 06.20 -----------------------------------
io = loans.groupby("repayment_type")["default"].agg(
    ["sum", "count"])
z_io, p_io = proportions_ztest(io["sum"], io["count"])
print(io)
print(f"z = {z_io:.2f}, p-value = {p_io:.2e}")
r = io["sum"] / io["count"]
diff = r["Interest-only"] - r["Repayment"]
se_diff = np.sqrt((r * (1 - r) / io["count"]).sum())
print(f"Difference: {diff:.4f} +/- {1.96 * se_diff:.4f}")

# --- Listing 06.21 -----------------------------------
X2 = sm.add_constant(defaults[["indexed_ltv_at_default",
                               "forced_sale_discount"]])
ols2 = sm.OLS(defaults["loss_severity"], X2).fit()
print(ols2.params.round(4))
print(f"R-squared: {ols.rsquared:.3f} -> {ols2.rsquared:.3f}")

# --- Listing 06.22 -----------------------------------
scaled = 1.5 * loans["pd_5y"]
print(f"Gini original: {gini_full:.4f}")
print(f"Gini scaled:   {gini(loans['default'], scaled):.4f}")
print(f"Mean PD scaled: {scaled.mean():.4f}, "
      f"observed: {loans['default'].mean():.4f}")

# --- Listing 06.23 -----------------------------------
# (not executed in the book)
# FEATURES = ["credit_score", "original_ltv", "loan_to_income",
#             "interest_only", "self_employed", "buy_to_let",
#             "flat"]

# def default_flag(loans, defaults):
#     """1 if the loan defaulted during the 60 observed months."""
#     flag = loans["loan_id"].isin(defaults["loan_id"])
#     return flag.astype(int)

# def fit_pd_model(loans, defaults):
#     """Logistic regression of the 5-year default flag."""
#     X = sm.add_constant(prepare_features(loans).astype(float))
#     y = default_flag(loans, defaults)
#     return sm.Logit(y, X).fit(disp=0)

# --- Listing 06.24 -----------------------------------
from sfrating import pd_model
pkg_model = pd_model.fit_pd_model(loans, defaults)
pkg_pd = pd_model.predict_pd(pkg_model, loans)
flag = pd_model.default_flag(loans, defaults)
print(f"{pd_model.gini(flag, pkg_pd):.4f}")
