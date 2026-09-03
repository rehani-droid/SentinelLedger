"""Safe, replaceable adapters for synthetic or production telemetry connectors."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SourceType(StrEnum):
    vulnerability_management = "vulnerability_management"
    siem = "siem"
    iam = "iam"
    edr = "edr"
    cspm = "cspm"
    asset_inventory = "asset_inventory"
    threat_intelligence = "threat_intelligence"


class NormalizedEvent(BaseModel):
    source_id: str = Field(min_length=1, max_length=80)
    source_type: SourceType
    source_event_id: str = Field(min_length=1, max_length=100)
    observed_at: datetime
    payload: dict[str, Any]

    @field_validator("observed_at")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("observed_at must include a timezone")
        return value.astimezone(timezone.utc)

    def payload_fingerprint(self) -> str:
        canonical = json.dumps(self.payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


class SourceAdapter(ABC):
    source_type: SourceType

    @abstractmethod
    def normalize(self, raw: dict[str, Any]) -> NormalizedEvent: ...


class GenericAdapter(SourceAdapter):
    """Normalises vendor-neutral envelopes; vendor adapters can subclass it later."""

    def __init__(self, source_type: SourceType) -> None:
        self.source_type = source_type

    def normalize(self, raw: dict[str, Any]) -> NormalizedEvent:
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        return NormalizedEvent(
            source_id=raw.get("source_id"), source_type=self.source_type,
            source_event_id=raw.get("source_event_id"), observed_at=raw.get("observed_at"), payload=payload,
        )


ADAPTERS = {source: GenericAdapter(source) for source in SourceType}


def normalize_json(source_type: SourceType, records: list[dict[str, Any]]) -> list[NormalizedEvent]:
    if not records:
        raise ValueError("at least one event is required")
    return [ADAPTERS[source_type].normalize(record) for record in records]


def normalize_json_partial(source_type: SourceType, records: list[dict[str, Any]]) -> tuple[list[NormalizedEvent], list[dict[str, Any]]]:
    """Keep valid events in a batch when individual source records are malformed."""
    events: list[NormalizedEvent] = []
    rejected: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        try:
            events.append(ADAPTERS[source_type].normalize(record))
        except Exception as error:
            rejected.append({"index": index, "reason": str(error)})
    return events, rejected


def normalize_csv(source_type: SourceType, content: str) -> list[NormalizedEvent]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV header is required")
    required = {"source_id", "source_event_id", "observed_at", "payload"}
    missing = required - set(reader.fieldnames)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")
    records: list[dict[str, Any]] = []
    for row in reader:
        try:
            row["payload"] = json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError("CSV payload must be valid JSON") from error
        records.append(row)
    return normalize_json(source_type, records)


def normalize_csv_partial(source_type: SourceType, content: str) -> tuple[list[NormalizedEvent], list[dict[str, Any]]]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        raise ValueError("CSV header is required")
    required = {"source_id", "source_event_id", "observed_at", "payload"}
    missing = required - set(reader.fieldnames)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")
    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, row in enumerate(reader):
        try:
            row["payload"] = json.loads(row["payload"])
            records.append(row)
        except (TypeError, json.JSONDecodeError):
            rejected.append({"index": index, "reason": "CSV payload must be valid JSON"})
    events, invalid_envelopes = normalize_json_partial(source_type, records)
    return events, rejected + invalid_envelopes
