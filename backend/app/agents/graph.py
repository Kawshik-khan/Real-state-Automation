"""LangGraph orchestration for the AI pipeline.

State is AIState (Pydantic BaseModel). Nodes receive and return dicts
of fields to update — LangGraph merges them into the state object.
"""
from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.state import Action, AIState, IntentResult, LeadScore, ModerationResult

# ── Entry ───────────────────────────────────────────────────

def entry_node(state: AIState) -> dict:
    return {}


# ── Moderation ──────────────────────────────────────────────

async def moderation_node(state: AIState) -> dict:
    from app.services.llm import llm_service
    from app.services.policy_engine import policy_engine

    if not state.message or not state.message.strip():
        return {"moderation": ModerationResult(action="allow"), "moderated": True}

    # 1. Deterministic Policy Engine (Pillar 1 Pre-Guard: Jailbreak Defense & PII Redaction)
    policy_res = policy_engine.evaluate_inbound_message(state.message)
    if not policy_res.is_allowed or policy_res.action == "block":
        return {
            "moderation": ModerationResult(
                action="block",
                reason=policy_res.reasons[0] if policy_res.reasons else "Message blocked by deterministic security policy.",
            ),
            "moderated": True,
            "message": policy_res.sanitized_text or state.message,
        }

    clean_message = policy_res.sanitized_text if policy_res.action == "sanitize" else state.message

    # 2. LLM-based Moderation
    try:
        result = await llm_service.structured_chat(
            [
                {"role": "system", "content": MODERATION_PROMPT},
                {"role": "user", "content": clean_message},
            ],
            json_schema={},
            temperature=0.1,
        )
        return {
            "moderation": ModerationResult(**result),
            "moderated": True,
            "message": clean_message,
        }
    except Exception:
        return {
            "moderation": ModerationResult(action="allow"),
            "moderated": True,
            "message": clean_message,
        }


def moderation_router(state: AIState) -> str:
    if state.moderation.action == "block":
        return "blocked"
    return "memory_load"


async def blocked_node(state: AIState) -> dict:
    return {
        "agent_used": "moderation",
        "agent_reply": "I'm sorry, but I can't process that message. Please keep our conversation respectful and on-topic.",
        "agent_done": True,
        "safety_check_passed": True,
        "safety_checked": True,
        "output_built": True,
    }


# ── Memory & Dynamic Belief Reconciliation ──────────────────

async def memory_load_node(state: AIState) -> dict:
    from app.services.belief_memory import belief_memory_service
    from app.services.memory import conversation_memory

    history = await conversation_memory.get_history(state.conversation_id)
    beliefs = await belief_memory_service.get_beliefs(state.conversation_id)
    return {
        "history": [
            {"role": e.role, "content": e.content, "timestamp": e.timestamp.isoformat()}
            for e in history
        ],
        "beliefs": beliefs,
        "memory_loaded": True,
    }


async def memory_reflection_node(state: AIState) -> dict:
    """Self-correcting memory reflection pass:
    Evaluates incoming message against active beliefs to detect corrections,
    contradictions, and revisions.
    """
    from app.services.belief_memory import belief_memory_service

    updated_beliefs, new_revisions = await belief_memory_service.reconcile_beliefs(
        current=state.beliefs,
        user_message=state.message,
        history=state.history,
    )
    return {
        "beliefs": updated_beliefs,
        "memory_corrections": new_revisions,
        "has_corrections": bool(new_revisions),
    }


# ── Supervisor ──────────────────────────────────────────────

