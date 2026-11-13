"""One-factor (Vasicek) model and Gaussian copula simulation (Chapter 13)."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm


def conditional_pd(pd: float, rho: float, z):
    """Default probability given the systematic factor Z = z."""
    return norm.cdf((norm.ppf(pd) - np.sqrt(rho) * np.asarray(z)) / np.sqrt(1 - rho))


def vasicek_cdf(x, pd: float, rho: float):
    """P(portfolio default rate <= x) for a large homogeneous pool."""
    x = np.asarray(x, dtype=float)
    return norm.cdf((np.sqrt(1 - rho) * norm.ppf(x) - norm.ppf(pd)) / np.sqrt(rho))


def vasicek_quantile(q: float, pd: float, rho: float) -> float:
    """Default rate not exceeded with probability q."""
    return float(norm.cdf((norm.ppf(pd) + np.sqrt(rho) * norm.ppf(q)) / np.sqrt(1 - rho)))


def estimate_rho_moments(default_rates) -> tuple[float, float]:
    """Estimate (pd, rho) from a time series of default rates.

    Uses the probit transform: if DR = Phi((Phi^-1(pd) - sqrt(rho) Z) / sqrt(1-rho)),
    then Phi^-1(DR) is normal with variance rho / (1 - rho).
    """
    dr = np.clip(np.asarray(default_rates, dtype=float), 1e-6, 1 - 1e-6)
    y = norm.ppf(dr)
    v = y.var(ddof=1)
    rho = v / (1 + v)
    pd = norm.cdf(y.mean() * np.sqrt(1 - rho))
    return float(pd), float(rho)


def simulate_portfolio_losses(pd, lgd, ead, rho: float, n_sims: int = 10_000,
                              seed: int = 0, batch: int = 1_000) -> np.ndarray:
    """Portfolio loss as a share of total exposure, one value per scenario.

    Each loan defaults when sqrt(rho) Z + sqrt(1 - rho) e_i < Phi^-1(pd_i).
    """
    rng = np.random.default_rng(seed)
    pd = np.asarray(pd, dtype=float)
    lgd = np.broadcast_to(np.asarray(lgd, dtype=float), pd.shape)
    ead = np.broadcast_to(np.asarray(ead, dtype=float), pd.shape)
    threshold = norm.ppf(pd)
    total = ead.sum()
    out = np.empty(n_sims)
    done = 0
    while done < n_sims:
        m = min(batch, n_sims - done)
        z = rng.standard_normal((m, 1))
        e = rng.standard_normal((m, pd.size))
        x = np.sqrt(rho) * z + np.sqrt(1 - rho) * e
        out[done:done + m] = ((x < threshold) * (lgd * ead)).sum(axis=1) / total
        done += m
    return out
