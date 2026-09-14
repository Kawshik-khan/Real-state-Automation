"""Self-Correcting Belief Memory Service for Real Estate Customer Conversations.

Tracks dynamic user beliefs and constraints (location, budget, bedroom count, facing,
negative exclusions) across multi-turn interactions.
Detects explicit and implicit user corrections (e.g. changing locations or budgets),
reconciles contradictions, and maintains a timestamped audit trail of belief revisions.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from app.agents.state import UserBeliefState
from app.services.llm import llm_service

RECONCILIATION_PROMPT = """You are an expert cognitive memory reconciliation engine for a luxury real estate advisory platform (GLG Assets).
Your task is to analyze the user's latest message in context of their current belief state and conversation history.

Detect any of the following:
1. EXPLICIT CORRECTIONS: User correcting a previous assumption, detail, or preference (e.g., "No, I said 3 bedrooms, not 2", "Actually, I changed my mind", "Not Banani, I want Gulshan").
2. CONSTRAINTS UPDATE: User changing budget, moving location, or setting new property criteria.
3. NEGATIVE CONSTRAINTS: Explicit dislikes, exclusions, or dealbreakers (e.g., "Do not show me ground floor", "Never Mirpur", "No low ceilings").
4. PROFILE UPDATES: Name, phone, investor vs end-user status.

CRITICAL RULES:
- When a user explicitly changes a preference (e.g. from Banani to Gulshan 2), the old preference MUST be invalidated/replaced, NOT merged.
- If the user says "exclude X" or "skip X" or "no X", add X to excluded_locations or negative_constraints.
- Normalize Bangladesh budget amounts: "1 Crore" = 10,000,000 BDT, "50 Lakh" = 5,000,000 BDT.
- If the message has NO new constraints and NO corrections (e.g. general questions like "does it have a gym?"), return has_correction: false and keep current_state intact.

