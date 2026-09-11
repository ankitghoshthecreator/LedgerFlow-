"""
LedgerFlow configuration — reads from environment / .env file.
All settings are validated at startup via pydantic-settings.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "LedgerFlow"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = "change-me-in-production"
    debug: bool = True

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./ledgerflow.db"

    # ── Event Bus ────────────────────────────────────────────────────────
    event_bus_backend: Literal["in_process", "kafka"] = "in_process"
    kafka_bootstrap_servers: str = "localhost:9092"

    # ── Cache ────────────────────────────────────────────────────────────
    cache_backend: Literal["memory", "redis"] = "memory"
    redis_url: str = "redis://localhost:6379/0"

    # ── Mock Service Behaviour ───────────────────────────────────────────
    credit_bureau_fail_rate: float = 0.1
    credit_bureau_min_latency_ms: int = 100
    credit_bureau_max_latency_ms: int = 800
    force_kyc_fail: bool = False

    # ── MCP Server ───────────────────────────────────────────────────────
    mcp_server_host: str = "0.0.0.0"
    mcp_server_port: int = 8001
    backend_api_url: str = "http://localhost:8000"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — safe to import anywhere."""
    return Settings()
