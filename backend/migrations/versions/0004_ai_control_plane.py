"""Create AI and Agent Control Plane tables.

Revision ID: 0004_ai_control_plane
Revises: 0003_knowledge_chunks
Create Date: 2026-09-14
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_ai_control_plane"
down_revision = "0003_knowledge_chunks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. AI Agents
    op.create_table(
        "ai_agents",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role", sa.String(64), server_default="assistant"),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(128), server_default="dev-team@glgassets.com"),
        sa.Column("status", sa.String(32), server_default="PRODUCTION"),
        sa.Column("environment", sa.String(32), server_default="production"),
        sa.Column("primary_model", sa.String(128), server_default="llama-3.3-70b-versatile"),
        sa.Column("fallback_model", sa.String(128), server_default="llama-3.1-8b-instant", nullable=True),
        sa.Column("current_prompt_version", sa.String(32), server_default="v1.0"),
        sa.Column("temperature", sa.Float(), server_default="0.2"),
        sa.Column("top_p", sa.Float(), server_default="0.9"),
        sa.Column("max_tokens", sa.Integer(), server_default="1024"),
        sa.Column("presence_penalty", sa.Float(), server_default="0.0"),
        sa.Column("frequency_penalty", sa.Float(), server_default="0.0"),
        sa.Column("persona_preset", sa.String(64), server_default="Consultative Luxury"),
        sa.Column("enabled_tools", sa.JSON(), server_default="[]"),
        sa.Column("rag_config", sa.JSON(), server_default="{}"),
        sa.Column("memory_config", sa.JSON(), server_default="{}"),
        sa.Column("guardrail_policy_ids", sa.JSON(), server_default="[]"),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("human_approval_policy", sa.String(64), server_default="NONE"),
        sa.Column("max_execution_steps", sa.Integer(), server_default="5"),
        sa.Column("timeout_seconds", sa.Integer(), server_default="30"),
        sa.Column("retry_policy", sa.JSON(), server_default="{}"),
        sa.Column("tenant_id", sa.String(128), server_default="glg-assets-main"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_agents_slug", "ai_agents", ["slug"])

    # 2. AI Agent Versions
    op.create_table(
        "ai_agent_versions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("agent_id", sa.String(64), sa.ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_tag", sa.String(32), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_agent_versions_agent_id", "ai_agent_versions", ["agent_id"])

    # 3. AI Providers
    op.create_table(
        "ai_providers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("provider_key", sa.String(64), unique=True, nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("base_url", sa.String(256), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("health_status", sa.String(32), server_default="HEALTHY"),
        sa.Column("last_ping_ms", sa.Float(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capabilities", sa.JSON(), server_default="[]"),
        sa.Column("rate_limit_rpm", sa.Integer(), server_default="60"),
        sa.Column("rate_limit_tpm", sa.Integer(), server_default="100000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_providers_provider_key", "ai_providers", ["provider_key"])

    # 4. AI Models
    op.create_table(
        "ai_models",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("model_id", sa.String(128), unique=True, nullable=False),
        sa.Column("provider_id", sa.String(64), sa.ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("model_type", sa.String(32), server_default="BASE"),
        sa.Column("context_window", sa.Integer(), server_default="131072"),
        sa.Column("max_output_tokens", sa.Integer(), server_default="8192"),
        sa.Column("input_cost_per_m", sa.Float(), server_default="0.59"),
        sa.Column("output_cost_per_m", sa.Float(), server_default="0.79"),
        sa.Column("cached_cost_per_m", sa.Float(), server_default="0.30"),
        sa.Column("supports_structured_output", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("supports_tools", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("supports_streaming", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("status", sa.String(32), server_default="PRODUCTION"),
        sa.Column("benchmark_scores", sa.JSON(), server_default="{}"),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_models_model_id", "ai_models", ["model_id"])

    # 5. Prompt Templates
    op.create_table(
        "ai_prompt_templates",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("target_agent_id", sa.String(64), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("developer_instructions", sa.Text(), nullable=True),
        sa.Column("tool_instructions", sa.Text(), nullable=True),
        sa.Column("output_constraints", sa.Text(), nullable=True),
        sa.Column("active_version", sa.String(32), server_default="v1.0"),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("tenant_id", sa.String(128), server_default="glg-assets-main"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_prompt_templates_slug", "ai_prompt_templates", ["slug"])

    # 6. Prompt Versions
    op.create_table(
        "ai_prompt_versions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("template_id", sa.String(64), sa.ForeignKey("ai_prompt_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_tag", sa.String(32), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("developer_instructions", sa.Text(), nullable=True),
        sa.Column("tool_instructions", sa.Text(), nullable=True),
        sa.Column("output_constraints", sa.Text(), nullable=True),
        sa.Column("declared_variables", sa.JSON(), server_default="[]"),
        sa.Column("token_estimate", sa.Integer(), server_default="0"),
        sa.Column("character_count", sa.Integer(), server_default="0"),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_prompt_versions_template_id", "ai_prompt_versions", ["template_id"])

    # 7. AI Tools
    op.create_table(
        "ai_tools",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tool_key", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), server_default="data_retrieval"),
        sa.Column("parameters_schema", sa.JSON(), server_default="{}"),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("risk_level", sa.String(32), server_default="LOW"),
        sa.Column("timeout_ms", sa.Integer(), server_default="5000"),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("assigned_agents", sa.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_tools_tool_key", "ai_tools", ["tool_key"])

    # 8. AI Workflows
    op.create_table(
        "ai_workflows",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(32), server_default="1.0.0"),
        sa.Column("nodes", sa.JSON(), server_default="[]"),
        sa.Column("edges", sa.JSON(), server_default="[]"),
        sa.Column("status", sa.String(32), server_default="ACTIVE"),
        sa.Column("is_valid", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("validation_errors", sa.JSON(), server_default="[]"),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("tenant_id", sa.String(128), server_default="glg-assets-main"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_workflows_slug", "ai_workflows", ["slug"])

    # 9. AI Memory Policies
    op.create_table(
        "ai_memory_policies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("scope", sa.String(32), server_default="CONVERSATION"),
        sa.Column("retention_ttl_hours", sa.Integer(), server_default="168"),
        sa.Column("max_entries", sa.Integer(), server_default="20"),
        sa.Column("relevance_threshold", sa.Float(), server_default="0.65"),
        sa.Column("write_policy", sa.String(32), server_default="AUTO_EXTRACT"),
        sa.Column("redact_sensitive_fields", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_memory_policies_agent_id", "ai_memory_policies", ["agent_id"])

    # 10. AI RAG Configs
    op.create_table(
        "ai_rag_configs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("chunk_size", sa.Integer(), server_default="512"),
        sa.Column("chunk_overlap", sa.Integer(), server_default="64"),
        sa.Column("top_k", sa.Integer(), server_default="5"),
        sa.Column("similarity_threshold", sa.Float(), server_default="0.65"),
        sa.Column("hybrid_alpha", sa.Float(), server_default="0.65"),
        sa.Column("reranking_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("max_context_tokens", sa.Integer(), server_default="2048"),
        sa.Column("grounding_enforced", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("enabled_sources", sa.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_rag_configs_agent_id", "ai_rag_configs", ["agent_id"])

    # 11. AI Guardrail Policies
    op.create_table(
        "ai_guardrail_policies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("rule_name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action", sa.String(32), server_default="BLOCK"),
        sa.Column("severity", sa.String(32), server_default="HIGH"),
        sa.Column("rule_parameters", sa.JSON(), server_default="{}"),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("total_triggers", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 12. AI Guardrail Events
    op.create_table(
        "ai_guardrail_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("policy_id", sa.String(64), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("action_taken", sa.String(32), nullable=False),
        sa.Column("violation_type", sa.String(64), nullable=False),
        sa.Column("raw_input_snippet", sa.Text(), nullable=False),
        sa.Column("sanitized_output_snippet", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_guardrail_events_policy_id", "ai_guardrail_events", ["policy_id"])
    op.create_index("ix_ai_guardrail_events_trace_id", "ai_guardrail_events", ["trace_id"])

    # 13. AI Routing Rules
    op.create_table(
        "ai_routing_rules",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("priority", sa.Integer(), server_default="100"),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("condition_task", sa.String(64), nullable=True),
        sa.Column("condition_complexity", sa.String(32), nullable=True),
        sa.Column("condition_agent", sa.String(64), nullable=True),
        sa.Column("target_model_id", sa.String(128), nullable=False),
        sa.Column("fallback_model_id", sa.String(128), nullable=True),
        sa.Column("strategy", sa.String(32), server_default="RULE_BASED"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 14. AI Datasets
    op.create_table(
        "ai_datasets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("dataset_type", sa.String(32), server_default="evaluation"),
        sa.Column("target_agent", sa.String(64), server_default="property_agent"),
        sa.Column("version", sa.String(32), server_default="v1.0"),
        sa.Column("total_examples", sa.Integer(), server_default="0"),
        sa.Column("quality_score", sa.Float(), server_default="96.5"),
        sa.Column("train_count", sa.Integer(), server_default="0"),
        sa.Column("val_count", sa.Integer(), server_default="0"),
        sa.Column("test_count", sa.Integer(), server_default="0"),
        sa.Column("is_locked", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_datasets_slug", "ai_datasets", ["slug"])

    # 15. AI Dataset Examples
    op.create_table(
        "ai_dataset_examples",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("dataset_id", sa.String(64), sa.ForeignKey("ai_datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("split", sa.String(16), server_default="test"),
        sa.Column("input_message", sa.Text(), nullable=False),
        sa.Column("expected_intent", sa.String(64), nullable=True),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("expected_tools", sa.JSON(), server_default="[]"),
        sa.Column("expected_facts", sa.JSON(), server_default="[]"),
        sa.Column("metadata_tags", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_dataset_examples_dataset_id", "ai_dataset_examples", ["dataset_id"])

    # 16. AI Evaluations
    op.create_table(
        "ai_evaluations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("suite_name", sa.String(128), nullable=False),
        sa.Column("dataset_id", sa.String(64), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("model_tested", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(32), server_default="v1.0"),
        sa.Column("total_cases", sa.Integer(), server_default="0"),
        sa.Column("passed_cases", sa.Integer(), server_default="0"),
        sa.Column("failed_cases", sa.Integer(), server_default="0"),
        sa.Column("accuracy_pct", sa.Float(), server_default="0.0"),
        sa.Column("groundedness_pct", sa.Float(), server_default="0.0"),
        sa.Column("hallucination_pct", sa.Float(), server_default="0.0"),
        sa.Column("tool_accuracy_pct", sa.Float(), server_default="0.0"),
        sa.Column("schema_correctness_pct", sa.Float(), server_default="0.0"),
        sa.Column("avg_latency_ms", sa.Float(), server_default="0.0"),
        sa.Column("status", sa.String(32), server_default="COMPLETED"),
        sa.Column("gate_verdict", sa.String(16), server_default="PASS"),
        sa.Column("report_data", sa.JSON(), server_default="{}"),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 17. AI Traces
    op.create_table(
        "ai_traces",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("trace_id", sa.String(64), unique=True, nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("conversation_id", sa.String(128), nullable=True),
        sa.Column("channel", sa.String(32), server_default="playground"),
        sa.Column("environment", sa.String(32), server_default="production"),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column("agent_response", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(32), server_default="v1.0"),
        sa.Column("status", sa.String(32), server_default="SUCCESS"),
        sa.Column("total_tokens", sa.Integer(), server_default="0"),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), server_default="0"),
        sa.Column("cached_tokens", sa.Integer(), server_default="0"),
        sa.Column("latency_ms", sa.Float(), server_default="0.0"),
        sa.Column("cost_usd", sa.Float(), server_default="0.0"),
        sa.Column("cost_bdt", sa.Float(), server_default="0.0"),
        sa.Column("spans", sa.JSON(), server_default="[]"),
        sa.Column("guardrail_actions", sa.JSON(), server_default="[]"),
        sa.Column("tool_calls", sa.JSON(), server_default="[]"),
        sa.Column("rag_retrievals", sa.JSON(), server_default="[]"),
        sa.Column("tenant_id", sa.String(128), server_default="glg-assets-main"),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_traces_trace_id", "ai_traces", ["trace_id"])
    op.create_index("ix_ai_traces_agent_id", "ai_traces", ["agent_id"])

    # 18. AI Budgets
    op.create_table(
        "ai_budgets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("period", sa.String(16), server_default="MONTHLY"),
        sa.Column("monthly_budget_usd", sa.Float(), server_default="500.0"),
        sa.Column("current_spend_usd", sa.Float(), server_default="0.0"),
        sa.Column("warn_threshold_pct", sa.Float(), server_default="75.0"),
        sa.Column("hard_stop_threshold_pct", sa.Float(), server_default="100.0"),
        sa.Column("is_hard_stop_active", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("agent_budgets", sa.JSON(), server_default="{}"),
        sa.Column("tenant_id", sa.String(128), server_default="glg-assets-main"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 19. AI Releases
    op.create_table(
        "ai_releases",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("release_tag", sa.String(32), unique=True, nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("environment", sa.String(32), server_default="STAGING"),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("evaluation_gate_passed", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("evaluation_score", sa.Float(), server_default="98.0"),
        sa.Column("deployed_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("can_rollback", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("previous_release_tag", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_releases_release_tag", "ai_releases", ["release_tag"])

    # 20. AI Approvals
    op.create_table(
        "ai_approvals",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("risk_level", sa.String(32), server_default="HIGH"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("context_data", sa.JSON(), server_default="{}"),
        sa.Column("generated_content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING"),
        sa.Column("reviewer", sa.String(128), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 21. AI Policies
    op.create_table(
        "ai_policies",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="10"),
        sa.Column("condition_expression", sa.Text(), nullable=False),
        sa.Column("action_directive", sa.String(64), nullable=False),
        sa.Column("scope", sa.String(64), server_default="ALL_AGENTS"),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("environment", sa.String(32), server_default="production"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 22. AI Incidents
    op.create_table(
        "ai_incidents",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("incident_number", sa.String(32), unique=True, nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("severity", sa.String(16), server_default="P2"),
        sa.Column("incident_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="OPEN"),
        sa.Column("agent_id", sa.String(64), nullable=True),
        sa.Column("model_id", sa.String(128), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("owner", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("timeline", sa.JSON(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_incidents_incident_number", "ai_incidents", ["incident_number"])

    # 23. AI Audit Logs
    op.create_table(
        "ai_audit_logs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor_email", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("actor_role", sa.String(64), server_default="developer"),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(128), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("environment", sa.String(32), server_default="production"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_audit_logs_event_type", "ai_audit_logs", ["event_type"])

    # 24. AI Fine-Tune Jobs
    op.create_table(
        "ai_fine_tune_jobs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("base_model", sa.String(128), nullable=False),
        sa.Column("dataset_id", sa.String(64), nullable=False),
        sa.Column("adapter_tag", sa.String(64), nullable=False),
        sa.Column("agent_slug", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), server_default="PENDING"),
        sa.Column("hyperparameters", sa.JSON(), server_default="{}"),
        sa.Column("training_loss", sa.Float(), nullable=True),
        sa.Column("validation_perplexity", sa.Float(), nullable=True),
        sa.Column("progress_pct", sa.Float(), server_default="0.0"),
        sa.Column("estimated_cost_usd", sa.Float(), server_default="0.0"),
        sa.Column("estimated_cost_bdt", sa.Float(), server_default="0.0"),
        sa.Column("checkpoint_uri", sa.String(256), nullable=True),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_fine_tune_jobs_status", "ai_fine_tune_jobs", ["status"])

    # 25. AI Experiments (A/B Testing)
    op.create_table(
        "ai_experiments",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("test_type", sa.String(32), server_default="PROMPT"),
        sa.Column("status", sa.String(32), server_default="RUNNING"),
        sa.Column("traffic_split_a_pct", sa.Integer(), server_default="50"),
        sa.Column("traffic_split_b_pct", sa.Integer(), server_default="50"),
        sa.Column("variant_a_config", sa.JSON(), nullable=False),
        sa.Column("variant_b_config", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), server_default="{}"),
        sa.Column("winner", sa.String(32), nullable=True),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("concluded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_experiments_agent_id", "ai_experiments", ["agent_id"])

    # 26. AI Benchmarks
    op.create_table(
        "ai_benchmarks",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), server_default="GROUNDING"),
        sa.Column("entity_a_label", sa.String(128), nullable=False),
        sa.Column("entity_b_label", sa.String(128), nullable=False),
        sa.Column("entity_a_config", sa.JSON(), nullable=False),
        sa.Column("entity_b_config", sa.JSON(), nullable=False),
        sa.Column("metrics_comparison", sa.JSON(), server_default="{}"),
        sa.Column("scorecard", sa.JSON(), server_default="{}"),
        sa.Column("winner", sa.String(128), nullable=True),
        sa.Column("executed_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_benchmarks_category", "ai_benchmarks", ["category"])

    # 27. AI Memory Items
    op.create_table(
        "ai_memory_items",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("agent_id", sa.String(64), nullable=False),
        sa.Column("customer_id", sa.String(64), nullable=True),
        sa.Column("conversation_id", sa.String(64), nullable=True),
        sa.Column("scope", sa.String(32), server_default="CUSTOMER"),
        sa.Column("memory_key", sa.String(128), nullable=False),
        sa.Column("memory_value", sa.Text(), nullable=False),
        sa.Column("relevance_score", sa.Float(), server_default="1.0"),
        sa.Column("is_sensitive", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_memory_items_agent_id", "ai_memory_items", ["agent_id"])

    # 28. AI Configuration Snapshots
    op.create_table(
        "ai_configuration_snapshots",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("snapshot_tag", sa.String(64), unique=True, nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("agent_slug", sa.String(64), nullable=False),
        sa.Column("agent_version", sa.String(32), nullable=False),
        sa.Column("prompt_version", sa.String(32), nullable=False),
        sa.Column("model_id", sa.String(128), nullable=False),
        sa.Column("rag_version", sa.String(32), server_default="v1.0"),
        sa.Column("guardrail_version", sa.String(32), server_default="v1.0"),
        sa.Column("tool_versions", sa.JSON(), server_default="[]"),
        sa.Column("memory_version", sa.String(32), server_default="v1.0"),
        sa.Column("workflow_version", sa.String(32), server_default="v1.0.0"),
        sa.Column("full_manifest", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(128), server_default="developer@glgassets.com"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_snapshots_snapshot_tag", "ai_configuration_snapshots", ["snapshot_tag"])


def downgrade() -> None:
    tables = [
        "ai_configuration_snapshots",
        "ai_memory_items",
        "ai_benchmarks",
        "ai_experiments",
        "ai_fine_tune_jobs",
        "ai_audit_logs",
        "ai_incidents",
        "ai_policies",
        "ai_approvals",
        "ai_releases",
        "ai_budgets",
        "ai_traces",
        "ai_evaluations",
        "ai_dataset_examples",
        "ai_datasets",
        "ai_routing_rules",
        "ai_guardrail_events",
        "ai_guardrail_policies",
        "ai_rag_configs",
        "ai_memory_policies",
        "ai_workflows",
        "ai_tools",
        "ai_prompt_versions",
        "ai_prompt_templates",
        "ai_models",
        "ai_providers",
        "ai_agent_versions",
        "ai_agents",
    ]
    for tbl in tables:
        op.drop_table(tbl)

