"""The Merton structural model of default (Chapter 9)."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm


def distance_to_default(V: float, D: float, mu: float, sigma: float, T: float) -> float:
    """Number of standard deviations between expected log asset value and the debt."""
    return (np.log(V / D) + (mu - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))


def merton_pd(V: float, D: float, mu: float, sigma: float, T: float) -> float:
    """Probability that assets end below the debt D at time T."""
    return float(norm.cdf(-distance_to_default(V, D, mu, sigma, T)))


def simulate_asset_paths(V0: float, mu: float, sigma: float, T: float, steps: int,
                         n_paths: int, seed: int = 0) -> np.ndarray:
    """Geometric Brownian motion paths, shape (n_paths, steps + 1)."""
    rng = np.random.default_rng(seed)
    dt = T / steps
    dW = rng.normal(0.0, np.sqrt(dt), (n_paths, steps))
    log_inc = (mu - 0.5 * sigma ** 2) * dt + sigma * dW
    log_path = np.concatenate([np.zeros((n_paths, 1)), np.cumsum(log_inc, axis=1)], axis=1)
    return V0 * np.exp(log_path)
