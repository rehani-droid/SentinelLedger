"""Hash-chained immutable event representation for assessment evidence."""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

GENESIS_HASH = "0" * 64

def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

def digest(payload: dict, previous_hash: str) -> str:
    return hashlib.sha256(f"{canonical_json(payload)}:{previous_hash}".encode()).hexdigest()

@dataclass(frozen=True)
class LedgerEvent:
    sequence: int
    payload: dict
    previous_hash: str
    event_hash: str
    timestamp: str

class AuditLedger:
    """In-memory adapter; persistence is supplied by the database repository layer."""
    def __init__(self) -> None:
        self.events: list[LedgerEvent] = []

    def append(self, payload: dict) -> LedgerEvent:
        previous_hash = self.events[-1].event_hash if self.events else GENESIS_HASH
        event = LedgerEvent(len(self.events) + 1, payload, previous_hash, digest(payload, previous_hash),
                            datetime.now(timezone.utc).isoformat())
        self.events.append(event)
        return event

    def verify(self, sequence: int) -> bool:
        if not 1 <= sequence <= len(self.events):
            return False
        event = self.events[sequence - 1]
        expected_previous = self.events[sequence - 2].event_hash if sequence > 1 else GENESIS_HASH
        return event.previous_hash == expected_previous and event.event_hash == digest(event.payload, event.previous_hash)


def verify_persisted_chain(events: list[object]) -> dict:
    """Verify every persisted event in order, including links after a tampered event.

    The repository deliberately passes lightweight objects with ``id``, ``payload``,
    ``previous_hash`` and ``event_hash`` attributes so this function stays independent
    of SQLAlchemy and is easy to test.
    """
    previous_hash = GENESIS_HASH
    for event in events:
        try:
            payload = json.loads(event.payload)
            hash_matches = event.event_hash == digest(payload, event.previous_hash)
            link_matches = event.previous_hash == previous_hash
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            hash_matches = link_matches = False
        if not (hash_matches and link_matches):
            return {
                "valid": False,
                "events_checked": event.id,
                "first_invalid_sequence": event.id,
                "reason": "payload_hash_mismatch" if not hash_matches else "previous_hash_mismatch",
            }
        previous_hash = event.event_hash
    return {"valid": True, "events_checked": len(events), "first_invalid_sequence": None, "reason": None}
