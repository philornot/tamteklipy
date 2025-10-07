"""
Konfiguracja aplikacji - zmienne środowiskowe
"""
import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# Pobierz environment PRZED utworzeniem klasy
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ENV_FILE = f".env.{ENVIRONMENT}"


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

    # CORS - teraz Pydantic będzie to ładować z .env.production
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Email (opcjonalnie)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    redis_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,  # <-- UŻYWAJ ZMIENNEJ GLOBALNEJ, NIE ClassVar
        env_file_encoding="utf-8",
        case_sensitive=False,  # <-- ALLOWED_ORIGINS → allowed_origins
        extra="ignore"  # Ignoruj nieznane zmienne z .env
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
