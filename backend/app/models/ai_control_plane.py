"""SQLAlchemy models for the AI & Agent Control Plane.

Implements all persistent entities required for enterprise AI agent operations:
- Agent versions, configurations, and lifecycle states
- Model gateway, providers, and capability configurations
- Prompt templates, immutable versions, and variable bindings
- Tool registry, agent assignments, and execution logs
- Workflow graphs, nodes, edges, and executions
- Memory scopes and RAG knowledge sources
- Guardrail policies, rules, and blocked violation events
- Model routing strategies and decision traces
- Datasets, examples, and fine-tuning pipelines
- Evaluation suites, benchmarks, and release quality gates
- Distributed traces, spans, and latency metrics
- Multi-currency token telemetry, budgets, and cost optimizations
- Releases, approvals, governance policies, and immutable audit logs
"""

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.models import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── 1. AI Agents & Agent Versions ────────────────────────────

class AIAgentRecord(Base):
    __tablename__ = "ai_agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(64), default="assistant")
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(128), default="dev-team@glgassets.com")
    status: Mapped[str] = mapped_column(String(32), default="PRODUCTION")  # DRAFT, TESTING, STAGING, CANARY, PRODUCTION, DISABLED, ARCHIVED
    environment: Mapped[str] = mapped_column(String(32), default="production")
    primary_model: Mapped[str] = mapped_column(String(128), default="llama-3.3-70b-versatile")
    fallback_model: Mapped[str | None] = mapped_column(String(128), default="llama-3.1-8b-instant")
    current_prompt_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    top_p: Mapped[float] = mapped_column(Float, default=0.9)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1024)
    presence_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    frequency_penalty: Mapped[float] = mapped_column(Float, default=0.0)
    persona_preset: Mapped[str] = mapped_column(String(64), default="Consultative Luxury")
    enabled_tools: Mapped[List[str]] = mapped_column(JSON, default=list)
    rag_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    memory_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    guardrail_policy_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    output_schema: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    human_approval_policy: Mapped[str] = mapped_column(String(64), default="NONE")  # NONE, HIGH_RISK_ONLY, ALWAYS
    max_execution_steps: Mapped[int] = mapped_column(Integer, default=5)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    retry_policy: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets-main")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AIAgentVersionRecord(Base):
    __tablename__ = "ai_agent_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(64), ForeignKey("ai_agents.id"), index=True)
    version_tag: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g., "v1.0.0"
    snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 2. Models & Providers ────────────────────────────────────

class AIProviderRecord(Base):
    __tablename__ = "ai_providers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    provider_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # groq, openai, anthropic, google, openrouter, azure
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    health_status: Mapped[str] = mapped_column(String(32), default="HEALTHY")  # HEALTHY, DEGRADED, DOWN, UNCONFIGURED
    last_ping_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    capabilities: Mapped[List[str]] = mapped_column(JSON, default=list)  # ["chat", "streaming", "tools", "vision", "embeddings"]
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=60)
    rate_limit_tpm: Mapped[int] = mapped_column(Integer, default=100000)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIModelRecord(Base):
    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    model_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), ForeignKey("ai_providers.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_type: Mapped[str] = mapped_column(String(32), default="BASE")  # BASE, FINE_TUNED, EMBEDDING, RERANKER, CLASSIFIER, VISION
    context_window: Mapped[int] = mapped_column(Integer, default=131072)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=8192)
    input_cost_per_m: Mapped[float] = mapped_column(Float, default=0.59)
    output_cost_per_m: Mapped[float] = mapped_column(Float, default=0.79)
    cached_cost_per_m: Mapped[float] = mapped_column(Float, default=0.30)
    supports_structured_output: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_tools: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(32), default="PRODUCTION")  # EXPERIMENTAL, TESTING, STAGING, PRODUCTION, DEPRECATED
    benchmark_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 3. Prompt Templates & Versions ───────────────────────────

class AIPromptTemplateRecord(Base):
    __tablename__ = "ai_prompt_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    developer_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    active_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets-main")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class AIPromptVersionRecord(Base):
    __tablename__ = "ai_prompt_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    template_id: Mapped[str] = mapped_column(String(64), ForeignKey("ai_prompt_templates.id"), index=True)
    version_tag: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g., "v1.0", "v1.1"
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    developer_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    declared_variables: Mapped[List[str]] = mapped_column(JSON, default=list)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    character_count: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 4. Tools & Action Catalog ────────────────────────────────

