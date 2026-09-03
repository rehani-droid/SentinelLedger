from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.ml.service import FEATURE_NAMES, OBSERVATIONS_PER_ASSET, build_feature_rows, build_synthetic_historical_rows, prediction_payload
from app.auth import current_user
from app.ai.service import classify, handle_query
from fastapi import HTTPException
from app.services.demo_seed import seed_demo


def session_with_demo():
    engine = create_engine("sqlite://")
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    seed_demo(session)
    return session


def test_feature_generation_uses_only_persisted_fields_and_is_reproducible():
    session = session_with_demo()
    first = build_feature_rows(session)
    second = build_feature_rows(session)
    assert len(first) == 100
    assert first == second
    assert len(first[0].features) == len(FEATURE_NAMES)
    assert first[0].features[3] >= 0


def test_seeded_demo_trains_on_synthetic_history():
    payload = prediction_payload(session_with_demo())
    assert payload["modelled"] is True
    assert payload["available"] is True
    assert payload["target"] == "incident_within_90_days"
    assert payload["rows"] == 100 * OBSERVATIONS_PER_ASSET
    assert payload["positive_rows"] > 0
    assert payload["negative_rows"] > 0
    assert "predicted_likelihood" in payload
    assert payload["model_version"].startswith("phase9-")


def test_prediction_contract_contains_horizon_features_and_metrics():
    payload = prediction_payload(session_with_demo(), asset_id=999999)
    assert payload["prediction_horizon_days"] == 90
    assert payload["feature_names"] == list(FEATURE_NAMES)
    assert payload["trained_at"] is not None
    assert payload["available"] is False
    assert payload["unavailable_reason"] == "asset_not_found"


def test_model_produces_reproducible_prediction_when_both_classes_exist():
    session = session_with_demo()
    first = prediction_payload(session, asset_id=1)
    second = prediction_payload(session, asset_id=1)
    assert first["available"] is True
    assert 0 <= first["predicted_likelihood"] <= 1
    assert first["metrics"] == second["metrics"]
    assert first["key_predictive_drivers"] == second["key_predictive_drivers"]


def test_synthetic_history_has_multiple_time_separated_observations_and_both_classes():
    session = session_with_demo()
    first = build_synthetic_historical_rows(session)
    second = build_synthetic_historical_rows(session)
    assert first == second
    assert len(first) == 1200
    assert len({row.target for row in first}) == 2
    assert len({row.observed_at for row in first}) == OBSERVATIONS_PER_ASSET
    assert all(sum(row.asset_id == asset_id for row in first) == OBSERVATIONS_PER_ASSET for asset_id in range(1, 101))


def test_prediction_requires_authentication_dependency():
    try:
        current_user(credentials=None, session=session_with_demo())
    except HTTPException as error:
        assert error.status_code == 401
    else:
        raise AssertionError("Unauthenticated prediction access must be rejected")


def test_predictive_assistant_uses_prediction_service_structure():
    result = handle_query(session_with_demo(), "What is our predicted incident likelihood?")
    assert classify("Is our cyber risk increasing?") == "predictive_risk"
    assert result["intent"] == "predictive_risk"
    assert result["data"]["predictive_risk"]["available"] is True
    assert result["calculation"]
    assert result["recommendation"]


def test_empty_dataset_keeps_model_unavailable():
    engine = create_engine("sqlite://")
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    result = prediction_payload(session)
    assert result["available"] is False
    assert result["unavailable_reason"] == "insufficient_rows"
