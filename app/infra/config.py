from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application configuration loaded from environment variables and .env files."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="APP_LOG_LEVEL")
    user_id: int = Field(default=1, validation_alias="APP_USER_ID")

    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, validation_alias="GROQ_API_KEY")
    ollama_endpoint: Optional[str] = Field(default=None, validation_alias="OLLAMA_ENDPOINT")

    alpha_vantage_api_key: Optional[str] = Field(
        default=None, validation_alias="ALPHA_VANTAGE_API_KEY"
    )
    serpapi_key: Optional[str] = Field(default=None, validation_alias="SERPAPI_KEY")
    bing_api_key: Optional[str] = Field(default=None, validation_alias="BING_API_KEY")

    planner_llm_model: str = Field(default="gpt-4o-mini", validation_alias="PLANNER_LLM_MODEL")
    planner_allow_unlisted_sources: bool = Field(
        default=False, validation_alias="PLANNER_ALLOW_UNLISTED_SOURCES"
    )

    supabase_url: Optional[str] = Field(default=None, validation_alias="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, validation_alias="SUPABASE_SERVICE_ROLE_KEY")

    browser_use_endpoint: Optional[str] = Field(
        default=None, validation_alias="BROWSER_USE_ENDPOINT"
    )
    browser_use_timeout_seconds: int = Field(default=45)

    twitter_username: Optional[str] = Field(default=None, validation_alias="TWITTER_USERNAME")
    twitter_password: Optional[str] = Field(default=None, validation_alias="TWITTER_PASSWORD")

    # n8n Integration (replaces browser-use for Twitter)
    n8n_api_key: Optional[str] = Field(default=None, validation_alias="N8N_API_KEY")
    n8n_base_url: Optional[str] = Field(default=None, validation_alias="N8N_BASE_URL")
    n8n_twitter_workflow_id: Optional[str] = Field(default=None, validation_alias="N8N_TWITTER_WORKFLOW_ID")
    n8n_timeout_seconds: int = Field(default=300, validation_alias="N8N_TIMEOUT_SECONDS")

    planner_timeout_minutes: int = Field(default=8)
    planner_max_documents: int = Field(default=60)
    planner_include_social: bool = Field(default=True)
    planner_include_filings: bool = Field(default=True)
    planner_avoid_paywalls: bool = Field(default=True)
    planner_region_hint: str = Field(default="US")
    planner_language: str = Field(default="en")

    collector_page_timeout_seconds: int = Field(default=30)
    collector_retry_attempts: int = Field(default=2)

    llm_batch_size: int = Field(default=10)
    llm_max_tokens_per_doc: int = Field(default=1000)

    fear_greed_history: int = Field(default=5)

    # Email configuration
    smtp_host: Optional[str] = Field(default="smtp.gmail.com", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, validation_alias="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, validation_alias="SMTP_PASSWORD")
    sender_email: Optional[str] = Field(default=None, validation_alias="SENDER_EMAIL")
    recipient_emails: Optional[str] = Field(default=None, validation_alias="RECIPIENT_EMAILS")  # Comma-separated

    @property
    def manus_headers(self) -> Dict[str, str]:
        if not self.manus_api_key:
            return {}
        return {"Authorization": f"Bearer {self.manus_api_key}"}

    @property
    def supabase_credentials(self) -> Optional[Dict[str, str]]:
        if not self.supabase_url or not self.supabase_key:
            return None
        return {"url": self.supabase_url, "key": self.supabase_key}

    @property
    def llm_credentials(self) -> Dict[str, Optional[str]]:
        return {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "groq": self.groq_api_key,
            "ollama": self.ollama_endpoint,
        }

    def planner_payload_defaults(self) -> Dict[str, Any]:
        return {
            "window_hours": 6,
            "max_documents": self.planner_max_documents,
            "include_social": self.planner_include_social,
            "include_filings": self.planner_include_filings,
            "avoid_paywalls": self.planner_avoid_paywalls,
            "region_hint": self.planner_region_hint,
            "lang": self.planner_language,
            "budget": {
                "max_runtime_minutes": self.planner_timeout_minutes,
                "max_documents": self.planner_max_documents,
            },
            "llm_model": self.planner_llm_model,
            "allow_unlisted_sources": self.planner_allow_unlisted_sources,
        }


@lru_cache
def get_settings() -> AppSettings:
    load_dotenv()
    return AppSettings()


__all__ = ["AppSettings", "get_settings"]
