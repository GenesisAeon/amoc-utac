"""RAPID-MOCHA 26°N array data loader and synthetic time-series generator."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml


class RapidLoader:
    """
    RAPID-MOCHA 26°N array data loader.

    Handles:
    - Loading summary statistics from a bundled YAML file (public data)
    - Generating synthetic annual AMOC time series calibrated to RAPID stats
    - Providing present-day state estimates in Sv

    Real-time data source: https://rapid.ac.uk/rapidmoc/rapid_data/datadl.php
    Publication: Smeed et al. (2018), Ocean Sci. 14, 111-124.
    """

    RAPID_START_YEAR: int = 2004
    RAPID_MEAN_SV: float = 17.0
    RAPID_STD_SV: float = 4.0

    def __init__(
        self,
        data_path: Path | str | None = None,
        seed: int = 42,
    ) -> None:
        self.rng = np.random.default_rng(seed)
        if data_path is not None:
            self._summary = self._load_yaml(Path(data_path))
        else:
            self._summary = self._default_summary()

    # ── Public API ───────────────────────────────────────────────────────────

    @property
    def summary(self) -> dict:
        return dict(self._summary)

    def present_state(self) -> dict[str, float]:
        """Return present-day AMOC state from RAPID statistics."""
        return {
            "strength_sv": float(self._summary.get("mean_sv", self.RAPID_MEAN_SV)),
            "std_sv": float(self._summary.get("std_sv", self.RAPID_STD_SV)),
            "trend_sv_per_decade": float(self._summary.get("trend_sv_per_decade", -0.5)),
        }

    def synthetic_annual(
        self,
        start: int = 1950,
        end: int = 2100,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Generate synthetic annual AMOC time series [Sv].

        Calibration:
        - Pre-industrial baseline ~21 Sv (proxy-based)
        - Linear weakening ~3 Sv from 1950 to 2004
        - Slow post-2004 weakening (−0.5 Sv/decade, RAPID trend)
        - Accelerating toward tipping post-2050 (SSP2-4.5 scenario)
        - AR(1) noise (φ = 0.80) superimposed

        Returns: (years, amoc_sv)
        """
        years = np.arange(start, end + 1, dtype=float)
        n = len(years)
        baseline_2004 = self.RAPID_MEAN_SV
        trend_pre = -3.0 / 54.0    # Sv/yr before 2004

        strength = np.zeros(n)
        for i, y in enumerate(years):
            if y < 2004:
                strength[i] = baseline_2004 + trend_pre * (y - 2004.0)
            elif y < 2050:
                strength[i] = baseline_2004 + (y - 2004.0) * (-0.05)
            else:
                # Exponential collapse toward near-zero AMOC
                dt = y - 2050.0
                strength[i] = (baseline_2004 - 2.0) * np.exp(-dt / 80.0)

        # AR(1) noise process
        phi = 0.80
        sigma_eps = self.RAPID_STD_SV * np.sqrt(1.0 - phi ** 2)
        noise = np.zeros(n)
        noise[0] = float(self.rng.normal(0.0, self.RAPID_STD_SV))
        for i in range(1, n):
            noise[i] = phi * noise[i - 1] + float(self.rng.normal(0.0, sigma_eps))

        amoc = np.clip(strength + noise * 0.5, 0.0, 30.0)
        return years, amoc

    # ── Internals ────────────────────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        with path.open() as fh:
            return yaml.safe_load(fh)  # type: ignore[no-any-return]

    def _default_summary(self) -> dict:
        return {
            "source": "RAPID-MOCHA 26°N array",
            "period": "2004-2023",
            "mean_sv": self.RAPID_MEAN_SV,
            "std_sv": self.RAPID_STD_SV,
            "min_sv": 4.0,
            "max_sv": 31.0,
            "trend_sv_per_decade": -0.5,
            "n_years": 19,
        }