async def supervisor_node(state: AIState) -> dict:
    from app.services.llm import llm_service

    msg_lower = state.message.lower() if state.message else ""
    # Direct greeting safeguard
    msg_trimmed = msg_lower.strip()
    if msg_trimmed in ["hi", "hello", "hey", "salam", "assalamu alaikum", "assalamualaykum", "good morning", "good evening", "good afternoon"] or (
        any(msg_trimmed.startswith(gw) for gw in ["hi ", "hello ", "hey ", "good morning", "good evening", "assalamu alaikum"]) and not any(kw in msg_lower for kw in ["banani", "gulshan", "uttara", "flat", "project", "ki ache", "price", "dam"])
    ):
        return {
            "intent": IntentResult(
                intent="greeting",
                confidence=0.98,
                entities={"location": "", "project": "", "bedrooms": 0, "budget": ""}
            ),
            "intent_classified": True,
            "messages_used": state.messages_used + 1
        }

    import re

    # Non-property retail goods inquiry safeguard -> routes cleanly to fallback_handler
    consumer_retail_terms = [
        "jacket", "shirt", "pant", "t-shirt", "dress", "clothing", "shoe", "shoes",
        "chocolate", "kitkat", "candy", "phone", "iphone", "laptop",
        "watch", "car", "bike", "food", "grocery", "groceries", "medicine", "ticket"
    ]
    if any(re.search(rf"\b{re.escape(term)}\b", msg_lower) for term in consumer_retail_terms):
        return {
            "intent": IntentResult(
                intent="other",
                confidence=0.98,
                entities={"location": "", "project": "", "bedrooms": 0, "budget": ""},
            ),
            "intent_classified": True,
            "messages_used": state.messages_used + 1,
        }

    # Banglish / Bangla property inquiry safeguard
    # Require explicit property indicators (or recognized project/locations), not generic single words like "price"
    real_estate_explicit_terms = [
        "flat", "apartment", "plot", "duplex", "penthouse", "bhk", "building",
        "floor plan", "sqft", "square feet", "handover", "booking"
    ]
    location_terms = ["banani", "gulshan", "uttara", "dhanmondi", "baridhara", "mirpur"]
    property_phrases = [
        "ki ache", "konta ache", "kothay ache", "flat ache", "ongoing project",
        "dam koto", "price koto", "koto dam", "flat price", "apartment price"
    ]
    has_explicit_re = any(term in msg_lower for term in real_estate_explicit_terms)
    has_loc = any(loc in msg_lower for loc in location_terms)
    has_prop_phrase = any(phrase in msg_lower for phrase in property_phrases)

    if (has_explicit_re or (has_loc and (has_prop_phrase or "project" in msg_lower)) or has_prop_phrase):
        from app.services.location_service import location_service
        loc = await location_service.resolve_location_from_text(msg_lower)
        return {
            "intent": IntentResult(
                intent="property_search",
                confidence=0.95,
                entities={"location": loc, "project": "", "bedrooms": 0, "budget": ""}
            ),
            "intent_classified": True,
            "messages_used": state.messages_used + 1
        }

    history_context = ""
    if state.history:
        entries = state.history[-5:]
        history_context = "\n".join(
            f"{e['role']}: {e['content'][:200]}" for e in entries
        )

    # Contextual belief context if available
    belief_context = ""
    if state.beliefs.preferred_locations or state.beliefs.budget_raw:
        belief_context = f"\nActive User Constraints: Locations={state.beliefs.preferred_locations}, Budget={state.beliefs.budget_raw}, Bedrooms={state.beliefs.bedrooms}"

    messages = [{"role": "system", "content": SUPERVISOR_PROMPT}]
    if history_context:
        messages.append({"role": "system", "content": f"Conversation history:\n{history_context}"})
    if belief_context:
        messages.append({"role": "system", "content": belief_context})
    messages.append({"role": "user", "content": f"Channel: {state.channel}\nMessage: {state.message}"})

    try:
        result = await llm_service.structured_chat(messages, json_schema={}, temperature=0.2)
        return {"intent": IntentResult(**result), "intent_classified": True, "messages_used": state.messages_used + 1}
    except Exception:
        return {"intent": IntentResult(intent="other", confidence=0.5), "intent_classified": True}


def intent_router(state: AIState) -> str:
    intent = state.intent.intent
    if intent == "greeting":
        return "greeting_handler"
    elif intent in ("booking", "lead") or state.intent.requires_escalation:
        return "booking_handler"
    elif intent == "property_search":
        return "property_agent"
    elif intent == "faq":
        return "faq_agent"
    elif intent == "content_request":
        return "content_agent"
    return "fallback_handler"


