"""Versioned API for SentinelLedger's offline demo and production adapters."""
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .ai.fallback import answer
from .auth import require_roles
from .audit.ledger import AuditLedger
from .compliance import FRAMEWORKS
from .core.config import settings
from .db import Base, engine, get_session
from .ingestion.schemas import VulnerabilityEvent
from .models import Asset, Incident, IngestionEvent, Role, User, Vulnerability
from .optimization.portfolio import InvestmentOption, optimise
from .risk.engine import cyber_var, eal, expected_loss, likelihood
from .schemas import AIQueryInput, AuditInput, CsvTelemetryInput, LoginInput, MfaScenarioInput, OptimisationInput, RiskInput, TelemetryBatchInput
from .core.security import issue_token, verify_password
from .services.demo_seed import seed_demo
from sqlalchemy import func, select
from .audit.ledger import GENESIS_HASH, canonical_json, digest, verify_persisted_chain
from .models import AuditEventRecord
from .scenarios.service import simulate_privileged_mfa
from .ingestion.adapters import SourceType, normalize_csv, normalize_json

app = FastAPI(title="SentinelLedger API", version="0.1.0", description="Modelled cyber risk decision support.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"])
ledger = AuditLedger()
DEMO_OPTIONS = [
    InvestmentOption("patch", "Patch critical vulnerabilities", 800_000, 2_800_000),
    InvestmentOption("mfa", "Privileged MFA rollout", 1_200_000, 3_500_000),
    InvestmentOption("edr", "EDR coverage expansion", 2_000_000, 3_000_000),
    InvestmentOption("segmentation", "Network segmentation", 2_500_000, 4_200_000, depends_on=("edr",)),
]

@app.on_event("startup")
def initialise_database() -> None:
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "offline-demo"}

@app.post("/api/v1/auth/login")
def login(data: LoginInput, session: Session = Depends(get_session)) -> dict:
    user = session.scalar(select(User).where(User.username == data.username))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    role = session.get(Role, user.role_id)
    return {"access_token": issue_token(user.username, role.name), "token_type": "bearer", "role": role.name}

@app.post("/api/v1/admin/seed")
def seed(session: Session = Depends(get_session)) -> dict:
    return seed_demo(session)

@app.post("/api/v1/ingestion/vulnerabilities", status_code=status.HTTP_201_CREATED)
def ingest_vulnerability(event: VulnerabilityEvent, session: Session = Depends(get_session)) -> dict:
    record = Vulnerability(asset_id=event.asset_id, cve_id=event.cve_id, cvss=event.cvss,
                           exploitability=event.exploitability, source_id=event.source_id,
                           source_event_id=event.source_event_id)
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate source event")
    return {"id": record.id, "status": "normalised", "source_id": event.source_id}

def _record_telemetry(events, session: Session) -> dict:
    records = [IngestionEvent(source_id=event.source_id, source_type=event.source_type.value,
                              source_event_id=event.source_event_id, observed_at=event.observed_at,
                              payload_hash=event.payload_fingerprint()) for event in events]
    session.add_all(records)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Duplicate source event")
    return {"accepted": len(records), "status": "normalised", "recalculation_requested": True,
            "sources": sorted({event.source_type.value for event in events})}

@app.post("/api/v1/ingestion/{source_type}/json", status_code=status.HTTP_201_CREATED)
def ingest_json(source_type: SourceType, batch: TelemetryBatchInput, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    try:
        return _record_telemetry(normalize_json(source_type, batch.events), session)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

@app.post("/api/v1/ingestion/{source_type}/csv", status_code=status.HTTP_201_CREATED)
def ingest_csv(source_type: SourceType, batch: CsvTelemetryInput, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    try:
        return _record_telemetry(normalize_csv(source_type, batch.content), session)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

@app.get("/api/v1/frameworks")
def frameworks() -> dict:
    return {"frameworks": FRAMEWORKS, "disclaimer": "Mappings are prototype references, not compliance certification."}

@app.get("/api/v1/assets")
def list_assets(page: int = 1, page_size: int = 25, session: Session = Depends(get_session)) -> dict:
    page_size = min(max(page_size, 1), 100); page = max(page, 1)
    query = select(Asset).order_by(Asset.criticality.desc())
    total = session.scalar(select(func.count()).select_from(Asset)) or 0
    rows = session.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"id": a.id, "name": a.name, "type": a.asset_type, "criticality": a.criticality, "internet_exposed": a.internet_exposed} for a in rows], "page": page, "page_size": page_size, "total": total}

