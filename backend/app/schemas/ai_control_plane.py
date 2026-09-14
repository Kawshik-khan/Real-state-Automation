"""Pydantic v2 schemas for AI & Agent Control Plane.

Provides strict request validation and response models for all 27 capabilities:
Agents, Prompts, Models, Routing, Tools, Workflows, RAG, Memory, Guardrails,
Playground, Evaluations, Datasets, Releases, Approvals, Incidents, and Audit.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Overview & Telemetry ──

class TelemetrySummaryResponse(BaseModel):
    success: bool = True
    timestamp: str
    time_range: str
    metrics: Dict[str, Any]
    budget: Dict[str, Any]
    providers: List[Dict[str, Any]]
    recent_runs: List[Dict[str, Any]]


# ── Agents ──

class AgentUpdateRequest(BaseModel):
    slug: str
    name: Optional[str] = None
    description: Optional[str] = None
    role: Optional[str] = None
    objective: Optional[str] = None
    status: Optional[str] = None
    primary_model: Optional[str] = None
    fallback_model: Optional[str] = None
    current_prompt_version: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=64, le=8192)
    persona_preset: Optional[str] = None
    enabled_tools: Optional[List[str]] = None
    rag_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None
    guardrail_policy_ids: Optional[List[str]] = None
    human_approval_policy: Optional[str] = None


class AgentPublishRequest(BaseModel):
    changelog: str = Field("Production release update", description="Changelog notes for this immutable version")


# ── Prompts ──

class PromptValidateRequest(BaseModel):
    prompt_text: str = Field(..., description="Full system prompt text to analyze and validate")


# ── Models & Gateway ──

class ModelConnectionTestRequest(BaseModel):
    provider_key: str = Field("groq", description="Target provider (groq, openai, anthropic, google, openrouter)")
    model_id: Optional[str] = Field(None, description="Optional model to ping")
    custom_base_url: Optional[str] = None


# ── Routing ──

class RoutingSimulationRequest(BaseModel):
    task: str = Field("property_inquiry", description="Task type (classification, recommendation, complex_analysis)")
    complexity: str = Field("medium", description="Complexity tier (low, medium, high)")
    agent_slug: str = Field("property_agent", description="Target agent slug")


# ── Tools ──

class ToolTestRequest(BaseModel):
    tool_key: str = Field(..., description="Key of the tool to test")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters matching tool schema")


# ── Workflows ──

class WorkflowValidateRequest(BaseModel):
    nodes: List[Dict[str, Any]] = Field(..., description="List of graph nodes")
    edges: List[Dict[str, Any]] = Field(..., description="List of directed edges")


# ── RAG ──

class RAGRetrievalTestRequest(BaseModel):
    query: str = Field(..., description="User search query to retrieve against RAG index")
    top_k: int = Field(4, ge=1, le=20)
    alpha: float = Field(0.65, ge=0.0, le=1.0, description="0.0 = BM25 sparse, 1.0 = Dense vector")


# ── Guardrails ──

class GuardrailTestRequest(BaseModel):
    rule_id: str = Field("gr-inj-001", description="Policy rule ID to test against")
    test_text: str = Field(..., description="Input message to evaluate")


# ── Playground ──

class PlaygroundRunRequest(BaseModel):
    agent_slug: str = Field("property_agent", description="Target agent to run")
    user_message: str = Field(..., description="Prompt/chat input message")
    model_override: Optional[str] = None
    system_prompt_override: Optional[str] = None
    temperature_override: Optional[float] = None
    rag_enabled: bool = True


# ── Evaluations ──

class EvaluationRunRequest(BaseModel):
    dataset_id: str = Field("ds-eval-001", description="Dataset identifier")
    agent_slug: str = Field("property_agent", description="Target agent to evaluate")


# ── Releases ──

class ReleaseCreateRequest(BaseModel):
    release_tag: str = Field(..., description="Semantic version tag e.g. v3.9.0")
    title: str = Field(..., description="Release headline")
    description: Optional[str] = None


class ReleaseDeployRequest(BaseModel):
    release_tag: str = Field(..., description="Release tag to deploy or rollback")


# ── Approvals ──

class ApprovalDecisionRequest(BaseModel):
    status: str = Field(..., description="APPROVED, REJECTED, EDITED")
    notes: Optional[str] = None
    edited_content: Optional[str] = None


# ── Incidents ──

class IncidentCreateRequest(BaseModel):
    title: str = Field(..., description="Incident title")
    severity: str = Field("P2", description="P0, P1, P2, P3")
    incident_type: str = Field(..., description="hallucination, wrong_price, provider_outage, guardrail_breach, circuit_breaker")
    description: str = Field(..., description="Incident description or root cause analysis")
    trace_id: Optional[str] = None


class IncidentUpdateRequest(BaseModel):
    status: str = Field(..., description="OPEN, INVESTIGATING, MITIGATED, RESOLVED, CLOSED")
    note: Optional[str] = None
    resolution: Optional[str] = None


class CircuitBreakerTripRequest(BaseModel):
    agent_slug: str = Field(..., description="Target agent to deactivate")
    reason: str = Field("Manual emergency stop triggered by developer", description="Reason for tripping")


class AgentRollbackRequest(BaseModel):
    target_version: str = Field(..., description="Target version tag to revert to (e.g. v2.0)")


# ── Budget ──

class BudgetUpdateRequest(BaseModel):
    monthly_budget_usd: Optional[float] = None
    warn_threshold_pct: Optional[float] = None
    hard_stop_threshold_pct: Optional[float] = None
    agent_budgets: Optional[Dict[str, float]] = None


# ── Red-Teaming & Stress Testing ──

class RedTeamRunRequest(BaseModel):
    agent_slug: str = Field("property_agent", description="Target agent to attack")


class StressTestRunRequest(BaseModel):
    agent_slug: str = Field("property_agent", description="Target agent to test")
    concurrency: int = Field(5, ge=1, le=20)
    num_requests: int = Field(10, ge=1, le=50)


# ── Fine-Tuning ──

class FineTuningTriggerRequest(BaseModel):
    dataset_id: str = Field("ds-eval-001", description="Dataset for training")
    base_model: str = Field("llama-3.1-8b-instant", description="Base foundation model")
    lora_rank: int = Field(16, ge=4, le=64)
    epochs: int = Field(3, ge=1, le=10)
    learning_rate: float = Field(0.0002, ge=0.00001, le=0.01)


# ── Cost Optimization ──

class ApplyOptimizationRequest(BaseModel):
    recommendation_id: str = Field(..., description="Recommendation to apply")


# ── Datasets & Examples ──

class DatasetCreateRequest(BaseModel):
    slug: str
    name: str
    dataset_type: str = "evaluation"
    target_agent: str = "property_agent"
    version: str = "v1.0"


class DatasetExampleCreateRequest(BaseModel):
    dataset_id: str
    split: str = "test"
    input_message: str
    expected_intent: Optional[str] = None
    expected_output: str
    expected_tools: Optional[List[str]] = None
    expected_facts: Optional[List[str]] = None
    metadata_tags: Optional[Dict[str, Any]] = None


# ── Routing Rules ──

class RoutingRuleCreateRequest(BaseModel):
    priority: int = 100
    name: str
    condition_task: Optional[str] = None
    condition_complexity: Optional[str] = None
    condition_agent: Optional[str] = None
    target_model_id: str
    fallback_model_id: Optional[str] = None
    strategy: str = "RULE_BASED"
    is_active: bool = True


# ── Experiments (A/B Testing) ──

class ExperimentCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    agent_id: str = "property_agent"
    test_type: str = "PROMPT"  # PROMPT, MODEL, RAG, WORKFLOW
    traffic_split_a_pct: int = 50
    traffic_split_b_pct: int = 50
    variant_a_config: Dict[str, Any]
    variant_b_config: Dict[str, Any]


class ExperimentActionRequest(BaseModel):
    action: str = Field(..., description="PAUSE, RESUME, SELECT_WINNER")
    winner: Optional[str] = None  # VARIANT_A, VARIANT_B


# ── Benchmarking ──

class BenchmarkRunRequest(BaseModel):
    name: str
    category: str = "MODEL_HEAD_TO_HEAD"
    entity_a_label: str
    entity_b_label: str
    entity_a_config: Dict[str, Any]
    entity_b_config: Dict[str, Any]


# ── Policy Engine ──

class PolicyCreateRequest(BaseModel):
    name: str
    description: str
    priority: int = 10
    condition_expression: str
    action_directive: str  # HUMAN_APPROVAL, BLOCK, REWRITE, ROUTE_CHEAPER
    scope: str = "ALL_AGENTS"
    is_enabled: bool = True
    environment: str = "production"


class PolicySimulateRequest(BaseModel):
    condition_expression: str
    context: Dict[str, Any]


# ── Memories ──

class MemoryItemCreateRequest(BaseModel):
    agent_id: str
    customer_id: Optional[str] = None
    conversation_id: Optional[str] = None
    scope: str = "CONVERSATION"  # SHORT_TERM, CONVERSATION, CUSTOMER, AGENT, ORGANIZATION
    memory_key: str
    memory_value: str
    relevance_score: float = 1.0
    is_sensitive: bool = False


# ── Snapshots & Versioning ──

class SnapshotCreateRequest(BaseModel):
    snapshot_tag: str
    title: str
    description: Optional[str] = None
    agent_slug: str
    full_manifest: Optional[Dict[str, Any]] = None


# ── Model Recommendation ──

class ModelRecommendRequest(BaseModel):
    task: str = "recommendation"
    budget_constraint: Optional[float] = None
    latency_requirement_ms: Optional[float] = None
    requires_tools: bool = True
    requires_structured_output: bool = True
    context_length: int = 4096


