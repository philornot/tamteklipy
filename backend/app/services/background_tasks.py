"""
Background tasks dla asynchronicznego przetwarzania
Wywoływane przez FastAPI BackgroundTasks
"""
import logging
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.clip import Clip, ClipType
from app.services.thumbnail_service import (
    generate_thumbnail,
    generate_image_thumbnail,
    extract_video_metadata,
    extract_image_metadata
)

logger = logging.getLogger(__name__)


def process_thumbnail_background(clip_id: int, file_path: str, clip_type: ClipType):
    """
    Generuje thumbnail w tle (wywoływane przez BackgroundTasks)

    WAŻNE: Ta funkcja NIE jest async - działa w osobnym wątku

    Args:
        clip_id: ID klipa w bazie
        file_path: ścieżka do pliku
        clip_type: VIDEO lub SCREENSHOT
    """
    db = SessionLocal()

    try:
        logger.info(f"[BG] Processing thumbnail for clip {clip_id}")

        # Przygotuj ścieżki dla thumbnails
        thumbnails_dir = Path(settings.thumbnails_path)

        if settings.environment == "development":
            thumbnails_dir = (Path.cwd() / "uploads" / "thumbnails").resolve()

        thumbnails_dir.mkdir(parents=True, exist_ok=True)

        thumbnail_filename = Path(file_path).stem
        thumbnail_base_path = thumbnails_dir / thumbnail_filename

        thumbnail_path = None
        thumbnail_webp_path = None
        metadata = None

        # Generuj thumbnail w zależności od typu
        if clip_type == ClipType.VIDEO:
            logger.info(f"[BG] Extracting video metadata...")
            metadata = extract_video_metadata(file_path)

            logger.info(f"[BG] Generating video thumbnail...")
            success, webp_path = generate_thumbnail(
                video_path=file_path,
                output_path=str(thumbnail_base_path),
                timestamp="00:00:01",
                width=320,
                quality=5
            )

            if success:
                thumbnail_path = f"{thumbnail_base_path}.jpg"
                thumbnail_webp_path = webp_path
                logger.info(f"[BG] Video thumbnail generated (JPEG + WebP)")
            else:
                logger.warning(f"[BG] Video thumbnail generation failed")

        else:  # SCREENSHOT
            logger.info(f"[BG] Extracting image metadata...")
            metadata = extract_image_metadata(file_path)

            logger.info(f"[BG] Generating image thumbnail...")
            success, webp_path = generate_image_thumbnail(
                image_path=file_path,
                output_path=str(thumbnail_base_path),
                width=320,
                quality=5
            )

            if success:
                thumbnail_path = f"{thumbnail_base_path}.jpg"
                thumbnail_webp_path = webp_path
                logger.info(f"[BG] Image thumbnail generated (JPEG + WebP)")
            else:
                logger.warning(f"[BG] Image thumbnail generation failed")

        # Zaktualizuj bazę danych
        clip = db.query(Clip).filter(Clip.id == clip_id).first()

        if clip:
            clip.thumbnail_path = thumbnail_path
            clip.thumbnail_webp_path = thumbnail_webp_path

            if metadata:
                clip.duration = metadata.get("duration")
                clip.width = metadata.get("width")
                clip.height = metadata.get("height")

            db.commit()

            logger.info(f"[BG] Clip {clip_id} updated with:")
            logger.info(f"[BG]    - Thumbnail: {thumbnail_path is not None}")
            logger.info(f"[BG]    - WebP: {thumbnail_webp_path is not None}")
            logger.info(f"[BG]    - Metadata: {metadata is not None}")

            if metadata:
                logger.info(f"[BG]    - Resolution: {metadata.get('width')}x{metadata.get('height')}")
                if metadata.get('duration'):
                    logger.info(f"[BG]    - Duration: {metadata.get('duration')}s")
        else:
            logger.warning(f"[BG] Clip {clip_id} not found in database!")

        logger.info(f"[BG] Background processing complete for clip {clip_id}")

    except Exception as e:
        logger.warning(f"[BG] Thumbnail processing failed for clip {clip_id}: {e}", exc_info=True)
        db.rollback()

    finally:
        db.close()


# Opcjonalnie: Funkcja do retry, jeśli thumbnail się nie udał
def retry_thumbnail_generation(clip_id: int):
    """
    Ponowna próba wygenerowania thumbnail dla istniejącego klipa
    Przydatne, jeśli pierwsze generowanie się nie powiodło
    """
    db = SessionLocal()

    try:
        clip = db.query(Clip).filter(Clip.id == clip_id).first()

        if not clip:
            logger.warning(f"[RETRY] Clip {clip_id} not found")
            return

        if clip.thumbnail_path:
            logger.info(f"[RETRY] Clip {clip_id} already has thumbnail, skipping")
            return

        file_path = clip.file_path

        if not Path(file_path).exists():
            logger.warning(f"[RETRY] File not found: {file_path}")
            return

        logger.info(f"[RETRY] Retrying thumbnail generation for clip {clip_id}")

        # Wywołaj główną funkcję
        process_thumbnail_background(clip_id, file_path, clip.clip_type)

    except Exception as e:
        logger.warning(f"[RETRY] Failed to retry thumbnail: {e}")

    finally:
        db.close()


def generate_webp_from_jpeg_background(jpeg_path: str, webp_path: str, clip_id: int, db):
    """
    Konwertuje JPEG na WebP w tle i aktualizuje bazę
    """
    from app.core.database import SessionLocal
    import subprocess

    db_session = SessionLocal()

    try:
        cmd = [
            "ffmpeg",
            "-i", jpeg_path,
            "-c:v", "libwebp",
            "-quality", "75",
            "-y",
            webp_path
        ]

        result = subprocess.run(cmd, capture_output=True, timeout=30)

        if result.returncode == 0 and Path(webp_path).exists():
            logger.info(f"WebP generated: {webp_path}")

            # Zaktualizuj bazę
            clip = db_session.query(Clip).filter(Clip.id == clip_id).first()
            if clip:
                clip.thumbnail_webp_path = webp_path
                db_session.commit()
                logger.info(f"Clip {clip_id} updated with WebP path")
        else:
            logger.warning(f"WebP generation failed for clip {clip_id}, JPEG fallback OK")

    except Exception as e:
        logger.warning(f"WebP generation error (non-critical): {e}")
    finally:
        db_session.close()
