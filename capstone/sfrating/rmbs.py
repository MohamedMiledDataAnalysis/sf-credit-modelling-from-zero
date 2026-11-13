"""Loan-level RMBS rating stresses: default frequency and loss severity (Chapter 15).

For each rating level the model asks two questions about every loan:
  * how likely is it to default?  base PD x default multiple, capped at 100%
  * how much is lost if it does?  stressed sale value after a market value decline
The pool loss at that rating is the balance-weighted sum of frequency x severity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FORCED_SALE_DISCOUNT = 0.20
SALE_COSTS_PCT = 0.045
FIXED_COSTS = 3_500.0
ACCRUED_MONTHS = 15


def loss_severity(balance, value, rate_pct, mvd_pct, fsd=FORCED_SALE_DISCOUNT):
    """Loss severity per loan after a market value decline of ``mvd_pct`` percent."""
    balance = np.asarray(balance, dtype=float)
    value_stressed = np.asarray(value, dtype=float) * (1 - mvd_pct / 100)
    exposure = balance * (1 + np.asarray(rate_pct) / 100 / 12 * ACCRUED_MONTHS)
    proceeds = value_stressed * (1 - fsd) - (SALE_COSTS_PCT * value_stressed + FIXED_COSTS)
    loss = np.clip(exposure - np.clip(proceeds, 0, None), 0, None)
    return loss / exposure


def rating_level_losses(loans: pd.DataFrame, base_pd, stresses: pd.DataFrame,
                        value_col: str = "property_value") -> pd.DataFrame:
    """Weighted default frequency, severity and expected loss per rating level."""
    bal = loans["current_balance"].to_numpy()
    w = bal / bal.sum()
    rows = []
    for _, s in stresses.iterrows():
        ff = np.clip(np.asarray(base_pd) * s["default_multiple"], 0, 1)
        ls = loss_severity(bal, loans[value_col], loans["interest_rate"],
                           s["market_value_decline_pct"])
        wa_ff = float((w * ff).sum())
        loss = float((w * ff * ls).sum())
        wa_ls = loss / wa_ff if wa_ff > 0 else 0.0
        rows.append({"rating": s["rating"], "default_frequency": wa_ff,
                     "loss_severity": wa_ls, "pool_loss": loss})
    return pd.DataFrame(rows)
