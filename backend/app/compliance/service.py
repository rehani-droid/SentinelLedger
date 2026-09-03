"""Read-only compliance mapping projections."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Control, FrameworkMapping

FRAMEWORK_NAMES = {
    "NIST-CSF-2.0": "NIST CSF",
    "NIST CSF": "NIST CSF",
    "ISO-27001:2022": "ISO/IEC 27001",
    "ISO 27001": "ISO/IEC 27001",
    "CIS-v8": "CIS Controls",
    "CIS": "CIS Controls",
    "RBI": "RBI Cyber Security Framework",
    "SEBI-CSCRF": "SEBI Cybersecurity and Cyber Resilience Framework",
    "SEBI": "SEBI Cybersecurity and Cyber Resilience Framework",
}


def framework_mappings(session: Session) -> dict:
    mappings = session.execute(
        select(FrameworkMapping, Control)
        .outerjoin(Control, FrameworkMapping.control_id == Control.id)
        .order_by(FrameworkMapping.framework, FrameworkMapping.control_reference)
    ).all()
    grouped = {
        "NIST CSF": [],
        "ISO/IEC 27001": [],
        "CIS Controls": [],
        "RBI Cyber Security Framework": [],
        "SEBI Cybersecurity and Cyber Resilience Framework": [],
    }
    for mapping, control in mappings:
        framework_name = FRAMEWORK_NAMES.get(mapping.framework, mapping.framework)
        grouped.setdefault(framework_name, []).append(
            {
                "reference": mapping.control_reference,
                "control": {
                    "id": control.id,
                    "name": control.name,
                    "category": control.category,
                    "coverage": control.baseline_effectiveness,
                }
                if control
                else None,
                "status": "mapped" if control else "reference_only",
                "risk_relevance": (
                    "Linked to a SENTINELEDGER control"
                    if control
                    else "No linked SENTINELEDGER control record"
                ),
                "evidence": None,
            }
        )
    return {
        "frameworks": [
            {"name": name, "mappings": items} for name, items in grouped.items()
        ],
        "disclaimer": "Mappings are prototype references, not compliance certification.",
    }
