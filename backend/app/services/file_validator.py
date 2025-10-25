"""
Walidacja plików - typy, rozmiary, nazwy
"""
import shutil
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import ValidationError, StorageError
from app.models.clip import ClipType

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


def validate_file_type(content_type: str) -> tuple[ClipType, str]:
    """
    Waliduje typ pliku na podstawie MIME type

    Returns:
        tuple: (ClipType, extension)
    """
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            message=f"Niedozwolony typ pliku: {content_type}",
            field="file",
            details={
                "allowed_types": list(ALLOWED_MIME_TYPES.keys()),
                "received_type": content_type
            }
        )

    if content_type in ALLOWED_VIDEO_TYPES:
        clip_type = ClipType.VIDEO
    else:
        clip_type = ClipType.SCREENSHOT

    extension = ALLOWED_MIME_TYPES[content_type]

    return clip_type, extension


def validate_file_size(file_size: int, clip_type: ClipType):
    """Waliduje rozmiar pliku"""
    max_size = (settings.max_video_size_bytes if clip_type == ClipType.VIDEO
                else settings.max_image_size_bytes)

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


def generate_unique_filename(original_filename: str, extension: str) -> str:
    """
    Generuje unikalną nazwę pliku używając UUID

    Returns:
        str: Unikalna nazwa pliku z rozszerzeniem
    """
    # Usuń rozszerzenie z original_filename jeśli istnieje
    name_without_ext = Path(original_filename).stem

    safe_name = "".join(c for c in name_without_ext if c.isalnum() or c in "._- ")
    safe_name = safe_name[:50]
    unique_id = str(uuid.uuid4())

    # Upewnij się że extension zaczyna się od kropki
    if not extension.startswith('.'):
        extension = f'.{extension}'

    return f"{unique_id}_{safe_name}{extension}"


def check_disk_space(storage_path: Path, required_bytes: int) -> bool:
    """
    Sprawdza czy jest wystarczająco miejsca na dysku

    Raises:
        StorageError: Jeśli nie ma wystarczająco miejsca
    """
    try:
        if storage_path.exists():
            target = storage_path
        else:
            anchor = storage_path.anchor or Path.cwd().anchor
            target = Path(anchor)

        stat = shutil.disk_usage(target)
        free_space = stat.free

        SAFETY_BUFFER = 1 * 1024 * 1024 * 1024  # 1 GB

        if free_space - required_bytes < SAFETY_BUFFER:
            free_mb = free_space / (1024 * 1024)
            required_mb = required_bytes / (1024 * 1024)

            raise StorageError(
                message=f"Brak miejsca na dysku: dostępne {free_mb:.0f}MB, wymagane {required_mb:.0f}MB",
                path=str(target)
            )
    except PermissionError:
        raise StorageError(
            message="Brak uprawnień do sprawdzenia miejsca na dysku",
            path=str(storage_path)
        )

    except OSError:
        raise StorageError(
            message="Błąd OSError przy sprawdzaniu miejsca na dysku",
            path=str(storage_path)
        )

    except Exception:
        raise StorageError(
            message="Nieoczekiwany błąd przy sprawdzaniu miejsca na dysku",
            path=str(storage_path)
        )


def guess_content_type(filename: str) -> str:
    """Zgadnij content type z rozszerzenia"""
    ext = Path(filename).suffix.lower()

    mapping = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }

    return mapping.get(ext, "video/mp4")
