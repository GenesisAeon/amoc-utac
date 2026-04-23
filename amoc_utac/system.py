"""AmocUTAC — Diamond-Template interface for GenesisAeon Package 18."""

from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np

from amoc_utac.constants import (
    AMOC_PRESENT_SV,
    GAMMA_AMOC,
    PACKAGE_REGISTRY_18,
    UTAC_R,
    UTAC_SEED,
    UTAC_SIGMA,
)
from amoc_utac.crep_amoc import CREPAmocTensor
from amoc_utac.ethics_gate import EthicsGate
from amoc_utac.fingerprint import AmocFingerprintIndex
from amoc_utac.freshwater import FreshwaterTransport
from amoc_utac.rapid_loader import RapidLoader
from amoc_utac.tension_metric import TensionMetric
from amoc_utac.tipping_predictor import TippingPredictor


class AmocUTAC:
    """
    Atlantic Meridional Overturning Circulation UTAC System.

    Implements the Diamond-Template contract (Package 18):
        run_cycle()        → execute one full simulation cycle
        get_crep_state()   → {C, R, E, P, Gamma}
        get_utac_state()   → {H, dH_dt, H_star, K_eff}
        get_phase_events() → list of threshold-crossing events
        to_zenodo_record() → Zenodo-compatible metadata dict

    Physical mapping:
        H(t)  ← AMOC strength [Sv], normalised by K = 18 Sv
        H*    ← K · tanh(σ · Γ) ≈ 0.50 · K  (50% weakening setpoint)
        Γ     ≈ 0.251  (medium-CREP; same as Γ_brain — cross-domain universality)
        r     ≈ 0.08 yr⁻¹  (intrinsic recovery rate)
        σ     = 2.2  (CREP coupling constant)

    Central result:
        Γ_AMOC = arctanh(η=0.50) / σ=2.2 ≈ 0.251

    Ethics-Gate Light (Phase H):
        After each run_cycle the TensionMetric is updated and the EthicsGate
        is queried.  If tension ≥ ETHICS_TENSION_BLOCK, to_zenodo_record()
        raises RuntimeError requiring human review before publication.

    References:
        van Westen et al. (2024). Sci. Adv. 10(6), eadk1189.
        Ditlevsen & Ditlevsen (2023). Nat. Commun.
        Chavent et al. (2026). Sci. Adv.
    """

    PACKAGE_ID: int = 18

    def __init__(
        self,
        K: float = AMOC_PRESENT_SV,
        r: float = UTAC_R,
        sigma: float = UTAC_SIGMA,
        seed: int = UTAC_SEED,
    ) -> None:
        self.K = K
        self.r = r
        self.sigma = sigma
        self.seed = seed
        self._rng = np.random.default_rng(seed)

        self._loader = RapidLoader(seed=seed)
        self._fingerprint = AmocFingerprintIndex(seed=seed)
        self._freshwater = FreshwaterTransport(rng=self._rng)
        self._crep = CREPAmocTensor()
        self._predictor = TippingPredictor(
            K=K, r=r, sigma=sigma, gamma_amoc=GAMMA_AMOC, seed=seed
        )
        self._tension_metric = TensionMetric()
        self._ethics_gate = EthicsGate()

        # State populated by run_cycle()
        self._years: np.ndarray | None = None
        self._amoc_sv: np.ndarray | None = None
        self._fov: np.ndarray | None = None
        self._ar1: np.ndarray | None = None
        self._pe: np.ndarray | None = None
        self._crep_state: dict[str, float] | None = None
        self._utac_state: dict | None = None
        self._phase_events: list[dict] | None = None
        self._utac_sim: dict | None = None
        self._start_year: int = 2024

    # ── Diamond interface ─────────────────────────────────────────────────────

    def run_cycle(self, duration_years: int = 120) -> dict:
        """Execute one full AMOC-UTAC simulation cycle.

        Steps:
        1. Generate RAPID-calibrated AMOC time series (1950 → 1950+duration)
        2. Compute CREP components (C, R, E, P) at present-day (2024)
        3. Integrate UTAC ODE for H(t) over the projection window
        4. Detect phase-transition events (threshold crossings)
        5. Update TensionMetric and run Ethics-Gate check

        Returns: full state dict with time series and CREP/UTAC state.
        """
        start = 1950
        end = start + duration_years

        self._years, self._amoc_sv = self._loader.synthetic_annual(start=start, end=end)
        self._fov = self._freshwater.timeseries(self._amoc_sv)
        self._ar1 = self._fingerprint.autocorrelation_ar1(self._amoc_sv, window=30)
        self._pe = self._fingerprint.permutation_entropy(self._amoc_sv, window=30)

        present_idx = int(np.clip(
            np.searchsorted(self._years, self._start_year),
            0,
            len(self._amoc_sv) - 1,
        ))

        C = self._crep.compute_c(self._ar1[:present_idx])
        R = self._crep.compute_r(float(self._fov[present_idx]))
        E = self._crep.compute_e(self._amoc_sv[:present_idx])
        P = self._crep.compute_p(self._pe[:present_idx])
        gamma = self._crep.compute_gamma(C, R, E, P)
        self._crep_state = {"C": C, "R": R, "E": E, "P": P, "Gamma": gamma}

        H0 = float(self._amoc_sv[present_idx])
        self._utac_sim = self._predictor.simulate_utac(
            t_span=(0.0, float(duration_years)),
            H0=H0,
            gamma_trend=0.0015,
        )

        H_now = float(self._utac_sim["H"][0])
        H_star = self.K * math.tanh(self.sigma * gamma)
        dH_dt = self.r * H_now * (H_star / self.K - H_now / self.K)
        self._utac_state = {
            "H": H_now,
            "H_normalised": H_now / self.K,
            "dH_dt": dH_dt,
            "H_star": H_star,
            "K_eff": self.K,
            "r": self.r,
            "sigma": self.sigma,
            "Gamma": gamma,
        }

        self._phase_events = self._detect_phase_events()

        # ── Ethics-Gate Light (Phase H) ────────────────────────────────────
        tension_value = self._tension_metric.update(
            gamma=gamma,
            H=H_now,
            K=self.K,
            dH_dt=dH_dt,
        )
        ethics_result = self._ethics_gate.check(
            state=self._crep_state | {"H_normalised": H_now / self.K},
            tension_value=tension_value,
        )
        # BLOCKED state is recorded but does not halt run_cycle itself;
        # it is enforced at publication time in to_zenodo_record().

        return {
            "years": self._years.tolist(),
            "amoc_sv": self._amoc_sv.tolist(),
            "fov": self._fov.tolist(),
            "crep_state": self._crep_state,
            "utac_state": self._utac_state,
            "utac_trajectory": {
                "t": self._utac_sim["t"].tolist(),
                "H": self._utac_sim["H"].tolist(),
                "H_star": self._utac_sim["H_star"].tolist(),
            },
            "phase_events": self._phase_events,
            "ethics": {
                "tension": tension_value,
                "level": ethics_result["level"],
                "caveats": ethics_result["caveats"],
            },
        }

    def get_crep_state(self) -> dict:
        """Return CREP tensor state {C, R, E, P, Gamma}."""
        if self._crep_state is None:
            self.run_cycle()
        return dict(self._crep_state)  # type: ignore[arg-type]

    def get_utac_state(self) -> dict:
        """Return UTAC state {H, dH_dt, H_star, K_eff}."""
        if self._utac_state is None:
            self.run_cycle()
        return dict(self._utac_state)  # type: ignore[arg-type]

    def get_phase_events(self) -> list:
        """Return list of phase-transition events (threshold crossings)."""
        if self._phase_events is None:
            self.run_cycle()
        return list(self._phase_events)  # type: ignore[arg-type]

    def to_zenodo_record(self) -> dict:
        """Export simulation results as a Zenodo-compatible metadata record.

        Ethics-Gate check: raises RuntimeError if tension is above the block
        threshold, preventing automated publication of high-uncertainty states.
        """
        crep = self.get_crep_state()
        utac = self.get_utac_state()

        # ── Ethics-Gate Light (Phase H) ────────────────────────────────────
        tension_value = self._tension_metric.get_current_tension()
        ethics_result = self._ethics_gate.check(
            state=crep | {"H_normalised": utac.get("H_normalised")},
            tension_value=tension_value,
        )
        if not ethics_result["allowed"]:
            raise RuntimeError(
                f"EthicsGate blocked: {ethics_result['reason']}"
            )

        return {
            "title": (
                "AMOC-UTAC: Atlantic Meridional Overturning Circulation "
                "Collapse Early Warning (GenesisAeon Package 18)"
            ),
            "description": (
                "AMOC modelled as a UTAC dynamical system. "
                f"Γ_AMOC = {crep['Gamma']:.4f} (calibration target: 0.251). "
                "Package 18 of the GenesisAeon cross-domain CREP atlas. "
                "Central result: Γ_AMOC = Γ_brain = 0.251 "
                "(cross-domain universality at η = 50% efficiency setpoint)."
            ),
            "creators": [
                {"name": "Römer, Johann", "affiliation": "MOR Research Collective"}
            ],
            "keywords": [
                "AMOC",
                "tipping point",
                "UTAC",
                "CREP",
                "ocean circulation",
                "GenesisAeon",
                "early warning signal",
            ],
            "license": "MIT",
            "version": "0.1.0",
            "doi": PACKAGE_REGISTRY_18["zenodo"],
            "related_identifiers": [
                {
                    "identifier": "10.1126/sciadv.adk1189",
                    "relation": "isCitedBy",
                    "scheme": "doi",
                },
                {
                    "identifier": "10.1038/s41467-023-39810-w",
                    "relation": "isCitedBy",
                    "scheme": "doi",
                },
            ],
            "custom_fields": {
                "package_id": self.PACKAGE_ID,
                "crep_state": crep,
                "utac_state": utac,
                "gamma_amoc_target": GAMMA_AMOC,
                "ethics": {
                    "tension": tension_value,
                    "level": ethics_result["level"],
                    "caveats": ethics_result["caveats"],
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    def predict_tipping_year(self) -> dict:
        """UTAC tipping-year prediction.

        Compares with Ditlevsen 2023 (central 2057, range 2025–2095)
        and Chavent 2026 (50% weakening by 2100).
        """
        return self._predictor.predict_tipping_year(
            start_year=self._start_year,
            gamma_trend=0.0015,
            tipping_threshold=0.50,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _detect_phase_events(self) -> list[dict]:
        """Detect AMOC threshold crossings in the UTAC trajectory."""
        if self._utac_sim is None:
            return []

        H = self._utac_sim["H"]
        H_star = self._utac_sim["H_star"]
        t = self._utac_sim["t"]
        events: list[dict] = []

        for threshold in (0.90, 0.75, 0.50, 0.25):
            target = threshold * self.K
            sign_changes = np.where(np.diff(np.sign(H - target)))[0]
            for idx in sign_changes:
                events.append(
                    {
                        "type": "threshold_crossing",
                        "threshold_fraction": threshold,
                        "threshold_sv": float(target),
                        "year": float(self._start_year + t[idx]),
                        "H_at_crossing": float(H[idx]),
                        "H_star_at_crossing": float(H_star[idx]),
                    }
                )

        return sorted(events, key=lambda e: e["year"])

    # ── CREP Spectrum Atlas stub (genesis-os integration) ─────────────────────

    @staticmethod
    def crep_spectrum_entry() -> dict:
        """Return this package's entry for the GenesisAeon CREP Spectrum Atlas.

        After completing Packages 18–22, integrate this dict into genesis-os
        CREPSpectrumAtlas.register() to build the cross-domain Γ atlas.
        """
        return {
            "package_id": 18,
            "name": "amoc-utac",
            "domain": "oceanography",
            "gamma": GAMMA_AMOC,
            "eta": 0.50,
            "character": "homeostatic",
            "note": "Γ_AMOC = Γ_brain = 0.251 — cross-domain universality at η=50%",
        }
