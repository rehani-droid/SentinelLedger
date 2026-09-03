from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..db import Base

def now() -> datetime:
    return datetime.now(timezone.utc)

class BusinessUnit(Base):
    __tablename__ = "business_units"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)

class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    business_unit_id: Mapped[int] = mapped_column(ForeignKey("business_units.id"), index=True)

class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    severity: Mapped[str] = mapped_column(String(20))
    financial_loss: Mapped[float] = mapped_column(Float)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class ThreatScenario(Base):
    __tablename__ = "threat_scenarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    threat_type: Mapped[str] = mapped_column(String(80))
    activity: Mapped[float] = mapped_column(Float)

class InvestmentOptionRecord(Base):
    __tablename__ = "investment_options"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    cost: Mapped[float] = mapped_column(Float)
    risk_reduction: Mapped[float] = mapped_column(Float)
    affected_asset_ids: Mapped[list] = mapped_column(JSON, default=list)
    affected_control_ids: Mapped[list] = mapped_column(JSON, default=list)
    dependencies: Mapped[list] = mapped_column(JSON, default=list)
    exclusions: Mapped[list] = mapped_column(JSON, default=list)

class OptimizationRunRecord(Base):
    __tablename__ = "optimization_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    budget: Mapped[float] = mapped_column(Float)
    selected_investments: Mapped[list] = mapped_column(JSON)
    total_cost: Mapped[float] = mapped_column(Float)
    estimated_risk_reduction: Mapped[float] = mapped_column(Float)
    residual_risk: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)

class FrameworkMapping(Base):
    __tablename__ = "framework_mappings"
    id: Mapped[int] = mapped_column(primary_key=True)
    framework: Mapped[str] = mapped_column(String(80), index=True)
    control_reference: Mapped[str] = mapped_column(String(80))
    control_id: Mapped[int | None] = mapped_column(ForeignKey("controls.id"))

class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    business_unit_id: Mapped[int | None] = mapped_column(ForeignKey("business_units.id"))
    criticality: Mapped[float] = mapped_column(Float)
    data_sensitivity: Mapped[float] = mapped_column(Float)
    internet_exposed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    cve_id: Mapped[str] = mapped_column(String(30), index=True)
    cvss: Mapped[float] = mapped_column(Float)
    exploitability: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="open")
    source_id: Mapped[str] = mapped_column(String(80))
    source_event_id: Mapped[str] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("source_id", "source_event_id", name="uq_source_event"),)

class Control(Base):
    __tablename__ = "controls"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(80))
    implementation_cost: Mapped[float] = mapped_column(Float)
    baseline_effectiveness: Mapped[float] = mapped_column(Float)

class RiskAssessmentRecord(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    target_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    scope: Mapped[str] = mapped_column(String(30), index=True)
    business_unit_id: Mapped[int | None] = mapped_column(ForeignKey("business_units.id"), index=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), index=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id"), index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    likelihood: Mapped[float] = mapped_column(Float)
    financial_impact: Mapped[float] = mapped_column(Float)
    expected_annual_loss: Mapped[float] = mapped_column(Float)
    var_95: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(20))
    major_risk_drivers: Mapped[list] = mapped_column(JSON)
    assumptions: Mapped[dict] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float)
    data_freshness: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)

class AuditEventRecord(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_hash: Mapped[str] = mapped_column(String(64), unique=True)
    previous_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class IngestionEvent(Base):
    """Immutable source receipt metadata; raw telemetry is intentionally not retained here."""
    __tablename__ = "ingestion_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(80), index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    source_event_id: Mapped[str] = mapped_column(String(100))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    payload_hash: Mapped[str] = mapped_column(String(64))
    __table_args__ = (UniqueConstraint("source_id", "source_event_id", name="uq_ingestion_source_event"),)

class TelemetryEntityState(Base):
    """Latest applied event for a domain object; prevents stale feeds overwriting newer state."""
    __tablename__ = "telemetry_entity_states"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[str] = mapped_column(String(80), index=True)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    entity_key: Mapped[str] = mapped_column(String(200))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_event_id: Mapped[str] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("source_id", "source_type", "entity_key", name="uq_telemetry_entity_state"),)
