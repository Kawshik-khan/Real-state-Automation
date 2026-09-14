"""Policy Repository — Company-Approved Legal, Financial & Documentation Guidelines.

Architecture Rule: Prompts must NOT invent legal/financial rules or documentation requirements.
All policy answers are versioned, approved, and retrieved from here.
"""
from typing import Any, Dict, Optional

APPROVED_POLICIES: Dict[str, Dict[str, Any]] = {
    "required_documents_purchase": {
        "policy_key": "required_documents_purchase",
        "title_en": "Required Documents for Apartment Purchase",
        "title_bn": "অ্যাপার্টমেন্ট কেনার প্রয়োজনীয় কাগজপত্র",
        "approved": True,
        "effective_from": "2026-09-01",
        "country": "Bangladesh",
        "answer_en": (
            "For purchasing a residential apartment with GLG Assets in Bangladesh, the standard required documents are:\n"
            "1. National ID (NID / Smart Card) or Valid Passport copy\n"
            "2. E-TIN Certificate and recent Tax Return acknowledgement receipt\n"
            "3. 2 copies of passport-sized photographs of buyer & nominee\n"
            "4. Bank statements (last 6-12 months)\n"
            "5. Executed GLG Assets Booking & Allotment Agreement.\n"
            "*For Non-Resident Bangladeshis (NRBs)*: Copy of valid foreign work permit/residence visa and FC/NITA bank account details."
        ),
        "answer_bn": (
            "GLG Assets-এর মাধ্যমে বাংলাদেশে অ্যাপার্টমেন্ট কেনার জন্য অনুমোদিত প্রয়োজনীয় কাগজপত্র:\n"
            "১. জাতীয় পরিচয়পত্র (NID / স্মার্ট কার্ড) অথবা বৈধ পাসপোর্টের কপি\n"
            "২. ই-টিন (e-TIN) সার্টিফিকেট ও সর্বশেষ আয়কর রিটার্ন জমার প্রমাণ\n"
            "৩. আবেদনকারী ও নমিনির পাসপোর্ট সাইজ ছবি (২ কপি)\n"
            "৪. ব্যাংক স্টেটমেন্ট (বিগত ৬-১২ মাসের)\n"
            "৫. GLG Assets বুকিং এবং বরাদ্দপত্র (Allotment Agreement)।\n"
            "*প্রবাসী বাংলাদেশীদের (NRB) জন্য*: বৈধ কাজের অনুমতি/ভিসার কপি এবং ফরেন কারেন্সি ব্যাংক হিসাবের বিবরণ।"
        ),
    },
    "required_documents_rental": {
        "policy_key": "required_documents_rental",
        "title_en": "Required Documents for Tenancy / Rental",
        "title_bn": "ভাড়া নেওয়ার জন্য প্রয়োজনীয় কাগজপত্র",
        "approved": True,
        "effective_from": "2026-09-01",
        "country": "Bangladesh",
        "answer_en": (
            "For renting a GLG residential unit in Dhaka:\n"
            "1. Copy of National ID (NID) / Passport\n"
            "2. Professional employment proof or trade license\n"
            "3. Police verification form (Dhaka Metropolitan Police tenant disclosure format)\n"
            "4. Standard rental agreement with 2-3 months advance security deposit."
        ),
        "answer_bn": (
            "ঢাকায় GLG রেসিডেনশিয়াল ইউনিট ভাড়া নেওয়ার জন্য প্রয়োজনীয় তথ্য:\n"
            "১. জাতীয় পরিচয়পত্র (NID) অথবা পাসপোর্টের কপি\n"
            "২. কর্মসংস্থান সনদ বা ট্রেড লাইসেন্স\n"
            "৩. ডিএমপি (DMP) ভাড়াটিয়া তথ্য ফরম পূরণ\n"
            "৪. স্ট্যান্ডার্ড রেন্টাল এগ্রিমেন্ট এবং ২-৩ মাসের অগ্রিম জামানত।"
        ),
    },
    "standard_payment_plan": {
        "policy_key": "standard_payment_plan",
        "title_en": "Standard Payment & Installment Terms",
        "title_bn": "পেমেন্ট প্ল্যান ও কিস্তি সুবিধা",
        "approved": True,
        "effective_from": "2026-09-01",
        "country": "Bangladesh",
        "answer_en": (
            "GLG Assets standard payment structure:\n"
            "• 10% Booking Deposit upon official unit reservation\n"
            "• 30% Milestone-based construction installments (distributed across the project lifecycle)\n"
            "• 60% Final settlement upon official handover and possession\n"
            "• Home financing and mortgage support is facilitated through partner banks (DBH, IDLC, BRAC Bank, etc.)."
        ),
        "answer_bn": (
            "GLG Assets-এর স্ট্যান্ডার্ড পেমেন্ট স্ট্রাকচার:\n"
            "• ১০% বুকিং মানি অফিসিয়াল ইউনিট রিজার্ভেশনের সময়\n"
            "• ৩০% কনস্ট্রাকশন ভিত্তিক মাইলস্টোন কিস্তি (প্রজেক্ট সময়সীমার মধ্যে)\n"
            "• ৬০% চূড়ান্ত পেমেন্ট হ্যান্ডওভার এবং পজেশন হস্তান্তরের সময়\n"
            "• শীর্ষস্থানীয় ব্যাংক ও আর্থিক প্রতিষ্ঠানের (যেমন DBH, IDLC, BRAC Bank) মাধ্যমে হোম লোন সুবিধা রয়েছে।"
        ),
    },
    "rent_vs_buy": {
        "policy_key": "rent_vs_buy",
        "title_en": "Rent vs Buy Advisory",
        "title_bn": "ভাড়া বনাম কেনার পরামর্শ",
        "approved": True,
        "effective_from": "2026-09-01",
        "country": "Bangladesh",
        "answer_en": (
            "Investing in luxury property in prime Dhaka areas (Gulshan, Banani, Baridhara) provides long-term capital appreciation, high rental yields from expatriates/diplomats, and wealth preservation. Renting offers immediate flexibility with lower initial capital outlay. Our sales advisors can help evaluate your portfolio goals."
        ),
        "answer_bn": (
            "ঢাকার প্রধান এলাকাগুলোতে (গুলশান, বনানী, বারিধারা) রিয়েল এস্টেট ক্রয়ের মাধ্যমে দীর্ঘমেয়াদী মূলধন বৃদ্ধি এবং আকর্ষণীয় ভাড়ার রিটার্ন পাওয়া যায়। ভাড়া নেওয়ার মাধ্যমে সাময়িক সুবিধা নিশ্চিত হয়। আপনার প্রয়োজন অনুযায়ী আমাদের টিম পরামর্শ দিয়ে সহযোগিতা করবে।"
        ),
    },
}


