"""
Konfiguracja aplikacji - zmienne środowiskowe
"""
import os
from typing import List, ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ustawienia aplikacji załadowane z .env"""

    # App
    app_name: str = "TamteKlipy API"
    environment: str = "development"

    # Awards
    award_icons_path: str = "/mnt/tamteklipy/award_icons"

    # Database
    database_url: str = "sqlite:///./tamteklipy.db"

    # JWT Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Storage paths
    storage_path: str = "/mnt/tamteklipy"
    clips_path: str = "/mnt/tamteklipy/clips"
    screenshots_path: str = "/mnt/tamteklipy/screenshots"
    thumbnails_path: str = "/mnt/tamteklipy/thumbnails"
    metadata_path: str = "/mnt/tamteklipy/metadata"

    # File upload limits
    max_video_size_mb: int = 500
    max_image_size_mb: int = 10

    # CORS
    allowed_origins: str = (
        "http://localhost:5173,http://localhost:3000,"
        "http://localhost:8000,https://localhost:8001"
    )

    # Email (opcjonalnie)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # To jest zmienna klasowa (nie pole Pydantic)
    _env: ClassVar[str] = os.getenv("ENVIRONMENT", "development")
    _env_file: ClassVar[str] = f".env.{_env}"

    model_config = SettingsConfigDict(
        env_file=_env_file,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Własne property ---
    @property
    def max_video_size_bytes(self) -> int:
        return self.max_video_size_mb * 1024 * 1024

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    @property
    def origins_list(self) -> List[str]:
        """Zwraca listę dozwolonych origins dla CORS"""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


# Singleton - jedna instancja dla całej aplikacji
settings = Settings()
