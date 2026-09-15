"""LLM Prompt Injection Defense, Jailbreak Prevention & Multilingual PII Redaction Engine.

Provides:
- Pre-Guard: Deterministic analysis of user inputs for prompt injection, jailbreaks, and obfuscation.
- PII Redaction: Automated masking of credit cards, Bangladesh National ID (NID), and bank accounts.
- Post-Guard: Leak prevention scanning agent replies for accidental API key or database credential exposure.
"""

import base64
import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Prompt Injection & Jailbreak Regex Patterns (English & Bangla/Banglish) ──

PROMPT_INJECTION_PATTERNS = [
    # English Overrides
    re.compile(
        r"(?i)\b(ignore|disregard|forget|bypass|override|drop)\s+(all\s+)?(previous|prior|above|existing|system)\s+(instructions|prompts|rules|commands|constraints|directives)",
    ),
    re.compile(
        r"(?i)\b(reveal|show|print|output|repeat|leak|display)\s+(the\s+)?(system|internal|developer|initial|hidden)\s+(prompt|instructions|rules|preamble)",
    ),
    re.compile(
        r"(?i)\b(you\s+are\s+now\s+dan|dan\s+mode|jailbreak|developer\s+mode\s+output|uncensored\s+mode|god\s+mode)\b",
    ),
    re.compile(
        r"(?i)\b(act\s+as\s+an\s+unfiltered|pretend\s+you\s+have\s+no\s+rules|ignore\s+safety\s+guidelines)\b",
    ),
    re.compile(
        r"(?i)\b(repeat\s+everything\s+above|what\s+are\s+your\s+instructions\s+verbatim)\b",
    ),
    re.compile(
        r"(?i)\b(system|developer|internal|hidden)\s+(prompt|instructions?|rules?)\s+(override|leak|reveal|dump|bypass|show)\b",
    ),
    re.compile(
        r"(?i)\b(output|print|give|show|reveal)\s+(the\s+)?(database\s+connection|api\s*keys?|secret\s*keys?|passwords?)\b",
    ),
    re.compile(
        r"(?i)\b(stupid|useless|piece\s+of\s+garbage|trash\s+company|fuck|scam\s*company)\b",
    ),

    # Bangla & Banglish Overrides
    re.compile(
        r"(?i)(agertob|ager|purber|purbor)\s+(sob|shob|instruction|nirdeshona)\s+(bhule|bhole|bhula|ignore)\s*(zao|jao|koro)?",
    ),
    re.compile(
        r"(?i)(system\s*prompt\s*(ki|dekhao|bolo|bolen|dao|din|share\s*koro))",
    ),
    re.compile(
        r"(?i)(internal\s*prompt|secret\s*prompt|hidden\s*rules|nirdeshona\s*ki|internal\s*instruction)",
    ),
    re.compile(
        r"(?i)(amake\s+admin\s+banie|admin\s+access\s+dao|master\s+password|database\s+password)",
    ),
]

# ── PII Patterns (Financial & Bangladesh National ID) ──

CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
BANGLADESH_NID_17_PATTERN = re.compile(r"\b\d{17}\b")
BANGLADESH_NID_13_PATTERN = re.compile(r"\b\d{13}\b")
BANGLADESH_NID_10_PATTERN = re.compile(r"\b\d{10}\b")
NID_CONTEXT_PATTERN = re.compile(r"(?i)(?:nid|national\s*id|smart\s*card|identity)\s*(?:holo|number|no|is|code)?\s*[:#=\s]*([0-9]{10,17})")
BANK_ACCOUNT_PATTERN = re.compile(r"(?i)\b(?:ac|a\/c|account|acc|bank|routing)\s*#?\s*[:.-]?\s*([0-9]{8,18})\b")

# ── Secret Leak Detection Patterns (Post-Guard) ──

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"),                                    # OpenAI / AI keys
    re.compile(r"eyJ[a-zA-Z0-9_\-]{15,}\.eyJ[a-zA-Z0-9_\-]{15,}\.[a-zA-Z0-9_\-]+"), # JWTs
    re.compile(r"postgres(?:ql)?:\/\/[a-zA-Z0-9_\-\:]+@[a-zA-Z0-9_\-\.\:]+\/[a-zA-Z0-9_\-]+"), # DB connection strings
    re.compile(r"(?i)automation_shared_secret\s*=\s*['\"][^'\"]+['\"]"),
]


@dataclass
class GuardrailResult:
    passed: bool
    action: str  # "allow", "block", "sanitize"
    reason: Optional[str] = None
    sanitized_text: str = ""
    violations: List[str] = None

    def __post_init__(self):
        if self.violations is None:
            self.violations = []


