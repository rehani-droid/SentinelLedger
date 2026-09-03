"""Scenario deltas are explicit assumptions and never alter stored evidence."""
from __future__ import annotations
from ..risk.engine import eal, rosi
from math import isfinite

def simulate_privileged_mfa(*, before_eal: float, rollout_cost: float, current_privileged_coverage: float, target_privileged_coverage: float) -> dict[str, float | str]:
    if not isfinite(before_eal) or not isfinite(rollout_cost) or before_eal <= 0 or rollout_cost <= 0:
        raise ValueError("EAL and rollout cost must be finite and positive")
    if not 0 <= current_privileged_coverage <= target_privileged_coverage <= 1:
        raise ValueError("Coverage values must be ordered probabilities")
    reduction_fraction = (target_privileged_coverage - current_privileged_coverage) * 0.45
    after_eal = eal(1 - reduction_fraction, before_eal)
    reduction = before_eal - after_eal
    return {"before_eal": before_eal, "after_eal": after_eal, "risk_reduction": reduction, "improvement_percent": reduction_fraction * 100, "implementation_cost": rollout_cost, "rosi": rosi(reduction, rollout_cost), "estimate": "scenario-based"}

def simulate_scenario(*, baseline_eal: float, mfa_enabled: bool, current_privileged_coverage: float,
                      target_privileged_coverage: float, remediation_delay_days: int,
                      investment_reduction: float = 0, investment_cost: float = 0,
                      selected_control: str | None = None, selected_investment: str | None = None,
                      investment_change: float = 0) -> dict:
    if not isfinite(baseline_eal) or baseline_eal < 0 or not isfinite(investment_reduction) or investment_reduction < 0 or not isfinite(investment_cost) or investment_cost < 0 or not isfinite(investment_change) or investment_change < 0:
        raise ValueError("Scenario financial values must be finite and non-negative")
    if current_privileged_coverage > target_privileged_coverage:
        raise ValueError("Coverage values must be ordered probabilities")
    mfa_fraction = ((target_privileged_coverage - current_privileged_coverage) * 0.45) if mfa_enabled else 0
    delay_fraction = min(remediation_delay_days * 0.002, 0.5)
    control_fraction = 0.08 if selected_control else 0
    investment_fraction = min(max(investment_reduction / max(baseline_eal, 1), 0), 0.5)
    scenario_factor = max(0, 1 - mfa_fraction - control_fraction - investment_fraction + delay_fraction)
    scenario_eal = eal(scenario_factor, baseline_eal)
    delta = baseline_eal - scenario_eal
    total_cost = investment_cost + investment_change
    return {
        "baseline_eal": baseline_eal, "scenario_eal": scenario_eal,
        "eal_reduction": delta, "risk_reduction": delta,
        "financial_impact": delta, "implementation_cost": total_cost,
        "rosi": rosi(delta, total_cost) if total_cost > 0 else None,
        "assumptions": [
            "Values are deterministic, modelled estimates.",
            "MFA coverage changes reduce privileged-access exposure by 45% of the coverage delta." if mfa_enabled else "MFA is unchanged.",
            "Each remediation delay day increases modelled EAL by 0.2%, capped at 50%." if remediation_delay_days else "No remediation delay applied.",
            "A selected control applies an 8% modelled reduction." if selected_control else "No additional control applied.",
            f"Investment option {selected_investment} uses its persisted expected reduction." if selected_investment else "No investment option selected.",
        ],
        "estimate": "scenario-based",
    }
