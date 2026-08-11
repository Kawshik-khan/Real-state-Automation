"""FAQ Agent — handles general questions about GLG Assets and real estate."""

from app.services.llm import llm_service
from app.prompts.base import FAQ_AGENT_PROMPT


# Common FAQs for quick response without LLM call
FAQ_ANSWERS = {
    "what documents are required": "For home purchase: PAN card, Aadhaar, IT returns (last 3 years), bank statements (last 6 months), and property agreement. For rental: Aadhaar, employment letter, bank statements, and rental agreement.",
    "payment terms": "Standard payment plan: 10% booking amount, 30% during construction (milestone-based), 60% at possession. Home loan financing available through all major banks.",
    "location": "GLG Assets has projects in Mumbai (Bandra, Andheri, Powai), Bangalore (Whitefield, Electronic City), and Goa (Palm Beach, Panjim).",
    "contact": "You can reach our team at team@glgassets.com or call our helpline at +91-1800-GLG-ASSET. We're available Mon-Sat, 9 AM to 7 PM.",
    "rent vs buy": "Buying is ideal for long-term investment (5+ years) with tax benefits on home loans. Renting offers flexibility with lower upfront costs. We can help with both options!",
}


class FAQAgent:
    """Handles general knowledge and FAQ conversations."""

    async def handle(self, message: str, extra_context: str = "") -> str:
        """Process a FAQ-type query.

        Args:
            message: The user's query.
            extra_context: Optional RAG context to inject into the prompt.
        """
        query_lower = message.lower()

        # Check against FAQ bank first
        for key, answer in FAQ_ANSWERS.items():
            if key in query_lower:
                return f"📋 *{key.title()}*\n\n{answer}"

        # Build system prompt with optional RAG context
        system_content = FAQ_AGENT_PROMPT + "\n\nCompany: GLG Assets is a premium real-estate developer operating in Mumbai, Bangalore, and Goa."
        if extra_context:
            system_content += "\n\nAdditional context:\n" + extra_context

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message}
        ]
        return await llm_service.chat(messages, temperature=0.3)


faq_agent = FAQAgent()
