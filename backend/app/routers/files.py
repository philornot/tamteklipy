"""
Router dla zarządzania plikami — upload, download, listowanie klipów i screenshotów
"""
import hashlib
import logging
import shutil
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import FileUploadError, ValidationError
from app.models.clip import Clip, ClipType
from app.models.user import User
from app.services.thumbnail_service import generate_thumbnail, extract_video_metadata
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
MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500 MB
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
    max_size = settings.max_video_size_bytes if clip_type == ClipType.VIDEO else settings.max_image_size_bytes

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
    """Upload pliku z automatycznym generowaniem thumbnail dla video"""

    logger.info(f"Upload request from user {current_user.username}: {file.filename} ({file.content_type})")

    try:
        # Walidacja i zapis pliku (jak wcześniej)
        clip_type, extension = validate_file_type(file.filename, file.content_type)
        file_content = await file.read()
        file_size = len(file_content)
        validate_file_size(file_size, clip_type)
        unique_filename = generate_unique_filename(file.filename, extension)

        if clip_type == ClipType.VIDEO:
            storage_dir = Path(settings.clips_path)
        else:
            storage_dir = Path(settings.screenshots_path)

        if settings.environment == "development":
            storage_dir = Path("uploads") / ("clips" if clip_type == ClipType.VIDEO else "screenshots")

        storage_dir.mkdir(parents=True, exist_ok=True)
        file_path = storage_dir / unique_filename

        # Sprawdź wolne miejsce na dysku
        check_disk_space(storage_dir, file_size)

        with open(file_path, "wb") as f:
            f.write(file_content)

        logger.info(f"File saved: {file_path}")

        # 7. Generuj thumbnail dla video
        thumbnail_path = None
        video_metadata = None

        if clip_type == ClipType.VIDEO:
            try:
                # Wyciągnij metadane
                video_metadata = extract_video_metadata(str(file_path))

                # Ścieżka do thumbnail
                thumbnails_dir = Path(settings.thumbnails_path)
                if settings.environment == "development":
                    thumbnails_dir = Path("uploads/thumbnails")

                thumbnails_dir.mkdir(parents=True, exist_ok=True)

                thumbnail_filename = f"{Path(unique_filename).stem}.jpg"
                thumbnail_full_path = thumbnails_dir / thumbnail_filename

                # Generuj thumbnail
                generate_thumbnail(
                    video_path=str(file_path),
                    output_path=str(thumbnail_full_path),
                    timestamp="00:00:01",
                    width=320,
                    quality=2
                )

                thumbnail_path = str(thumbnail_full_path)
                logger.info(f"Thumbnail generated: {thumbnail_path}")

            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {e}")
                # Nie przerywamy uploadu jeśli thumbnail się nie uda

        # 8. Zapisz do bazy danych z metadanymi
        new_clip = Clip(
            filename=file.filename,
            file_path=str(file_path),
            thumbnail_path=thumbnail_path,
            clip_type=clip_type,
            file_size=file_size,
            duration=video_metadata.get("duration") if video_metadata else None,
            width=video_metadata.get("width") if video_metadata else None,
            height=video_metadata.get("height") if video_metadata else None,
            uploader_id=current_user.id
        )

        db.add(new_clip)
        db.commit()
        db.refresh(new_clip)

        logger.info(f"Clip created in database: ID={new_clip.id}")

        response_data = {
            "message": "Plik został przesłany pomyślnie",
            "clip_id": new_clip.id,
            "filename": file.filename,
            "unique_filename": unique_filename,
            "file_size": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "clip_type": clip_type.value,
            "uploader": current_user.username
        }

        if thumbnail_path:
            response_data["thumbnail_generated"] = True
            response_data["thumbnail_path"] = thumbnail_path

        if video_metadata:
            response_data["duration"] = video_metadata.get("duration")
            response_data["width"] = video_metadata.get("width")
            response_data["height"] = video_metadata.get("height")

        return response_data

    except (ValidationError, FileUploadError):
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


def check_disk_space(storage_path: Path, required_bytes: int) -> bool:
    """
    Sprawdza czy jest wystarczająco miejsca na dysku

    Args:
        storage_path: Ścieżka do katalogu storage
        required_bytes: Wymagana ilość bajtów

    Returns:
        bool: True jeśli jest miejsce, False jeśli nie ma

    Raises:
        StorageError: Jeśli nie ma wystarczająco miejsca
    """
    try:
        stat = shutil.disk_usage(storage_path)
        free_space = stat.free

        # Zostawmy przynajmniej 1GB wolnego miejsca jako bufor
        SAFETY_BUFFER = 1 * 1024 * 1024 * 1024  # 1 GB

        if free_space - required_bytes < SAFETY_BUFFER:
            free_mb = free_space / (1024 * 1024)
            required_mb = required_bytes / (1024 * 1024)

            from app.core.exceptions import StorageError
            raise StorageError(
                message=f"Brak miejsca na dysku: dostępne {free_mb:.0f}MB, wymagane {required_mb:.0f}MB",
                path=str(storage_path)
            )

        return True

    except Exception as e:
        logger.error(f"Failed to check disk space: {e}")
        # Nie przerywamy uploadu, jeśli nie możemy sprawdzić miejsca
        return True


def calculate_file_hash(file_content: bytes) -> str:
    """
    Oblicza SHA256 hash pliku

    Args:
        file_content: Zawartość pliku w bajtach

    Returns:
        str: SHA256 hash jako hex string
    """
    return hashlib.sha256(file_content).hexdigest()


def check_duplicate(db: Session, file_hash: str, user_id: int) -> Optional[Clip]:
    """
    Sprawdza czy użytkownik już uploadował ten sam plik

    Args:
        db: Sesja bazy danych
        file_hash: SHA256 hash pliku
        user_id: ID użytkownika

    Returns:
        Clip: Istniejący klip jeśli duplikat, None jeśli nie
    """
    # Dodaj pole file_hash do modelu Clip (wymaga migracji)
    # Na razie zwracamy None
    return None
