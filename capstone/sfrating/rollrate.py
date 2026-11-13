"""Roll-rate (Markov chain) models (Chapter 11)."""
from __future__ import annotations

import numpy as np
import pandas as pd

STATES = ["C", "30", "60", "90", "DEF", "PRE"]
ABSORBING = ["DEF", "PRE"]


def add_previous_status(perf: pd.DataFrame, initial: str = "C") -> pd.DataFrame:
    """Add prev_status: the loan's status one month earlier.

    Every loan is current at the cut-off date, so the first month's
    previous status is ``initial``.
    """
    out = perf.sort_values(["loan_id", "period"]).copy()
    out["prev_status"] = out.groupby("loan_id")["status"].shift(1).fillna(initial)
    return out


def transition_counts(perf: pd.DataFrame, periods=None) -> pd.DataFrame:
    """Count moves from prev_status to status, optionally for selected periods."""
    df = perf if "prev_status" in perf else add_previous_status(perf)
    if periods is not None:
        df = df[df["period"].isin(periods)]
    counts = pd.crosstab(df["prev_status"], df["status"])
    return counts.reindex(index=STATES, columns=STATES, fill_value=0)


def transition_matrix(perf: pd.DataFrame, periods=None) -> pd.DataFrame:
    """Row-normalised one-month transition matrix.

    Rows for DEF and PRE (absorbing) and for any state with no observations
    are identity rows: the loan stays where it is.
    """
    counts = transition_counts(perf, periods).astype(float)
    for s in STATES:
        # Absorbing states, and states never observed, stay where they are
        if s in ABSORBING or counts.loc[s].sum() == 0:
            counts.loc[s] = 0.0
            counts.loc[s, s] = 1.0
    return counts.div(counts.sum(axis=1), axis=0)


def project(matrix: pd.DataFrame, start: dict | pd.Series, months: int) -> pd.DataFrame:
    """Distribution over states for months 0..months, starting from ``start``."""
    P = matrix.to_numpy()
    v = pd.Series(start, dtype=float).reindex(matrix.index, fill_value=0.0).to_numpy()
    rows = [v]
    for _ in range(months):
        v = v @ P
        rows.append(v)
    return pd.DataFrame(rows, columns=matrix.columns).rename_axis("month")


def cumulative_default_rate(matrix: pd.DataFrame, months: int) -> float:
    """Share of an all-current pool that has defaulted after ``months``."""
    return float(project(matrix, {"C": 1.0}, months)["DEF"].iloc[-1])
