"""Tests for TippingPredictor (UTAC and statistical AMOC tipping estimates)."""

from __future__ import annotations

import numpy as np
import pytest

from amoc_utac.tipping_predictor import TippingPredictor


@pytest.fixture(scope="module")
def predictor() -> TippingPredictor:
    return TippingPredictor(seed=42)


# ── Fixed point ───────────────────────────────────────────────────────────────


def test_h_star_at_gamma_amoc(predictor: TippingPredictor):
    """H* at Γ_AMOC ≈ 0.251 should be ~50% of K."""
    h_star = predictor.h_star(0.251)
    ratio = h_star / predictor.K
    assert abs(ratio - 0.50) < 0.02, f"η = {ratio:.3f}, expected ≈ 0.50"


def test_h_star_increases_with_gamma(predictor: TippingPredictor):
    h1 = predictor.h_star(0.1)
    h2 = predictor.h_star(0.5)
    assert h2 > h1


def test_h_star_bounded_by_k(predictor: TippingPredictor):
    for gamma in (0.0, 0.25, 0.50, 1.0):
        assert predictor.h_star(gamma) <= predictor.K


# ── ODE integration ───────────────────────────────────────────────────────────


def test_simulate_utac_keys(predictor: TippingPredictor):
    result = predictor.simulate_utac((0.0, 30.0), H0=18.0)
    for key in ("t", "H", "H_normalised", "gamma", "H_star"):
        assert key in result


def test_simulate_utac_positive_values(predictor: TippingPredictor):
    result = predictor.simulate_utac((0.0, 30.0), H0=18.0)
    assert (result["H"] >= 0.0).all()


def test_simulate_utac_weakening_trend(predictor: TippingPredictor):
    """With positive gamma_trend, AMOC should weaken over time."""
    result = predictor.simulate_utac((0.0, 60.0), H0=18.0, gamma_trend=0.002)
    assert result["H"][-1] < result["H"][0]


# ── Tipping year prediction ───────────────────────────────────────────────────


def test_predict_tipping_year_keys(predictor: TippingPredictor):
    pred = predictor.predict_tipping_year()
    for key in (
        "utac_central_year", "utac_5pct", "utac_95pct",
        "ditlevsen_2023_central", "gamma_amoc", "threshold_sv",
    ):
        assert key in pred


def test_ditlevsen_reference(predictor: TippingPredictor):
    assert predictor.predict_tipping_year()["ditlevsen_2023_central"] == 2057


def test_utac_tipping_plausible_range(predictor: TippingPredictor):
    pred = predictor.predict_tipping_year()
    year = pred["utac_central_year"]
    assert 2020.0 <= year <= 2200.0, f"Tipping year {year} outside plausible range"


def test_5pct_le_central_le_95pct(predictor: TippingPredictor):
    pred = predictor.predict_tipping_year()
    assert pred["utac_5pct"] <= pred["utac_central_year"]
    assert pred["utac_central_year"] <= pred["utac_95pct"]


# ── Statistical extrapolation ─────────────────────────────────────────────────


def test_statistical_estimate_keys(predictor: TippingPredictor):
    years = np.arange(1950.0, 2024.0)
    amoc = 20.0 - 0.08 * (years - 1950.0)
    result = predictor.statistical_tipping_estimate(amoc, years)
    for key in ("trend_sv_per_year", "r_squared", "statistical_crossing_year"):
        assert key in result


def test_statistical_negative_trend(predictor: TippingPredictor):
    years = np.arange(1950.0, 2024.0)
    amoc = 20.0 - 0.1 * (years - 1950.0)
    result = predictor.statistical_tipping_estimate(amoc, years)
    assert result["trend_sv_per_year"] < 0.0


def test_statistical_r_squared_high_for_linear(predictor: TippingPredictor):
    years = np.arange(1950.0, 2024.0)
    amoc = 20.0 - 0.1 * (years - 1950.0) + np.random.default_rng(0).normal(0, 0.1, 74)
    result = predictor.statistical_tipping_estimate(amoc, years)
    assert result["r_squared"] > 0.90
