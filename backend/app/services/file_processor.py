"""
Przetwarzanie plików - zapis, thumbnail, metadata
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

from app.core.config import settings
from app.core.exceptions import StorageError, FileUploadError
from app.models.clip import Clip, ClipType
from app.services.thumbnail_service import (
    generate_thumbnail,
    generate_image_thumbnail,
    extract_video_metadata,
    extract_image_metadata
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_storage_directory(clip_type: ClipType) -> Path:
    """Zwraca katalog dla danego typu pliku"""
    if clip_type == ClipType.VIDEO:
        storage_dir = Path(settings.clips_path)
    else:
        storage_dir = Path(settings.screenshots_path)

    if settings.environment == "development":
        subdir = "clips" if clip_type == ClipType.VIDEO else "screenshots"
        storage_dir = (Path.cwd() / "uploads" / subdir).resolve()

    return storage_dir


async def save_file_to_disk(
        file_content: bytes,
        unique_filename: str,
        clip_type: ClipType
) -> Path:
    """
    Zapisuje plik na dysku

    Returns:
        Path: Ścieżka do zapisanego pliku
    """
    storage_dir = get_storage_directory(clip_type)

    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory: {e}")
        raise StorageError(
            message="Nie można utworzyć katalogu",
            path=str(storage_dir)
        )

    file_path = storage_dir / unique_filename

    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"File saved: {file_path}")
        return file_path
    except OSError as e:
        logger.error(f"Failed to write file: {e}")
        raise StorageError(
            message="Nie można zapisać pliku na dysku",
            path=str(file_path)
        )


def generate_thumbnails_sync(
        file_path: Path,
        clip_type: ClipType
) -> Tuple[Optional[str], Optional[str], Optional[dict]]:
    """
    Generuje thumbnails synchronicznie (JPEG + WebP)

    Returns:
        Tuple[thumbnail_path, thumbnail_webp_path, metadata]
    """
    thumbnails_dir = Path(settings.thumbnails_path)

    if settings.environment == "development":
        thumbnails_dir = (Path.cwd() / "uploads" / "thumbnails").resolve()

    try:
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.warning(f"Thumbnail directory error: {e}")
        return None, None, None

    thumbnail_filename = file_path.stem
    thumbnail_base_path = thumbnails_dir / thumbnail_filename

    thumbnail_path = None
    thumbnail_webp_path = None
    metadata = None

    try:
        if clip_type == ClipType.VIDEO:
            metadata = extract_video_metadata(str(file_path))

            success, webp_path = generate_thumbnail(
                video_path=str(file_path),
                output_path=str(thumbnail_base_path),
                timestamp="00:00:01",
                width=320,
                quality=5
            )

            if success:
                thumbnail_path = f"{thumbnail_base_path}.jpg"
                thumbnail_webp_path = webp_path
                logger.info("Video thumbnail generated: JPEG + WebP")

        else:  # SCREENSHOT
            metadata = extract_image_metadata(str(file_path))

            success, webp_path = generate_image_thumbnail(
                image_path=str(file_path),
                output_path=str(thumbnail_base_path),
                width=320,
                quality=5
            )

            if success:
                thumbnail_path = f"{thumbnail_base_path}.jpg"
                thumbnail_webp_path = webp_path
                logger.info("Image thumbnail generated: JPEG + WebP")

    except (FileUploadError, OSError) as e:
        logger.warning(f"Thumbnail generation failed: {e}")

    return thumbnail_path, thumbnail_webp_path, metadata


async def create_clip_record(
        db: Session,
        filename: str,
        file_path: Path,
        file_size: int,
        clip_type: ClipType,
        uploader_id: int,
        thumbnail_path: Optional[str] = None,
        thumbnail_webp_path: Optional[str] = None,
        metadata: Optional[dict] = None
) -> Clip:
    """
    Tworzy rekord klipa w bazie

    Returns:
        Clip: Utworzony obiekt Clip
    """
    from sqlalchemy.exc import SQLAlchemyError
    from app.core.exceptions import DatabaseError

    new_clip = Clip(
        filename=filename,
        file_path=str(file_path.resolve()),
        thumbnail_path=thumbnail_path,
        thumbnail_webp_path=thumbnail_webp_path,
        clip_type=clip_type,
        file_size=file_size,
        duration=metadata.get("duration") if metadata else None,
        width=metadata.get("width") if metadata else None,
        height=metadata.get("height") if metadata else None,
        uploader_id=uploader_id
    )

    try:
        db.add(new_clip)
        db.commit()
        db.refresh(new_clip)
        logger.info(f"Clip created: ID={new_clip.id}")
        return new_clip

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()

        # Cleanup plików
        try:
            file_path.unlink()
            if thumbnail_path:
                Path(thumbnail_path).unlink()
            if thumbnail_webp_path:
                Path(thumbnail_webp_path).unlink()
        except OSError:
            pass

        raise DatabaseError(
            message="Nie można zapisać do bazy danych",
            operation="create_clip"
        )


async def invalidate_clips_cache():
    """Invaliduje cache klipów"""
    try:
        from app.core.cache import invalidate_cache
        await invalidate_cache("clips:*")
        logger.info("Cache invalidated")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")
