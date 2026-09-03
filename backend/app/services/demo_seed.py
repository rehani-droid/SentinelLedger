"""Deterministic, idempotent SIH demo dataset seeding."""
import os
from random import Random
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.security import hash_password
from ..models import Application, Asset, BusinessUnit, Control, FrameworkMapping, Incident, InvestmentOptionRecord, Role, ThreatScenario, User, Vulnerability

SEED = 26105

def _ensure_investment_options(session: Session) -> None:
    assets = session.scalars(select(Asset).order_by(Asset.id)).all()
    controls = session.scalars(select(Control).order_by(Control.id)).all()
    if not assets or not controls:
        return
    options = [
        ("patch", "Patch critical vulnerabilities", "Remediate the highest-risk externally exposed vulnerability backlog.", 800000, 2800000, [], []),
        ("mfa", "Privileged MFA rollout", "Require phishing-resistant MFA for privileged access paths.", 1200000, 3500000, [], []),
        ("edr", "EDR coverage expansion", "Extend managed endpoint detection and response to unmanaged servers.", 2000000, 3000000, [], []),
        ("segmentation", "Network segmentation", "Segment critical payment and identity workloads after endpoint coverage is in place.", 2500000, 4200000, ["edr"], ["backup_isolation"]),
        ("backup_isolation", "Immutable backup isolation", "Protect recovery copies from ransomware encryption paths.", 1500000, 2400000, [], ["segmentation"]),
    ]
    for index, (code, name, description, cost, reduction, dependencies, exclusions) in enumerate(options):
        record = session.scalar(select(InvestmentOptionRecord).where(InvestmentOptionRecord.code == code))
        values = dict(name=name, description=description, cost=cost, risk_reduction=reduction,
                      affected_asset_ids=[asset.id for asset in assets[index * 10:(index + 1) * 10]],
                      affected_control_ids=[controls[index % len(controls)].id], dependencies=dependencies, exclusions=exclusions)
        if record is None:
            session.add(InvestmentOptionRecord(code=code, **values))
        else:
            for field, value in values.items():
                setattr(record, field, value)

def seed_demo(session: Session) -> dict[str, int]:
    if session.scalar(select(Asset.id).limit(1)):
        _ensure_investment_options(session)
        session.commit()
        return {"assets": session.query(Asset).count(), "status": "already_seeded"}
    rng = Random(SEED)
    units = [BusinessUnit(name=name) for name in ["Retail Banking", "Payments", "Wealth", "Operations", "Technology", "Risk", "Corporate"]]
    roles = [Role(name=name) for name in ["ciso", "analyst", "auditor"]]
    session.add_all(units + roles); session.flush()
    role_by_name = {role.name: role for role in roles}
    demo_users = [
        ("ciso", os.getenv("DEMO_CISO_PASSWORD", "CisoDemo!2026")),
        ("analyst", os.getenv("DEMO_ANALYST_PASSWORD", "AnalystDemo!2026")),
        ("auditor", os.getenv("DEMO_AUDITOR_PASSWORD", "AuditorDemo!2026")),
    ]
    session.add_all([
        User(username=username, password_hash=hash_password(password), role_id=role_by_name[username].id)
        for username, password in demo_users
    ])
    asset_types = ["database", "web_server", "api", "workstation", "laptop", "cloud_workload", "identity_server", "payment_system", "email_server", "backup_server"]
    assets = [Asset(name=f"Demo {asset_types[i % len(asset_types)].replace('_', ' ').title()} {i+1:03}", asset_type=asset_types[i % len(asset_types)], business_unit_id=units[i % len(units)].id, criticality=round(rng.uniform(.2, .98),2), data_sensitivity=round(rng.uniform(.2, .98),2), internet_exposed=i % 3 == 0) for i in range(100)]
    session.add_all(assets); session.flush()
    session.add_all([Application(name=f"Enterprise Application {i+1:03}", business_unit_id=units[i % len(units)].id) for i in range(150)])
    session.add_all([Vulnerability(asset_id=assets[i % 100].id, cve_id=f"CVE-202{(i % 6)}-{1000+i}", cvss=round(rng.uniform(3, 10),1), exploitability=round(rng.uniform(.1,1),2), source_id="demo-vm", source_event_id=f"demo-vuln-{i}") for i in range(600)])
    controls = [Control(name=f"Control {i+1:02}", category=["identity","endpoint","network","recovery","monitoring"][i%5], implementation_cost=float((i+1)*100000), baseline_effectiveness=round(rng.uniform(.35,.85),2)) for i in range(35)]
    session.add_all(controls); session.flush()
    session.add_all([Incident(asset_id=assets[i%100].id, severity=["low","medium","high","critical"][i%4], financial_loss=float(rng.randint(50_000,3_000_000))) for i in range(520)])
    session.add_all([ThreatScenario(name=f"Threat Scenario {i+1:02}", threat_type=["ransomware","credential_compromise","data_breach","cloud_misconfiguration"][i%4], activity=round(rng.uniform(.2,.95),2)) for i in range(24)])
    _ensure_investment_options(session)
    session.add_all([FrameworkMapping(framework=framework, control_reference=reference, control_id=controls[i % len(controls)].id) for i,(framework,reference) in enumerate([(f,r) for f, refs in {"NIST CSF":["PR.AA","DE.CM"],"ISO 27001":["A.5.15","A.8.8"],"CIS":["1","4"],"RBI":["Vulnerability Management"],"SEBI":["IAM"]}.items() for r in refs])])
    session.commit()
    return {"assets":100,"applications":150,"vulnerabilities":600,"controls":35,"incidents":520,"threat_scenarios":24,"status":"seeded"}
