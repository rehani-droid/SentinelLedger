"""Deterministic, dependency-light predictive incident-likelihood service.

The demo dataset is intentionally treated as modelled data. A prediction is only
returned when the persisted observations contain both target classes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import exp
from random import Random

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Asset, Control, Incident, ThreatScenario, Vulnerability

MODEL_VERSION = "phase9-logistic-v1"
FEATURE_VERSION = "asset-risk-features-v1"
HORIZON_DAYS = 90
FEATURE_NAMES = (
    "criticality",
    "data_sensitivity",
    "internet_exposed",
    "vulnerability_count",
    "mean_cvss",
    "mean_exploitability",
    "control_effectiveness",
    "threat_activity",
)
MIN_TRAINING_ROWS = 20
HISTORY_SEED = 90209
OBSERVATIONS_PER_ASSET = 12


@dataclass(frozen=True)
class FeatureRow:
    asset_id: int
    features: tuple[float, ...]
    target: int


@dataclass(frozen=True)
class HistoricalFeatureRow:
    asset_id: int
    observed_at: datetime
    features: tuple[float, ...]
    target: int


@dataclass(frozen=True)
class ModelResult:
    available: bool
    probability: float | None
    confidence: float | None
    drivers: list[dict]
    reason: str | None
    rows: int
    positive_rows: int
    metrics: dict
    trained_at: datetime


def _mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def build_feature_rows(session: Session) -> list[FeatureRow]:
    """Build one reproducible asset row from fields already persisted."""
    assets = session.scalars(select(Asset).order_by(Asset.id)).all()
    vulnerabilities = session.scalars(select(Vulnerability)).all()
    incidents = session.scalars(select(Incident)).all()
    controls = session.scalars(select(Control)).all()
    threats = session.scalars(select(ThreatScenario)).all()
    vulns_by_asset: dict[int, list[Vulnerability]] = {}
    incidents_by_asset: dict[int, int] = {}
    for vuln in vulnerabilities:
        vulns_by_asset.setdefault(vuln.asset_id, []).append(vuln)
    for incident in incidents:
        incidents_by_asset[incident.asset_id] = incidents_by_asset.get(incident.asset_id, 0) + 1
    control_effectiveness = _mean([control.baseline_effectiveness for control in controls])
    threat_activity = _mean([threat.activity for threat in threats])
    rows = []
    for asset in assets:
        asset_vulns = vulns_by_asset.get(asset.id, [])
        rows.append(FeatureRow(
            asset_id=asset.id,
            features=(
                float(asset.criticality),
                float(asset.data_sensitivity),
                float(asset.internet_exposed),
                float(len(asset_vulns)),
                _mean([v.cvss for v in asset_vulns]),
                _mean([v.exploitability for v in asset_vulns]),
                control_effectiveness,
                threat_activity,
            ),
            target=int(incidents_by_asset.get(asset.id, 0) > 0),
        ))
    return rows


def build_synthetic_historical_rows(session: Session) -> list[HistoricalFeatureRow]:
    """Create reproducible, time-separated demonstration observations.

    Outcomes are sampled from a bounded risk score plus deterministic noise; they
    are not a direct copy of any one feature or a real-world observation.
    """
    base_rows = build_feature_rows(session)
    rng = Random(HISTORY_SEED)
    start = datetime(2023, 1, 1, tzinfo=timezone.utc)
    rows: list[HistoricalFeatureRow] = []
    for base in base_rows:
        for period in range(OBSERVATIONS_PER_ASSET):
            criticality, sensitivity, exposed, vuln_count, cvss, exploitability, control, threat = base.features
            seasonal = (period % 4 - 1.5) * 0.025
            features = (
                max(0.0, min(1.0, criticality + rng.uniform(-0.06, 0.06))),
                max(0.0, min(1.0, sensitivity + rng.uniform(-0.06, 0.06))),
                exposed,
                max(0.0, vuln_count + rng.randint(-2, 2)),
                max(0.0, min(10.0, cvss + rng.uniform(-0.35, 0.35))),
                max(0.0, min(1.0, exploitability + rng.uniform(-0.06, 0.06))),
                max(0.0, min(1.0, control + rng.uniform(-0.05, 0.05))),
                max(0.0, min(1.0, threat + seasonal + rng.uniform(-0.05, 0.05))),
            )
            signal = (
                -2.8 + 1.15 * features[0] + 0.55 * features[1] +
                0.65 * features[2] + 0.045 * features[3] +
                0.16 * features[4] + 0.65 * features[5] -
                1.25 * features[6] + 0.9 * features[7] + seasonal
            )
            probability = float(_sigmoid(signal))
            target = int(rng.random() < probability)
            rows.append(HistoricalFeatureRow(
                asset_id=base.asset_id,
                observed_at=start + timedelta(days=30 * period),
                features=features,
                target=target,
            ))
    return rows


def _sigmoid(value: np.ndarray | float) -> np.ndarray | float:
    if isinstance(value, np.ndarray):
        return 1 / (1 + np.exp(-np.clip(value, -30, 30)))
    return 1 / (1 + exp(-max(-30, min(30, value))))


def _fit(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = x.mean(axis=0)
    scale = x.std(axis=0)
    scale[scale == 0] = 1
    normalized = (x - mean) / scale
    weights = np.zeros(normalized.shape[1])
    bias = 0.0
    for _ in range(600):
        probabilities = _sigmoid(normalized @ weights + bias)
        error = probabilities - y
        weights -= 0.08 * ((normalized.T @ error) / len(y) + 0.01 * weights)
        bias -= 0.08 * float(error.mean())
    return np.concatenate(([bias], weights)), mean, scale


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    tp = int(((actual == 1) & (predicted == 1)).sum())
    tn = int(((actual == 0) & (predicted == 0)).sum())
    fp = int(((actual == 0) & (predicted == 1)).sum())
    fn = int(((actual == 1) & (predicted == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
            "confusion_matrix": [[tn, fp], [fn, tp]], "evaluation_rows": int(len(actual))}


def train_and_predict(session: Session, asset_id: int | None = None) -> ModelResult:
    rows = sorted(build_synthetic_historical_rows(session), key=lambda row: (row.observed_at, row.asset_id))
    now = datetime.now(timezone.utc)
    positives = sum(row.target for row in rows)
    if len(rows) < MIN_TRAINING_ROWS:
        return ModelResult(False, None, None, [], "insufficient_rows", len(rows), positives, {}, now)
    if positives == 0 or positives == len(rows):
        return ModelResult(False, None, None, [], "single_target_class", len(rows), positives, {}, now)
    split = max(1, int(len(rows) * 0.8))
    train, evaluation = rows[:split], rows[split:]
    if len({row.target for row in train}) < 2 or len({row.target for row in evaluation}) < 2:
        return ModelResult(False, None, None, [], "non_representative_time_split", len(rows), positives, {}, now)
    x_train = np.array([row.features for row in train], dtype=float)
    y_train = np.array([row.target for row in train], dtype=float)
    parameters, mean, scale = _fit(x_train, y_train)
    x_eval = (np.array([row.features for row in evaluation]) - mean) / scale
    probabilities = _sigmoid(x_eval @ parameters[1:] + parameters[0])
    metrics = _metrics(np.array([row.target for row in evaluation]), (probabilities >= 0.5).astype(int))
    selected = next((row for row in reversed(rows) if row.asset_id == asset_id), None) if asset_id is not None else (rows[-1] if rows else None)
    if selected is None:
        return ModelResult(False, None, None, [], "asset_not_found", len(rows), positives, metrics, now)
    x_selected = (np.array(selected.features) - mean) / scale
    probability = float(_sigmoid(x_selected @ parameters[1:] + parameters[0]))
    contributions = [
        {"feature": name, "value": round(value, 4), "direction": "increases" if value >= 0 else "decreases"}
        for name, value in sorted(zip(FEATURE_NAMES, x_selected * parameters[1:]), key=lambda pair: abs(pair[1]), reverse=True)[:4]
    ]
    confidence = round(abs(probability - 0.5) * 2, 4)
    return ModelResult(True, round(probability, 4), confidence, contributions, None,
                       len(rows), positives, metrics, now)


def prediction_payload(session: Session, asset_id: int | None = None) -> dict:
    result = train_and_predict(session, asset_id)
    payload = {
        "available": result.available,
        "target": "incident_within_90_days",
        "prediction_horizon_days": HORIZON_DAYS,
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "feature_names": list(FEATURE_NAMES),
        "modelled": True,
        "trained_at": result.trained_at,
        "prediction_timestamp": result.trained_at,
        "dataset": "synthetic_historical_demonstration",
        "negative_rows": result.rows - result.positive_rows,
        "rows": result.rows,
        "positive_rows": result.positive_rows,
        "metrics": result.metrics,
        "key_predictive_drivers": result.drivers,
    }
    if result.available:
        payload.update({"predicted_likelihood": result.probability, "confidence": result.confidence})
    else:
        payload["unavailable_reason"] = result.reason
    return payload
