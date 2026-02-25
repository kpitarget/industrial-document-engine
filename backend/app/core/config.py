from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Work Sheet Matcher API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./mvp.db"
    local_storage_path: str = "./storage"
    max_upload_size_mb: int = 10

    # TODO: Use these in the real SharePoint Graph uploader implementation.
    sharepoint_tenant_id: Optional[str] = None
    sharepoint_client_id: Optional[str] = None
    sharepoint_client_secret: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
