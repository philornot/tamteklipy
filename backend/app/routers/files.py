"""
Router dla zarządzania plikami — upload, download, listowanie klipów i screenshotów
"""
import hashlib
import io
import logging
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional

import aiofiles
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import FileUploadError, ValidationError, NotFoundError, AuthorizationError, StorageError, \
    DatabaseError
from app.models.clip import Clip, ClipType
from app.models.award import Award
from app.models.user import User
from app.schemas.clip import ClipResponse, ClipListResponse, ClipDetailResponse
from app.services.thumbnail_service import generate_thumbnail, extract_video_metadata
from fastapi import APIRouter, UploadFile, File, Depends, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, asc
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
    """
    Upload pliku z pełną walidacją i error handling
    """
    logger.info(f"Upload from {current_user.username}: {file.filename} ({file.content_type})")

    try:
        # 1. Waliduj typ pliku
        try:
            clip_type, extension = validate_file_type(file.filename, file.content_type)
        except ValidationError as e:
            logger.warning(f"Invalid file type: {file.content_type}")
            raise

        # 2. Przeczytaj plik
        try:
            file_content = await file.read()
            file_size = len(file_content)
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            raise FileUploadError(
                message="Nie można odczytać pliku",
                filename=file.filename,
                reason="File read error"
            )

        # 3. Waliduj rozmiar
        try:
            validate_file_size(file_size, clip_type)
        except ValidationError as e:
            logger.warning(f"File too large: {file_size} bytes")
            raise

        # 4. Wygeneruj unikalną nazwę
        unique_filename = generate_unique_filename(file.filename, extension)

        # 5. Określ ścieżkę
        if clip_type == ClipType.VIDEO:
            storage_dir = Path(settings.clips_path)
        else:
            storage_dir = Path(settings.screenshots_path)

        if settings.environment == "development":
            storage_dir = Path("uploads") / ("clips" if clip_type == ClipType.VIDEO else "screenshots")

        # 6. Sprawdź miejsce na dysku
        try:
            check_disk_space(storage_dir, file_size)
        except StorageError as e:
            logger.error(f"Insufficient disk space: {e}")
            raise

        # 7. Utwórz katalog
        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            raise StorageError(
                message="Nie można utworzyć katalogu",
                path=str(storage_dir)
            )

        file_path = storage_dir / unique_filename

        # 8. Zapisz plik
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info(f"File saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write file: {e}")
            raise StorageError(
                message="Nie można zapisać pliku na dysku",
                path=str(file_path)
            )

        # 9. Generuj thumbnail dla video
        thumbnail_path = None
        video_metadata = None

        if clip_type == ClipType.VIDEO:
            try:
                from app.services.thumbnail_service import generate_thumbnail, extract_video_metadata

                video_metadata = extract_video_metadata(str(file_path))

                thumbnails_dir = Path(settings.thumbnails_path)
                if settings.environment == "development":
                    thumbnails_dir = Path("uploads/thumbnails")

                thumbnails_dir.mkdir(parents=True, exist_ok=True)

                thumbnail_filename = f"{Path(unique_filename).stem}.jpg"
                thumbnail_full_path = thumbnails_dir / thumbnail_filename

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
                logger.warning(f"Thumbnail generation failed: {e}")
                # Kontynuuj mimo błędu thumbnail

        # 10. Zapisz do bazy
        try:
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

            logger.info(f"Clip created: ID={new_clip.id}")

        except Exception as e:
            logger.error(f"Database error: {e}")
            # Usuń plik jeśli zapis do bazy się nie udał
            try:
                file_path.unlink()
                if thumbnail_path:
                    Path(thumbnail_path).unlink()
            except:
                pass

            from app.core.exceptions import DatabaseError
            raise DatabaseError(
                message="Nie można zapisać do bazy danych",
                operation="create_clip"
            )

        # 11. Zwróć sukces
        response = {
            "message": "Plik został przesłany pomyślnie",
            "clip_id": new_clip.id,
            "filename": file.filename,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "clip_type": clip_type.value,
            "uploader": current_user.username,
            "created_at": new_clip.created_at.isoformat()
        }

        if thumbnail_path:
            response["thumbnail_generated"] = True

        if video_metadata:
            response["duration"] = video_metadata.get("duration")
            response["resolution"] = f"{video_metadata.get('width')}x{video_metadata.get('height')}"

        return response

    except (ValidationError, FileUploadError, StorageError, DatabaseError):
        # Nasze własne wyjątki - przepuść dalej
        raise
    except Exception as e:
        # Nieoczekiwany błąd
        logger.error(f"Unexpected upload error: {e}", exc_info=True)
        raise FileUploadError(
            message="Nieoczekiwany błąd podczas uploadu",
            filename=file.filename,
            reason=str(e)
        )


