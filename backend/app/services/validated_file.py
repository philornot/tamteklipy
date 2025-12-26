"""
Enkapsulacja walidowanego pliku uploaded przez użytkownika.
Po konstrukcji obiekt gwarantuje że plik jest poprawny.
"""
import logging
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.models.clip import ClipType
from fastapi import UploadFile

logger = logging.getLogger(__name__)

# Dozwolone typy plików
ALLOWED_VIDEO_TYPES = {
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}

ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}

ALLOWED_MIME_TYPES = {**ALLOWED_VIDEO_TYPES, **ALLOWED_IMAGE_TYPES}


class ValidatedFile:
    """
    Enkapsulacja walidowanego pliku z uploaded content.
    Po konstrukcji obiekt gwarantuje że plik jest poprawny i gotowy do zapisu.
    """

    def __init__(
            self,
            file_content: bytes,
            filename: str,
            content_type: str,
            max_size_bytes: Optional[int] = None
    ):
        """
        Konstruktor waliduje plik i rzuca ValidationError jeśli coś jest nie tak.

        Args:
            file_content: Zawartość pliku (bytes)
            filename: Oryginalna nazwa pliku
            content_type: MIME type pliku
            max_size_bytes: Maksymalny rozmiar w bajtach (domyślnie z settings)

        Raises:
            ValidationError: Jeśli plik nie przechodzi walidacji
        """
        self.original_filename = filename
        self.content_type = content_type
        self.content = file_content

        # 1. Walidacja typu pliku
        self._validate_type()

        # 2. Określ clip_type i extension
        self.clip_type = self._determine_clip_type()
        self.extension = self._get_extension()

        # 3. Walidacja rozmiaru
        max_size = max_size_bytes or self._get_default_max_size()
        self._validate_size(max_size)

        # 4. Wygeneruj unikalną nazwę
        self.unique_filename = self._generate_unique_filename()

        logger.info(
            f"File validated: {self.original_filename} "
            f"({self.size_mb:.2f}MB, {self.clip_type.value})"
        )

    @classmethod
    async def from_upload_file(
            cls,
            uploaded_file: UploadFile,
            max_size_bytes: Optional[int] = None
    ):
        """
        Factory method - tworzy ValidatedFile z FastAPI UploadFile.

        Args:
            uploaded_file: Plik z FastAPI UploadFile
            max_size_bytes: Maksymalny rozmiar w bajtach

        Returns:
            ValidatedFile: Zwalidowany plik

        Raises:
            ValidationError: Jeśli plik nie przechodzi walidacji
        """
        content = await uploaded_file.read()

        return cls(
            file_content=content,
            filename=uploaded_file.filename,
            content_type=uploaded_file.content_type,
            max_size_bytes=max_size_bytes
        )

    def _validate_type(self):
        """Sprawdza czy content_type jest dozwolony"""
        if self.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(
                message=f"Niedozwolony typ pliku: {self.content_type}",
                field="file",
                details={
                    "allowed_types": list(ALLOWED_MIME_TYPES.keys()),
                    "received_type": self.content_type
                }
            )

    def _determine_clip_type(self) -> ClipType:
        """Określa czy to video czy screenshot"""
        if self.content_type in ALLOWED_VIDEO_TYPES:
            return ClipType.VIDEO
        else:
            return ClipType.SCREENSHOT

    def _get_extension(self) -> str:
        """Zwraca rozszerzenie pliku dla danego content_type"""
        return ALLOWED_MIME_TYPES[self.content_type]

    def _get_default_max_size(self) -> int:
        """Zwraca domyślny max size dla typu pliku"""
        if self.clip_type == ClipType.VIDEO:
            return settings.max_video_size_bytes
        else:
            return settings.max_image_size_bytes

    def _validate_size(self, max_size: int):
        """Sprawdza czy rozmiar pliku nie przekracza limitu"""
        file_size = len(self.content)

        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            actual_size_mb = file_size / (1024 * 1024)

            raise ValidationError(
                message=f"Plik jest za duży: {actual_size_mb:.1f}MB (max: {max_size_mb:.0f}MB)",
                field="file",
                details={
                    "max_size_bytes": max_size,
                    "actual_size_bytes": file_size,
                    "max_size_mb": max_size_mb,
                    "actual_size_mb": actual_size_mb
                }
            )

    def _generate_unique_filename(self) -> str:
        """Generuje unikalną nazwę pliku używając UUID"""
        # Usuń rozszerzenie z original_filename
        name_without_ext = Path(self.original_filename).stem

        # Sanitize - zostaw tylko alfanumeryczne i wybrane znaki
        safe_name = "".join(
            c for c in name_without_ext
            if c.isalnum() or c in "._- "
        )
        safe_name = safe_name[:50]  # Obetnij długie nazwy

        # Dodaj UUID dla unikalności
        unique_id = str(uuid.uuid4())

        # Upewnij się że extension zaczyna się od kropki
        ext = self.extension if self.extension.startswith('.') else f'.{self.extension}'

        return f"{unique_id}_{safe_name}{ext}"

    @property
    def size_bytes(self) -> int:
        """Rozmiar w bajtach"""
        return len(self.content)

    @property
    def size_mb(self) -> float:
        """Rozmiar w megabajtach dla wyświetlania"""
        return self.size_bytes / (1024 * 1024)

    def calculate_sha256(self) -> str:
        """Oblicza SHA256 hash zawartości pliku"""
        import hashlib
        return hashlib.sha256(self.content).hexdigest()
