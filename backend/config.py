"""
config.py
Configuración centralizada de la aplicación.
Lee variables desde el archivo .env usando pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.
    Todas las variables se leen desde el archivo .env en la raíz del proyecto.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # ── CORS ──────────────────────────────────────────────────────────────────
    # En el .env: CORS_ORIGINS=http://localhost:3000,http://localhost:5173
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Google Drive ──────────────────────────────────────────────────────────
    GOOGLE_DRIVE_FOLDER_ID: str = ""
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account.json"

    # ── Propiedad calculada ───────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna CORS_ORIGINS como lista de strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna el singleton de Settings.
    El decorador lru_cache garantiza que solo se instancia una vez.
    """
    return Settings()  # type: ignore[call-arg]


# Objeto singleton listo para importar directamente
settings: Settings = get_settings()