@router.get("/clips", response_model=ClipListResponse)
async def list_clips(
        page: int = 1,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        clip_type: Optional[str] = None,
        uploader_id: Optional[int] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Listowanie klipów z paginacją, sortowaniem i filtrowaniem

    GET /api/files/clips?page=1&limit=50&sort_by=created_at&sort_order=desc&clip_type=video

    Query params:
        - page: Numer strony (default: 1)
        - limit: Liczba elementów na stronę (default: 50, max: 100)
        - sort_by: Pole sortowania (created_at, filename, file_size, duration)
        - sort_order: Kierunek sortowania (asc, desc)
        - clip_type: Filtr typu (video, screenshot)
        - uploader_id: Filtr po uploaderze
    """
    # Walidacja parametrów
    if page < 1:
        page = 1

    if limit < 1:
        limit = 50
    elif limit > 100:
        limit = 100

    # Oblicz offset
    offset = (page - 1) * limit

    # Bazowe query
    query = db.query(Clip).filter(Clip.is_deleted == False)

    # Filtrowanie po typie
    if clip_type:
        try:
            filter_type = ClipType(clip_type.lower())
            query = query.filter(Clip.clip_type == filter_type)
        except ValueError:
            raise ValidationError(
                message=f"Nieprawidłowy typ klipa: {clip_type}",
                field="clip_type",
                details={"allowed_values": ["video", "screenshot"]}
            )

    # Filtrowanie po uploaderze
    if uploader_id:
        query = query.filter(Clip.uploader_id == uploader_id)

    # Sortowanie
    allowed_sort_fields = {
        "created_at": Clip.created_at,
        "filename": Clip.filename,
        "file_size": Clip.file_size,
        "duration": Clip.duration
    }

    if sort_by not in allowed_sort_fields:
        raise ValidationError(
            message=f"Nieprawidłowe pole sortowania: {sort_by}",
            field="sort_by",
            details={"allowed_values": list(allowed_sort_fields.keys())}
        )

    sort_field = allowed_sort_fields[sort_by]

    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_field))
    else:
        query = query.order_by(desc(sort_field))

    # Pobierz total przed paginacją
    total = query.count()

    # Zastosuj paginację
    clips = query.offset(offset).limit(limit).all()

    # Oblicz liczbę stron
    pages = (total + limit - 1) // limit

    # Konwertuj do response
    clips_response = [
        ClipResponse(
            id=clip.id,
            filename=clip.filename,
            clip_type=clip.clip_type.value,
            file_size=clip.file_size,
            file_size_mb=clip.file_size_mb,
            duration=clip.duration,
            width=clip.width,
            height=clip.height,
            created_at=clip.created_at,
            uploader_username=clip.uploader.username,
            uploader_id=clip.uploader_id,
            award_count=clip.award_count,
            has_thumbnail=clip.thumbnail_path is not None
        )
        for clip in clips
    ]

    return ClipListResponse(
        clips=clips_response,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/clips/{clip_id}", response_model=ClipDetailResponse)
async def get_clip(
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz szczegóły pojedynczego klipa z nagrodami

    GET /api/files/clips/{clip_id}
    """
    from sqlalchemy.orm import joinedload

    clip = db.query(Clip).options(
        joinedload(Clip.uploader),
        joinedload(Clip.awards).joinedload(Award.user)
    ).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Przygotuj informacje o nagrodach
    awards_info = [
        {
            "id": award.id,
            "award_name": award.award_name,
            "user_id": award.user_id,
            "username": award.user.username,
            "awarded_at": award.awarded_at.isoformat()
        }
        for award in clip.awards
    ]

    return ClipDetailResponse(
        id=clip.id,
        filename=clip.filename,
        clip_type=clip.clip_type.value,
        file_size=clip.file_size,
        file_size_mb=clip.file_size_mb,
        duration=clip.duration,
        width=clip.width,
        height=clip.height,
        created_at=clip.created_at,
        uploader_username=clip.uploader.username,
        uploader_id=clip.uploader_id,
        award_count=clip.award_count,
        has_thumbnail=clip.thumbnail_path is not None,
        awards=awards_info,
        thumbnail_url=f"/api/files/thumbnails/{clip.id}" if clip.thumbnail_path else None,
        download_url=f"/api/files/download/{clip.id}"
    )


@router.get("/download/{clip_id}")
async def download_clip(
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz plik klipa

    GET /api/files/download/{clip_id}

    Zwraca plik z odpowiednimi headerami Content-Type i Content-Disposition
    """
    # Znajdź klip w bazie
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Sprawdź uprawnienia
    if not can_access_clip(clip, current_user):
        raise AuthorizationError(
            message="Nie masz uprawnień do pobrania tego pliku"
        )

    # Sprawdź czy plik istnieje
    file_path = Path(clip.file_path)

    if not file_path.exists():
        logger.error(f"File not found on disk: {file_path}")
        raise StorageError(
            message="Plik nie został znaleziony na dysku",
            path=str(file_path)
        )

    # Określ MIME type
    if clip.clip_type == ClipType.VIDEO:
        media_type = "video/mp4"  # Możesz dopasować do rzeczywistego typu
    else:
        media_type = "image/png"  # Możesz dopasować do rzeczywistego typu

    # Zwróć plik z proper headers
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=clip.filename,  # Original filename dla użytkownika
        headers={
            "Content-Disposition": f'attachment; filename="{clip.filename}"',
            "Accept-Ranges": "bytes"  # Informuje że wspieramy range requests
        }
    )


class BulkDownloadRequest(BaseModel):
    """Request body dla bulk download"""
    clip_ids: List[int] = Field(..., min_items=1, max_items=50)


@router.post("/download-bulk")
async def download_bulk(
        request: BulkDownloadRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz wiele plików jako archiwum ZIP

    POST /api/files/download-bulk
    Body: {"clip_ids": [1, 2, 3]}

    Zwraca archiwum ZIP ze wszystkimi wybranymi plikami
    Maksymalnie 50 plików na raz
    """
    clip_ids = request.clip_ids

    # Walidacja liczby plików
    if len(clip_ids) > 50:
        raise ValidationError(
            message="Zbyt wiele plików - maksymalnie 50 naraz",
            field="clip_ids",
            details={"requested": len(clip_ids), "max": 50}
        )

    # Pobierz klipy z bazy
    clips = db.query(Clip).filter(
        Clip.id.in_(clip_ids),
        Clip.is_deleted == False
    ).all()

    if not clips:
        raise NotFoundError(resource="Klipy", resource_id=None)

    found_ids = {clip.id for clip in clips}
    missing_ids = set(clip_ids) - found_ids

    if missing_ids:
        logger.warning(f"Missing clip IDs: {missing_ids}")

    # Sprawdź uprawnienia dla każdego klipa
    accessible_clips = []
    for clip in clips:
        if can_access_clip(clip, current_user):
            accessible_clips.append(clip)

    if not accessible_clips:
        raise AuthorizationError(
            message="Nie masz dostępu do żadnego z wybranych plików"
        )

    # Sprawdź czy wszystkie pliki istnieją na dysku
    existing_clips = []
    total_size = 0

    for clip in accessible_clips:
        file_path = Path(clip.file_path)
        if file_path.exists():
            existing_clips.append(clip)
            total_size += clip.file_size
        else:
            logger.error(f"File not found: {file_path}")

    if not existing_clips:
        raise StorageError(
            message="Żaden z plików nie został znaleziony na dysku"
        )

    # Limit całkowitego rozmiaru (1GB)
    MAX_TOTAL_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB

    if total_size > MAX_TOTAL_SIZE:
        raise ValidationError(
            message=f"Całkowity rozmiar plików przekracza limit: {total_size / (1024 ** 3):.2f}GB (max: 1GB)",
            field="clip_ids",
            details={
                "total_size_bytes": total_size,
                "max_size_bytes": MAX_TOTAL_SIZE
            }
        )

    logger.info(f"Creating ZIP archive with {len(existing_clips)} files, total size: {total_size / (1024 ** 2):.2f}MB")

    # Generator do streamowania ZIP
    async def zip_generator():
        """
        Generator który tworzy ZIP w locie i streamuje do klienta
        """
        # Użyj BytesIO jako temporary buffer
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for clip in existing_clips:
                file_path = Path(clip.file_path)

                # Użyj oryginalnej nazwy pliku w ZIP
                # Dodaj ID żeby uniknąć kolizji nazw
                filename_in_zip = f"{clip.id}_{clip.filename}"

                try:
                    # Dodaj plik do ZIP
                    zip_file.write(file_path, arcname=filename_in_zip)
                    logger.debug(f"Added to ZIP: {filename_in_zip}")

                except Exception as e:
                    logger.error(f"Failed to add file to ZIP: {file_path}, error: {e}")
                    # Kontynuuj z pozostałymi plikami

        # Przenieś wskaźnik na początek bufora
        buffer.seek(0)

        # Streamuj ZIP w chunkach
        while True:
            chunk = buffer.read(8192)  # 8KB chunks
            if not chunk:
                break
            yield chunk

    # Wygeneruj nazwę archiwum
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"tamteklipy_{timestamp}.zip"

    return StreamingResponse(
        zip_generator(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
        }
    )


@router.get("/thumbnails/{clip_id}")
async def get_thumbnail(
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz miniaturę klipa

    GET /api/files/thumbnails/{clip_id}
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    if not clip.thumbnail_path:
        raise NotFoundError(resource="Thumbnail dla klipa", resource_id=clip_id)

    thumbnail_path = Path(clip.thumbnail_path)

    if not thumbnail_path.exists():
        logger.error(f"Thumbnail not found: {thumbnail_path}")
        raise StorageError(
            message="Thumbnail nie został znaleziony",
            path=str(thumbnail_path)
        )

    return FileResponse(
        path=str(thumbnail_path),
        media_type="image/jpeg",
        headers={
            "Cache-Control": "public, max-age=3600"  # Cache na 1h
        }
    )


@router.get("/stream/{clip_id}")
async def stream_video(
        clip_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Stream video z obsługą Range requests (dla video player)

    GET /api/files/stream/{clip_id}
    Header: Range: bytes=0-1024

    Obsługuje partial content requests dla video streaming
    """
    # Znajdź klip
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False,
        Clip.clip_type == ClipType.VIDEO
    ).first()

    if not clip:
        raise NotFoundError(resource="Video klip", resource_id=clip_id)

    file_path = Path(clip.file_path)

    if not file_path.exists():
        raise StorageError(
            message="Plik nie został znaleziony",
            path=str(file_path)
        )

    file_size = file_path.stat().st_size

    # Sprawdź czy request ma header Range
    range_header = request.headers.get("range")

    if not range_header:
        # Brak Range header - zwróć cały plik
        return FileResponse(
            path=str(file_path),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size)
            }
        )

    # Parse Range header: "bytes=0-1024"
    try:
        range_str = range_header.replace("bytes=", "")
        start_str, end_str = range_str.split("-")

        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1

        # Waliduj range
        if start >= file_size or end >= file_size or start > end:
            raise ValueError("Invalid range")

        chunk_size = end - start + 1

    except (ValueError, AttributeError):
        raise ValidationError(
            message="Nieprawidłowy header Range",
            field="Range",
            details={"range": range_header}
        )

    # Funkcja generatora dla streaming
    async def file_iterator():
        async with aiofiles.open(file_path, mode='rb') as f:
            await f.seek(start)
            remaining = chunk_size

            while remaining > 0:
                read_size = min(8192, remaining)  # 8KB chunks
                data = await f.read(read_size)

                if not data:
                    break

                remaining -= len(data)
                yield data

    # Zwróć partial content response (206)
    return StreamingResponse(
        file_iterator(),
        status_code=206,  # Partial Content
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Cache-Control": "public, max-age=3600"
        }
    )


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


# todo: sugestie co do hashowania: dodaj pole `file_hash` do modelu `Clip`, utwórz migrację Alembic, indeksuj `file_hash` w bazie
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


def can_access_clip(clip: Clip, user: User) -> bool:
    """
    Sprawdza czy użytkownik ma dostęp do klipa

    Args:
        clip: Klip do sprawdzenia
        user: Użytkownik

    Returns:
        bool: True jeśli ma dostęp
    """
    # Zasady dostępu:
    # 1. Właściciel zawsze ma dostęp
    if clip.uploader_id == user.id:
        return True

    # 2. Wszyscy zalogowani mają dostęp
    # W przyszłości można dodać np. prywatne klipy
    return True