# ── Agents ──────────────────────────────────────────────────

async def property_agent_node(state: AIState) -> dict:
    from app.agents.property_agent import property_agent
    from app.rag.pipeline import rag

    try:
        entities = state.intent.entities or {}
        agent_context = f"Looking for: {state.message}\n"
        
        # Include conversation history for context continuity
        if state.history:
            history_lines = [f"{h['role'].upper()}: {h['content']}" for h in state.history[-6:]]
            agent_context += "\n--- CONVERSATION HISTORY ---\n" + "\n".join(history_lines) + "\n"
            
        # Prioritize Reconciled Active Beliefs from Self-Correcting Memory
        reconciled_loc = state.beliefs.preferred_locations[0] if state.beliefs.preferred_locations else entities.get("location", "")
        reconciled_budget = state.beliefs.budget_raw or entities.get("budget", "")
        reconciled_beds = state.beliefs.bedrooms or entities.get("bedrooms", 0)

        if not entities.get("location") and not reconciled_loc and state.history:
            # Only inherit past location if current message is an inquiry follow-up, not a new topic
            is_followup = any(kw in state.message.lower() for kw in [
                "ar ki", "konta", "details", "bistatito", "floor plan", "brochure",
                "price", "dam", "size", "handover", "amenities", "pool", "bhk", "bedroom"
            ])
            if is_followup:
                from app.services.location_service import location_service
                for turn in reversed(state.history):
                    found_loc = await location_service.resolve_location_from_text(turn.get("content", ""))
                    if found_loc:
                        reconciled_loc = found_loc
                        break

        if reconciled_loc:
            entities["location"] = reconciled_loc
            agent_context += f"Active Preferred Location: {reconciled_loc}\n"
        if reconciled_budget:
            entities["budget"] = reconciled_budget
            agent_context += f"Active Budget: {reconciled_budget}\n"
        if reconciled_beds:
            entities["bedrooms"] = reconciled_beds
            agent_context += f"Active Bedrooms: {reconciled_beds}\n"
        if state.beliefs.negative_constraints:
            agent_context += f"MANDATORY EXCLUSIONS & NEGATIVE CONSTRAINTS: {', '.join(state.beliefs.negative_constraints)}\n"
        if state.beliefs.excluded_locations:
            agent_context += f"EXCLUDED LOCATIONS (DO NOT SUGGEST): {', '.join(state.beliefs.excluded_locations)}\n"

        if entities.get("project"):
            agent_context += f"Project: {entities['project']}\n"

        rag_context, rag_done = "", False
        try:
            rag_filters = {}
            if reconciled_loc:
                rag_filters["location"] = reconciled_loc
            if entities.get("project"):
                rag_filters["project"] = entities["project"]
            chunks = await rag.query(state.message, top_k=3, filters=rag_filters if rag_filters else None)
            if chunks:
                context_str = await rag.build_context(chunks)
                agent_context += f"\nKnowledge base context:\n{context_str}"
                rag_context = context_str
                rag_done = True
        except Exception:
            pass

        reply = await property_agent.handle(state.message, entities, extra_context=agent_context)
        final_rag_context = rag_context if rag_context else agent_context
        return {"agent_reply": reply, "agent_used": "property_agent", "agent_done": True,
                "rag_context": final_rag_context, "rag_done": rag_done}
    except Exception as e:
        return {"agent_reply": "I'm sorry, I couldn't find property information right now. Please try again.",
                "agent_used": "property_agent", "agent_done": True, "agent_error": str(e)}


