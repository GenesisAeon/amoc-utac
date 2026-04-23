"""Tests for AmocFingerprintIndex (SST-based AMOC proxy)."""

from __future__ import annotations

import numpy as np
import pytest

from amoc_utac.fingerprint import AmocFingerprintIndex


@pytest.fixture
def fp() -> AmocFingerprintIndex:
    return AmocFingerprintIndex(seed=42)


# ── Synthetic index ───────────────────────────────────────────────────────────


def test_synthetic_index_shape(fp: AmocFingerprintIndex):
    years = np.arange(1950, 2101)
    index = fp.synthetic_index(years)
    assert index.shape == years.shape


def test_synthetic_index_non_negative(fp: AmocFingerprintIndex):
    years = np.arange(1950, 2101)
    index = fp.synthetic_index(years)
    assert (index >= 0.0).all()


def test_synthetic_index_weakening_trend(fp: AmocFingerprintIndex):
    """Mean of first 30 years should exceed mean of last 30 years."""
    years = np.arange(1950, 2101)
    index = fp.synthetic_index(years, noise_std=0.0)
    assert index[:30].mean() > index[-30:].mean()


# ── Normalisation ─────────────────────────────────────────────────────────────


def test_normalise_zero(fp: AmocFingerprintIndex):
    assert fp.normalise_to_utac(np.array([0.0]))[0] == pytest.approx(0.0)


def test_normalise_reference(fp: AmocFingerprintIndex):
    assert fp.normalise_to_utac(np.array([18.0]))[0] == pytest.approx(1.0)


def test_normalise_half(fp: AmocFingerprintIndex):
    assert fp.normalise_to_utac(np.array([9.0]))[0] == pytest.approx(0.5)


# ── AR(1) autocorrelation ─────────────────────────────────────────────────────


def test_ar1_length(fp: AmocFingerprintIndex):
    series = np.random.default_rng(42).normal(0, 1, 100)
    ar1 = fp.autocorrelation_ar1(series, window=20)
    assert len(ar1) == len(series)


def test_ar1_nan_before_window(fp: AmocFingerprintIndex):
    series = np.random.default_rng(42).normal(0, 1, 100)
    ar1 = fp.autocorrelation_ar1(series, window=30)
    assert np.isnan(ar1[:30]).all()


def test_ar1_range(fp: AmocFingerprintIndex):
    series = np.random.default_rng(42).normal(0, 1, 200)
    ar1 = fp.autocorrelation_ar1(series, window=30)
    valid = ar1[~np.isnan(ar1)]
    assert (np.abs(valid) <= 1.0).all()


# ── Permutation entropy ───────────────────────────────────────────────────────


def test_pe_length(fp: AmocFingerprintIndex):
    series = np.random.default_rng(42).normal(0, 1, 100)
    pe = fp.permutation_entropy(series, order=3, window=20)
    assert len(pe) == len(series)


def test_pe_range(fp: AmocFingerprintIndex):
    series = np.random.default_rng(42).normal(0, 1, 200)
    pe = fp.permutation_entropy(series, order=3, window=30)
    valid = pe[~np.isnan(pe)]
    assert (valid >= 0.0).all()
    assert (valid <= 1.0).all()


def test_pe_random_near_one(fp: AmocFingerprintIndex):
    """Fully random signal should have PE close to 1 (maximum entropy)."""
    rng = np.random.default_rng(0)
    series = rng.normal(0, 1, 500)
    pe = fp.permutation_entropy(series, order=3, window=50)
    valid = pe[~np.isnan(pe)]
    assert float(np.mean(valid)) > 0.85
