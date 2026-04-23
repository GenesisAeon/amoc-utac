"""
amoc-utac · GenesisAeon Package 18
===================================
Atlantic Meridional Overturning Circulation Collapse Early Warning.

Central result:
    Γ_AMOC = arctanh(η=0.50) / σ=2.2 ≈ 0.251

This is the same as Γ_brain (Package 20) — cross-domain CREP universality
at the η = 50% homeostatic efficiency setpoint.

Diamond-Template contract:
    AmocUTAC.run_cycle()        → execute simulation
    AmocUTAC.get_crep_state()   → {C, R, E, P, Gamma}
    AmocUTAC.get_utac_state()   → {H, dH_dt, H_star, K_eff}
    AmocUTAC.get_phase_events() → list of tipping events
    AmocUTAC.to_zenodo_record() → publication-ready metadata

References:
    van Westen, Kliphuis & Dijkstra (2024). Sci. Adv. 10(6), eadk1189.
    Ditlevsen & Ditlevsen (2023). Nat. Commun.
    Chavent et al. (2026). Sci. Adv.
"""

from amoc_utac.system import AmocUTAC
from amoc_utac.constants import GAMMA_AMOC, PACKAGE_REGISTRY_18

__version__ = "0.1.0"
__all__ = ["AmocUTAC", "GAMMA_AMOC", "PACKAGE_REGISTRY_18"]
