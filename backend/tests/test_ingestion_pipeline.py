from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.ingestion.adapters import SourceType, normalize_json_partial
from app.ingestion.pipeline import ingest_normalized_events
from app.models import Application, Asset, BusinessUnit, Control, Incident, IngestionEvent, RiskAssessmentRecord, ThreatScenario, Vulnerability


def _event(source: SourceType, event_id: str, payload: dict, observed_at: datetime | None = None) -> dict:
    return {"source_id": "pipeline-test", "source_event_id": event_id,
            "observed_at": (observed_at or datetime(2026, 1, 1, tzinfo=timezone.utc)).isoformat(), "payload": payload}


def _session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    unit = BusinessUnit(name="Technology")
    session.add(unit); session.commit()
    return session, unit.id


def test_valid_events_populate_domain_entities_and_recalculate_risk() -> None:
    session, unit_id = _session()
    raw = [
        _event(SourceType.asset_inventory, "asset-1", {"name": "Payments API", "asset_type": "api", "criticality": .9, "data_sensitivity": .8, "internet_exposed": True, "business_unit_id": unit_id}),
    ]
    events, rejected = normalize_json_partial(SourceType.asset_inventory, raw)
    assert not rejected
    assert ingest_normalized_events(session, events)["recalculated"] is True
    asset = session.scalar(select(Asset).where(Asset.name == "Payments API"))
    assert asset is not None
    event_groups = [
        (SourceType.asset_inventory, "app-1", {"entity": "application", "name": "Payments Portal", "business_unit_id": unit_id}),
        (SourceType.vulnerability_management, "vuln-1", {"asset_id": asset.id, "cve_id": "CVE-2026-10001", "cvss": 9.1, "exploitability": .8}),
        (SourceType.siem, "incident-1", {"asset_id": asset.id, "severity": "high", "financial_loss": 500000}),
        (SourceType.iam, "control-1", {"name": "Privileged MFA", "category": "identity", "implementation_cost": 100000, "baseline_effectiveness": .7}),
        (SourceType.threat_intelligence, "threat-1", {"name": "Credential compromise", "threat_type": "credential_compromise", "activity": .8}),
    ]
    for source, event_id, payload in event_groups:
        events, rejected = normalize_json_partial(source, [_event(source, event_id, payload)])
        assert not rejected
        assert ingest_normalized_events(session, events)["accepted"] == 1
    assert session.query(Application).count() == 1
    assert session.query(Vulnerability).count() == 1
    assert session.query(Incident).count() == 1
    assert session.query(Control).count() == 1
    assert session.query(ThreatScenario).count() == 1
    assert session.scalar(select(RiskAssessmentRecord).where(RiskAssessmentRecord.target_key == f"asset:{asset.id}")) is not None


def test_duplicate_and_stale_events_do_not_overwrite_domain_data() -> None:
    session, _ = _session()
    newest = datetime(2026, 1, 2, tzinfo=timezone.utc)
    payload = {"name": "Managed Host", "asset_type": "server", "criticality": .8, "data_sensitivity": .5}
    events, _ = normalize_json_partial(SourceType.asset_inventory, [_event(SourceType.asset_inventory, "one", payload, newest)])
    assert ingest_normalized_events(session, events)["accepted"] == 1
    assert ingest_normalized_events(session, events)["duplicates"] == 1
    stale_payload = {**payload, "criticality": .2}
    events, _ = normalize_json_partial(SourceType.asset_inventory, [_event(SourceType.asset_inventory, "two", stale_payload, newest - timedelta(days=1))])
    assert ingest_normalized_events(session, events)["stale"] == 1
    assert session.scalar(select(Asset).where(Asset.name == "Managed Host")).criticality == .8
    assert session.query(IngestionEvent).count() == 2


def test_malformed_and_missing_payload_fields_are_rejected_without_aborting_batch() -> None:
    session, _ = _session()
    valid = _event(SourceType.asset_inventory, "valid", {"name": "Valid Host", "asset_type": "server", "criticality": .7, "data_sensitivity": .4})
    malformed = {"source_id": "pipeline-test", "source_event_id": "broken", "observed_at": "2026-01-01T00:00:00+00:00", "payload": "not-an-object"}
    events, envelope_errors = normalize_json_partial(SourceType.asset_inventory, [valid, malformed])
    result = ingest_normalized_events(session, events)
    assert result["accepted"] == 1
    assert len(envelope_errors) == 1
    missing_field = _event(SourceType.asset_inventory, "missing", {"name": "Incomplete", "criticality": .7, "data_sensitivity": .4})
    events, _ = normalize_json_partial(SourceType.asset_inventory, [missing_field])
    result = ingest_normalized_events(session, events)
    assert result["accepted"] == 0
    assert len(result["rejected"]) == 1
    assert session.query(Asset).count() == 1
