"""TensionMetric — measures AMOC system tension for the Ethics-Gate (Phase H)."""

from __future__ import annotations

import numpy as np

from amoc_utac.constants import GAMMA_AMOC


class TensionMetric:
    """
    Quantifies how urgently the AMOC system is approaching its tipping point.

    Tension ∈ [0, 1] is computed from the CREP state and UTAC trajectory:

        τ_Γ   = Γ / Γ_max                      (CREP loading fraction)
        τ_H   = 1 − H / K                       (fractional AMOC weakening)
        τ_dH  = sigmoid(−dH/dt / dH_scale)      (rate-of-change signal)

        tension = w_Γ·τ_Γ + w_H·τ_H + w_dH·τ_dH

    Tension > 0.70 → ethics warning.
    Tension > 0.90 → ethics block (publication requires human review).
    """

    GAMMA_MAX: float = 1.0
    DH_SCALE: float = 0.5      # [Sv/yr] normalisation for dH/dt
    WEIGHTS: dict[str, float] = {"gamma": 0.40, "h": 0.35, "dh": 0.25}

    def __init__(self) -> None:
        self._current_tension: float = 0.0
        self._components: dict[str, float] = {}

    def update(
        self,
        gamma: float,
        H: float,
        K: float,
        dH_dt: float,
    ) -> float:
        """Compute and cache current tension from UTAC state.

        Args:
            gamma:  Current CREP Γ value.
            H:      Current AMOC strength [Sv].
            K:      Reference AMOC strength (K_eff) [Sv].
            dH_dt:  Current rate of change [Sv/yr].

        Returns: tension ∈ [0, 1].
        """
        tau_gamma = float(np.clip(gamma / self.GAMMA_MAX, 0.0, 1.0))
        tau_h = float(np.clip(1.0 - H / K, 0.0, 1.0))
        # Negative dH/dt (weakening) increases tension
        tau_dh = float(1.0 / (1.0 + np.exp(dH_dt / self.DH_SCALE)))

        w = self.WEIGHTS
        tension = w["gamma"] * tau_gamma + w["h"] * tau_h + w["dh"] * tau_dh

        self._current_tension = float(np.clip(tension, 0.0, 1.0))
        self._components = {
            "tau_gamma": tau_gamma,
            "tau_h": tau_h,
            "tau_dh": tau_dh,
            "tension": self._current_tension,
        }
        return self._current_tension

    def get_current_tension(self) -> float:
        """Return the most recently computed tension value."""
        return self._current_tension

    @property
    def components(self) -> dict[str, float]:
        """Breakdown of the tension into its components."""
        return dict(self._components)
