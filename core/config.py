import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_OWNER_GROUP_ID = os.getenv("LINE_OWNER_GROUP_ID", "")
RESERVATION_TRIGGER = "予約"  # LINE RICH MENU BUTTON TRIGGER


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    gemini_api_key: str
    gemini_model: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float


def get_llm_settings() -> LLMSettings:
    timeout_raw = os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")
    try:
        timeout_seconds = float(timeout_raw)
    except ValueError as exc:
        raise ValueError("OLLAMA_TIMEOUT_SECONDS must be a number") from exc

    return LLMSettings(
        provider=os.getenv("LLM_PROVIDER", "gemini").strip().lower(),
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma3:4b").strip(),
        ollama_timeout_seconds=timeout_seconds,
    )
