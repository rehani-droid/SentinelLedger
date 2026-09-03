"""Versioned API for SentinelLedger's offline demo and production adapters."""
import logging
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .ai.service import handle_query
from .auth import require_roles
from .audit.ledger import AuditLedger
from .compliance import FRAMEWORKS
from .compliance.service import framework_mappings
from .core.config import settings
from .db import get_session
from .models import Asset, Control, Incident, InvestmentOptionRecord, OptimizationRunRecord, RiskAssessmentRecord, Role, User
from .optimization.service import run_optimization, serialize_option, serialize_run
from .risk.engine import cyber_var, eal, expected_loss, likelihood
from .schemas import AIQueryInput, AuditInput, CsvTelemetryInput, LoginInput, MfaScenarioInput, OptimisationInput, RiskInput, ScenarioInput, TelemetryBatchInput
from .core.security import issue_token, verify_password
from .services.demo_seed import seed_demo
from .services.risk_persistence import recalculate_risk_assessments
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from .audit.ledger import GENESIS_HASH, canonical_json, digest, verify_persisted_chain
from .models import AuditEventRecord
from .scenarios.service import simulate_privileged_mfa, simulate_scenario
from .ingestion.adapters import SourceType, normalize_csv_partial, normalize_json_partial
from .ingestion.pipeline import ingest_normalized_events
from .services.dashboard import asset_detail, business_units, executive, technical
from .ml.service import prediction_payload

app = FastAPI(title="SentinelLedger API", version="0.1.0", description="Modelled cyber risk decision support.")
logger = logging.getLogger("sentinelledger")
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
    if settings.seed_demo_data:
        with next(get_session()) as session:
            seed_demo(session)
            recalculate_risk_assessments(session)

@app.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    try:
        session.execute(select(1))
    except SQLAlchemyError:
        logger.exception("Health check database probe failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok", "mode": "offline-demo"}

