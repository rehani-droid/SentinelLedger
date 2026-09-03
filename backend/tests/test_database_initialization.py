from types import SimpleNamespace
from unittest.mock import patch

from app import main
from app.core.config import Settings


def test_run_db_init_defaults_to_false() -> None:
    assert Settings(run_db_init=False).run_db_init is False


def test_initialise_database_skips_when_disabled() -> None:
    with patch.object(main, "settings", SimpleNamespace(run_db_init=False)):
        with patch("alembic.command.upgrade") as upgrade:
            main.initialise_database()

    upgrade.assert_not_called()


def test_initialise_database_runs_migrations_when_enabled() -> None:
    settings = SimpleNamespace(
        run_db_init=True,
        database_url="sqlite:///./sentinelledger.db",
        seed_demo_data=False,
    )
    with patch.object(main, "settings", settings):
        with patch("alembic.command.upgrade") as upgrade:
            main.initialise_database()

    upgrade.assert_called_once()
