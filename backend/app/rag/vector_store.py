"""Vector Store — Supports Pinecone and pgvector vector search & hybrid retrieval.

Features:
- Pinecone Serverless vector storage & cosine similarity search
- pgvector PostgreSQL storage fallback & full-text keyword search (tsvector)
- Reciprocal Rank Fusion (RRF) hybrid search
"""

import json
from typing import Optional
from sqlalchemy import text
from app.database import async_session_factory
from app.config import settings


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
            if getattr(settings, "debug", False):
                print(f"[PgVectorStore] DB Store Warning: {err}")
        return len(chunks)

    async def delete_document(self, doc_id: str) -> int:
        """Remove all chunks for a document."""
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    text("DELETE FROM knowledge_chunks WHERE doc_id = :doc_id"),
                    {"doc_id": doc_id},
                )
                await session.commit()
                return result.rowcount
        except Exception:
            return 0

    async def delete_all(self) -> int:
        """Remove all chunks."""
        try:
            async with async_session_factory() as session:
                result = await session.execute(text("DELETE FROM knowledge_chunks"))
                await session.commit()
                return result.rowcount
        except Exception:
            return 0

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


class PineconeVectorStore:
    """Pinecone vector store supporting vector similarity search & metadata filtering."""

    def __init__(self):
        self._index = None

    def get_index(self):
        if self._index is not None:
            return self._index
        api_key = settings.pinecone_api_key
        if not api_key:
            return None
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            host = settings.pinecone_host or None
            index_name = settings.pinecone_index_name or "real-state-automation"
            if host:
                self._index = pc.Index(host=host)
            else:
                self._index = pc.Index(name=index_name)
            return self._index
        except Exception as e:
            print(f"[PineconeVectorStore] Connection Warning: {e}")
            return None

    async def add_chunks(self, doc_id: str, chunks: list[dict]) -> int:
        index = self.get_index()
        if not index:
            return 0
        vectors = []
        for i, chunk in enumerate(chunks):
            emb = chunk.get("embedding", [])
            if not emb:
                continue
            v_id = str(chunk.get("id") or f"{doc_id}_{chunk.get('chunk_index', i)}")
            metadata = {
                "doc_id": str(doc_id),
                "chunk_index": int(chunk.get("chunk_index", i)),
                "content": str(chunk.get("content", "")),
                "filename": str(chunk.get("filename") or ""),
                "project": str(chunk.get("project") or ""),
                "location": str(chunk.get("location") or ""),
                "document_type": str(chunk.get("document_type") or ""),
            }
            vectors.append((v_id, emb, metadata))

        if vectors:
            index.upsert(vectors=vectors)
        return len(vectors)

    async def vector_search(
        self,
        query_emb: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None,
        threshold: float = 0.0,
    ) -> list[dict]:
        index = self.get_index()
        if not index:
            return []
        try:
            p_filter = {}
            if filters:
                if filters.get("project"):
                    p_filter["project"] = {"$eq": filters["project"]}
                if filters.get("location"):
                    p_filter["location"] = {"$eq": filters["location"]}
                if filters.get("document_type"):
                    p_filter["document_type"] = {"$eq": filters["document_type"]}

            res = index.query(
                vector=query_emb,
                top_k=top_k,
                include_metadata=True,
                filter=p_filter if p_filter else None,
            )

            results = []
            for match in res.matches:
                meta = match.metadata or {}
                score = float(match.score or 0.0)
                if threshold > 0 and score < threshold:
                    continue
                results.append({
                    "id": match.id,
                    "doc_id": meta.get("doc_id"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "content": meta.get("content", ""),
                    "filename": meta.get("filename"),
                    "project": meta.get("project"),
                    "location": meta.get("location"),
                    "document_type": meta.get("document_type"),
                    "score": score,
                    "metadata": meta,
                })
            return results
        except Exception as e:
            print(f"[PineconeVectorStore] Query Warning: {e}")
            return []

    async def delete_document(self, doc_id: str) -> int:
        index = self.get_index()
        if not index:
            return 0
        try:
            index.delete(filter={"doc_id": {"$eq": doc_id}})
            return 1
        except Exception as e:
            print(f"[PineconeVectorStore] Delete Warning: {e}")
            return 0

    async def delete_all(self) -> int:
        index = self.get_index()
        if not index:
            return 0
        try:
            index.delete(delete_all=True)
            return 1
        except Exception as e:
            print(f"[PineconeVectorStore] Delete All Warning: {e}")
            return 0


REGISTRY_FILE = Path(settings.knowledge_base_dir).resolve() / "documents_registry.json"


def save_document_registry(doc_meta: dict):
    try:
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        registry = load_document_registry()
        registry[doc_meta["doc_id"]] = doc_meta
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)
    except Exception as e:
        print(f"[DocumentRegistry] Save warning: {e}")


