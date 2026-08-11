"""Content Agent — generates marketing copy, captions, descriptions."""

from app.services.llm import llm_service
from app.prompts.base import CONTENT_AGENT_PROMPT


class ContentAgent:
    """Handles content generation requests."""

    async def generate_captions(self, topic: str, tone: str = "professional", count: int = 3) -> list[str]:
        """Generate social media captions for a topic."""
        messages = [
            {"role": "system", "content": CONTENT_AGENT_PROMPT},
            {
                "role": "user",
                "content": f"Generate {count} social media captions about '{topic}' in a {tone} tone. "
                           f"Return as a JSON array of strings."
            }
        ]
        result = await llm_service.structured_chat(messages, json_schema={}, temperature=0.7)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "captions" in result:
            return result["captions"]
        return [str(result)]

    async def generate_description(self, project_name: str, location: str, features: list[str]) -> str:
        """Generate a property description."""
        features_str = ", ".join(features)
        messages = [
            {"role": "system", "content": CONTENT_AGENT_PROMPT},
            {
                "role": "user",
                "content": f"Write a compelling property description for {project_name} located at {location}. "
                           f"Key features: {features_str}. Tone: luxurious and professional."
            }
        ]
        return await llm_service.chat(messages, temperature=0.5)

    async def generate_hashtags(self, topic: str, count: int = 8) -> list[str]:
        """Generate relevant hashtags."""
        messages = [
            {"role": "system", "content": CONTENT_AGENT_PROMPT},
            {
                "role": "user",
                "content": f"Generate {count} relevant hashtags for a post about '{topic}' in real estate. "
                           f"Return as a JSON array of strings."
            }
        ]
        result = await llm_service.structured_chat(messages, json_schema={}, temperature=0.6)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "hashtags" in result:
            return result["hashtags"]
        return [str(result)]


content_agent = ContentAgent()