@app.get("/api/v1/financial/eal")
def enterprise_eal(session: Session = Depends(get_session)) -> dict:
    losses = session.scalar(select(func.coalesce(func.sum(Incident.financial_loss), 0.0))) or 0.0
    return {"eal": losses / 5, "basis": "five-year deterministic synthetic incident history", "model_version": "1.0.0"}

@app.post("/api/v1/ai/query")
def ai_query(data: AIQueryInput, session: Session = Depends(get_session)) -> dict:
    losses = session.scalar(select(func.coalesce(func.sum(Incident.financial_loss), 0.0))) or 0.0
    return {**answer(data.question, enterprise_eal=losses / 5), "source": "persisted synthetic incident history"}

@app.post("/api/v1/risk/assess")
def assess_risk(data: RiskInput) -> dict:
    loss = expected_loss(data.losses)
    probability = likelihood(**data.model_dump(exclude={"losses"}))
    return {"likelihood": probability, "expected_loss": loss, "eal": eal(probability, loss),
            "var": cyber_var(annual_probability=probability, expected_loss_per_incident=loss), "model_version": "1.0.0"}

@app.post("/api/v1/optimization")
def investment_optimisation(data: OptimisationInput, _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    result = optimise(DEMO_OPTIONS, data.budget)
    return {**result, "selected": [item.__dict__ for item in result["selected"]], "estimate": "modelled"}

@app.post("/api/v1/scenarios/mfa")
def simulate_mfa(data: MfaScenarioInput) -> dict:
    return simulate_privileged_mfa(**data.model_dump())

@app.post("/api/v1/audit", status_code=status.HTTP_201_CREATED)
def finalise_assessment(data: AuditInput, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    payload = data.model_dump()
    previous = session.scalar(select(AuditEventRecord).order_by(AuditEventRecord.id.desc()).limit(1))
    previous_hash = previous.event_hash if previous else GENESIS_HASH
    event = AuditEventRecord(event_hash=digest(payload, previous_hash), previous_hash=previous_hash, payload=canonical_json(payload))
    session.add(event); session.commit(); session.refresh(event)
    return {"sequence": event.id, "hash": event.event_hash, "timestamp": event.created_at}

@app.get("/api/v1/audit")
def list_audit_events(page: int = 1, page_size: int = 25, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "auditor"))) -> dict:
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    total = session.scalar(select(func.count()).select_from(AuditEventRecord)) or 0
    records = session.scalars(select(AuditEventRecord).order_by(AuditEventRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"sequence": record.id, "hash": record.event_hash, "previous_hash": record.previous_hash, "timestamp": record.created_at} for record in records], "page": page, "page_size": page_size, "total": total}

@app.get("/api/v1/audit/verify-chain")
def verify_audit_chain(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "auditor"))) -> dict:
    events = session.scalars(select(AuditEventRecord).order_by(AuditEventRecord.id)).all()
    return verify_persisted_chain(events)

@app.get("/api/v1/audit/{sequence}/verify")
def verify_assessment(sequence: int, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "auditor"))) -> dict:
    if sequence < 1:
        raise HTTPException(status_code=400, detail="Sequence must be positive")
    event = session.get(AuditEventRecord, sequence)
    if not event: return {"sequence": sequence, "valid": False}
    prior = session.get(AuditEventRecord, sequence - 1)
    expected_previous = prior.event_hash if prior else GENESIS_HASH
    import json
    return {"sequence": sequence, "valid": event.previous_hash == expected_previous and event.event_hash == digest(json.loads(event.payload), event.previous_hash)}
