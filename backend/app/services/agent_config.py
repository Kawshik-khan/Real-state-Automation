"""Agent Configuration & Hyperparameter Service.

Handles persistence directly into PostgreSQL / Supabase (agent_configurations table),
with resilient fallback to local JSON cache and in-memory runtime hot-reloading.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select, text

from app.database import async_session_factory, is_db_reachable
from app.models.models import AgentConfigurationRecord
from app.prompts.email import EMAIL_AGENT_SYSTEM_PROMPT
from app.prompts.faq import FAQ_AGENT_PROMPT
from app.prompts.property import PROPERTY_AGENT_PROMPT
from app.prompts.registry import PROMPT_REGISTRY
from app.prompts.social import SOCIAL_BRIDGE_PROMPT

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
FALLBACK_CONFIG_FILE = DATA_DIR / "agent_configurations.json"

DEFAULT_SUPERVISOR_PROMPT = """You are the master supervisor & dialogue orchestrator for GLG Assets.
Your task is to classify user inquiries accurately into exact target agent domains:
- 'property': Inquiries about apartments, plots, commercial towers, bedrooms, bathrooms, locations (Gulshan, Banani, Baridhara), prices, and handover dates.
- 'faq': Inquiries regarding company policies, document requirements (NID, TIN), official contact details, helplines, developer credibility, and buying processes.
- 'lead': Explicit appointment booking, requesting a private viewing, agent callback, or providing phone/email contact details.
- 'escalation': Customer explicitly asks for human manager, expresses high frustration, legal disputes, or repeated misunderstandings.
- 'greeting': Initial pleasantries, 'Hi', 'Hello', 'Assalamu Alaikum', 'Kemon achen'.
- 'out_of_domain': Off-topic questions (e.g. crypto, recipes, general politics, unrelated tech).

