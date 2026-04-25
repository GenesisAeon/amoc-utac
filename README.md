# amoc-utac

> GenesisAeon Package 18 — Atlantic Meridional Overturning Circulation as UTAC System

[![GenesisAeon](https://img.shields.io/badge/GenesisAeon-Package%2018-blueviolet)](https://github.com/GenesisAeon)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg)](https://doi.org/10.5281/zenodo.19645351)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Reference](https://img.shields.io/badge/Ref-Science%20Advances%202024-red)](https://doi.org/10.1126/sciadv.adk1189)

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
