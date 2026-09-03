from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import RiskAssessmentRecord
from app.services.demo_seed import seed_demo
from app.services.risk_persistence import recalculate_risk_assessments


def test_recalculation_persists_and_updates_all_supported_scopes() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    seed_demo(session)
    assert recalculate_risk_assessments(session) == {"assets": 100, "business_units": 7, "applications": 150, "enterprise": 1}
    records = session.scalars(select(RiskAssessmentRecord)).all()
    assert len(records) == 258
    enterprise = session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == "enterprise"))
    assert enterprise is not None
    assert enterprise.financial_impact > 0
    assert enterprise.expected_annual_loss > 0
    assert enterprise.var_95 >= enterprise.expected_annual_loss
    assert enterprise.major_risk_drivers
    first_calculated_at = enterprise.calculated_at
    recalculate_risk_assessments(session)
    assert session.query(RiskAssessmentRecord).count() == 258
    assert session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == "enterprise")).calculated_at >= first_calculated_at
