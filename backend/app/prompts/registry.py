"""Prompt Registry & Version Control for GLG Assets.

Audit Reference: prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md
Centralizes all production prompts, versions, and telemetry logging metadata.
"""
import logging
from typing import Any, Dict, Optional

from app.prompts.core import SYSTEM_CORE_POLICY
from app.prompts.email import EMAIL_AGENT_SYSTEM_PROMPT
from app.prompts.fallback import FALLBACK_PROMPT
from app.prompts.faq import FAQ_AGENT_PROMPT
from app.prompts.lean_core import (
    LEAN_EMAIL_PROMPT,
    LEAN_FAQ_PROMPT,
    LEAN_PROPERTY_PROMPT,
    LEAN_SYSTEM_CORE,
)
from app.prompts.property import PROPERTY_AGENT_PROMPT
from app.prompts.social import SOCIAL_BRIDGE_PROMPT, SOCIAL_CONTENT_PROMPT

logger = logging.getLogger(__name__)

PROMPT_VERSION = "2026.09.15-GOVERNANCE"

PROMPT_REGISTRY: Dict[str, str] = {
    "core": SYSTEM_CORE_POLICY,
    "property": PROPERTY_AGENT_PROMPT,
    "faq": FAQ_AGENT_PROMPT,
    "email": EMAIL_AGENT_SYSTEM_PROMPT,
    "social_content": SOCIAL_CONTENT_PROMPT,
    "social_bridge": SOCIAL_BRIDGE_PROMPT,
    "fallback": FALLBACK_PROMPT,
    # Lean Micro-Prompts (Pillar 2 Architecture)
    "lean_core": LEAN_SYSTEM_CORE,
    "lean_property": LEAN_PROPERTY_PROMPT,
    "lean_faq": LEAN_FAQ_PROMPT,
    "lean_email": LEAN_EMAIL_PROMPT,
}


def get_prompt(agent_name: str) -> str:
    """Retrieve versioned prompt for a specific agent."""
    if agent_name in PROMPT_REGISTRY:
        return PROMPT_REGISTRY[agent_name]
    logger.warning(f"Unknown prompt agent '{agent_name}'. Falling back to core policy.")
    return SYSTEM_CORE_POLICY


def log_prompt_telemetry(
    agent_name: str,
    model_name: str,
    temperature: float,
    language: str,
    retrieved_source_ids: Optional[list] = None,
    grounding_status: bool = True,
) -> Dict[str, Any]:
    """Generates structured logging payload for LLM prompt invocation audits."""
    telemetry = {
        "prompt_version": PROMPT_VERSION,
        "agent_name": agent_name,
        "model_name": model_name,
        "temperature": temperature,
        "language": language,
        "retrieved_source_ids": retrieved_source_ids or [],
        "grounding_status": "grounded" if grounding_status else "violation_detected",
    }
    logger.info(f"PROMPT_TELEMETRY: {telemetry}")
    return telemetry
