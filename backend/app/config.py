from pydantic_settings import BaseSettings
from typing import Optional


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

    # Security
    automation_shared_secret: str = "change-me-in-production"
    api_key: Optional[str] = None

    # CORS — comma-separated origins; "*" for development
    cors_origins: str = "*"

    # Defaults
    default_tenant_id: str = "glg-assets-main"

    # OpenAI / LLM
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_base_url: Optional[str] = None

    # Knowledge Base & Vector Store
    knowledge_base_dir: str = "data/knowledge"
    vector_dim: int = 1024
    vector_store_provider: str = "auto"  # "auto", "pinecone", "pgvector"
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "real-state-automation"
    pinecone_host: Optional[str] = "https://real-state-automation-o25ptb6.svc.aped-4627-b74a.pinecone.io"

    # Notification defaults & Tokens
    default_email_recipient: str = "team@glgassets.com"
    n8n_email_webhook_url: Optional[str] = "http://localhost:5678/webhook/email-send"
    n8n_api_url: str = "http://localhost:5678/api/v1"
    n8n_api_key: Optional[str] = None
    default_slack_channel: str = "#leads"
    default_telegram_chat_id: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None

    @property
    def allowed_origins(self) -> list[str]:
        """Parse CORS_ORIGINS into a list; handles '*' for development."""
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ("backend/.env", ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
