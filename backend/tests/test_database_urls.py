from app.core.config import Settings, normalize_database_url


def test_sqlite_url_is_preserved() -> None:
    url = "sqlite:///./sentinelledger.db"
    assert normalize_database_url(url) == url
    assert Settings(database_url=url).database_url == url


def test_postgresql_url_uses_psycopg3_dialect() -> None:
    url = "postgresql://user:password@localhost:5432/database"
    expected = "postgresql+psycopg://user:password@localhost:5432/database"
    assert normalize_database_url(url) == expected
    assert Settings(database_url=url).database_url == expected


def test_postgres_alias_uses_psycopg3_dialect() -> None:
    url = "postgres://user:password@localhost:5432/database"
    assert normalize_database_url(url) == "postgresql+psycopg://user:password@localhost:5432/database"


def test_postgresql_psycopg_url_is_preserved() -> None:
    url = "postgresql+psycopg://user:password@localhost:5432/database"
    assert normalize_database_url(url) == url
    assert Settings(database_url=url).database_url == url