class AIToolRecord(Base):
    __tablename__ = "ai_tools"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    tool_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="data_retrieval")  # data_retrieval, transaction, communication, crm
    parameters_schema: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    output_schema: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str] = mapped_column(String(32), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    timeout_ms: Mapped[int] = mapped_column(Integer, default=5000)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_agents: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 5. Workflows & Executions ────────────────────────────────

class AIWorkflowRecord(Base):
    __tablename__ = "ai_workflows"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    nodes: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    edges: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # DRAFT, ACTIVE, DEPRECATED
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_errors: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets-main")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


# ── 6. Memory Policies & RAG Configurations ──────────────────

class AIMemoryPolicyRecord(Base):
    __tablename__ = "ai_memory_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(32), default="CONVERSATION")  # SHORT_TERM, CONVERSATION, CUSTOMER, AGENT, ORGANIZATION
    retention_ttl_hours: Mapped[int] = mapped_column(Integer, default=168)  # 7 days
    max_entries: Mapped[int] = mapped_column(Integer, default=20)
    relevance_threshold: Mapped[float] = mapped_column(Float, default=0.65)
    write_policy: Mapped[str] = mapped_column(String(32), default="AUTO_EXTRACT")  # AUTO_EXTRACT, EXPLICIT_ONLY, DISABLED
    redact_sensitive_fields: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIRAGConfigRecord(Base):
    __tablename__ = "ai_rag_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chunk_size: Mapped[int] = mapped_column(Integer, default=512)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=64)
    top_k: Mapped[int] = mapped_column(Integer, default=5)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.65)
    hybrid_alpha: Mapped[float] = mapped_column(Float, default=0.65)  # 0.0 = BM25 sparse only, 1.0 = dense vector only
    reranking_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    max_context_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    grounding_enforced: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled_sources: Mapped[List[str]] = mapped_column(JSON, default=list)  # ["property_db", "brochures", "faq_policies", "pricing_matrix"]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 7. Guardrail Policies & Blocked Violations ────────────────

class AIGuardrailPolicyRecord(Base):
    __tablename__ = "ai_guardrail_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # SAFETY, DATA, BUSINESS, OUTPUT
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(32), default="BLOCK")  # ALLOW, WARN, REWRITE, BLOCK, HUMAN_REVIEW
    severity: Mapped[str] = mapped_column(String(32), default="HIGH")  # LOW, MEDIUM, HIGH, CRITICAL
    rule_parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    total_triggers: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIGuardrailEventRecord(Base):
    __tablename__ = "ai_guardrail_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    policy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    action_taken: Mapped[str] = mapped_column(String(32), nullable=False)
    violation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_input_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    sanitized_output_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 8. Model Routing Rules ───────────────────────────────────

class AIRoutingRuleRecord(Base):
    __tablename__ = "ai_routing_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    priority: Mapped[int] = mapped_column(Integer, default=100)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    condition_task: Mapped[str | None] = mapped_column(String(64), nullable=True)  # classification, simple_faq, recommendation, complex_analysis
    condition_complexity: Mapped[str | None] = mapped_column(String(32), nullable=True)  # low, medium, high
    condition_agent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    fallback_model_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    strategy: Mapped[str] = mapped_column(String(32), default="RULE_BASED")  # FIXED, RULE_BASED, COST_OPTIMIZED, LATENCY_OPTIMIZED
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 9. Datasets & Evaluation Framework ───────────────────────