async def faq_agent_node(state: AIState) -> dict:
    from app.agents.faq_agent import faq_agent
    from app.rag.pipeline import rag

    try:
        agent_context = state.message
        rag_context, rag_done = "", False
        try:
            chunks = await rag.query(state.message, top_k=2)
            if chunks:
                context_str = await rag.build_context(chunks)
                agent_context += f"\n\nReference context:\n{context_str}"
                rag_context = context_str
                rag_done = True
        except Exception:
            pass

        reply = await faq_agent.handle(state.message, extra_context=agent_context)
        return {"agent_reply": reply, "agent_used": "faq_agent", "agent_done": True,
                "rag_context": rag_context, "rag_done": rag_done}
    except Exception as e:
        return {"agent_reply": "I'm sorry, I couldn't find that information. Please contact our team.",
                "agent_used": "faq_agent", "agent_done": True, "agent_error": str(e)}


async def content_agent_node(state: AIState) -> dict:
    from app.agents.content_agent import content_agent

    try:
        reply = await content_agent.handle(state.message)
        return {"agent_reply": reply, "agent_used": "content_agent", "agent_done": True}
    except Exception as e:
        return {"agent_reply": "I'm sorry, I couldn't generate that content right now.",
                "agent_used": "content_agent", "agent_done": True, "agent_error": str(e)}


async def greeting_handler_node(state: AIState) -> dict:
    from app.utils.language import is_english_query

    is_english = is_english_query(state.message) if state.message else False
    if is_english:
        reply = (
            "👋 Welcome to *GLG Assets*! I'm your AI real estate assistant.\n\n"
            "I can help you with:\n"
            "🏢 *Property Search* — Find your dream home\n"
            "📋 *Project Info* — Details about our developments\n"
            "❓ *FAQs* — Answer your questions\n"
            "📅 *Schedule Visit* — Book a site tour\n\n"
            "How can I help you today? 😊"
        )
    else:
        reply = (
            "👋 *GLG Assets*-এ আপনাকে স্বাগতম! আমি আপনার AI রিয়েল এস্টেট অ্যাসিস্ট্যান্ট।\n\n"
            "আমি আপনাকে যেভাবে সাহায্য করতে পারি:\n"
            "🏢 *প্রপার্টি সার্চ* — আপনার স্বপ্নের বাড়ি খুঁজুন\n"
            "📋 *প্রজেক্ট তথ্য* — আমাদের প্রজেক্ট সমূহের বিস্তারিত\n"
            "❓ *FAQs* — যেকোনো প্রশ্নের উত্তর\n"
            "📅 *সাইট ভিজিট* — ভিজিট সিডিউল বুক করুন\n\n"
            "আজ আপনাকে কীভাবে সাহায্য করতে পারি? 😊"
        )
    return {
        "agent_reply": reply,
        "agent_used": "greeting_handler",
        "agent_done": True,
        "requires_escalation": False,
    }


async def booking_handler_node(state: AIState) -> dict:
    from app.repositories.contact_repository import contact_repository
    from app.tools.booking_tool import SiteVisitProposalInput, booking_tool
    from app.utils.language import is_english_query

    is_english = is_english_query(state.message) if state.message else False
    contact_card = contact_repository.format_contact_card(is_english=is_english)

    # Pillar 3: Governed Booking Tool with Tier 3 HITL approval gate
    client_name = getattr(state, "sender_name", None) or "Valued Client"
    client_contact = getattr(state, "sender_id", None) or "WhatsApp Client"
    project_target = (state.intent.entities or {}).get("project") or "GLG Luxury Project"

    proposal_input = SiteVisitProposalInput(
        client_name=client_name,
        phone_or_email=client_contact,
        project_name=project_target,
        preferred_date="To be coordinated",
        preferred_time_slot="Flexible",
        notes=state.message[:200] if state.message else None,
    )
    hitl_proposal = await booking_tool.propose_site_visit(proposal_input)

    if is_english:
        reply = (
            f"Thank you for your interest! 🎉\n\n"
            f"Your request for scheduling a private viewing (Status: *PENDING SALES CONFIRMATION*) has been submitted to our senior relationship desk in Banani. "
            f"A dedicated property consultant will contact you shortly to confirm the scheduled viewing slot.\n\n"
            f"{contact_card}"
        )
    else:
        reply = (
            f"আমাদের প্রজেক্টে সাইট পরিদর্শনের আগ্রহ প্রকাশের জন্য ধন্যবাদ! 🎉\n\n"
            f"আপনার পরিদর্শন অনুরোধটি (স্ট্যাটাস: *সেলস কনফার্মেশনের অপেক্ষায়*) আমাদের বনানী প্রধান কার্যালয়ের সিনিয়র রিলেশনশিপ ডেস্কে জমা দেওয়া হয়েছে। "
            f"আমাদের প্রতিনিধি খুব দ্রুত আপনার সাথে যোগাযোগ করে চূড়ান্ত সময়সূচী নিশ্চিত করবেন।\n\n"
            f"{contact_card}"
        )

    return {
        "agent_reply": reply,
        "agent_actions": [Action(type="escalate", payload={"reason": "site_visit_proposal_hitl", "priority": "high", "proposal": hitl_proposal})],
        "agent_used": "booking_handler",
        "agent_done": True,
        "requires_escalation": True,
        "escalation_reason": state.intent.escalation_reason or "HITL Site Visit Proposal Submitted",
    }


