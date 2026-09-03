"""Read-only projections for the live dashboard."""
from collections import defaultdict
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..models import Asset, BusinessUnit, Control, Incident, InvestmentOptionRecord, RiskAssessmentRecord, ThreatScenario, Vulnerability
from ..ml.service import prediction_payload

def executive(session: Session) -> dict:
    enterprise = session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == "enterprise"))
    asset_risks = session.scalars(select(RiskAssessmentRecord).where(RiskAssessmentRecord.scope == "asset").order_by(RiskAssessmentRecord.expected_annual_loss.desc()).limit(5)).all()
    trend = defaultdict(float)
    for incident in session.scalars(select(Incident)):
        trend[incident.occurred_at.strftime("%Y-%m")] += incident.financial_loss
    return {"enterprise": _risk(enterprise), "predictive_risk": prediction_payload(session), "risk_trend": [{"period": period, "financial_loss": loss} for period, loss in sorted(trend.items())[-6:]], "top_contributors": [{"asset_id": r.asset_id, "name": session.get(Asset, r.asset_id).name, **_risk(r)} for r in asset_risks], "opportunities": [{"code": o.code, "name": o.name, "cost": o.cost, "risk_reduction": o.risk_reduction} for o in session.scalars(select(InvestmentOptionRecord).order_by(InvestmentOptionRecord.risk_reduction.desc()).limit(5))]}

def technical(session: Session) -> dict:
    max_time = session.scalar(select(func.max(Incident.occurred_at)))
    return {"counts": {"assets": session.scalar(select(func.count()).select_from(Asset)) or 0, "vulnerabilities": session.scalar(select(func.count()).select_from(Vulnerability)) or 0, "incidents": session.scalar(select(func.count()).select_from(Incident)) or 0, "controls": session.scalar(select(func.count()).select_from(Control)) or 0, "threats": session.scalar(select(func.count()).select_from(ThreatScenario)) or 0}, "telemetry_freshness": max_time}

def asset_detail(session: Session, asset_id: int) -> dict | None:
    asset = session.get(Asset, asset_id)
    if not asset: return None
    risk = session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == f"asset:{asset_id}"))
    related_options = session.scalars(select(InvestmentOptionRecord)).all()
    control_ids = {control_id for option in related_options if asset_id in (option.affected_asset_ids or []) for control_id in (option.affected_control_ids or [])}
    controls = session.scalars(select(Control).where(Control.id.in_(control_ids))) if control_ids else []
    return {"id": asset.id, "name": asset.name, "type": asset.asset_type, "criticality": asset.criticality, "data_sensitivity": asset.data_sensitivity, "internet_exposed": asset.internet_exposed, "risk": _risk(risk), "vulnerabilities": [{"cve_id": v.cve_id, "cvss": v.cvss, "exploitability": v.exploitability, "status": v.status} for v in session.scalars(select(Vulnerability).where(Vulnerability.asset_id == asset_id).order_by(Vulnerability.cvss.desc()))], "controls": [{"name": c.name, "category": c.category, "effectiveness": c.baseline_effectiveness} for c in controls]}

def business_units(session: Session) -> list[dict]:
    return [{"id": unit.id, "name": unit.name, "risk": _risk(session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == f"business_unit:{unit.id}")))} for unit in session.scalars(select(BusinessUnit).order_by(BusinessUnit.name))]

def _risk(record: RiskAssessmentRecord | None) -> dict:
    if not record: return {"risk_score": 0, "financial_impact": 0, "eal": 0, "var_95": 0, "drivers": [], "calculated_at": None}
    return {"risk_score": record.risk_score, "likelihood": record.likelihood, "financial_impact": record.financial_impact, "eal": record.expected_annual_loss, "var_95": record.var_95, "drivers": record.major_risk_drivers, "calculated_at": record.calculated_at}
