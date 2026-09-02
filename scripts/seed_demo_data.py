"""Create reproducible synthetic demo telemetry without exposing real enterprise data."""
from __future__ import annotations
import json
from pathlib import Path
from random import Random

SEED = 26105
ASSET_TYPES = ["database", "web_server", "api", "workstation", "cloud_workload", "identity_server", "payment_system", "email_server", "backup_server"]

def main() -> None:
    rng = Random(SEED)
    assets = [{"id": index + 1, "name": f"Demo-{kind.replace('_', '-').title()}-{index + 1:03}", "type": kind,
               "criticality": round(rng.uniform(.25, .98), 2), "internet_exposed": rng.choice([True, False])}
              for index, kind in ((i, ASSET_TYPES[i % len(ASSET_TYPES)]) for i in range(100))]
    output = Path("data/generated")
    output.mkdir(parents=True, exist_ok=True)
    (output / "assets.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
    print(f"Generated {len(assets)} deterministic synthetic assets in {output}")

if __name__ == "__main__":
    main()
