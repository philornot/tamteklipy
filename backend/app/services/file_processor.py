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
    import os
    import tempfile

    storage_dir = get_storage_directory(clip_type)

    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        logger.error(f"Permission denied creating directory: {storage_dir} - {e}")
        raise StorageError(
            message=f"Brak uprawnień do utworzenia katalogu. Sprawdź uprawnienia do: {storage_dir}",
            path=str(storage_dir)
        )
    except OSError as e:
        logger.error(f"Failed to create directory: {e}")
        raise StorageError(
            message=f"Nie można utworzyć katalogu: {e}",
            path=str(storage_dir)
        )

    if storage_dir.exists() and not storage_dir.is_dir():
        logger.error(f"Storage path exists and is not a directory: {storage_dir}")
        raise StorageError(
            message=f"Ścieżka istnieje i nie jest katalogiem: {storage_dir}",
            path=str(storage_dir)
        )

    file_path = storage_dir / unique_filename
    tmp_path = None
    moved = False

    try:
        # Zapis do pliku tymczasowego w tym samym katalogu, a następnie atomic zastąpienie
        with tempfile.NamedTemporaryFile(delete=False, dir=str(storage_dir)) as tmp:
            tmp_path = Path(tmp.name)
            try:
                tmp.write(file_content)
                tmp.flush()
                os.fsync(tmp.fileno())
            except PermissionError as e:
                logger.error(f"Permission denied writing temporary file: {tmp_path} - {e}")
                raise StorageError(
                    message=f"Brak uprawnień do zapisu pliku tymczasowego: {tmp_path}",
                    path=str(tmp_path)
                )
            except OSError as e:
                logger.error(f"Failed to write temporary file: {e}")
                raise StorageError(
                    message=f"Nie można zapisać pliku tymczasowego: {e}",
                    path=str(tmp_path)
                )

        # Atomowe przeniesienie na docelową nazwę
        try:
            os.replace(str(tmp_path), str(file_path))
            moved = True
        except PermissionError as e:
            logger.error(f"Permission denied moving file to final destination: {file_path} - {e}")
            raise StorageError(
                message=f"Brak uprawnień do przeniesienia pliku do: {file_path}",
                path=str(file_path)
            )
        except OSError as e:
            logger.error(f"Failed to move temporary file to final destination: {e}")
            raise StorageError(
                message=f"Nie można przenieść pliku na docelową ścieżkę: {e}",
                path=str(file_path)
            )

        logger.info(f"File saved: {file_path}")
        return file_path

    finally:
        # Cleanup pliku tymczasowego, jeżeli nie został przeniesiony
        try:
            if tmp_path and tmp_path.exists() and not moved:
                tmp_path.unlink()
        except OSError:
            # Nie przerywamy działania, tylko logujemy
            logger.debug(f"Failed to remove temporary file: {tmp_path}")


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