@app.exception_handler(Exception)
async def unhandled_exception(request: Request, error: Exception):
    logger.exception("Unhandled request failure: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.post("/api/v1/auth/login")
def login(data: LoginInput, session: Session = Depends(get_session)) -> dict:
    user = session.scalar(select(User).where(User.username == data.username))
    if not user or not user.active or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    role = session.get(Role, user.role_id)
    if role is None:
        logger.error("User %s has no valid role", user.username)
        raise HTTPException(500, "User account is misconfigured")
    return {"access_token": issue_token(user.username, role.name), "token_type": "bearer", "role": role.name}

@app.post("/api/v1/admin/seed")
def seed(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso"))) -> dict:
    result = seed_demo(session); recalculate_risk_assessments(session); return result

@app.post("/api/v1/auth/logout")
def logout(_: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict[str, str]:
    return {"status": "logged_out"}

@app.get("/api/v1/dashboard/executive")
def executive_dashboard(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return executive(session)

@app.get("/api/v1/risk/predictive")
def predictive_risk(asset_id: int | None = Query(default=None, ge=1), session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return prediction_payload(session, asset_id)

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
def frameworks(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return framework_mappings(session)

@app.get("/api/v1/assets")
def list_assets(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    page_size = min(max(page_size, 1), 100); page = max(page, 1)
    query = select(Asset).order_by(Asset.criticality.desc())
    total = session.scalar(select(func.count()).select_from(Asset)) or 0
    rows = session.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [{"id": a.id, "name": a.name, "type": a.asset_type, "criticality": a.criticality, "internet_exposed": a.internet_exposed} for a in rows], "page": page, "page_size": page_size, "total": total}

@app.get("/api/v1/financial/eal")
def enterprise_eal(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    losses = session.scalar(select(func.coalesce(func.sum(Incident.financial_loss), 0.0))) or 0.0
    return {"eal": losses / 5, "basis": "five-year deterministic synthetic incident history", "model_version": "1.0.0"}

@app.post("/api/v1/ai/query")
def ai_query(data: AIQueryInput, session: Session = Depends(get_session),
             _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
    return handle_query(session, data.question)

@app.post("/api/v1/risk/assess")
def assess_risk(data: RiskInput, _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
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
def list_optimization_runs(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "analyst", "auditor"))) -> dict:
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
def simulate_mfa(data: MfaScenarioInput, _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    return simulate_privileged_mfa(**data.model_dump())

@app.post("/api/v1/scenarios")
def scenario(data: ScenarioInput, session: Session = Depends(get_session),
             _: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    enterprise = session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == "enterprise"))
    baseline_eal = enterprise.expected_annual_loss if enterprise else 0
    option = session.scalar(select(InvestmentOptionRecord).where(InvestmentOptionRecord.code == data.investment_code)) if data.investment_code else None
    if data.investment_code and option is None:
        raise HTTPException(status_code=422, detail="Unknown investment option")
    control = data.control_code
    if control:
        known_control = session.scalar(select(Control).where(Control.name == control))
        known_option = session.scalar(select(InvestmentOptionRecord).where(InvestmentOptionRecord.code == control))
        if known_control is None and known_option is None:
            raise HTTPException(status_code=422, detail="Unknown security control")
    return simulate_scenario(
        baseline_eal=baseline_eal, mfa_enabled=data.mfa_enabled,
        current_privileged_coverage=data.current_privileged_coverage,
        target_privileged_coverage=data.target_privileged_coverage,
        remediation_delay_days=data.remediation_delay_days,
        investment_reduction=option.risk_reduction if option else 0,
        investment_cost=option.cost if option else 0,
        selected_control=control, selected_investment=option.code if option else None,
        investment_change=data.investment_change,
    )

@app.post("/api/v1/audit", status_code=status.HTTP_201_CREATED)
def finalise_assessment(data: AuditInput, session: Session = Depends(get_session), user: User = Depends(require_roles("ciso", "analyst"))) -> dict:
    payload = {**data.model_dump(), "actor": user.username}
    previous = session.scalar(select(AuditEventRecord).order_by(AuditEventRecord.id.desc()).limit(1))
    previous_hash = previous.event_hash if previous else GENESIS_HASH
    event = AuditEventRecord(event_hash=digest(payload, previous_hash), previous_hash=previous_hash, payload=canonical_json(payload))
    session.add(event); session.commit(); session.refresh(event)
    return {"sequence": event.id, "hash": event.event_hash, "timestamp": event.created_at}

@app.get("/api/v1/audit")
def list_audit_events(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "auditor"))) -> dict:
    total = session.scalar(select(func.count()).select_from(AuditEventRecord)) or 0
    records = session.scalars(select(AuditEventRecord).order_by(AuditEventRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    import json
    items = []
    for record in records:
        payload = json.loads(record.payload)
        items.append({
            "sequence": record.id,
            "hash": record.event_hash,
            "previous_hash": record.previous_hash,
            "timestamp": record.created_at,
            "actor": payload.get("actor"),
            "action": "assessment_finalised",
            "resource": payload.get("assessment_id"),
            "payload": payload,
        })
    return {"items": items, "page": page, "page_size": page_size, "total": total}

@app.get("/api/v1/audit/verify-chain")
def verify_audit_chain(session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "auditor"))) -> dict:
    events = session.scalars(select(AuditEventRecord).order_by(AuditEventRecord.id)).all()
    return verify_persisted_chain(events)

@app.get("/api/v1/audit/{sequence}/verify")
def verify_assessment(sequence: int, session: Session = Depends(get_session), _: User = Depends(require_roles("ciso", "auditor"))) -> dict:
    if sequence < 1:
        raise HTTPException(status_code=400, detail="Sequence must be positive")
    event = session.get(AuditEventRecord, sequence)
    if not event:
        return {"sequence": sequence, "valid": False}
    prior = session.get(AuditEventRecord, sequence - 1)
    expected_previous = prior.event_hash if prior else GENESIS_HASH
    import json
    return {"sequence": sequence, "valid": event.previous_hash == expected_previous and event.event_hash == digest(json.loads(event.payload), event.previous_hash)}
