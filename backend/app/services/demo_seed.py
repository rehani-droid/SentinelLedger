"""Deterministic, idempotent SIH demo dataset seeding."""
from random import Random
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..core.security import hash_password
from ..models import Application, Asset, BusinessUnit, Control, FrameworkMapping, Incident, InvestmentOptionRecord, Role, ThreatScenario, User, Vulnerability

SEED = 26105
def seed_demo(session: Session) -> dict[str, int]:
    if session.scalar(select(Asset.id).limit(1)):
        return {"assets": session.query(Asset).count(), "status": "already_seeded"}
    rng = Random(SEED)
    units = [BusinessUnit(name=name) for name in ["Retail Banking", "Payments", "Wealth", "Operations", "Technology", "Risk", "Corporate"]]
    roles = [Role(name=name) for name in ["ciso", "analyst", "auditor"]]
    session.add_all(units + roles); session.flush()
    role_by_name = {role.name: role for role in roles}
    session.add_all([User(username="ciso", password_hash=hash_password("CisoDemo!2026"), role_id=role_by_name["ciso"].id), User(username="analyst", password_hash=hash_password("AnalystDemo!2026"), role_id=role_by_name["analyst"].id), User(username="auditor", password_hash=hash_password("AuditorDemo!2026"), role_id=role_by_name["auditor"].id)])
    asset_types = ["database", "web_server", "api", "workstation", "laptop", "cloud_workload", "identity_server", "payment_system", "email_server", "backup_server"]
    assets = [Asset(name=f"Demo {asset_types[i % len(asset_types)].replace('_', ' ').title()} {i+1:03}", asset_type=asset_types[i % len(asset_types)], business_unit_id=units[i % len(units)].id, criticality=round(rng.uniform(.2, .98),2), data_sensitivity=round(rng.uniform(.2, .98),2), internet_exposed=i % 3 == 0) for i in range(100)]
    session.add_all(assets); session.flush()
    session.add_all([Application(name=f"Enterprise Application {i+1:03}", business_unit_id=units[i % len(units)].id) for i in range(150)])
    session.add_all([Vulnerability(asset_id=assets[i % 100].id, cve_id=f"CVE-202{(i % 6)}-{1000+i}", cvss=round(rng.uniform(3, 10),1), exploitability=round(rng.uniform(.1,1),2), source_id="demo-vm", source_event_id=f"demo-vuln-{i}") for i in range(600)])
    controls = [Control(name=f"Control {i+1:02}", category=["identity","endpoint","network","recovery","monitoring"][i%5], implementation_cost=float((i+1)*100000), baseline_effectiveness=round(rng.uniform(.35,.85),2)) for i in range(35)]
    session.add_all(controls); session.flush()
    session.add_all([Incident(asset_id=assets[i%100].id, severity=["low","medium","high","critical"][i%4], financial_loss=float(rng.randint(50_000,3_000_000))) for i in range(520)])
    session.add_all([ThreatScenario(name=f"Threat Scenario {i+1:02}", threat_type=["ransomware","credential_compromise","data_breach","cloud_misconfiguration"][i%4], activity=round(rng.uniform(.2,.95),2)) for i in range(24)])
    session.add_all([InvestmentOptionRecord(code=code, name=name, cost=cost, risk_reduction=reduction) for code,name,cost,reduction in [("patch","Patch critical vulnerabilities",800000,2800000),("mfa","Privileged MFA",1200000,3500000),("edr","EDR expansion",2000000,3000000),("segment","Network segmentation",2500000,4200000)]])
    session.add_all([FrameworkMapping(framework=framework, control_reference=reference, control_id=controls[i % len(controls)].id) for i,(framework,reference) in enumerate([(f,r) for f, refs in {"NIST CSF":["PR.AA","DE.CM"],"ISO 27001":["A.5.15","A.8.8"],"CIS":["1","4"],"RBI":["Vulnerability Management"],"SEBI":["IAM"]}.items() for r in refs])])
    session.commit()
    return {"assets":100,"applications":150,"vulnerabilities":600,"controls":35,"incidents":520,"threat_scenarios":24,"status":"seeded"}
