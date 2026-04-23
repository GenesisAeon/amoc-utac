"""SST fingerprint AMOC index — Caesar et al. (2018) method."""

from __future__ import annotations

from itertools import permutations

import numpy as np
from scipy.signal import detrend


class AmocFingerprintIndex:
    """
    SST-based AMOC strength index (Caesar et al. 2018).

    The fingerprint exploits the cooling signature of the subpolar North
    Atlantic (45–60°N, 10–60°W) relative to the global mean: a weakening
    AMOC reduces northward heat transport, cooling that region.

    Available 1870–present from HadSST4 / ERA5.
    Maps to UTAC state variable H(t) after normalisation [Sv → 0..1].
    """

    NORMALISATION_SV: float = 18.0   # K_eff [Sv]

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)

    def synthetic_index(
        self,
        years: np.ndarray,
        trend_sv_per_decade: float = -0.3,
        noise_std: float = 1.5,
        phi: float = 0.85,
    ) -> np.ndarray:
        """Generate synthetic annual AMOC index [Sv].

        Linear trend + AR(1) noise calibrated to observed RAPID statistics
        and proxy-based ~3 Sv weakening since 1950.
        """
        n = len(years)
        y0 = float(years[0])
        trend = self.NORMALISATION_SV + trend_sv_per_decade / 10.0 * (years - y0)

        ar1 = np.zeros(n)
        sigma_eps = noise_std * np.sqrt(1.0 - phi ** 2)
        ar1[0] = float(self.rng.normal(0.0, noise_std))
        for i in range(1, n):
            ar1[i] = phi * ar1[i - 1] + float(self.rng.normal(0.0, sigma_eps))

        return np.clip(trend + ar1, 0.0, 30.0)

    def normalise_to_utac(self, strength_sv: np.ndarray) -> np.ndarray:
        """Normalise AMOC strength [Sv] to UTAC state variable H ∈ [0, 1]."""
        return strength_sv / self.NORMALISATION_SV

    def autocorrelation_ar1(self, series: np.ndarray, window: int = 30) -> np.ndarray:
        """Rolling AR(1) coefficient — critical slowing-down indicator.

        Approaches 1 as system nears tipping (loss of resilience).
        Maps to CREP C-component.
        """
        n = len(series)
        ar1 = np.full(n, np.nan)
        for i in range(window, n):
            chunk = detrend(series[i - window : i])
            std = float(chunk.std())
            if std > 1e-10:
                ar1[i] = float(np.corrcoef(chunk[:-1], chunk[1:])[0, 1])
        return ar1

    def permutation_entropy(
        self,
        series: np.ndarray,
        order: int = 3,
        window: int = 30,
    ) -> np.ndarray:
        """Rolling normalised permutation entropy ∈ [0, 1].

        Lower PE → more ordered dynamics → approaching tipping.
        Maps to CREP P-component (raw PE, not inverted).
        """
        n = len(series)
        pe = np.full(n, np.nan)

        all_perms = list(permutations(range(order)))
        n_perms = len(all_perms)
        perm_index = {p: i for i, p in enumerate(all_perms)}

        for i in range(window + order - 1, n):
            chunk = series[i - window : i]
            counts = np.zeros(n_perms)
            for j in range(len(chunk) - order + 1):
                pattern = tuple(int(x) for x in np.argsort(chunk[j : j + order]))
                counts[perm_index[pattern]] += 1
            probs = counts / counts.sum()
            probs = probs[probs > 0]
            pe[i] = float(-np.sum(probs * np.log2(probs)) / np.log2(n_perms))

        return pe
