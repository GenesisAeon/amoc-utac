"""Freshwater transport at 34°S — physics-based EWS (van Westen et al. 2024)."""

from __future__ import annotations

import numpy as np


class FreshwaterTransport:
    """
    Computes Fov = AMOC-induced freshwater transport at 34°S.

    Fov < 0 indicates AMOC bistability — the key early-warning signal from
    van Westen, Kliphuis & Dijkstra (2024), Science Advances 10(6), eadk1189.

    Simplified parameterisation:
        Fov ≈ α_Fov · Ψ · ΔS / S₀

    where Ψ is AMOC streamfunction strength [Sv], ΔS = S_Atlantic − S_ref,
    S₀ = 35 psu reference salinity.

    Maps to CREP R-component:
        R = sigmoid(−Fov / Fov_ref)
        Fov < 0  →  R > 0.5  (bistable, high resonance)
    """

    S0: float = 35.0        # Reference salinity [psu]
    S_ATLANTIC: float = 36.0
    S_PACIFIC: float = 34.5
    ALPHA_FOV: float = -0.05
    FOV_REF: float = 0.1    # Normalisation scale [Sv]

    def __init__(self, rng: np.random.Generator | None = None) -> None:
        self.rng = rng if rng is not None else np.random.default_rng(42)

    def compute(self, amoc_strength_sv: float, noise_scale: float = 0.01) -> float:
        """Return Fov [Sv] for a given AMOC strength.

        At present-day AMOC (~17–18 Sv) Fov ≈ −0.07 Sv (negative → bistable).
        As AMOC weakens toward collapse, Fov → 0.
        """
        delta_s = self.S_ATLANTIC - self.S_PACIFIC
        fov = self.ALPHA_FOV * amoc_strength_sv * delta_s / self.S0
        fov += float(self.rng.normal(0.0, noise_scale))
        return fov

    def is_bistable(self, fov: float) -> bool:
        """True when Fov < 0 (AMOC in bistable, tipping-prone regime)."""
        return fov < 0.0

    def to_crep_r(self, fov: float) -> float:
        """Map Fov to CREP R-component ∈ [0, 1].

        R = 1 / (1 + exp(Fov / Fov_ref))
        Negative Fov → R > 0.5 (bistability signal → high resonance).
        """
        return float(1.0 / (1.0 + np.exp(fov / self.FOV_REF)))

    def timeseries(self, amoc_sv: np.ndarray, noise_scale: float = 0.01) -> np.ndarray:
        """Compute Fov time series from an AMOC strength array [Sv]."""
        return np.array([self.compute(h, noise_scale) for h in amoc_sv])