Return strictly JSON with 'intent', 'confidence' (0.0 to 1.0), and extracted 'entities'."""

CANONICAL_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "property_agent": {
        "agent_key": "property_agent",
        "name": "Property Consultant Agent",
        "description": "Handles luxury residential & commercial inquiries, inventory filtering, floor plans, and pricing in Dhaka.",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "fallback_model": "llama-3.1-8b-instant",
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 1024,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "system_prompt": PROPERTY_AGENT_PROMPT,
        "rag_settings": {
            "hybrid_alpha": 0.65,
            "top_k": 5,
            "min_score": 0.65,
            "memory_depth": 5,
            "reconcile_contradictions": True,
        },
        "lora_adapter": "glg-bangla-realestate-lora-v1",
        "is_active": True,
        "persona_preset": "Consultative Luxury",
    },
    "faq_agent": {
        "agent_key": "faq_agent",
        "name": "FAQ & Customer Advisory Agent",
        "description": "Answers questions on buying policies, NID/TIN paperwork, payment schedules, and office directions.",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "fallback_model": "llama-3.1-8b-instant",
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 1024,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "system_prompt": FAQ_AGENT_PROMPT,
        "rag_settings": {
            "hybrid_alpha": 0.70,
            "top_k": 4,
            "min_score": 0.70,
            "memory_depth": 4,
            "reconcile_contradictions": True,
        },
        "lora_adapter": None,
        "is_active": True,
        "persona_preset": "Analytical Advisor",
    },
    "supervisor": {
        "agent_key": "supervisor",
        "name": "Supervisor Intent Orchestrator",
        "description": "Routes multi-lingual messages (Bangla/Banglish/EN) to target agents with confidence scoring.",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "fallback_model": "llama-3.1-8b-instant",
        "temperature": 0.1,
        "top_p": 0.85,
        "max_tokens": 512,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "system_prompt": DEFAULT_SUPERVISOR_PROMPT,
        "rag_settings": {
            "hybrid_alpha": 0.50,
            "top_k": 3,
            "min_score": 0.60,
            "memory_depth": 6,
            "reconcile_contradictions": True,
        },
        "lora_adapter": None,
        "is_active": True,
        "persona_preset": "Deterministic Router",
    },
    "email_agent": {
        "agent_key": "email_agent",
        "name": "Lead & Email Concierge Agent",
        "description": "Drafts formal real-estate proposals, executive tour confirmations, and investor follow-ups.",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "fallback_model": "llama-3.1-8b-instant",
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 1024,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "system_prompt": EMAIL_AGENT_SYSTEM_PROMPT,
        "rag_settings": {
            "hybrid_alpha": 0.60,
            "top_k": 4,
            "min_score": 0.65,
            "memory_depth": 3,
            "reconcile_contradictions": False,
        },
        "lora_adapter": "glg-executive-pitch-lora-v2",
        "is_active": True,
        "persona_preset": "Executive Closer",
    },
    "social_bridge": {
        "agent_key": "social_bridge",
        "name": "Social Media Omnichannel Bridge",
        "description": "Handles WhatsApp, Facebook Messenger, and Instagram Direct incoming lead responses.",
        "provider": "groq",
        "model": "llama-3.3-70b-versatile",
        "fallback_model": "llama-3.1-8b-instant",
        "temperature": 0.35,
        "top_p": 0.95,
        "max_tokens": 800,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.1,
        "system_prompt": SOCIAL_BRIDGE_PROMPT,
        "rag_settings": {
            "hybrid_alpha": 0.55,
            "top_k": 3,
            "min_score": 0.60,
            "memory_depth": 3,
            "reconcile_contradictions": True,
        },
        "lora_adapter": None,
        "is_active": True,
        "persona_preset": "Warm Conversational",
    },
}


class AgentConfigService:
    """Central service managing agent configurations, hyperparameters, and prompts."""

    def __init__(self):
        self._runtime_cache: Dict[str, Dict[str, Any]] = {}
        self._ensure_cache_loaded()

    def _ensure_cache_loaded(self):
        """Pre-populate in-memory cache with fallback or defaults."""
        if not self._runtime_cache:
            loaded = self._read_fallback_file()
            if loaded:
                self._runtime_cache = loaded
            else:
                self._runtime_cache = {k: dict(v) for k, v in CANONICAL_DEFAULTS.items()}
                self._write_fallback_file(self._runtime_cache)

    def _read_fallback_file(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """Read local fallback JSON configuration."""
        try:
            if FALLBACK_CONFIG_FILE.exists():
                with open(FALLBACK_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception as e:
            logger.warning(f"Could not read fallback agent config file: {e}")
        return None

    def _write_fallback_file(self, data: Dict[str, Any]):
        """Persist current config to local fallback JSON file."""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(FALLBACK_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to write fallback agent config: {e}")

    async def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all active agent configurations from PostgreSQL/Supabase, falling back to cache."""
        # 1. Attempt PostgreSQL fetch if database is reachable
        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    # Check if table exists
                    stmt = select(AgentConfigurationRecord)
                    res = await session.execute(stmt)
                    records = res.scalars().all()
                    if records:
                        db_configs = {}
                        for r in records:
                            db_configs[r.agent_key] = {
                                "id": r.id,
                                "agent_key": r.agent_key,
                                "name": r.name,
                                "description": r.description,
                                "provider": r.provider,
                                "model": r.model,
                                "fallback_model": r.fallback_model,
                                "temperature": r.temperature,
                                "top_p": r.top_p,
                                "max_tokens": r.max_tokens,
                                "presence_penalty": r.presence_penalty,
                                "frequency_penalty": r.frequency_penalty,
                                "system_prompt": r.system_prompt,
                                "rag_settings": r.rag_settings or {},
                                "lora_adapter": r.lora_adapter,
                                "is_active": r.is_active,
                                "tenant_id": r.tenant_id,
                                "created_at": r.created_at.isoformat() if r.created_at else None,
                                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                            }
                        # Merge with any missing canonical defaults
                        for k, v in CANONICAL_DEFAULTS.items():
                            if k not in db_configs:
                                db_configs[k] = dict(v)
                        self._runtime_cache = db_configs
                        self._write_fallback_file(db_configs)
                        return list(db_configs.values())
            except Exception as e:
                logger.warning(f"PostgreSQL agent config query failed, using cache: {e}")

        # Fallback to in-memory runtime cache
        self._ensure_cache_loaded()
        return list(self._runtime_cache.values())

    async def get(self, agent_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve single agent configuration by key."""
        all_configs = await self.get_all()
        for cfg in all_configs:
            if cfg.get("agent_key") == agent_key:
                return cfg
        return CANONICAL_DEFAULTS.get(agent_key)

    async def save(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update agent configuration in PostgreSQL/Supabase and update runtime cache."""
        agent_key = config_data.get("agent_key")
        if not agent_key:
            raise ValueError("agent_key is required")

        # Base default to ensure no missing keys
        merged = dict(CANONICAL_DEFAULTS.get(agent_key, {}))
        merged.update(config_data)
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()

        # 1. Update in-memory runtime and disk fallback
        self._runtime_cache[agent_key] = merged
        self._write_fallback_file(self._runtime_cache)

        # 2. Hot-reload into active runtime PROMPT_REGISTRY
        if "system_prompt" in merged:
            PROMPT_REGISTRY[agent_key] = merged["system_prompt"]
            if agent_key == "property_agent":
                PROMPT_REGISTRY["property"] = merged["system_prompt"]
            elif agent_key == "faq_agent":
                PROMPT_REGISTRY["faq"] = merged["system_prompt"]
            elif agent_key == "email_agent":
                PROMPT_REGISTRY["email"] = merged["system_prompt"]

        # 3. Persist directly to PostgreSQL/Supabase if reachable
        if is_db_reachable():
            try:
                async with async_session_factory() as session:
                    stmt = select(AgentConfigurationRecord).where(AgentConfigurationRecord.agent_key == agent_key)
                    res = await session.execute(stmt)
                    record = res.scalar_one_or_none()

                    if record:
                        record.name = merged.get("name", record.name)
                        record.description = merged.get("description", record.description)
                        record.provider = merged.get("provider", record.provider)
                        record.model = merged.get("model", record.model)
                        record.fallback_model = merged.get("fallback_model", record.fallback_model)
                        record.temperature = float(merged.get("temperature", record.temperature))
                        record.top_p = float(merged.get("top_p", record.top_p))
                        record.max_tokens = int(merged.get("max_tokens", record.max_tokens))
                        record.presence_penalty = float(merged.get("presence_penalty", record.presence_penalty))
                        record.frequency_penalty = float(merged.get("frequency_penalty", record.frequency_penalty))
                        record.system_prompt = merged.get("system_prompt", record.system_prompt)
                        record.rag_settings = merged.get("rag_settings", record.rag_settings)
                        record.lora_adapter = merged.get("lora_adapter", record.lora_adapter)
                        record.is_active = bool(merged.get("is_active", record.is_active))
                        record.updated_at = datetime.now(timezone.utc)
                    else:
                        new_record = AgentConfigurationRecord(
                            id=str(uuid4()),
                            agent_key=agent_key,
                            name=merged.get("name", agent_key.title()),
                            description=merged.get("description", ""),
                            provider=merged.get("provider", "groq"),
                            model=merged.get("model", "llama-3.3-70b-versatile"),
                            fallback_model=merged.get("fallback_model", "llama-3.1-8b-instant"),
                            temperature=float(merged.get("temperature", 0.2)),
                            top_p=float(merged.get("top_p", 0.9)),
                            max_tokens=int(merged.get("max_tokens", 1024)),
                            presence_penalty=float(merged.get("presence_penalty", 0.0)),
                            frequency_penalty=float(merged.get("frequency_penalty", 0.0)),
                            system_prompt=merged.get("system_prompt", ""),
                            rag_settings=merged.get("rag_settings", {}),
                            lora_adapter=merged.get("lora_adapter"),
                            is_active=bool(merged.get("is_active", True)),
                            tenant_id=merged.get("tenant_id", "glg-assets-main"),
                        )
                        session.add(new_record)
                    await session.commit()
                    logger.info(f"Successfully saved agent config for {agent_key} in PostgreSQL.")
            except Exception as e:
                logger.warning(f"Could not persist agent config to PostgreSQL (saved to local cache): {e}")

        return merged

    async def reset(self, agent_key: Optional[str] = None) -> Dict[str, Any]:
        """Reset agent config to canonical system defaults."""
        if agent_key and agent_key in CANONICAL_DEFAULTS:
            default_cfg = dict(CANONICAL_DEFAULTS[agent_key])
            return await self.save(default_cfg)
        elif not agent_key:
            for k, v in CANONICAL_DEFAULTS.items():
                await self.save(dict(v))
            return {"status": "success", "message": "All agents reset to defaults"}
        raise ValueError(f"Unknown agent_key {agent_key}")


agent_config_service = AgentConfigService()
