"""Resilient PostgreSQL Persistence Store for AI & Agent Control Plane.

Implements asynchronous read/write operations against Supabase / PostgreSQL tables
via SQLAlchemy 2.0 async sessions, with automatic schema population from canonical
Bangladesh real-estate domain seeds.
"""

import asyncio
import copy
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import func, or_, select, update

from app.database import async_session_factory, is_db_reachable
from app.models.ai_control_plane import (
    AIAgentRecord,
    AIAgentVersionRecord,
    AIApprovalRequestRecord,
    AIAuditLogRecord,
    AIBenchmarkRecord,
    AIBudgetRecord,
    AIDatasetExampleRecord,
    AIDatasetRecord,
    AIEvaluationRunRecord,
    AIExperimentRecord,
    AIFineTuneJobRecord,
    AIGuardrailEventRecord,
    AIGuardrailPolicyRecord,
    AIIncidentRecord,
    AIModelRecord,
    AIProviderRecord,
    AIReleaseRecord,
    AIRoutingRuleRecord,
    AIToolRecord,
    AITraceRecord,
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
STORE_FILE = DATA_DIR / "ai_control_plane_store.json"


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Canonical Seed Data (Bangladesh Real-Estate Enterprise Domain) ─

INITIAL_SEEDS: Dict[str, Any] = {
    "agents": [
        {
            "id": "agent-prop-001",
            "slug": "property_agent",
            "name": "Property Consultant Agent",
            "description": "Consultative real estate advisor specialized in Gulshan, Banani, and Baridhara luxury residences, verified unit layouts, and BDT pricing.",
            "role": "Property Advisor",
            "objective": "Guide high-net-worth investors through luxury floor plans, verified prices, and private site visits.",
            "owner": "sales-tech@glgassets.com",
            "status": "PRODUCTION",
            "environment": "production",
            "primary_model": "llama-3.3-70b-versatile",
            "fallback_model": "llama-3.1-8b-instant",
            "current_prompt_version": "v2.1",
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 1024,
            "persona_preset": "Consultative Luxury",
            "enabled_tools": ["property_search", "availability_check", "crm_lead_sync", "schedule_tour"],
            "rag_config": {
                "chunk_size": 512,
                "top_k": 5,
                "similarity_threshold": 0.68,
                "hybrid_alpha": 0.65,
                "grounding_enforced": True,
                "enabled_sources": ["property_db", "brochures", "pricing_matrix"]
            },
            "memory_config": {
                "scope": "CONVERSATION",
                "retention_ttl_hours": 168,
                "max_entries": 20,
                "relevance_threshold": 0.65
            },
            "guardrail_policy_ids": ["gr-fact-001", "gr-pii-001", "gr-inj-001"],
            "human_approval_policy": "HIGH_RISK_ONLY",
            "max_execution_steps": 6,
            "timeout_seconds": 30,
        },
        {
            "id": "agent-faq-002",
            "slug": "faq_agent",
            "name": "FAQ & Customer Advisory Agent",
            "description": "Official policy advisor addressing NID/TIN verification, installment schedules, legal disclosures, and developer credentials.",
            "role": "Policy Specialist",
            "objective": "Answer customer questions factually using approved company policies and financing partnerships.",
            "owner": "legal-compliance@glgassets.com",
            "status": "PRODUCTION",
            "environment": "production",
            "primary_model": "llama-3.3-70b-versatile",
            "fallback_model": "llama-3.1-8b-instant",
            "current_prompt_version": "v1.4",
            "temperature": 0.15,
            "top_p": 0.85,
            "max_tokens": 1024,
            "persona_preset": "Analytical Advisor",
            "enabled_tools": ["knowledge_search", "policy_lookup"],
            "rag_config": {
                "chunk_size": 512,
                "top_k": 4,
                "similarity_threshold": 0.70,
                "hybrid_alpha": 0.70,
                "grounding_enforced": True,
                "enabled_sources": ["faq_policies", "legal_disclosures"]
            },
            "memory_config": {
                "scope": "CONVERSATION",
                "retention_ttl_hours": 72,
                "max_entries": 10,
                "relevance_threshold": 0.70
            },
            "guardrail_policy_ids": ["gr-pii-001", "gr-inj-001"],
            "human_approval_policy": "NONE",
            "max_execution_steps": 4,
            "timeout_seconds": 25,
        },
        {
            "id": "agent-sup-003",
            "slug": "supervisor",
            "name": "Supervisor Intent Orchestrator",
            "description": "Deterministic classifier routing incoming multi-lingual inquiries (Bangla, Banglish, English) to the optimal domain agent with confidence telemetry.",
            "role": "Router & Orchestrator",
            "objective": "Detect user intent, extract location/budget entities, and dispatch to appropriate sub-agents.",
            "owner": "core-ai@glgassets.com",
            "status": "PRODUCTION",
            "environment": "production",
            "primary_model": "llama-3.3-70b-versatile",
            "fallback_model": "llama-3.1-8b-instant",
            "current_prompt_version": "v2.0",
            "temperature": 0.1,
            "top_p": 0.85,
            "max_tokens": 512,
            "persona_preset": "Deterministic Router",
            "enabled_tools": ["crm_lead_sync"],
            "rag_config": {
                "chunk_size": 256,
                "top_k": 3,
                "similarity_threshold": 0.60,
                "hybrid_alpha": 0.50,
                "grounding_enforced": False,
                "enabled_sources": ["faq_policies"]
            },
            "memory_config": {
                "scope": "SHORT_TERM",
                "retention_ttl_hours": 24,
                "max_entries": 6,
                "relevance_threshold": 0.60
            },
            "guardrail_policy_ids": ["gr-inj-001"],
            "human_approval_policy": "NONE",
            "max_execution_steps": 3,
            "timeout_seconds": 15,
        },
        {
            "id": "agent-email-004",
            "slug": "email_agent",
            "name": "Lead & Email Concierge Agent",
            "description": "Executive correspondent drafting formal proposals, VIP site visit itineraries, and structured payment plan breakdowns for investors.",
            "role": "Executive Concierge",
            "objective": "Compose polished investor communications and confirm scheduled appointments.",
            "owner": "investor-relations@glgassets.com",
            "status": "PRODUCTION",
            "environment": "production",
            "primary_model": "llama-3.3-70b-versatile",
            "fallback_model": "llama-3.1-8b-instant",
            "current_prompt_version": "v1.2",
            "temperature": 0.3,
            "top_p": 0.9,
            "max_tokens": 1200,
            "persona_preset": "High-Urgency Closer",
            "enabled_tools": ["email_dispatch", "schedule_tour", "crm_lead_sync"],
            "rag_config": {
                "chunk_size": 512,
                "top_k": 4,
                "similarity_threshold": 0.65,
                "hybrid_alpha": 0.60,
                "grounding_enforced": True,
                "enabled_sources": ["property_db", "pricing_matrix"]
            },
            "memory_config": {
                "scope": "CUSTOMER",
                "retention_ttl_hours": 336,
                "max_entries": 15,
                "relevance_threshold": 0.65
            },
            "guardrail_policy_ids": ["gr-fact-001", "gr-pii-001"],
            "human_approval_policy": "HIGH_RISK_ONLY",
            "max_execution_steps": 5,
            "timeout_seconds": 35,
        },
        {
            "id": "agent-social-005",
            "slug": "social_bridge",
            "name": "Social Media Omnichannel Bridge",
            "description": "Engaging conversational bridge managing WhatsApp, Facebook Messenger, and Instagram Direct conversations with warm hospitality.",
            "role": "Social Concierge",
            "objective": "Convert social engagements into qualified buyer leads via welcoming Bangla/Banglish/English interaction.",
            "owner": "growth-marketing@glgassets.com",
            "status": "PRODUCTION",
            "environment": "production",
            "primary_model": "llama-3.3-70b-versatile",
            "fallback_model": "llama-3.1-8b-instant",
            "current_prompt_version": "v1.5",
            "temperature": 0.35,
            "top_p": 0.95,
            "max_tokens": 850,
            "persona_preset": "Warm Conversational",
            "enabled_tools": ["whatsapp_send", "property_search", "crm_lead_sync"],
            "rag_config": {
                "chunk_size": 384,
                "top_k": 3,
                "similarity_threshold": 0.60,
                "hybrid_alpha": 0.55,
                "grounding_enforced": True,
                "enabled_sources": ["property_db", "brochures"]
            },
            "memory_config": {
                "scope": "CONVERSATION",
                "retention_ttl_hours": 48,
                "max_entries": 8,
                "relevance_threshold": 0.60
            },
            "guardrail_policy_ids": ["gr-fact-001", "gr-pii-001", "gr-inj-001"],
            "human_approval_policy": "NONE",
            "max_execution_steps": 4,
            "timeout_seconds": 20,
        }
    ],
    "providers": [
        {
            "id": "prov-groq",
            "provider_key": "groq",
            "display_name": "Groq LPU Inference Engine",
            "base_url": "https://api.groq.com/openai/v1",
            "is_active": True,
            "health_status": "HEALTHY",
            "last_ping_ms": 142.5,
            "capabilities": ["chat", "streaming", "tools", "structured_output"],
            "rate_limit_rpm": 60,
            "rate_limit_tpm": 120000,
        },
        {
            "id": "prov-openai",
            "provider_key": "openai",
            "display_name": "OpenAI Enterprise Gateway",
            "base_url": "https://api.openai.com/v1",
            "is_active": True,
            "health_status": "HEALTHY",
            "last_ping_ms": 285.0,
            "capabilities": ["chat", "streaming", "tools", "vision", "embeddings", "fine_tuning"],
            "rate_limit_rpm": 500,
            "rate_limit_tpm": 300000,
        },
        {
            "id": "prov-anthropic",
            "provider_key": "anthropic",
            "display_name": "Anthropic Claude Suite",
            "base_url": "https://api.anthropic.com/v1",
            "is_active": True,
            "health_status": "HEALTHY",
            "last_ping_ms": 310.2,
            "capabilities": ["chat", "streaming", "tools", "vision", "long_context"],
            "rate_limit_rpm": 200,
            "rate_limit_tpm": 250000,
        },
        {
            "id": "prov-google",
            "provider_key": "google",
            "display_name": "Google Gemini Enterprise",
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "is_active": True,
            "health_status": "HEALTHY",
            "last_ping_ms": 195.4,
            "capabilities": ["chat", "streaming", "tools", "vision", "embeddings", "multimodal"],
            "rate_limit_rpm": 300,
            "rate_limit_tpm": 500000,
        },
        {
            "id": "prov-openrouter",
            "provider_key": "openrouter",
            "display_name": "OpenRouter Global Aggregator",
            "base_url": "https://openrouter.ai/api/v1",
            "is_active": True,
            "health_status": "HEALTHY",
            "last_ping_ms": 210.0,
            "capabilities": ["chat", "streaming", "tools"],
            "rate_limit_rpm": 120,
            "rate_limit_tpm": 200000,
        }
    ],
    "models": [
        {
            "id": "mod-llama-70b",
            "model_id": "llama-3.3-70b-versatile",
            "provider_id": "prov-groq",
            "display_name": "LLaMA 3.3 70B Versatile",
            "model_type": "BASE",
            "context_window": 131072,
            "max_output_tokens": 8192,
            "input_cost_per_m": 0.59,
            "output_cost_per_m": 0.79,
            "cached_cost_per_m": 0.30,
            "supports_structured_output": True,
            "supports_tools": True,
            "supports_streaming": True,
            "status": "PRODUCTION",
            "benchmark_scores": {"groundedness": 97.4, "latency_p50": 340, "tool_accuracy": 96.8},
            "is_enabled": True
        },
        {
            "id": "mod-llama-8b",
            "model_id": "llama-3.1-8b-instant",
            "provider_id": "prov-groq",
            "display_name": "LLaMA 3.1 8B Instant (Fallback)",
            "model_type": "BASE",
            "context_window": 131072,
            "max_output_tokens": 4096,
            "input_cost_per_m": 0.05,
            "output_cost_per_m": 0.08,
            "cached_cost_per_m": 0.02,
            "supports_structured_output": True,
            "supports_tools": True,
            "supports_streaming": True,
            "status": "PRODUCTION",
            "benchmark_scores": {"groundedness": 92.1, "latency_p50": 110, "tool_accuracy": 91.5},
            "is_enabled": True
        },
        {
            "id": "mod-gpt4o",
            "model_id": "gpt-4o",
            "provider_id": "prov-openai",
            "display_name": "OpenAI GPT-4o Flagship",
            "model_type": "BASE",
            "context_window": 128000,
            "max_output_tokens": 4096,
            "input_cost_per_m": 2.50,
            "output_cost_per_m": 10.00,
            "cached_cost_per_m": 1.25,
            "supports_structured_output": True,
            "supports_tools": True,
            "supports_streaming": True,
            "status": "PRODUCTION",
            "benchmark_scores": {"groundedness": 98.9, "latency_p50": 620, "tool_accuracy": 98.5},
            "is_enabled": True
        },
        {
            "id": "mod-gpt4o-mini",
            "model_id": "gpt-4o-mini",
            "provider_id": "prov-openai",
            "display_name": "OpenAI GPT-4o Mini",
            "model_type": "BASE",
            "context_window": 128000,
            "max_output_tokens": 4096,
            "input_cost_per_m": 0.15,
            "output_cost_per_m": 0.60,
            "cached_cost_per_m": 0.075,
            "supports_structured_output": True,
            "supports_tools": True,
            "supports_streaming": True,
            "status": "PRODUCTION",
            "benchmark_scores": {"groundedness": 96.5, "latency_p50": 240, "tool_accuracy": 96.0},
            "is_enabled": True
        },
        {
            "id": "mod-claude-sonnet",
            "model_id": "claude-3-5-sonnet-20241022",
            "provider_id": "prov-anthropic",
            "display_name": "Anthropic Claude 3.5 Sonnet",
            "model_type": "BASE",
            "context_window": 200000,
            "max_output_tokens": 8192,
            "input_cost_per_m": 3.00,
            "output_cost_per_m": 15.00,
            "cached_cost_per_m": 1.50,
            "supports_structured_output": True,
            "supports_tools": True,
            "supports_streaming": True,
            "status": "PRODUCTION",
            "benchmark_scores": {"groundedness": 99.1, "latency_p50": 740, "tool_accuracy": 98.8},
            "is_enabled": True
        },
        {
            "id": "mod-lora-dhaka",
            "model_id": "glg-bangla-realestate-lora-v1",
            "provider_id": "prov-groq",
            "display_name": "GLG Bangla Real Estate LoRA v1",
            "model_type": "FINE_TUNED",
            "context_window": 131072,
            "max_output_tokens": 4096,
            "input_cost_per_m": 0.65,
            "output_cost_per_m": 0.85,
            "cached_cost_per_m": 0.35,
            "supports_structured_output": True,
            "supports_tools": True,
            "supports_streaming": True,
            "status": "PRODUCTION",
            "benchmark_scores": {"groundedness": 98.4, "latency_p50": 360, "bangla_fluency": 99.2},
            "is_enabled": True
        }
    ],
    "tools": [
        {
            "id": "tool-prop-search",
            "tool_key": "property_search",
            "name": "Property Inventory Search",
            "description": "Query verified real-estate database for luxury apartments, penthouses, and commercial spaces across Dhaka (Gulshan, Banani, Baridhara, Dhanmondi).",
            "category": "data_retrieval",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Target micro-market: Gulshan, Banani, Baridhara, Dhanmondi"},
                    "bedrooms": {"type": "integer", "description": "Number of bedrooms (3, 4, 5)"},
                    "max_price_bdt": {"type": "number", "description": "Maximum budget in BDT (e.g. 25000000 for 2.5 Cr)"}
                },
                "required": []
            },
            "requires_approval": False,
            "risk_level": "LOW",
            "timeout_ms": 3000,
            "is_enabled": True,
            "assigned_agents": ["property_agent", "supervisor", "social_bridge"]
        },
        {
            "id": "tool-avail-check",
            "tool_key": "availability_check",
            "name": "Live Unit Availability Check",
            "description": "Check real-time unit status (Available, Reserved, Sold) and floor availability across GLG projects.",
            "category": "data_retrieval",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "GLG Sky Tower, GLG Crown Jewel, etc."}
                },
                "required": ["project_name"]
            },
            "requires_approval": False,
            "risk_level": "LOW",
            "timeout_ms": 2500,
            "is_enabled": True,
            "assigned_agents": ["property_agent", "faq_agent"]
        },
        {
            "id": "tool-tour-book",
            "tool_key": "schedule_tour",
            "name": "VIP Site Tour Booking",
            "description": "Reserve a private executive site tour slot and assign a luxury relationship manager.",
            "category": "transaction",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string"},
                    "preferred_date": {"type": "string"},
                    "client_phone": {"type": "string"}
                },
                "required": ["project_name", "client_phone"]
            },
            "requires_approval": True,
            "risk_level": "HIGH",
            "timeout_ms": 5000,
            "is_enabled": True,
            "assigned_agents": ["property_agent", "email_agent"]
        },
        {
            "id": "tool-crm-sync",
            "tool_key": "crm_lead_sync",
            "name": "CRM Lead Qualification Sync",
            "description": "Sync customer budget, timeframe, and micro-market preferences to the central CRM lead card.",
            "category": "crm",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string"},
                    "phone": {"type": "string"},
                    "budget_bdt": {"type": "number"},
                    "target_location": {"type": "string"}
                },
                "required": ["phone"]
            },
            "requires_approval": False,
            "risk_level": "LOW",
            "timeout_ms": 3000,
            "is_enabled": True,
            "assigned_agents": ["supervisor", "property_agent", "email_agent", "social_bridge"]
        },
        {
            "id": "tool-knowledge-search",
            "tool_key": "knowledge_search",
            "name": "Company Policy & Spec Lookup",
            "description": "Search official specifications, backup generator capacities, lift brands, and legal titles.",
            "category": "data_retrieval",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            },
            "requires_approval": False,
            "risk_level": "LOW",
            "timeout_ms": 2500,
            "is_enabled": True,
            "assigned_agents": ["faq_agent"]
        },
        {
            "id": "tool-policy-lookup",
            "tool_key": "policy_lookup",
            "name": "Legal & Installment Guidelines",
            "description": "Retrieve official Rajuk approval details, land mutation records, and standard payment installment terms.",
            "category": "data_retrieval",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"}
                },
                "required": ["topic"]
            },
            "requires_approval": False,
            "risk_level": "LOW",
            "timeout_ms": 2500,
            "is_enabled": True,
            "assigned_agents": ["faq_agent"]
        },
        {
            "id": "tool-email-dispatch",
            "tool_key": "email_dispatch",
            "name": "Executive Email Proposal Dispatch",
            "description": "Send formal investment summaries and luxury brochure links via authenticated SMTP.",
            "category": "communication",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "recipient_email": {"type": "string"},
                    "subject": {"type": "string"},
                    "body_html": {"type": "string"}
                },
                "required": ["recipient_email", "subject", "body_html"]
            },
            "requires_approval": True,
            "risk_level": "HIGH",
            "timeout_ms": 6000,
            "is_enabled": True,
            "assigned_agents": ["email_agent"]
        },
        {
            "id": "tool-whatsapp-send",
            "tool_key": "whatsapp_send",
            "name": "WhatsApp Business Interactive Message",
            "description": "Dispatch rich media messages, brochure PDFs, and quick-reply buttons via WhatsApp Cloud API.",
            "category": "communication",
            "parameters_schema": {
                "type": "object",
                "properties": {
                    "recipient_phone": {"type": "string"},
                    "message_text": {"type": "string"}
                },
                "required": ["recipient_phone", "message_text"]
            },
            "requires_approval": False,
            "risk_level": "MEDIUM",
            "timeout_ms": 4000,
            "is_enabled": True,
            "assigned_agents": ["social_bridge"]
        }
    ],
    "routing_rules": [
        {
            "id": "route-001",
            "priority": 1,
            "name": "Intent Classification -> Ultra-Fast LLaMA 8B",
            "condition_task": "classification",
            "condition_complexity": "low",
            "condition_agent": "supervisor",
            "target_model_id": "llama-3.1-8b-instant",
            "fallback_model_id": "llama-3.3-70b-versatile",
            "strategy": "COST_OPTIMIZED",
            "is_active": True
        },
        {
            "id": "route-002",
            "priority": 2,
            "name": "Complex Property Advisory -> LLaMA 70B",
            "condition_task": "recommendation",
            "condition_complexity": "medium",
            "condition_agent": "property_agent",
            "target_model_id": "llama-3.3-70b-versatile",
            "fallback_model_id": "gpt-4o",
            "strategy": "QUALITY_OPTIMIZED",
            "is_active": True
        },
        {
            "id": "route-003",
            "priority": 3,
            "name": "Executive Pitch Drafting -> Claude 3.5 Sonnet",
            "condition_task": "complex_analysis",
            "condition_complexity": "high",
            "condition_agent": "email_agent",
            "target_model_id": "claude-3-5-sonnet-20241022",
            "fallback_model_id": "llama-3.3-70b-versatile",
            "strategy": "QUALITY_OPTIMIZED",
            "is_active": True
        }
    ],
    "guardrails": [
        {
            "id": "gr-fact-001",
            "category": "BUSINESS",
            "rule_name": "Verified Property Price & Handover Shield",
            "description": "Prevents AI from inventing prices or unverified handover dates. Must cite canonical database pricing in BDT.",
            "action": "BLOCK",
            "severity": "CRITICAL",
            "rule_parameters": {"tolerance_pct": 0.0, "require_provenance": True},
            "is_enabled": True,
            "total_triggers": 14
        },
        {
            "id": "gr-pii-001",
            "category": "DATA",
            "rule_name": "Bangladesh NID & Financial Redaction",
            "description": "Automatically masks 10/13/17-digit Bangladesh National IDs, bank routing numbers, and payment cards.",
            "action": "REWRITE",
            "severity": "HIGH",
            "rule_parameters": {"mask_char": "*", "preserve_last_digits": 4},
            "is_enabled": True,
            "total_triggers": 42
        },
        {
            "id": "gr-inj-001",
            "category": "SAFETY",
            "rule_name": "Prompt Injection & Jailbreak Neutralizer",
            "description": "Detects multilingual override commands ('ignore all instructions', 'ager shob bhule jao', 'dan mode').",
            "action": "BLOCK",
            "severity": "CRITICAL",
            "rule_parameters": {"scan_bangla": True, "strictness": 0.92},
            "is_enabled": True,
            "total_triggers": 27
        }
    ],
    "datasets": [
        {
            "id": "ds-eval-001",
            "slug": "dhaka_luxury_eval_v2",
            "name": "Dhaka Luxury Residences Golden Benchmark",
            "dataset_type": "evaluation",
            "target_agent": "property_agent",
            "version": "v2.0",
            "total_examples": 5,
            "quality_score": 98.4,
            "train_count": 0,
            "val_count": 1,
            "test_count": 4,
            "is_locked": True,
            "created_by": "developer@glgassets.com"
        },
        {
            "id": "ds-eval-002",
            "slug": "bangla_banglish_intent_v1",
            "name": "Bangla & Banglish Intent Classification Corpus",
            "dataset_type": "evaluation",
            "target_agent": "supervisor",
            "version": "v1.5",
            "total_examples": 5,
            "quality_score": 97.8,
            "train_count": 0,
            "val_count": 1,
            "test_count": 4,
            "is_locked": True,
            "created_by": "developer@glgassets.com"
        }
    ],
    "dataset_examples": [
        {
            "id": "ex-001",
            "dataset_id": "ds-eval-001",
            "split": "test",
            "input_message": "Gulshan 2 e 3 BHK luxury flat er price koto ar handover kobe?",
            "expected_intent": "property_search",
            "expected_output": "GLG Gulshan Heights features 3 BHK apartments priced at 95 Lakhs BDT (৳9,500,000) with handover scheduled for December 2026.",
            "expected_tools": ["property_search"],
            "expected_facts": ["95 Lakhs BDT", "December 2026", "Gulshan 2"],
            "metadata_tags": {"area": "Gulshan 2", "language": "banglish"}
        },
        {
            "id": "ex-002",
            "dataset_id": "ds-eval-001",
            "split": "test",
            "input_message": "Banani te kono available project ache infinity pool soho?",
            "expected_intent": "property_search",
            "expected_output": "GLG Banani Crest on prime Banani Road includes a Rooftop Infinity Pool, 3 BHK suites priced at 1.2 Crore BDT with December 2026 handover.",
            "expected_tools": ["property_search"],
            "expected_facts": ["GLG Banani Crest", "Infinity Pool", "1.2 Crore BDT"],
            "metadata_tags": {"area": "Banani", "amenity": "pool"}
        },
        {
            "id": "ex-003",
            "dataset_id": "ds-eval-001",
            "split": "test",
            "input_message": "Baridhara diplomatic zone er 4 BHK project details bolun.",
            "expected_intent": "property_search",
            "expected_output": "GLG Luxe Heights in Baridhara Diplomatic Zone offers ultra-exclusive 4 BHK residences overlooking the lake, priced at 1.8 Crore BDT.",
            "expected_tools": ["property_search"],
            "expected_facts": ["GLG Luxe Heights", "Baridhara Diplomatic Zone", "1.8 Crore BDT"],
            "metadata_tags": {"area": "Baridhara"}
        },
        {
            "id": "ex-004",
            "dataset_id": "ds-eval-002",
            "split": "test",
            "input_message": "Ami flat kinte chai, Gulshan e budget 1.5 crore.",
            "expected_intent": "property_inquiry",
            "expected_output": "Supervisor routes to property_agent with extracted budget 1.5 Crore BDT and location Gulshan.",
            "expected_tools": ["crm_lead_sync"],
            "expected_facts": ["Gulshan", "1.5 Crore"],
            "metadata_tags": {"language": "banglish"}
        },
        {
            "id": "ex-005",
            "dataset_id": "ds-eval-002",
            "split": "test",
            "input_message": "Installment payment schedule ki bhabe kaj kore?",
            "expected_intent": "faq_policy",
            "expected_output": "Supervisor routes to faq_agent for installment schedule policies.",
            "expected_tools": ["knowledge_search"],
            "expected_facts": ["payment schedule"],
            "metadata_tags": {"intent": "policy"}
        }
    ],
    "evaluations": [
        {
            "id": "eval-001",
            "suite_name": "Banani & Gulshan Property Inquiries Baseline",
            "dataset_id": "ds-eval-001",
            "agent_id": "property_agent",
            "model_tested": "llama-3.3-70b-versatile",
            "prompt_version": "v2.1",
            "total_cases": 50,
            "passed_cases": 49,
            "failed_cases": 1,
            "accuracy_pct": 98.0,
            "groundedness_pct": 98.5,
            "hallucination_pct": 0.4,
            "tool_accuracy_pct": 97.2,
            "schema_correctness_pct": 100.0,
            "avg_latency_ms": 342.0,
            "status": "COMPLETED",
            "gate_verdict": "PASS",
            "created_by": "developer@glgassets.com"
        }
    ],
    "releases": [
        {
            "id": "rel-3-8-0",
            "release_tag": "v3.8.0",
            "title": "Production AI Release — Banani & Gulshan Hybrid RAG v2",
            "description": "Full release snapshot with Groq LLaMA 3.3 70B inference, pgvector 1536-d semantic retrieval, and dual BDT currency accounting.",
            "environment": "PRODUCTION",
            "manifest": {
                "agents": {"property_agent": "v2.1", "supervisor": "v2.0", "faq_agent": "v1.4"},
                "model": "llama-3.3-70b-versatile",
                "rag": "hybrid_rrf_k60",
                "guardrails": ["gr-fact-001", "gr-pii-001", "gr-inj-001"],
                "tools": ["property_search", "availability_check", "crm_lead_sync", "schedule_tour"]
            },
            "evaluation_gate_passed": True,
            "evaluation_score": 98.5,
            "deployed_by": "developer@glgassets.com",
            "deployed_at": "2026-09-12T10:00:00Z",
            "can_rollback": True,
            "previous_release_tag": "v3.7.2"
        },
        {
            "id": "rel-3-7-2",
            "release_tag": "v3.7.2",
            "title": "Staging Release — Fallback Cascades",
            "description": "Automated 8B fallback validation for rate-limit protection.",
            "environment": "ARCHIVED",
            "manifest": {
                "agents": {"property_agent": "v2.0", "supervisor": "v1.9"},
                "model": "llama-3.3-70b-versatile"
            },
            "evaluation_gate_passed": True,
            "evaluation_score": 97.2,
            "deployed_by": "developer@glgassets.com",
            "deployed_at": "2026-09-01T10:00:00Z",
            "can_rollback": False,
            "previous_release_tag": None
        }
    ],
    "budget": {
        "id": "bgt-001",
        "period": "MONTHLY",
        "monthly_budget_usd": 650.0,
        "current_spend_usd": 128.45,
        "warn_threshold_pct": 75.0,
        "hard_stop_threshold_pct": 100.0,
        "is_hard_stop_active": False,
        "agent_budgets": {
            "property_agent": 300.0,
            "supervisor": 120.0,
            "faq_agent": 90.0,
            "email_agent": 80.0,
            "social_bridge": 60.0
        }
    },
    "approvals": [
        {
            "id": "appr-001",
            "agent_id": "email_agent",
            "action_type": "SEND_OFFER",
            "risk_level": "HIGH",
            "reason": "Exclusive discount proposal for GLG Sky Tower 4BHK exceeding ৳500,000 threshold.",
            "context_data": {"customer": "Tanvir Ahmed", "project": "GLG Sky Tower", "quoted_price": "৳2.40 Crore"},
            "generated_content": "Dear Mr. Tanvir, GLG Assets is pleased to extend an executive limited-time token waiver on the 18th floor panoramic suite at GLG Sky Tower.",
            "status": "PENDING",
            "reviewer": None,
            "reviewer_notes": None,
            "reviewed_at": None,
            "created_at": "2026-09-14T07:15:00Z"
        },
        {
            "id": "appr-002",
            "agent_id": "property_agent",
            "action_type": "SCHEDULE_VIP_TOUR",
            "risk_level": "MEDIUM",
            "reason": "Request for private helicopter transfer and site inspection for Baridhara Diplomatic Penthouse.",
            "context_data": {"customer": "Kamrul Hassan", "project": "GLG Luxe Heights"},
            "generated_content": "Confirmed tentative VIP site tour slot for Saturday, Sept 20th. Relationship Manager assigned.",
            "status": "PENDING",
            "reviewer": None,
            "reviewer_notes": None,
            "reviewed_at": None,
            "created_at": "2026-09-14T09:30:00Z"
        }
    ],
    "incidents": [
        {
            "id": "inc-001",
            "incident_number": "INC-2026-004",
            "title": "Groq API transient 429 rate limit spike (mitigated by 8B fallback)",
            "severity": "P2",
            "incident_type": "provider_outage",
            "status": "RESOLVED",
            "agent_id": "property_agent",
            "model_id": "llama-3.3-70b-versatile",
            "owner": "developer@glgassets.com",
            "root_cause": "Concurrently high traffic burst during weekend open house promotion triggered 60 RPM provider bucket limit.",
            "resolution": "Graceful fallback to LLaMA 3.1 8B Instant automatically intercepted 14 requests without customer drop-off.",
            "timeline": [
                {"timestamp": "2026-09-13T14:22:00Z", "note": "Elevated 429 responses detected on Groq 70B."},
                {"timestamp": "2026-09-13T14:22:05Z", "note": "Automated fallback to 8B Instant engaged."},
                {"timestamp": "2026-09-13T14:35:00Z", "note": "Rate limit quota reset; primary 70B resumed."}
            ]
        }
    ],
    "audit_logs": [
        {
            "id": "audit-001",
            "event_type": "AGENT_CONFIG_UPDATED",
            "actor_email": "developer@glgassets.com",
            "actor_role": "developer",
            "entity_type": "ai_agent",
            "entity_id": "property_agent",
            "action": "UPDATE",
            "reason": "Fine-tuned hybrid RAG alpha from 0.60 to 0.65 for improved Dhaka landmark grounding.",
            "created_at": "2026-09-14T06:30:00Z"
        },
        {
            "id": "audit-002",
            "event_type": "RELEASE_DEPLOYED",
            "actor_email": "developer@glgassets.com",
            "actor_role": "developer",
            "entity_type": "ai_release",
            "entity_id": "v3.8.0",
            "action": "DEPLOY",
            "reason": "Promoted release v3.8.0 to Production following 98.5% evaluation gate pass.",
            "created_at": "2026-09-12T10:00:00Z"
        }
    ],
    "traces": [
        {
            "id": "trc-init-001",
            "trace_id": "trc-98fa321a",
            "run_id": "run-a101",
            "agent_id": "property_agent",
            "channel": "WhatsApp",
            "environment": "production",
            "user_query": "Gulshan 2 e 3 BHK apartment er price koto?",
            "agent_response": "GLG Gulshan Heights features 3 BHK residences starting at 95 Lakhs BDT with handover in December 2026.",
            "model_used": "llama-3.3-70b-versatile",
            "prompt_version": "v2.1",
            "status": "SUCCESS",
            "total_tokens": 412,
            "prompt_tokens": 284,
            "completion_tokens": 128,
            "cached_tokens": 64,
            "latency_ms": 342.0,
            "cost_usd": 0.00028,
            "cost_bdt": 0.0343,
            "spans": [
                {"span_id": "span-1", "name": "Ingress & Authentication", "latency_ms": 2.4, "status": "OK"},
                {"span_id": "span-2", "name": "Pre-Guard PII Check", "latency_ms": 14.0, "status": "OK"},
                {"span_id": "span-3", "name": "RAG Hybrid Retrieval", "latency_ms": 42.0, "status": "OK"},
                {"span_id": "span-4", "name": "Tool Execution: property_search", "latency_ms": 68.0, "status": "OK"},
                {"span_id": "span-5", "name": "LLM Inference: Groq LLaMA 70B", "latency_ms": 215.0, "status": "OK"}
            ],
            "guardrail_actions": [],
            "tool_calls": [{"tool": "property_search", "location": "Gulshan 2"}],
            "rag_retrievals": [{"document": "GLG_Gulshan_Heights_Brochure.pdf", "score": 0.94}],
            "timestamp": "2026-09-14T08:00:00Z"
        }
    ],
    "fine_tune_jobs": [
        {
            "id": "ft-job-001",
            "job_name": "glg-bangla-realestate-lora-v1",
            "base_model": "llama-3.3-70b-versatile",
            "dataset_id": "ds-eval-002",
            "lora_rank": 16,
            "epochs": 3,
            "learning_rate": 0.0002,
            "status": "COMPLETED",
            "progress_pct": 100.0,
            "current_epoch": 3,
            "train_loss": 0.412,
            "eval_loss": 0.385,
            "output_model_id": "glg-bangla-realestate-lora-v1",
            "metrics": {"perplexity": 1.47, "accuracy": 97.4, "bleu": 42.6},
            "training_duration_sec": 3840,
            "cost_usd": 14.80,
            "cost_bdt": 1813.00,
            "created_by": "developer@glgassets.com",
            "started_at": "2026-09-10T04:00:00Z",
            "completed_at": "2026-09-10T05:04:00Z",
            "created_at": "2026-09-10T03:55:00Z"
        }
    ],
    "experiments": [
        {
            "id": "exp-001",
            "name": "Consultative Luxury vs Direct Pitch Prompt",
            "description": "A/B test comparing conversational consultative tone against high-urgency luxury pitch on WhatsApp.",
            "agent_id": "property_agent",
            "test_type": "PROMPT",
            "status": "RUNNING",
            "traffic_split_a_pct": 50,
            "traffic_split_b_pct": 50,
            "variant_a_config": {"prompt_version": "v2.1", "persona": "Consultative Luxury", "model": "llama-3.3-70b-versatile"},
            "variant_b_config": {"prompt_version": "v2.2-urgency", "persona": "Direct Executive Closer", "model": "llama-3.3-70b-versatile"},
            "metrics_a": {"conversion_rate": 28.4, "task_success_pct": 96.2, "latency_ms": 340.0, "cost_per_req_usd": 0.00028, "total_runs": 128},
            "metrics_b": {"conversion_rate": 31.8, "task_success_pct": 97.1, "latency_ms": 335.0, "cost_per_req_usd": 0.00027, "total_runs": 126},
            "winner_variant": "VARIANT_B",
            "confidence_pct": 92.4,
            "total_evaluations": 254,
            "created_by": "developer@glgassets.com",
            "created_at": "2026-09-11T12:00:00Z"
        }
    ],
    "benchmarks": [
        {
            "id": "bmk-001",
            "name": "Groq LLaMA 3.3 70B vs OpenAI GPT-4o Flagship",
            "category": "MODEL_HEAD_TO_HEAD",
            "entity_a_label": "Groq LLaMA 3.3 70B Versatile",
            "entity_b_label": "OpenAI GPT-4o Flagship",
            "entity_a_config": {"model": "llama-3.3-70b-versatile", "provider": "groq"},
            "entity_b_config": {"model": "gpt-4o", "provider": "openai"},
            "metrics_comparison": {
                "quality": {"a": 96.8, "b": 98.2},
                "latency_p50_ms": {"a": 280.0, "b": 640.0},
                "cost_per_m_usd": {"a": 0.59, "b": 2.50},
                "reliability_pct": {"a": 99.4, "b": 99.8},
                "tool_accuracy_pct": {"a": 97.5, "b": 98.9},
                "grounding_pct": {"a": 98.4, "b": 99.1},
                "safety_score_pct": {"a": 99.6, "b": 99.7},
                "completion_rate_pct": {"a": 99.1, "b": 99.5}
            },
            "scorecard": {
                "winner": "llama-3.3-70b-versatile",
                "verdict": "Groq LLaMA 3.3 70B recommended for production: 2.3x faster latency and 76% lower cost with comparable 96.8% quality.",
                "radar_dimensions": ["Quality", "Latency", "Cost Efficiency", "Reliability", "Tool Accuracy", "Grounding", "Safety", "Task Completion"]
            },
            "winner": "llama-3.3-70b-versatile",
            "executed_by": "developer@glgassets.com",
            "created_at": "2026-09-13T09:00:00Z"
        }
    ],
    "memories": [
        {
            "id": "mem-001",
            "agent_id": "property_agent",
            "customer_id": "cust-tanvir-01",
            "conversation_id": "conv-wsp-4412",
            "scope": "CUSTOMER",
            "memory_key": "preferred_neighborhood",
            "memory_value": "Banani Road 11 or Gulshan 2 (minimum 3 bedrooms with 2 dedicated parking bays)",
            "relevance_score": 0.95,
            "is_sensitive": False,
            "created_at": "2026-09-12T14:30:00Z"
        },
        {
            "id": "mem-002",
            "agent_id": "property_agent",
            "customer_id": "cust-tanvir-01",
            "conversation_id": "conv-wsp-4412",
            "scope": "CUSTOMER",
            "memory_key": "maximum_budget_bdt",
            "memory_value": "৳2.2 Crore BDT maximum purchase capability",
            "relevance_score": 0.98,
            "is_sensitive": True,
            "created_at": "2026-09-12T14:32:00Z"
        }
    ],
    "snapshots": [
        {
            "id": "snap-001",
            "snapshot_tag": "AI-RELEASE-3.8.0",
            "title": "Unified Production Snapshot v3.8.0",
            "description": "Canonical release bundling Property Consultant v2.1, Prompt v2.1, Groq LLaMA 70B, pgvector Hybrid RAG, and Security Guardrails.",
            "agent_slug": "property_agent",
            "agent_version": "v2.1",
            "prompt_version": "v2.1",
            "model_id": "llama-3.3-70b-versatile",
            "rag_version": "v2.0",
            "guardrail_version": "v1.4",
            "tool_versions": ["property_search:v2.0", "availability_check:v1.2", "schedule_tour:v1.5"],
            "memory_version": "v1.8",
            "workflow_version": "v1.2.0",
            "full_manifest": {
                "temperature": 0.2,
                "top_p": 0.9,
                "tools": ["property_search", "availability_check", "crm_lead_sync", "schedule_tour"],
                "guardrails": ["gr-fact-001", "gr-pii-001", "gr-inj-001"],
                "hybrid_alpha": 0.65
            },
            "created_by": "developer@glgassets.com",
            "created_at": "2026-09-12T10:00:00Z"
        }
    ],
    "policies": [
        {
            "id": "pol-001",
            "name": "High-Value Offer Mandatory Human Escalation",
            "description": "Escalates any proposed pricing concession exceeding ৳500,000 to Human Approval queue.",
            "priority": 1,
            "condition_expression": "action == 'SEND_OFFER' and discount_amount_bdt > 500000",
            "action_directive": "HUMAN_APPROVAL",
            "scope": "ALL_AGENTS",
            "is_enabled": True,
            "environment": "production",
            "created_at": "2026-09-08T00:00:00Z"
        },
        {
            "id": "pol-002",
            "name": "Unverified Database Price Block",
            "description": "Blocks any generated response with property price differing from canonical database price.",
            "priority": 2,
            "condition_expression": "property_price != verified_database_price",
            "action_directive": "BLOCK",
            "scope": "property_agent",
            "is_enabled": True,
            "environment": "production",
            "created_at": "2026-09-08T00:00:00Z"
        },
        {
            "id": "pol-003",
            "name": "Low Confidence Message Human Escalation",
            "description": "Directs customer communication with model confidence < 0.85 to human agent review.",
            "priority": 3,
            "condition_expression": "action == 'SEND_MESSAGE' and confidence < 0.85",
            "action_directive": "HUMAN_APPROVAL",
            "scope": "ALL_AGENTS",
            "is_enabled": True,
            "environment": "production",
            "created_at": "2026-09-08T00:00:00Z"
        }
    ]
}


