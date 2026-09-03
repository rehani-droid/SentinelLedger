"""Database-backed option retrieval and durable optimisation-run history."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import InvestmentOptionRecord, OptimizationRunRecord, RiskAssessmentRecord
from .portfolio import InvestmentOption, optimise


def _option(record: InvestmentOptionRecord) -> InvestmentOption:
    return InvestmentOption(identifier=record.code, name=record.name, cost=record.cost,
                            risk_reduction=record.risk_reduction,
                            depends_on=tuple(record.dependencies or []), excludes=tuple(record.exclusions or []))


def serialize_option(record: InvestmentOptionRecord) -> dict:
    return {"code": record.code, "name": record.name, "description": record.description, "cost": record.cost,
            "expected_risk_reduction": record.risk_reduction, "affected_asset_ids": record.affected_asset_ids,
            "affected_control_ids": record.affected_control_ids, "dependencies": record.dependencies,
            "exclusions": record.exclusions}


def serialize_run(record: OptimizationRunRecord) -> dict:
    return {"id": record.id, "budget": record.budget, "selected_investments": record.selected_investments,
            "total_cost": record.total_cost, "estimated_risk_reduction": record.estimated_risk_reduction,
            "residual_risk": record.residual_risk, "optimization_timestamp": record.created_at}


def run_optimization(session: Session, budget: float) -> OptimizationRunRecord:
    options = [_option(record) for record in session.scalars(select(InvestmentOptionRecord).order_by(InvestmentOptionRecord.code)).all()]
    result = optimise(options, budget)
    enterprise = session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == "enterprise"))
    baseline_risk = enterprise.expected_annual_loss if enterprise else 0.0
    selected = [{"code": option.identifier, "name": option.name, "cost": option.cost,
                 "expected_risk_reduction": option.risk_reduction} for option in result["selected"]]
    record = OptimizationRunRecord(budget=budget, selected_investments=selected, total_cost=result["total_cost"],
                                   estimated_risk_reduction=result["risk_reduction"],
                                   residual_risk=max(0.0, baseline_risk - result["risk_reduction"]))
    session.add(record); session.commit(); session.refresh(record)
    return record