class PolicyRepository:
    """Repository for accessing approved business and compliance policies."""

    def __init__(self, policies: Optional[Dict[str, Dict[str, Any]]] = None):
        self._policies = policies or APPROVED_POLICIES

    def get_policy(self, policy_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve policy by key."""
        return self._policies.get(policy_key)

    def match_policy(self, query: str) -> Optional[Dict[str, Any]]:
        """Match query text to an approved policy."""
        q = query.lower()
        # Check payment terms first (prevents "down payment requirements" from matching documents)
        if any(kw in q for kw in ["payment", "installment", "kisti", "down payment", "booking amount", "financing", "loan"]):
            return self._policies.get("standard_payment_plan")

        if any(kw in q for kw in ["document", "kagoj", "paper", "nid", "tin", "tax return", "passport", "lagbe"]):
            if "rent" in q or "bhara" in q:
                return self._policies.get("required_documents_rental")
            return self._policies.get("required_documents_purchase")

        if "requirements" in q:
            if "rent" in q or "bhara" in q:
                return self._policies.get("required_documents_rental")
            return self._policies.get("required_documents_purchase")

        if any(kw in q for kw in ["rent vs buy", "kena bhalo na bhara"]):
            return self._policies.get("rent_vs_buy")

        return None


policy_repository = PolicyRepository()
