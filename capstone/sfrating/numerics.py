"""Numerical methods written by hand (Chapter 7)."""
from __future__ import annotations

from typing import Callable

import numpy as np


def bisection(f: Callable[[float], float], a: float, b: float,
              tol: float = 1e-10, max_iter: int = 200) -> float:
    """Root of f in [a, b]; f(a) and f(b) must have opposite signs."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("f(a) and f(b) must have opposite signs")
    for _ in range(max_iter):
        m = (a + b) / 2
        fm = f(m)
        if fm == 0 or (b - a) / 2 < tol:
            return m
        if fa * fm < 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return (a + b) / 2


def newton(f: Callable[[float], float], df: Callable[[float], float], x0: float,
           tol: float = 1e-12, max_iter: int = 50) -> float:
    """Newton-Raphson iteration from the starting point x0."""
    x = x0
    for _ in range(max_iter):
        step = f(x) / df(x)
        x -= step
        if abs(step) < tol:
            return x
    raise RuntimeError("Newton did not converge")


def trapezoid(f: Callable[[np.ndarray], np.ndarray], a: float, b: float, n: int = 1000) -> float:
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return h * (y[0] / 2 + y[1:-1].sum() + y[-1] / 2)


def simpson(f: Callable[[np.ndarray], np.ndarray], a: float, b: float, n: int = 1000) -> float:
    if n % 2:
        n += 1
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return h / 3 * (y[0] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum() + y[-1])
