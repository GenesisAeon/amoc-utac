# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
