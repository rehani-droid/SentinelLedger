from math import isfinite
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .ingestion.adapters import SourceType
from typing import Any

class StrictModel(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")

class RiskInput(StrictModel):
    cvss: float = Field(ge=0, le=10)
    exploitability: float = Field(ge=0, le=1)
    criticality: float = Field(ge=.1, le=1)
    internet_exposure: float = Field(ge=0, le=1)
    vulnerability_age_days: int = Field(ge=0)
    threat_activity: float = Field(ge=0, le=1)
    historical_incident_rate: float = Field(ge=0, le=1)
    control_reduction: float = Field(ge=0, le=1)
    losses: dict[str, float]

    @field_validator("losses")
    @classmethod
    def losses_must_be_finite_and_non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        if any(not isfinite(amount) or amount < 0 for amount in value.values()):
            raise ValueError("Financial loss components must be finite and non-negative")
        return value

class OptimisationInput(StrictModel):
    budget: float = Field(ge=0)

class AuditInput(StrictModel):
    assessment_id: str = Field(min_length=1, max_length=100)
    model_version: str = Field(min_length=1, max_length=20)
    eal: float = Field(ge=0)

class MfaScenarioInput(StrictModel):
    before_eal: float = Field(gt=0)
    rollout_cost: float = Field(gt=0)
    current_privileged_coverage: float = Field(ge=0, le=1)
    target_privileged_coverage: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def coverage_must_be_ordered(self):
        if self.current_privileged_coverage > self.target_privileged_coverage:
            raise ValueError("Coverage values must be ordered probabilities")
        return self

class ScenarioInput(StrictModel):
    mfa_enabled: bool = False
    current_privileged_coverage: float = Field(ge=0, le=1)
    target_privileged_coverage: float = Field(ge=0, le=1)
    remediation_delay_days: int = Field(ge=0, le=3650)
    control_code: str | None = Field(default=None, min_length=1, max_length=60)
    investment_code: str | None = Field(default=None, min_length=1, max_length=60)
    investment_change: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def coverage_must_be_ordered(self):
        if self.current_privileged_coverage > self.target_privileged_coverage:
            raise ValueError("Coverage values must be ordered probabilities")
        return self

class AIQueryInput(StrictModel):
    question: str = Field(min_length=3, max_length=500)

class LoginInput(StrictModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)

class TelemetryBatchInput(StrictModel):
    events: list[dict[str, Any]] = Field(min_length=1, max_length=1000)

class CsvTelemetryInput(StrictModel):
    content: str = Field(min_length=1, max_length=2_000_000)
