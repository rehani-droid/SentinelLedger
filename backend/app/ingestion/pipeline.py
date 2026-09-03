"""Maps normalised telemetry envelopes onto the existing risk domain safely."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Application, Asset, BusinessUnit, Control, Incident, IngestionEvent, TelemetryEntityState, ThreatScenario, Vulnerability
from ..services.risk_persistence import recalculate_risk_assessments
from .adapters import NormalizedEvent, SourceType


class AssetPayload(BaseModel):
    entity: str = "asset"
    name: str = Field(min_length=1, max_length=160)
    asset_type: str = Field(min_length=1, max_length=50)
    criticality: float = Field(ge=.1, le=1)
    data_sensitivity: float = Field(ge=0, le=1)
    internet_exposed: bool = False
    business_unit_id: int | None = Field(default=None, gt=0)


class ApplicationPayload(BaseModel):
    entity: str = "application"
    name: str = Field(min_length=1, max_length=160)
    business_unit_id: int = Field(gt=0)


class VulnerabilityPayload(BaseModel):
    asset_id: int = Field(gt=0)
    cve_id: str = Field(pattern=r"^CVE-\d{4}-\d{4,}$")
    cvss: float = Field(ge=0, le=10)
    exploitability: float = Field(ge=0, le=1)
    status: str = Field(default="open", min_length=1, max_length=30)


class IncidentPayload(BaseModel):
    asset_id: int = Field(gt=0)
    severity: str = Field(min_length=1, max_length=20)
    financial_loss: float = Field(ge=0)


class ControlPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    implementation_cost: float = Field(ge=0)
    baseline_effectiveness: float = Field(ge=0, le=1)


class ThreatPayload(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    threat_type: str = Field(min_length=1, max_length=80)
    activity: float = Field(ge=0, le=1)


def _entity_key(event: NormalizedEvent) -> str:
    payload = event.payload
    if event.source_type is SourceType.asset_inventory:
        return f"{payload.get('entity', 'asset')}:{payload.get('name', '')}"
    if event.source_type in {SourceType.vulnerability_management, SourceType.cspm}:
        return f"vulnerability:{payload.get('asset_id', '')}:{payload.get('cve_id', '')}"
    if event.source_type in {SourceType.siem, SourceType.edr}:
        return f"incident:{event.source_event_id}"
    if event.source_type is SourceType.iam:
        return f"control:{payload.get('name', '')}"
    return f"threat:{payload.get('name', '')}"


def _require_asset(session: Session, asset_id: int) -> None:
    if session.get(Asset, asset_id) is None:
        raise ValueError(f"asset_id {asset_id} does not exist")


def _as_utc(value: datetime) -> datetime:
    """SQLite may return naive values even for timezone-aware columns."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _apply_domain_event(session: Session, event: NormalizedEvent) -> None:
    payload: Any = event.payload
    if event.source_type is SourceType.asset_inventory:
        if payload.get("entity", "asset") == "application":
            data = ApplicationPayload.model_validate(payload)
            if session.get(BusinessUnit, data.business_unit_id) is None:
                raise ValueError(f"business_unit_id {data.business_unit_id} does not exist")
            record = session.scalar(select(Application).where(Application.name == data.name))
            if record is None:
                session.add(Application(name=data.name, business_unit_id=data.business_unit_id))
            else:
                record.business_unit_id = data.business_unit_id
            return
        data = AssetPayload.model_validate(payload)
        if data.business_unit_id is not None and session.get(BusinessUnit, data.business_unit_id) is None:
            raise ValueError(f"business_unit_id {data.business_unit_id} does not exist")
        record = session.scalar(select(Asset).where(Asset.name == data.name))
        if record is None:
            session.add(Asset(name=data.name, asset_type=data.asset_type, criticality=data.criticality,
                              data_sensitivity=data.data_sensitivity, internet_exposed=data.internet_exposed,
                              business_unit_id=data.business_unit_id))
        else:
            for field in ("asset_type", "criticality", "data_sensitivity", "internet_exposed", "business_unit_id"):
                setattr(record, field, getattr(data, field))
        return
    if event.source_type in {SourceType.vulnerability_management, SourceType.cspm}:
        data = VulnerabilityPayload.model_validate(payload); _require_asset(session, data.asset_id)
        record = session.scalar(select(Vulnerability).where(Vulnerability.asset_id == data.asset_id, Vulnerability.cve_id == data.cve_id))
        if record is None:
            session.add(Vulnerability(asset_id=data.asset_id, cve_id=data.cve_id, cvss=data.cvss,
                                      exploitability=data.exploitability, status=data.status, source_id=event.source_id,
                                      source_event_id=event.source_event_id))
        else:
            record.cvss, record.exploitability, record.status = data.cvss, data.exploitability, data.status
        return
    if event.source_type in {SourceType.siem, SourceType.edr}:
        data = IncidentPayload.model_validate(payload); _require_asset(session, data.asset_id)
        session.add(Incident(asset_id=data.asset_id, severity=data.severity, financial_loss=data.financial_loss, occurred_at=event.observed_at))
        return
    if event.source_type is SourceType.iam:
        data = ControlPayload.model_validate(payload)
        record = session.scalar(select(Control).where(Control.name == data.name))
        if record is None:
            session.add(Control(**data.model_dump()))
        else:
            record.category, record.implementation_cost, record.baseline_effectiveness = data.category, data.implementation_cost, data.baseline_effectiveness
        return
    data = ThreatPayload.model_validate(payload)
    record = session.scalar(select(ThreatScenario).where(ThreatScenario.name == data.name))
    if record is None:
        session.add(ThreatScenario(**data.model_dump()))
    else:
        record.threat_type, record.activity = data.threat_type, data.activity


def ingest_normalized_events(session: Session, events: list[NormalizedEvent]) -> dict[str, Any]:
    """Record receipts, apply valid non-stale domain changes, then refresh persisted risk once."""
    result: dict[str, Any] = {"accepted": 0, "duplicates": 0, "stale": 0, "rejected": [], "recalculated": False}
    changed = False
    for index, event in enumerate(events):
        if session.scalar(select(IngestionEvent.id).where(IngestionEvent.source_id == event.source_id, IngestionEvent.source_event_id == event.source_event_id)):
            result["duplicates"] += 1
            continue
        key = _entity_key(event)
        state = session.scalar(select(TelemetryEntityState).where(TelemetryEntityState.source_id == event.source_id, TelemetryEntityState.source_type == event.source_type.value, TelemetryEntityState.entity_key == key))
        receipt = IngestionEvent(source_id=event.source_id, source_type=event.source_type.value,
                                 source_event_id=event.source_event_id, observed_at=event.observed_at,
                                 payload_hash=event.payload_fingerprint())
        session.add(receipt)
        if state is not None and event.observed_at <= _as_utc(state.observed_at):
            result["stale"] += 1
            continue
        try:
            with session.begin_nested():
                _apply_domain_event(session, event)
                if state is None:
                    session.add(TelemetryEntityState(source_id=event.source_id, source_type=event.source_type.value,
                                                     entity_key=key, observed_at=event.observed_at, source_event_id=event.source_event_id))
                else:
                    state.observed_at, state.source_event_id = event.observed_at, event.source_event_id
            result["accepted"] += 1
            changed = True
        except (ValidationError, ValueError) as error:
            session.expunge(receipt)
            result["rejected"].append({"index": index, "reason": str(error)})
    session.commit()
    if changed:
        recalculate_risk_assessments(session)
        result["recalculated"] = True
    return result