async def fallback_handler_node(state: AIState) -> dict:
    from app.prompts.fallback import FALLBACK_PROMPT
    from app.services.grounding_validator import grounding_validator
    from app.services.llm import llm_service
    from app.utils.language import is_english_query

    context_messages = [{"role": "system", "content": FALLBACK_PROMPT}]
    if state.rag_context:
        context_messages.append({"role": "system", "content": f"Relevant context:\n{state.rag_context}"})
    if state.history:
        for entry in state.history[-6:]:
            context_messages.append({"role": entry["role"], "content": entry["content"]})
    context_messages.append({"role": "user", "content": state.message})

    is_en = is_english_query(state.message) if state.message else False
    try:
        reply = await llm_service.chat(context_messages, temperature=0.2)
    except Exception:
        if is_en:
            reply = (
                "Thank you for contacting GLG Assets Limited. We are a premier luxury real-estate developer in Bangladesh. "
                "We assist exclusively with property inquiries, project developments, and site visits in Dhaka. "
                "Please let us know if you would like information regarding our luxury residential or commercial properties."
            )
        else:
            reply = (
                "GLG Assets Limited-এ যোগাযোগ করার জন্য ধন্যবাদ। আমরা বাংলাদেশের একটি প্রিমিয়াম লাক্সারি রিয়েল-এস্টেট ডেভেলপার প্রতিষ্ঠান। "
                "আমরা শুধুমাত্র ফ্ল্যাট, অ্যাপার্টমেন্ট ও আবাসন প্রকল্প সম্পর্কিত তথ্য ও সেবা প্রদান করে থাকি। "
                "আমাদের চলমান বা আসন্ন আবাসন প্রকল্প সম্পর্কে যেকোনো তথ্যের জন্য আমাদের জানাতে পারেন।"
            )

    # Validate fallback response
    val = grounding_validator.validate(reply_text=reply, is_english=is_en)
    if not val.is_grounded and val.sanitized_reply:
        reply = val.sanitized_reply

    return {"agent_reply": reply, "agent_used": "fallback", "agent_done": True}


# ── Safety Check ────────────────────────────────────────────

