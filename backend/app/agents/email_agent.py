"""Email Agent — Specialized AI Agent for Email Ingestion & Auto-Reply Generation.

Processes email thread context, parses attachments, performs RAG retrieval on property
catalogs & FAQs, evaluates confidence/risk, and generates structured email replies.
"""

from typing import Any, Dict, List, Optional
import logging

from app.services.llm import llm_service
from app.services.attachment_parser import attachment_parser

logger = logging.getLogger(__name__)

EMAIL_AGENT_SYSTEM_PROMPT = """You are the Lead Executive AI Email Representative for GLG Assets Real Estate.
Your responsibility is to generate formal, highly professional, polite, and accurate email responses to customer inquiries.

GUIDELINES:
1. Tone: Warm, executive, professional real-estate advisor.
2. Structure:
   - Greeting (e.g. "Dear [Customer Name],")
   - Gratitude for contacting GLG Assets
   - Clear, direct, structured answer to their specific questions (use clean bullet points if summarizing property details, unit availability, or payment terms)
   - Call to Action (e.g. scheduling a private property tour or speaking with a dedicated property manager)
   - Formal Sign-off ("Best regards,\nGLG Assets Client Services Team")
3. Context: Rely on property information, payment options, and FAQs provided below.
4. Accuracy: Do NOT invent property features or prices not backed by the provided knowledge.

KNOWLEDGE BASE CONTEXT:
- GLG Gulshan Heights: Premium luxury residential complex in Gulshan, 3-4 BHK apartments, modern amenities (rooftop pool, gym, 24/7 security). Starting price $250,000 / BDT 3.5 Crore.
- Payment Terms: 10% booking amount, 30% milestone construction-linked payments, 60% upon possession. Home loan financing available through partner banks.
- Location: Gulshan Avenue, Dhaka, Bangladesh.
"""


class EmailAgent:
    """Specialized AI Agent for Email Automation."""

    async def process_email(
        self,
        subject: str,
        body_text: str,
        sender_name: Optional[str] = None,
        sender_email: str = "",
        thread_history: Optional[List[Dict[str, str]]] = None,
        attachment_texts: Optional[List[str]] = None,
        rag_context: str = "",
    ) -> Dict[str, Any]:
        """Processes an incoming email message within its thread context and generates an AI draft response."""

        # 1. Format thread history
        history_str = ""
        if thread_history:
            formatted_turns = []
            for turn in thread_history[-5:]:
                role = turn.get("sender_type", turn.get("role", "customer"))
                content = turn.get("body_text", turn.get("text", turn.get("content", "")))
                formatted_turns.append(f"[{role.upper()}]: {content[:400]}")
            history_str = "\n".join(formatted_turns)

        # 2. Format attachment context
        attachments_str = ""
        if attachment_texts:
            attachments_str = "\n\n--- EXTRACTED ATTACHMENT TEXT ---\n" + "\n".join(attachment_texts)

        # 3. Assemble complete context prompt
        full_user_content = f"SENDER: {sender_name or sender_email} ({sender_email})\n"
        full_user_content += f"SUBJECT: {subject}\n"
        if history_str:
            full_user_content += f"\n--- EMAIL THREAD HISTORY ---\n{history_str}\n"
        full_user_content += f"\n--- LATEST INCOMING EMAIL ---\n{body_text}\n"
        if attachments_str:
            full_user_content += attachments_str
        if rag_context:
            full_user_content += f"\n--- ADDITIONAL RAG PROPERTY KNOWLEDGE ---\n{rag_context}\n"

        # 4. LLM Generation
        messages = [
            {"role": "system", "content": EMAIL_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": full_user_content},
        ]

        try:
            raw_reply = await llm_service.chat(messages, temperature=0.3)
        except Exception as e:
            logger.error(f"LLM call failed in EmailAgent: {e}")
            raw_reply = (
                f"Thank you for contacting GLG Assets regarding '{subject}'. "
                "Our real estate advisory team has received your inquiry and will provide detailed property specifications shortly."
            )

        # 5. Intent Classification & Confidence Evaluation
        intent, priority, confidence = self._evaluate_intent_and_confidence(body_text, subject)

        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

        # 6. Policy decision
        # High confidence (>=0.85) and low-risk inquiry -> AUTO_SEND
        # Low confidence or high priority / complaint / pricing negotiation -> REQUIRES_APPROVAL
        auto_send_eligible = (
            confidence >= 0.85
            and priority != "high"
            and intent not in ["complaint", "price_negotiation"]
        )

        action = "AUTO_SEND" if auto_send_eligible else "REQUIRES_APPROVAL"

        return {
            "reply_subject": reply_subject,
            "reply_body": raw_reply,
            "intent": intent,
            "priority": priority,
            "confidence_score": confidence,
            "action": action,
            "auto_send_eligible": auto_send_eligible,
        }

    def _evaluate_intent_and_confidence(
        self, body_text: str, subject: str
    ) -> tuple[str, str, float]:
        """Simple heuristic intent & confidence scorer (backed by LLM prompts)."""
        combined = f"{subject} {body_text}".lower()

        if any(w in combined for w in ["cancel", "complaint", "legal", "scam", "refund", "issue"]):
            return "complaint", "high", 0.60
        elif any(w in combined for w in ["discount", "negotiate", "lowest price", "best offer", "deal"]):
            return "price_negotiation", "high", 0.70
        elif any(w in combined for w in ["tour", "visit", "schedule", "appointment", "see property"]):
            return "tour_request", "high", 0.90
        elif any(w in combined for w in ["price", "cost", "brochure", "floor plan", "details", "available"]):
            return "property_inquiry", "normal", 0.88
        else:
            return "general_inquiry", "normal", 0.82


email_agent = EmailAgent()
