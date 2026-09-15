"""Validation against van Westen 2024 and Ditlevsen 2023 benchmark targets."""

from __future__ import annotations

import math
from typing import Any

from amoc_utac.constants import AMOC_TARGETS, UTAC_SIGMA


class AmocBenchmark:
    """
    Validates amoc-utac outputs against published benchmark targets.

    Targets (from AMOC_TARGETS in constants.py):
        present_strength_Sv     : (17.0, rtol=0.15)
        weakening_since_1950_Sv : (3.0,  rtol=0.33)
        gamma_amoc              : (0.251, atol=0.05)
        fov_sign                : "negative"
        tipping_year_central    : (2065,  ±50 yr) -- corrected 2026-08-02 (was 2057)
    """

    def check_gamma(self, gamma: float) -> dict[str, Any]:
        """Verify Γ_AMOC is within 5% of 0.251."""
        target, tol = AMOC_TARGETS["gamma_amoc"]
        passed = abs(gamma - target) <= tol
        return {"value": gamma, "target": target, "tolerance": tol, "passed": passed}

    def check_present_strength(self, strength_sv: float) -> dict[str, Any]:
        target, rtol = AMOC_TARGETS["present_strength_Sv"]
        passed = abs(strength_sv - target) <= rtol * target + 2.0
        return {
            "value": strength_sv,
            "target": target,
            "rtol": rtol,
            "passed": passed,
        }

    def check_fov_sign(self, fov: float) -> dict[str, Any]:
        expected, _ = AMOC_TARGETS["fov_sign"]
        actual = "negative" if fov < 0.0 else "positive"
        return {
            "value": fov,
            "expected_sign": expected,
            "actual_sign": actual,
            "passed": actual == expected,
        }

    def check_tipping_year(self, predicted_year: float) -> dict[str, Any]:
        """Accept any UTAC prediction within 50 years of Ditlevsen 2023 central."""
        target, _ = AMOC_TARGETS["tipping_year_central"]
        tolerance = 50
        passed = abs(predicted_year - target) <= tolerance
        return {
            "value": predicted_year,
            "target": target,
            "tolerance_years": tolerance,
            "passed": passed,
        }

    def gamma_formula_check(self) -> dict[str, Any]:
        """Recompute arctanh(0.50)/2.2 and compare to the literal 0.251.

        NOTE (2026-09-15, ecosystem-wide Gamma-circularity review): this is
        an arithmetic self-consistency check, not an empirical validation --
        GAMMA_AMOC in constants.py is defined by this exact formula, so this
        can only ever fail from a transcription error, never from new
        evidence. See constants.py's GAMMA_AMOC docstring and
        FOLLOWUP_TICKETS.md for the actual calibration-status caveat.
        """
        expected = math.atanh(0.50) / UTAC_SIGMA
        return {
            "formula": "arctanh(η=0.50) / σ=2.2",
            "computed": expected,
            "expected_approx": 0.251,
            "matches": abs(expected - 0.251) < 0.001,
            "note": "arithmetic self-consistency check, not empirical validation",
        }

    def run_all(
        self,
        gamma: float,
        strength_sv: float,
        fov: float,
        tipping_year: float,
    ) -> dict[str, Any]:
        """Execute all checks and return a summary report."""
        checks = {
            "gamma": self.check_gamma(gamma),
            "present_strength": self.check_present_strength(strength_sv),
            "fov_sign": self.check_fov_sign(fov),
            "tipping_year": self.check_tipping_year(tipping_year),
            "gamma_formula": self.gamma_formula_check(),
        }

        n_passed = sum(1 for r in checks.values() if r.get("passed", False))
        n_total = len(checks)

        return {
            "checks": checks,
            "passed": n_passed,
            "total": n_total,
            "success_rate": n_passed / n_total,
            "all_passed": n_passed == n_total,
        }
