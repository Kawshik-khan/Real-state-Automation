"""Supabase Storage Service Helper

Provides utility methods for uploading brochures, floor plan images, and OCR files
directly to Supabase Cloud Storage buckets.
"""
import json
import urllib.request
import urllib.error
from typing import Optional
from app.config import settings


def upload_to_supabase_storage(
    file_bytes: bytes,
    file_name: str,
    bucket_name: str = "brochures",
    content_type: str = "application/pdf"
) -> Optional[str]:
    """Uploads a file to a Supabase Storage Bucket and returns its Public URL.
    
    Returns None if Supabase URL or Service Role Key is not configured.
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None

    url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket_name}/{file_name}"
    
    headers = {
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": content_type,
        "x-upsert": "true"
    }

    req = urllib.request.Request(
        url,
        data=file_bytes,
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (200, 201):
                # Construct public URL
                public_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{bucket_name}/{file_name}"
                return public_url
    except urllib.error.HTTPError as e:
        print(f"[Supabase Storage Error] {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"[Supabase Storage Error] {e}")

    return None
