import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartInbox AI Microservice"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Google GenAI Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Primary model is gemini-3.5-flash with alias fallback to gemini-3.5-flash-lite
    MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-3.5-flash")
    FALLBACK_MODEL_NAME: str = "gemini-3.5-flash-lite"
    EMBEDDING_MODEL_NAME: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    ENABLE_SEMANTIC_RETRIEVAL: bool = True
    ENABLE_SEMANTIC_VERIFICATION: bool = True

    # Groq Settings (Step 5 Semantic Evidence Verification - LLM #2)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_VERIFIER_MODEL: str = os.getenv("GROQ_VERIFIER_MODEL", "openai/gpt-oss-20b")
    GROQ_API_URL: str = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")
    VERIFIER_BATCH_MAX_ITEMS: int = int(os.getenv("VERIFIER_BATCH_MAX_ITEMS", "15"))
    VERIFIER_BATCH_MAX_CHARS: int = int(os.getenv("VERIFIER_BATCH_MAX_CHARS", "12000"))
    VERIFIER_TOP_K_CANDIDATES_PER_FACT: int = int(os.getenv("VERIFIER_TOP_K_CANDIDATES_PER_FACT", "2"))
    
    # Caching & Resilience (Disabled - 100% Live Gemini AI)
    USE_LOCAL_CACHE: bool = False
    CACHE_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data" / "cache"
    BENCHMARK_FILE: Path = Path(__file__).resolve().parent.parent.parent.parent / "test-data" / "ground_truth" / "benchmark.json"
    
    # Rate Limiting & Timeouts
    RATE_LIMIT_RPM: int = 15
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()
