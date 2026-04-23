"""AMOC-specific CREP tensor computation."""

from __future__ import annotations

import numpy as np


class CREPAmocTensor:
    """
    Computes the four-component CREP tensor Γ for the AMOC system.

    Components (all ∈ [0, 1]):
        C  — autocorrelation increase (critical slowing down)
        R  — freshwater transport resonance at 34°S  (van Westen 2024)
        E  — multi-scale variance emergence
        P  — permutation entropy of RAPID fingerprint (raw; low = ordered)

    Composition:
        Γ = w_C·C + w_R·R + w_E·E + w_P·(1 − P)

    Calibrated so that present-day AMOC gives Γ ≈ 0.251
    (medium-CREP regime; η = 50% efficiency setpoint).
    """

    SIGMA: float = 2.2
    WEIGHTS: dict[str, float] = {"C": 0.30, "R": 0.35, "E": 0.20, "P": 0.15}

    def __init__(self) -> None:
        self._last_components: dict[str, float] = {}

    # ── Individual components ────────────────────────────────────────────────

    def compute_c(self, ar1_series: np.ndarray) -> float:
        """C: trend-normalised AR(1) increase — critical slowing-down signal.

        Measures the *increase* in AR(1) from baseline to present, normalised
        by the remaining room to AR(1)=1.  C=0 at no change, C=1 when AR(1)
        has risen from baseline all the way to 1 (full CSD).
        """
        valid = ar1_series[~np.isnan(ar1_series)]
        if len(valid) < 20:
            return 0.0
        n_win = max(10, len(valid) // 6)
        baseline = float(np.nanmean(valid[:n_win]))
        current = float(np.nanmean(valid[-n_win:]))
        headroom = 1.0 - baseline
        if headroom < 1e-6:
            return 1.0
        return float(np.clip((current - baseline) / headroom, 0.0, 1.0))

    def compute_r(self, fov: float, fov_ref: float = 0.1) -> float:
        """R: freshwater-transport resonance.

        R = sigmoid(−Fov / Fov_ref).
        Fov < 0 (bistable) → R > 0.5.
        """
        return float(1.0 / (1.0 + np.exp(fov / fov_ref)))

    def compute_e(
        self,
        amoc_series: np.ndarray,
        short_window: int = 10,
        long_window: int = 50,
    ) -> float:
        """E: short/long variance ratio — emergence of instability."""
        if len(amoc_series) < long_window:
            return 0.0
        var_short = float(np.var(amoc_series[-short_window:]))
        var_long = float(np.var(amoc_series[-long_window:]))
        if var_long < 1e-10:
            return 0.0
        return float(np.clip(var_short / var_long / 4.0, 0.0, 1.0))

    def compute_p(self, pe_series: np.ndarray) -> float:
        """P: current permutation entropy level ∈ [0, 1].

        Composed into Γ as (1 − P): lower entropy → higher CREP contribution.
        """
        valid = pe_series[~np.isnan(pe_series)]
        if len(valid) == 0:
            return 0.5
        return float(np.clip(np.mean(valid[-min(10, len(valid)) :]), 0.0, 1.0))

    # ── Composite Γ ──────────────────────────────────────────────────────────

    def compute_gamma(self, C: float, R: float, E: float, P: float) -> float:
        """Compute composite CREP Γ from the four components."""
        w = self.WEIGHTS
        gamma = w["C"] * C + w["R"] * R + w["E"] * E + w["P"] * (1.0 - P)
        self._last_components = {"C": C, "R": R, "E": E, "P": P, "Gamma": gamma}
        return float(np.clip(gamma, 0.0, 1.0))

    def compute_all(
        self,
        ar1_series: np.ndarray,
        fov: float,
        amoc_series: np.ndarray,
        pe_series: np.ndarray,
    ) -> dict[str, float]:
        """Compute all components and return full CREP state dict."""
        C = self.compute_c(ar1_series)
        R = self.compute_r(fov)
        E = self.compute_e(amoc_series)
        P = self.compute_p(pe_series)
        gamma = self.compute_gamma(C, R, E, P)
        return {"C": C, "R": R, "E": E, "P": P, "Gamma": gamma}

    @property
    def last_components(self) -> dict[str, float]:
        return dict(self._last_components)
