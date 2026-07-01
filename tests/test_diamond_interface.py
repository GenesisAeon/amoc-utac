"""Tests for the AmocUTAC Diamond-Template interface (Package 18)."""

from __future__ import annotations

import math

import pytest
from diamond_setup.protocol import NotConvergedError
from diamond_setup.validation import validate_diamond_instance

from amoc_utac.system import AmocUTAC


@pytest.fixture(scope="module")
def amoc() -> AmocUTAC:
    system = AmocUTAC(seed=42)
    system.run_cycle(duration_years=60)
    return system


# ── Diamond protocol compliance ───────────────────────────────────────────────


def test_not_converged_before_run_cycle():
    pkg = AmocUTAC(seed=42)
    with pytest.raises(NotConvergedError):
        pkg.get_crep_state()


def test_validate_diamond_instance():
    pkg = AmocUTAC(seed=42)
    assert validate_diamond_instance(pkg) == []


# ── run_cycle ────────────────────────────────────────────────────────────────


def test_run_cycle_returns_dict():
    result = AmocUTAC(seed=42).run_cycle(duration_years=30)
    assert isinstance(result, dict)


def test_run_cycle_has_required_keys():
    result = AmocUTAC(seed=42).run_cycle(duration_years=30)
    for key in (
        "years",
        "amoc_sv",
        "fov",
        "crep_state",
        "utac_state",
        "utac_extended",
        "utac_trajectory",
        "phase_events",
        "ethics",
    ):
        assert key in result, f"Missing key: {key}"


def test_run_cycle_time_series_lengths():
    result = AmocUTAC(seed=42).run_cycle(duration_years=30)
    n = len(result["years"])
    assert n == len(result["amoc_sv"])
    assert n == len(result["fov"])


# ── get_crep_state ────────────────────────────────────────────────────────────


def test_get_crep_state_keys(amoc: AmocUTAC):
    state = amoc.get_crep_state()
    assert set(state.keys()) == {"C", "R", "E", "P", "Gamma"}


def test_get_crep_state_range(amoc: AmocUTAC):
    state = amoc.get_crep_state()
    for k, v in state.items():
        assert 0.0 <= v <= 1.0, f"CREP component {k}={v} outside [0, 1]"


def test_gamma_is_in_medium_crep_range(amoc: AmocUTAC):
    gamma = amoc.get_crep_state()["Gamma"]
    assert 0.05 <= gamma <= 0.75, f"Γ = {gamma} outside medium-CREP zone"


# ── get_utac_state ────────────────────────────────────────────────────────────


def test_get_utac_state_keys(amoc: AmocUTAC):
    state = amoc.get_utac_state()
    assert set(state.keys()) == {"H", "H_star", "K_eff"}


def test_utac_h_normalized(amoc: AmocUTAC):
    state = amoc.get_utac_state()
    assert 0.0 < state["H"] <= 1.0


def test_utac_h_star_is_normalised_setpoint(amoc: AmocUTAC):
    state = amoc.get_utac_state()
    assert 0.0 < state["H_star"] <= 1.0
    assert state["K_eff"] == amoc.K


def test_utac_extended_has_dh_dt(amoc: AmocUTAC):
    extended = amoc._utac_internal
    assert extended is not None
    assert "dH_dt" in extended


# ── get_phase_events ─────────────────────────────────────────────────────────


def test_get_phase_events_is_list(amoc: AmocUTAC):
    events = amoc.get_phase_events()
    assert isinstance(events, list)


def test_phase_events_structure(amoc: AmocUTAC):
    events = amoc.get_phase_events()
    for ev in events:
        assert "type" in ev
        assert "year" in ev
        assert "threshold_fraction" in ev


# ── to_zenodo_record ─────────────────────────────────────────────────────────


def test_to_zenodo_record_structure(amoc: AmocUTAC):
    record = amoc.to_zenodo_record()
    for key in ("title", "creators", "keywords", "license", "custom_fields"):
        assert key in record


def test_to_zenodo_record_contains_crep(amoc: AmocUTAC):
    record = amoc.to_zenodo_record()
    assert "crep_state" in record["custom_fields"]
    assert "Gamma" in record["custom_fields"]["crep_state"]


def test_to_zenodo_record_ethics_present(amoc: AmocUTAC):
    record = amoc.to_zenodo_record()
    assert "ethics" in record["custom_fields"]
    assert "level" in record["custom_fields"]["ethics"]


# ── predict_tipping_year ──────────────────────────────────────────────────────


def test_predict_tipping_year_keys(amoc: AmocUTAC):
    pred = amoc.predict_tipping_year()
    for key in (
        "utac_central_year",
        "utac_5pct",
        "utac_95pct",
        "ditlevsen_2023_central",
        "gamma_amoc",
    ):
        assert key in pred


def test_ditlevsen_reference_year(amoc: AmocUTAC):
    assert amoc.predict_tipping_year()["ditlevsen_2023_central"] == 2057


# ── Central formula verification ─────────────────────────────────────────────


def test_gamma_amoc_formula():
    gamma = math.atanh(0.50) / 2.2
    assert abs(gamma - 0.251) < 0.002


def test_crep_spectrum_entry():
    entry = AmocUTAC.crep_spectrum_entry()
    assert entry["package_id"] == 18
    assert abs(entry["gamma"] - 0.251) < 0.002
    assert entry["eta"] == 0.50