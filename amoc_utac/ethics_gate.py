"""EthicsGate — Phase H responsible-AI safety check for amoc-utac outputs."""

from __future__ import annotations

from amoc_utac.constants import ETHICS_TENSION_BLOCK, ETHICS_TENSION_WARN


class EthicsGate:
    """
    Ethics-Gate Light (Phase H) — validates AMOC-UTAC state before publication.

    The gate checks whether the current system state and tension metric are
    within bounds that allow confident, responsible publication of results.

    Three-level response:
        ALLOWED   (tension < WARN)   — proceed normally
        WARNED    (WARN ≤ tension < BLOCK)  — attach uncertainty caveat
        BLOCKED   (tension ≥ BLOCK)  — halt; require human review

    Rationale: at very high tension the UTAC model operates near its validity
    boundary (Γ → 1, H → 0).  Outputs in this regime carry high epistemic
    uncertainty and must not be disseminated without expert review.
    """

    def __init__(
        self,
        warn_threshold: float = ETHICS_TENSION_WARN,
        block_threshold: float = ETHICS_TENSION_BLOCK,
    ) -> None:
        self.warn_threshold = warn_threshold
        self.block_threshold = block_threshold
        self._history: list[dict] = []

    def check(self, state: dict, tension_value: float) -> dict:
        """Evaluate whether the current state may be published.

        Args:
            state:         UTAC state dict (from get_utac_state()).
            tension_value: Current TensionMetric value ∈ [0, 1].

        Returns:
            dict with keys: allowed (bool), level (str), reason (str),
                            tension (float), caveats (list[str]).
        """
        caveats: list[str] = []

        if tension_value >= self.block_threshold:
            level = "BLOCKED"
            allowed = False
            reason = (
                f"Tension {tension_value:.3f} ≥ block threshold {self.block_threshold}. "
                "UTAC model near validity boundary (Γ → 1, H → 0). "
                "Results require expert review before publication."
            )
        elif tension_value >= self.warn_threshold:
            level = "WARNED"
            allowed = True
            reason = (
                f"Tension {tension_value:.3f} ≥ warn threshold {self.warn_threshold}. "
                "Attach uncertainty caveats to all outputs."
            )
            caveats.append(
                "AMOC system is in elevated-tension state; "
                "tipping-year predictions carry large uncertainty."
            )
            caveats.append(
                "Do not present UTAC tipping estimates as deterministic forecasts."
            )
        else:
            level = "ALLOWED"
            allowed = True
            reason = f"Tension {tension_value:.3f} within safe operating range."

        record = {
            "allowed": allowed,
            "level": level,
            "reason": reason,
            "tension": tension_value,
            "caveats": caveats,
            "gamma": state.get("Gamma"),
            "H_normalised": state.get("H_normalised"),
        }
        self._history.append(record)
        return record

    @property
    def history(self) -> list[dict]:
        """Full history of gate evaluations in this session."""
        return list(self._history)
