"""Environment configuration, validated once at the application boundary."""

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """Explicit resource budgets; API secrets remain in the environment."""

    source_timeout: float = Field(default=20, gt=0, le=300)
    synthesis_timeout: float = Field(default=60, gt=0, le=600)
    http_timeout: float = Field(default=8, gt=0, le=120)
    attempts: int = Field(default=3, ge=1, le=5)
    backoff: float = Field(default=0.5, ge=0, le=30)
    concurrency: int = Field(default=3, ge=1, le=20)
    rate_interval: float = Field(default=1, ge=0, le=60)
    arxiv_interval: float = Field(default=3, ge=0, le=60)
    cache_ttl: float = Field(default=3600, ge=0)
    cache_dir: Path = Path(".cache/researcher")
    max_question_length: int = Field(default=2000, ge=10, le=10000)
    max_results: int = Field(default=3, ge=1, le=10)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    web_search_provider: Literal["tavily", "serper", "duckduckgo"] = "tavily"
    llm_provider: Literal["anthropic", "openai", "gemini"] = "anthropic"
    llm_model: str = ""
    web_fallbacks: str = ""
    web_provider_timeout: float = Field(default=6, gt=0, le=120)
    gemini_tpm: int = Field(default=60000, gt=0)
    openai_tpm: int = Field(default=60000, gt=0)
    anthropic_tpm: int = Field(default=60000, gt=0)

    @field_validator("web_fallbacks")
    @classmethod
    def valid_fallbacks(cls, value: str) -> str:
        """Reject unrecognised web adapters before doing any network work."""
        names = [n.strip() for n in value.split(",") if n.strip()]
        if any(n not in {"tavily", "serper", "duckduckgo"} for n in names):
            raise ValueError("Unknown fallback provider")
        return ",".join(dict.fromkeys(names))

    @classmethod
    def from_env(cls) -> "Settings":
        """Read .env without overriding values supplied by the shell."""
        load_dotenv()
        values = {}
        for name in cls.model_fields:
            key = (
                name.upper()
                if name in {"llm_provider", "llm_model", "web_search_provider"}
                else f"RESEARCH_{name.upper()}"
            )
            if key in os.environ:
                values[name] = os.environ[key]
        return cls.model_validate(values)

    def check_credentials(self, sources: list[str]) -> None:
        """Fail early with the missing variable name, never its value."""
        key = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "gemini": "GOOGLE_API_KEY"}[
            self.llm_provider
        ]
        if self.llm_provider == "gemini" and os.getenv("GEMINI_API_KEY"):
            key = "GEMINI_API_KEY"
        required = [key]
        if os.getenv("LLM_API_KEY"):
            required = []
        if "web" in sources and self.web_search_provider != "duckduckgo":
            required.append(f"{self.web_search_provider.upper()}_API_KEY")
        for variable in required:
            if not os.getenv(variable):
                raise ValueError(f"Set {variable} in .env for live mode, or use --offline.")
