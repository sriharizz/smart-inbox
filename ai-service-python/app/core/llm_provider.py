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

class GroqProvider(LLMProvider):
    """
    Concrete Groq provider implementation for Step 5 Semantic Evidence Verification (LLM #2).
    Uses Groq's high-speed API with OpenAI-compatible chat completions endpoint and JSON object mode.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        timeout: Optional[float] = None,
        client: Optional[Any] = None
    ):
        self._api_key = api_key or settings.GROQ_API_KEY
        self._base_url = (base_url or settings.GROQ_API_URL).rstrip("/")
        self._default_model = default_model or settings.GROQ_VERIFIER_MODEL
        self._timeout = timeout or float(settings.REQUEST_TIMEOUT_SECONDS)
        self._client = client
        self._rate_limited_until: float = 0.0

    @property
    def provider_name(self) -> str:
        return "groq"

    def is_healthy(self) -> bool:
        if not self._api_key:
            return False
        if self._rate_limited_until > time.time():
            return False
        return True

    def generate_content(
        self,
        contents: Any,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        import httpx
        if not self._api_key:
            raise RuntimeError("GROQ_API_KEY is not configured. Verify .env or environment variables.")
        if self._rate_limited_until > time.time():
            raise RuntimeError("Groq provider is currently rate-limited (HTTP 429). Circuit breaker open.")

        target_model = model or self._default_model
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": str(contents)})

        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self._base_url}/chat/completions"

        if self._client is not None:
            resp = self._client.post(url, headers=headers, json=payload)
        else:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(url, headers=headers, json=payload)

        if resp.status_code != 200:
            if resp.status_code == 429:
                self._rate_limited_until = time.time() + 60.0
            err_text = resp.text[:200]
            logger.warning(f"Groq API returned HTTP {resp.status_code}: {err_text}")
            resp.raise_for_status()

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"Groq API returned empty choices list: {data}")

        return choices[0]["message"]["content"] or ""

    def generate_structured(
        self,
        contents: Any,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> T:
        raw_text = self.generate_content(
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

        parsed = json.loads(clean_json)
        return response_schema.model_validate(parsed)

    def is_healthy(self) -> bool:
        return bool(self._api_key)

def get_llm_provider(provider_type: Optional[str] = None) -> LLMProvider:
    """Factory function returning the active LLM provider."""
    ptype = (provider_type or "gemini").lower()
    if ptype == "gemini":
        return GeminiProvider()
    elif ptype == "groq":
        return GroqProvider()
    raise ValueError(f"Unsupported LLM provider: {provider_type}. Expected 'gemini' or 'groq'.")
