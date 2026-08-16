#!/usr/bin/env python3
"""Application configuration loaded from environment variables.

Secrets and connection strings come from the environment (see .env.example).
Never hardcode credentials in this repository.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Cyber Arena"
    debug: bool = False

    # The server binds this origin-filtered URL for the WebSocket + REST API.
    host: str = "0.0.0.0"
    port: int = 8000

    # Comma-separated list of allowed CORS origins for the browser UI.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # MongoDB connection string. Leave empty to run with in-memory persistence
    # (useful for local dev without a database installed).
    mongodb_url: str = ""
    mongodb_db: str = "cyber_arena"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def mongo_enabled(self) -> bool:
        return bool(self.mongodb_url.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
