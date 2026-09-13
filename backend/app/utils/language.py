"""Language detection utility for GLG Assets chatbot.

Audit Reference: prompt-engineering-and-system-prompt-audit-bangladesh-fixed.md
Uses multi-signal classifier: Bengali script ratio + Romanized Bangla core lexical scoring
+ Banglish grammatical suffix patterns + common phrase matching + English grammar exclusion.
"""

import re
from typing import Any, Dict

# Bengali script range: U+0980 to U+09FF
BENGALI_REGEX = re.compile(r"[\u0980-\u09FF]")
LATIN_REGEX = re.compile(r"[a-zA-Z]")

# Core Romanized Bangla Lexicon (excludes shared real estate loan words like 'flat', 'budget')
CORE_BANGLISH_WORDS = {
    # Pronouns & Address
    "ami", "amra", "tumi", "apni", "apnara", "apnader", "amader", "amar", "tader",
    "bhai", "bhaiya", "vai", "vaiya", "apu", "sir", "madam",
    # Question words
    "koto", "kothay", "koi", "konta", "konti", "ki", "kemon", "kamon", "keno", "kar",
    # Verbs / Inquiry forms
    "pabo", "paben", "pabe", "pacchi", "paowa",
    "dekhbo", "dekhte", "dekhben", "dekhi", "dekhano",
    "nibo", "kinbo", "nite", "nebo", "kena", "kinte",
    "janaben", "bolben", "bolun", "janan", "bolte", "janano",
    "thakbe", "ache", "ase", "chilo", "thake", "thakbo", "nai", "nei",
    "lagbe", "dorkar", "chai", "chahi", "chaile", "hobe", "korben", "korte",
    "porbe", "dile", "paowa", "jabe",
    # Common adjectives & nouns
    "dam", "dham", "taka", "notun", "boro", "choto", "shundor", "khuje",
    "valo", "bhalo", "achen", "achhen", "kisu", "kichu", "jomi", "bari", "basha",
    "kisti", "kistite", "suvidha", "subidha", "khoj", "khobor",
}

# Shared domain loan words common in both English and Banglish real estate queries
SHARED_LOAN_WORDS = {
    "flat", "flats", "apartment", "apartments", "project", "projects", "dhaka",
    "budget", "price", "pricing", "bhk", "luxury", "duplex", "suite", "road",
    "gulshan", "banani", "baridhara", "dhanmondi", "uttara", "crest", "heights",
}

# English grammatical & conversational indicator words
ENGLISH_GRAMMAR_WORDS = {
    "what", "is", "are", "the", "for", "and", "can", "tell", "me", "about", "could", "you",
    "please", "we", "our", "in", "to", "of", "with", "at", "from", "on", "send", "give",
    "schedule", "handover", "available", "units", "details", "contact", "brochure",
    "bedroom", "bedrooms", "bathroom", "bathrooms", "floor", "plan", "plans",
    "where", "how", "much", "many", "when", "which", "who", "whom", "will", "would",
    "there", "here", "have", "has", "had", "under", "over", "more", "before", "after",
    "looking", "interested", "information", "regards", "thank", "thanks", "hello",
}

BANGLISH_SUFFIX_PATTERNS = [
    re.compile(r"^[a-zA-Z]+(e|te|ete)$", re.IGNORECASE),       # locative -e, -te (e.g. gulshane, bananite)
    re.compile(r"^[a-zA-Z]+(er|der)$", re.IGNORECASE),          # genitive -er, -der (e.g. flater, apnader)
    re.compile(r"^[a-zA-Z]+(gulo|gula|gulor)$", re.IGNORECASE), # plural -gulo, -gula
    re.compile(r"^[a-zA-Z]+(ta|ti|khana)$", re.IGNORECASE),     # definitive -ta, -ti
]

BANGLISH_PHRASES = [
    "ki ache", "konta ache", "kothay ache", "flat ache", "dam koto",
    "price koto", "kisti ache", "kistite deya", "details inbox",
    "dekhbo ami", "nite chai", "kinte chai", "koto porbe",
]


def bengali_script_ratio(text: str) -> float:
    """Calculate ratio of Bengali script characters to total non-space characters."""
    clean = re.sub(r"\s+", "", text)
    if not clean:
        return 0.0
    bn_chars = len(BENGALI_REGEX.findall(clean))
    return bn_chars / len(clean)


def latin_ratio(text: str) -> float:
    """Calculate ratio of Latin alphabet characters to total non-space characters."""
    clean = re.sub(r"\s+", "", text)
    if not clean:
        return 0.0
    lat_chars = len(LATIN_REGEX.findall(clean))
    return lat_chars / len(clean)


def detect_language(text: str) -> Dict[str, Any]:
    """Multi-signal language detector returning language code and confidence.

    Returns:
        dict: {"language": "bn" | "banglish" | "en" | "mixed", "confidence": float}
    """
    if not text or not text.strip():
        return {"language": "en", "confidence": 1.0}

    clean_text = text.strip()
    text_lower = clean_text.lower()
    tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", text_lower)

    # 1. Check Bengali script presence (>= 25% characters)
    bn_ratio = bengali_script_ratio(clean_text)
    if bn_ratio >= 0.25:
        return {"language": "bn", "confidence": min(0.70 + bn_ratio, 0.99)}

    # 2. Count distinct token signals
    core_banglish_count = sum(1 for t in tokens if t in CORE_BANGLISH_WORDS)
    english_grammar_count = sum(1 for t in tokens if t in ENGLISH_GRAMMAR_WORDS)
    phrase_matches = sum(1 for phrase in BANGLISH_PHRASES if phrase in text_lower)

    # Calculate suffix score only for non-English words
    suffix_score = 0.0
    for t in tokens:
        if t in ENGLISH_GRAMMAR_WORDS or t in SHARED_LOAN_WORDS or len(t) < 4:
            continue
        for pattern in BANGLISH_SUFFIX_PATTERNS:
            if pattern.match(t):
                suffix_score += 0.25
                break
    suffix_score = min(suffix_score, 1.0)

    # Default short greetings
    if text_lower in ("hi", "hello", "hey", "hola", "hy"):
        return {"language": "banglish", "confidence": 0.65}

    # 3. Decision Logic:
    # Clear Banglish if core Banglish words or idioms are present
    if core_banglish_count >= 1 or phrase_matches >= 1:
        confidence = min(0.70 + (core_banglish_count * 0.1) + (phrase_matches * 0.2), 0.99)
        return {"language": "banglish", "confidence": confidence}

    # Suffix score without core Banglish words triggers only if English grammar words are absent
    if suffix_score >= 0.25 and english_grammar_count == 0:
        return {"language": "banglish", "confidence": 0.70}

    # If sentence contains English grammatical markers and no core Banglish
    if english_grammar_count >= 1 and core_banglish_count == 0:
        return {"language": "en", "confidence": min(0.80 + (english_grammar_count * 0.05), 0.99)}

    # Fallback to Latin script ratio
    lat_ratio = latin_ratio(clean_text)
    if lat_ratio >= 0.70 and core_banglish_count == 0 and suffix_score == 0:
        return {"language": "en", "confidence": 0.85}

    return {"language": "mixed", "confidence": 0.50}


def is_english_query(text: str) -> bool:
    """Backward-compatible helper: Returns True only if query is strictly English."""
    result = detect_language(text)
    return result["language"] == "en"
