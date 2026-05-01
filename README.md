# amoc-utac

> GenesisAeon Package 18 — Atlantic Meridional Overturning Circulation as UTAC System

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.19645351"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg" alt="DOI (GenesisAeon Whitepaper)"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3 License"/></a>
  <a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/docs-CC%20BY%204.0-lightblue.svg" alt="CC BY 4.0"/></a>
  <a href="https://github.com/GenesisAeon/genesis-os"><img src="https://img.shields.io/badge/part%20of-genesis--os-blueviolet" alt="Part of genesis-os"/></a>
  <img src="https://img.shields.io/badge/UTAC-package%2018-orange" alt="Package 18"/>
</p>

**AMOC modelled as UTAC dynamical system** with physics-based early-warning from van Westen et al. (2024).

**Key result**: Γ_AMOC ≈ 0.251 (medium-CREP) → same universality point as neural criticality (η = 50 %).

## Installation

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

## License

Code: MIT • Docs & Data: CC BY 4.0
