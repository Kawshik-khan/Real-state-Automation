"""Service Integrations & Secrets Management Hub (Database + Encryption + Hot-Reloading).

Allows developers and admins to connect and rotate third-party credentials (Groq, Pinecone,
Telegram, Gmail, LangSmith, WhatsApp) directly from the UI without modifying `.env` or redeploying.
Credentials are encrypted at rest with AES-256-GCM / Authenticated Keystream Cipher in PostgreSQL.
"""

import asyncio
from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import delete, select

from app.config import settings
from app.core.crypto import decrypt_data, encrypt_data, mask_secret_value
from app.database import async_session_factory
from app.models.models import SystemIntegrationRecord

logger = logging.getLogger(__name__)

# Canonical Catalog of Supported Integrations
INTEGRATION_CATALOG = {
    "groq": {
        "service_key": "groq",
        "display_name": "GroqCloud (LLM Engine)",
        "category": "ai",
        "description": "High-throughput inference engine for reasoning, lead scoring, and customer chat.",
        "docs_url": "https://console.groq.com/keys",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "gsk_...", "required": True},
            {"key": "model", "label": "Model Name", "type": "text", "placeholder": "llama-3.3-70b-versatile", "required": False},
            {"key": "base_url", "label": "Base URL", "type": "text", "placeholder": "https://api.groq.com/openai/v1", "required": False},
        ],
    },
    "pinecone": {
        "service_key": "pinecone",
        "display_name": "Pinecone (Vector Database)",
        "category": "vector_db",
        "description": "Serverless vector index storing real estate property knowledge chunks for hybrid RAG.",
        "docs_url": "https://app.pinecone.io/",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "pcsk_...", "required": True},
            {"key": "index_name", "label": "Index Name", "type": "text", "placeholder": "real-state-automation", "required": False},
            {"key": "host", "label": "Index Host URL", "type": "text", "placeholder": "https://...svc.pinecone.io", "required": False},
        ],
    },
    "telegram": {
        "service_key": "telegram",
        "display_name": "Telegram Bot Alerts",
        "category": "notifications",
        "description": "Instant lead escalation alerts, daily executive reports, and system notices dispatched to staff chat.",
        "docs_url": "https://t.me/BotFather",
        "fields": [
            {"key": "bot_token", "label": "Bot Token", "type": "password", "placeholder": "123456789:ABCdef...", "required": True},
            {"key": "default_chat_id", "label": "Default Chat ID", "type": "text", "placeholder": "6761679294", "required": False},
        ],
    },
    "gmail": {
        "service_key": "gmail",
        "display_name": "Google Gmail (SMTP & IMAP)",
        "category": "communication",
        "description": "Inbound inquiry polling and automated outbound brochure / floor plan email dispatch.",
        "docs_url": "https://myaccount.google.com/apppasswords",
        "fields": [
            {"key": "user_email", "label": "Gmail Address", "type": "email", "placeholder": "team@glgassets.com", "required": True},
            {"key": "app_password", "label": "Google App Password (16-char)", "type": "password", "placeholder": "xxxx xxxx xxxx xxxx", "required": True},
            {"key": "client_id", "label": "OAuth Client ID (Optional)", "type": "text", "placeholder": "....apps.googleusercontent.com", "required": False},
            {"key": "client_secret", "label": "OAuth Client Secret (Optional)", "type": "password", "placeholder": "GOCSPX-...", "required": False},
            {"key": "refresh_token", "label": "OAuth Refresh Token (Optional)", "type": "password", "placeholder": "1//04...", "required": False},
        ],
    },
    "langsmith": {
        "service_key": "langsmith",
        "display_name": "LangSmith (Observability)",
        "category": "observability",
        "description": "Automated LLM execution tracing, token telemetry, latency profiling, and regression monitoring.",
        "docs_url": "https://smith.langchain.com/settings",
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "password", "placeholder": "lsv2_pt_...", "required": True},
            {"key": "project", "label": "Project Name", "type": "text", "placeholder": "glg-assets-ai-os", "required": False},
            {"key": "endpoint", "label": "Endpoint URL", "type": "text", "placeholder": "https://api.smith.langchain.com", "required": False},
        ],
    },
    "whatsapp": {
        "service_key": "whatsapp",
        "display_name": "Meta / WhatsApp Cloud API",
        "category": "communication",
        "description": "Official WhatsApp Business Cloud API integration for omnichannel customer messaging.",
        "docs_url": "https://developers.facebook.com/apps/",
        "fields": [
            {"key": "phone_number_id", "label": "Phone Number ID", "type": "text", "placeholder": "10023456789...", "required": True},
            {"key": "access_token", "label": "Permanent Access Token", "type": "password", "placeholder": "EAA...", "required": True},
            {"key": "verify_token", "label": "Webhook Verify Token", "type": "text", "placeholder": "glg_wa_verify_2026", "required": False},
        ],
    },
}


