from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.ai.service import classify, handle_query
from app.services.demo_seed import seed_demo
from app.services.risk_persistence import recalculate_risk_assessments


def session_with_demo():
    engine = create_engine("sqlite://")
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    seed_demo(session)
    recalculate_risk_assessments(session)
    return session


def test_supported_intents_are_routed():
    assert classify("What are our biggest cyber risks?") == "top_risk_contributors"
    assert classify("Where should we spend our next 10 lakh?") == "budget_optimization"
    assert classify("What happens if we enable MFA?") == "scenario_simulation"
    assert classify("What are the highest priority vulnerabilities?") == "vulnerability_prioritization"
    assert classify("Which controls map to NIST?") == "control_compliance"


def test_queries_return_data_calculation_and_recommendation():
    session = session_with_demo()
    for question in ("biggest cyber risks", "security investment", "enable MFA", "highest priority vulnerabilities"):
        result = handle_query(session, question)
        assert result["intent"] != "unsupported"
        assert result["data"] is not None
        assert result["calculation"]
        assert result["recommendation"]
        assert result["provider"] == "deterministic-local-fallback"


def test_unsupported_questions_do_not_hallucinate():
    result = handle_query(session_with_demo(), "Tell me a joke")
    assert result["intent"] == "unsupported"
    assert "approved deterministic" in result["calculation"]
