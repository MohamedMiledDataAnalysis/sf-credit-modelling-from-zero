"""
Generate every dataset used in *Structured Finance Credit Modelling from Zero*.

All data are synthetic. The originator, the deals and the borrowers are
fictional. The generator is seeded, so every reader obtains exactly the same
files and every number printed in the book can be reproduced.

Run from the repository root:

    python scripts/generate_data.py

Files written to data/raw/, in the formats of real work (see
data/raw/data_dictionary.xlsx and Chapter 4):
    uk_rmbs/      UK RRE loan-level template (RREL, RREC), originator
                  additional data, deal summary, 60 monthly servicer
                  reports, losses report, investor report (Annex 12)
    economic/     Bank of England, ONS and HM Land Registry layouts,
                  internal credit cycle index
    uk_auto/      UK automobile loan-level template (AUTL)
    cmbs/         servicer loan history report
    clo/          CLO trustee report, collateral portfolio
    assumptions/  rating criteria tables (illustrative)

Then run scripts/prepare_data.py to build the model tables in data/.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import write_raw

SEED = 2026
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

N_MONTHS = 60
START = pd.Period("2020-01", freq="M")
PERIODS = pd.period_range(START, periods=N_MONTHS, freq="M")


def logistic(x):
    return 1.0 / (1.0 + np.exp(-x))


# ---------------------------------------------------------------------------
# 1. Macro series
# ---------------------------------------------------------------------------
def make_macro(rng: np.random.Generator) -> pd.DataFrame:
    t = np.arange(N_MONTHS)
    # Unemployment: 4.0% rising to a peak of 7.4% around month 20, back to ~4.6%
    unemp = 4.0 + 3.4 * np.exp(-0.5 * ((t - 20) / 7.0) ** 2) + 0.6 * (t / N_MONTHS)
    unemp = unemp + rng.normal(0, 0.08, N_MONTHS)
    # House price index: 100, dips about 9% around month 22, then recovers
    hpi_growth = 0.0030 - 0.0110 * np.exp(-0.5 * ((t - 17) / 6.0) ** 2) + rng.normal(0, 0.002, N_MONTHS)
    hpi = 100 * np.cumprod(1 + hpi_growth)
    # Bank rate / SONIA-style overnight rate: low, then rising from month 26
    sonia = np.where(t < 26, 0.10, np.minimum(0.10 + 0.24 * (t - 26), 5.20))
    sonia = sonia + rng.normal(0, 0.01, N_MONTHS)
    sonia = np.clip(sonia, 0.05, None)
    # Systematic credit factor: standardised unemployment plus noise
    z = (unemp - 4.8) / 1.1 + rng.normal(0, 0.25, N_MONTHS)
    return pd.DataFrame(
        {
            "period": PERIODS.astype(str),
            "unemployment_rate": unemp.round(2),
            "hpi": hpi.round(2),
            "sonia": sonia.round(2),
            "credit_factor": z.round(4),
        }
    )


# ---------------------------------------------------------------------------
# 2. RMBS pool: static loan data at the cut-off date (31 Dec 2019)
# ---------------------------------------------------------------------------
REGIONS = [
    "London", "South East", "South West", "East of England", "West Midlands",
    "East Midlands", "Yorkshire", "North West", "North East", "Wales",
    "Scotland", "Northern Ireland",
]
REGION_P = [0.16, 0.15, 0.09, 0.10, 0.08, 0.07, 0.08, 0.10, 0.04, 0.05, 0.06, 0.02]


def make_rmbs_loans(rng: np.random.Generator, n: int = 10_000) -> pd.DataFrame:
    cutoff = pd.Timestamp("2019-12-31")
    orig_months_ago = rng.integers(6, 72, n)  # seasoning between 6 months and 6 years
    orig_date = pd.PeriodIndex([cutoff.to_period("M") - int(k) for k in orig_months_ago]).to_timestamp()
    term_years = rng.choice([20, 25, 30, 35], n, p=[0.15, 0.45, 0.30, 0.10])
    orig_balance = np.round(np.exp(rng.normal(np.log(170_000), 0.45, n)), -2)
    orig_balance = np.clip(orig_balance, 40_000, 1_200_000)
    orig_ltv = np.clip(rng.beta(5.5, 2.2, n) * 100, 35, 95).round(1)
    property_value = (orig_balance / (orig_ltv / 100)).round(-2)
    region = rng.choice(REGIONS, n, p=REGION_P)
    prop_type = rng.choice(["House", "Flat", "Bungalow"], n, p=[0.70, 0.24, 0.06])
    occupancy = rng.choice(["Owner-occupied", "Buy-to-let"], n, p=[0.85, 0.15])
    io_prob = np.where(occupancy == "Buy-to-let", 0.80, 0.06)
    repayment = np.where(rng.random(n) < io_prob, "Interest-only", "Repayment")
    employment = rng.choice(["Employed", "Self-employed"], n, p=[0.82, 0.18])
    income = np.round(orig_balance / rng.uniform(2.5, 4.5, n), -2)
    lti = (orig_balance / income).round(2)
    credit_score = np.clip(rng.normal(820, 70, n) - 1.2 * (orig_ltv - 75), 450, 999).round().astype(int)
    fixed_years = rng.choice([2, 5], n, p=[0.55, 0.45])
    product_end = (pd.Series(orig_date).dt.to_period("M") + 12 * fixed_years).dt.to_timestamp()
    rate = (1.4 + 0.012 * (orig_ltv - 60) + 0.35 * (fixed_years == 5)
            + 0.45 * (occupancy == "Buy-to-let") + rng.normal(0, 0.25, n))
    rate = np.clip(rate, 0.9, 5.5).round(2)

    # Current balance at cut-off: amortise repayment loans
    r = rate / 100 / 12
    nterm = term_years * 12
    pay = orig_balance * r / (1 - (1 + r) ** (-nterm))
    k = orig_months_ago
    bal_rep = orig_balance * (1 + r) ** k - pay * ((1 + r) ** k - 1) / r
    cur_balance = np.where(repayment == "Repayment", bal_rep, orig_balance).round(2)
    remaining_term = nterm - k
    current_ltv = (cur_balance / property_value * 100).round(1)

    df = pd.DataFrame(
        {
            "loan_id": [f"TB{i:06d}" for i in range(1, n + 1)],
            "origination_date": pd.Series(orig_date).dt.strftime("%Y-%m-%d"),
            "original_balance": orig_balance,
            "current_balance": cur_balance,
            "property_value": property_value,
            "original_ltv": orig_ltv,
            "current_ltv": current_ltv,
            "interest_rate": rate,
            "fixed_rate_years": fixed_years,
            "product_end_date": product_end.dt.strftime("%Y-%m-%d"),
            "term_months": nterm,
            "remaining_term_months": remaining_term,
            "seasoning_months": k,
            "repayment_type": repayment,
            "occupancy": occupancy,
            "property_type": prop_type,
            "region": region,
            "employment": employment,
            "income": income,
            "loan_to_income": lti,
            "credit_score": credit_score,
        }
    )
    return df


# ---------------------------------------------------------------------------
# 3. RMBS monthly performance (Markov chain driven by loan risk and macro)
# ---------------------------------------------------------------------------
STATES = ["C", "30", "60", "90", "DEF", "PRE"]


def simulate_rmbs_performance(rng, loans: pd.DataFrame, macro: pd.DataFrame):
    n = len(loans)
    # Loan-level risk score for the Current -> 30 transition (log-odds)
    x = (
        -6.55
        - 0.0090 * (loans["credit_score"].to_numpy() - 820)
        + 0.030 * (loans["original_ltv"].to_numpy() - 75)
        + 0.22 * (loans["loan_to_income"].to_numpy() - 3.5)
        + 0.35 * (loans["repayment_type"].to_numpy() == "Interest-only")
        + 0.40 * (loans["employment"].to_numpy() == "Self-employed")
        + 0.25 * (loans["occupancy"].to_numpy() == "Buy-to-let")
        + 0.15 * (loans["property_type"].to_numpy() == "Flat")
    )
    z = macro["credit_factor"].to_numpy()
    hpi = macro["hpi"].to_numpy()

    rate = loans["interest_rate"].to_numpy() / 100 / 12
    nterm = loans["term_months"].to_numpy()
    seas0 = loans["seasoning_months"].to_numpy()
    ltv0 = loans["original_ltv"].to_numpy()
    is_io = loans["repayment_type"].to_numpy() == "Interest-only"
    orig_bal = loans["original_balance"].to_numpy()
    pay = np.where(is_io, orig_bal * rate, orig_bal * rate / (1 - (1 + rate) ** (-nterm)))
    prod_end = pd.to_datetime(loans["product_end_date"]).dt.to_period("M")
    months_to_prod_end = np.array([(p - START).n for p in prod_end])  # month index of product end

    state = np.zeros(n, dtype=int)  # 0=C,1=30,2=60,3=90,4=DEF,5=PRE
    bal = loans["current_balance"].to_numpy().astype(float).copy()
    prop_value0 = loans["property_value"].to_numpy()
    rows = []
    default_rows = []

    for t in range(N_MONTHS):
        u = rng.random(n)
        new = state.copy()
        # From Current
        c = state == 0
        p30 = logistic(x + 0.45 * z[t])
        # Prepayment: base SMM 0.55%, spike in 3 months after product end, lower when LTV high
        since_end = t - months_to_prod_end
        spike = (since_end >= 0) & (since_end < 3)
        smm = 0.0060 * np.where(spike, 35.0, 1.0) * np.where(ltv0 > 85, 0.6, 1.0)
        smm = smm * (1 - 0.25 * np.clip(z[t], 0, None))
        go30 = c & (u < p30)
        gopre = c & (u >= p30) & (u < p30 + smm)
        new[go30] = 1
        new[gopre] = 5
        # From 30: cure / stay / roll
        s1 = state == 1
        roll1 = logistic(-0.45 + 0.35 * z[t] + 0.004 * (820 - loans["credit_score"].to_numpy()))
        cure1 = (1 - roll1) * 0.68
        new[s1 & (u < cure1)] = 0
        new[s1 & (u >= cure1) & (u < cure1 + roll1)] = 2
        # From 60
        s2 = state == 2
        roll2 = logistic(0.35 + 0.30 * z[t])
        cure2 = (1 - roll2) * 0.45
        back2 = (1 - roll2) * 0.25
        new[s2 & (u < cure2)] = 0
        new[s2 & (u >= cure2) & (u < cure2 + back2)] = 1
        new[s2 & (u >= cure2 + back2) & (u < cure2 + back2 + roll2)] = 3
        # From 90
        s3 = state == 3
        pdef = logistic(0.20 + 0.25 * z[t])
        cure3 = (1 - pdef) * 0.35
        back3 = (1 - pdef) * 0.20
        new[s3 & (u < cure3)] = 0
        new[s3 & (u >= cure3) & (u < cure3 + back3)] = 2
        new[s3 & (u >= cure3 + back3) & (u < cure3 + back3 + pdef)] = 4

        # Balances: performing loans amortise; arrears loans do not
        active = state <= 3
        paying = active & (new == 0) | (active & (new == state) & (state == 0))
        interest = bal * rate
        principal = np.where(is_io, 0.0, np.clip(pay - interest, 0, bal))
        principal = np.where(paying, principal, 0.0)
        bal_new = bal - principal
        # Prepaid loans repay fully
        prepaid_now = (new == 5) & (state != 5)
        prepay_amount = np.where(prepaid_now, bal_new, 0.0)
        # Defaults: record balance, recovery and loss
        defaulted_now = (new == 4) & (state != 4)
        for i in np.flatnonzero(defaulted_now):
            months_from_orig = seas0[i] + t
            value_now = prop_value0[i] * hpi[t] / 100 * (1 + 0.0015) ** (seas0[i])
            lag = int(rng.integers(9, 22))
            t_sale = min(t + lag, N_MONTHS - 1)
            value_sale = prop_value0[i] * hpi[t_sale] / 100 * (1 + 0.0015) ** (seas0[i])
            fsd = float(np.clip(rng.normal(0.22, 0.06), 0.05, 0.45))  # forced-sale discount
            costs = 0.045 * value_sale + 3_500
            accrued = bal_new[i] * rate[i] * lag
            exposure = bal_new[i] + accrued
            proceeds = max(value_sale * (1 - fsd) - costs, 0.0)
            recovery = min(proceeds, exposure)
            loss = exposure - recovery
            default_rows.append(
                {
                    "loan_id": loans["loan_id"].iat[i],
                    "default_period": str(PERIODS[t]),
                    "months_since_origination": int(months_from_orig),
                    "balance_at_default": round(bal_new[i], 2),
                    "indexed_value_at_default": round(value_now, 2),
                    "indexed_ltv_at_default": round(bal_new[i] / value_now * 100, 1),
                    "recovery_lag_months": lag,
                    "forced_sale_discount": round(fsd, 3),
                    "sale_value": round(value_sale, 2),
                    "sale_costs": round(costs, 2),
                    "accrued_interest": round(accrued, 2),
                    "exposure_at_default": round(exposure, 2),
                    "recovery": round(recovery, 2),
                    "loss": round(loss, 2),
                    "loss_severity": round(loss / exposure, 4) if exposure > 0 else 0.0,
                }
            )
        out_bal = np.where(new >= 4, 0.0, bal_new)
        alive_or_exit = (state <= 3)
        idx = np.flatnonzero(alive_or_exit)
        rows.append(
            pd.DataFrame(
                {
                    "loan_id": loans["loan_id"].to_numpy()[idx],
                    "period": str(PERIODS[t]),
                    "status": np.array(STATES)[new[idx]],
                    "opening_balance": bal[idx].round(2),
                    "scheduled_payment": pay[idx].round(2),
                    "principal_paid": principal[idx].round(2),
                    "interest_due": interest[idx].round(2),
                    "prepayment": prepay_amount[idx].round(2),
                    "default_balance": np.where(defaulted_now[idx], bal_new[idx], 0.0).round(2),
                    "closing_balance": out_bal[idx].round(2),
                }
            )
        )
        bal = out_bal
        state = new

    perf = pd.concat(rows, ignore_index=True)
    defaults = pd.DataFrame(default_rows)
    return perf, defaults


# ---------------------------------------------------------------------------
# 4. Deal structure
# ---------------------------------------------------------------------------
def make_deal(pool_balance: float) -> dict:
    tranches = [
        ("A", 0.880, 0.45, "AAA"),
        ("B", 0.040, 0.90, "AA"),
        ("C", 0.030, 1.40, "A"),
        ("D", 0.025, 2.20, "BBB"),
        ("E", 0.015, 3.50, "BB"),
        ("Z", 0.010, None, "NR"),
    ]
    return {
        "deal_name": "Thamesbridge Mortgages No. 1 plc",
        "originator": "Thamesbridge Building Society (fictional)",
        "closing_date": "2020-01-31",
        "cut_off_date": "2019-12-31",
        "pool_balance": round(pool_balance, 2),
        "payment_frequency": "monthly",
        "reference_rate": "SONIA",
        "senior_fees_bps_per_year": 20,
        "reserve_fund_target_pct": 0.015,
        "reserve_fund_funded_by": "subordinated loan from the originator",
        "excess_spread_used_to_cure_losses": True,
        "principal_waterfall": "sequential",
        "tranches": [
            {
                "class": c,
                "share_of_pool": s,
                "balance": round(pool_balance * s, 2),
                "margin_pct": m,
                "target_rating_illustrative": r,
            }
            for c, s, m, r in tranches
        ],
        "note": "Fictional transaction for teaching. Not based on any real deal.",
    }


# ---------------------------------------------------------------------------
# 5. CMBS loans
# ---------------------------------------------------------------------------
def make_cmbs(rng, n=120):
    ptype = rng.choice(["Office", "Retail", "Industrial", "Multifamily", "Hotel"], n,
                       p=[0.28, 0.22, 0.20, 0.20, 0.10])
    value = np.round(np.exp(rng.normal(np.log(30e6), 0.7, n)), -5)
    ltv = np.clip(rng.normal(62, 9, n), 35, 85).round(1)
    balance = np.round(value * ltv / 100, -3)
    cap_rate = {"Office": 6.0, "Retail": 7.0, "Industrial": 5.2, "Multifamily": 4.8, "Hotel": 8.0}
    noi = np.array([value[i] * cap_rate[p] / 100 for i, p in enumerate(ptype)])
    noi = noi * rng.normal(1.0, 0.07, n)
    rate = np.clip(rng.normal(4.6, 0.5, n), 3.0, 7.0).round(2)
    debt_service = balance * rate / 100  # interest-only
    dscr = (noi / debt_service).round(2)
    term = rng.choice([5, 7, 10], n, p=[0.5, 0.2, 0.3])
    shock = {"Office": -0.25, "Retail": -0.20, "Industrial": 0.05, "Multifamily": 0.02, "Hotel": -0.15}
    noi_stressed = noi * np.array([1 + shock[p] for p in ptype]) * rng.normal(1.0, 0.10, n)
    dscr_term = noi_stressed / debt_service
    p_term = logistic(-1.5 - 2.5 * (dscr_term - 1.3))
    term_default = rng.random(n) < p_term
    value_mat = noi_stressed / (np.array([cap_rate[p] for p in ptype]) / 100 + 0.005)
    ltv_mat = balance / value_mat * 100
    refi_ok = (ltv_mat < 80) & ((noi_stressed / (balance * 0.065)) > 1.25)
    maturity_default = (~term_default) & (~refi_ok) & (rng.random(n) < 0.60)
    severity = np.where(term_default | maturity_default,
                        np.clip(1 - (value_mat * 0.85) / balance, 0.0, 0.9), 0.0)
    return pd.DataFrame({
        "loan_id": [f"CM{i:04d}" for i in range(1, n + 1)],
        "property_type": ptype,
        "property_value": value,
        "loan_balance": balance,
        "ltv": ltv,
        "interest_rate": rate,
        "noi": noi.round(-2),
        "dscr": dscr,
        "term_years": term,
        "noi_after_stress_period": noi_stressed.round(-2),
        "value_at_maturity": value_mat.round(-3),
        "ltv_at_maturity": ltv_mat.round(1),
        "term_default": term_default.astype(int),
        "maturity_default": maturity_default.astype(int),
        "loss_severity": severity.round(4),
    })


# ---------------------------------------------------------------------------
# 6. Auto ABS loans (survival format)
# ---------------------------------------------------------------------------
def make_auto(rng, n=8000):
    product = rng.choice(["PCP", "HP"], n, p=[0.7, 0.3])
    used = rng.random(n) < 0.55
    score = np.clip(rng.normal(700, 80, n), 400, 999).round().astype(int)
    amount = np.round(np.exp(rng.normal(np.log(18_000), 0.4, n)), -2)
    term = rng.choice([36, 48, 60], n, p=[0.25, 0.55, 0.20])
    deposit_pct = np.clip(rng.normal(12, 6, n), 0, 40).round(1)
    apr = np.clip(rng.normal(8.5, 2.5, n) + 2.5 * used - 0.01 * (score - 700), 2.9, 24.9).round(1)
    # Weibull default time: scale depends on risk
    risk = (-0.012 * (score - 700) + 0.35 * used - 0.025 * (deposit_pct - 12)
            + 0.03 * (apr - 8.5))
    shape = 1.35
    scale_def = 420 * np.exp(-risk)  # months
    t_def = scale_def * rng.weibull(shape, n)
    t_pre = rng.exponential(110, n)
    t_obs = np.minimum(term, rng.integers(12, 61, n))  # observation window (censoring)
    event_time = np.minimum.reduce([t_def, t_pre, t_obs])
    event = np.where(event_time == t_def, "default",
                     np.where(event_time == t_pre, "prepaid", "censored"))
    months = np.maximum(np.ceil(event_time), 1).astype(int)
    recov = np.clip(rng.normal(0.55, 0.15, n) - 0.08 * used, 0.05, 0.95)
    return pd.DataFrame({
        "loan_id": [f"AU{i:05d}" for i in range(1, n + 1)],
        "product": product,
        "vehicle": np.where(used, "Used", "New"),
        "credit_score": score,
        "amount_financed": amount,
        "term_months": term,
        "deposit_pct": deposit_pct,
        "apr": apr,
        "months_observed": months,
        "outcome": event,
        "default": (event == "default").astype(int),
        "recovery_rate_if_default": np.where(event == "default", recov.round(3), np.nan),
    })


# ---------------------------------------------------------------------------
# 7. CLO portfolio and rating tables
# ---------------------------------------------------------------------------
RATINGS = ["AAA", "AA", "A", "BBB", "BB+", "BB", "BB-", "B+", "B", "B-", "CCC"]
# Illustrative one-year default probabilities (not any agency's published figures)
PD1 = {"AAA": 0.0001, "AA": 0.0002, "A": 0.0006, "BBB": 0.0018, "BB+": 0.0045, "BB": 0.0070,
       "BB-": 0.0110, "B+": 0.0180, "B": 0.0280, "B-": 0.0450, "CCC": 0.2000}


def make_rating_table():
    rows = []
    for r in RATINGS:
        p1 = PD1[r]
        for h in range(1, 11):
            # cumulative PD under a constant hazard
            rows.append({"rating": r, "horizon_years": h, "cumulative_pd": round(1 - (1 - p1) ** h, 6)})
    return pd.DataFrame(rows)


def make_clo(rng, n=150):
    industries = ["Software", "Healthcare", "Business services", "Chemicals", "Telecoms",
                  "Retail", "Leisure", "Media", "Construction", "Food and beverage",
                  "Automotive", "Insurance brokers", "Packaging", "Transport", "Utilities"]
    rating = rng.choice(RATINGS[4:], n, p=[0.06, 0.10, 0.16, 0.22, 0.24, 0.17, 0.05])
    par = np.round(rng.uniform(2.0, 6.0, n) * 1_000_000, -5)
    spread = np.array([{"BB+": 2.75, "BB": 3.0, "BB-": 3.25, "B+": 3.6, "B": 4.0, "B-": 4.6,
                        "CCC": 6.0}[r] for r in rating]) + rng.normal(0, 0.25, n)
    return pd.DataFrame({
        "obligor": [f"Obligor {i:03d}" for i in range(1, n + 1)],
        "industry": rng.choice(industries, n),
        "rating": rating,
        "par": par,
        "spread_pct": spread.round(2),
        "years_to_maturity": rng.integers(3, 8, n),
        "recovery_assumption": np.clip(rng.normal(0.62, 0.08, n), 0.35, 0.80).round(2),
        "one_year_pd": [PD1[r] for r in rating],
    })


def make_rating_stresses():
    # Illustrative rating-level stresses for the teaching model in Chapters 14 and 20.
    return pd.DataFrame({
        "rating": ["AAA", "AA", "A", "BBB", "BB", "B"],
        "default_multiple": [5.0, 4.0, 3.0, 2.0, 1.5, 1.2],
        "market_value_decline_pct": [45, 38, 32, 25, 18, 12],
        "prepayment_stress": ["low", "low", "low", "base", "base", "base"],
        "target_loss_quantile": [0.9999, 0.999, 0.995, 0.98, 0.95, 0.90],
        "note": ["Illustrative teaching values"] * 6,
    })


def main():
    DATA.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)
    macro = make_macro(rng)
    loans = make_rmbs_loans(rng)
    perf, defaults = simulate_rmbs_performance(rng, loans, macro)
    deal = make_deal(loans["current_balance"].sum())
    cmbs = make_cmbs(rng)
    auto = make_auto(rng)
    clo = make_clo(rng)

    write_raw.write_all(DATA / "raw", np.random.default_rng(SEED + 1),
                        macro, loans, perf, defaults, deal, cmbs, auto, clo,
                        make_rating_table(), make_rating_stresses())
    print("Raw files written to", DATA / "raw")


if __name__ == "__main__":
    main()