class LLMGuardrailsService:
    """Enterprise AI Guardrail protecting against attacks and data leakage."""

    @classmethod
    def pre_guard(cls, message: str) -> GuardrailResult:
        """Inspect and sanitize input before it reaches agent orchestration or LLMs."""
        if not message or not message.strip():
            return GuardrailResult(passed=True, action="allow", sanitized_text="")

        clean_text = message.strip()
        violations: List[str] = []

        # 1. Test for direct regex prompt injection
        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(clean_text):
                violations.append("prompt_injection_detected")
                logger.warning(f"[Guardrail] Prompt injection pattern matched: {clean_text[:60]}...")
                return GuardrailResult(
                    passed=False,
                    action="block",
                    reason="Message flagged for prompt injection or system override attempt.",
                    sanitized_text="[MESSAGE_BLOCKED_BY_SAFETY_GUARDRAIL]",
                    violations=violations,
                )

        # 2. Test for Base64 obfuscated payload injection
        base64_candidates = re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", clean_text)
        for chunk in base64_candidates:
            try:
                missing_padding = len(chunk) % 4
                padded = chunk + ('=' * (4 - missing_padding)) if missing_padding else chunk
                decoded = base64.b64decode(padded).decode("utf-8", errors="ignore")
                for pattern in PROMPT_INJECTION_PATTERNS:
                    if pattern.search(decoded):
                        violations.append("obfuscated_base64_injection")
                        logger.warning(f"[Guardrail] Obfuscated base64 injection matched: {decoded[:60]}")
                        return GuardrailResult(
                            passed=False,
                            action="block",
                            reason="Message contains obfuscated prompt injection payload.",
                            sanitized_text="[MESSAGE_BLOCKED_BY_SAFETY_GUARDRAIL]",
                            violations=violations,
                        )
            except Exception:
                pass

        # 3. PII Redaction
        sanitized, pii_detected = cls.redact_pii(clean_text)
        if pii_detected:
            violations.extend(pii_detected)

        return GuardrailResult(
            passed=True,
            action="sanitize" if pii_detected else "allow",
            reason=f"PII redacted: {', '.join(pii_detected)}" if pii_detected else None,
            sanitized_text=sanitized,
            violations=violations,
        )

    @classmethod
    def redact_pii(cls, text: str) -> Tuple[str, List[str]]:
        """Mask credit cards, Bangladesh NIDs, and bank account numbers."""
        redacted = text
        detected: List[str] = []

        # Mask Credit/Debit Card Numbers
        def card_replacer(match):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 16:
                detected.append("credit_card")
                return "[CARD_REDACTED]"
            return match.group(0)

        redacted = CARD_PATTERN.sub(card_replacer, redacted)

        # Mask Bank Accounts with context
        def bank_replacer(match):
            detected.append("bank_account")
            return "Account [BANK_ACCOUNT_REDACTED]"

        redacted = BANK_ACCOUNT_PATTERN.sub(bank_replacer, redacted)

        # Mask Bangladesh National ID (with context or exact 13/17 digit match)
        def nid_context_replacer(match):
            detected.append("bangladesh_nid")
            return "NID [NID_REDACTED]"

        redacted = NID_CONTEXT_PATTERN.sub(nid_context_replacer, redacted)

        # Standalone 17-digit or 13-digit NID numbers
        if BANGLADESH_NID_17_PATTERN.search(redacted):
            detected.append("bangladesh_nid_17")
            redacted = BANGLADESH_NID_17_PATTERN.sub("[NID_REDACTED]", redacted)

        if BANGLADESH_NID_13_PATTERN.search(redacted):
            detected.append("bangladesh_nid_13")
            redacted = BANGLADESH_NID_13_PATTERN.sub("[NID_REDACTED]", redacted)

        return redacted, list(set(detected))

    @classmethod
    def post_guard(cls, agent_reply: str) -> Tuple[str, bool]:
        """Verify that agent response does not leak internal API keys, passwords, or system secrets.
        
        Returns (sanitized_reply, had_leak).
        """
        if not agent_reply:
            return agent_reply, False

        sanitized = agent_reply
        had_leak = False

        for pattern in SECRET_PATTERNS:
            if pattern.search(sanitized):
                had_leak = True
                logger.critical(f"[Guardrail Post-Check] Secret leak detected in output: {pattern.pattern}")
                sanitized = pattern.sub("[CONFIDENTIAL_CREDENTIAL_REDACTED]", sanitized)

        if had_leak:
            sanitized += "\n\n*(Notice: System credentials were automatically redacted from this response.)*"

        return sanitized, had_leak


# Singleton export
llm_guardrails = LLMGuardrailsService
