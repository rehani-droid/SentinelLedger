from types import SimpleNamespace
from app.audit.ledger import AuditLedger, GENESIS_HASH, canonical_json, digest, verify_persisted_chain

def test_ledger_detects_payload_tampering() -> None:
    ledger = AuditLedger()
    ledger.append({"assessment": "A", "eal": 12})
    assert ledger.verify(1)
    ledger.events[0].payload["eal"] = 13
    assert not ledger.verify(1)


def test_persisted_chain_detects_a_bad_link_after_valid_events() -> None:
    first = {"assessment": "A", "eal": 12}
    first_hash = digest(first, GENESIS_HASH)
    second = {"assessment": "B", "eal": 20}
    events = [
        SimpleNamespace(id=1, payload=canonical_json(first), previous_hash=GENESIS_HASH, event_hash=first_hash),
        SimpleNamespace(id=2, payload=canonical_json(second), previous_hash="f" * 64, event_hash=digest(second, "f" * 64)),
    ]
    assert verify_persisted_chain(events) == {"valid": False, "events_checked": 2, "first_invalid_sequence": 2, "reason": "previous_hash_mismatch"}


def test_persisted_chain_verifies_all_events() -> None:
    first = {"assessment": "A", "eal": 12}
    first_hash = digest(first, GENESIS_HASH)
    second = {"assessment": "B", "eal": 20}
    second_hash = digest(second, first_hash)
    events = [
        SimpleNamespace(id=1, payload=canonical_json(first), previous_hash=GENESIS_HASH, event_hash=first_hash),
        SimpleNamespace(id=2, payload=canonical_json(second), previous_hash=first_hash, event_hash=second_hash),
    ]
    assert verify_persisted_chain(events)["valid"] is True
