"""Persisted, reproducible risk assessment projections derived from stored telemetry."""
from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Application, Asset, BusinessUnit, Control, Incident, RiskAssessmentRecord, ThreatScenario, Vulnerability
from ..risk.config import MODEL_VERSION
from ..risk.engine import cyber_var, eal, likelihood


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _risk_score(likelihood_value: float, criticality: float) -> float:
    return round(min(100.0, likelihood_value * criticality * 100.0), 2)


def _upsert(session: Session, *, target_key: str, scope: str, business_unit_id: int | None = None,
            asset_id: int | None = None, application_id: int | None = None, risk_score: float,
            likelihood_value: float, financial_impact: float, annual_loss: float, var_95: float,
            drivers: list[dict], assumptions: dict, confidence: float, freshness: datetime) -> RiskAssessmentRecord:
    record = session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == target_key))
    values = dict(scope=scope, business_unit_id=business_unit_id, asset_id=asset_id,
                  application_id=application_id, risk_score=risk_score, likelihood=likelihood_value,
                  financial_impact=financial_impact, expected_annual_loss=annual_loss, var_95=var_95,
                  model_version=MODEL_VERSION, major_risk_drivers=drivers, assumptions=assumptions,
                  confidence=confidence, data_freshness=freshness, calculated_at=_now())
    if record is None:
        record = RiskAssessmentRecord(target_key=target_key, **values)
        session.add(record)
    else:
        for field, value in values.items():
            setattr(record, field, value)
    return record


def recalculate_risk_assessments(session: Session) -> dict[str, int]:
    """Refresh one current projection for every asset, business unit, application and enterprise."""
    assets = session.scalars(select(Asset).order_by(Asset.id)).all()
    controls = session.scalars(select(Control)).all()
    threats = session.scalars(select(ThreatScenario)).all()
    control_reduction = min(.9, mean([c.baseline_effectiveness for c in controls]) if controls else 0.0)
    threat_activity = mean([t.activity for t in threats]) if threats else 0.0
    freshness = session.scalar(select(func.max(Incident.occurred_at))) or _now()
    asset_records: list[RiskAssessmentRecord] = []

    for asset in assets:
        vulnerabilities = session.scalars(select(Vulnerability).where(Vulnerability.asset_id == asset.id)).all()
        incidents = session.scalars(select(Incident).where(Incident.asset_id == asset.id)).all()
        avg_cvss = mean([v.cvss for v in vulnerabilities]) if vulnerabilities else 0.0
        avg_exploitability = mean([v.exploitability for v in vulnerabilities]) if vulnerabilities else 0.0
        financial_impact = mean([i.financial_loss for i in incidents]) if incidents else 0.0
        historical_rate = min(1.0, len(incidents) / 5.0)
        probability = likelihood(cvss=avg_cvss, exploitability=avg_exploitability, criticality=asset.criticality,
                                 internet_exposure=1.0 if asset.internet_exposed else 0.0,
                                 vulnerability_age_days=0, threat_activity=threat_activity,
                                 historical_incident_rate=historical_rate, control_reduction=control_reduction)
        annual_loss = eal(probability, financial_impact)
        var_95 = cyber_var(annual_probability=probability, expected_loss_per_incident=financial_impact)["p95"]
        drivers = [
            {"driver": "vulnerability_exposure", "value": round(avg_cvss, 2), "unit": "cvss"},
            {"driver": "internet_exposure", "value": asset.internet_exposed, "unit": "boolean"},
            {"driver": "historical_incidents", "value": len(incidents), "unit": "count"},
        ]
        record = _upsert(session, target_key=f"asset:{asset.id}", scope="asset", asset_id=asset.id,
                         risk_score=_risk_score(probability, asset.criticality), likelihood_value=probability,
                         financial_impact=financial_impact, annual_loss=annual_loss, var_95=var_95, drivers=drivers,
                         assumptions={"control_reduction": control_reduction, "threat_activity": threat_activity,
                                      "financial_impact_basis": "mean historical incident loss"},
                         confidence=min(1.0, .4 + len(vulnerabilities) / 12 + len(incidents) / 12), freshness=freshness)
        asset_records.append(record)

    def aggregate(target_key: str, scope: str, records: list[RiskAssessmentRecord], **targets: int | None) -> RiskAssessmentRecord:
        financial_impact = sum(r.financial_impact for r in records)
        annual_loss = sum(r.expected_annual_loss for r in records)
        probability = mean([r.likelihood for r in records]) if records else 0.0
        var_95 = sum(r.var_95 for r in records)
        score = mean([r.risk_score for r in records]) if records else 0.0
        drivers = [{"driver": "highest_asset_eal", "asset_id": r.asset_id, "value": r.expected_annual_loss, "unit": "inr"}
                   for r in sorted(records, key=lambda item: item.expected_annual_loss, reverse=True)[:3]]
        return _upsert(session, target_key=target_key, scope=scope, risk_score=round(score, 2),
                       likelihood_value=probability, financial_impact=financial_impact, annual_loss=annual_loss,
                       var_95=var_95, drivers=drivers,
                       assumptions={"aggregation": "sum financial metrics; mean likelihood and risk score"},
                       confidence=mean([r.confidence for r in records]) if records else 0.0, freshness=freshness, **targets)

    units = session.scalars(select(BusinessUnit)).all()
    for unit in units:
        aggregate(f"business_unit:{unit.id}", "business_unit", [r for r in asset_records if session.get(Asset, r.asset_id).business_unit_id == unit.id], business_unit_id=unit.id)
    applications = session.scalars(select(Application)).all()
    for application in applications:
        aggregate(f"application:{application.id}", "application", [r for r in asset_records if session.get(Asset, r.asset_id).business_unit_id == application.business_unit_id], application_id=application.id)
    aggregate("enterprise", "enterprise", asset_records)
    session.commit()
    return {"assets": len(assets), "business_units": len(units), "applications": len(applications), "enterprise": 1}
