# amoc-utac

> GenesisAeon Package 18 — Atlantic Meridional Overturning Circulation as UTAC System

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.19645351"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg" alt="DOI (GenesisAeon Whitepaper)"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"/></a>
  <a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/docs-CC%20BY%204.0-lightblue.svg" alt="CC BY 4.0"/></a>
  <a href="https://github.com/GenesisAeon/genesis-os"><img src="https://img.shields.io/badge/part%20of-genesis--os-blueviolet" alt="Part of genesis-os"/></a>
  <img src="https://img.shields.io/badge/UTAC-package%2018-orange" alt="Package 18"/>
</p>

**AMOC modelled as UTAC dynamical system** with physics-based early-warning from van Westen et al. (2024).

**Key result**: Γ_AMOC ≈ 0.251 (medium-CREP) → same universality point as neural criticality (η = 50 %).

## Installation

```bash
pip install amoc-utac
```

For development:

```bash
pip install -e ".[dev]"
```

## Quickstart

```bash
amoc-utac run --duration 120
amoc-utac tipping-estimate
amoc-utac zenodo-export
```

## Integration in genesis-os

```python
from genesis_os import GenesisOS
os = GenesisOS()
amoc = os.load_package(18)
results = amoc.run_cycle(duration_years=120)
```

## Benchmark

Validated against RAPID array, van Westen 2024 & Ditlevsen 2023.

## Falsifiable Prediction

AMOC crosses 50 % weakening (H* = 0.5 K) between 2045–2065.

## Scientific Context — Consensus vs. Single Studies (added 2026-08-01, corrected 2026-08-02)

The Ditlevsen & Ditlevsen (2023) tipping-year estimate this package compares
against is a **real, published, but more alarmist single study**, not the
mainstream consensus. **Important: the paper was itself corrected in 2025**
(Author Correction, Nat. Commun. 16, 7794, DOI `10.1038/s41467-025-63201-y`)
— the central estimate moved from 2057 [2025-2095] to **2065 [2037-2109]**;
this package now uses the corrected values. A 2026 preprint (Morr et al.,
arXiv:2604.20341, not yet peer-reviewed) further argues the underlying
statistical fingerprint/model choice is fragile enough that alternative,
equally-defensible specifications push the estimate much later.

The **IPCC AR6 Working Group I Summary for Policymakers (2021, Section
C.3.4)** states: "there is medium confidence that the Atlantic Meridional
Overturning Circulation will not collapse abruptly before 2100." Note this
is *not* the same as the commonly-repeated shorthand "very unlikely before
2100" — "very likely" in the same AR6 passage describes the assessed
*weakening itself* (24% [4-46%] under SSP1-2.6, 39% [17-55%] under
SSP5-8.5 by 2100), not an exclusion of collapse, and "medium confidence" is
not a numeric probability. Both the corrected Ditlevsen estimate and the
AR6 consensus position are surfaced together in `predict_tipping_year()`'s
return value (`ipcc_ar6_confidence_statement`, `ipcc_ar6_citation`,
`consensus_note`) and in the `tipping-estimate` CLI command's output table,
so users see the consensus baseline alongside this package's own (more
alarmist) UTAC estimate rather than only the latter.

## Role in the GenesisAeon Ecosystem

`amoc-utac` is **P18** in the GenesisAeon ecosystem, covering the
oceanography / AMOC tipping domain. It applies the UTAC-Logistic ODE and
CREP metrics to the Atlantic Meridional Overturning Circulation, sharing
its criticality framework (Γ ≈ 0.251) with sibling packages across other
domains (e.g. neuroscience, heliophysics).

## Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21432660.svg)](https://doi.org/10.5281/zenodo.21432660)

## License

Code: MIT • Docs & Data: CC BY 4.0
