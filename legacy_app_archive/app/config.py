from dataclasses import dataclass
import os


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI Real Estate Customer Engagement Platform")
    environment: str = os.getenv("APP_ENV", "test")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./real_estate.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    enable_persistence: bool = _as_bool(os.getenv("ENABLE_PERSISTENCE"), False)
    
    # n8n Integration Settings
    n8n_webhook_url: str = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/platform-events")
    n8n_api_url: str = os.getenv("N8N_API_URL", "http://localhost:5678/api/v1")
    n8n_api_key: str = os.getenv("N8N_API_KEY", "")
    n8n_webhook_secret: str = os.getenv("N8N_WEBHOOK_SECRET", "change-me-in-production")
    n8n_timeout: int = int(os.getenv("N8N_TIMEOUT", "30"))
    enable_n8n: bool = _as_bool(os.getenv("ENABLE_N8N"), False)


settings = Settings()