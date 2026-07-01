# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
