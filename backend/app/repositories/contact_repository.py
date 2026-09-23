"""Contact Config Repository — Canonical GLG Assets Operational Contacts.

Architecture Rule: Prompts must NOT hardcode phone numbers or office locations.
All customer-facing contact details are retrieved dynamically from this repository.
"""
from typing import Any, Dict

OFFICIAL_CONTACT_CONFIG: Dict[str, Any] = {
    "company_name": "GLG Assets Limited",
    "primary_phone": "+880-13178610",
    "hotline": "013178610",
    "whatsapp_support": "+880-13178610",
    "sales_email": "sales@glgassets.com",
    "support_email": "concierge@glgassets.com",
    "head_office": {
        "building": "House # 12",
        "road": "Rd 16/A",
        "area": "Gulshan-1",
        "city": "Dhaka - 1212",
        "country": "Bangladesh",
        "formatted_en": "House # 12, Rd 16/A, Gulshan-1, Dhaka 1212, Bangladesh",
        "formatted_bn": "হাউজ # ১২, রোড ১৬/এ, গুলশান-১, ঢাকা ১২১২, বাংলাদেশ",
    },
    "operating_hours": {
        "days_en": "Saturday – Thursday",
        "days_bn": "শনিবার – বৃহস্পতিবার",
        "hours_en": "9:30 AM – 6:30 PM (BST)",
        "hours_bn": "সকাল ৯:৩০ – সন্ধ্যা ৬:৩০",
        "friday_support": "By Prior Appointment / Digital Concierge Active",
    },
    "active": True,
    "last_verified_at": "2026-09-23",
}


class ContactRepository:
    """Canonical contact repository."""

    def __init__(self, config: Dict[str, Any] = OFFICIAL_CONTACT_CONFIG):
        self._config = config

    def get_contact_info(self) -> Dict[str, Any]:
        """Returns verified contact data."""
        return dict(self._config)

    def format_contact_card(self, is_english: bool = False) -> str:
        """Generates formatted contact block for chat/email/social."""
        cfg = self._config
        if is_english:
            return (
                f"📞 *Official Helpline*: {cfg['hotline']} ({cfg['primary_phone']})\n"
                f"💬 *WhatsApp Support*: {cfg['whatsapp_support']}\n"
                f"✉️ *Email*: {cfg['sales_email']}\n"
                f"🏢 *Head Office*: {cfg['head_office']['formatted_en']}\n"
                f"🕒 *Office Hours*: {cfg['operating_hours']['days_en']}, {cfg['operating_hours']['hours_en']}"
            )
        return (
            f"📞 *অফিসিয়াল হেল্পলাইন*: {cfg['hotline']} ({cfg['primary_phone']})\n"
            f"💬 *হোয়াটসঅ্যাপ সাপোর্ট*: {cfg['whatsapp_support']}\n"
            f"✉️ *ইমেইল*: {cfg['sales_email']}\n"
            f"🏢 *হেড অফিস*: {cfg['head_office']['formatted_bn']}\n"
            f"🕒 *কার্যকাল*: {cfg['operating_hours']['days_bn']}, {cfg['operating_hours']['hours_bn']}"
        )


contact_repository = ContactRepository()
