import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    openai_api_key: str
    openai_base_url: str
    default_chat_model: str

    ollama_base_url: str

    embedding_provider: str
    embedding_model: str
    embedding_base_url: str
    embedding_api_key: str

    tts_enabled: bool
    tts_base_url: str
    tts_api_key: str
    tts_model: str
    tts_voice: str
    tts_output_dir: str
    tts_format: str
    tts_speed: float
    tts_instructions: str
    tts_timeout: float
    tts_max_retries: int
    tts_headers: str

    chroma_dir: str
    max_context_tokens: int
    max_output_tokens: int
    memory_top_k: int
    history_max_messages: int
    temperature: float
    sleep_seconds: float
    admin_use_llm: bool
    verbose: bool
    log_level: str
    log_dir: str


def load_settings() -> Settings:
    load_dotenv()

    def _get_bool(key: str, default: str) -> bool:
        return os.getenv(key, default).lower() in {"1", "true", "yes", "on"}

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        default_chat_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "ollama"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "qwen:0.5b"),
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL", "http://localhost:11434"),
        embedding_api_key=os.getenv("EMBEDDING_API_KEY", ""),
        tts_enabled=_get_bool("TTS_ENABLED", "false"),
        tts_base_url=os.getenv("TTS_BASE_URL", "https://api.openai.com/v1"),
        tts_api_key=os.getenv("TTS_API_KEY", ""),
        tts_model=os.getenv("TTS_MODEL", "tts-1"),
        tts_voice=os.getenv("TTS_VOICE", "alloy"),
        tts_output_dir=os.getenv("TTS_OUTPUT_DIR", "./tts_out"),
        tts_format=os.getenv("TTS_FORMAT", "mp3"),
        tts_speed=float(os.getenv("TTS_SPEED", "1.0")),
        tts_instructions=os.getenv("TTS_INSTRUCTIONS", ""),
        tts_timeout=float(os.getenv("TTS_TIMEOUT", "30.0")),
        tts_max_retries=int(os.getenv("TTS_MAX_RETRIES", "3")),
        tts_headers=os.getenv("TTS_HEADERS", ""),
        chroma_dir=os.getenv("CHROMA_DIR", "./data/chroma"),
        max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "32000")),
        max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "512")),
        memory_top_k=int(os.getenv("MEMORY_TOP_K", "5")),
        history_max_messages=int(os.getenv("HISTORY_MAX_MESSAGES", "20")),
        temperature=float(os.getenv("TEMPERATURE", "0.9")),
        sleep_seconds=float(os.getenv("SLEEP_SECONDS", "2")),
        admin_use_llm=_get_bool("ADMIN_USE_LLM", "true"),
        verbose=_get_bool("VERBOSE", "false"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_dir=os.getenv("LOG_DIR", "./logs"),
    )
