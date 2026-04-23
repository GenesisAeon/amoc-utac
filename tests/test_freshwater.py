"""Tests for FreshwaterTransport (van Westen 2024 Fov EWS)."""

from __future__ import annotations

import numpy as np
import pytest

from amoc_utac.freshwater import FreshwaterTransport


@pytest.fixture
def fwt() -> FreshwaterTransport:
    return FreshwaterTransport(rng=np.random.default_rng(42))


# ── Physical correctness ─────────────────────────────────────────────────────


def test_fov_negative_at_present_amoc(fwt: FreshwaterTransport):
    """Present-day AMOC (~17 Sv) must give Fov < 0 (bistability indicator)."""
    fov = fwt.compute(amoc_strength_sv=17.0, noise_scale=0.0)
    assert fov < 0.0, f"Expected Fov < 0 (bistable regime), got {fov}"


def test_fov_positive_at_zero_amoc(fwt: FreshwaterTransport):
    """With near-zero AMOC the freshwater signal should be negligible (→ 0)."""
    fov = fwt.compute(amoc_strength_sv=0.0, noise_scale=0.0)
    assert abs(fov) < 1e-6


def test_fov_scales_with_amoc(fwt: FreshwaterTransport):
    """Fov magnitude should increase with AMOC strength (stronger → more negative)."""
    fov_weak = fwt.compute(amoc_strength_sv=5.0, noise_scale=0.0)
    fov_strong = fwt.compute(amoc_strength_sv=20.0, noise_scale=0.0)
    assert fov_strong < fov_weak


# ── Bistability check ────────────────────────────────────────────────────────


def test_is_bistable_negative(fwt: FreshwaterTransport):
    assert fwt.is_bistable(-0.05) is True


def test_is_bistable_positive(fwt: FreshwaterTransport):
    assert fwt.is_bistable(0.05) is False


def test_is_bistable_zero(fwt: FreshwaterTransport):
    assert fwt.is_bistable(0.0) is False


# ── CREP R-component ─────────────────────────────────────────────────────────


def test_to_crep_r_range(fwt: FreshwaterTransport):
    for fov in [-0.3, -0.1, 0.0, 0.1, 0.3]:
        r = fwt.to_crep_r(fov)
        assert 0.0 <= r <= 1.0, f"R={r} out of [0,1] for Fov={fov}"


def test_to_crep_r_negative_fov_gives_high_r(fwt: FreshwaterTransport):
    """Negative Fov → R > 0.5 (bistable → high resonance contribution)."""
    r = fwt.to_crep_r(-0.1)
    assert r > 0.5


def test_to_crep_r_positive_fov_gives_low_r(fwt: FreshwaterTransport):
    r = fwt.to_crep_r(0.1)
    assert r < 0.5


def test_to_crep_r_zero_fov_is_half(fwt: FreshwaterTransport):
    r = fwt.to_crep_r(0.0)
    assert abs(r - 0.5) < 1e-6


# ── Time series ──────────────────────────────────────────────────────────────


def test_timeseries_length(fwt: FreshwaterTransport):
    amoc = np.linspace(18.0, 5.0, 80)
    fov_series = fwt.timeseries(amoc, noise_scale=0.0)
    assert len(fov_series) == 80


def test_timeseries_all_negative_noiseless(fwt: FreshwaterTransport):
    """Without noise, all Fov values should be negative for AMOC > 0."""
    amoc = np.linspace(1.0, 20.0, 50)
    fov_series = fwt.timeseries(amoc, noise_scale=0.0)
    assert (fov_series < 0).all()
