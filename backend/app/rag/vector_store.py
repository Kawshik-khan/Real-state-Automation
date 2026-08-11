"""Vector Store — pgvector-backed vector search and hybrid retrieval.

Flow:
1. add_chunks() — Bulk insert chunks into pgvector knowledge_chunks table
2. vector_search() — Cosine similarity search using CAST(:emb AS vector)
3. keyword_search() — PostgreSQL full-text search using tsvector / tsquery
4. hybrid_search() — Reciprocal Rank Fusion (RRF) combining vector + keyword
"""

import json
from typing import Optional
from sqlalchemy import text
from app.database import async_session_factory


class PgVectorStore:
    """pgvector store supporting vector, keyword, and hybrid search."""

    async def add_chunks(self, doc_id: str, chunks: list[dict]) -> int:
        """Store chunk records with embeddings in pgvector table."""
        try:
            async with async_session_factory() as session:
                for chunk in chunks:
                    emb = chunk.get("embedding", [])
                    emb_str = "[" + ",".join(str(v) for v in emb) + "]" if emb else None
                    meta_json = json.dumps(chunk.get("metadata", {}))

                    row = {
                        "id": chunk.get("id") or f"{doc_id}_{chunk.get('chunk_index', 0)}",
                        "doc_id": doc_id,
                        "chunk_index": chunk.get("chunk_index", 0),
                        "content": chunk.get("content", ""),
                        "embedding": emb_str,
                        "metadata": meta_json,
                        "filename": chunk.get("filename"),
                        "project": chunk.get("project"),
                        "location": chunk.get("location"),
                        "document_type": chunk.get("document_type"),
                    }
                    await session.execute(
                        text("""
                            INSERT INTO knowledge_chunks
                                (id, doc_id, chunk_index, content, embedding,
                                 metadata, filename, project, location, document_type)
                            VALUES
                                (:id, :doc_id, :chunk_index, :content, CAST(:embedding AS vector),
                                 CAST(:metadata AS jsonb), :filename, :project, :location, :document_type)
                        """),
                        row,
                    )
                await session.commit()
        except Exception as err:
            print(f"[PgVectorStore] DB Store Warning: {err}")
        return len(chunks)

    async def delete_document(self, doc_id: str) -> int:
        """Remove all chunks for a document."""
        async with async_session_factory() as session:
            result = await session.execute(
                text("DELETE FROM knowledge_chunks WHERE doc_id = :doc_id"),
                {"doc_id": doc_id},
            )
            await session.commit()
            return result.rowcount

    async def delete_all(self) -> int:
        """Remove all chunks."""
        async with async_session_factory() as session:
            result = await session.execute(text("DELETE FROM knowledge_chunks"))
            await session.commit()
            return result.rowcount

    async def vector_search(
        self,
        query_emb: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None,
        threshold: float = 0.7,
    ) -> list[dict]:
        """Cosine similarity search with optional metadata filters."""
        try:
            emb_str = "[" + ",".join(str(v) for v in query_emb) + "]"
            where_clauses = ["c.embedding IS NOT NULL"]
            params: dict = {"emb": emb_str, "limit": top_k}

            if filters:
                if filters.get("project"):
                    where_clauses.append("c.project = :project")
                    params["project"] = filters["project"]
                if filters.get("location"):
                    where_clauses.append("c.location = :location")
                    params["location"] = filters["location"]

            where_sql = " AND ".join(where_clauses)
            sql = f"""
                SELECT c.id, c.doc_id, c.chunk_index, c.content, c.filename,
                       c.project, c.location, c.document_type, c.metadata,
                       1 - (c.embedding <=> CAST(:emb AS vector)) AS score
                FROM knowledge_chunks c
                WHERE {where_sql}
                ORDER BY score DESC
                LIMIT :limit
            """
            async with async_session_factory() as session:
                result = await session.execute(text(sql), params)
                rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception:
            return []

    async def keyword_search(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """Full-text search using tsvector with optional filters."""
        try:
            where_clauses = ["c.content_tsv @@ plainto_tsquery('english', :query)"]
            params: dict = {"query": query_text, "limit": top_k}
            if filters:
                if filters.get("project"):
                    where_clauses.append("c.project = :project")
                    params["project"] = filters["project"]

            where_sql = " AND ".join(where_clauses)
            sql = f"""
                SELECT c.id, c.doc_id, c.chunk_index, c.content, c.filename,
                       c.project, c.location, c.document_type, c.metadata,
                       ts_rank(c.content_tsv, plainto_tsquery('english', :query)) AS score
                FROM knowledge_chunks c
                WHERE {where_sql}
                ORDER BY score DESC
                LIMIT :limit
            """
            async with async_session_factory() as session:
                result = await session.execute(text(sql), params)
                rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception:
            return []

    async def hybrid_search(
        self,
        query_emb: list[float],
        query_text: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
        vector_weight: float = 0.5,
        keyword_weight: float = 0.5,
        rrf_k: int = 60,
    ) -> list[dict]:
        """Hybrid search using Reciprocal Rank Fusion (RRF)."""
        vec_results = await self.vector_search(query_emb, top_k * 2, filters, threshold=0.0)
        kw_results = await self.keyword_search(query_text, top_k * 2, filters)

        rrf_scores: dict[str, dict] = {}
        for rank, row in enumerate(vec_results):
            doc_id = str(row["id"])
            entry = rrf_scores.setdefault(doc_id, {k: row[k] for k in row if k != "score"})
            entry.setdefault("rrf_score", 0.0)
            entry.setdefault("vector_score", 0.0)
            entry.setdefault("keyword_score", 0.0)
            entry["rrf_score"] += vector_weight / (rrf_k + rank + 1)
            entry["vector_score"] = float(row.get("score", 0.0))

        for rank, row in enumerate(kw_results):
            doc_id = str(row["id"])
            entry = rrf_scores.setdefault(doc_id, {k: row[k] for k in row if k != "score"})
            entry.setdefault("rrf_score", 0.0)
            entry.setdefault("vector_score", 0.0)
            entry.setdefault("keyword_score", 0.0)
            entry["rrf_score"] += keyword_weight / (rrf_k + rank + 1)
            entry["keyword_score"] = float(row.get("score", 0.0))

        sorted_items = sorted(rrf_scores.values(), key=lambda x: x["rrf_score"], reverse=True)
        return sorted_items[:top_k]

    async def list_documents(self) -> list[dict]:
        """List unique document metadata."""
        try:
            sql = """
                SELECT doc_id, filename, project, location, document_type, COUNT(*) as chunk_count
                FROM knowledge_chunks
                GROUP BY doc_id, filename, project, location, document_type
            """
            async with async_session_factory() as session:
                result = await session.execute(text(sql))
                rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception:
            return []

    async def count_chunks(self, doc_id: Optional[str] = None) -> int:
        """Count chunks."""
        try:
            sql = "SELECT COUNT(*) FROM knowledge_chunks"
            params = {}
            if doc_id:
                sql += " WHERE doc_id = :doc_id"
                params["doc_id"] = doc_id
            async with async_session_factory() as session:
                result = await session.execute(text(sql), params)
                return result.scalar() or 0
        except Exception:
            return 0


vector_store = PgVectorStore()
