"""Versioned API for SentinelLedger's offline demo and production adapters."""
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .ai.fallback import answer
from .auth import require_roles
from .audit.ledger import AuditLedger
from .compliance import FRAMEWORKS
from .core.config import settings
from .db import get_session
from .models import Asset, Incident, InvestmentOptionRecord, OptimizationRunRecord, Role, User
from .optimization.service import run_optimization, serialize_option, serialize_run
from .risk.engine import cyber_var, eal, expected_loss, likelihood
from .schemas import AIQueryInput, AuditInput, CsvTelemetryInput, LoginInput, MfaScenarioInput, OptimisationInput, RiskInput, TelemetryBatchInput
from .core.security import issue_token, verify_password
from .services.demo_seed import seed_demo
from .services.risk_persistence import recalculate_risk_assessments
from sqlalchemy import func, select
from .audit.ledger import GENESIS_HASH, canonical_json, digest, verify_persisted_chain
from .models import AuditEventRecord
from .scenarios.service import simulate_privileged_mfa
from .ingestion.adapters import SourceType, normalize_csv_partial, normalize_json_partial
from .ingestion.pipeline import ingest_normalized_events
from .services.dashboard import asset_detail, business_units, executive, technical

app = FastAPI(title="SentinelLedger API", version="0.1.0", description="Modelled cyber risk decision support.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"])
ledger = AuditLedger()

@app.on_event("startup")
def initialise_database() -> None:
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")

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
    result = seed_demo(session); recalculate_risk_assessments(session); return result

@app.get("/api/v1/dashboard/executive")
def executive_dashboard(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return executive(session)

@app.get("/api/v1/dashboard/technical")
def technical_dashboard(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return technical(session)

@app.get("/api/v1/assets/{asset_id}")
def get_asset(asset_id: int, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    result = asset_detail(session, asset_id)
    if result is None: raise HTTPException(404, "Asset not found")
    return result

@app.get("/api/v1/business-units")
def list_business_units(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return {"items": business_units(session)}

@app.post("/api/v1/risk/recalculate")
def recalculate_risk(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    return {"status": "recalculated", **recalculate_risk_assessments(session)}

@app.post("/api/v1/ingestion/{source_type}/json", status_code=status.HTTP_201_CREATED)
def ingest_json(source_type: SourceType, batch: TelemetryBatchInput, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    events, rejected = normalize_json_partial(source_type, batch.events)
    result = ingest_normalized_events(session, events)
    result["rejected"] = rejected + result["rejected"]
    return result

@app.post("/api/v1/ingestion/{source_type}/csv", status_code=status.HTTP_201_CREATED)
def ingest_csv(source_type: SourceType, batch: CsvTelemetryInput, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    try:
        events, rejected = normalize_csv_partial(source_type, batch.content)
        result = ingest_normalized_events(session, events)
        result["rejected"] = rejected + result["rejected"]
        return result
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
def investment_optimisation(data: OptimisationInput, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    return {**serialize_run(run_optimization(session, data.budget)), "estimate": "modelled"}

@app.get("/api/v1/investment-options")
def list_investment_options(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return {"items": [serialize_option(record) for record in session.scalars(select(InvestmentOptionRecord).order_by(InvestmentOptionRecord.code)).all()]}

@app.get("/api/v1/optimization")
def list_optimization_runs(page: int = 1, page_size: int = 25, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    total = session.scalar(select(func.count()).select_from(OptimizationRunRecord)) or 0
    records = session.scalars(select(OptimizationRunRecord).order_by(OptimizationRunRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_run(record) for record in records], "page": page, "page_size": page_size, "total": total}

@app.get("/api/v1/optimization/{run_id}")
def get_optimization_run(run_id: int, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    record = session.get(OptimizationRunRecord, run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Optimisation run not found")
    return serialize_run(record)

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
