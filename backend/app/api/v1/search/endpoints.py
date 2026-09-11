"""Search API — POST /api/search for hybrid search across knowledge base."""

from fastapi import APIRouter, Depends

from app.dependencies import require_automation_secret as _auth
from app.rag.pipeline import rag

router = APIRouter()


@router.post("/search", summary="Hybrid search across knowledge base")
async def search_knowledge(body: dict, auth: dict = Depends(_auth)):
    """Search the knowledge base using hybrid search (vector + full-text).

    Request body:
    {
        "query": "What documents are needed for home loan?",
        "top_k": 3,
        "filters": {
            "project": "GLG Gulshan Heights",
            "location": "Gulshan 2, Dhaka",
            "document_type": "legal"
        }
    }
    """
    query = body.get("query", "").strip()
    if not query:
        return {
            "success": False,
            "results": [],
            "count": 0,
            "message": "Query is required",
            "tenantId": auth["tenant_id"],
        }

    top_k = min(int(body.get("top_k", 3)), 20)
    filters = body.get("filters", None)
    use_hybrid = body.get("use_hybrid", True)

    results = await rag.query(query, top_k=top_k, filters=filters, use_hybrid=use_hybrid)

    # Strip embeddings from response (too large to transmit)
    clean_results = []
    for r in results:
        clean = {k: v for k, v in r.items() if k not in ("embedding",)}
        clean_results.append(clean)

    return {
        "success": True,
        "results": clean_results,
        "count": len(clean_results),
        "query": query,
        "filters_applied": filters,
        "tenantId": auth["tenant_id"],
    }