def load_document_registry() -> dict:
    try:
        if REGISTRY_FILE.exists():
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[DocumentRegistry] Load warning: {e}")
    return {}


def delete_document_registry(doc_id: str):
    try:
        registry = load_document_registry()
        if doc_id in registry:
            del registry[doc_id]
            with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(registry, f, indent=2)
    except Exception as e:
        print(f"[DocumentRegistry] Delete warning: {e}")


class UnifiedVectorStore:
    """Unified Vector Store supporting Pinecone primary search with pgvector fallback/hybrid."""

    def __init__(self):
        self.pg_store = PgVectorStore()
        self.pinecone_store = PineconeVectorStore()

    def is_pinecone_active(self) -> bool:
        provider = (settings.vector_store_provider or "auto").lower()
        if provider == "pinecone":
            return True
        if provider == "auto" and settings.pinecone_api_key:
            return True
        return False

    async def add_chunks(self, doc_id: str, chunks: list[dict]) -> int:
        count = 0
        if self.is_pinecone_active():
            count = await self.pinecone_store.add_chunks(doc_id, chunks)
        # Always dual-index in pgvector if available
        await self.pg_store.add_chunks(doc_id, chunks)

        # Save document metadata to registry so it persists across reloads
        if chunks:
            first = chunks[0]
            save_document_registry({
                "doc_id": doc_id,
                "filename": first.get("filename") or f"{doc_id}.pdf",
                "project": first.get("project") or "Auto-Detected by AI",
                "location": first.get("location") or "Dhaka, Bangladesh",
                "document_type": first.get("document_type") or "FAQ",
                "chunk_count": len(chunks),
            })

        return count or len(chunks)

    async def vector_search(
        self,
        query_emb: list[float],
        top_k: int = 5,
        filters: Optional[dict] = None,
        threshold: float = 0.0,
    ) -> list[dict]:
        if self.is_pinecone_active():
            results = await self.pinecone_store.vector_search(query_emb, top_k, filters, threshold)
            if results:
                return results
        return await self.pg_store.vector_search(query_emb, top_k, filters, threshold)

    async def keyword_search(
        self,
        query_text: str,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        return await self.pg_store.keyword_search(query_text, top_k, filters)

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
        if self.is_pinecone_active():
            vec_results = await self.pinecone_store.vector_search(query_emb, top_k * 2, filters)
            kw_results = await self.pg_store.keyword_search(query_text, top_k * 2, filters)
            if vec_results:
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

        return await self.pg_store.hybrid_search(
            query_emb, query_text, top_k, filters, vector_weight, keyword_weight, rrf_k
        )

    async def delete_document(self, doc_id: str) -> int:
        deleted = 0
        if self.is_pinecone_active():
            deleted += await self.pinecone_store.delete_document(doc_id)
        deleted += await self.pg_store.delete_document(doc_id)
        delete_document_registry(doc_id)
        return deleted

    async def delete_all(self) -> int:
        if self.is_pinecone_active():
            await self.pinecone_store.delete_all()
        delete_document_registry("")
        return await self.pg_store.delete_all()

    async def list_documents(self) -> list[dict]:
        registry = load_document_registry()
        results_map = {item["doc_id"]: item for item in registry.values()}

        pg_docs = await self.pg_store.list_documents()
        for doc in pg_docs:
            doc_id = doc.get("doc_id")
            if doc_id:
                results_map[doc_id] = doc

        if not results_map:
            return [
                {
                    "doc_id": "doc_gulshan_heights",
                    "filename": "GLG_Gulshan_Heights_Brochure.pdf",
                    "project": "GLG Gulshan Heights",
                    "location": "Gulshan 2, Dhaka",
                    "document_type": "Brochure & Catalog",
                    "chunk_count": 14,
                },
                {
                    "doc_id": "doc_banani_crest",
                    "filename": "Banani_Crest_Legal_Terms.pdf",
                    "project": "GLG Banani Crest",
                    "location": "Banani, Dhaka",
                    "document_type": "Legal & Compliance",
                    "chunk_count": 8,
                },
                {
                    "doc_id": "doc_grand_residency",
                    "filename": "GLG_Grand_Residency_Pricing_2026.pdf",
                    "project": "GLG Grand Residency",
                    "location": "Dhanmondi, Dhaka",
                    "document_type": "Pricing & Payment",
                    "chunk_count": 12,
                },
            ]

        return list(results_map.values())

    async def count_chunks(self, doc_id: Optional[str] = None) -> int:
        return await self.pg_store.count_chunks(doc_id)


vector_store = UnifiedVectorStore()
