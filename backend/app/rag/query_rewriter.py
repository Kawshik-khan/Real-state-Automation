"""Query Rewriter — Uses LLM to rewrite and expand user queries for better retrieval.

Transforms natural language questions into multiple search-optimized query variants,
extracts structured filters (location, project, budget), and generates
expanded keyword variants.
"""

from app.services.llm import llm_service

QUERY_REWRITER_PROMPT = """You are a query rewriting assistant for a real-estate knowledge base.
Given a user's question, generate 3 search-optimized query variants that will help
retrieve the most relevant documents from a vector database.

Also extract any structured filters:
- project: specific project name (null if none)
- location: city or area mentioned (null if none)
- document_type: type of document needed (null if none)

Respond with JSON:
{
  "original_query": "...",
  "queries": ["variant 1", "variant 2", "variant 3"],
  "filters": {
    "project": null,
    "location": null,
    "document_type": null
  },
  "keywords": ["keyword1", "keyword2", ...]
}"""


class QueryRewriter:
    """Rewrites user queries into multiple search variants + metadata filters."""

    async def rewrite(self, query: str) -> dict:
        """Rewrite a user query into search-optimized variants and filters.

        Returns:
            dict with keys: original_query, queries (list), filters (dict), keywords (list)
        """
        if not query.strip():
            return {
                "original_query": query,
                "queries": [query],
                "filters": {},
                "keywords": [],
            }

        messages = [
            {"role": "system", "content": QUERY_REWRITER_PROMPT},
            {"role": "user", "content": query},
        ]
        try:
            result = await llm_service.structured_chat(messages, json_schema={}, temperature=0.3)
            if not isinstance(result, dict):
                result = {}
            if "queries" not in result or not result.get("queries"):
                result["queries"] = [query]
            return result
        except Exception:
            return {
                "original_query": query,
                "queries": [query],
                "filters": {},
                "keywords": [query],
            }


query_rewriter = QueryRewriter()
