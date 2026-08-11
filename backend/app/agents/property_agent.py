"""Property Agent — handles property search and inquiries using PropertySearchTool."""

from app.services.llm import llm_service
from app.prompts.base import PROPERTY_AGENT_PROMPT
from app.tools.property_tool import property_search_tool, PROJECTS_DATABASE


class PropertyAgent:
    """Handles property search and inquiry conversations."""

    async def handle(self, message: str, entities: dict | None = None, extra_context: str = "") -> str:
        """Process a property query using SQL property search + RAG context."""
        entities = entities or {}
        location = entities.get("location")
        budget = entities.get("budget")

        # Run SQL Property Search Tool
        search_res = await property_search_tool.search(
            query=message,
            location=location,
        )

        projects = search_res.get("projects", [])
        if projects:
            formatted = []
            for p in projects:
                formatted.append(
                    f"🏢 *{p['name']}*\n"
                    f"📍 {p['location']}\n"
                    f"💰 Price: {p['price']} ({p['bedrooms']} BHK)\n"
                    f"📝 {p['description']}\n"
                    f"✨ Amenities: {', '.join(p['amenities'])}"
                )
            reply_header = f"I found {len(projects)} project(s) matching your criteria:\n\n"
            return reply_header + "\n\n---\n\n".join(formatted)

        # Fallback to LLM with full context
        system_content = PROPERTY_AGENT_PROMPT + f"\n\nAvailable projects catalog: {PROJECTS_DATABASE}"
        if extra_context:
            system_content += f"\n\nAdditional RAG context:\n{extra_context}"

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message}
        ]
        return await llm_service.chat(messages, temperature=0.3)

    async def get_projects(self) -> list[dict]:
        """Return all available projects."""
        return PROJECTS_DATABASE


property_agent = PropertyAgent()
