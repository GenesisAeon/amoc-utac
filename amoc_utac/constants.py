"""Physical and model constants for amoc-utac (Package 18)."""

import math

# ── AMOC physical parameters ─────────────────────────────────────────────────
AMOC_PRESENT_SV: float = 18.0       # Present AMOC strength (RAPID 2004–2023) [Sv]
AMOC_RAPID_MEAN_SV: float = 17.0    # RAPID 2004–2023 array mean [Sv]
AMOC_RAPID_STD_SV: float = 4.0      # RAPID inter-annual std [Sv]
AMOC_WEAKENING_SV: float = 3.0      # Proxy-based weakening since 1950 [Sv]

# ── UTAC model parameters ─────────────────────────────────────────────────────
UTAC_R: float = 0.08                # AMOC intrinsic recovery rate [1/yr]
UTAC_SIGMA: float = 2.2             # CREP coupling constant
UTAC_SEED: int = 42

# ── CREP calibration ──────────────────────────────────────────────────────────
# Central result: Γ_AMOC = arctanh(η=0.50) / σ=2.2 ≈ 0.251
AMOC_TIPPING_ETA: float = 0.50      # 50% weakening projection (Chavent et al. 2026)
GAMMA_AMOC: float = math.atanh(AMOC_TIPPING_ETA) / UTAC_SIGMA   # ≈ 0.2510

# ── Freshwater transport ─────────────────────────────────────────────────────
FOV_REF: float = 0.1                # Reference Fov [Sv] for sigmoid normalisation
FOV_ALPHA: float = -0.05            # Calibrated Fov–AMOC coefficient

# ── Benchmark targets (value, relative_tolerance) ────────────────────────────
AMOC_TARGETS: dict = {
    "present_strength_Sv":     (17.0, 0.15),
    "weakening_since_1950_Sv": (3.0,  0.33),
    "gamma_amoc":              (0.251, 0.05),
    "fov_sign":                ("negative", None),
    "tipping_year_central":    (2057, 10),
}

# ── Tipping year references ───────────────────────────────────────────────────
DITLEVSEN_2023_CENTRAL: int = 2057
DITLEVSEN_2023_RANGE: tuple[int, int] = (2025, 2095)
CHAVENT_2026_WEAKENING_BY: int = 2100

# ── Package registry ─────────────────────────────────────────────────────────
PACKAGE_REGISTRY_18: dict = {
    "name": "amoc-utac",
    "class": "AmocUTAC",
    "domain": "oceanography",
    "scale": "planetary",
    "zenodo": "10.5281/zenodo.19645351",
    "reference": "10.1126/sciadv.adk1189",
    "package_id": 18,
}

# ── Ethics-Gate thresholds (Phase H) ─────────────────────────────────────────
ETHICS_TENSION_WARN: float = 0.70   # Warn above this tension
ETHICS_TENSION_BLOCK: float = 0.90  # Block publication above this tension
