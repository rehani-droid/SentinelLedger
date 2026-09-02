from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sentinelledger.db")
    environment: str = os.getenv("ENVIRONMENT", "development")
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-before-production")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

settings = Settings()
