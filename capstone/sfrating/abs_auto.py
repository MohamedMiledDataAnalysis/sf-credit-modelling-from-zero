"""Consumer ABS: static-pool loss curves and base-case loss (Chapter 17)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def cumulative_default_curve(auto: pd.DataFrame, horizon: int = 60) -> pd.DataFrame:
    """Kaplan-Meier style cumulative default rate by months on book.

    Prepaid and censored loans leave the risk set without defaulting.
    """
    t = auto["months_observed"].to_numpy()
    e = auto["default"].to_numpy()
    surv = 1.0
    rows = []
    for m in range(1, horizon + 1):
        at_risk = (t >= m).sum()
        d = ((t == m) & (e == 1)).sum()
        if at_risk > 0:
            surv *= 1 - d / at_risk
        rows.append((m, int(at_risk), int(d), 1 - surv))
    return pd.DataFrame(rows, columns=["month", "at_risk", "defaults", "cumulative_default"])


def base_case_loss(cum_default: float, recovery: float) -> float:
    """Cumulative net loss = cumulative default x (1 - recovery)."""
    return cum_default * (1 - recovery)


def stressed_loss(base_loss: float, multiple: float) -> float:
    """Rating-level loss = base-case loss x stress multiple."""
    return base_loss * multiple