async def safety_check_node(state: AIState) -> dict:
    from app.services.llm import llm_service
    from app.services.policy_engine import policy_engine
    from app.utils.language import is_english_query

    if not state.agent_reply.strip():
        return {"safety_check_passed": True, "safety_checked": True}

    is_en = is_english_query(state.message) if state.message else False

    # 1. Deterministic Policy Engine Outbound Evaluation (Pillar 1: Grounding & Leak Protection)
    policy_res = policy_engine.evaluate_outbound_response(state.agent_reply, is_english=is_en)
    sanitized_reply = policy_res.sanitized_text or state.agent_reply

    if not policy_res.is_allowed and policy_res.action == "block":
        return {
            "agent_reply": sanitized_reply,
            "requires_escalation": True,
            "safety_check_passed": False,
            "safety_checked": True,
        }

    # 2. LLM-based Safety Content Check
    prompt = f"""You are a safety checker. Review this message for harmful or inappropriate content.
Reply should be allowed for a real-estate customer communication channel.

Message: "{sanitized_reply[:500]}"

Respond with JSON: {{"safe": true, "reason": ""}} or {{"safe": false, "reason": "..."}}"""

    try:
        result = await llm_service.structured_chat(
            [{"role": "user", "content": prompt}], json_schema={}, temperature=0.1,
        )
        if result.get("safe") is False:
            return {
                "agent_reply": "I'm sorry, I couldn't generate an appropriate response. Let me connect you with a team member.",
                "requires_escalation": True,
                "safety_check_passed": False,
                "safety_checked": True,
            }
        return {"agent_reply": sanitized_reply, "safety_check_passed": True, "safety_checked": True}
    except Exception:
        return {"agent_reply": sanitized_reply, "safety_check_passed": True, "safety_checked": True}


# ── Response Builder ────────────────────────────────────────

async def response_builder_node(state: AIState) -> dict:
    from app.schemas.chat import MemoryEntry
    from app.services.belief_memory import belief_memory_service
    from app.services.memory import conversation_memory

    user_entry = MemoryEntry(role="user", content=state.message)
    await conversation_memory.add(state.conversation_id, user_entry)

    assistant_entry = MemoryEntry(role="assistant", content=state.agent_reply)
    await conversation_memory.add(state.conversation_id, assistant_entry)

    # Persist updated belief state
    await belief_memory_service.save_beliefs(state.conversation_id, state.beliefs)

    return {"output_built": True}


async def output_formatter_node(state: AIState) -> dict:
    return {}


# ── Lead Intent Scoring Engine ───────────────────────────────

async def lead_scoring_node(state: AIState) -> dict:
    """Computes a Lead Intent Score (0-100) based on budget, timeline, and engagement."""
    msg_lower = state.message.lower()
    
    # 1. Budget Readiness (max 35 pts)
    budget_pts = 0
    budget_status = "unknown"
    has_active_budget = bool(state.beliefs.budget_max or state.beliefs.budget_raw)
    if has_active_budget or any(k in msg_lower for k in ["crore", "lakh", "budget", "$", "৳", "price", "cost", "cash", "loan", "financing"]):
        if has_active_budget or any(k in msg_lower for k in ["crore", "lakh", "under", "ready", "pre-approved", "$", "৳"]):
            budget_pts = 35
            budget_status = "ready"
        else:
            budget_pts = 20
            budget_status = "exploratory"

    # 2. Timeline & Urgency (max 35 pts)
    timeline_pts = 0
    timeline_urgency = "unknown"
    if any(k in msg_lower for k in ["visit", "tour", "tomorrow", "schedule", "book", "urgent", "ready to buy", "handover", "next week"]):
        timeline_pts = 35
        timeline_urgency = "immediate"
    elif any(k in msg_lower for k in ["month", "soon", "planning", "duplex", "flat"]):
        timeline_pts = 20
        timeline_urgency = "1-3_months"

    # 3. Engagement Depth & Intent (max 30 pts)
    engagement_pts = 0
    channel_depth = "medium" if state.channel in ["whatsapp", "instagram"] else "low"
    
    if state.intent.intent in ["booking", "lead"]:
        engagement_pts += 20
    elif state.intent.intent == "property_search":
        engagement_pts += 15

    if len(state.history) >= 2:
        engagement_pts += 10
        channel_depth = "high"

    total_score = min(100, budget_pts + timeline_pts + engagement_pts)
    is_hot = total_score >= 80 or state.intent.intent in ["booking", "lead"]

    lead_score_obj = LeadScore(
        score=total_score,
        budget_status=budget_status,
        timeline_urgency=timeline_urgency,
        channel_depth=channel_depth,
        high_priority_hot_lead=is_hot,
        scoring_breakdown={
            "budget_pts": budget_pts,
            "timeline_pts": timeline_pts,
            "engagement_pts": engagement_pts,
        }
    )

    updates = {"lead_score": lead_score_obj}
    if is_hot:
        updates["requires_escalation"] = True
        updates["escalation_reason"] = f"🔥 HOT LEAD (Score {total_score}/100) — High Intent Sales Opportunity"

    return updates