class AIControlPlaneStore:
    """PostgreSQL-first Persistence Store for the AI & Agent Control Plane."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self._memory_cache: Dict[str, Any] = copy.deepcopy(INITIAL_SEEDS)
        self._db_initialized = False

    async def _get_db_session(self):
        """Helper to get async db session if DB is reachable."""
        if not is_db_reachable():
            return None
        try:
            return async_session_factory()
        except Exception:
            return None

    async def ensure_db_seeded(self):
        """Seed PostgreSQL tables with canonical data if database is empty."""
        session_cm = await self._get_db_session()
        if not session_cm:
            return

        async with session_cm as session:
            try:
                # Check if agents table has rows
                stmt = select(func.count()).select_from(AIAgentRecord)
                res = await session.execute(stmt)
                count = res.scalar() or 0
                if count > 0:
                    self._db_initialized = True
                    return

                logger.info("[AIControlPlaneStore] Seeding PostgreSQL tables with canonical dataset...")

                # 1. Seed Providers
                for p in INITIAL_SEEDS["providers"]:
                    session.add(AIProviderRecord(
                        id=p["id"],
                        provider_key=p["provider_key"],
                        display_name=p["display_name"],
                        base_url=p.get("base_url"),
                        is_active=p.get("is_active", True),
                        health_status=p.get("health_status", "HEALTHY"),
                        last_ping_ms=p.get("last_ping_ms"),
                        capabilities=p.get("capabilities", []),
                        rate_limit_rpm=p.get("rate_limit_rpm", 60),
                        rate_limit_tpm=p.get("rate_limit_tpm", 100000)
                    ))

                # 2. Seed Models
                for m in INITIAL_SEEDS["models"]:
                    session.add(AIModelRecord(
                        id=m["id"],
                        model_id=m["model_id"],
                        provider_id=m["provider_id"],
                        display_name=m["display_name"],
                        model_type=m.get("model_type", "BASE"),
                        context_window=m.get("context_window", 131072),
                        max_output_tokens=m.get("max_output_tokens", 4096),
                        input_cost_per_m=m.get("input_cost_per_m", 0.59),
                        output_cost_per_m=m.get("output_cost_per_m", 0.79),
                        cached_cost_per_m=m.get("cached_cost_per_m", 0.30),
                        supports_structured_output=m.get("supports_structured_output", True),
                        supports_tools=m.get("supports_tools", True),
                        supports_streaming=m.get("supports_streaming", True),
                        status=m.get("status", "PRODUCTION"),
                        benchmark_scores=m.get("benchmark_scores", {}),
                        is_enabled=m.get("is_enabled", True)
                    ))

                # 3. Seed Agents
                for a in INITIAL_SEEDS["agents"]:
                    session.add(AIAgentRecord(
                        id=a["id"],
                        slug=a["slug"],
                        name=a["name"],
                        description=a.get("description"),
                        role=a.get("role", "assistant"),
                        objective=a.get("objective"),
                        owner=a.get("owner", "dev-team@glgassets.com"),
                        status=a.get("status", "PRODUCTION"),
                        environment=a.get("environment", "production"),
                        primary_model=a.get("primary_model", "llama-3.3-70b-versatile"),
                        fallback_model=a.get("fallback_model"),
                        current_prompt_version=a.get("current_prompt_version", "v1.0"),
                        temperature=a.get("temperature", 0.2),
                        top_p=a.get("top_p", 0.9),
                        max_tokens=a.get("max_tokens", 1024),
                        persona_preset=a.get("persona_preset", "Consultative Luxury"),
                        enabled_tools=a.get("enabled_tools", []),
                        rag_config=a.get("rag_config", {}),
                        memory_config=a.get("memory_config", {}),
                        guardrail_policy_ids=a.get("guardrail_policy_ids", []),
                        human_approval_policy=a.get("human_approval_policy", "NONE"),
                        max_execution_steps=a.get("max_execution_steps", 5),
                        timeout_seconds=a.get("timeout_seconds", 30)
                    ))

                # 4. Seed Tools
                for t in INITIAL_SEEDS["tools"]:
                    session.add(AIToolRecord(
                        id=t["id"],
                        tool_key=t["tool_key"],
                        name=t["name"],
                        description=t["description"],
                        category=t.get("category", "data_retrieval"),
                        parameters_schema=t.get("parameters_schema", {}),
                        output_schema=t.get("output_schema"),
                        requires_approval=t.get("requires_approval", False),
                        risk_level=t.get("risk_level", "LOW"),
                        timeout_ms=t.get("timeout_ms", 5000),
                        is_enabled=t.get("is_enabled", True),
                        assigned_agents=t.get("assigned_agents", [])
                    ))

                # 5. Seed Guardrails
                for g in INITIAL_SEEDS["guardrails"]:
                    session.add(AIGuardrailPolicyRecord(
                        id=g["id"],
                        category=g["category"],
                        rule_name=g["rule_name"],
                        description=g["description"],
                        action=g.get("action", "BLOCK"),
                        severity=g.get("severity", "HIGH"),
                        rule_parameters=g.get("rule_parameters", {}),
                        is_enabled=g.get("is_enabled", True),
                        total_triggers=g.get("total_triggers", 0)
                    ))

                # 6. Seed Routing Rules
                for r in INITIAL_SEEDS["routing_rules"]:
                    session.add(AIRoutingRuleRecord(
                        id=r["id"],
                        priority=r.get("priority", 100),
                        name=r["name"],
                        condition_task=r.get("condition_task"),
                        condition_complexity=r.get("condition_complexity"),
                        condition_agent=r.get("condition_agent"),
                        target_model_id=r["target_model_id"],
                        fallback_model_id=r.get("fallback_model_id"),
                        strategy=r.get("strategy", "RULE_BASED"),
                        is_active=r.get("is_active", True)
                    ))

                # 7. Seed Datasets & Examples
                for ds in INITIAL_SEEDS["datasets"]:
                    session.add(AIDatasetRecord(
                        id=ds["id"],
                        slug=ds["slug"],
                        name=ds["name"],
                        dataset_type=ds.get("dataset_type", "evaluation"),
                        target_agent=ds.get("target_agent", "property_agent"),
                        version=ds.get("version", "v1.0"),
                        total_examples=ds.get("total_examples", 0),
                        quality_score=ds.get("quality_score", 96.5),
                        train_count=ds.get("train_count", 0),
                        val_count=ds.get("val_count", 0),
                        test_count=ds.get("test_count", 0),
                        is_locked=ds.get("is_locked", False),
                        created_by=ds.get("created_by", "developer@glgassets.com")
                    ))

                for ex in INITIAL_SEEDS["dataset_examples"]:
                    session.add(AIDatasetExampleRecord(
                        id=ex["id"],
                        dataset_id=ex["dataset_id"],
                        split=ex.get("split", "test"),
                        input_message=ex["input_message"],
                        expected_intent=ex.get("expected_intent"),
                        expected_output=ex["expected_output"],
                        expected_tools=ex.get("expected_tools", []),
                        expected_facts=ex.get("expected_facts", []),
                        metadata_tags=ex.get("metadata_tags", {})
                    ))

                # 8. Seed Budget
                b = INITIAL_SEEDS["budget"]
                session.add(AIBudgetRecord(
                    id=b["id"],
                    period=b.get("period", "MONTHLY"),
                    monthly_budget_usd=b.get("monthly_budget_usd", 500.0),
                    current_spend_usd=b.get("current_spend_usd", 0.0),
                    warn_threshold_pct=b.get("warn_threshold_pct", 75.0),
                    hard_stop_threshold_pct=b.get("hard_stop_threshold_pct", 100.0),
                    is_hard_stop_active=b.get("is_hard_stop_active", False),
                    agent_budgets=b.get("agent_budgets", {})
                ))

                # 9. Seed Releases
                for rel in INITIAL_SEEDS["releases"]:
                    session.add(AIReleaseRecord(
                        id=rel["id"],
                        release_tag=rel["release_tag"],
                        title=rel["title"],
                        description=rel.get("description"),
                        environment=rel.get("environment", "STAGING"),
                        manifest=rel.get("manifest", {}),
                        evaluation_gate_passed=rel.get("evaluation_gate_passed", True),
                        evaluation_score=rel.get("evaluation_score", 98.0),
                        deployed_by=rel.get("deployed_by", "developer@glgassets.com"),
                        can_rollback=rel.get("can_rollback", True),
                        previous_release_tag=rel.get("previous_release_tag")
                    ))

                # 10. Seed Approvals
                for appr in INITIAL_SEEDS["approvals"]:
                    session.add(AIApprovalRequestRecord(
                        id=appr["id"],
                        agent_id=appr["agent_id"],
                        action_type=appr["action_type"],
                        risk_level=appr.get("risk_level", "HIGH"),
                        reason=appr["reason"],
                        context_data=appr.get("context_data", {}),
                        generated_content=appr["generated_content"],
                        status=appr.get("status", "PENDING")
                    ))

                # 11. Seed Incidents
                for inc in INITIAL_SEEDS["incidents"]:
                    session.add(AIIncidentRecord(
                        id=inc["id"],
                        incident_number=inc["incident_number"],
                        title=inc["title"],
                        severity=inc.get("severity", "P2"),
                        incident_type=inc.get("incident_type", "provider_outage"),
                        status=inc.get("status", "OPEN"),
                        agent_id=inc.get("agent_id"),
                        model_id=inc.get("model_id"),
                        owner=inc.get("owner", "developer@glgassets.com"),
                        root_cause=inc.get("root_cause"),
                        resolution=inc.get("resolution"),
                        timeline=inc.get("timeline", [])
                    ))

                # 12. Seed Traces
                for trc in INITIAL_SEEDS["traces"]:
                    session.add(AITraceRecord(
                        id=trc["id"],
                        trace_id=trc["trace_id"],
                        run_id=trc["run_id"],
                        agent_id=trc["agent_id"],
                        channel=trc.get("channel", "playground"),
                        environment=trc.get("environment", "production"),
                        user_query=trc["user_query"],
                        agent_response=trc["agent_response"],
                        model_used=trc["model_used"],
                        prompt_version=trc.get("prompt_version", "v1.0"),
                        status=trc.get("status", "SUCCESS"),
                        total_tokens=trc.get("total_tokens", 0),
                        prompt_tokens=trc.get("prompt_tokens", 0),
                        completion_tokens=trc.get("completion_tokens", 0),
                        cached_tokens=trc.get("cached_tokens", 0),
                        latency_ms=trc.get("latency_ms", 0.0),
                        cost_usd=trc.get("cost_usd", 0.0),
                        cost_bdt=trc.get("cost_bdt", 0.0),
                        spans=trc.get("spans", []),
                        guardrail_actions=trc.get("guardrail_actions", []),
                        tool_calls=trc.get("tool_calls", []),
                        rag_retrievals=trc.get("rag_retrievals", [])
                    ))

                # 13. Seed Audit Logs
                for aud in INITIAL_SEEDS["audit_logs"]:
                    session.add(AIAuditLogRecord(
                        id=aud["id"],
                        event_type=aud["event_type"],
                        actor_email=aud.get("actor_email", "developer@glgassets.com"),
                        actor_role=aud.get("actor_role", "developer"),
                        entity_type=aud["entity_type"],
                        entity_id=aud["entity_id"],
                        action=aud["action"],
                        reason=aud.get("reason")
                    ))

                await session.commit()
                self._db_initialized = True
                logger.info("[AIControlPlaneStore] PostgreSQL successfully seeded.")
            except Exception as e:
                await session.rollback()
                logger.warning(f"[AIControlPlaneStore] DB seed notice: {e}")

    # ── 1. Agents ──

    async def get_agents(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIAgentRecord).order_by(AIAgentRecord.name.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = []
                        for r in rows:
                            d = {
                                "id": r.id,
                                "slug": r.slug,
                                "name": r.name,
                                "description": r.description,
                                "role": r.role,
                                "objective": r.objective,
                                "owner": r.owner,
                                "status": r.status,
                                "environment": r.environment,
                                "primary_model": r.primary_model,
                                "fallback_model": r.fallback_model,
                                "current_prompt_version": r.current_prompt_version,
                                "temperature": r.temperature,
                                "top_p": r.top_p,
                                "max_tokens": r.max_tokens,
                                "presence_penalty": r.presence_penalty,
                                "frequency_penalty": r.frequency_penalty,
                                "persona_preset": r.persona_preset,
                                "enabled_tools": r.enabled_tools or [],
                                "rag_config": r.rag_config or {},
                                "memory_config": r.memory_config or {},
                                "guardrail_policy_ids": r.guardrail_policy_ids or [],
                                "human_approval_policy": r.human_approval_policy,
                                "max_execution_steps": r.max_execution_steps,
                                "timeout_seconds": r.timeout_seconds,
                                "created_at": r.created_at.isoformat() if r.created_at else utc_iso(),
                                "updated_at": r.updated_at.isoformat() if r.updated_at else utc_iso(),
                            }
                            result.append(d)
                        self._memory_cache["agents"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching agents from DB: {e}")

        return list(self._memory_cache.get("agents", []))

    async def get_agent_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        agents = await self.get_agents()
        for a in agents:
            if a.get("slug") == slug:
                return a
        return None

    async def save_agent(self, agent_data: Dict[str, Any], actor_email: str = "developer@glgassets.com") -> Dict[str, Any]:
        slug = agent_data.get("slug")
        if not slug:
            raise ValueError("Agent slug is required")

        session_cm = await self._get_db_session()
        persisted = None

        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIAgentRecord).where(AIAgentRecord.slug == slug)
                    res = await session.execute(stmt)
                    record = res.scalar_one_or_none()

                    action = "UPDATE" if record else "CREATE"
                    before_state = None

                    if record:
                        before_state = {
                            "slug": record.slug,
                            "name": record.name,
                            "temperature": record.temperature,
                            "primary_model": record.primary_model,
                            "current_prompt_version": record.current_prompt_version
                        }
                        for k, v in agent_data.items():
                            if hasattr(record, k) and k not in ("id", "slug", "created_at"):
                                setattr(record, k, v)
                        record.updated_at = datetime.now(timezone.utc)
                    else:
                        record = AIAgentRecord(
                            id=agent_data.get("id", str(uuid4())),
                            slug=slug,
                            name=agent_data.get("name", slug),
                            description=agent_data.get("description"),
                            role=agent_data.get("role", "assistant"),
                            objective=agent_data.get("objective"),
                            owner=agent_data.get("owner", actor_email),
                            status=agent_data.get("status", "PRODUCTION"),
                            environment=agent_data.get("environment", "production"),
                            primary_model=agent_data.get("primary_model", "llama-3.3-70b-versatile"),
                            fallback_model=agent_data.get("fallback_model"),
                            current_prompt_version=agent_data.get("current_prompt_version", "v1.0"),
                            temperature=agent_data.get("temperature", 0.2),
                            top_p=agent_data.get("top_p", 0.9),
                            max_tokens=agent_data.get("max_tokens", 1024),
                            persona_preset=agent_data.get("persona_preset", "Consultative Luxury"),
                            enabled_tools=agent_data.get("enabled_tools", []),
                            rag_config=agent_data.get("rag_config", {}),
                            memory_config=agent_data.get("memory_config", {}),
                            guardrail_policy_ids=agent_data.get("guardrail_policy_ids", []),
                            human_approval_policy=agent_data.get("human_approval_policy", "NONE"),
                            max_execution_steps=agent_data.get("max_execution_steps", 5),
                            timeout_seconds=agent_data.get("timeout_seconds", 30)
                        )
                        session.add(record)

                    await session.commit()
                    await session.refresh(record)

                    persisted = {
                        "id": record.id,
                        "slug": record.slug,
                        "name": record.name,
                        "description": record.description,
                        "role": record.role,
                        "objective": record.objective,
                        "owner": record.owner,
                        "status": record.status,
                        "environment": record.environment,
                        "primary_model": record.primary_model,
                        "fallback_model": record.fallback_model,
                        "current_prompt_version": record.current_prompt_version,
                        "temperature": record.temperature,
                        "top_p": record.top_p,
                        "max_tokens": record.max_tokens,
                        "persona_preset": record.persona_preset,
                        "enabled_tools": record.enabled_tools or [],
                        "rag_config": record.rag_config or {},
                        "memory_config": record.memory_config or {},
                        "guardrail_policy_ids": record.guardrail_policy_ids or [],
                        "human_approval_policy": record.human_approval_policy,
                        "max_execution_steps": record.max_execution_steps,
                        "timeout_seconds": record.timeout_seconds,
                        "created_at": record.created_at.isoformat() if record.created_at else utc_iso(),
                        "updated_at": record.updated_at.isoformat() if record.updated_at else utc_iso(),
                    }

                    # Log audit event in DB
                    audit_entry = AIAuditLogRecord(
                        id=f"audit-{uuid4().hex[:8]}",
                        event_type="AGENT_CONFIG_SAVED",
                        actor_email=actor_email,
                        actor_role="developer",
                        entity_type="ai_agent",
                        entity_id=slug,
                        action=action,
                        before_state=before_state,
                        after_state={"name": record.name, "primary_model": record.primary_model, "version": record.current_prompt_version},
                        reason=f"Agent '{record.name}' updated by {actor_email}"
                    )
                    session.add(audit_entry)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error persisting agent to DB: {e}")

        # Sync memory cache
        async with self._lock:
            agents = self._memory_cache.setdefault("agents", [])
            idx = next((i for i, a in enumerate(agents) if a.get("slug") == slug), None)
            if persisted:
                if idx is not None:
                    agents[idx] = persisted
                else:
                    agents.append(persisted)
                res = persisted
            else:
                updated = {
                    "id": str(uuid4()),
                    "created_at": utc_iso(),
                    "updated_at": utc_iso(),
                    **agent_data
                }
                if idx is not None:
                    agents[idx] = {**agents[idx], **updated}
                    res = agents[idx]
                else:
                    agents.append(updated)
                    res = updated
            return res

    async def get_agent_versions(self, agent_slug: str) -> List[Dict[str, Any]]:
        """Fetch historical snapshots of an agent for rollback."""
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = (
                        select(AIAgentVersionRecord)
                        .join(AIAgentRecord, AIAgentVersionRecord.agent_id == AIAgentRecord.id)
                        .where(AIAgentRecord.slug == agent_slug)
                        .order_by(AIAgentVersionRecord.created_at.desc())
                    )
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    return [
                        {
                            "id": r.id,
                            "agent_id": r.agent_id,
                            "version_tag": r.version_tag,
                            "snapshot": r.snapshot,
                            "changelog": r.changelog,
                            "created_by": r.created_by,
                            "created_at": r.created_at.isoformat() if r.created_at else utc_iso()
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.warning(f"Error fetching agent versions from DB: {e}")

        # Fallback memory
        agent = await self.get_agent_by_slug(agent_slug)
        if not agent:
            return []
        return [
            {
                "id": "ver-init-001",
                "agent_id": agent.get("id"),
                "version_tag": agent.get("current_prompt_version", "v1.0"),
                "snapshot": agent,
                "changelog": "Baseline initial version",
                "created_by": "developer@glgassets.com",
                "created_at": agent.get("created_at", utc_iso())
            }
        ]

    async def save_agent_version(self, agent_slug: str, version_tag: str, snapshot: Dict[str, Any], changelog: str, actor_email: str) -> Dict[str, Any]:
        agent = await self.get_agent_by_slug(agent_slug)
        agent_id = agent.get("id") if agent else agent_slug

        session_cm = await self._get_db_session()
        new_version_record = {
            "id": f"ver-{uuid4().hex[:8]}",
            "agent_id": agent_id,
            "version_tag": version_tag,
            "snapshot": snapshot,
            "changelog": changelog,
            "created_by": actor_email,
            "created_at": utc_iso()
        }

        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIAgentVersionRecord(
                        id=new_version_record["id"],
                        agent_id=agent_id,
                        version_tag=version_tag,
                        snapshot=snapshot,
                        changelog=changelog,
                        created_by=actor_email
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error persisting agent version: {e}")

        return new_version_record

    # ── 2. Providers & Models ──

    async def get_providers(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIProviderRecord).order_by(AIProviderRecord.display_name.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "provider_key": r.provider_key,
                                "display_name": r.display_name,
                                "base_url": r.base_url,
                                "is_active": r.is_active,
                                "health_status": r.health_status,
                                "last_ping_ms": r.last_ping_ms,
                                "last_checked_at": r.last_checked_at.isoformat() if r.last_checked_at else None,
                                "capabilities": r.capabilities or [],
                                "rate_limit_rpm": r.rate_limit_rpm,
                                "rate_limit_tpm": r.rate_limit_tpm
                            }
                            for r in rows
                        ]
                        self._memory_cache["providers"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error querying providers: {e}")

        return list(self._memory_cache.get("providers", []))

    async def update_provider_ping(self, provider_key: str, latency_ms: float, status: str = "HEALTHY"):
        session_cm = await self._get_db_session()
        now = datetime.now(timezone.utc)
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = (
                        update(AIProviderRecord)
                        .where(AIProviderRecord.provider_key == provider_key)
                        .values(
                            last_ping_ms=round(latency_ms, 1),
                            health_status=status,
                            last_checked_at=now
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error updating provider ping: {e}")

        async with self._lock:
            for p in self._memory_cache.get("providers", []):
                if p.get("provider_key") == provider_key:
                    p["last_ping_ms"] = round(latency_ms, 1)
                    p["health_status"] = status
                    p["last_checked_at"] = now.isoformat()

    async def get_models(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIModelRecord).order_by(AIModelRecord.display_name.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "model_id": r.model_id,
                                "provider_id": r.provider_id,
                                "display_name": r.display_name,
                                "model_type": r.model_type,
                                "context_window": r.context_window,
                                "max_output_tokens": r.max_output_tokens,
                                "input_cost_per_m": r.input_cost_per_m,
                                "output_cost_per_m": r.output_cost_per_m,
                                "cached_cost_per_m": r.cached_cost_per_m,
                                "supports_structured_output": r.supports_structured_output,
                                "supports_tools": r.supports_tools,
                                "supports_streaming": r.supports_streaming,
                                "status": r.status,
                                "benchmark_scores": r.benchmark_scores or {},
                                "is_enabled": r.is_enabled
                            }
                            for r in rows
                        ]
                        self._memory_cache["models"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching models: {e}")

        return list(self._memory_cache.get("models", []))

    async def save_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        model_id = model_data.get("model_id")
        session_cm = await self._get_db_session()
        if session_cm and model_id:
            try:
                async with session_cm as session:
                    stmt = select(AIModelRecord).where(AIModelRecord.model_id == model_id)
                    res = await session.execute(stmt)
                    rec = res.scalar_one_or_none()
                    if rec:
                        for k, v in model_data.items():
                            if hasattr(rec, k) and k not in ("id", "model_id"):
                                setattr(rec, k, v)
                    else:
                        rec = AIModelRecord(
                            id=str(uuid4()),
                            model_id=model_id,
                            provider_id=model_data.get("provider_id", "prov-groq"),
                            display_name=model_data.get("display_name", model_id),
                            model_type=model_data.get("model_type", "BASE"),
                            context_window=model_data.get("context_window", 131072),
                            max_output_tokens=model_data.get("max_output_tokens", 4096),
                            input_cost_per_m=model_data.get("input_cost_per_m", 0.59),
                            output_cost_per_m=model_data.get("output_cost_per_m", 0.79),
                            cached_cost_per_m=model_data.get("cached_cost_per_m", 0.30),
                            is_enabled=model_data.get("is_enabled", True)
                        )
                        session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error saving model: {e}")

        async with self._lock:
            models = self._memory_cache.setdefault("models", [])
            idx = next((i for i, m in enumerate(models) if m.get("model_id") == model_id), None)
            if idx is not None:
                models[idx] = {**models[idx], **model_data}
                return models[idx]
            else:
                new_m = {"id": str(uuid4()), **model_data}
                models.append(new_m)
                return new_m

    # ── 3. Tools ──

    async def get_tools(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIToolRecord).order_by(AIToolRecord.name.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "tool_key": r.tool_key,
                                "name": r.name,
                                "description": r.description,
                                "category": r.category,
                                "parameters_schema": r.parameters_schema or {},
                                "output_schema": r.output_schema,
                                "requires_approval": r.requires_approval,
                                "risk_level": r.risk_level,
                                "timeout_ms": r.timeout_ms,
                                "is_enabled": r.is_enabled,
                                "assigned_agents": r.assigned_agents or []
                            }
                            for r in rows
                        ]
                        self._memory_cache["tools"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching tools: {e}")

        return list(self._memory_cache.get("tools", []))

    async def save_tool(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        tool_key = tool_data.get("tool_key")
        session_cm = await self._get_db_session()
        if session_cm and tool_key:
            try:
                async with session_cm as session:
                    stmt = select(AIToolRecord).where(AIToolRecord.tool_key == tool_key)
                    res = await session.execute(stmt)
                    rec = res.scalar_one_or_none()
                    if rec:
                        for k, v in tool_data.items():
                            if hasattr(rec, k) and k not in ("id", "tool_key"):
                                setattr(rec, k, v)
                    else:
                        rec = AIToolRecord(
                            id=str(uuid4()),
                            tool_key=tool_key,
                            name=tool_data.get("name", tool_key),
                            description=tool_data.get("description", ""),
                            category=tool_data.get("category", "data_retrieval"),
                            parameters_schema=tool_data.get("parameters_schema", {}),
                            requires_approval=tool_data.get("requires_approval", False),
                            risk_level=tool_data.get("risk_level", "LOW"),
                            timeout_ms=tool_data.get("timeout_ms", 5000),
                            is_enabled=tool_data.get("is_enabled", True),
                            assigned_agents=tool_data.get("assigned_agents", [])
                        )
                        session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error saving tool: {e}")

        async with self._lock:
            tools = self._memory_cache.setdefault("tools", [])
            idx = next((i for i, t in enumerate(tools) if t.get("tool_key") == tool_key), None)
            if idx is not None:
                tools[idx] = {**tools[idx], **tool_data}
                return tools[idx]
            else:
                new_t = {"id": str(uuid4()), **tool_data}
                tools.append(new_t)
                return new_t

    # ── 4. Routing Rules ──

    async def get_routing_rules(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIRoutingRuleRecord).order_by(AIRoutingRuleRecord.priority.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "priority": r.priority,
                                "name": r.name,
                                "condition_task": r.condition_task,
                                "condition_complexity": r.condition_complexity,
                                "condition_agent": r.condition_agent,
                                "target_model_id": r.target_model_id,
                                "fallback_model_id": r.fallback_model_id,
                                "strategy": r.strategy,
                                "is_active": r.is_active
                            }
                            for r in rows
                        ]
                        self._memory_cache["routing_rules"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching routing rules: {e}")

        return list(self._memory_cache.get("routing_rules", []))

    async def save_routing_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        rule_id = rule.get("id") or str(uuid4())
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIRoutingRuleRecord).where(AIRoutingRuleRecord.id == rule_id)
                    res = await session.execute(stmt)
                    rec = res.scalar_one_or_none()
                    if rec:
                        for k, v in rule.items():
                            if hasattr(rec, k) and k != "id":
                                setattr(rec, k, v)
                    else:
                        rec = AIRoutingRuleRecord(
                            id=rule_id,
                            priority=rule.get("priority", 100),
                            name=rule.get("name", "New Routing Rule"),
                            condition_task=rule.get("condition_task"),
                            condition_complexity=rule.get("condition_complexity"),
                            condition_agent=rule.get("condition_agent"),
                            target_model_id=rule.get("target_model_id", "llama-3.3-70b-versatile"),
                            fallback_model_id=rule.get("fallback_model_id"),
                            strategy=rule.get("strategy", "RULE_BASED"),
                            is_active=rule.get("is_active", True)
                        )
                        session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error saving routing rule: {e}")

        async with self._lock:
            rules = self._memory_cache.setdefault("routing_rules", [])
            idx = next((i for i, r in enumerate(rules) if r.get("id") == rule_id), None)
            if idx is not None:
                rules[idx] = {**rules[idx], **rule, "id": rule_id}
                return rules[idx]
            else:
                new_r = {**rule, "id": rule_id}
                rules.append(new_r)
                return new_r

    # ── 5. Guardrails ──

    async def get_guardrails(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIGuardrailPolicyRecord).order_by(AIGuardrailPolicyRecord.severity.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "category": r.category,
                                "rule_name": r.rule_name,
                                "description": r.description,
                                "action": r.action,
                                "severity": r.severity,
                                "rule_parameters": r.rule_parameters or {},
                                "is_enabled": r.is_enabled,
                                "total_triggers": r.total_triggers
                            }
                            for r in rows
                        ]
                        self._memory_cache["guardrails"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching guardrails: {e}")

        return list(self._memory_cache.get("guardrails", []))

    async def save_guardrail(self, guardrail_data: Dict[str, Any]) -> Dict[str, Any]:
        rule_id = guardrail_data.get("id") or f"gr-{uuid4().hex[:6]}"
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIGuardrailPolicyRecord).where(AIGuardrailPolicyRecord.id == rule_id)
                    res = await session.execute(stmt)
                    rec = res.scalar_one_or_none()
                    if rec:
                        for k, v in guardrail_data.items():
                            if hasattr(rec, k) and k != "id":
                                setattr(rec, k, v)
                    else:
                        rec = AIGuardrailPolicyRecord(
                            id=rule_id,
                            category=guardrail_data.get("category", "SAFETY"),
                            rule_name=guardrail_data.get("rule_name", "Policy"),
                            description=guardrail_data.get("description", ""),
                            action=guardrail_data.get("action", "BLOCK"),
                            severity=guardrail_data.get("severity", "HIGH"),
                            rule_parameters=guardrail_data.get("rule_parameters", {}),
                            is_enabled=guardrail_data.get("is_enabled", True),
                            total_triggers=guardrail_data.get("total_triggers", 0)
                        )
                        session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error saving guardrail: {e}")

        async with self._lock:
            grs = self._memory_cache.setdefault("guardrails", [])
            idx = next((i for i, g in enumerate(grs) if g.get("id") == rule_id), None)
            if idx is not None:
                grs[idx] = {**grs[idx], **guardrail_data, "id": rule_id}
                return grs[idx]
            else:
                new_g = {**guardrail_data, "id": rule_id}
                grs.append(new_g)
                return new_g

    async def record_guardrail_trigger(self, policy_id: str):
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = (
                        update(AIGuardrailPolicyRecord)
                        .where(AIGuardrailPolicyRecord.id == policy_id)
                        .values(total_triggers=AIGuardrailPolicyRecord.total_triggers + 1)
                    )
                    await session.execute(stmt)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error recording guardrail trigger in DB: {e}")

        async with self._lock:
            for g in self._memory_cache.get("guardrails", []):
                if g.get("id") == policy_id:
                    g["total_triggers"] = g.get("total_triggers", 0) + 1

    async def record_guardrail_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        event_id = f"gre-{uuid4().hex[:8]}"
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIGuardrailEventRecord(
                        id=event_id,
                        policy_id=event_data["policy_id"],
                        agent_id=event_data.get("agent_id", "property_agent"),
                        trace_id=event_data.get("trace_id"),
                        action_taken=event_data.get("action_taken", "BLOCK"),
                        violation_type=event_data.get("violation_type", "SAFETY_VIOLATION"),
                        raw_input_snippet=event_data.get("raw_input_snippet", "")[:1000],
                        sanitized_output_snippet=event_data.get("sanitized_output_snippet")
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error recording guardrail event: {e}")

        return {"id": event_id, **event_data, "timestamp": utc_iso()}

    # ── 6. Evaluations ──

    async def get_evaluations(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIEvaluationRunRecord).order_by(AIEvaluationRunRecord.created_at.desc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "suite_name": r.suite_name,
                                "dataset_id": r.dataset_id,
                                "agent_id": r.agent_id,
                                "model_tested": r.model_tested,
                                "prompt_version": r.prompt_version,
                                "total_cases": r.total_cases,
                                "passed_cases": r.passed_cases,
                                "failed_cases": r.failed_cases,
                                "accuracy_pct": r.accuracy_pct,
                                "groundedness_pct": r.groundedness_pct,
                                "hallucination_pct": r.hallucination_pct,
                                "tool_accuracy_pct": r.tool_accuracy_pct,
                                "schema_correctness_pct": r.schema_correctness_pct,
                                "avg_latency_ms": r.avg_latency_ms,
                                "status": r.status,
                                "gate_verdict": r.gate_verdict,
                                "report_data": r.report_data or {},
                                "created_by": r.created_by,
                                "created_at": r.created_at.isoformat() if r.created_at else utc_iso()
                            }
                            for r in rows
                        ]
                        self._memory_cache["evaluations"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching evaluations: {e}")

        return list(self._memory_cache.get("evaluations", []))

    async def record_evaluation(self, eval_data: Dict[str, Any]) -> Dict[str, Any]:
        eval_id = eval_data.get("id") or f"eval-{uuid4().hex[:6]}"
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIEvaluationRunRecord(
                        id=eval_id,
                        suite_name=eval_data.get("suite_name", "Evaluation Suite"),
                        dataset_id=eval_data.get("dataset_id", "ds-eval-001"),
                        agent_id=eval_data.get("agent_id", "property_agent"),
                        model_tested=eval_data.get("model_tested", "llama-3.3-70b-versatile"),
                        prompt_version=eval_data.get("prompt_version", "v1.0"),
                        total_cases=eval_data.get("total_cases", 0),
                        passed_cases=eval_data.get("passed_cases", 0),
                        failed_cases=eval_data.get("failed_cases", 0),
                        accuracy_pct=eval_data.get("accuracy_pct", 0.0),
                        groundedness_pct=eval_data.get("groundedness_pct", 0.0),
                        hallucination_pct=eval_data.get("hallucination_pct", 0.0),
                        tool_accuracy_pct=eval_data.get("tool_accuracy_pct", 0.0),
                        schema_correctness_pct=eval_data.get("schema_correctness_pct", 100.0),
                        avg_latency_ms=eval_data.get("avg_latency_ms", 0.0),
                        status=eval_data.get("status", "COMPLETED"),
                        gate_verdict=eval_data.get("gate_verdict", "PASS"),
                        report_data=eval_data.get("report_data", {}),
                        created_by=eval_data.get("created_by", "developer@glgassets.com")
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error persisting evaluation run: {e}")

        saved = {**eval_data, "id": eval_id, "created_at": utc_iso()}
        async with self._lock:
            self._memory_cache.setdefault("evaluations", []).insert(0, saved)
        return saved

    # ── 7. Datasets & Examples ──

    async def get_datasets(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIDatasetRecord).order_by(AIDatasetRecord.name.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "slug": r.slug,
                                "name": r.name,
                                "dataset_type": r.dataset_type,
                                "target_agent": r.target_agent,
                                "version": r.version,
                                "total_examples": r.total_examples,
                                "quality_score": r.quality_score,
                                "train_count": r.train_count,
                                "val_count": r.val_count,
                                "test_count": r.test_count,
                                "is_locked": r.is_locked,
                                "created_by": r.created_by,
                                "created_at": r.created_at.isoformat() if r.created_at else utc_iso()
                            }
                            for r in rows
                        ]
                        self._memory_cache["datasets"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching datasets: {e}")

        return list(self._memory_cache.get("datasets", []))

    async def get_dataset_examples(self, dataset_id: str) -> List[Dict[str, Any]]:
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIDatasetExampleRecord).where(
                        or_(AIDatasetExampleRecord.dataset_id == dataset_id)
                    ).order_by(AIDatasetExampleRecord.created_at.asc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        return [
                            {
                                "id": r.id,
                                "dataset_id": r.dataset_id,
                                "split": r.split,
                                "input_message": r.input_message,
                                "expected_intent": r.expected_intent,
                                "expected_output": r.expected_output,
                                "expected_tools": r.expected_tools or [],
                                "expected_facts": r.expected_facts or [],
                                "metadata_tags": r.metadata_tags or {}
                            }
                            for r in rows
                        ]
            except Exception as e:
                logger.warning(f"Error fetching dataset examples: {e}")

        # Fallback memory
        return [ex for ex in self._memory_cache.get("dataset_examples", []) if ex.get("dataset_id") == dataset_id]

    async def save_dataset_example(self, example_data: Dict[str, Any]) -> Dict[str, Any]:
        ex_id = example_data.get("id") or f"ex-{uuid4().hex[:6]}"
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIDatasetExampleRecord(
                        id=ex_id,
                        dataset_id=example_data["dataset_id"],
                        split=example_data.get("split", "test"),
                        input_message=example_data["input_message"],
                        expected_intent=example_data.get("expected_intent"),
                        expected_output=example_data["expected_output"],
                        expected_tools=example_data.get("expected_tools", []),
                        expected_facts=example_data.get("expected_facts", []),
                        metadata_tags=example_data.get("metadata_tags", {})
                    )
                    session.add(rec)
                    # update dataset count
                    await session.execute(
                        update(AIDatasetRecord)
                        .where(AIDatasetRecord.id == example_data["dataset_id"])
                        .values(total_examples=AIDatasetRecord.total_examples + 1)
                    )
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error saving dataset example: {e}")

        saved = {**example_data, "id": ex_id}
        self._memory_cache.setdefault("dataset_examples", []).append(saved)
        return saved

    # ── 8. Releases ──

    async def get_releases(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIReleaseRecord).order_by(AIReleaseRecord.created_at.desc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "release_tag": r.release_tag,
                                "title": r.title,
                                "description": r.description,
                                "environment": r.environment,
                                "manifest": r.manifest or {},
                                "evaluation_gate_passed": r.evaluation_gate_passed,
                                "evaluation_score": r.evaluation_score,
                                "deployed_by": r.deployed_by,
                                "deployed_at": r.deployed_at.isoformat() if r.deployed_at else None,
                                "can_rollback": r.can_rollback,
                                "previous_release_tag": r.previous_release_tag,
                                "created_at": r.created_at.isoformat() if r.created_at else utc_iso()
                            }
                            for r in rows
                        ]
                        self._memory_cache["releases"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching releases: {e}")

        return list(self._memory_cache.get("releases", []))

    async def create_release(self, release_data: Dict[str, Any], actor_email: str = "developer@glgassets.com") -> Dict[str, Any]:
        rel_id = f"rel-{uuid4().hex[:6]}"
        new_rel = {
            "id": rel_id,
            "created_at": utc_iso(),
            "deployed_by": actor_email,
            **release_data
        }
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIReleaseRecord(
                        id=rel_id,
                        release_tag=release_data["release_tag"],
                        title=release_data["title"],
                        description=release_data.get("description"),
                        environment=release_data.get("environment", "STAGING"),
                        manifest=release_data.get("manifest", {}),
                        evaluation_gate_passed=release_data.get("evaluation_gate_passed", True),
                        evaluation_score=release_data.get("evaluation_score", 98.0),
                        deployed_by=actor_email,
                        can_rollback=release_data.get("can_rollback", True),
                        previous_release_tag=release_data.get("previous_release_tag")
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error creating release: {e}")

        await self.record_audit_log(
            event_type="RELEASE_CREATED",
            actor_email=actor_email,
            entity_type="ai_release",
            entity_id=new_rel["release_tag"],
            action="CREATE",
            reason=f"Release {new_rel['release_tag']} created for {new_rel.get('environment')}."
        )
        self._memory_cache.setdefault("releases", []).insert(0, new_rel)
        return new_rel

    async def deploy_release(self, release_tag: str, actor_email: str = "developer@glgassets.com") -> Dict[str, Any]:
        session_cm = await self._get_db_session()
        now = datetime.now(timezone.utc)
        target = None

        if session_cm:
            try:
                async with session_cm as session:
                    # Archive current production
                    await session.execute(
                        update(AIReleaseRecord)
                        .where(AIReleaseRecord.environment == "PRODUCTION")
                        .values(environment="ARCHIVED")
                    )
                    # Promote target
                    stmt = (
                        update(AIReleaseRecord)
                        .where(AIReleaseRecord.release_tag == release_tag)
                        .values(
                            environment="PRODUCTION",
                            deployed_at=now,
                            deployed_by=actor_email
                        )
                    )
                    await session.execute(stmt)
                    await session.commit()

                    stmt_fetch = select(AIReleaseRecord).where(AIReleaseRecord.release_tag == release_tag)
                    res = await session.execute(stmt_fetch)
                    r = res.scalar_one_or_none()
                    if r:
                        target = {
                            "id": r.id,
                            "release_tag": r.release_tag,
                            "title": r.title,
                            "description": r.description,
                            "environment": "PRODUCTION",
                            "manifest": r.manifest or {},
                            "deployed_at": now.isoformat(),
                            "deployed_by": actor_email
                        }
            except Exception as e:
                logger.warning(f"Error deploying release in DB: {e}")

        if not target:
            releases = self._memory_cache.setdefault("releases", [])
            for r in releases:
                if r.get("environment") == "PRODUCTION":
                    r["environment"] = "ARCHIVED"
                if r.get("release_tag") == release_tag:
                    r["environment"] = "PRODUCTION"
                    r["deployed_at"] = now.isoformat()
                    r["deployed_by"] = actor_email
                    target = r

        await self.record_audit_log(
            event_type="RELEASE_DEPLOYED",
            actor_email=actor_email,
            entity_type="ai_release",
            entity_id=release_tag,
            action="DEPLOY",
            reason=f"Release {release_tag} promoted to PRODUCTION."
        )
        return target or {"release_tag": release_tag, "environment": "PRODUCTION"}

    async def rollback_release(self, target_release_tag: str, actor_email: str = "developer@glgassets.com") -> Dict[str, Any]:
        return await self.deploy_release(target_release_tag, actor_email=actor_email)

    # ── 9. Traces ──

    async def get_traces(self, limit: int = 50, agent_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AITraceRecord)
                    if agent_filter and agent_filter != "all":
                        stmt = stmt.where(AITraceRecord.agent_id == agent_filter)
                    stmt = stmt.order_by(AITraceRecord.timestamp.desc()).limit(limit)
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "trace_id": r.trace_id,
                                "run_id": r.run_id,
                                "agent_id": r.agent_id,
                                "channel": r.channel,
                                "environment": r.environment,
                                "user_query": r.user_query,
                                "agent_response": r.agent_response,
                                "model_used": r.model_used,
                                "prompt_version": r.prompt_version,
                                "status": r.status,
                                "total_tokens": r.total_tokens,
                                "prompt_tokens": r.prompt_tokens,
                                "completion_tokens": r.completion_tokens,
                                "cached_tokens": r.cached_tokens,
                                "latency_ms": r.latency_ms,
                                "cost_usd": r.cost_usd,
                                "cost_bdt": r.cost_bdt,
                                "spans": r.spans or [],
                                "guardrail_actions": r.guardrail_actions or [],
                                "tool_calls": r.tool_calls or [],
                                "rag_retrievals": r.rag_retrievals or [],
                                "timestamp": r.timestamp.isoformat() if r.timestamp else utc_iso()
                            }
                            for r in rows
                        ]
                        return result
            except Exception as e:
                logger.warning(f"Error fetching traces: {e}")

        traces = self._memory_cache.setdefault("traces", [])
        if agent_filter and agent_filter != "all":
            return [t for t in traces if t.get("agent_id") == agent_filter][:limit]
        return traces[:limit]

    async def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        traces = await self.get_traces(limit=200)
        for t in traces:
            if t.get("trace_id") == trace_id or t.get("id") == trace_id:
                return t
        return None

    async def record_trace(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        trace_id = trace_data.get("trace_id") or f"trc-{uuid4().hex[:12]}"
        run_id = trace_data.get("run_id") or f"run-{uuid4().hex[:8]}"
        session_cm = await self._get_db_session()

        if session_cm:
            try:
                async with session_cm as session:
                    rec = AITraceRecord(
                        id=f"trc-{uuid4().hex[:8]}",
                        trace_id=trace_id,
                        run_id=run_id,
                        agent_id=trace_data.get("agent_id", "property_agent"),
                        conversation_id=trace_data.get("conversation_id"),
                        channel=trace_data.get("channel", "playground"),
                        environment=trace_data.get("environment", "production"),
                        user_query=trace_data.get("user_query", ""),
                        agent_response=trace_data.get("agent_response", ""),
                        model_used=trace_data.get("model_used", "llama-3.3-70b-versatile"),
                        prompt_version=trace_data.get("prompt_version", "v1.0"),
                        status=trace_data.get("status", "SUCCESS"),
                        total_tokens=trace_data.get("total_tokens", 0),
                        prompt_tokens=trace_data.get("prompt_tokens", 0),
                        completion_tokens=trace_data.get("completion_tokens", 0),
                        cached_tokens=trace_data.get("cached_tokens", 0),
                        latency_ms=trace_data.get("latency_ms", 0.0),
                        cost_usd=trace_data.get("cost_usd", 0.0),
                        cost_bdt=trace_data.get("cost_bdt", 0.0),
                        spans=trace_data.get("spans", []),
                        guardrail_actions=trace_data.get("guardrail_actions", []),
                        tool_calls=trace_data.get("tool_calls", []),
                        rag_retrievals=trace_data.get("rag_retrievals", [])
                    )
                    session.add(rec)

                    # Accumulate budget spend
                    cost = trace_data.get("cost_usd", 0.0)
                    if cost > 0:
                        await session.execute(
                            update(AIBudgetRecord)
                            .values(current_spend_usd=AIBudgetRecord.current_spend_usd + cost)
                        )

                    await session.commit()
            except Exception as e:
                logger.warning(f"Error persisting trace: {e}")

        saved = {
            "id": f"trc-{uuid4().hex[:8]}",
            "trace_id": trace_id,
            "run_id": run_id,
            "timestamp": utc_iso(),
            **trace_data
        }
        async with self._lock:
            traces = self._memory_cache.setdefault("traces", [])
            traces.insert(0, saved)
            self._memory_cache["traces"] = traces[:200]
            # Update budget
            bgt = self._memory_cache.get("budget", {})
            bgt["current_spend_usd"] = round(bgt.get("current_spend_usd", 0.0) + trace_data.get("cost_usd", 0.0), 4)

        return saved

    # ── 10. Human Approvals ──

    async def get_approval_queue(self, status: Optional[str] = "PENDING") -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIApprovalRequestRecord)
                    if status and status != "ALL":
                        stmt = stmt.where(AIApprovalRequestRecord.status == status)
                    stmt = stmt.order_by(AIApprovalRequestRecord.created_at.desc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "agent_id": r.agent_id,
                                "action_type": r.action_type,
                                "risk_level": r.risk_level,
                                "reason": r.reason,
                                "context_data": r.context_data or {},
                                "generated_content": r.generated_content,
                                "status": r.status,
                                "reviewer": r.reviewer,
                                "reviewer_notes": r.reviewer_notes,
                                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
                                "created_at": r.created_at.isoformat() if r.created_at else utc_iso()
                            }
                            for r in rows
                        ]
                        self._memory_cache["approvals"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching approvals: {e}")

        approvals = self._memory_cache.setdefault("approvals", [])
        if status and status != "ALL":
            return [a for a in approvals if a.get("status") == status]
        return approvals

    async def create_approval_request(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        appr_id = f"appr-{uuid4().hex[:6]}"
        new_appr = {
            "id": appr_id,
            "status": "PENDING",
            "created_at": utc_iso(),
            **req_data
        }
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIApprovalRequestRecord(
                        id=appr_id,
                        agent_id=req_data["agent_id"],
                        action_type=req_data["action_type"],
                        risk_level=req_data.get("risk_level", "HIGH"),
                        reason=req_data["reason"],
                        context_data=req_data.get("context_data", {}),
                        generated_content=req_data["generated_content"],
                        status="PENDING"
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error creating approval request: {e}")

        async with self._lock:
            self._memory_cache.setdefault("approvals", []).insert(0, new_appr)
        return new_appr

    async def decide_approval(
        self,
        approval_id: str,
        decision: str,
        reviewer: str = "developer@glgassets.com",
        reviewer_notes: Optional[str] = None,
        edited_content: Optional[str] = None
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        session_cm = await self._get_db_session()
        updated_item = None

        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIApprovalRequestRecord).where(AIApprovalRequestRecord.id == approval_id)
                    res = await session.execute(stmt)
                    rec = res.scalar_one_or_none()
                    if rec:
                        rec.status = decision
                        rec.reviewer = reviewer
                        rec.reviewer_notes = reviewer_notes
                        rec.reviewed_at = now
                        if edited_content:
                            rec.generated_content = edited_content
                        await session.commit()
                        updated_item = {
                            "id": rec.id,
                            "agent_id": rec.agent_id,
                            "action_type": rec.action_type,
                            "status": rec.status,
                            "reviewer": rec.reviewer,
                            "reviewed_at": now.isoformat()
                        }
            except Exception as e:
                logger.warning(f"Error deciding approval in DB: {e}")

        async with self._lock:
            for a in self._memory_cache.get("approvals", []):
                if a.get("id") == approval_id:
                    a["status"] = decision
                    a["reviewer"] = reviewer
                    a["reviewer_notes"] = reviewer_notes
                    a["reviewed_at"] = now.isoformat()
                    if edited_content:
                        a["generated_content"] = edited_content
                    updated_item = a

        await self.record_audit_log(
            event_type="APPROVAL_DECIDED",
            actor_email=reviewer,
            entity_type="ai_approval",
            entity_id=approval_id,
            action=decision,
            reason=f"Approval request {approval_id} marked as {decision} by {reviewer}"
        )
        return updated_item or {"id": approval_id, "status": decision}

    # ── 11. Incidents & Circuit Breakers ──

    async def get_incidents(self) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIIncidentRecord).order_by(AIIncidentRecord.created_at.desc())
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "incident_number": r.incident_number,
                                "title": r.title,
                                "severity": r.severity,
                                "incident_type": r.incident_type,
                                "status": r.status,
                                "agent_id": r.agent_id,
                                "model_id": r.model_id,
                                "trace_id": r.trace_id,
                                "owner": r.owner,
                                "root_cause": r.root_cause,
                                "resolution": r.resolution,
                                "timeline": r.timeline or [],
                                "created_at": r.created_at.isoformat() if r.created_at else utc_iso(),
                                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None
                            }
                            for r in rows
                        ]
                        self._memory_cache["incidents"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching incidents: {e}")

        return list(self._memory_cache.get("incidents", []))

    async def create_incident(self, inc_data: Dict[str, Any]) -> Dict[str, Any]:
        incidents = await self.get_incidents()
        inc_num = f"INC-2026-{len(incidents) + 1:03d}"
        inc_id = f"inc-{uuid4().hex[:6]}"

        new_inc = {
            "id": inc_id,
            "incident_number": inc_num,
            "status": "OPEN",
            "created_at": utc_iso(),
            "timeline": [{"timestamp": utc_iso(), "note": f"Incident {inc_num} opened: {inc_data.get('title')}"}],
            **inc_data
        }

        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIIncidentRecord(
                        id=inc_id,
                        incident_number=inc_num,
                        title=inc_data["title"],
                        severity=inc_data.get("severity", "P2"),
                        incident_type=inc_data.get("incident_type", "provider_outage"),
                        status="OPEN",
                        agent_id=inc_data.get("agent_id"),
                        model_id=inc_data.get("model_id"),
                        trace_id=inc_data.get("trace_id"),
                        owner=inc_data.get("owner", "developer@glgassets.com"),
                        root_cause=inc_data.get("root_cause"),
                        resolution=inc_data.get("resolution"),
                        timeline=new_inc["timeline"]
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error persisting incident: {e}")

        async with self._lock:
            self._memory_cache.setdefault("incidents", []).insert(0, new_inc)

        await self.record_audit_log(
            event_type="INCIDENT_OPENED",
            actor_email=inc_data.get("owner", "developer@glgassets.com"),
            entity_type="ai_incident",
            entity_id=inc_num,
            action="OPEN",
            reason=f"Incident {inc_num} opened with severity {inc_data.get('severity')}"
        )
        return new_inc

    async def update_incident_status(self, inc_id: str, new_status: str, note: Optional[str] = None) -> Dict[str, Any]:
        session_cm = await self._get_db_session()
        now = datetime.now(timezone.utc)
        target = None

        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIIncidentRecord).where(or_(AIIncidentRecord.id == inc_id, AIIncidentRecord.incident_number == inc_id))
                    res = await session.execute(stmt)
                    rec = res.scalar_one_or_none()
                    if rec:
                        rec.status = new_status
                        tl = list(rec.timeline or [])
                        if note:
                            tl.append({"timestamp": now.isoformat(), "note": note})
                        rec.timeline = tl
                        if new_status in ("RESOLVED", "CLOSED"):
                            rec.resolved_at = now
                        await session.commit()
                        target = {
                            "id": rec.id,
                            "incident_number": rec.incident_number,
                            "status": rec.status,
                            "timeline": rec.timeline
                        }
            except Exception as e:
                logger.warning(f"Error updating incident status: {e}")

        async with self._lock:
            for inc in self._memory_cache.get("incidents", []):
                if inc.get("id") == inc_id or inc.get("incident_number") == inc_id:
                    inc["status"] = new_status
                    if note:
                        inc.setdefault("timeline", []).append({"timestamp": now.isoformat(), "note": note})
                    if new_status in ("RESOLVED", "CLOSED"):
                        inc["resolved_at"] = now.isoformat()
                    target = inc

        return target or {"id": inc_id, "status": new_status}

    # ── 12. Budget ──

    async def get_budget(self) -> Dict[str, Any]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIBudgetRecord).limit(1)
                    res = await session.execute(stmt)
                    r = res.scalar_one_or_none()
                    if r:
                        result = {
                            "id": r.id,
                            "period": r.period,
                            "monthly_budget_usd": r.monthly_budget_usd,
                            "current_spend_usd": r.current_spend_usd,
                            "warn_threshold_pct": r.warn_threshold_pct,
                            "hard_stop_threshold_pct": r.hard_stop_threshold_pct,
                            "is_hard_stop_active": r.is_hard_stop_active,
                            "agent_budgets": r.agent_budgets or {}
                        }
                        self._memory_cache["budget"] = result
                        return result
            except Exception as e:
                logger.warning(f"Error fetching budget: {e}")

        return dict(self._memory_cache.get("budget", INITIAL_SEEDS["budget"]))

    async def update_budget(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIBudgetRecord).limit(1)
                    res = await session.execute(stmt)
                    rec = res.scalar_one_or_none()
                    if rec:
                        for k, v in budget_data.items():
                            if hasattr(rec, k) and k != "id":
                                setattr(rec, k, v)
                    else:
                        rec = AIBudgetRecord(
                            id="bgt-001",
                            period=budget_data.get("period", "MONTHLY"),
                            monthly_budget_usd=budget_data.get("monthly_budget_usd", 500.0),
                            current_spend_usd=budget_data.get("current_spend_usd", 0.0),
                            warn_threshold_pct=budget_data.get("warn_threshold_pct", 75.0),
                            hard_stop_threshold_pct=budget_data.get("hard_stop_threshold_pct", 100.0),
                            is_hard_stop_active=budget_data.get("is_hard_stop_active", False),
                            agent_budgets=budget_data.get("agent_budgets", {})
                        )
                        session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error updating budget in DB: {e}")

        async with self._lock:
            self._memory_cache["budget"] = {**self._memory_cache.get("budget", {}), **budget_data}
            return self._memory_cache["budget"]

    # ── 13. Audit Log ──

    async def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        await self.ensure_db_seeded()
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    stmt = select(AIAuditLogRecord).order_by(AIAuditLogRecord.created_at.desc()).limit(limit)
                    res = await session.execute(stmt)
                    rows = res.scalars().all()
                    if rows:
                        result = [
                            {
                                "id": r.id,
                                "event_type": r.event_type,
                                "actor_email": r.actor_email,
                                "actor_role": r.actor_role,
                                "entity_type": r.entity_type,
                                "entity_id": r.entity_id,
                                "action": r.action,
                                "before_state": r.before_state,
                                "after_state": r.after_state,
                                "reason": r.reason,
                                "created_at": r.created_at.isoformat() if r.created_at else utc_iso()
                            }
                            for r in rows
                        ]
                        return result
            except Exception as e:
                logger.warning(f"Error fetching audit logs: {e}")

        return list(self._memory_cache.get("audit_logs", []))[:limit]

    async def record_audit_log(
        self,
        event_type: str,
        actor_email: str,
        entity_type: str,
        entity_id: str,
        action: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        entry_id = f"audit-{uuid4().hex[:8]}"
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIAuditLogRecord(
                        id=entry_id,
                        event_type=event_type,
                        actor_email=actor_email,
                        actor_role="developer",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        action=action,
                        before_state=before_state,
                        after_state=after_state,
                        reason=reason
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"Error recording audit log in DB: {e}")

        entry = {
            "id": entry_id,
            "event_type": event_type,
            "actor_email": actor_email,
            "actor_role": "developer",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "before_state": before_state,
            "after_state": after_state,
            "reason": reason,
            "created_at": utc_iso()
        }
        async with self._lock:
            logs = self._memory_cache.setdefault("audit_logs", [])
            logs.insert(0, entry)
            self._memory_cache["audit_logs"] = logs[:500]

        return entry

    # ── 17. Fine-Tuning Jobs ─────────────────────────────────────

    async def get_fine_tune_jobs(self) -> List[Dict[str, Any]]:
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    res = await session.execute(select(AIFineTuneJobRecord).order_by(AIFineTuneJobRecord.created_at.desc()))
                    records = res.scalars().all()
                    if records:
                        return [
                            {
                                "id": r.id,
                                "job_name": r.job_name,
                                "base_model": r.base_model,
                                "dataset_id": r.dataset_id,
                                "lora_rank": r.lora_rank,
                                "epochs": r.epochs,
                                "learning_rate": r.learning_rate,
                                "status": r.status,
                                "progress_pct": r.progress_pct,
                                "current_epoch": r.current_epoch,
                                "train_loss": r.train_loss,
                                "eval_loss": r.eval_loss,
                                "output_model_id": r.output_model_id,
                                "metrics": r.metrics,
                                "training_duration_sec": r.training_duration_sec,
                                "cost_usd": r.cost_usd,
                                "cost_bdt": r.cost_bdt,
                                "error_message": r.error_message,
                                "created_by": r.created_by,
                                "started_at": r.started_at.isoformat() if r.started_at else None,
                                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                                "created_at": r.created_at.isoformat() if r.created_at else None,
                            }
                            for r in records
                        ]
            except Exception as e:
                logger.warning(f"DB error fetching fine-tuning jobs: {e}")

        return list(self._memory_cache.get("fine_tune_jobs", []))

    async def create_fine_tune_job(self, data: Dict[str, Any]) -> Dict[str, Any]:
        job_id = data.get("id") or f"ft-job-{uuid4().hex[:8]}"
        data["id"] = job_id
        if "created_at" not in data:
            data["created_at"] = utc_iso()

        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    rec = AIFineTuneJobRecord(
                        id=job_id,
                        job_name=data.get("job_name", "fine-tune-job"),
                        base_model=data.get("base_model", "llama-3.3-70b-versatile"),
                        dataset_id=data.get("dataset_id", "ds-eval-001"),
                        lora_rank=data.get("lora_rank", 16),
                        epochs=data.get("epochs", 3),
                        learning_rate=data.get("learning_rate", 2e-4),
                        status=data.get("status", "QUEUED"),
                        progress_pct=data.get("progress_pct", 0.0),
                        created_by=data.get("created_by", "developer@glgassets.com")
                    )
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.warning(f"DB error creating fine-tuning job: {e}")

        async with self._lock:
            jobs = self._memory_cache.setdefault("fine_tune_jobs", [])
            jobs.insert(0, data)

        return data

    async def update_fine_tune_job(self, job_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            jobs = self._memory_cache.setdefault("fine_tune_jobs", [])
            target = next((j for j in jobs if j.get("id") == job_id), None)
            if target:
                target.update(updates)
                return target
        return None

    # ── 18. A/B Testing Experiments ──────────────────────────────

    async def get_experiments(self) -> List[Dict[str, Any]]:
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    res = await session.execute(select(AIExperimentRecord).order_by(AIExperimentRecord.created_at.desc()))
                    records = res.scalars().all()
                    if records:
                        return [
                            {
                                "id": r.id,
                                "name": r.name,
                                "description": r.description,
                                "agent_id": r.agent_id,
                                "test_type": r.test_type,
                                "status": r.status,
                                "traffic_split_a_pct": r.traffic_split_a_pct,
                                "traffic_split_b_pct": r.traffic_split_b_pct,
                                "variant_a_config": r.variant_a_config,
                                "variant_b_config": r.variant_b_config,
                                "metrics_a": r.metrics_a,
                                "metrics_b": r.metrics_b,
                                "winner_variant": r.winner_variant,
                                "confidence_pct": r.confidence_pct,
                                "total_evaluations": r.total_evaluations,
                                "created_by": r.created_by,
                                "created_at": r.created_at.isoformat() if r.created_at else None,
                            }
                            for r in records
                        ]
            except Exception as e:
                logger.warning(f"DB error fetching experiments: {e}")

        return list(self._memory_cache.get("experiments", []))

    async def create_experiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        exp_id = data.get("id") or f"exp-{uuid4().hex[:8]}"
        data["id"] = exp_id
        if "created_at" not in data:
            data["created_at"] = utc_iso()

        async with self._lock:
            experiments = self._memory_cache.setdefault("experiments", [])
            experiments.insert(0, data)
        return data

    async def update_experiment(self, exp_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self._lock:
            experiments = self._memory_cache.setdefault("experiments", [])
            target = next((e for e in experiments if e.get("id") == exp_id), None)
            if target:
                target.update(updates)
                return target
        return None

    # ── 19. Benchmarks ───────────────────────────────────────────

    async def get_benchmarks(self) -> List[Dict[str, Any]]:
        session_cm = await self._get_db_session()
        if session_cm:
            try:
                async with session_cm as session:
                    res = await session.execute(select(AIBenchmarkRecord).order_by(AIBenchmarkRecord.created_at.desc()))
                    records = res.scalars().all()
                    if records:
                        return [
                            {
                                "id": r.id,
                                "name": r.name,
                                "category": r.category,
                                "entity_a_label": r.entity_a_label,
                                "entity_b_label": r.entity_b_label,
                                "entity_a_config": r.entity_a_config,
                                "entity_b_config": r.entity_b_config,
                                "metrics_comparison": r.metrics_comparison,
                                "scorecard": r.scorecard,
                                "winner": r.winner,
                                "executed_by": r.executed_by,
                                "created_at": r.created_at.isoformat() if r.created_at else None,
                            }
                            for r in records
                        ]
            except Exception as e:
                logger.warning(f"DB error fetching benchmarks: {e}")

        return list(self._memory_cache.get("benchmarks", []))

    async def record_benchmark(self, data: Dict[str, Any]) -> Dict[str, Any]:
        bmk_id = data.get("id") or f"bmk-{uuid4().hex[:8]}"
        data["id"] = bmk_id
        if "created_at" not in data:
            data["created_at"] = utc_iso()

        async with self._lock:
            benchmarks = self._memory_cache.setdefault("benchmarks", [])
            benchmarks.insert(0, data)
        return data

    # ── 20. Scoped Memories ──────────────────────────────────────

    async def get_memories(self, agent_id: Optional[str] = None, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        async with self._lock:
            memories = list(self._memory_cache.get("memories", []))
            if agent_id:
                memories = [m for m in memories if m.get("agent_id") == agent_id]
            if customer_id:
                memories = [m for m in memories if m.get("customer_id") == customer_id]
            return memories

    async def save_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        mem_id = data.get("id") or f"mem-{uuid4().hex[:8]}"
        data["id"] = mem_id
        if "created_at" not in data:
            data["created_at"] = utc_iso()

        async with self._lock:
            memories = self._memory_cache.setdefault("memories", [])
            existing = next((i for i, m in enumerate(memories) if m.get("id") == mem_id or (m.get("agent_id") == data.get("agent_id") and m.get("memory_key") == data.get("memory_key"))), None)
            if existing is not None:
                memories[existing] = data
            else:
                memories.insert(0, data)
        return data

    async def delete_memory(self, memory_id: str) -> bool:
        async with self._lock:
            memories = self._memory_cache.setdefault("memories", [])
            orig_len = len(memories)
            self._memory_cache["memories"] = [m for m in memories if m.get("id") != memory_id]
            return len(self._memory_cache["memories"]) < orig_len

    # ── 21. AI Configuration Snapshots ───────────────────────────

    async def get_snapshots(self, agent_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        async with self._lock:
            snapshots = list(self._memory_cache.get("snapshots", []))
            if agent_slug:
                snapshots = [s for s in snapshots if s.get("agent_slug") == agent_slug]
            return snapshots

    async def create_snapshot(self, data: Dict[str, Any]) -> Dict[str, Any]:
        snap_id = data.get("id") or f"snap-{uuid4().hex[:8]}"
        data["id"] = snap_id
        if "created_at" not in data:
            data["created_at"] = utc_iso()

        async with self._lock:
            snapshots = self._memory_cache.setdefault("snapshots", [])
            snapshots.insert(0, data)
        return data

    async def get_snapshot_by_tag(self, snapshot_tag: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            snapshots = self._memory_cache.get("snapshots", [])
            return next((s for s in snapshots if s.get("snapshot_tag") == snapshot_tag), None)

    # ── 22. Policy Engine ────────────────────────────────────────

    async def get_policies(self) -> List[Dict[str, Any]]:
        async with self._lock:
            return list(self._memory_cache.get("policies", []))

    async def save_policy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pol_id = data.get("id") or f"pol-{uuid4().hex[:8]}"
        data["id"] = pol_id
        if "created_at" not in data:
            data["created_at"] = utc_iso()

        async with self._lock:
            policies = self._memory_cache.setdefault("policies", [])
            existing = next((i for i, p in enumerate(policies) if p.get("id") == pol_id), None)
            if existing is not None:
                policies[existing] = data
            else:
                policies.insert(0, data)
        return data

    async def delete_policy(self, policy_id: str) -> bool:
        async with self._lock:
            policies = self._memory_cache.setdefault("policies", [])
            orig_len = len(policies)
            self._memory_cache["policies"] = [p for p in policies if p.get("id") != policy_id]
            return len(self._memory_cache["policies"]) < orig_len


ai_control_plane_store = AIControlPlaneStore()

