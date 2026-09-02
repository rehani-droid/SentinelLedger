"""Scenario deltas are explicit assumptions and never alter stored evidence."""
from __future__ import annotations
from ..risk.engine import eal, rosi

def simulate_privileged_mfa(*, before_eal: float, rollout_cost: float, current_privileged_coverage: float, target_privileged_coverage: float) -> dict[str, float | str]:
    if not 0 <= current_privileged_coverage <= target_privileged_coverage <= 1:
        raise ValueError("Coverage values must be ordered probabilities")
    reduction_fraction = (target_privileged_coverage - current_privileged_coverage) * 0.45
    after_eal = eal(1 - reduction_fraction, before_eal)
    reduction = before_eal - after_eal
    return {"before_eal": before_eal, "after_eal": after_eal, "risk_reduction": reduction, "improvement_percent": reduction_fraction * 100, "implementation_cost": rollout_cost, "rosi": rosi(reduction, rollout_cost), "estimate": "scenario-based"}
