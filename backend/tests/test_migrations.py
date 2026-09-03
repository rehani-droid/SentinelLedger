from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_creates_persisted_risk_schema(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    inspector = inspect(create_engine(database_url))
    assert {"assets", "risk_assessments", "telemetry_entity_states", "optimization_runs", "alembic_version"}.issubset(inspector.get_table_names())
    columns = {column["name"] for column in inspector.get_columns("risk_assessments")}
    assert {"target_key", "scope", "risk_score", "financial_impact", "major_risk_drivers", "calculated_at"}.issubset(columns)
    option_columns = {column["name"] for column in inspector.get_columns("investment_options")}
    assert {"description", "affected_asset_ids", "affected_control_ids", "dependencies", "exclusions"}.issubset(option_columns)
