from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.services.dashboard import asset_detail, business_units, executive, technical
from app.services.demo_seed import seed_demo
from app.services.risk_persistence import recalculate_risk_assessments

def test_dashboard_projections_use_persisted_synthetic_data() -> None:
    engine = create_engine("sqlite://")
    session = sessionmaker(bind=engine)(); Base.metadata.create_all(engine)
    seed_demo(session); recalculate_risk_assessments(session)
    summary = executive(session)
    assert summary["enterprise"]["eal"] > 0 and summary["top_contributors"]
    assert technical(session)["counts"]["assets"] == 100
    assert len(business_units(session)) == 7
    assert asset_detail(session, summary["top_contributors"][0]["asset_id"])["risk"]["risk_score"] > 0
