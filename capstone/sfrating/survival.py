"""Survival analysis: time to default (Chapter 12)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def rmbs_durations(perf: pd.DataFrame) -> pd.DataFrame:
    """One row per loan: months observed and whether the loan defaulted.

    A loan that prepays, or is still alive at the end of the data, is
    censored: we know it had not defaulted up to that month, nothing more.
    """
    last = perf.sort_values("period").groupby("loan_id").tail(1)
    months = perf.groupby("loan_id").size()
    out = pd.DataFrame({"loan_id": last["loan_id"].to_numpy(),
                        "status": last["status"].to_numpy()})
    out["duration"] = months.reindex(out["loan_id"]).to_numpy()
    out["event"] = (out["status"] == "DEF").astype(int)
    return out[["loan_id", "duration", "event"]]


def kaplan_meier(duration, event) -> pd.DataFrame:
    """Kaplan-Meier survival table built step by step."""
    d = pd.DataFrame({"t": np.asarray(duration), "e": np.asarray(event)})
    times = np.sort(d.loc[d["e"] == 1, "t"].unique())
    rows = []
    s = 1.0
    for t in times:
        at_risk = int((d["t"] >= t).sum())
        events = int(((d["t"] == t) & (d["e"] == 1)).sum())
        s *= 1 - events / at_risk
        rows.append((t, at_risk, events, s))
    return pd.DataFrame(rows, columns=["time", "at_risk", "events", "survival"])


def survival_at(km: pd.DataFrame, t: float) -> float:
    """Kaplan-Meier survival probability at time t (step function)."""
    past = km[km["time"] <= t]
    return 1.0 if past.empty else float(past["survival"].iloc[-1])
