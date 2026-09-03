"""Read-only natural-language routing over persisted SentinelLedger projections."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Asset, Control, Incident, InvestmentOptionRecord, RiskAssessmentRecord, Vulnerability
from ..optimization.portfolio import InvestmentOption, optimise
from ..scenarios.service import simulate_scenario

SUPPORTED = (
    "risk_overview", "top_risk_contributors", "asset_risk", "financial_exposure",
    "investment_recommendation", "budget_optimization", "scenario_simulation",
    "vulnerability_prioritization", "control_compliance",
)


def classify(question: str) -> str:
    text = " ".join(question.casefold().split())
    if any(word in text for word in ("mfa", "what happens if", "scenario", "enable")):
        return "scenario_simulation"
    if any(word in text for word in ("budget", "spend", "lakh", "optimi")):
        return "budget_optimization"
    if any(word in text for word in ("invest", "security investment", "risk reduction")):
        return "investment_recommendation"
    if any(word in text for word in ("vulnerab", "cve", "patch")):
        return "vulnerability_prioritization"
    if any(word in text for word in ("control", "compliance", "framework", "rbi", "sebi", "nist", "iso")):
        return "control_compliance"
    if any(word in text for word in ("asset", "contribute", "biggest", "highest risk", "risk driver")):
        return "top_risk_contributors" if "asset" not in text or "contribute" in text or "biggest" in text else "asset_risk"
    if any(word in text for word in ("financial", "exposure", "eal", "var")):
        return "financial_exposure"
    if any(word in text for word in ("risk", "cyber")):
        return "risk_overview"
    return "unsupported"


def _risk(record: RiskAssessmentRecord | None) -> dict:
    if not record:
        return {"risk_score": 0, "financial_impact": 0, "eal": 0, "var_95": 0, "drivers": []}
    return {"risk_score": record.risk_score, "likelihood": record.likelihood, "financial_impact": record.financial_impact,
            "eal": record.expected_annual_loss, "var_95": record.var_95, "drivers": record.major_risk_drivers}


def _envelope(intent: str, data: dict, calculation: str, recommendation: str) -> dict:
    return {"intent": intent, "provider": "deterministic-local-fallback", "ai_generated": False,
            "data": data, "calculation": calculation, "recommendation": recommendation}


def handle_query(session: Session, question: str) -> dict:
    intent = classify(question)
    enterprise = session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == "enterprise"))
    if intent == "unsupported":
        return _envelope(intent, {}, "No approved deterministic operation matched the question.",
                          "Try a question about risk, assets, financial exposure, vulnerabilities, controls, investments, budgets, or MFA scenarios.")
    if intent in ("risk_overview", "financial_exposure"):
        incidents = session.scalar(select(func.count()).select_from(Incident)) or 0
        return _envelope(intent, {"enterprise": _risk(enterprise), "incident_count": incidents},
                         "Returned the persisted enterprise risk projection and incident count.",
                         "Use the displayed EAL and P95 VaR as modelled decision-support metrics; they are not predictions.")
    if intent == "top_risk_contributors":
        records = session.scalars(select(RiskAssessmentRecord).where(RiskAssessmentRecord.scope == "asset").order_by(RiskAssessmentRecord.expected_annual_loss.desc()).limit(5)).all()
        items = [{"asset_id": r.asset_id, "name": session.get(Asset, r.asset_id).name, **_risk(r)} for r in records]
        return _envelope(intent, {"items": items}, "Ranked persisted asset projections by expected annual loss.",
                         "Prioritise the assets at the top of this ranked list for review.")
    if intent == "asset_risk":
        records = session.scalars(select(RiskAssessmentRecord).where(RiskAssessmentRecord.scope == "asset").order_by(RiskAssessmentRecord.risk_score.desc()).limit(5)).all()
        items = [{"asset_id": r.asset_id, "name": session.get(Asset, r.asset_id).name, **_risk(r)} for r in records]
        return _envelope(intent, {"items": items}, "Ranked persisted asset projections by risk score.",
                         "Review the listed assets and their linked vulnerabilities and controls.")
    if intent == "vulnerability_prioritization":
        rows = session.scalars(select(Vulnerability).where(Vulnerability.status != "closed").order_by(Vulnerability.cvss.desc(), Vulnerability.exploitability.desc()).limit(10)).all()
        items = [{"cve_id": v.cve_id, "asset_id": v.asset_id, "cvss": v.cvss, "exploitability": v.exploitability, "status": v.status} for v in rows]
        return _envelope(intent, {"items": items}, "Sorted open persisted vulnerabilities by CVSS, then exploitability.",
                         "Address the highest-ranked open vulnerabilities first, subject to operational validation.")
    if intent == "control_compliance":
        controls = session.scalars(select(Control).order_by(Control.baseline_effectiveness.asc()).limit(10)).all()
        items = [{"name": c.name, "category": c.category, "effectiveness": c.baseline_effectiveness} for c in controls]
        return _envelope(intent, {"controls": items}, "Returned persisted controls ordered by lowest baseline effectiveness.",
                         "Review low-effectiveness controls against the relevant compliance framework evidence.")
    options = session.scalars(select(InvestmentOptionRecord).order_by(InvestmentOptionRecord.risk_reduction.desc())).all()
    if intent == "investment_recommendation":
        items = [{"code": o.code, "name": o.name, "cost": o.cost, "expected_risk_reduction": o.risk_reduction} for o in options[:5]]
        return _envelope(intent, {"options": items}, "Ranked persisted investment options by expected risk reduction.",
                         "Compare these modelled reductions with cost, dependencies, and exclusions before approval.")
    if intent == "budget_optimization":
        budget = 1_000_000 if "lakh" in question.casefold() else 5_000_000
        portfolio = optimise([InvestmentOption(o.code, o.name, o.cost, o.risk_reduction, tuple(o.dependencies or []), tuple(o.exclusions or [])) for o in options], budget)
        selected = [{"code": o.identifier, "name": o.name, "cost": o.cost, "expected_risk_reduction": o.risk_reduction} for o in portfolio["selected"]]
        return _envelope(intent, {"budget": budget, "selected_investments": selected, "total_cost": portfolio["total_cost"],
                                  "remaining_budget": portfolio["remaining_budget"], "expected_risk_reduction": portfolio["risk_reduction"]},
                         "Ran the existing dependency- and exclusion-aware deterministic optimizer without persisting a run.",
                         "Use this portfolio as a review starting point; it is not an automatic purchase decision.")
    baseline = enterprise.expected_annual_loss if enterprise else 0
    result = simulate_scenario(baseline_eal=baseline, mfa_enabled=True, current_privileged_coverage=0.2,
                               target_privileged_coverage=1, remediation_delay_days=0)
    return _envelope(intent, {"baseline_eal": baseline, "scenario": result},
                     "Ran the existing deterministic MFA coverage scenario using 20% to 100% coverage.",
                     "Evaluate the modelled EAL reduction and implementation requirements with the security owner.")
