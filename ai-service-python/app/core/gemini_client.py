import time
import logging
from typing import List, Any, Optional
from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger("smartinbox.gemini")

class GeminiClient:
    _instance: Optional["GeminiClient"] = None
    _client: Optional[genai.Client] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiClient, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        try:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("Initialized Google GenAI client successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI client: {e}")
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.5, min=2, max=10),
        reraise=True
    )
    def generate_content(
        self,
        contents: Any,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate content using Gemini Flash with automatic exponential retry and model fallback.
        """
        if not self._client:
            self._init_client()
            if not self._client:
                raise RuntimeError("Gemini Client not initialized. Verify GEMINI_API_KEY.")

        target_model = model or settings.MODEL_NAME
        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction
        if temperature is not None:
            config["temperature"] = temperature

        try:
            response = self._client.models.generate_content(
                model=target_model,
                contents=contents,
                config=config if config else None
            )
            return response.text or ""
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Error calling {target_model}: {err_msg}. Attempting fallback...")
            # If primary model fails, try fallback model
            if target_model != settings.FALLBACK_MODEL_NAME:
                response = self._client.models.generate_content(
                    model=settings.FALLBACK_MODEL_NAME,
                    contents=contents,
                    config=config if config else None
                )
                return response.text or ""
            raise e

gemini_client = GeminiClient()
