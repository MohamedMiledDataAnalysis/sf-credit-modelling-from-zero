"""CLO portfolio metrics and the binomial expansion technique (Chapter 18)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import binom


def weighted_average(values, weights) -> float:
    w = np.asarray(weights, dtype=float)
    return float((np.asarray(values, dtype=float) * w).sum() / w.sum())


def diversity_score(par: pd.Series, industry: pd.Series) -> float:
    """Simplified diversity score: equivalent number of independent obligors.

    Within each industry, the number of equal-sized obligors is
    (sum of par)^2 / sum(par^2) (the inverse Herfindahl index). Industry
    totals are then shrunk with a concave map so that many obligors in one
    industry count for less than the same number spread across industries.
    """
    df = pd.DataFrame({"par": par.to_numpy(), "industry": industry.to_numpy()})
    total = 0.0
    for _, g in df.groupby("industry"):
        n_eq = g["par"].sum() ** 2 / (g["par"] ** 2).sum()
        total += 2 * np.sqrt(n_eq) - 1 if n_eq >= 1 else n_eq
    return float(total)


def bet_loss_distribution(diversity: int, p: float, lgd: float) -> pd.DataFrame:
    """Binomial expansion: D independent equal loans, each defaulting with probability p."""
    k = np.arange(diversity + 1)
    prob = binom.pmf(k, diversity, p)
    loss = k / diversity * lgd
    return pd.DataFrame({"defaults": k, "probability": prob, "portfolio_loss": loss})


def tranche_expected_loss(dist: pd.DataFrame, attach: float, detach: float) -> float:
    """Expected loss of a tranche as a share of its own size."""
    loss = dist["portfolio_loss"].to_numpy()
    hit = np.clip(loss - attach, 0, detach - attach) / (detach - attach)
    return float((hit * dist["probability"].to_numpy()).sum())
