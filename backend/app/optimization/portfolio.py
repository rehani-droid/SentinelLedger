"""Exact, dependency-aware 0/1 portfolio search for MVP-sized option sets."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from math import isfinite
from ..risk.engine import rosi

@dataclass(frozen=True)
class InvestmentOption:
    identifier: str
    name: str
    cost: float
    risk_reduction: float
    depends_on: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()

def optimise(options: list[InvestmentOption], budget: float) -> dict:
    if not isfinite(budget) or budget < 0:
        raise ValueError("Budget cannot be negative")
    if any(not isfinite(item.cost) or item.cost < 0 or not isfinite(item.risk_reduction) or item.risk_reduction < 0 for item in options):
        raise ValueError("Investment options must contain finite, non-negative values")
    best: tuple[InvestmentOption, ...] = ()
    best_reduction = 0.0
    for size in range(len(options) + 1):
        for candidate in combinations(options, size):
            ids = {item.identifier for item in candidate}
            cost = sum(item.cost for item in candidate)
            valid = cost <= budget and all(set(item.depends_on) <= ids and not (set(item.excludes) & ids) for item in candidate)
            reduction = sum(item.risk_reduction for item in candidate)
            if valid and reduction > best_reduction:
                best, best_reduction = candidate, reduction
    total_cost = sum(item.cost for item in best)
    return {"selected": list(best), "total_cost": total_cost, "risk_reduction": best_reduction,
            "remaining_budget": budget - total_cost, "rosi": rosi(best_reduction, total_cost) if total_cost else 0.0}