# ── Graph Builder ───────────────────────────────────────────

def build_ai_graph() -> CompiledStateGraph:
    workflow = StateGraph(AIState)

    workflow.add_node("entry", entry_node)
    workflow.add_node("moderation", moderation_node)
    workflow.add_node("blocked", blocked_node)
    workflow.add_node("memory_load", memory_load_node)
    workflow.add_node("memory_reflection", memory_reflection_node)
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("lead_scoring", lead_scoring_node)
    workflow.add_node("greeting_handler", greeting_handler_node)
    workflow.add_node("booking_handler", booking_handler_node)
    workflow.add_node("property_agent", property_agent_node)
    workflow.add_node("faq_agent", faq_agent_node)
    workflow.add_node("content_agent", content_agent_node)
    workflow.add_node("fallback_handler", fallback_handler_node)
    workflow.add_node("safety_check", safety_check_node)
    workflow.add_node("response_builder", response_builder_node)
    workflow.add_node("output_formatter", output_formatter_node)

    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "moderation")
    workflow.add_conditional_edges("moderation", moderation_router, {
        "blocked": "blocked",
        "memory_load": "memory_load",
    })
    workflow.add_edge("blocked", "safety_check")
    workflow.add_edge("memory_load", "memory_reflection")
    workflow.add_edge("memory_reflection", "supervisor")
    workflow.add_edge("supervisor", "lead_scoring")
    workflow.add_conditional_edges("lead_scoring", intent_router, {
        "greeting_handler": "greeting_handler",
        "booking_handler": "booking_handler",
        "property_agent": "property_agent",
        "faq_agent": "faq_agent",
        "content_agent": "content_agent",
        "fallback_handler": "fallback_handler",
    })
    for agent in ["greeting_handler", "booking_handler", "property_agent", "faq_agent", "content_agent", "fallback_handler"]:
        workflow.add_edge(agent, "safety_check")
    workflow.add_edge("safety_check", "response_builder")
    workflow.add_edge("response_builder", "output_formatter")
    workflow.add_edge("output_formatter", END)

    return workflow.compile()


SUPERVISOR_PROMPT = """You are an intent classifier for a real-estate company called GLG Assets.
Analyze the user's message and classify their intent into exactly one of these categories:
- property_search: Looking for properties, units, inventory, projects, or asking about available real estate (e.g., "Banani te ki ache", "Gulshan e flat ache?", "What 3BHK units are available?")
- faq: General question about the company, services, process, documentation requirements
- content_request: Asking to create content like captions, descriptions, social media posts
- booking: Wants to schedule a site visit, tour, or meeting
- lead: Wants to be contacted or expressing interest in buying/renting
- complaint: Has a complaint or issue
- greeting: Saying hello or starting a conversation
- chitchat: General conversation, trivia, or general knowledge not related to real estate
- other: None of the above
CRITICAL RULE FOR BANGLISH: If the message asks "ki ache", "konta ache", or specifies a location like "Banani", classify as property_search.
Respond as JSON:
{"intent": "one_of_the_above", "confidence": 0.0-1.0, "entities": {"project": "", "location": "", "bedrooms": 0, "budget": ""}, "requires_escalation": false, "escalation_reason": ""}"""

MODERATION_PROMPT = """You are a content moderation assistant for GLG Assets, a real-estate company.
Analyze the user message for spam, toxicity, PII, or inappropriate content.
Respond with a JSON object:
{"is_spam": false, "is_toxic": false, "contains_pii": false, "is_inappropriate": false, "confidence": 0.0, "action": "allow|flag|block", "reason": ""}"""

ai_graph = build_ai_graph()
