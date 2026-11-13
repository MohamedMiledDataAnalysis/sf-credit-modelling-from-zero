"""Pool loss distribution and loss at a confidence level (Chapter 14)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .vasicek import simulate_portfolio_losses


def loss_quantiles(losses, levels=(0.5, 0.9, 0.95, 0.99, 0.995, 0.999)) -> pd.Series:
    losses = np.asarray(losses)
    return pd.Series({q: float(np.quantile(losses, q)) for q in levels}, name="loss")


def expected_shortfall(losses, q: float) -> float:
    """Average loss in the worst (1 - q) share of scenarios."""
    losses = np.sort(np.asarray(losses))
    cut = np.quantile(losses, q)
    return float(losses[losses >= cut].mean())


def pool_loss_distribution(pd_annual, lgd, ead, rho: float, years: int = 5,
                           n_sims: int = 20_000, seed: int = 0) -> np.ndarray:
    """Simulated cumulative pool loss over ``years`` with a one-factor copula."""
    pd_h = 1 - (1 - np.asarray(pd_annual, dtype=float)) ** years
    return simulate_portfolio_losses(pd_h, lgd, ead, rho, n_sims=n_sims, seed=seed)
