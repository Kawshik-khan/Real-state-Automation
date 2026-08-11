"""FAQ Agent — handles general questions about GLG Assets and real estate."""

from app.services.llm import llm_service
from app.prompts.base import FAQ_AGENT_PROMPT
from app.utils.language import is_english_query


# Common FAQs for quick response without LLM call
FAQ_ANSWERS_EN = {
    "what documents are required": ("Required Documents", "For home purchase: PAN card, Aadhaar, IT returns (last 3 years), bank statements (last 6 months), and property agreement. For rental: Aadhaar, employment letter, bank statements, and rental agreement."),
    "payment terms": ("Payment Terms", "Standard payment plan: 10% booking amount, 30% during construction (milestone-based), 60% at possession. Home loan financing available through all major banks."),
    "location": ("Project Locations", "GLG Assets has projects in Mumbai (Bandra, Andheri, Powai), Bangalore (Whitefield, Electronic City), and Goa (Palm Beach, Panjim)."),
    "contact": ("Contact Info", "You can reach our team at team@glgassets.com or call our helpline at +91-1800-GLG-ASSET. We're available Mon-Sat, 9 AM to 7 PM."),
    "rent vs buy": ("Rent vs Buy", "Buying is ideal for long-term investment (5+ years) with tax benefits on home loans. Renting offers flexibility with lower upfront costs. We can help with both options!"),
}

FAQ_ANSWERS_BN = {
    "document": ("প্রয়োজনীয় কাগজপত্র", "বাড়ি কেনার জন্য: PAN কার্ড, আধার, ইনকাম ট্যাক্স রিটার্ন (গত ৩ বছরের), ব্যাংক স্টেটমেন্ট (গত ৬ মাসের), এবং প্রপার্টি এগ্রিমেন্ট। ভাড়া নেওয়ার জন্য: আধার, চাকরির লেটার, ব্যাংক স্টেটমেন্ট ও রেন্টাল এগ্রিমেন্ট।"),
    "kagoj": ("প্রয়োজনীয় কাগজপত্র", "বাড়ি কেনার জন্য: PAN কার্ড, আধার, ইনকাম ট্যাক্স রিটার্ন (গত ৩ বছরের), ব্যাংক স্টেটমেন্ট (গত ৬ মাসের), এবং প্রপার্টি এগ্রিমেন্ট।"),
    "payment": ("পেমেন্ট সংক্রান্ত তথ্য", "স্ট্যান্ডার্ড পেমেন্ট প্ল্যান: ১০% বুকিং অ্যামাউন্ট, ৩০% কনস্ট্রাকশনের সময় (মাইলস্টোন ভিত্তিক), এবং ৬০% পজেশনের সময়। প্রধান ব্যাংকগুলোর মাধ্যমে হোম লোন সুবিধা রয়েছে।"),
    "taka": ("পেমেন্ট সংক্রান্ত তথ্য", "স্ট্যান্ডার্ড পেমেন্ট প্ল্যান: ১০% বুকিং অ্যামাউন্ট, ৩০% কনস্ট্রাকশনের সময় (মাইলস্টোন ভিত্তিক), এবং ৬০% পজেশনের সময়।"),
    "location": ("প্রজেক্টের লোকেশন", "GLG Assets-এর প্রজেক্টসমূহ মুম্বাই (বান্ধ্রা, আন্ধেরি, পওয়াই), ব্যাঙ্গালোর (হোয়াইটফিল্ড, ইলেকট্রনিক সিটি), এবং গোয়াতে (পাম বিচ, পঞ্জিম) অবস্থিত।"),
    "kothay": ("প্রজেক্টের লোকেশন", "GLG Assets-এর প্রজেক্টসমূহ মুম্বাই (বান্ধ্রা, আন্ধেরি, পওয়াই), ব্যাঙ্গালোর (হোয়াইটফিল্ড, ইলেকট্রনিক সিটি), এবং গোয়াতে (পাম বিচ, পঞ্জিম) অবস্থিত।"),
    "contact": ("যোগাযোগের বিবরণ", "আমাদের সাথে যোগাযোগ করুন team@glgassets.com ইমেইলে অথবা কল করুন হেল্পলাইনে +91-1800-GLG-ASSET (সোম-শনি, সকাল ৯টা - সন্ধ্যা ৭টা)।"),
    "jogajog": ("যোগাযোগের বিবরণ", "আমাদের সাথে যোগাযোগ করুন team@glgassets.com ইমেইলে অথবা কল করুন হেল্পলাইনে +91-1800-GLG-ASSET (সোম-শনি, সকাল ৯টা - সন্ধ্যা ৭টা)।"),
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
        is_english = is_english_query(message)

        # Check against FAQ bank first
        if is_english:
            for key, (title, answer) in FAQ_ANSWERS_EN.items():
                if key in query_lower:
                    return f"📋 *{title}*\n\n{answer}"
        else:
            for key, (title, answer) in FAQ_ANSWERS_BN.items():
                if key in query_lower:
                    return f"📋 *{title}*\n\n{answer}"

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

