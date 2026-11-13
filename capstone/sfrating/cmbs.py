"""Commercial real estate loans: DSCR, LTV and stressed refinancing (Chapter 16)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def dscr(noi, debt_service):
    """Debt service coverage ratio: net operating income / debt service."""
    return np.asarray(noi, dtype=float) / np.asarray(debt_service, dtype=float)


def stressed_value(noi, cap_rate, noi_haircut=0.0):
    """Property value = stressed NOI / stressed capitalisation rate."""
    return np.asarray(noi, dtype=float) * (1 - noi_haircut) / np.asarray(cap_rate, dtype=float)


def refinance_test(balance, noi, cap_rate, noi_haircut=0.10, refi_rate=0.065,
                   max_ltv=0.80, min_dscr=1.25) -> pd.DataFrame:
    """Can each loan be refinanced at maturity under stressed conditions?"""
    value = stressed_value(noi, cap_rate, noi_haircut)
    noi_s = np.asarray(noi, dtype=float) * (1 - noi_haircut)
    ltv = np.asarray(balance, dtype=float) / value
    cover = noi_s / (np.asarray(balance, dtype=float) * refi_rate)
    return pd.DataFrame({"stressed_value": value, "stressed_ltv": ltv,
                         "refi_dscr": cover,
                         "refinances": (ltv <= max_ltv) & (cover >= min_dscr)})
