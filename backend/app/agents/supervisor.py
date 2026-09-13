"""Supervisor agent — classifies user intent and routes to the right handler."""

from app.prompts.base import SUPERVISOR_PROMPT
from app.services.llm import llm_service
from app.services.memory import conversation_memory


class SupervisorAgent:
    """Classifies intent and returns structured routing decision."""

    async def classify(self, message: str, conversation_id: str, channel: str = "whatsapp") -> dict:
        """Analyze message and return intent classification."""
        history = await conversation_memory.get_history(conversation_id)
        messages = [
            {"role": "system", "content": SUPERVISOR_PROMPT},
        ]
        # Add recent history for context
        for entry in history[-5:]:
            messages.append({"role": entry.role, "content": entry.content})
        messages.append({"role": "user", "content": f"Channel: {channel}\nMessage: {message}"})

        result = await llm_service.structured_chat(messages, json_schema={}, temperature=0.2)
        return result


supervisor = SupervisorAgent()
