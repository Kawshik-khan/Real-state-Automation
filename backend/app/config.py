from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    app_name: str = "GLG Assets Automation API"
    debug: bool = False

    # Database & Supabase pgvector
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/glg_assets"
    
    # Supabase Specific Settings (Optional)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # Supabase Storage Buckets
    supabase_bucket_brochures: str = "brochures"
    supabase_bucket_floorplans: str = "floorplans"
    supabase_bucket_ocr: str = "ocr-documents"

    # Redis / Distributed Cache
    redis_url: Optional[str] = None

    # Security — REQUIRED: Must be provided via .env or environment variables.
    # The application will refuse to start if these are missing, preventing
    # accidental deployment with known/default credentials.
    automation_shared_secret: str
    jwt_secret: str
    password_hash_salt: str
    api_key: Optional[str] = None
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS — comma-separated allowed origins (no wildcard with credentials)
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # Defaults
    default_tenant_id: str = "glg-assets-main"

    # OpenAI / LLM
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_base_url: Optional[str] = None

    # Multimodal: Audio Transcription & Vision
    whisper_model: str = "whisper-large-v3"
    vision_model: str = "llama-3.2-11b-vision-preview"

    # LangSmith Observability & Tracing
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "glg-assets-ai-os"

    # Knowledge Base & Vector Store
    knowledge_base_dir: str = "data/knowledge"
    vector_dim: int = 1024
    vector_store_provider: str = "auto"  # "auto", "pinecone", "pgvector"
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "real-state-automation"
    pinecone_host: Optional[str] = None

    # Notification defaults & Tokens
    default_email_recipient: str = "team@glgassets.com"
    n8n_email_webhook_url: Optional[str] = "https://glg-ai.app.n8n.cloud/webhook/glg-email-webhook"
    n8n_api_url: str = "https://glg-ai.app.n8n.cloud/api/v1"
    n8n_webhook_base_url: Optional[str] = "https://glg-ai.app.n8n.cloud"
    n8n_api_key: Optional[str] = None
    default_slack_channel: str = "#leads"
    default_telegram_chat_id: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None

    # Meta / Facebook / Instagram Graph API Settings
    facebook_page_id: Optional[str] = None
    facebook_page_access_token: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    instagram_account_id: Optional[str] = None
    meta_graph_api_version: str = "v19.0"
    social_auto_dm_enabled: bool = True

    # Gmail SMTP / IMAP Settings
    gmail_user_email: Optional[str] = None
    gmail_app_password: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        """Ensure database_url has explicit async driver (postgresql+asyncpg://) for SQLAlchemy async engine."""
        url = (self.database_url or "").strip()
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://"):]
        if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            return "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    @property
    def allowed_origins(self) -> list[str]:
        """Parse CORS_ORIGINS into a list. Prevents raw wildcard '*' with allow_credentials=True."""
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=(_ENV_PATH, "backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
