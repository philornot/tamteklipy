"""
Router dla zarządzania plikami — upload, download, listowanie klipów i screenshotów
"""
import logging
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import FileUploadError, ValidationError
from app.models.clip import Clip, ClipType
from app.models.user import User
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

router = APIRouter()
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

# Maksymalne rozmiary plików (w bajtach)
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def validate_file_type(filename: str, content_type: str) -> tuple[ClipType, str]:
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

    # Określ typ klipa
    if content_type in ALLOWED_VIDEO_TYPES:
        clip_type = ClipType.VIDEO
    else:
        clip_type = ClipType.SCREENSHOT

    extension = ALLOWED_MIME_TYPES[content_type]

    return clip_type, extension


def validate_file_size(file_size: int, clip_type: ClipType):
    """Waliduje rozmiar pliku"""
    max_size = MAX_VIDEO_SIZE if clip_type == ClipType.VIDEO else MAX_IMAGE_SIZE

    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        actual_size_mb = file_size / (1024 * 1024)
        raise ValidationError(
            message=f"Plik jest za duży: {actual_size_mb:.1f}MB (max: {max_size_mb:.0f}MB)",
            field="file",
            details={
                "max_size_bytes": max_size,
                "actual_size_bytes": file_size
            }
        )


def generate_unique_filename(original_filename: str, extension: str) -> str:
    """
    Generuje unikalną nazwę pliku używając UUID

    Returns:
        str: Unikalna nazwa pliku z rozszerzeniem
    """
    # Usuń niebezpieczne znaki z oryginalnej nazwy
    safe_name = "".join(c for c in original_filename if c.isalnum() or c in "._- ")
    safe_name = safe_name[:50]  # Ogranicz długość

    # Wygeneruj UUID
    unique_id = str(uuid.uuid4())

    # Nazwa: UUID_oryginalna_nazwa.ext
    return f"{unique_id}_{safe_name}{extension}"


@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Upload pliku (klip lub screenshot)

    POST /api/files/upload
    Body: multipart/form-data z plikiem
    Header: Authorization: Bearer <token>

    Returns:
        Informacje o uploadowanym pliku
    """
    logger.info(f"Upload request from user {current_user.username}: {file.filename} ({file.content_type})")

    try:
        # 1. Waliduj typ pliku
        clip_type, extension = validate_file_type(file.filename, file.content_type)

        # 2. Przeczytaj plik do pamięci (żeby sprawdzić rozmiar)
        file_content = await file.read()
        file_size = len(file_content)

        # 3. Waliduj rozmiar
        validate_file_size(file_size, clip_type)

        # 4. Wygeneruj unikalną nazwę
        unique_filename = generate_unique_filename(file.filename, extension)

        # 5. Określ ścieżkę zapisu
        if clip_type == ClipType.VIDEO:
            storage_dir = Path(settings.clips_path)
        else:
            storage_dir = Path(settings.screenshots_path)

        # Dla developmentu (Windows) użyj lokalnego katalogu
        if settings.environment == "development":
            storage_dir = Path("uploads") / ("clips" if clip_type == ClipType.VIDEO else "screenshots")

        # Utwórz katalog jeśli nie istnieje
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Pełna ścieżka do pliku
        file_path = storage_dir / unique_filename

        # 6. Zapisz plik na dysku
        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"File saved: {file_path}")

        # 7. Zapisz do bazy danych
        new_clip = Clip(
            filename=file.filename,  # Oryginalna nazwa
            file_path=str(file_path),  # Pełna ścieżka
            thumbnail_path=None,  # TODO: Generowanie thumbnails
            clip_type=clip_type,
            file_size=file_size,
            duration=None,  # TODO: Ekstrakcja metadanych video
            width=None,
            height=None,
            uploader_id=current_user.id
        )

        db.add(new_clip)
        db.commit()
        db.refresh(new_clip)

        logger.info(f"Clip created in database: ID={new_clip.id}")

        return {
            "message": "Plik został przesłany pomyślnie",
            "clip_id": new_clip.id,
            "filename": file.filename,
            "unique_filename": unique_filename,
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "clip_type": clip_type.value,
            "uploader": current_user.username
        }

    except (ValidationError, FileUploadError):
        # Re-raise nasze własne wyjątki
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise FileUploadError(
            message="Błąd podczas uploadu pliku",
            filename=file.filename,
            reason=str(e)
        )


@router.get("/clips")
async def list_clips(
        skip: int = 0,
        limit: int = 50,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Listowanie klipów z paginacją
    GET /api/files/clips?skip=0&limit=50
    """
    clips = db.query(Clip).filter(
        Clip.is_deleted == False
    ).order_by(
        Clip.created_at.desc()
    ).offset(skip).limit(limit).all()

    total = db.query(Clip).filter(Clip.is_deleted == False).count()

    return {
        "clips": [
            {
                "id": clip.id,
                "filename": clip.filename,
                "clip_type": clip.clip_type.value,
                "file_size_mb": clip.file_size_mb,
                "uploader": clip.uploader.username,
                "created_at": clip.created_at.isoformat(),
                "award_count": clip.award_count
            }
            for clip in clips
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }
