"""Pool cashflow projection and the deal waterfall (Chapter 19).

The model is a representative-line model: the whole pool is treated as one
large loan with the pool's balance, interest rate and remaining term.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def monthly_timing(annual_shares, months_per_year: int = 12) -> np.ndarray:
    """Spread annual default-timing shares evenly over the months of each year."""
    a = np.asarray(annual_shares, dtype=float)
    a = a / a.sum()
    return np.repeat(a / months_per_year, months_per_year)


def cpr_to_smm(cpr: float) -> float:
    """Annual constant prepayment rate -> single monthly mortality."""
    return 1 - (1 - cpr) ** (1 / 12)


def project_pool(balance: float, remaining_term: int, cum_default: float = 0.0,
                 severity: float = 0.0, cpr: float = 0.10,
                 timing=(0.20, 0.25, 0.20, 0.15, 0.10, 0.10), recovery_lag: int = 15,
                 annuity_rate_pct: float = 1.8, months: int = 360) -> pd.DataFrame:
    """Monthly pool cashflows.

    cum_default : cumulative defaults as a share of the original balance
    severity    : loss as a share of each defaulted balance
    timing      : share of all defaults falling in each year
    """
    curve = monthly_timing(timing)
    r = annuity_rate_pct / 100 / 12
    bal = balance
    pending_rec = np.zeros(months + recovery_lag + 1)
    pending_loss = np.zeros(months + recovery_lag + 1)
    rows = []
    for t in range(months):
        start = bal
        target_def = cum_default * balance * (curve[t] if t < len(curve) else 0.0)
        defaults = min(target_def, start)
        perf = start - defaults
        n_rem = max(remaining_term - t, 1)
        sched = perf * r / ((1 + r) ** n_rem - 1) if r > 0 else perf / n_rem
        sched = min(sched, perf)
        prepay = (perf - sched) * cpr_to_smm(cpr)
        bal = perf - sched - prepay
        pending_rec[t + recovery_lag] += defaults * (1 - severity)
        pending_loss[t + recovery_lag] += defaults * severity
        rows.append({"month": t + 1, "opening_balance": start, "defaults": defaults,
                     "scheduled_principal": sched, "prepayments": prepay,
                     "recoveries": pending_rec[t], "losses": pending_loss[t],
                     "closing_balance": bal})
        if bal < 1e-6 and t >= len(curve) + recovery_lag:
            break
    return pd.DataFrame(rows)


def run_waterfall(pool: pd.DataFrame, deal: dict, sonia_pct: float = 3.0,
                  pool_spread_pct: float = 1.60) -> dict:
    """Run interest and principal waterfalls month by month.

    Revenue: performing balance x (SONIA + pool spread) / 12, as if the fixed
    rate mortgages were swapped into floating rate.
    Order of revenue: senior fees, class interest A..E in sequence,
    principal deficiency ledger (PDL) cure, reserve fund top-up, residual.
    Principal (plus PDL cures) repays the notes sequentially A..Z.
    """
    classes = [t["class"] for t in deal["tranches"]]
    bal = {t["class"]: t["balance"] for t in deal["tranches"]}
    margin = {t["class"]: (t["margin_pct"] or 0.0) for t in deal["tranches"]}
    pool_bal0 = deal["pool_balance"]
    reserve_target = deal["reserve_fund_target_pct"] * pool_bal0
    reserve = reserve_target
    fee_rate = deal["senior_fees_bps_per_year"] / 10_000 / 12
    pdl = 0.0
    short = {c: 0.0 for c in classes}        # unpaid interest carried forward
    first_short = {c: None for c in classes}
    log = []
    for _, m in pool.iterrows():
        perf_bal = m["opening_balance"] - m["defaults"]
        revenue = perf_bal * (sonia_pct + pool_spread_pct) / 100 / 12
        avail = revenue + reserve
        reserve = 0.0
        fees = min(avail, m["opening_balance"] * fee_rate)
        avail -= fees
        paid_int = {}
        for c in classes:
            if c == "Z":
                continue
            due = bal[c] * (sonia_pct + margin[c]) / 100 / 12 + short[c]
            pay = min(avail, due)
            avail -= pay
            short[c] = due - pay
            if short[c] > 1e-6 and first_short[c] is None:
                first_short[c] = int(m["month"])
            paid_int[c] = pay
        pdl += m["losses"]
        cure = min(avail, pdl)
        avail -= cure
        pdl -= cure
        reserve = min(avail, reserve_target)
        avail -= reserve
        residual = avail
        prin = m["scheduled_principal"] + m["prepayments"] + m["recoveries"] + cure
        for c in classes:
            pay = min(prin, bal[c])
            bal[c] -= pay
            prin -= pay
        log.append({"month": int(m["month"]), "revenue": revenue, "fees": fees,
                    **{f"int_{c}": v for c, v in paid_int.items()},
                    "pdl_cure": cure, "pdl_balance": pdl, "reserve": reserve,
                    "residual": residual, **{f"bal_{c}": bal[c] for c in classes}})
    # Notes still outstanding once the pool has paid everything are losses
    ledger = pd.DataFrame(log)
    tranche_loss = {c: bal[c] / max(t["balance"], 1e-9)
                    for c, t in zip(classes, deal["tranches"])}
    return {"ledger": ledger, "tranche_loss": tranche_loss,
            "interest_shortfall": short, "first_interest_shortfall": first_short}


def credit_enhancement(deal: dict) -> pd.DataFrame:
    """Subordination below each class plus the reserve fund, as % of the pool."""
    rows = []
    below = 1.0
    for t in deal["tranches"]:
        below -= t["share_of_pool"]
        rows.append({"class": t["class"], "size": t["share_of_pool"],
                     "subordination": below,
                     "credit_enhancement": below + deal["reserve_fund_target_pct"]})
    return pd.DataFrame(rows)
