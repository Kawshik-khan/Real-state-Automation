"""Automated Test Suite for Self-Correcting Memory & Dynamic Belief Reconciliation."""

import asyncio
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.agents.state import UserBeliefState, AIState
from app.services.belief_memory import belief_memory_service, BeliefMemoryService
from app.agents.graph import ai_graph

client = TestClient(app)
VALID_SECRET = settings.automation_shared_secret
AUTH_HEADERS = {"X-Automation-Secret": VALID_SECRET}


# ============================================================
#  1. BELIEF MEMORY SERVICE UNIT TESTS
# ============================================================

class TestBeliefMemoryUnit:
    def test_initial_beliefs_are_empty(self):
        async def _run():
            service = BeliefMemoryService()
            beliefs = await service.get_beliefs("test_conv_empty")
            assert beliefs.preferred_locations == []
            assert beliefs.budget_max is None
            assert beliefs.bedrooms is None
            assert beliefs.negative_constraints == []
            assert beliefs.revision_history == []
        asyncio.run(_run())

    def test_greeting_fast_path_bypasses_reconciliation(self):
        async def _run():
            service = BeliefMemoryService()
            current = UserBeliefState(preferred_locations=["Banani"])
            updated, revisions = await service.reconcile_beliefs(current, "Hello! Assalamu Alaikum", [])
            assert revisions == []
            assert updated.preferred_locations == ["Banani"]
        asyncio.run(_run())

    def test_initial_preference_extraction(self):
        async def _run():
            service = BeliefMemoryService()
            current = UserBeliefState()
            message = "I am looking for a 3 bedroom apartment in Banani with budget 3.5 Crore"
            updated, revisions = await service.reconcile_beliefs(current, message, [])
            
            assert "Banani" in updated.preferred_locations
            assert updated.bedrooms == 3
            assert updated.budget_max is not None
            assert len(revisions) >= 1
        asyncio.run(_run())

    def test_explicit_correction_replaces_old_location(self):
        async def _run():
            service = BeliefMemoryService()
            # User previously had Banani as preferred location
            current = UserBeliefState(
                preferred_locations=["Banani"],
                budget_max=35000000.0,
                budget_raw="3.5 Crore",
                bedrooms=3,
            )
            # User explicitly changes their mind
            message = "Actually, changed my mind. Not Banani, I want Gulshan 2 instead, and budget is 5 Crore"
            updated, revisions = await service.reconcile_beliefs(current, message, [
                {"role": "user", "content": "I am looking for Banani 3.5 Crore"},
                {"role": "assistant", "content": "Here are options in Banani."},
            ])

            # Banani must be superseded by Gulshan 2 (or Gulshan)
            assert any("Gulshan" in loc for loc in updated.preferred_locations)
            assert "Banani" not in updated.preferred_locations
            # Budget must be updated to 5 Crore
            assert updated.budget_max == 50000000.0
            # Revisions audit trail must record the change
            assert len(updated.revision_history) >= 1
            location_rev = next((r for r in updated.revision_history if r.get("field") == "preferred_locations"), None)
            assert location_rev is not None
            assert "Gulshan" in str(location_rev["new_value"])
        asyncio.run(_run())

    def test_negative_constraint_registration(self):
        async def _run():
            service = BeliefMemoryService()
            current = UserBeliefState(preferred_locations=["Gulshan 2"])
            message = "Do not show me ground floor units. No ground floor please."
            updated, revisions = await service.reconcile_beliefs(current, message, [])

            assert any("ground floor" in neg.lower() for neg in updated.negative_constraints)
            assert len(revisions) >= 1
        asyncio.run(_run())


# ============================================================
#  2. INTROSPECTION & AUDIT API ENDPOINTS
# ============================================================

class TestMemoryApiEndpoints:
    def test_get_beliefs_requires_auth(self):
        response = client.get("/api/v1/memory/conv_test_123/beliefs")
        assert response.status_code == 401

    def test_get_and_correct_beliefs_lifecycle(self):
        conv_id = "conv_test_audit_lifecycle"

        # 1. Inspect initial empty beliefs
        res = client.get(f"/api/v1/memory/{conv_id}/beliefs", headers=AUTH_HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert data["conversation_id"] == conv_id
        assert data["beliefs"]["preferred_locations"] == []

        # 2. Perform manual correction via dashboard API
        override_payload = {
            "field": "preferred_locations",
            "new_value": ["Baridhara Diplomatic Zone"],
            "reason": "Customer called sales desk directly to update preference",
        }
        post_res = client.post(
            f"/api/v1/memory/{conv_id}/correct",
            json=override_payload,
            headers=AUTH_HEADERS,
        )
        assert post_res.status_code == 200
        post_data = post_res.json()
        assert post_data["status"] == "success"
        assert post_data["current_beliefs"]["preferred_locations"] == ["Baridhara Diplomatic Zone"]
        assert len(post_data["current_beliefs"]["revision_history"]) == 1

        # 3. Verify GET returns the updated belief
        check_res = client.get(f"/api/v1/memory/{conv_id}/beliefs", headers=AUTH_HEADERS)
        assert check_res.status_code == 200
        assert check_res.json()["beliefs"]["preferred_locations"] == ["Baridhara Diplomatic Zone"]

        # 4. Reset beliefs
        del_res = client.delete(f"/api/v1/memory/{conv_id}/beliefs", headers=AUTH_HEADERS)
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"

        # 5. Verify beliefs are cleared
        final_check = client.get(f"/api/v1/memory/{conv_id}/beliefs", headers=AUTH_HEADERS)
        assert final_check.json()["beliefs"]["preferred_locations"] == []


# ============================================================
#  3. LANGGRAPH INTEGRATION END-TO-END FLOW
# ============================================================

class TestLangGraphSelfCorrectionFlow:
    def test_langgraph_reflection_updates_state(self):
        async def _run():
            conv_id = "test_graph_correction_flow"

            # Turn 1: Initial query
            state_turn1 = AIState(
                message="Do you have any 3 bedroom flats in Banani under 3.5 Crore?",
                conversation_id=conv_id,
                channel="whatsapp",
            )
            result1 = await ai_graph.ainvoke(state_turn1)
            assert result1.get("output_built") is True
            assert "Banani" in result1.get("beliefs").preferred_locations

            # Turn 2: User explicitly corrects location to Gulshan
            state_turn2 = AIState(
                message="Actually, skip Banani, I want Gulshan 2 instead, budget 5 Crore",
                conversation_id=conv_id,
                channel="whatsapp",
            )
            result2 = await ai_graph.ainvoke(state_turn2)
            assert result2.get("output_built") is True
            
            reconciled_beliefs = result2.get("beliefs")
            assert any("Gulshan" in loc for loc in reconciled_beliefs.preferred_locations)
            assert "Banani" not in reconciled_beliefs.preferred_locations
            assert reconciled_beliefs.budget_max == 50000000.0
            assert len(reconciled_beliefs.revision_history) >= 1
        asyncio.run(_run())
