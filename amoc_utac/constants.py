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
    "tipping_year_central":    (2065, 10),  # corrected 2026-08-02, was 2057
}

# ── Tipping year references (corrected 2026-08-02, see AMOC meta-analysis) ────
# Ditlevsen & Ditlevsen (2023, Nat. Commun. 14, 4254) was itself corrected by
# an Author Correction in 2025 (Nat. Commun. 16, 7794, DOI
# 10.1038/s41467-025-63201-y): the central tipping-time estimate moved from
# 2057 [2025-2095] to 2065 [2037-2109]. The OLD 2057 figure some earlier
# GenesisAeon docs/code cited is now superseded -- use these corrected values.
DITLEVSEN_2023_CENTRAL: int = 2065
DITLEVSEN_2023_RANGE: tuple[int, int] = (2037, 2109)
DITLEVSEN_2025_CORRECTION_DOI: str = "10.1038/s41467-025-63201-y"
CHAVENT_2026_WEAKENING_BY: int = 2100

# A 2026 preprint (Morr et al., arXiv:2604.20341, not yet peer-reviewed as of
# this writing) argues the Ditlevsen fingerprint/model choice is itself
# fragile: alternative, equally-plausible model specifications push the
# estimated tipping time much later (into the 22nd century or beyond), and
# the method can manufacture a finite "tipping year" even from synthetic
# non-tipping time series. This is a real, substantive methodological
# critique -- but a preprint, not a peer-reviewed refutation. Kept here as
# context, not as a replacement value.
MORR_2026_CRITIQUE_CITATION: str = (
    "Morr et al. (2026), \"Extrapolation from historical data cannot "
    "reliably predict the time of a potential AMOC collapse\", arXiv:2604.20341 "
    "(preprint, not yet peer-reviewed)"
)

# ── AR6's own quantified weakening (real, not a collapse-year estimate) ──────
# IPCC AR6 WG1 Ch.9 / SPM: assessed AMOC weakening by 2100, medium confidence.
# This is NOT a collapse probability -- it's a projected strength reduction.
AR6_WEAKENING_SSP126_PCT: tuple[float, float, float] = (24.0, 4.0, 46.0)  # (central, low, high)
AR6_WEAKENING_SSP585_PCT: tuple[float, float, float] = (39.0, 17.0, 55.0)

# ── IPCC AR6 consensus position (added 2026-08-01, wording corrected 2026-08-02) ─
# Ditlevsen & Ditlevsen (2023/2025-corrected) is a single, statistically
# noteworthy reanalysis-based study -- real, but NOT the IPCC consensus.
# IMPORTANT WORDING NOTE (corrected 2026-08-02): the AR6 WG1 SPM (Section
# C.3.4) does NOT literally say "very unlikely" attached to "collapse before
# 2100" -- that phrasing is a common but imprecise public-communication
# shorthand. The SPM's own exact sentence is: "there is medium confidence
# that the Atlantic Meridional Overturning Circulation will not collapse
# abruptly before 2100." "Very likely" in the same passage describes the
# assessed WEAKENING itself (see AR6_WEAKENING_* above), not an exclusion of
# collapse. "Medium confidence" is not a numeric probability and should not
# be read as implying any specific percentage. See DISCLAIMER.md.
IPCC_AR6_CONFIDENCE_STATEMENT: str = (
    "medium confidence that the Atlantic Meridional Overturning Circulation "
    "will not collapse abruptly before 2100"
)
IPCC_AR6_CITATION: str = (
    "IPCC AR6 Working Group I, Summary for Policymakers (2021), Section C.3.4"
)

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