class AIDatasetRecord(Base):
    __tablename__ = "ai_datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(32), default="evaluation")  # evaluation, fine_tuning, benchmark, regression, safety
    target_agent: Mapped[str] = mapped_column(String(64), default="property_agent")
    version: Mapped[str] = mapped_column(String(32), default="v1.0")
    total_examples: Mapped[int] = mapped_column(Integer, default=0)
    quality_score: Mapped[float] = mapped_column(Float, default=96.5)
    train_count: Mapped[int] = mapped_column(Integer, default=0)
    val_count: Mapped[int] = mapped_column(Integer, default=0)
    test_count: Mapped[int] = mapped_column(Integer, default=0)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIDatasetExampleRecord(Base):
    __tablename__ = "ai_dataset_examples"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("ai_datasets.id"), index=True)
    split: Mapped[str] = mapped_column(String(16), default="test")  # train, val, test
    input_message: Mapped[str] = mapped_column(Text, nullable=False)
    expected_intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    expected_tools: Mapped[List[str]] = mapped_column(JSON, default=list)
    expected_facts: Mapped[List[str]] = mapped_column(JSON, default=list)
    metadata_tags: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIEvaluationRunRecord(Base):
    __tablename__ = "ai_evaluations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    suite_name: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_tested: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_pct: Mapped[float] = mapped_column(Float, default=0.0)
    groundedness_pct: Mapped[float] = mapped_column(Float, default=0.0)
    hallucination_pct: Mapped[float] = mapped_column(Float, default=0.0)
    tool_accuracy_pct: Mapped[float] = mapped_column(Float, default=0.0)
    schema_correctness_pct: Mapped[float] = mapped_column(Float, default=0.0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")  # QUEUED, RUNNING, COMPLETED, FAILED
    gate_verdict: Mapped[str] = mapped_column(String(16), default="PASS")  # PASS, FAIL
    report_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 10. Traces & Distributed Observability ───────────────────

class AITraceRecord(Base):
    __tablename__ = "ai_traces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    trace_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    channel: Mapped[str] = mapped_column(String(32), default="playground")
    environment: Mapped[str] = mapped_column(String(32), default="production")
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    agent_response: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS")  # SUCCESS, BLOCKED, ERROR, TIMEOUT
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cost_bdt: Mapped[float] = mapped_column(Float, default=0.0)
    spans: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    guardrail_actions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    tool_calls: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    rag_retrievals: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets-main")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 11. Budgets & Cost Accounting ────────────────────────────

class AIBudgetRecord(Base):
    __tablename__ = "ai_budgets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    period: Mapped[str] = mapped_column(String(16), default="MONTHLY")  # DAILY, MONTHLY
    monthly_budget_usd: Mapped[float] = mapped_column(Float, default=500.0)
    current_spend_usd: Mapped[float] = mapped_column(Float, default=84.25)
    warn_threshold_pct: Mapped[float] = mapped_column(Float, default=75.0)
    hard_stop_threshold_pct: Mapped[float] = mapped_column(Float, default=100.0)
    is_hard_stop_active: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_budgets: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    tenant_id: Mapped[str] = mapped_column(String(128), default="glg-assets-main")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


# ── 12. AI Releases & Deployment Pipeline ────────────────────

class AIReleaseRecord(Base):
    __tablename__ = "ai_releases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    release_tag: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)  # e.g., "v3.8.0"
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(32), default="STAGING")  # DRAFT, VALIDATION, STAGING, CANARY, PRODUCTION, ROLLED_BACK
    manifest: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # Full bundle: agent versions, models, prompts, tools, RAG, guardrails
    evaluation_gate_passed: Mapped[bool] = mapped_column(Boolean, default=True)
    evaluation_score: Mapped[float] = mapped_column(Float, default=98.2)
    deployed_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    can_rollback: Mapped[bool] = mapped_column(Boolean, default=True)
    previous_release_tag: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 13. Human Approvals & Escalations ────────────────────────

class AIApprovalRequestRecord(Base):
    __tablename__ = "ai_approvals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)  # SEND_OFFER, MODIFY_PROPERTY, CRM_UPDATE, HIGH_VAL_DISCOUNT
    risk_level: Mapped[str] = mapped_column(String(32), default="HIGH")  # MEDIUM, HIGH, CRITICAL
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    context_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    generated_content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")  # PENDING, APPROVED, REJECTED, EDITED
    reviewer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 14. Governance Policies & Rule Engine ────────────────────

class AIPolicyRecord(Base):
    __tablename__ = "ai_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=10)
    condition_expression: Mapped[str] = mapped_column(Text, nullable=False)  # e.g., "action == 'SEND_MESSAGE' and confidence < 0.85"
    action_directive: Mapped[str] = mapped_column(String(64), nullable=False)  # HUMAN_APPROVAL, BLOCK, REWRITE, ROUTE_CHEAP
    scope: Mapped[str] = mapped_column(String(64), default="ALL_AGENTS")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    environment: Mapped[str] = mapped_column(String(32), default="production")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 15. AI Incidents & Postmortems ───────────────────────────

