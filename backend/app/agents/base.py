"""Base agent — shared LLM call pattern with retry + token tracking.

Each specialized agent inherits from BaseAgent and defines:
- name: agent identifier (used in token tracker breakdown)
- system_prompt: agent's role and output format spec
- run(): async method that processes a chunk and returns structured output
"""
import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.token_tracker import TokenTracker


class BaseAgent(ABC):
    """Abstract base for all specialized agents."""

    name: str = "base"
    system_prompt: str = ""

    def __init__(self, tracker: TokenTracker, client: AsyncOpenAI | None = None):
        self.tracker = tracker
        self.client = client or AsyncOpenAI(
            api_key=settings.mimo_api_key,
            base_url=settings.mimo_base_url,
            timeout=settings.agent_timeout,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=15),
        reraise=True,
    )
    async def reason(
        self,
        request_id: str,
        user: str,
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Make an LLM call, track tokens, return the assistant content."""
        sys_msg = system or self.system_prompt
        resp = await self.client.chat.completions.create(
            model=settings.mimo_model,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        usage = resp.usage
        if usage:
            self.tracker.record(
                request_id=request_id,
                agent=self.name,
                model=settings.mimo_model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
            )
        content = resp.choices[0].message.content or ""
        return content.strip()

    @abstractmethod
    async def handle(self, request_id: str, chunk_content: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process a chunk and return structured output. Must be overridden."""
        ...
