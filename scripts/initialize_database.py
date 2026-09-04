"""Manually initialize a configured SentinelLedger database once.

Run this script from the repository root with DATABASE_URL set to the target
database, for example a PostgreSQL connection string. It always runs migrations.
Set SEED_DEMO_DATA=true to seed deterministic demo records and recalculate
persisted risk projections. Vercel startup does not invoke this script.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set before initializing the database")

    sys.path.insert(0, str(BACKEND_ROOT))

    from alembic import command
    from alembic.config import Config
    from app.core.config import normalize_database_url
    from app.db import SessionLocal
    from app.services.demo_seed import seed_demo
    from app.services.risk_persistence import recalculate_risk_assessments

    alembic_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_config.set_main_option("sqlalchemy.url", normalize_database_url(database_url))
    command.upgrade(alembic_config, "head")

    if os.getenv("SEED_DEMO_DATA", "false").lower() in {"1", "true", "yes", "on"}:
        session = SessionLocal()
        try:
            seed_demo(session)
            recalculate_risk_assessments(session)
        finally:
            session.close()

    print("Database initialization completed.")


if __name__ == "__main__":
    main()
