"""AmocUTAC — Diamond-Template interface for GenesisAeon Package 18."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import numpy as np
from diamond_setup.protocol import (
    CREPState,
    DiamondPackage,
    UTACState,
    ZenodoCreator,
    ZenodoRecord,
)

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


class AmocUTAC(DiamondPackage):
    """
    Atlantic Meridional Overturning Circulation UTAC System.

    Implements the Diamond interface (Package 18) via :class:`DiamondPackage`:
        run_cycle()        → execute one full simulation cycle
        get_crep_state()   → {C, R, E, P, Gamma}  (after first run_cycle)
        get_utac_state()   → {H, H_star, K_eff}     (after first run_cycle)
        get_phase_events() → list of threshold-crossing events
        to_zenodo_record() → publication-ready metadata dict

    Physical mapping:
        H(t)  ← AMOC strength [Sv], normalised by K = 18 Sv for UTACState.H
        H*    ← K · tanh(σ · Γ) ≈ 0.50 · K  (50% weakening setpoint)
        Γ     ≈ 0.251  (medium-CREP; same as Γ_brain — cross-domain universality)
        r     ≈ 0.08 yr⁻¹  (intrinsic recovery rate)
        σ     = 2.2  (CREP coupling constant)

    Central result:
        Γ_AMOC = arctanh(η=0.50) / σ=2.2 ≈ 0.251

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
        duration_years: int = 120,
    ) -> None:
        super().__init__()
        self.K = K
        self.r = r
        self.sigma = sigma
        self.seed = seed
        self._duration_years = duration_years
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

        self._years: np.ndarray | None = None
        self._amoc_sv: np.ndarray | None = None
        self._fov: np.ndarray | None = None
        self._ar1: np.ndarray | None = None
        self._pe: np.ndarray | None = None
        self._crep_components: dict[str, float] | None = None
        self._utac_internal: dict[str, float] | None = None
        self._phase_events: list[dict[str, Any]] | None = None
        self._utac_sim: dict[str, np.ndarray] | None = None
        self._start_year: int = 2024
        self._last_ethics: dict[str, Any] | None = None

    def run_cycle(self, duration_years: int | None = None) -> dict[str, Any]:
        """Execute one AMOC-UTAC cycle (optional *duration_years* override)."""
        if duration_years is not None:
            self._duration_years = duration_years
        return super().run_cycle()

    def _run_cycle(self) -> dict[str, Any]:
        duration_years = self._duration_years
        start = 1950
        end = start + duration_years

        self._years, self._amoc_sv = self._loader.synthetic_annual(start=start, end=end)
        self._fov = self._freshwater.timeseries(self._amoc_sv)
        self._ar1 = self._fingerprint.autocorrelation_ar1(self._amoc_sv, window=30)
        self._pe = self._fingerprint.permutation_entropy(self._amoc_sv, window=30)

        present_idx = int(
            np.clip(
                np.searchsorted(self._years, self._start_year),
                0,
                len(self._amoc_sv) - 1,
            )
        )

        c = self._crep.compute_c(self._ar1[:present_idx])
        r_comp = self._crep.compute_r(float(self._fov[present_idx]))
        e = self._crep.compute_e(self._amoc_sv[:present_idx])
        p = self._crep.compute_p(self._pe[:present_idx])
        gamma = self._crep.compute_gamma(c, r_comp, e, p)
        self._crep_components = {"C": c, "R": r_comp, "E": e, "P": p, "Gamma": gamma}

        h0 = float(self._amoc_sv[present_idx])
        self._utac_sim = self._predictor.simulate_utac(
            t_span=(0.0, float(duration_years)),
            H0=h0,
            gamma_trend=0.0015,
        )

        h_now = float(self._utac_sim["H"][0])
        h_star = self.K * math.tanh(self.sigma * gamma)
        dh_dt = self.r * h_now * (h_star / self.K - h_now / self.K)
        self._utac_internal = {
            "H_sv": h_now,
            "H_normalised": h_now / self.K,
            "dH_dt": dh_dt,
            "H_star_sv": h_star,
            "K_eff": self.K,
            "r": self.r,
            "sigma": self.sigma,
            "Gamma": gamma,
        }

        self._phase_events = self._detect_phase_events()

        tension_value = self._tension_metric.update(
            gamma=gamma,
            H=h_now,
            K=self.K,
            dH_dt=dh_dt,
        )
        ethics_result = self._ethics_gate.check(
            state=self._crep_components | {"H_normalised": h_now / self.K},
            tension_value=tension_value,
        )
        self._last_ethics = {
            "tension": tension_value,
            "level": ethics_result["level"],
            "caveats": ethics_result["caveats"],
            "allowed": ethics_result["allowed"],
            "reason": ethics_result.get("reason"),
        }

        return {
            "years": self._years.tolist(),
            "amoc_sv": self._amoc_sv.tolist(),
            "fov": self._fov.tolist(),
            "crep_state": self._build_crep_state().as_dict(),
            "utac_state": self._build_utac_state().as_dict(),
            "utac_extended": dict(self._utac_internal),
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

    def _build_crep_state(self) -> CREPState:
        if self._crep_components is None:
            raise RuntimeError("CREP state unavailable before _run_cycle completes")
        s = self._crep_components
        return CREPState(C=s["C"], R=s["R"], E=s["E"], P=s["P"])

    def _build_utac_state(self) -> UTACState:
        if self._utac_internal is None:
            raise RuntimeError("UTAC state unavailable before _run_cycle completes")
        internal = self._utac_internal
        h_norm = float(min(1.0, max(0.0, internal["H_normalised"])))
        h_star_norm = float(min(1.0, max(0.0, internal["H_star_sv"] / self.K)))
        return UTACState(H=h_norm, H_star=h_star_norm, K_eff=internal["K_eff"])

    def _build_phase_events(self) -> list[dict[str, Any]]:
        return list(self._phase_events or [])

    def _build_zenodo_record(self) -> ZenodoRecord:
        return ZenodoRecord(
            title=(
                "AMOC-UTAC: Atlantic Meridional Overturning Circulation "
                "Collapse Early Warning (GenesisAeon Package 18)"
            ),
            description=(
                "AMOC modelled as a UTAC dynamical system. "
                f"Γ_AMOC calibration target: {GAMMA_AMOC:.4f}. "
                "Package 18 of the GenesisAeon cross-domain CREP atlas."
            ),
            creators=[ZenodoCreator(name="Römer, Johann", affiliation="MOR Research Collective")],
        )

    def to_zenodo_record(self) -> dict[str, Any]:
        """Export results as Zenodo metadata (Ethics-Gate enforced)."""
        crep = self.get_crep_state()
        utac = self.get_utac_state()
        extended = self._utac_internal or {}

        tension_value = self._tension_metric.get_current_tension()
        ethics_result = self._ethics_gate.check(
            state=crep | {"H_normalised": extended.get("H_normalised")},
            tension_value=tension_value,
        )
        if not ethics_result["allowed"]:
            raise RuntimeError(f"EthicsGate blocked: {ethics_result['reason']}")

        base = self._build_zenodo_record().as_dict()
        return {
            **base,
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
            "version": "1.1.0",
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
                "utac_extended": extended,
                "gamma_amoc_target": GAMMA_AMOC,
                "ethics": {
                    "tension": tension_value,
                    "level": ethics_result["level"],
                    "caveats": ethics_result["caveats"],
                },
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

    def predict_tipping_year(self) -> dict[str, Any]:
        """UTAC tipping-year prediction vs Ditlevsen 2023 / Chavent 2026 references."""
        return self._predictor.predict_tipping_year(
            start_year=self._start_year,
            gamma_trend=0.0015,
            tipping_threshold=0.50,
        )

    def _detect_phase_events(self) -> list[dict[str, Any]]:
        if self._utac_sim is None:
            return []

        h = self._utac_sim["H"]
        h_star = self._utac_sim["H_star"]
        t = self._utac_sim["t"]
        events: list[dict[str, Any]] = []

        for threshold in (0.90, 0.75, 0.50, 0.25):
            target = threshold * self.K
            sign_changes = np.where(np.diff(np.sign(h - target)))[0]
            for idx in sign_changes:
                events.append(
                    {
                        "type": "threshold_crossing",
                        "threshold_fraction": threshold,
                        "threshold_sv": float(target),
                        "year": float(self._start_year + t[idx]),
                        "H_at_crossing": float(h[idx]),
                        "H_star_at_crossing": float(h_star[idx]),
                    }
                )

        return sorted(events, key=lambda e: e["year"])

    @staticmethod
    def crep_spectrum_entry() -> dict[str, Any]:
        """Return this package's entry for the GenesisAeon CREP Spectrum Atlas."""
        return {
            "package_id": 18,
            "name": "amoc-utac",
            "domain": "oceanography",
            "gamma": GAMMA_AMOC,
            "eta": 0.50,
            "character": "homeostatic",
            "note": "Γ_AMOC = Γ_brain = 0.251 — cross-domain universality at η=50%",
        }