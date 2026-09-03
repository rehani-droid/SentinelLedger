from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import InvestmentOptionRecord, OptimizationRunRecord, RiskAssessmentRecord
from app.optimization.service import run_optimization


def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        InvestmentOptionRecord(code="base", name="Foundation", description="", cost=40, risk_reduction=80,
                               affected_asset_ids=[], affected_control_ids=[], dependencies=[], exclusions=["exclusive"]),
        InvestmentOptionRecord(code="dependent", name="Dependent", description="", cost=30, risk_reduction=100,
                               affected_asset_ids=[], affected_control_ids=[], dependencies=["base"], exclusions=[]),
        InvestmentOptionRecord(code="exclusive", name="Exclusive", description="", cost=50, risk_reduction=150,
                               affected_asset_ids=[], affected_control_ids=[], dependencies=[], exclusions=["base"]),
    ])
    session.commit()
    return session


def _codes(run):
    return {item["code"] for item in run.selected_investments}


def test_persisted_optimization_handles_normal_and_zero_budgets() -> None:
    session = _session()
    normal = run_optimization(session, 70)
    assert _codes(normal) == {"base", "dependent"}
    assert normal.total_cost == 70
    assert normal.estimated_risk_reduction == 180
    assert session.get(OptimizationRunRecord, normal.id) is not None
    zero = run_optimization(session, 0)
    assert zero.selected_investments == []
    assert zero.total_cost == 0


def test_persisted_optimization_handles_insufficient_budget_and_dependencies() -> None:
    session = _session()
    insufficient = run_optimization(session, 20)
    assert insufficient.selected_investments == []
    session.query(InvestmentOptionRecord).filter(InvestmentOptionRecord.code != "dependent").delete()
    session.commit()
    dependent_only = run_optimization(session, 30)
    assert dependent_only.selected_investments == []


def test_persisted_optimization_respects_exclusions() -> None:
    session = _session()
    session.query(InvestmentOptionRecord).filter(InvestmentOptionRecord.code == "dependent").delete()
    session.commit()
    run = run_optimization(session, 90)
    assert _codes(run) == {"exclusive"}
    assert run.residual_risk == 0
