"""UTAC-based and statistical AMOC tipping-time estimators."""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import linregress

from amoc_utac.constants import (
    CHAVENT_2026_WEAKENING_BY,
    DITLEVSEN_2023_CENTRAL,
    DITLEVSEN_2023_RANGE,
    GAMMA_AMOC,
    UTAC_R,
    UTAC_SIGMA,
)


class TippingPredictor:
    """
    AMOC tipping-year prediction via UTAC dynamics and linear extrapolation.

    UTAC ODE:
        dH/dt = r · H · (tanh(σ · Γ(t)) − H/K)

    As Γ increases under freshwater forcing, the fixed point
        H*(t) = K · tanh(σ · Γ(t))
    drifts below K, pulling H toward lower AMOC states.
    At Γ_AMOC ≈ 0.251, H* ≈ 0.50 K (50% weakening threshold).

    Compares with:
    - Ditlevsen & Ditlevsen (2023) Nature Commun.: central 2057, range 2025–2095
    - Chavent et al. (2026) Science Advances: 50% weakening by 2100
    """

    def __init__(
        self,
        K: float = 18.0,
        r: float = UTAC_R,
        sigma: float = UTAC_SIGMA,
        gamma_amoc: float = GAMMA_AMOC,
        seed: int = 42,
    ) -> None:
        self.K = K
        self.r = r
        self.sigma = sigma
        self.gamma_amoc = gamma_amoc
        self.rng = np.random.default_rng(seed)

    # ── UTAC fixed point ─────────────────────────────────────────────────────

    def h_star(self, gamma: float) -> float:
        """UTAC fixed point: H*(Γ) = K · tanh(σ · Γ)."""
        return self.K * float(np.tanh(self.sigma * gamma))

    # ── ODE integration ──────────────────────────────────────────────────────

    def _ode(self, t: float, y: list[float], gamma_func) -> list[float]:  # type: ignore[type-arg]
        H = float(y[0])
        gamma = float(gamma_func(t))
        h_star = self.K * float(np.tanh(self.sigma * gamma))
        dH = self.r * H * (h_star / self.K - H / self.K)
        return [dH]

    def simulate_utac(
        self,
        t_span: tuple[float, float],
        H0: float | None = None,
        gamma_trend: float = 0.0015,
    ) -> dict:
        """Integrate AMOC UTAC ODE with linearly increasing Γ(t).

        gamma_trend: Γ increase per year (represents freshwater forcing growth).
        Returns dict with keys t, H, H_normalised, gamma, H_star.
        """
        if H0 is None:
            H0 = self.h_star(self.gamma_amoc)

        def gamma_func(t: float) -> float:
            return min(self.gamma_amoc + gamma_trend * t, 0.95)

        n_steps = int(t_span[1] - t_span[0]) + 1
        t_eval = np.linspace(t_span[0], t_span[1], n_steps)

        sol = solve_ivp(
            self._ode,
            t_span,
            [H0],
            args=(gamma_func,),
            t_eval=t_eval,
            method="RK45",
            rtol=1e-6,
            atol=1e-8,
            dense_output=False,
        )

        gamma_arr = np.array([gamma_func(t) for t in sol.t])
        return {
            "t": sol.t,
            "H": sol.y[0],
            "H_normalised": sol.y[0] / self.K,
            "gamma": gamma_arr,
            "H_star": np.array([self.h_star(g) for g in gamma_arr]),
        }

    # ── Tipping year prediction ───────────────────────────────────────────────

    def predict_tipping_year(
        self,
        start_year: int = 2024,
        gamma_trend: float = 0.0015,
        tipping_threshold: float = 0.50,
    ) -> dict:
        """Predict year AMOC crosses H = tipping_threshold · K (default: 50%).

        Runs 100-member Monte Carlo ensemble for uncertainty bounds.
        Compares with Ditlevsen 2023 and Chavent 2026 published estimates.
        """
        H0 = self.h_star(self.gamma_amoc)
        threshold_sv = tipping_threshold * self.K

        # Deterministic run
        sim = self.simulate_utac((0.0, 120.0), H0=H0, gamma_trend=gamma_trend)
        below = sim["H"] < threshold_sv
        if below.any():
            utac_year = float(start_year + sim["t"][int(np.argmax(below))])
        else:
            utac_year = float(start_year + 120)

        # Monte Carlo uncertainty
        mc_years: list[float] = []
        for _ in range(100):
            g_trend = float(self.rng.normal(gamma_trend, gamma_trend * 0.20))
            h0_mc = float(self.rng.normal(H0, H0 * 0.05))
            g_trend = float(np.clip(g_trend, 1e-4, 0.01))
            h0_mc = float(np.clip(h0_mc, 0.1, self.K))
            sim_mc = self.simulate_utac((0.0, 120.0), H0=h0_mc, gamma_trend=g_trend)
            b = sim_mc["H"] < threshold_sv
            if b.any():
                mc_years.append(float(start_year + sim_mc["t"][int(np.argmax(b))]))

        mc_arr = np.array(mc_years) if mc_years else np.array([utac_year])

        return {
            "utac_central_year": utac_year,
            "utac_5pct": float(np.percentile(mc_arr, 5)),
            "utac_95pct": float(np.percentile(mc_arr, 95)),
            "ditlevsen_2023_central": DITLEVSEN_2023_CENTRAL,
            "ditlevsen_2023_range": DITLEVSEN_2023_RANGE,
            "chavent_2026_50pct_by": CHAVENT_2026_WEAKENING_BY,
            "threshold_sv": float(threshold_sv),
            "threshold_fraction": tipping_threshold,
            "H0_sv": float(H0),
            "gamma_amoc": self.gamma_amoc,
        }

    # ── Statistical extrapolation ─────────────────────────────────────────────

    def statistical_tipping_estimate(
        self,
        amoc_series: np.ndarray,
        years: np.ndarray,
    ) -> dict:
        """Linear-trend extrapolation to 50% weakening.

        Cross-check with UTAC prediction (linear model underestimates urgency
        because it ignores critical slowing down).
        """
        result = linregress(years, amoc_series)
        slope = float(result.slope)
        intercept = float(result.intercept)

        target_sv = 0.50 * float(amoc_series[-1])
        crossing_year = float((target_sv - intercept) / slope) if slope < 0.0 else float("inf")

        return {
            "trend_sv_per_year": slope,
            "r_squared": float(result.rvalue ** 2),
            "p_value": float(result.pvalue),
            "statistical_crossing_year": crossing_year,
            "target_strength_sv": target_sv,
        }
