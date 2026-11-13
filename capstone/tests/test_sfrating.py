"""Unit tests for the capstone package (Chapter 22). Run: pytest capstone/tests"""
import numpy as np
import pandas as pd
import pytest

from sfrating import cashflow, clo, numerics, rollrate, survival, vasicek
from sfrating.merton import merton_pd


def test_bisection_finds_square_root_of_two():
    assert numerics.bisection(lambda x: x * x - 2, 0, 2) == pytest.approx(2 ** 0.5, abs=1e-9)


def test_newton_matches_bisection():
    root = numerics.newton(lambda x: x ** 3 - x - 1, lambda x: 3 * x ** 2 - 1, 1.5)
    assert root == pytest.approx(numerics.bisection(lambda x: x ** 3 - x - 1, 1, 2), abs=1e-8)


def test_simpson_integrates_cubic_exactly():
    assert numerics.simpson(lambda x: x ** 3, 0, 2, n=10) == pytest.approx(4.0, abs=1e-12)


def test_transition_matrix_rows_sum_to_one():
    perf = pd.DataFrame({"loan_id": ["a", "a", "b", "b"], "period": ["1", "2", "1", "2"],
                         "status": ["C", "30", "C", "PRE"]})
    P = rollrate.transition_matrix(perf)
    assert np.allclose(P.sum(axis=1), 1.0)
    assert P.loc["DEF", "DEF"] == 1.0


def test_projection_conserves_probability():
    P = pd.DataFrame(np.eye(6), index=rollrate.STATES, columns=rollrate.STATES)
    out = rollrate.project(P, {"C": 1.0}, 12)
    assert np.allclose(out.sum(axis=1), 1.0)


def test_kaplan_meier_simple_case():
    km = survival.kaplan_meier([1, 2, 2, 3], [1, 1, 0, 1])
    assert km["survival"].iloc[0] == pytest.approx(0.75)
    assert km["survival"].iloc[1] == pytest.approx(0.75 * (1 - 1 / 3))


def test_vasicek_quantile_inverts_cdf():
    x = vasicek.vasicek_quantile(0.99, 0.02, 0.15)
    assert vasicek.vasicek_cdf(x, 0.02, 0.15) == pytest.approx(0.99)


def test_rho_estimate_recovers_simulated_value():
    rng = np.random.default_rng(1)
    z = rng.standard_normal(4000)
    dr = vasicek.conditional_pd(0.03, 0.12, z)
    pd_hat, rho_hat = vasicek.estimate_rho_moments(dr)
    assert rho_hat == pytest.approx(0.12, abs=0.01)
    assert pd_hat == pytest.approx(0.03, abs=0.003)


def test_merton_pd_falls_when_assets_rise():
    assert merton_pd(120, 100, 0.05, 0.2, 1) < merton_pd(110, 100, 0.05, 0.2, 1)


def test_bet_probabilities_sum_to_one():
    d = clo.bet_loss_distribution(40, 0.2, 0.4)
    assert d["probability"].sum() == pytest.approx(1.0)


def test_pool_without_losses_repays_every_class():
    deal = {"pool_balance": 100.0, "reserve_fund_target_pct": 0.01,
            "senior_fees_bps_per_year": 20,
            "tranches": [{"class": "A", "share_of_pool": 0.9, "balance": 90.0, "margin_pct": 0.5},
                         {"class": "Z", "share_of_pool": 0.1, "balance": 10.0, "margin_pct": None}]}
    pool = cashflow.project_pool(100.0, 120, cum_default=0.0, cpr=0.1, months=130)
    res = cashflow.run_waterfall(pool, deal, sonia_pct=1.0)
    assert res["tranche_loss"]["A"] == pytest.approx(0.0, abs=1e-9)
    assert res["tranche_loss"]["Z"] == pytest.approx(0.0, abs=1e-9)
