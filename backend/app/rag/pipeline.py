"""RAG Pipeline — Full orchestration: rewrite → hybrid search → rerank → context.

Replaces the in-memory MVP pipeline with pgvector-backed hybrid search
including query rewriting, metadata filtering, and LLM re-ranking.
"""

from typing import Optional

from app.rag.query_rewriter import query_rewriter
from app.rag.reranker import reciprocal_rank_fusion, reranker
from app.rag.vector_store import vector_store
from app.services.llm import llm_service


class RAGPipeline:
    """Production RAG pipeline with pgvector-backed hybrid search.

    Flow:
    1. add_document() — chunk + embed + store in pgvector
    2. query() — rewrite → hybrid BM25 + Vector RRF search → rerank → build context
    3. build_context() — format chunks into LLM context string
    """

    async def add_document(self, doc_id: str, chunks: list[dict]):
        """Store document chunks with embeddings into pgvector.

        Each chunk must have 'content'. If 'embedding' is missing,
        it's generated automatically.
        """
        for chunk in chunks:
            if "embedding" not in chunk or not chunk["embedding"]:
                chunk["embedding"] = await llm_service.embed(
                    chunk.get("content", chunk.get("text", ""))
                )
            chunk["doc_id"] = doc_id
        await vector_store.add_chunks(doc_id, chunks)

    async def query(
        self,
        query_text: str,
        top_k: int = 3,
        filters: dict = None,
        use_hybrid: bool = True,
    ) -> list[dict]:
        """Full RAG pipeline: rewrite → Vector + BM25 RRF Search → rerank.

        Args:
            query_text: User query string
            top_k: Number of results to return
            filters: Optional metadata filters (project, location, document_type)
            use_hybrid: If True, use hybrid RRF (vector + keyword) search; else vector-only

        Returns:
            List of chunk dicts with content, metadata, scores
        """
        if not query_text.strip():
            return []

        # Step 1: Query rewriting
        try:
            rewritten = await query_rewriter.rewrite(query_text)
            search_queries = rewritten.get("queries", [query_text])
            merged_filters = {**(filters or {}), **rewritten.get("filters", {})}
            keywords = rewritten.get("keywords", [])
        except Exception:
            search_queries = [query_text]
            merged_filters = filters or {}
            keywords = []

        # Step 2: Get query embedding
        query_emb = []
        try:
            query_emb = await llm_service.embed(query_text)
        except Exception:
            pass

        # Step 3: Run Vector Search and Keyword Search
        vector_results: list[dict] = []
        for q in search_queries:
            results = await vector_store.vector_search(query_emb, top_k=top_k * 2, filters=merged_filters)
            vector_results.extend(results)

        kw_query = " ".join(keywords) if keywords else query_text
        keyword_results = await vector_store.keyword_search(kw_query, top_k=top_k * 2, filters=merged_filters)

        # Step 4: Apply Reciprocal Rank Fusion (RRF)
        if use_hybrid and keyword_results:
            all_candidates = reciprocal_rank_fusion(vector_results, keyword_results, k=60)
        else:
            all_candidates = vector_results + keyword_results

        # Deduplicate candidates while preserving RRF rank order
        seen_ids = set()
        deduped = []
        for r in all_candidates:
            rid = str(r.get("id", r.get("doc_id", hash(str(r)))))
            if rid not in seen_ids:
                seen_ids.add(rid)
                deduped.append(r)

        # Step 5: Re-rank candidates using LLM Reranker
        try:
            ranked = await reranker.rerank(query_text, deduped, top_k=top_k)
            return ranked if ranked else deduped[:top_k]
        except Exception:
            return deduped[:top_k]

    async def build_context(self, chunks: list[dict]) -> str:
        """Build a context string from retrieved chunks for LLM consumption."""
        if not chunks:
            return ""

        parts = []
        for i, chunk in enumerate(chunks):
            text = chunk.get("content", "")
            filename = chunk.get("filename", "")
            project = chunk.get("project", "")
            loc = chunk.get("location", "")

            header = f"[Source {i+1}]"
            if filename:
                header += f" ({filename})"
            if project or loc:
                header += f" — {project} / {loc}".strip(" —/")
            parts.append(f"{header}:\n{text}")

        return "\n\n---\n\n".join(parts)

    async def delete_document(self, doc_id: str) -> int:
        """Remove a document and all its chunks from the store."""
        return await vector_store.delete_document(doc_id)

    async def list_documents(self) -> list[dict]:
        """List all unique documents with metadata and chunk counts."""
        return await vector_store.list_documents()

    async def count_chunks(self, doc_id: Optional[str] = None) -> int:
        """Count chunks in the store."""
        return await vector_store.count_chunks(doc_id)


rag = RAGPipeline()
