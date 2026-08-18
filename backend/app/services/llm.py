import json
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings


class LLMService:
    def get_client(self) -> Optional[AsyncOpenAI]:
        if not settings.openai_api_key:
            return None
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return AsyncOpenAI(**kwargs)

    @property
    def model(self) -> str:
        return settings.openai_model or "openai/gpt-oss-120b"

    async def chat(self, messages: list, response_format: Optional[dict] = None, temperature: float = 0.3) -> str:
        client = self.get_client()
        if not client:
            return json.dumps({"reply": "AI service not configured", "intent": "fallback", "confidence": 0.5})
        kwargs = dict(model=self.model, messages=messages, temperature=temperature)
        if response_format:
            kwargs["response_format"] = response_format
        resp = await client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    async def structured_chat(self, messages: list, json_schema: dict, temperature: float = 0.3) -> dict:
        client = self.get_client()
        if not client:
            return {"reply": "AI service not configured", "intent": "fallback", "confidence": 0.5}
        
        # Ensure system message requests valid JSON if response_format json_object is set
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        if "groq.com" not in (settings.openai_base_url or ""):
            kwargs["response_format"] = {"type": "json_object"}
            
        try:
            resp = await client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or "{}"
            # Clean markdown JSON formatting if present (```json ... ```)
            if "```" in content:
                content = content.split("```json")[-1].split("```")[0].strip()
                if not content.startswith("{"):
                    content = content.split("```")[-1].strip()
            return json.loads(content)
        except Exception as e:
            print(f"[LLMService Error] structured_chat failed: {e}")
            return {"reply": "I am unable to process that right now.", "intent": "fallback", "confidence": 0.5}

    def __init__(self):
        self._pinecone_client = None

    def get_pinecone_client(self):
        if self._pinecone_client is None and settings.pinecone_api_key:
            try:
                from pinecone import Pinecone
                self._pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
            except Exception as e:
                print(f"[LLMService] Failed initializing Pinecone client: {e}")
        return self._pinecone_client

    async def embed(self, text: str, input_type: str = "passage") -> list[float]:
        results = await self.embed_batch([text], input_type=input_type)
        return results[0] if results else [(0.0) for _ in range(getattr(settings, "vector_dim", 1024))]

    async def embed_batch(self, texts: list[str], input_type: str = "passage") -> list[list[float]]:
        if not texts:
            return []

        target_dim = getattr(settings, "vector_dim", 1024)

        # 1. Try OpenAI embeddings
        client = self.get_client()
        if client and "groq.com" not in (settings.openai_base_url or ""):
            try:
                emb_model = getattr(settings, "openai_embedding_model", None) or "text-embedding-3-large"
                kwargs = {"model": emb_model, "input": texts}
                if "text-embedding-3" in emb_model:
                    kwargs["dimensions"] = target_dim
                resp = await client.embeddings.create(**kwargs)
                return [d.embedding for d in resp.data]
            except Exception as e:
                print(f"[LLMService] OpenAI batch embedding failed: {e}")

        # 2. Try Pinecone Inference API (multilingual-e5-large outputs 1024-dim)
        pc = self.get_pinecone_client()
        if pc:
            try:
                all_vectors = []
                batch_size = 96
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    res = pc.inference.embed(
                        model="multilingual-e5-large",
                        inputs=batch,
                        parameters={"input_type": input_type, "truncate": "END"}
                    )
                    all_vectors.extend([r["values"] for r in res])
                return all_vectors
            except Exception as pe:
                print(f"[LLMService] Pinecone Inference batch embedding failed: {pe}")

        # 3. Fallback deterministic hash vectors
        import hashlib
        fallback_vecs = []
        for text in texts:
            h = hashlib.sha256(text.encode()).digest()
            fallback_vecs.append([(h[i % 32] / 255.0) - 0.5 for i in range(target_dim)])
        return fallback_vecs


llm_service = LLMService()