class AIIncidentRecord(Base):
    __tablename__ = "ai_incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    incident_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)  # INC-2026-001
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="P2")  # P0, P1, P2, P3
    incident_type: Mapped[str] = mapped_column(String(64), nullable=False)  # hallucination, wrong_price, provider_outage, guardrail_breach
    status: Mapped[str] = mapped_column(String(32), default="OPEN")  # OPEN, INVESTIGATING, MITIGATED, RESOLVED, CLOSED
    agent_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── 16. Immutable Audit Logs ─────────────────────────────────

class AIAuditLogRecord(Base):
    __tablename__ = "ai_audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # PROMPT_CHANGED, MODEL_CHANGED, AGENT_PUBLISHED, RELEASE_DEPLOYED
    actor_email: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    actor_role: Mapped[str] = mapped_column(String(64), default="developer")
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)  # CREATE, UPDATE, DELETE, PUBLISH, DEPLOY, ROLLBACK
    before_state: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    environment: Mapped[str] = mapped_column(String(32), default="production")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 17. Fine-Tuning Jobs ─────────────────────────────────────

class AIFineTuneJobRecord(Base):
    __tablename__ = "ai_fine_tune_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    job_name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_model: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    lora_rank: Mapped[int] = mapped_column(Integer, default=16)
    epochs: Mapped[int] = mapped_column(Integer, default=3)
    learning_rate: Mapped[float] = mapped_column(Float, default=2e-4)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED")  # QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    progress_pct: Mapped[float] = mapped_column(Float, default=0.0)
    current_epoch: Mapped[int] = mapped_column(Integer, default=0)
    train_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    eval_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    output_model_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    training_duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cost_bdt: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 18. A/B Testing Experiments ──────────────────────────────

class AIExperimentRecord(Base):
    __tablename__ = "ai_experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    test_type: Mapped[str] = mapped_column(String(32), default="PROMPT")  # PROMPT, MODEL, RAG, WORKFLOW
    status: Mapped[str] = mapped_column(String(32), default="RUNNING")  # DRAFT, RUNNING, PAUSED, CONCLUDED
    traffic_split_a_pct: Mapped[int] = mapped_column(Integer, default=50)
    traffic_split_b_pct: Mapped[int] = mapped_column(Integer, default=50)
    variant_a_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    variant_b_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    metrics_a: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    metrics_b: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    winner_variant: Mapped[str | None] = mapped_column(String(16), nullable=True)  # VARIANT_A, VARIANT_B
    confidence_pct: Mapped[float] = mapped_column(Float, default=0.0)
    total_evaluations: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    concluded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── 19. Benchmarking Suites ──────────────────────────────────

class AIBenchmarkRecord(Base):
    __tablename__ = "ai_benchmarks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="AGENT_HEAD_TO_HEAD")
    entity_a_label: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_b_label: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_a_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    entity_b_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    metrics_comparison: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)  # Quality, Latency, Cost, Reliability, Tool Accuracy, Grounding, Safety, Completion
    scorecard: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    winner: Mapped[str] = mapped_column(String(64), default="TIE")
    executed_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── 20. Scoped Persistent Memories ───────────────────────────

class AIMemoryItemRecord(Base):
    __tablename__ = "ai_memory_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    scope: Mapped[str] = mapped_column(String(32), default="CONVERSATION")  # SHORT_TERM, CONVERSATION, CUSTOMER, AGENT, ORGANIZATION
    memory_key: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g., "customer_budget", "preferred_location"
    memory_value: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


# ── 21. AI Unified Configuration Snapshots ───────────────────

class AIConfigurationSnapshotRecord(Base):
    __tablename__ = "ai_configuration_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    snapshot_tag: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., "AI-SNAPSHOT-3.8.0"
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_slug: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    prompt_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    model_id: Mapped[str] = mapped_column(String(128), nullable=False)
    rag_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    guardrail_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    tool_versions: Mapped[List[str]] = mapped_column(JSON, default=list)
    memory_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    workflow_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    full_manifest: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(128), default="developer@glgassets.com")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

