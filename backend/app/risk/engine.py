"""Transparent calculations used by assessment, scenario, and optimiser services."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable
import random
from math import isfinite

from .config import CONTROL_REDUCTION_CAP, CRITICALITY_WEIGHTS, LIKELIHOOD_WEIGHTS, LOSS_COMPONENTS, MODEL_VERSION


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def asset_criticality(**factors: float) -> float:
    """Return documented weighted criticality in [0.1, 1.0]."""
    score = sum(CRITICALITY_WEIGHTS[key] * clamp(factors.get(key, 0.0)) for key in CRITICALITY_WEIGHTS)
    return max(0.1, clamp(score))


def control_effectiveness(assessments: Iterable[tuple[float, float, bool]]) -> float:
    """Combine independent controls, discounting failed/missing evidence."""
    remaining_risk = 1.0
    for effectiveness, coverage, evidence_valid in assessments:
        evidence_factor = 1.0 if evidence_valid else 0.55
        reduction = clamp(effectiveness) * clamp(coverage) * evidence_factor
        remaining_risk *= 1.0 - reduction
    return min(CONTROL_REDUCTION_CAP, 1.0 - remaining_risk)


def likelihood(*, cvss: float, exploitability: float, criticality: float, internet_exposure: float,
               vulnerability_age_days: int, threat_activity: float, historical_incident_rate: float,
               control_reduction: float) -> float:
    """Estimate annual incident likelihood using transparent normalised drivers."""
    if not 0 <= cvss <= 10:
        raise ValueError("CVSS must be between 0 and 10")
    weighted = (
        LIKELIHOOD_WEIGHTS["base_rate"]
        + LIKELIHOOD_WEIGHTS["cvss"] * (cvss / 10)
        + LIKELIHOOD_WEIGHTS["exploitability"] * clamp(exploitability)
        + LIKELIHOOD_WEIGHTS["criticality"] * clamp(criticality)
        + LIKELIHOOD_WEIGHTS["internet_exposure"] * clamp(internet_exposure)
        + LIKELIHOOD_WEIGHTS["vulnerability_age"] * clamp(vulnerability_age_days / 365)
        + LIKELIHOOD_WEIGHTS["threat_activity"] * clamp(threat_activity)
        + LIKELIHOOD_WEIGHTS["incident_signal"] * clamp(historical_incident_rate)
    )
    return clamp(weighted * (1.0 - clamp(control_reduction)))


def expected_loss(losses: dict[str, float]) -> float:
    """Sum named, non-negative financial loss components in INR."""
    values = [losses.get(component, 0.0) for component in LOSS_COMPONENTS]
    if any(not isfinite(value) or value < 0 for value in values):
        raise ValueError("Financial loss components must be finite and non-negative")
    result = float(sum(values))
    if not isfinite(result):
        raise ValueError("Financial loss is outside the supported numeric range")
    return result


def eal(annual_incident_frequency: float, expected_loss_per_incident: float) -> float:
    if not isfinite(annual_incident_frequency) or not 0 <= annual_incident_frequency <= 1:
        raise ValueError("Annual incident frequency must be between 0 and 1")
    if not isfinite(expected_loss_per_incident) or expected_loss_per_incident < 0:
        raise ValueError("Expected loss cannot be negative")
    result = annual_incident_frequency * expected_loss_per_incident
    if not isfinite(result):
        raise ValueError("Expected annual loss is outside the supported numeric range")
    return result


def cyber_var(*, annual_probability: float, expected_loss_per_incident: float, simulations: int = 5000,
              seed: int = 26105) -> dict[str, float]:
    """Empirical annual loss distribution with bounded uncertainty; reproducible for demos."""
    if simulations < 100 or simulations > 100_000:
        raise ValueError("Simulations must be between 100 and 100000")
    if not isfinite(annual_probability) or not 0 <= annual_probability <= 1:
        raise ValueError("Annual probability must be between 0 and 1")
    if not isfinite(expected_loss_per_incident) or expected_loss_per_incident < 0:
        raise ValueError("Expected loss cannot be negative")
    rng = random.Random(seed)
    outcomes = []
    for _ in range(simulations):
        incident = rng.random() < annual_probability
        impact_factor = max(0.1, rng.lognormvariate(-0.08, 0.42))
        outcomes.append(expected_loss_per_incident * impact_factor if incident else 0.0)
    outcomes.sort()
    percentile = lambda p: outcomes[min(len(outcomes) - 1, int(p * (len(outcomes) - 1)))]
    return {"mean": sum(outcomes) / len(outcomes), "median": median(outcomes), "p90": percentile(.90),
            "p95": percentile(.95), "p99": percentile(.99)}


def rosi(risk_reduction: float, investment_cost: float) -> float:
    if investment_cost <= 0:
        raise ValueError("Investment cost must be positive")
    return ((risk_reduction - investment_cost) / investment_cost) * 100


@dataclass(frozen=True)
class RiskAssessment:
    likelihood: float
    expected_loss: float
    eal: float
    residual_risk: float
    model_version: str = MODEL_VERSION
