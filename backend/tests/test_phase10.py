import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import current_user
from app.main import app
from app.schemas import RiskInput, ScenarioInput
from app.core.security import decode_token
from pydantic import ValidationError


def test_data_and_calculation_endpoints_require_authentication():
    protected_paths = {
        "/api/v1/admin/seed",
        "/api/v1/assets",
        "/api/v1/financial/eal",
        "/api/v1/risk/assess",
        "/api/v1/scenarios/mfa",
    }
    routes = {route.path: route for route in app.routes if route.path in protected_paths}
    assert set(routes) == protected_paths
    for route in routes.values():
        assert route.dependant.dependencies


def test_missing_and_malformed_tokens_are_rejected():
    with pytest.raises(HTTPException) as missing:
        current_user(credentials=None, session=None)
    assert missing.value.status_code == 401

    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.a.jwt")
    with pytest.raises(HTTPException) as malformed:
        current_user(credentials=credentials, session=None)
    assert malformed.value.status_code == 401


def test_risk_and_scenario_inputs_reject_unsafe_values():
    with pytest.raises(ValidationError):
        RiskInput(
            cvss=1, exploitability=0.1, criticality=0.5, internet_exposure=0.1,
            vulnerability_age_days=1, threat_activity=0.1,
            historical_incident_rate=0.1, control_reduction=0.1,
            losses={"downtime_cost": -1},
        )
    with pytest.raises(ValidationError):
        ScenarioInput(current_privileged_coverage=0.9, target_privileged_coverage=0.1)


def test_token_claims_are_verified():
    with pytest.raises(ValueError):
        decode_token("eyJhbGciOiJub25lIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjo0MTAyNDQ0ODAwfQ.signature")
