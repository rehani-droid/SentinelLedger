from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.services.demo_seed import seed_demo
from app.compliance.service import framework_mappings


def test_framework_projection_includes_seeded_controls_and_supported_frameworks() -> None:
    engine = create_engine("sqlite://")
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    seed_demo(session)

    result = framework_mappings(session)
    names = {framework["name"] for framework in result["frameworks"]}
    assert names == {
        "NIST CSF",
        "ISO/IEC 27001",
        "CIS Controls",
        "RBI Cyber Security Framework",
        "SEBI Cybersecurity and Cyber Resilience Framework",
    }
    assert all(framework["mappings"] for framework in result["frameworks"])
    assert all(mapping["control"] for framework in result["frameworks"] for mapping in framework["mappings"])
