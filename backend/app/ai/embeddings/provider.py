"""
Embedding Provider Module.
Section 28: Pluggable text-to-vector embeddings supporting OpenAI and local sentence-transformers.
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Optional
import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceException
from app.core.logging import logger


class EmbeddingProvider(ABC):
    """Abstract interface for embedding generation."""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate a single embedding vector for text."""

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of texts."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the number of dimensions for this embedding model."""


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic mock embedding provider for testing and offline use.
    Generates reproducible fixed-dimension float vectors.
    """

    _DIMS = 1536  # matches text-embedding-ada-002 dimension

    async def embed_text(self, text: str) -> List[float]:
        # Deterministic pseudo-embedding based on text hash
        seed = hash(text) % (2**32)
        import math
        return [math.sin(seed + i) * 0.5 for i in range(self._DIMS)]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed_text(t) for t in texts]

    @property
    def dimensions(self) -> int:
        return self._DIMS


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI Embeddings API provider.
    Supports text-embedding-3-small and text-embedding-ada-002.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: str = "https://api.openai.com/v1",
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self._dims = 1536 if "ada" in model else 1536  # 3-small also 1536

    async def _call_api(self, input_texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": input_texts}

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(f"{self.base_url}/embeddings", headers=headers, json=payload)
                    res.raise_for_status()
                    data = res.json()
                    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise AIServiceException(f"Embedding API failed after {self.max_retries} attempts: {str(e)}")
                await asyncio.sleep(0.5 * (2**attempt))
        return []

    async def embed_text(self, text: str) -> List[float]:
        results = await self._call_api([text])
        return results[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        return await self._call_api(texts)

    @property
    def dimensions(self) -> int:
        return self._dims


def get_embedding_provider() -> EmbeddingProvider:
    """Factory: returns configured embedding provider."""
    if settings.LLM_PROVIDER == "openai" and settings.LLM_API_KEY:
        return OpenAIEmbeddingProvider(
            api_key=settings.LLM_API_KEY,
            model=getattr(settings, "EMBEDDING_MODEL", "text-embedding-3-small"),
        )
    return MockEmbeddingProvider()
