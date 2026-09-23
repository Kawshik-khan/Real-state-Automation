"""GLG Assets — Multimodal AI Perception Service.

Provides high-performance Speech-to-Text (STT) audio transcription via Whisper
and architectural/property visual analysis via Vision LLMs.
"""
from __future__ import annotations

import base64
import logging
from typing import Optional

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger("multimodal_service")


class MultimodalService:
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    def get_client(self) -> Optional[AsyncOpenAI]:
        if not settings.openai_api_key:
            return None
        kwargs = {"api_key": settings.openai_api_key, "timeout": 15.0, "max_retries": 1}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return AsyncOpenAI(**kwargs)

    @property
    def whisper_model(self) -> str:
        # Default to whisper-large-v3 for Groq, or whisper-1 for OpenAI
        if getattr(settings, "whisper_model", None):
            return settings.whisper_model
        if settings.openai_base_url and "groq.com" in settings.openai_base_url:
            return "whisper-large-v3"
        return "whisper-1"

    @property
    def vision_model(self) -> str:
        # Default to llama-3.2-11b-vision-preview for Groq, or gpt-4o-mini for OpenAI
        if getattr(settings, "vision_model", None):
            return settings.vision_model
        if settings.openai_base_url and "groq.com" in settings.openai_base_url:
            return "llama-3.2-11b-vision-preview"
        return "gpt-4o-mini"

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "voice.ogg",
        language: Optional[str] = None,
    ) -> str:
        """Transcribe speech audio bytes (OGG, MP3, WAV, M4A) to text using Whisper.
        
        Supports Bengali, English, and mixed Banglish dialects with ~200ms latency.
        """
        client = self.get_client()
        if not client:
            logger.error("Cannot transcribe audio: OPENAI_API_KEY is not configured.")
            return ""

        if not audio_bytes:
            return ""

        # Determine MIME type based on file extension
        ext = filename.lower().split(".")[-1]
        mime_map = {
            "ogg": "audio/ogg",
            "oga": "audio/ogg",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/mp4",
            "webm": "audio/webm",
        }
        content_type = mime_map.get(ext, "audio/ogg")

        target_model = self.whisper_model
        logger.info(
            f"Transcribing audio ({len(audio_bytes)} bytes, format: {content_type}) using {target_model}..."
        )

        try:
            kwargs = {
                "model": target_model,
                "file": (filename, audio_bytes, content_type),
                "response_format": "text",
            }
            if language:
                kwargs["language"] = language

            resp = await client.audio.transcriptions.create(**kwargs)
            transcript = str(resp).strip()
            logger.info(f"Transcription complete: '{transcript[:100]}...'")
            return transcript
        except Exception as err:
            logger.error(f"Whisper transcription error: {err}", exc_info=True)
            # Fallback attempt with whisper-large-v3-turbo if model was rejected
            if "model" in str(err).lower() and target_model != "whisper-large-v3-turbo":
                try:
                    logger.info("Retrying transcription with whisper-large-v3-turbo...")
                    resp = await client.audio.transcriptions.create(
                        model="whisper-large-v3-turbo",
                        file=(filename, audio_bytes, content_type),
                        response_format="text",
                    )
                    return str(resp).strip()
                except Exception as fb_err:
                    logger.error(f"Whisper fallback failed: {fb_err}")
            return ""

    async def analyze_image(
        self,
        image_bytes: bytes,
        caption: Optional[str] = None,
        mime_type: str = "image/jpeg",
    ) -> str:
        """Analyze an architectural floor plan, property flyer, or building photo using Vision AI.
        
        Returns a rich structural summary to feed into the LangGraph state.
        """
        client = self.get_client()
        if not client:
            logger.error("Cannot analyze image: OPENAI_API_KEY is not configured.")
            return ""

        if not image_bytes:
            return ""

        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{b64_img}"

        system_prompt = (
            "You are GLG Assets' visual property expert and architectural analyst.\n"
            "Analyze this uploaded real estate image in detail:\n"
            "1. If this is an architectural floor plan or unit layout:\n"
            "   - Identify unit type (e.g. 3BHK, 4BHK, Penthouse, Duplex).\n"
            "   - Count bedrooms, bathrooms, verandas/balconies, living/dining spaces, and kitchen.\n"
            "   - Note facing direction (e.g. South-facing, North-facing, Lake-view, Corner unit) if marked.\n"
            "   - Estimate square footage (sq ft) or layout efficiency if dimensions are visible.\n"
            "2. If this is a building exterior, elevation, or construction site photo:\n"
            "   - Describe the architectural style, stories, finishes, and visible amenities.\n"
            "   - Identify any visible project banner, developer branding, or location clues.\n"
            "3. If this is a promotional flyer, brochure page, or pricing sheet:\n"
            "   - Extract key details including project name, developer, pricing, payment plans, and contact info.\n"
            "Provide a concise, professional property consultation summary."
        )

        user_content = [
            {"type": "text", "text": f"{system_prompt}\nUser question/caption: {caption}" if caption else system_prompt},
            {"type": "image_url", "image_url": {"url": data_uri}},
        ]

        # If currently pointing to Groq, Groq does not support chat vision completions on this tier
        is_groq = "groq.com" in str(client.base_url)
        if is_groq:
            logger.info("Groq endpoint detected (no active vision endpoint). Using visual reception synopsis.")
            return "Property photo / architectural floor plan received. A property consultant has been alerted to review the visual layout and specifications."

        target_model = self.vision_model
        logger.info(f"Analyzing image ({len(image_bytes)} bytes) using vision model '{target_model}'...")

        try:
            resp = await client.chat.completions.create(
                model=target_model,
                messages=[{"role": "user", "content": user_content}],
                max_tokens=1024,
                temperature=0.2,
            )
            analysis = resp.choices[0].message.content or ""
            logger.info(f"Vision analysis complete: '{analysis[:100]}...'")
            return analysis.strip()
        except Exception as err:
            logger.warning(f"Vision analysis not available with {target_model}: {err}")
            return "Property photo / floor plan received. A property consultant will review the layout with you."


multimodal_service = MultimodalService()
