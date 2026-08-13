"""Attachment Parser Service for Incoming Email Attachments.

Extracts plain text from attached files (PDF, TXT, CSV, JSON, DOCX) to enrich
the RAG state and provide context to the Email Agent.
"""

import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AttachmentParserService:
    @staticmethod
    def extract_text_from_attachment(
        filename: str,
        content_type: str,
        file_bytes: Optional[bytes] = None,
        base64_content: Optional[str] = None,
    ) -> str:
        """Extract text from raw bytes or base64 encoded payload."""
        if not file_bytes and base64_content:
            try:
                file_bytes = base64.b64decode(base64_content)
            except Exception as e:
                logger.error(f"Failed to decode base64 attachment content for {filename}: {e}")
                return ""

        if not file_bytes:
            return ""

        filename_lower = filename.lower()

        # Plain Text / Markdown / CSV / JSON
        if any(filename_lower.endswith(ext) for ext in [".txt", ".md", ".csv", ".json", ".html"]):
            try:
                return file_bytes.decode("utf-8", errors="ignore")
            except Exception as e:
                logger.warning(f"Error decoding text attachment {filename}: {e}")
                return ""

        # PDF parsing
        if filename_lower.endswith(".pdf") or "pdf" in content_type.lower():
            try:
                import io
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    extracted = []
                    for page in reader.pages:
                        txt = page.extract_text()
                        if txt:
                            extracted.append(txt)
                    return "\n".join(extracted)
                except ImportError:
                    try:
                        import PyPDF2
                        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                        extracted = []
                        for page in reader.pages:
                            txt = page.extract_text()
                            if txt:
                                extracted.append(txt)
                        return "\n".join(extracted)
                    except ImportError:
                        logger.warning("Neither pypdf nor PyPDF2 installed; returning placeholder for PDF.")
                        return f"[PDF file: {filename} ({len(file_bytes)} bytes)]"
            except Exception as e:
                logger.error(f"Error parsing PDF attachment {filename}: {e}")
                return f"[PDF parsing failed for {filename}]"

        return f"[Attached file: {filename} ({len(file_bytes)} bytes)]"


attachment_parser = AttachmentParserService()
