from dataclasses import dataclass
import os

def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url[len("postgresql://"):]
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url[len("postgres://"):]
    return database_url

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sentinelledger.db")
    environment: str = os.getenv("ENVIRONMENT", "development")
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-before-production")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    run_db_init: bool = os.getenv("RUN_DB_INIT", "false").lower() in {"1", "true", "yes", "on"}
    seed_demo_data: bool = os.getenv("SEED_DEMO_DATA", "false").lower() in {"1", "true", "yes", "on"}

    def __post_init__(self) -> None:
        object.__setattr__(self, "database_url", normalize_database_url(self.database_url))
        if self.environment.lower() in {"production", "prod"} and (
            self.jwt_secret == "development-only-change-before-production" or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET must be at least 32 characters in production")

settings = Settings()