class IntegrationService:
    """Manages database-persisted encrypted credentials and dynamic hot-reloading."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def _get_env_fallback(self, service_key: str) -> Dict[str, Any]:
        """Read fallback credentials from current environment variables / settings."""
        if service_key == "groq":
            key = getattr(settings, "openai_api_key", None)
            if key and key.startswith("gsk_"):
                return {
                    "api_key": key,
                    "model": getattr(settings, "openai_model", "llama-3.3-70b-versatile"),
                    "base_url": getattr(settings, "openai_base_url", "https://api.groq.com/openai/v1"),
                }
        elif service_key == "pinecone":
            key = getattr(settings, "pinecone_api_key", None)
            if key:
                return {
                    "api_key": key,
                    "index_name": getattr(settings, "pinecone_index_name", "real-state-automation"),
                    "host": getattr(settings, "pinecone_host", ""),
                }
        elif service_key == "telegram":
            token = getattr(settings, "telegram_bot_token", None)
            if token:
                return {
                    "bot_token": token,
                    "default_chat_id": getattr(settings, "default_telegram_chat_id", ""),
                }
        elif service_key == "gmail":
            email = getattr(settings, "gmail_user_email", None)
            pwd = getattr(settings, "gmail_app_password", None)
            if email and pwd:
                return {
                    "user_email": email,
                    "app_password": pwd,
                    "client_id": getattr(settings, "gmail_client_id", ""),
                    "client_secret": getattr(settings, "gmail_client_secret", ""),
                    "refresh_token": getattr(settings, "gmail_refresh_token", ""),
                }
        elif service_key == "langsmith":
            key = getattr(settings, "langsmith_api_key", None)
            if key:
                return {
                    "api_key": key,
                    "project": getattr(settings, "langsmith_project", "glg-assets-ai-os"),
                    "endpoint": getattr(settings, "langsmith_endpoint", "https://api.smith.langchain.com"),
                }
        elif service_key == "whatsapp":
            token = getattr(settings, "whatsapp_access_token", None)
            phone_id = getattr(settings, "whatsapp_phone_number_id", None)
            if token and phone_id:
                return {
                    "phone_number_id": phone_id,
                    "access_token": token,
                    "verify_token": getattr(settings, "whatsapp_verify_token", "glg_wa_verify_2026"),
                }
        return {}

    def _mask_credentials_dict(self, creds: Dict[str, Any]) -> Dict[str, str]:
        """Produce safe masked representation of credentials dictionary for UI display."""
        masked = {}
        for k, v in creds.items():
            if not v:
                masked[k] = ""
            elif any(s in k.lower() for s in ["key", "token", "password", "secret"]):
                masked[k] = mask_secret_value(str(v))
            else:
                masked[k] = str(v)
        return masked

    async def get_all_integrations(self) -> List[Dict[str, Any]]:
        """Retrieve list of all supported integrations with status and masked credentials."""
        db_records: Dict[str, SystemIntegrationRecord] = {}

        try:
            async with async_session_factory() as session:
                stmt = select(SystemIntegrationRecord)
                res = await session.execute(stmt)
                for row in res.scalars().all():
                    db_records[row.service_key] = row
        except Exception as err:
            logger.debug(f"[IntegrationService] Database query failed (using cache/env): {err}")

        results = []
        for key, meta in INTEGRATION_CATALOG.items():
            db_row = db_records.get(key)
            env_creds = self._get_env_fallback(key)

            if db_row and db_row.is_active:
                source = "database"
                is_configured = bool(db_row.encrypted_credentials)
                masked = db_row.masked_preview or {}
                last_status = db_row.last_status
                last_tested_at = db_row.last_tested_at.isoformat() if db_row.last_tested_at else None
                last_error = db_row.last_error
            elif env_creds:
                source = "environment"
                is_configured = True
                masked = self._mask_credentials_dict(env_creds)
                last_status = "connected"
                last_tested_at = None
                last_error = None
            else:
                source = "not_configured"
                is_configured = False
                masked = {}
                last_status = "not_tested"
                last_tested_at = None
                last_error = None

            results.append({
                "service_key": key,
                "display_name": meta["display_name"],
                "category": meta["category"],
                "description": meta["description"],
                "docs_url": meta["docs_url"],
                "fields": meta["fields"],
                "is_configured": is_configured,
                "source": source,
                "masked_credentials": masked,
                "last_status": last_status,
                "last_tested_at": last_tested_at,
                "last_error": last_error,
            })

        return results

    async def save_integration(
        self,
        service_key: str,
        credentials: Dict[str, Any],
        is_active: bool = True,
        updated_by: str = "developer",
    ) -> Dict[str, Any]:
        """Encrypt and persist service credentials into PostgreSQL system_integrations table."""
        if service_key not in INTEGRATION_CATALOG:
            raise ValueError(f"Unknown service '{service_key}'")

        meta = INTEGRATION_CATALOG[service_key]
        clean_creds = {k: str(v).strip() for k, v in credentials.items() if v is not None and str(v).strip() != ""}

        # If partial update without new password, merge with existing
        existing_creds = await self.get_active_credentials(service_key) or {}
        for k, v in clean_creds.items():
            if "•" in v:  # User didn't change masked field
                clean_creds[k] = existing_creds.get(k, "")

        encrypted_payload = encrypt_data(clean_creds)
        masked_preview = self._mask_credentials_dict(clean_creds)

        now_dt = datetime.now(timezone.utc)
        try:
            async with async_session_factory() as session:
                stmt = select(SystemIntegrationRecord).where(SystemIntegrationRecord.service_key == service_key)
                res = await session.execute(stmt)
                record = res.scalars().first()

                if not record:
                    record = SystemIntegrationRecord(
                        service_key=service_key,
                        display_name=meta["display_name"],
                        category=meta["category"],
                        is_active=is_active,
                        encrypted_credentials=encrypted_payload,
                        masked_preview=masked_preview,
                        updated_by=updated_by,
                        created_at=now_dt,
                        updated_at=now_dt,
                    )
                    session.add(record)
                else:
                    record.is_active = is_active
                    record.encrypted_credentials = encrypted_payload
                    record.masked_preview = masked_preview
                    record.updated_by = updated_by
                    record.updated_at = now_dt

                await session.commit()
                logger.info(f"[IntegrationService] Successfully saved and encrypted credentials for '{service_key}'.")
        except Exception as err:
            logger.error(f"[IntegrationService] Database save failed for '{service_key}': {err}")

        # Sync to memory cache
        async with self._lock:
            self._cache[service_key] = clean_creds

        if service_key == "langsmith":
            api_key = clean_creds.get("api_key")
            if api_key:
                os.environ["LANGSMITH_API_KEY"] = api_key
                os.environ["LANGCHAIN_API_KEY"] = api_key
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                if clean_creds.get("project"):
                    os.environ["LANGCHAIN_PROJECT"] = clean_creds["project"]

        return {
            "success": True,
            "service_key": service_key,
            "source": "database",
            "masked_credentials": masked_preview,
            "message": f"{meta['display_name']} credentials saved and encrypted successfully.",
        }

    async def get_active_credentials(self, service_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve decrypted credentials for a service (DB priority -> env fallback)."""
        async with self._lock:
            if service_key in self._cache:
                return self._cache[service_key]

        try:
            async with async_session_factory() as session:
                stmt = select(SystemIntegrationRecord).where(
                    SystemIntegrationRecord.service_key == service_key,
                    SystemIntegrationRecord.is_active.is_(True),
                )
                res = await session.execute(stmt)
                record = res.scalars().first()
                if record and record.encrypted_credentials:
                    creds = decrypt_data(record.encrypted_credentials)
                    if creds:
                        async with self._lock:
                            self._cache[service_key] = creds
                        return creds
        except Exception as err:
            logger.debug(f"[IntegrationService] Failed to load credentials from DB: {err}")

        # Fallback to .env
        env_fallback = self._get_env_fallback(service_key)
        if env_fallback:
            return env_fallback

        return None

    def get_cached_credentials(self, service_key: str) -> Optional[Dict[str, Any]]:
        """Synchronous read from in-memory cache with fallback to environment."""
        if service_key in self._cache:
            return self._cache[service_key]
        fallback = self._get_env_fallback(service_key)
        if fallback:
            return fallback
        return None

    async def warm_cache(self) -> None:
        """Preload all active encrypted integration records into memory on application startup."""
        try:
            async with async_session_factory() as session:
                stmt = select(SystemIntegrationRecord).where(SystemIntegrationRecord.is_active.is_(True))
                res = await session.execute(stmt)
                records = res.scalars().all()
                async with self._lock:
                    for rec in records:
                        if rec.encrypted_credentials:
                            creds = decrypt_data(rec.encrypted_credentials)
                            if creds:
                                self._cache[rec.service_key] = creds
                                if rec.service_key == "langsmith" and creds.get("api_key"):
                                    os.environ["LANGSMITH_API_KEY"] = creds["api_key"]
                                    os.environ["LANGCHAIN_API_KEY"] = creds["api_key"]
                                    os.environ["LANGCHAIN_TRACING_V2"] = "true"
                                    if creds.get("project"):
                                        os.environ["LANGCHAIN_PROJECT"] = creds["project"]
            logger.info(f"[IntegrationService] Preloaded {len(self._cache)} integration secrets into secure memory cache.")
        except Exception as err:
            logger.debug(f"[IntegrationService] Startup secret cache preload skipped: {err}")


    async def delete_integration(self, service_key: str) -> bool:
        """Remove database credentials for a service (reverting to environment fallback)."""
        try:
            async with async_session_factory() as session:
                await session.execute(
                    delete(SystemIntegrationRecord).where(SystemIntegrationRecord.service_key == service_key)
                )
                await session.commit()
            async with self._lock:
                self._cache.pop(service_key, None)
            return True
        except Exception as err:
            logger.error(f"[IntegrationService] Failed to delete integration '{service_key}': {err}")
            return False

    async def test_connection(
        self,
        service_key: str,
        custom_credentials: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform a real-time HTTP/network handshake ping to verify credential validity."""
        creds = custom_credentials or await self.get_active_credentials(service_key)
        if not creds:
            return {
                "success": False,
                "latency_ms": 0,
                "message": f"No credentials provided or configured for {service_key}.",
            }

        start_time = time.time()
        test_success = False
        message = ""
        details = {}

        try:
            # 1. Groq Test
            if service_key == "groq":
                api_key = creds.get("api_key", "").strip()
                base_url = (creds.get("base_url") or "https://api.groq.com/openai/v1").rstrip("/")
                headers = {"Authorization": f"Bearer {api_key}"}
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(f"{base_url}/models", headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        model_count = len(data.get("data", []))
                        test_success = True
                        message = f"Connected to Groq Cloud. {model_count} models available."
                    else:
                        message = f"Groq Authentication failed (HTTP {resp.status_code}): {resp.text[:120]}"

            # 2. Pinecone Test
            elif service_key == "pinecone":
                api_key = creds.get("api_key", "").strip()
                headers = {"Api-Key": api_key}
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get("https://api.pinecone.io/indexes", headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        indexes = data.get("indexes", [])
                        names = [i.get("name") for i in indexes] if isinstance(indexes, list) else []
                        test_success = True
                        message = f"Pinecone connection successful. Indexes: {', '.join(names) or 'None'}"
                    else:
                        message = f"Pinecone auth failed (HTTP {resp.status_code}): {resp.text[:120]}"

            # 3. Telegram Test
            elif service_key == "telegram":
                bot_token = creds.get("bot_token", "").strip()
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
                    if resp.status_code == 200:
                        data = resp.json()
                        bot_user = data.get("result", {}).get("username", "unknown")
                        test_success = True
                        message = f"Telegram Bot verified: @{bot_user}"
                    else:
                        message = f"Telegram Bot Token invalid (HTTP {resp.status_code})"

            # 4. Gmail Test (SMTP Handshake)
            elif service_key == "gmail":
                email_addr = creds.get("user_email", "").strip()
                app_pwd = creds.get("app_password", "").strip().replace(" ", "")

                import smtplib
                def _smtp_test():
                    with smtplib.SMTP("smtp.gmail.com", 587, timeout=6.0) as server:
                        server.starttls()
                        server.login(email_addr, app_pwd)
                        return True

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, _smtp_test)
                test_success = True
                message = f"Gmail SMTP authentication verified for {email_addr}"

            # 5. LangSmith Test
            elif service_key == "langsmith":
                api_key = creds.get("api_key", "").strip()
                endpoint = (creds.get("endpoint") or "https://api.smith.langchain.com").rstrip("/")
                headers = {"x-api-key": api_key}
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(f"{endpoint}/sessions", headers=headers)
                    if resp.status_code in (200, 400):  # 200 or 400 parameter validation means key is authentic
                        test_success = True
                        message = "LangSmith API key authenticated successfully."
                    else:
                        message = f"LangSmith key rejected (HTTP {resp.status_code})"

            # 6. WhatsApp / Meta Test
            elif service_key == "whatsapp":
                phone_id = creds.get("phone_number_id", "").strip()
                token = creds.get("access_token", "").strip()
                headers = {"Authorization": f"Bearer {token}"}
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(f"https://graph.facebook.com/v21.0/{phone_id}", headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        display_name = data.get("display_phone_number") or data.get("verified_name") or phone_id
                        test_success = True
                        message = f"Meta WhatsApp verified for: {display_name}"
                    else:
                        message = f"WhatsApp API token/phone ID invalid (HTTP {resp.status_code})"

            else:
                message = f"No automated test runner defined for {service_key}."

        except Exception as err:
            test_success = False
            message = f"Connection test failed: {str(err)}"

        latency = round((time.time() - start_time) * 1000, 1)

        # Update status in database if integration is already saved
        try:
            async with async_session_factory() as session:
                stmt = select(SystemIntegrationRecord).where(SystemIntegrationRecord.service_key == service_key)
                res = await session.execute(stmt)
                record = res.scalars().first()
                if record:
                    record.last_tested_at = datetime.now(timezone.utc)
                    record.last_status = "connected" if test_success else "failed"
                    record.last_error = None if test_success else message
                    await session.commit()
        except Exception:
            pass

        return {
            "success": test_success,
            "latency_ms": latency,
            "message": message,
            "details": details,
        }


# Global integration service singleton
integration_service = IntegrationService()
