import asyncio
import json
from typing import Optional

from openai import AsyncOpenAI, RateLimitError

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

    async def chat(
        self,
        messages: list,
        response_format: Optional[dict] = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        client = self.get_client()
        if not client:
            return json.dumps({"reply": "AI service not configured", "intent": "fallback", "confidence": 0.5})
        
        target_model = self.model
        kwargs = dict(model=target_model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        if response_format:
            kwargs["response_format"] = response_format

        for attempt in range(4):
            try:
                resp = await client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except RateLimitError as rle:
                if attempt == 3:
                    print(f"[LLMService Error] Rate limit exceeded after 4 attempts: {rle}")
                    raise rle
                # Fallback to gpt-oss-20b if 120b is rate limited on Groq
                if "120b" in kwargs["model"]:
                    print("[LLMService RateLimit] Falling back from 120b to gpt-oss-20b for fast recovery...")
                    kwargs["model"] = "openai/gpt-oss-20b"
                    continue
                err_msg = str(rle)
                wait_sec = 2.0 * (2 ** attempt)
                if "try again in " in err_msg:
                    try:
                        wait_sec = min(15.0, float(err_msg.split("try again in ")[1].split("s")[0]) + 0.5)
                    except Exception:
                        pass
                print(f"[LLMService RateLimit] Rate limited on {kwargs['model']}. Waiting {wait_sec:.1f}s before retry {attempt+1}...")
                await asyncio.sleep(wait_sec)

        return ""

    async def structured_chat(
        self,
        messages: list,
        json_schema: dict,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> dict:
        client = self.get_client()
        if not client:
            return {"reply": "AI service not configured", "intent": "fallback", "confidence": 0.5}
        
        target_model = self.model
        kwargs = dict(
            model=target_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if "groq.com" not in (settings.openai_base_url or ""):
            kwargs["response_format"] = {"type": "json_object"}
            
        for attempt in range(4):
            try:
                resp = await client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content or "{}"
                # Clean markdown JSON formatting if present (```json ... ```)
                if "```" in content:
                    content = content.split("```json")[-1].split("```")[0].strip()
                    if not content.startswith("{"):
                        content = content.split("```")[-1].strip()
                return json.loads(content)
            except RateLimitError as rle:
                if attempt == 3:
                    print(f"[LLMService Error] structured_chat rate limit exceeded: {rle}")
                    break
                if "120b" in kwargs["model"]:
                    print("[LLMService RateLimit] Falling back from 120b to gpt-oss-20b in structured_chat...")
                    kwargs["model"] = "openai/gpt-oss-20b"
                    continue
                err_msg = str(rle)
                wait_sec = 2.0 * (2 ** attempt)
                if "try again in " in err_msg:
                    try:
                        wait_sec = min(15.0, float(err_msg.split("try again in ")[1].split("s")[0]) + 0.5)
                    except Exception:
                        pass
                print(f"[LLMService RateLimit] Waiting {wait_sec:.1f}s in structured_chat retry {attempt+1}...")
                await asyncio.sleep(wait_sec)
            except Exception as e:
                print(f"[LLMService Error] structured_chat failed: {e}")
                return {"reply": "I am unable to process that right now.", "intent": "fallback", "confidence": 0.5}

        return {"reply": "I am unable to process that right now.", "intent": "fallback", "confidence": 0.5}

    def __init__(self):
        self._pinecone_client = None
        self._pinecone_offline = False

    def get_pinecone_client(self):
        if getattr(self, "_pinecone_offline", False):
            return None
        if not self._pinecone_client and settings.pinecone_api_key:
            try:
                from pinecone import Pinecone
                self._pinecone_client = Pinecone(api_key=settings.pinecone_api_key)
            except Exception as e:
                print(f"[LLMService] Pinecone init error: {e}")
                self._pinecone_offline = True
        return self._pinecone_client

    async def embed(self, text: str, input_type: str = "passage") -> list[float]:
        res = await self.embed_batch([text], input_type=input_type)
        return res[0] if res else []

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
                err_str = str(pe)
                if "getaddrinfo" in err_str or "ConnectError" in err_str or "11001" in err_str:
                    self._pinecone_offline = True
                print(f"[LLMService] Pinecone Inference batch embedding failed: {pe}")

        # 3. Fallback deterministic semantic feature-hash vectors (words, bigrams & character 3-grams)
        import hashlib
        import math
        import re

        fallback_vecs = []
        for text in texts:
            vec = [0.0] * target_dim
            words = re.findall(r"\w+", text.lower())
            tokens = list(words)
            # Add word bigrams
            for i in range(len(words) - 1):
                tokens.append(f"{words[i]}_{words[i+1]}")
            # Add character 3-grams for subword matching
            clean_str = f" {text.lower()} "
            if len(clean_str) >= 3:
                tokens.extend([clean_str[i:i + 3] for i in range(len(clean_str) - 2)])

            for tok in tokens:
                h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
                idx = h % target_dim
                sign = 1.0 if ((h >> 16) & 1) else -1.0
                vec[idx] += sign

            # Normalize to unit length (L2 norm)
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 0:
                vec = [v / norm for v in vec]
            else:
                vec = [0.0] * target_dim

            fallback_vecs.append(vec)
        return fallback_vecs


llm_service = LLMService()
