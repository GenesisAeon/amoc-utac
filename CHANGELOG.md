# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.3.3] - 2026-09-15

### Fixed (real behavior change: `predict_tipping_year()`/`simulate_utac()` output)
- **Sign error in `TippingPredictor.h_star()`**: was `K·tanh(σ·Γ)`
  (increasing in Γ), meaning increasing freshwater-forcing Γ pulled the
  fixed point TOWARD K — i.e. the model predicted AMOC *strengthening*
  under increasing forcing, the opposite of every cited source's
  collapse/weakening narrative and of this class's own docstring
  ("the fixed point ... drifts below K"). Verified numerically before
  the fix: `simulate_utac()` over 120 years moved H from 9.0 to 12.7 Sv
  (strengthening), and the deterministic tipping-year run never crossed
  the threshold at all, silently falling back to `start_year+120=2144`.
  Corrected to `K·(1 − tanh(σ·Γ))` (decreasing in Γ). Because
  `AMOC_TIPPING_ETA=0.50` is self-symmetric (1−0.50=0.50), `GAMMA_AMOC`
  itself is unchanged — only H*(Γ) for Γ ≠ Γ_AMOC was wrong. After the
  fix, `simulate_utac()` correctly shows weakening (9.0 → 5.8 Sv over
  120 years) and `predict_tipping_year()`'s Monte Carlo ensemble shows
  a non-degenerate spread (previously identical 5th/95th percentiles).
  `system.py`'s duplicate inline formula and `tipping_predictor.py`'s
  `_ode()` were also updated/refactored to call the corrected
  `h_star()` instead of duplicating the (now-fixed) formula, preventing
  future drift between the two. `tests/test_tipping_predictor.py`'s
  `test_h_star_increases_with_gamma` (which encoded the old, wrong
  direction as a passing assertion) renamed to
  `test_h_star_decreases_with_gamma` with the corrected expectation.

### Fixed (documentation/metadata honesty, no further numeric value change)
- **Ecosystem-wide Γ-circularity review**: added an explicit honesty
  note to `GAMMA_AMOC` in `constants.py` (rescaling of a real 50%
  weakening projection via a shared, cross-package `UTAC_SIGMA=2.2`
  default never independently derived for AMOC). Corrected `system.py`'s
  class docstring, which claimed "same as Γ_brain — cross-domain
  universality" (the numeric match is an artifact of the shared sigma
  default, not shared physics — `README.md`/`CITATION.cff` already
  documented this correctly; the class docstring did not match).
  Labelled `benchmark.py`'s `gamma_formula_check()` as an arithmetic
  self-consistency check, not empirical validation. Documented in
  `rapid_loader.py` and `crep_amoc.py` that the "diagnostic" Gamma
  computed from the AMOC time series is (a) computed from a fully
  synthetic generator (hardcoded post-2050 exponential collapse), never
  real RAPID array data, and (b) not actually wired into
  `TippingPredictor`'s simulation, which uses only the fixed
  `GAMMA_AMOC` constant — a real, independently verified but
  intentionally undisturbed finding (fixing the wiring would not add
  genuine validation, since the diagnostic Gamma is itself
  synthetic-data-derived). See
  `D:\mandala\crep-utac-afet-formalism\worked_example_amoc_utac.md` and
  `FOLLOWUP_TICKETS.md` for the full analysis.

### Fixed (CI/typing only, no behavior change)
- 43 pre-existing `mypy --strict` errors (missing generic type
  parameters on `dict`/`np.ndarray`, an unused `type: ignore` combined
  with a genuinely missing parameter annotation on `_ode()`'s
  `gamma_func`, and the standard `DiamondPackage`-subclass/`Any`-return
  suppressions already used elsewhere in the ecosystem, e.g.
  `scope-resilience`) across 9 files. Not yet caught by CI (last run
  2026-09-05, predates a numpy release that changed stub strictness)
  but reproduced locally with the current unpinned `numpy` release.

## [1.3.0] - 2026-08-02
### Fixed
- **Ditlevsen & Ditlevsen (2023) was itself corrected in 2025** (Author
  Correction, Nat. Commun. 16, 7794, DOI `10.1038/s41467-025-63201-y`):
  central tipping-year estimate moved from 2057 [2025-2095] to **2065
  [2037-2109]**. This package previously cited the superseded 2057 figure;
  `DITLEVSEN_2023_CENTRAL`/`DITLEVSEN_2023_RANGE` and all dependent
  benchmark targets/tests now use the corrected values. Found via a
  dedicated DeepResearch meta-analysis of AMOC tipping-risk literature
  (2026-08-02).
- Corrected an imprecise AR6 wording: the SPM (Section C.3.4) does not
  literally say "very unlikely" attached to "collapse before 2100" --
  that's a common but inexact public-communication shorthand. The exact
  SPM sentence is "medium confidence that ... will not collapse abruptly
  before 2100"; "very likely" in the same passage describes the assessed
  *weakening*, not an exclusion of collapse.
