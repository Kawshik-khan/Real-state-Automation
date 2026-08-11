"""Re-ranker — LLM-based relevance scoring for RAG results.

Takes the original query + retrieved chunks and scores each chunk
for relevance, returning only the most relevant ones.
"""

from app.services.llm import llm_service


def reciprocal_rank_fusion(vector_results: list[dict], keyword_results: list[dict], k: int = 60) -> list[dict]:
    """Combines dense vector search results and sparse BM25 keyword search results
    using Reciprocal Rank Fusion (RRF): RRF_score(doc) = sum(1 / (k + rank(doc)))
    """
    scores: dict[str, float] = {}
    chunk_map: dict[str, dict] = {}

    for rank, chunk in enumerate(vector_results):
        cid = str(chunk.get("id", chunk.get("doc_id", hash(str(chunk)))))
        chunk_map[cid] = chunk
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)

    for rank, chunk in enumerate(keyword_results):
        cid = str(chunk.get("id", chunk.get("doc_id", hash(str(chunk)))))
        chunk_map[cid] = chunk
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)

    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    fused_chunks = []
    for cid in sorted_ids:
        c = chunk_map[cid].copy()
        c["rrf_score"] = round(scores[cid], 5)
        fused_chunks.append(c)

    return fused_chunks


RERANKER_PROMPT = """You are a relevance re-ranker for a real-estate RAG system.
You will be given a user query and several document chunks.
Score each chunk's relevance to the query on a scale of 0.0 to 1.0.
Only keep chunks with score >= 0.5.

Respond with a JSON object:
{
  "scored_chunks": [
    {"index": 0, "relevance_score": 0.95, "reason": "Directly answers the question"},
    {"index": 1, "relevance_score": 0.3, "reason": "Tangential information"}
  ]
}"""


class Reranker:
    """LLM-based chunk re-ranker for improving RAG result quality."""

    async def rerank(self, query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
        """Re-rank chunks by relevance to the query.

        For small sets (<= top_k), returns as-is.
        For 5 or fewer chunks, returns top_k without LLM call.
        For larger sets, uses LLM to score relevance.
        """
        if not chunks:
            return []
        if len(chunks) <= top_k:
            return chunks
        if len(chunks) <= 5:
            return chunks[:top_k]

        chunks_text = "\n\n---\n\n".join(
            f"[{i}] {c.get('content', '')[:300]}"
            for i, c in enumerate(chunks)
        )
        messages = [
            {"role": "system", "content": RERANKER_PROMPT},
            {
                "role": "user",
                "content": f"Query: {query}\n\nChunks:\n{chunks_text}",
            },
        ]
        try:
            result = await llm_service.structured_chat(messages, json_schema={}, temperature=0.1)
            scored = result.get("scored_chunks", [])
            if not scored:
                return chunks[:top_k]

            # Map scores back to original chunks, filter by threshold
            scored_map = {
                s["index"]: s["relevance_score"]
                for s in scored
                if s.get("relevance_score", 0) >= 0.5
            }
            ranked = [
                (scored_map.get(i, 0), chunks[i])
                for i in range(len(chunks))
                if i in scored_map
            ]
            ranked.sort(key=lambda x: -x[0])
            return [chunk for _, chunk in ranked[:top_k]]
        except Exception:
            return chunks[:top_k]


reranker = Reranker()
