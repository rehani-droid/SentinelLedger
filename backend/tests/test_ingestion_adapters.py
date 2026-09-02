import pytest
from app.ingestion.adapters import SourceType, normalize_csv, normalize_json


def _event(event_id: str = "evt-1") -> dict:
    return {"source_id": "demo-siem", "source_event_id": event_id,
            "observed_at": "2026-01-01T12:00:00+00:00", "payload": {"severity": "high"}}


def test_json_normalises_every_required_source_type() -> None:
    for source in SourceType:
        event = normalize_json(source, [_event()])[0]
        assert event.source_type is source
        assert len(event.payload_fingerprint()) == 64


def test_csv_normalises_valid_events() -> None:
    content = 'source_id,source_event_id,observed_at,payload\ndemo-edr,edr-1,2026-01-01T12:00:00+00:00,"{\"\"severity\"\": \"\"high\"\"}"\n'
    events = normalize_csv(SourceType.edr, content)
    assert events[0].source_event_id == "edr-1"


@pytest.mark.parametrize("content", ["source_id,payload\na,{}\n", "source_id,source_event_id,observed_at,payload\na,b,2026-01-01T00:00:00+00:00,not-json\n"])
def test_csv_rejects_malformed_input(content: str) -> None:
    with pytest.raises(ValueError):
        normalize_csv(SourceType.siem, content)


def test_json_rejects_naive_timestamp() -> None:
    event = _event(); event["observed_at"] = "2026-01-01T12:00:00"
    with pytest.raises(Exception):
        normalize_json(SourceType.siem, [event])
