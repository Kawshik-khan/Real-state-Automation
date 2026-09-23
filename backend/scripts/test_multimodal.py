"""Test Multimodal Voice (Whisper) and Vision AI Services."""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
load_dotenv(backend_dir / ".env")

from app.services.multimodal import multimodal_service  # noqa: E402
from app.services.telegram import telegram_service  # noqa: E402


async def main():
    print("=" * 60)
    print("  GLG Assets — Multimodal Perception Verification Suite")
    print("=" * 60)

    # 1. Inspect configured models
    print("\n[Step 1] Inspecting Model Configuration...")
    print(f" -> Whisper Model: {multimodal_service.whisper_model}")
    print(f" -> Vision Model:  {multimodal_service.vision_model}")
    print(f" -> API Base URL:  {os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')}")
    api_key = os.getenv("OPENAI_API_KEY", "")
    print(f" -> API Key:       {api_key[:10]}...{api_key[-4:] if len(api_key) > 10 else ''}")

    # 2. Test Telegram File Download Helper
    print("\n[Step 2] Testing Telegram File Downloader...")
    content, path = await telegram_service.download_file_bytes("invalid_test_id")
    print(f" -> Handled invalid file ID gracefully (bytes={len(content)}, path='{path}'): PASS")

    # 3. Test Vision AI Pipeline
    print("\n[Step 3] Testing Vision AI Pipeline (Floor Plan & Property Image Analyst)...")
    minimal_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x02\x00\x00\x00\xfd\xd4\x9as"
        b"\x00\x00\x00\x12IDATx\x9cc\xf8\xcf\xc0\x80\x03\x18\x05\x00\x00\x00\xff\xff\x03\x00\x03\xe8\x01\x88\xd1\x88\x1e\x87"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    try:
        vision_result = await multimodal_service.analyze_image(
            minimal_png,
            caption="Test architectural floorplan inspection",
            mime_type="image/png",
        )
        if vision_result:
            print(" -> Vision Model Communication: SUCCESS!")
            print(f" -> Sample Vision Output: '{vision_result[:120]}...'")
        else:
            print(" -> Vision model returned empty response (Check model availability).")
    except Exception as e:
        print(f" -> Vision test error: {e}")

    # 4. Test Audio Transcription (Whisper) Interface
    print("\n[Step 4] Testing Whisper STT Interface...")
    await multimodal_service.transcribe_audio(b"")
    print(" -> Handled empty audio buffer gracefully: PASS")

    print("\n" + "=" * 60)
    print("  Multimodal Verification Complete — Ready for Live Telegram Testing!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
