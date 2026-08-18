"""Language detection utility for GLG Assets chatbot."""

import re

BANGLISH_KEYWORDS = {
    "kemon", "koto", "kothay", "koi", "apnader", "amar", "amader", "dam", "dham",
    "lagbe", "chai", "chahi", "achhen", "achen", "achena", "bhai", "bhaiya", "vai",
    "vaiya", "bhalo", "valo", "ache", "ase", "korben", "janan", "bolun", "dhaka",
    "barier", "jomi", "dorkar", "apni", "tumi", "ke", "konta", "kisu"
}


def is_english_query(text: str) -> bool:
    """Check if the input text is in English.

    Returns False if the text contains Bengali script or common Banglish keywords,
    defaulting to Bangla/Banglish.
    """
    if not text or not text.strip():
        return False

    # 1. Check for Bengali script (U+0980 - U+09FF)
    if re.search(r"[\u0980-\u09FF]", text):
        return False

    # 2. Check for common Banglish keywords
    tokens = set(re.findall(r"\b\w+\b", text.lower()))
    if tokens.intersection(BANGLISH_KEYWORDS):
        return False

    # 3. If standard English input without Banglish cues, return True
    # For very short standard greetings like "hi", "hello", "hey", treat as default (Bangla/Banglish)
    clean_text = text.strip().lower()
    if clean_text in ("hi", "hello", "hey", "hola", "hy"):
        return False

    return True
