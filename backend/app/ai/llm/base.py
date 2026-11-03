"""
AI LLM Provider Abstraction.
Section 37, 38, 39:
- Provider interface: generate, generate_structured, stream
- Strict Pydantic-validated structured outputs
- Exponential backoff retry policy for transient errors
"""
import abc
import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

from app.core.exceptions import AIServiceException
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    latency_ms: float = 0.0


class LLMProvider(abc.ABC):
    """Abstract Base Class for LLM Providers."""

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate free-form completion text."""
        pass

    @abc.abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        max_retries: int = 2,
    ) -> T:
        """
        Generate structured output validated against Pydantic schema.
        Retries on validation error up to max_retries.
        """
        pass

    @abc.abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        """Stream token chunks."""
        pass
