"""From stressed losses to tranche ratings (Chapter 20).

For each rating level we run the cashflow model with that level's default
frequency and loss severity, under a slow and a fast prepayment assumption.
A class achieves a rating if it loses no principal in every scenario of that
level and, for classes A and B, never misses an interest payment.
"""
from __future__ import annotations

import pandas as pd

from .cashflow import project_pool, run_waterfall

RATING_ORDER = ["AAA", "AA", "A", "BBB", "BB", "B"]
TIMELY_INTEREST = {"A", "B"}


def scenario_results(deal: dict, level_losses: pd.DataFrame, remaining_term: int,
                     cprs=(0.05, 0.20), sonia_pct: float = 3.0,
                     timing=(0.20, 0.25, 0.20, 0.15, 0.10, 0.10),
                     annuity_rate_pct: float = 1.8) -> pd.DataFrame:
    """Tranche loss for every (rating level, prepayment) scenario."""
    rows = []
    for _, lv in level_losses.iterrows():
        for cpr in cprs:
            pool = project_pool(deal["pool_balance"], remaining_term,
                                cum_default=lv["default_frequency"],
                                severity=lv["loss_severity"], cpr=cpr, timing=timing,
                                annuity_rate_pct=annuity_rate_pct)
            res = run_waterfall(pool, deal, sonia_pct=sonia_pct)
            for c, loss in res["tranche_loss"].items():
                rows.append({"rating": lv["rating"], "cpr": cpr, "class": c,
                             "principal_loss": loss,
                             "interest_shortfall": res["first_interest_shortfall"][c] is not None})
    return pd.DataFrame(rows)


def assign_ratings(results: pd.DataFrame, tol: float = 1e-6) -> pd.Series:
    """Highest rating level whose scenarios every class survives."""
    out = {}
    for c, g in results.groupby("class", sort=False):
        out[c] = "Below B"
        for r in RATING_ORDER:
            s = g[g["rating"] == r]
            if s.empty:
                continue        # .all() of nothing is True: skip the level
            ok = (s["principal_loss"] <= tol).all()
            if c in TIMELY_INTEREST:
                ok = ok and not s["interest_shortfall"].any()
            if ok:
                out[c] = r
                break
    return pd.Series(out, name="model_rating")
