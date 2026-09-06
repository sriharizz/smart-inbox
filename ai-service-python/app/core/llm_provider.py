import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel

from app.core.config import settings
from app.core.gemini_client import gemini_client

logger = logging.getLogger("smartinbox.provider")
T = TypeVar("T", bound=BaseModel)

class LLMProvider(ABC):
    """
    Abstract interface for Large Language Model and Multimodal reasoning providers.
    Decouples the Smart Inbox extraction and triage pipeline from specific vendor SDKs.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini', 'groq', 'vertex')."""
        pass

    @abstractmethod
    def generate_content(
        self,
        contents: Any,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """Generate unstructured or raw text content."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        contents: Any,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> T:
        """Generate structured output validated against a Pydantic model schema."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if provider API key and client connectivity are healthy."""
        pass

class GeminiProvider(LLMProvider):
    """
    Concrete Google Gemini provider implementation.
    Delegates to GeminiClient with exponential retries and primary/fallback model support.
    """

    def __init__(self, client=None):
        self._client = client or gemini_client

    @property
    def provider_name(self) -> str:
        return "gemini"

    def generate_content(
        self,
        contents: Any,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        return self._client.generate_content(
            contents=contents,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature
        )

    def generate_structured(
        self,
        contents: Any,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> T:
        raw_text = self._client.generate_content(
            contents=contents,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature
        )
        clean_json = raw_text.strip()
        if clean_json.startswith("```"):
            lines = clean_json.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_json = "\n".join(lines).strip()
        
        data = json.loads(clean_json)
        return response_schema.model_validate(data)

    def is_healthy(self) -> bool:
        return bool(self._client and getattr(self._client, "_client", None))

def get_llm_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """Factory function returning the active LLM provider."""
    ptype = (provider_type or "gemini").lower()
    if ptype == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unsupported LLM provider: {provider_type}. Expected 'gemini'.")
