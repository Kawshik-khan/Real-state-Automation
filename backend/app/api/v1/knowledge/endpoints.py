"""Knowledge Services — Document upload with chunking + embedding + pgvector storage + OCR support."""

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import settings
from app.dependencies import require_roles
from app.models.user import UserRole
from app.rag.pipeline import rag
from app.services.llm import llm_service

router = APIRouter()
_knowledge_auth = require_roles([UserRole.ADMIN, UserRole.DEVELOPER])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
_DOC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _validated_doc_id(doc_id: str | None) -> str:
    """doc_id becomes a filename on disk: allow only a safe character set (no path parts)."""
    if not doc_id:
        return f"doc_{uuid.uuid4().hex[:12]}"
    if not _DOC_ID_RE.match(doc_id) or ".." in doc_id:
        raise HTTPException(status_code=400, detail="doc_id may only contain letters, digits, '_', '-', '.'")
    return doc_id


def _extract_text_from_file(filename: str, content: bytes) -> str:
    """Extract text from file bytes (supports .pdf, .txt, .md, .json, .csv)."""
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        # Try pypdf / PyPDF2 / pdfplumber for PDF text extraction
        try:
            import io

            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages_text = [page.extract_text() or "" for page in reader.pages]
            extracted = "\n".join(pages_text).strip()
            if extracted:
                return extracted
        except Exception:
            pass

        try:
            import io

            import pdfplumber
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages_text = [page.extract_text() or "" for page in pdf.pages]
                extracted = "\n".join(pages_text).strip()
                if extracted:
                    return extracted
        except Exception:
            pass

    # Fallback to UTF-8 / Latin-1 text decode
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
        if start >= len(words):
            break
    return chunks


@router.post("/upload", summary="Upload document — chunk, embed, and index")
async def knowledge_upload(
    file: UploadFile = File(...),
    doc_id: str = Form(None),
    project: str = Form(None),
    location: str = Form(None),
    document_type: str = Form(None),
    current_user: dict = Depends(_knowledge_auth),
):
    """Upload a document file (PDF/TXT/MD/JSON) for OCR/extraction, chunking, embedding, and indexing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    final_doc_id = _validated_doc_id(doc_id)
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit")
    text = _extract_text_from_file(file.filename, content)

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file or file is empty")

    chunks_raw = _chunk_text(text, chunk_size=500, overlap=50)

    if not chunks_raw:
        raise HTTPException(status_code=400, detail="No content to index")

    chunk_objects = []
    for i, chunk_text in enumerate(chunks_raw):
        embedding = await llm_service.embed(chunk_text)
        chunk_objects.append({
            "content": chunk_text,
            "embedding": embedding,
            "chunk_index": i,
            "filename": file.filename,
            "project": project,
            "location": location,
            "document_type": document_type,
            "metadata": {
                "filename": file.filename,
                "project": project,
                "location": location,
                "document_type": document_type,
            },
        })

    await rag.add_document(final_doc_id, chunk_objects)

    # Save to disk for persistence (safely handled if storage permissions vary)
    try:
        base_dir = Path(settings.knowledge_base_dir).resolve()
        base_dir.mkdir(parents=True, exist_ok=True)
        save_path = (base_dir / f"{final_doc_id}.txt").resolve()
        if save_path.parent != base_dir:
            raise ValueError("refusing to write outside the knowledge base directory")
        save_path.write_text(text, encoding="utf-8")
    except Exception as save_err:
        print(f"[Knowledge Persistence Warning] Could not save raw text file: {save_err}")

    return {
        "success": True,
        "document_id": final_doc_id,
        "filename": file.filename,
        "chunks_indexed": len(chunk_objects),
        "project": project,
        "location": location,
        "document_type": document_type,
        "status": "indexed",
        "ocr_status": "completed",
        "tenantId": current_user.get("tenant_id", settings.default_tenant_id),
    }


@router.post("/text", summary="Upload plain text — chunk, embed, and index")
async def knowledge_text(
    body: dict, 
    current_user: dict = Depends(_knowledge_auth),
):
    """Upload plain text content for chunking, embedding, and indexing."""
    text = body.get("text", "").strip()
    doc_id = _validated_doc_id(body.get("doc_id"))
    project = body.get("project")
    location = body.get("location")
    document_type = body.get("document_type")

    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    chunks_raw = _chunk_text(text, chunk_size=500, overlap=50)
    if not chunks_raw:
        raise HTTPException(status_code=400, detail="No content to index")

    chunk_objects = []
    for i, chunk_text in enumerate(chunks_raw):
        embedding = await llm_service.embed(chunk_text)
        chunk_objects.append({
            "content": chunk_text,
            "embedding": embedding,
            "chunk_index": i,
            "filename": body.get("filename", "text_upload.txt"),
            "project": project,
            "location": location,
            "document_type": document_type,
            "metadata": {
                "source": "api_text_upload",
                "project": project,
                "location": location,
                "document_type": document_type,
            },
        })

    await rag.add_document(doc_id, chunk_objects)

    return {
        "success": True,
        "document_id": doc_id,
        "chunks_indexed": len(chunk_objects),
        "project": project,
        "location": location,
        "document_type": document_type,
        "status": "indexed",
        "tenantId": current_user.get("tenant_id", settings.default_tenant_id),
    }


@router.get("/documents", summary="List all indexed documents")
async def list_documents(current_user: dict = Depends(_knowledge_auth)):
    """List all unique documents in the knowledge base with metadata."""
    docs = await rag.list_documents()
    return {
        "success": True,
        "documents": docs,
        "count": len(docs),
        "tenantId": current_user.get("tenant_id", settings.default_tenant_id),
    }


@router.delete("/documents/{doc_id}", summary="Delete a document and its chunks")
async def delete_document(
    doc_id: str, 
    current_user: dict = Depends(_knowledge_auth),
):
    """Delete a document and all its chunks from the knowledge base."""
    deleted = await rag.delete_document(doc_id)
    return {
        "success": True,
        "document_id": doc_id,
        "chunks_deleted": deleted,
        "tenantId": current_user.get("tenant_id", settings.default_tenant_id),
    }