### Added
- AR6's own quantified weakening-by-2100 figures (`AR6_WEAKENING_SSP126_PCT`,
  `AR6_WEAKENING_SSP585_PCT`: 24% [4-46%] and 39% [17-55%] respectively) --
  real assessed projections, not a collapse probability.
- Noted a 2026 preprint (Morr et al., arXiv:2604.20341, not yet peer
  reviewed) that substantively challenges the Ditlevsen fingerprint/model
  choice's robustness -- flagged as context, not adopted as a replacement
  value.
### Known follow-up (not done in this pass)
- The AMOC meta-analysis recommends replacing the single
  `collapse_year`-style framing with ~11 separate evidence-object fields
  (`formal_assessment`, `assessed_weakening`, `direct_observation`,
  `historical_reconstruction`, `statistical_tipping_estimate`,
  `physical_early_warning`, `model_tipping_onset`, `long_horizon_shutdown`,
  `constrained_projection_high/low`, `methodological_challenge`) each with
  measurement type, collapse definition, time horizon, peer-review status,
  and consensus status. This is a larger structural refactor, tracked as a
  follow-up, not done in this pass -- see `KlimaAktuell/deep-research-report2.md`.

## [1.2.0] - 2026-08-01
### Added
- IPCC AR6 WG1 SPM (2021) consensus context surfaced alongside the Ditlevsen
  & Ditlevsen (2023) tipping-year estimate in `predict_tipping_year()`
  (`ipcc_ar6_confidence_statement`, `ipcc_ar6_citation`, `consensus_note`)
  and in the `tipping-estimate` CLI table -- Ditlevsen 2023 is real but more
  alarmist than the IPCC's own "medium confidence that there will not be an
  abrupt collapse before 2100" assessment; both are now shown together
  instead of only the former. See README.md's new "Scientific Context"
  section.
### Fixed
- `predict_tipping_year()`: the deterministic single-path "central" estimate
  could fall outside its own reported 5-95% Monte Carlo band, because `H0`
  is calibrated to sit almost exactly at the tipping threshold, making the
  single deterministic run numerically unstable right at that boundary.
  `utac_central_year` now reports the internally consistent ensemble
  median; the original single-path value is preserved as
  `utac_deterministic_year`.
- CI (`ruff check amoc_utac tests`) was broken by a prior automated DOI-badge
  commit that dropped trailing newlines from two files -- restored.

## [1.1.1] - 2026-07-18
### Fixed
- CI release pipeline: removed the workflow-level `id-token: write`
  permission from `release.yml`. With it granted,
  `pypa/gh-action-pypi-publish` prefers OIDC Trusted Publishing over the
  supplied `password:` whenever an OIDC token is available, regardless
  of whether a valid `PYPI_API_TOKEN`/`TEST_PYPI_API_TOKEN` secret is
  also passed — and this repo's PyPI project was never registered as a
  Trusted Publisher, so every automated release since `v1.0.0` had its
  publish step fail (masked because releases were always shipped
  manually via `twine` instead, see `mandala/HANDOVER.md`). Identical
  bug found and fixed in `genesis-os/release.yml` the same day
  (`v1.0.9`→`v1.0.10`); applying the same fix here now that this repo's
  `PYPI_API_TOKEN`/`TEST_PYPI_API_TOKEN` secrets are actually configured
  (both repo-level and on the `pypi`/`testpypi` Environments).
- This tag is the live, real-tag verification that automated PyPI
  publishing now actually works for this package. No functional/API
  change.

## [1.1.0] - 2026-07-01
### Changed
- `AmocUTAC` subclasses `diamond_setup.DiamondPackage` (Diamond Protocol v2.1.0).
- `get_crep_state()` / `get_utac_state()` raise `NotConvergedError` before the
  first `run_cycle()` (Γ is an attractor, not an initial value).
- Canonical UTAC keys: `H` (normalised), `H_star`, `K_eff`; AMOC-specific fields
  (`dH_dt`, `H_sv`, …) remain in `run_cycle()` → `utac_extended`.
- Removed vendored `src/diamond_setup/`; real dependency `diamond-setup>=2.1.0`.

## [1.0.0] - 2026
### Added
- Initial v1.0.0 release as part of the GenesisAeon ecosystem-wide 1.0.0
  milestone.
- Standardized release tooling: `.zenodo.json`, GitHub Actions release
  workflow (`.github/workflows/release.yml`), `RELEASE_GUIDE.md`,
  `CONTRIBUTING.md`, issue/PR templates.

### Changed
- Project metadata (`pyproject.toml`) normalized: version bumped from
  0.1.0 to 1.0.0.
