from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sentinelledger.db")
    environment: str = os.getenv("ENVIRONMENT", "development")
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-before-production")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")

    def __post_init__(self) -> None:
        if self.environment.lower() in {"production", "prod"} and (
            self.jwt_secret == "development-only-change-before-production" or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET must be at least 32 characters in production")

settings = Settings()
