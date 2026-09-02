from pydantic import BaseModel, Field
from .ingestion.adapters import SourceType
from typing import Any

class RiskInput(BaseModel):
    cvss: float = Field(ge=0, le=10)
    exploitability: float = Field(ge=0, le=1)
    criticality: float = Field(ge=.1, le=1)
    internet_exposure: float = Field(ge=0, le=1)
    vulnerability_age_days: int = Field(ge=0)
    threat_activity: float = Field(ge=0, le=1)
    historical_incident_rate: float = Field(ge=0, le=1)
    control_reduction: float = Field(ge=0, le=1)
    losses: dict[str, float]

class OptimisationInput(BaseModel):
    budget: float = Field(ge=0)

class AuditInput(BaseModel):
    assessment_id: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=20)
    eal: float = Field(ge=0)

class MfaScenarioInput(BaseModel):
    before_eal: float = Field(gt=0)
    rollout_cost: float = Field(gt=0)
    current_privileged_coverage: float = Field(ge=0, le=1)
    target_privileged_coverage: float = Field(ge=0, le=1)

class AIQueryInput(BaseModel):
    question: str = Field(min_length=3, max_length=500)

class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)

class TelemetryBatchInput(BaseModel):
    events: list[dict[str, Any]] = Field(min_length=1, max_length=1000)

class CsvTelemetryInput(BaseModel):
    content: str = Field(min_length=1, max_length=2_000_000)
