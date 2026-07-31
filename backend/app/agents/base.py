"""Base agent class for all AI agents."""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    content: str
    agent_name: str
    confidence: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


class AIGenerationError(Exception):
    pass


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    name: str = "base"
    description: str = "Base agent"
    icon: str = "🤖"
    color: str = "#667eea"

    def __init__(self):
        self.openai = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_key,
            http_client=httpx.AsyncClient(timeout=60.0)
        )
        self.anthropic = AsyncAnthropic(
            api_key=settings.anthropic_key,
            http_client=httpx.AsyncClient(timeout=60.0)
        )
        genai.configure(api_key=settings.gemini_key)
        self.gemini = genai.GenerativeModel(settings.vision_model)

        self._failure_count = 0
        self._circuit_open = False
        self._circuit_timeout = 120
        self._last_failure = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
        reraise=True
    )
    async def _generate(
        self,
        system: str,
        user: str,
        model: Optional[str] = None,
        temp: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Generate text with circuit breaker and fallback."""
        if self._circuit_open:
            if self._last_failure and (asyncio.get_event_loop().time() - self._last_failure) < self._circuit_timeout:
                raise AIGenerationError("Circuit breaker is OPEN")
            self._circuit_open = False
            self._failure_count = 0

        model = model or settings.primary_model
        user = user[:8000]

        try:
            if "claude" in model:
                result = await self._call_claude(system, user, temp, max_tokens)
            elif "gemini" in model:
                result = await self._call_gemini(system, user, temp, max_tokens)
            else:
                result = await self._call_openrouter(system, user, model, temp, max_tokens)

            self._failure_count = 0
            return result

        except Exception as e:
            self._failure_count += 1
            self._last_failure = asyncio.get_event_loop().time()
            if self._failure_count >= 5:
                self._circuit_open = True

            # Fallback chain
            logger.error(f"Primary AI call failed for {self.name}: {e}")
            if "claude" not in model:
                return await self._call_claude(system, user, temp, max_tokens)
            elif "gemini" not in model:
                return await self._call_gemini(system, user, temp, max_tokens)
            raise AIGenerationError("All AI providers failed") from e

    async def _call_openrouter(self, system: str, user: str, model: str, temp: float, max_tokens: int) -> str:
        resp = await self.openai.chat.completions.create(
            model=model, temperature=temp, max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}]
        )
        return resp.choices[0].message.content or ""

    async def _call_claude(self, system: str, user: str, temp: float, max_tokens: int) -> str:
        resp = await self.anthropic.messages.create(
            model=settings.deep_model, max_tokens=max_tokens, temperature=temp,
            system=system, messages=[{"role": "user", "content": user}]
        )
        return resp.content[0].text

    async def _call_gemini(self, system: str, user: str, temp: float, max_tokens: int) -> str:
        response = await asyncio.to_thread(
            self.gemini.generate_content, f"{system}\n\n{user}",
            generation_config=genai.types.GenerationConfig(temperature=temp, max_output_tokens=max_tokens)
        )
        return response.text

    @abstractmethod
    async def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process user input and return response."""
        pass

    async def chat(self, message: str, history: Optional[List[Dict]] = None) -> AgentResponse:
        """Chat interface for the agent."""
        return await self.process(message, {"history": history or []})
