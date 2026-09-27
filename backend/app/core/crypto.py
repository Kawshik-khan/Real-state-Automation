"""Cryptographic utilities for encrypting credentials at rest (AES-GCM / Authenticated Cipher).

Protects third-party API keys (Groq, Pinecone, Telegram, Gmail) stored in PostgreSQL.
Keys are encrypted at rest with a master secret derived from settings.jwt_secret and settings.password_hash_salt.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from typing import Any, Dict, Optional

from app.config import settings

# Derive master 256-bit encryption key using PBKDF2
def _get_master_key() -> bytes:
    master_secret = (
        getattr(settings, "jwt_secret", "")
        + getattr(settings, "password_hash_salt", "")
        + getattr(settings, "automation_shared_secret", "glg_assets_default_salt")
    ).encode("utf-8")
    salt = b"glg_assets_credential_vault_salt_2026"
    return hashlib.pbkdf2_hmac("sha256", master_secret, salt, iterations=100000)


def encrypt_data(data: Dict[str, Any]) -> str:
    """Encrypt a dictionary payload into an authenticated base64 string."""
    raw_json = json.dumps(data).encode("utf-8")
    key = _get_master_key()

    try:
        # 1. Try standard cryptography AES-GCM if available
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aesgcm = AESGCM(key)
        nonce = secrets.token_bytes(12)
        ciphertext = aesgcm.encrypt(nonce, raw_json, None)
        envelope = {
            "v": 1,
            "alg": "AES-256-GCM",
            "n": base64.b64encode(nonce).decode("utf-8"),
            "c": base64.b64encode(ciphertext).decode("utf-8"),
        }
        return base64.b64encode(json.dumps(envelope).encode("utf-8")).decode("utf-8")
    except ImportError:
        # 2. Resilient Pure-Python Fallback: Authenticated Keystream CTR + HMAC-SHA256 (Encrypt-then-MAC)
        nonce = secrets.token_bytes(16)
        # Generate keystream block
        keystream = hashlib.sha256(key + nonce).digest()
        while len(keystream) < len(raw_json):
            keystream += hashlib.sha256(key + nonce + len(keystream).to_bytes(4, "big")).digest()
        encrypted_bytes = bytes(b ^ k for b, k in zip(raw_json, keystream[:len(raw_json)]))
        # Compute HMAC signature for authenticity (prevent tampering)
        sig = hmac.new(key, nonce + encrypted_bytes, hashlib.sha256).digest()
        envelope = {
            "v": 2,
            "alg": "HMAC-CTR-SHA256",
            "n": base64.b64encode(nonce).decode("utf-8"),
            "c": base64.b64encode(encrypted_bytes).decode("utf-8"),
            "s": base64.b64encode(sig).decode("utf-8"),
        }
        return base64.b64encode(json.dumps(envelope).encode("utf-8")).decode("utf-8")


def decrypt_data(token_str: str) -> Dict[str, Any]:
    """Decrypt an authenticated token back into the dictionary payload."""
    if not token_str:
        return {}
    try:
        raw_envelope = base64.b64decode(token_str.encode("utf-8")).decode("utf-8")
        envelope = json.loads(raw_envelope)
        key = _get_master_key()

        if envelope.get("v") == 1 and envelope.get("alg") == "AES-256-GCM":
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aesgcm = AESGCM(key)
            nonce = base64.b64decode(envelope["n"])
            ciphertext = base64.b64decode(envelope["c"])
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(decrypted.decode("utf-8"))

        elif envelope.get("v") == 2 and envelope.get("alg") == "HMAC-CTR-SHA256":
            nonce = base64.b64decode(envelope["n"])
            ciphertext = base64.b64decode(envelope["c"])
            expected_sig = base64.b64decode(envelope["s"])
            actual_sig = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(actual_sig, expected_sig):
                raise ValueError("Ciphertext signature verification failed")

            keystream = hashlib.sha256(key + nonce).digest()
            while len(keystream) < len(ciphertext):
                keystream += hashlib.sha256(key + nonce + len(keystream).to_bytes(4, "big")).digest()
            decrypted = bytes(b ^ k for b, k in zip(ciphertext, keystream[:len(ciphertext)]))
            return json.loads(decrypted.decode("utf-8"))

        # Fallback to direct JSON if unencrypted legacy
        return json.loads(token_str)
    except Exception:
        return {}


def mask_secret_value(value: Optional[str], visible_start: int = 4, visible_end: int = 4) -> str:
    """Mask a secret string (e.g., 'gsk_tP4oGEl...9p4D' -> 'gsk_...9p4D')."""
    if not value or not isinstance(value, str):
        return ""
    val_clean = value.strip()
    if len(val_clean) <= visible_start + visible_end:
        return "•" * len(val_clean)
    start = val_clean[:visible_start]
    end = val_clean[-visible_end:]
    return f"{start}...{end}"
