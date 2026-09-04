import pytest

from app.core.config import Settings


def test_production_rejects_demo_seeding():
    with pytest.raises(ValueError, match="SEED_DEMO_DATA"):
        Settings(
            database_url="sqlite:///./sentinelledger.db",
            environment="production",
            jwt_secret="x" * 32,
            cors_origins="https://example.test",
            seed_demo_data=True,
        )


def test_cors_origins_are_trimmed_and_wildcards_rejected():
    settings = Settings(cors_origins=" http://localhost:5173, https://example.test ")
    assert settings.cors_origins == "http://localhost:5173,https://example.test"
    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        Settings(cors_origins="*")