Respond with strict JSON matching this schema:
{
  "has_correction": true/false,
  "revisions": [
    {
      "field": "preferred_locations | excluded_locations | budget_max | budget_min | bedrooms | facing | handover_status | negative_constraints | buyer_profile",
      "old_value": any,
      "new_value": any,
      "reason": "Clear explanation of why this belief was updated or superseded"
    }
  ],
  "updated_state": {
    "preferred_locations": ["string"],
    "excluded_locations": ["string"],
    "budget_min": number or null,
    "budget_max": number or null,
    "budget_raw": "string or null",
    "bedrooms": number or null,
    "facing": "string or null",
    "handover_status": "string or null",
    "negative_constraints": ["string"],
    "buyer_profile": {}
  }
}"""


class BeliefMemoryService:
    """Manages active customer constraints, preference beliefs, and contradiction resolution."""

    def __init__(self):
        self._cache: dict[str, UserBeliefState] = {}

    async def get_beliefs(self, conversation_id: str) -> UserBeliefState:
        """Retrieve active belief state from cache or database."""
        if conversation_id in self._cache:
            return self._cache[conversation_id]

        # Attempt to load from database
        try:
            from app.database import async_session_factory, is_db_reachable
            if is_db_reachable():
                from sqlalchemy import text
                async with async_session_factory() as session:
                    result = await session.execute(
                        text("SELECT beliefs FROM conversations WHERE conversation_id = :cid"),
                        {"cid": conversation_id},
                    )
                    row = result.fetchone()
                    if row and row[0]:
                        data = row[0] if isinstance(row[0], dict) else json.loads(row[0])
                        beliefs = UserBeliefState(**data)
                        self._cache[conversation_id] = beliefs
                        return beliefs
        except Exception:
            pass

        new_beliefs = UserBeliefState()
        self._cache[conversation_id] = new_beliefs
        return new_beliefs

    async def save_beliefs(self, conversation_id: str, beliefs: UserBeliefState):
        """Persist belief state into cache and PostgreSQL."""
        self._cache[conversation_id] = beliefs
        try:
            from app.database import async_session_factory, is_db_reachable
            if is_db_reachable():
                from sqlalchemy import text
                beliefs_json = json.dumps(beliefs.model_dump())
                async with async_session_factory() as session:
                    await session.execute(
                        text("""
                            UPDATE conversations 
                            SET beliefs = CAST(:b AS jsonb) 
                            WHERE conversation_id = :cid
                        """),
                        {"b": beliefs_json, "cid": conversation_id},
                    )
                    await session.commit()
        except Exception:
            # Fallback for SQLite or environments without beliefs column
            pass

    async def reset_beliefs(self, conversation_id: str):
        """Clear customer beliefs."""
        self._cache.pop(conversation_id, None)
        try:
            from app.database import async_session_factory, is_db_reachable
            if is_db_reachable():
                from sqlalchemy import text
                async with async_session_factory() as session:
                    await session.execute(
                        text("UPDATE conversations SET beliefs = NULL WHERE conversation_id = :cid"),
                        {"cid": conversation_id},
                    )
                    await session.commit()
        except Exception:
            pass

    async def reconcile_beliefs(
        self,
        current: UserBeliefState,
        user_message: str,
        history: list[dict],
    ) -> tuple[UserBeliefState, list[dict]]:
        """Evaluate new message against active beliefs and reconcile any contradictions or corrections.

        Returns:
            (updated_belief_state, list_of_new_revisions)
        """
        if not user_message or not user_message.strip():
            return current, []

        msg_lower = user_message.lower().strip()

        # ── Fast Path 1: Pure greetings or short acknowledgements ──
        if msg_lower in [
            "hi", "hello", "hey", "salam", "assalamu alaikum", "thanks", 
            "thank you", "ok", "okay", "yes", "no", "sure"
        ]:
            return current, []

        # ── Fast Path 2: Heuristic Detection for Real Estate Entities & Corrections ──
        correction_signals = [
            "actually", "instead of", "changed my mind", "change", "not ", "skip ",
            "cancel ", "don't want", "dont want", "do not want", "exclude", "never",
            "no ground floor", "budget is", "my budget", "my name is", "i meant",
            "i said", "correction", "crore", "lakh", "bedroom", "bhk", "flat in",
            "apartment in", "gulshan", "banani", "uttara", "dhanmondi", "purbachal", "mirpur"
        ]

        has_signal = any(sig in msg_lower for sig in correction_signals)
        # If user mentions a property keyword or location that differs from active state, trigger reconciliation
        if not has_signal and not any(loc.lower() in msg_lower for loc in current.preferred_locations):
            # Check if any standard location is mentioned
            for loc in ["gulshan", "banani", "uttara", "dhanmondi", "mirpur", "purbachal", "baridhara", "bashundhara"]:
                if loc in msg_lower:
                    has_signal = True
                    break

        if not has_signal:
            return current, []

        # ── LLM Structured Cognitive Reflection ──
        history_context = ""
        if history:
            history_context = "\n".join(
                f"{h.get('role', 'user').upper()}: {h.get('content', '')[:200]}"
                for h in history[-4:]
            )

        prompt_input = (
            f"CURRENT BELIEF STATE:\n{json.dumps(current.model_dump(), indent=2)}\n\n"
            f"RECENT CONVERSATION HISTORY:\n{history_context or 'None'}\n\n"
            f"LATEST USER MESSAGE:\n\"{user_message}\"\n\n"
            "Analyze and reconcile any changes or corrections."
        )

        try:
            result = await llm_service.structured_chat(
                [
                    {"role": "system", "content": RECONCILIATION_PROMPT},
                    {"role": "user", "content": prompt_input},
                ],
                json_schema={},
                temperature=0.1,
            )

            if not isinstance(result, dict) or not result.get("has_correction"):
                # Heuristic fallback if LLM deemed false but message explicitly has location/budget
                return self._heuristic_reconciliation(current, user_message)

            raw_revisions = result.get("revisions", [])
            updated_state_dict = result.get("updated_state", {})

            # Construct updated UserBeliefState
            new_beliefs = current.model_copy(deep=True)

            if "preferred_locations" in updated_state_dict:
                new_beliefs.preferred_locations = [
                    loc.strip().title() for loc in updated_state_dict["preferred_locations"] if loc
                ]
            if "excluded_locations" in updated_state_dict:
                new_beliefs.excluded_locations = [
                    loc.strip().title() for loc in updated_state_dict["excluded_locations"] if loc
                ]
            if "budget_min" in updated_state_dict:
                new_beliefs.budget_min = updated_state_dict["budget_min"]
            if "budget_max" in updated_state_dict:
                new_beliefs.budget_max = updated_state_dict["budget_max"]
            if "budget_raw" in updated_state_dict:
                new_beliefs.budget_raw = updated_state_dict["budget_raw"]
            if "bedrooms" in updated_state_dict:
                new_beliefs.bedrooms = updated_state_dict["bedrooms"]
            if "facing" in updated_state_dict:
                new_beliefs.facing = updated_state_dict["facing"]
            if "handover_status" in updated_state_dict:
                new_beliefs.handover_status = updated_state_dict["handover_status"]
            if "negative_constraints" in updated_state_dict:
                new_beliefs.negative_constraints = updated_state_dict["negative_constraints"]
            if "buyer_profile" in updated_state_dict and updated_state_dict["buyer_profile"]:
                new_beliefs.buyer_profile.update(updated_state_dict["buyer_profile"])

            # Append timestamped revisions to revision_history
            now_iso = datetime.now(timezone.utc).isoformat()
            new_revisions_logged = []
            for rev in raw_revisions:
                logged_rev = {
                    "field": rev.get("field", "unknown"),
                    "old_value": rev.get("old_value"),
                    "new_value": rev.get("new_value"),
                    "reason": rev.get("reason", "User updated preference"),
                    "timestamp": now_iso,
                }
                new_beliefs.revision_history.append(logged_rev)
                new_revisions_logged.append(logged_rev)

            return new_beliefs, new_revisions_logged

        except Exception:
            # Deterministic heuristic fallback in case of LLM service failure
            return self._heuristic_reconciliation(current, user_message)

    def _heuristic_reconciliation(
        self, current: UserBeliefState, user_message: str
    ) -> tuple[UserBeliefState, list[dict]]:
        """Deterministic rule-based fallback for location and budget corrections."""
        msg_lower = user_message.lower()
        new_beliefs = current.model_copy(deep=True)
        revisions = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Location detection
        known_locations = [
            "Gulshan 2", "Gulshan 1", "Gulshan", "Banani", "Uttara", 
            "Dhanmondi", "Baridhara", "Bashundhara", "Mirpur", "Purbachal"
        ]

        found_loc = None
        for loc in known_locations:
            if loc.lower() in msg_lower:
                found_loc = loc
                break

        if found_loc:
            # Check if user is excluding or switching
            if any(neg in msg_lower for neg in ["not", "skip", "exclude", "instead of", "changed my mind"]):
                if current.preferred_locations and found_loc not in current.preferred_locations:
                    old_locs = list(current.preferred_locations)
                    new_beliefs.preferred_locations = [found_loc]
                    # Add old loc to excluded if explicitly stated "not X"
                    rev = {
                        "field": "preferred_locations",
                        "old_value": old_locs,
                        "new_value": [found_loc],
                        "reason": f"Heuristic detected location shift to {found_loc}",
                        "timestamp": now_iso,
                    }
                    new_beliefs.revision_history.append(rev)
                    revisions.append(rev)
            elif not current.preferred_locations:
                new_beliefs.preferred_locations = [found_loc]
                rev = {
                    "field": "preferred_locations",
                    "old_value": [],
                    "new_value": [found_loc],
                    "reason": f"Initial location preference set to {found_loc}",
                    "timestamp": now_iso,
                }
                new_beliefs.revision_history.append(rev)
                revisions.append(rev)

        # 2. Budget detection (Crore / Lakh)
        crore_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|koti)", msg_lower)
        if crore_match:
            val = float(crore_match.group(1)) * 10000000
            old_val = new_beliefs.budget_max
            new_beliefs.budget_max = val
            new_beliefs.budget_raw = f"{crore_match.group(1)} Crore"
            rev = {
                "field": "budget_max",
                "old_value": old_val,
                "new_value": val,
                "reason": f"Heuristic parsed budget of {new_beliefs.budget_raw}",
                "timestamp": now_iso,
            }
            new_beliefs.revision_history.append(rev)
            revisions.append(rev)

        # 3. Bedroom detection
        bed_match = re.search(r"(\d)\s*(?:bed|bedroom|bhk)", msg_lower)
        if bed_match:
            beds = int(bed_match.group(1))
            old_beds = new_beliefs.bedrooms
            new_beliefs.bedrooms = beds
            rev = {
                "field": "bedrooms",
                "old_value": old_beds,
                "new_value": beds,
                "reason": f"Heuristic parsed {beds} bedrooms",
                "timestamp": now_iso,
            }
            new_beliefs.revision_history.append(rev)
            revisions.append(rev)

        # 4. Negative constraint detection
        if "no ground floor" in msg_lower or "not ground floor" in msg_lower:
            if "no ground floor" not in new_beliefs.negative_constraints:
                new_beliefs.negative_constraints.append("no ground floor")
                rev = {
                    "field": "negative_constraints",
                    "old_value": [],
                    "new_value": ["no ground floor"],
                    "reason": "Heuristic parsed explicit exclusion: no ground floor",
                    "timestamp": now_iso,
                }
                new_beliefs.revision_history.append(rev)
                revisions.append(rev)

        return new_beliefs, revisions


belief_memory_service = BeliefMemoryService()
