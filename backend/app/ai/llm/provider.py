"""
LLM Provider Implementations: Mock and OpenAI-compatible Providers.
Section 37, 38, 39: Interfaces, Structured Output, and Retry Policies.
"""
import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel, ValidationError

from app.ai.llm.base import LLMProvider, LLMResponse
from app.core.config import settings
from app.core.exceptions import AIServiceException
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """
    Mock LLM Provider for testing and offline execution.
    Generates deterministic, schema-compliant responses based on prompt keywords.
    """

    def __init__(self, model_name: str = "mock-gpt-4o"):
        self.model_name = model_name
        self.provider_name = "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        content = "This is a mock LLM generated response based on prompt context."
        return LLMResponse(
            content=content,
            model=self.model_name,
            provider=self.provider_name,
            tokens_used=42,
            latency_ms=10.0,
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        max_retries: int = 2,
    ) -> T:
        """Dynamically construct a schema-compliant mock object based on target Pydantic model."""
        model_name = response_model.__name__

        # Question Generation
        if "Question" in model_name:
            topic = "Python"
            if "FastAPI" in prompt:
                topic = "FastAPI"
            elif "Pandas" in prompt:
                topic = "Pandas"
            elif "Machine Learning" in prompt:
                topic = "Machine Learning"
            elif "Statistics" in prompt:
                topic = "Statistics"

            # Derive variation count from prompt to guarantee unique question formulations
            prev_count = prompt.count("\n- ") + prompt.count("attempt")
            subtopics = ["Memory Management", "Concurrency & Async", "API Architecture", "Performance Tuning", "Data Structures"]
            selected_subtopic = subtopics[prev_count % len(subtopics)]

            mock_payload = {
                "question": f"Explain key architectural design considerations and trade-offs in {topic} regarding {selected_subtopic} (Question #{prev_count + 1}).",
                "topic": topic,
                "subtopic": selected_subtopic,
                "difficulty": "intermediate",
                "question_type": "conceptual",
                "expected_concepts": [
                    "memory allocation",
                    "vectorization or garbage collection",
                    "time complexity",
                    "practical best practices"
                ],
                "evaluation_rubric": {
                    "accuracy_criteria": "Must accurately describe core memory/execution model",
                    "concept_coverage_weight": 0.35,
                    "completeness_weight": 0.35,
                    "reasoning_weight": 0.30,
                    "required_concepts": ["memory allocation", "vectorization or garbage collection"],
                    "common_mistakes": ["confusing pass-by-reference with pass-by-assignment"]
                },
                "source_document_ids": []
            }
            return response_model.model_validate(mock_payload)

        # Interview Manager Decision
        elif "Manager" in model_name or "Decision" in model_name:
            mock_payload = {
                "action": "GENERATE_NEW_QUESTION",
                "topic": "Python",
                "difficulty": "intermediate",
                "question_type": "conceptual",
                "reason": "Proceeding with standard topic progression.",
                "follow_up": False
            }
            return response_model.model_validate(mock_payload)

        # Answer Technical Evaluation
        elif "Technical" in model_name or "AnswerEvaluation" in model_name:
            mock_payload = {
                "correctness": 88.0,
                "concept_coverage": 85.0,
                "completeness": 80.0,
                "reasoning": 82.0,
                "missing_concepts": ["specific garbage collection generation threshold"],
                "incorrect_claims": [],
                "strengths": ["Clear explanation of memory allocation", "Good reference to GIL and reference counting"],
                "weaknesses": ["Could provide a concrete code example"],
                "confidence": 0.92,
                "needs_human_review": False,
            }
            return response_model.model_validate(mock_payload)

        # Grammar Evaluation
        elif "Grammar" in model_name:
            mock_payload = {
                "grammar_score": 85.0,
                "errors": ["Minor subject-verb agreement"],
                "corrections": ["Use 'is managed' instead of 'is manage'"],
                "examples": ["Good technical vocabulary usage"],
            }
            return response_model.model_validate(mock_payload)

        # Communication Evaluation
        elif "Communication" in model_name:
            mock_payload = {
                "clarity_score": 85.0,
                "structure_score": 80.0,
                "relevance_score": 90.0,
                "conciseness_score": 82.0,
                "communication_score": 84.25,
                "structure_feedback": "Well-structured response following definition-explanation format.",
            }
            return response_model.model_validate(mock_payload)

        # Fallback: attempt to build default model instance
        try:
            return response_model()  # type: ignore
        except Exception:
            raise AIServiceException(f"Mock provider cannot fabricate response for {model_name}")

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        tokens = ["This ", "is ", "a ", "mock ", "streamed ", "response."]
        for t in tokens:
            yield t


class OpenAILLMProvider(LLMProvider):
    """
    OpenAI-compatible HTTP LLM Provider.
    Supports structured JSON schema outputs and exponential backoff retry.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.provider_name = "openai"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                latency_ms = round((time.perf_counter() - start) * 1000, 2)
                return LLMResponse(
                    content=content,
                    model=self.model_name,
                    provider=self.provider_name,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                )
            except Exception as e:
                raise AIServiceException(f"OpenAI completion request failed: {str(e)}")

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        max_retries: int = 2,
    ) -> T:
        schema_json = json.dumps(response_model.model_json_schema())
        enforced_system = (
            (system_prompt or "You are an expert AI interview system.")
            + f"\nYou MUST reply ONLY with a valid JSON object matching this schema:\n{schema_json}"
        )

        for attempt in range(max_retries + 1):
            try:
                resp = await self.generate(
                    prompt=prompt,
                    system_prompt=enforced_system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                clean_json = resp.content.strip()
                if clean_json.startswith("```json"):
                    clean_json = clean_json[7:]
                if clean_json.endswith("```"):
                    clean_json = clean_json[:-3]
                clean_json = clean_json.strip()

                parsed = json.loads(clean_json)
                return response_model.model_validate(parsed)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Structured output validation failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    raise AIServiceException(f"Failed to obtain valid structured output after {max_retries + 1} attempts: {str(e)}")
                # Exponential backoff
                await asyncio.sleep(0.5 * (2 ** attempt))
            except Exception as e:
                raise AIServiceException(f"LLM Provider communication error: {str(e)}")

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> AsyncGenerator[str, None]:
        # Basic streaming fallback
        res = await self.generate(prompt=prompt, system_prompt=system_prompt, temperature=temperature)
        yield res.content


def get_llm_provider() -> LLMProvider:
    """Factory to instantiate LLM Provider based on application settings."""
    is_groq = settings.LLM_PROVIDER == "groq" or (bool(settings.LLM_API_KEY) and settings.LLM_API_KEY.startswith("gsk_"))
    if (settings.LLM_PROVIDER in ("openai", "groq") or is_groq) and settings.LLM_API_KEY:
        base_url = getattr(settings, "LLM_BASE_URL", None)
        if not base_url:
            base_url = "https://api.groq.com/openai/v1" if is_groq else "https://api.openai.com/v1"
        model_name = settings.LLM_MODEL
        if is_groq and (model_name == "gpt-4o" or model_name == "mock-gpt-4o" or model_name == "llama-3.3-70b-versatile"):
            model_name = "openai/gpt-oss-120b"
        return OpenAILLMProvider(api_key=settings.LLM_API_KEY, model_name=model_name, base_url=base_url)
    return MockLLMProvider(model_name=settings.LLM_MODEL)
