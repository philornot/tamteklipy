"""
Migration script: Regeneruje wszystkie istniejące thumbnails
- Zmienia jakość z 2 na 5
- Dodaje WebP jako alternatywę
- Zachowuje JPEG jako fallback
"""
import sys
from pathlib import Path

# Dodaj backend do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from app.core.database import SessionLocal
from app.models.clip import Clip, ClipType
from app.services.thumbnail_service import generate_thumbnail, generate_image_thumbnail
from app.core.config import settings
from app.core.logging_config import setup_logging

# Spójna konfiguracja logowania
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


def regenerate_all_thumbnails():
    """
    Regeneruje wszystkie thumbnails dla klipów w bazie
    """
    db = SessionLocal()

    try:
        # Pobierz wszystkie klipy
        clips = db.query(Clip).filter(Clip.is_deleted == False).all()

        logger.info(f"Found {len(clips)} clips to process")

        success_count = 0
        skip_count = 0
        error_count = 0

        for clip in clips:
            logger.info(f"Processing clip {clip.id}: {clip.filename}")

            # Sprawdź czy plik źródłowy istnieje
            source_path = Path(clip.file_path)
            if not source_path.exists():
                logger.warning(f"Source file not found: {source_path}")
                skip_count += 1
                continue

            # Przygotuj katalog na thumbnails
            thumbnails_dir = Path(settings.thumbnails_path)
            if settings.environment == "development":
                thumbnails_dir = (Path.cwd() / "uploads" / "thumbnails").resolve()

            thumbnails_dir.mkdir(parents=True, exist_ok=True)

            # Przygotuj ścieżki (bez rozszerzenia)
            thumbnail_filename = f"{Path(clip.filename).stem}_{clip.id}"
            thumbnail_base_path = thumbnails_dir / thumbnail_filename

            try:
                if clip.clip_type == ClipType.VIDEO:
                    # Regeneruj thumbnail dla video
                    success, webp_path = generate_thumbnail(
                        video_path=str(source_path),
                        output_path=str(thumbnail_base_path),
                        timestamp="00:00:01",
                        width=320,
                        quality=5  # Nowa jakość
                    )
                else:
                    # Regeneruj thumbnail dla screenshota
                    success, webp_path = generate_image_thumbnail(
                        image_path=str(source_path),
                        output_path=str(thumbnail_base_path),
                        width=320,
                        quality=5  # Nowa jakość
                    )

                if success:
                    # Aktualizuj ścieżki w bazie
                    clip.thumbnail_path = f"{thumbnail_base_path}.jpg"
                    clip.thumbnail_webp_path = webp_path

                    db.commit()

                    if webp_path:
                        logger.info(f"Clip {clip.id}: JPEG + WebP generated")
                    else:
                        logger.info(f"Clip {clip.id}: JPEG generated (WebP failed)")

                    success_count += 1
                else:
                    logger.error(f"Clip {clip.id}: Generation failed")
                    error_count += 1

            except Exception as e:
                logger.error(f"Clip {clip.id}: Error - {e}")
                error_count += 1
                db.rollback()

        logger.info("\n" + "=" * 50)
        logger.info("REGENERATION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total clips: {len(clips)}")
        logger.info(f"Success: {success_count}")
        logger.info(f"Skipped: {skip_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting thumbnail regeneration...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Thumbnails path: {settings.thumbnails_path}")

    # Pytaj o potwierdzenie w produkcji
    if settings.environment == "production":
        response = input("\nRunning in PRODUCTION. Continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted by user")
            sys.exit(0)

    regenerate_all_thumbnails()
    logger.info("Migration complete!")
