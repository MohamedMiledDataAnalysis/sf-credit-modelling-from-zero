"""Loan-level probability of default and expected loss (Chapters 6 and 10)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

FEATURES = ["credit_score", "original_ltv", "loan_to_income",
            "interest_only", "self_employed", "buy_to_let", "flat"]


def prepare_features(loans: pd.DataFrame) -> pd.DataFrame:
    """Numeric model inputs: three continuous drivers and four 0/1 flags."""
    X = pd.DataFrame(index=loans.index)
    X["credit_score"] = loans["credit_score"]
    X["original_ltv"] = loans["original_ltv"]
    X["loan_to_income"] = loans["loan_to_income"]
    X["interest_only"] = (loans["repayment_type"] == "Interest-only").astype(int)
    X["self_employed"] = (loans["employment"] == "Self-employed").astype(int)
    X["buy_to_let"] = (loans["occupancy"] == "Buy-to-let").astype(int)
    X["flat"] = (loans["property_type"] == "Flat").astype(int)
    return X[FEATURES]


def default_flag(loans: pd.DataFrame, defaults: pd.DataFrame) -> pd.Series:
    """1 if the loan defaulted during the 60 observed months, else 0."""
    return loans["loan_id"].isin(defaults["loan_id"]).astype(int)


def fit_pd_model(loans: pd.DataFrame, defaults: pd.DataFrame):
    """Logistic regression of the 5-year default flag on loan characteristics."""
    X = sm.add_constant(prepare_features(loans).astype(float))
    y = default_flag(loans, defaults)
    return sm.Logit(y, X).fit(disp=0)


def predict_pd(model, loans: pd.DataFrame) -> pd.Series:
    """Five-year probability of default for each loan."""
    X = sm.add_constant(prepare_features(loans).astype(float), has_constant="add")
    return pd.Series(model.predict(X), index=loans.index, name="pd_5y")


def annualise(pd_horizon, years: float):
    """Constant annual default rate giving the same cumulative probability."""
    return 1 - (1 - np.asarray(pd_horizon)) ** (1 / years)


def expected_loss(pd, lgd, ead) -> float:
    """Expected loss in currency: sum of PD x LGD x EAD."""
    return float(np.sum(np.asarray(pd) * np.asarray(lgd) * np.asarray(ead)))


def gini(y_true, score) -> float:
    """Gini coefficient (2 x AUC - 1) of a score that ranks defaulters high."""
    from sklearn.metrics import roc_auc_score
    return 2 * roc_auc_score(y_true, score) - 1
