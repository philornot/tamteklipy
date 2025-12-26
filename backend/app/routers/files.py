"""
Router dla zarządzania plikami
Tylko endpointy, logika w services
"""
import io
import logging
import zipfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List
from typing import Optional

import aiofiles
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_flexible
from app.core.exceptions import (
    FileUploadError, ValidationError, NotFoundError,
    AuthorizationError, StorageError
)
from app.models.award import Award
from app.models.award_type import AwardType
from app.models.clip import Clip, ClipType
from app.models.user import User
from app.schemas.clip import ClipResponse, ClipListResponse, ClipDetailResponse
from app.services.background_tasks import generate_webp_from_jpeg_background
from app.services.background_tasks import process_thumbnail_background
from app.services.file_processor import (
    save_file_to_disk, create_clip_record,
    get_storage_directory
)
from app.services.validated_file import ValidatedFile
from app.utils.file_helpers import can_access_clip
from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks, Request, Response
from fastapi import Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, asc
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload, joinedload

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class BulkDownloadRequest(BaseModel):
    """Request model dla bulk download"""
    clip_ids: List[int] = Field(..., min_length=1, max_length=50)


class BulkActionType(str, Enum):
    """Dostępne typy akcji masowych"""
    DELETE = "delete"
    ADD_TAGS = "add-tags"
    ADD_TO_SESSION = "add-to-session"


class BulkActionRequest(BaseModel):
    """Request model dla bulk actions"""
    clip_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Lista ID klipów (1-100)"
    )
    action: BulkActionType = Field(..., description="Typ akcji do wykonania")
    tags: List[str] = Field(
        default=[],
        max_length=10,
        description="Tagi (dla add-tags)"
    )
    session_name: str = Field(
        default="",
        max_length=100,
        description="Nazwa sesji (dla add-to-session)"
    )


class BulkActionResponse(BaseModel):
    """Response model dla bulk actions"""
    success: bool
    action: str
    processed: int
    failed: int
    message: str
    details: dict = {}


# ============================================================================
# UPLOAD ENDPOINT
# ============================================================================

@router.post("/upload")
async def upload_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        thumbnail: Optional[UploadFile] = File(None),
        db=Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Upload pliku z opcjonalnym thumbnail z frontendu

    """
    logger.info(f"Upload from {current_user.username}: {file.filename}")

    try:
        # TK-626: Odczytaj zawartość pliku PRZED walidacją
        file_content = await file.read()

        # Walidacja pliku - używa factory method
        validated = ValidatedFile(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )

        # Przygotuj katalog storage
        storage_dir = get_storage_directory(validated.clip_type)

        # TODO: Implement disk space checking if needed

        # Zapis pliku na dysku
        file_path = await save_file_to_disk(
            validated.content,
            validated.unique_filename,
            validated.clip_type
        )
        logger.info(f"File saved: {file_path}")

        # Metadata będą uzupełnione w tle
        metadata = None

        # Utwórz rekord w bazie
        new_clip = await create_clip_record(
            db=db,
            filename=validated.original_filename,
            file_path=file_path,
            file_size=validated.size_bytes,
            clip_type=validated.clip_type,
            uploader_id=current_user.id,
            thumbnail_path=None,
            thumbnail_webp_path=None,
            metadata=metadata
        )
        logger.info(f"Clip created: ID={new_clip.id}")

        # Obsługa thumbnail z frontendu
        if thumbnail:
            try:
                # Przygotuj katalog
                thumbnails_dir = Path(settings.thumbnails_path)
                if settings.environment == "development":
                    thumbnails_dir = (Path.cwd() / "uploads" / "thumbnails").resolve()

                thumbnails_dir.mkdir(parents=True, exist_ok=True)

                # Nazwa pliku z ID klipu
                thumbnail_filename = f"{Path(file.filename).stem}_{new_clip.id}"
                thumbnail_path = thumbnails_dir / f"{thumbnail_filename}.jpg"

                # Zapisz thumbnail z frontendu
                thumbnail_content = await thumbnail.read()
                async with aiofiles.open(thumbnail_path, "wb") as f:
                    await f.write(thumbnail_content)

                logger.info(f"Thumbnail from frontend saved: {thumbnail_path}")

                # Zaktualizuj rekord w bazie
                new_clip.thumbnail_path = str(thumbnail_path)
                db.commit()

                # Zakolejkuj generowanie WebP w tle
                webp_path = thumbnails_dir / f"{thumbnail_filename}.webp"
                background_tasks.add_task(
                    generate_webp_from_jpeg_background,
                    str(thumbnail_path),
                    str(webp_path),
                    new_clip.id,
                    db
                )

            except Exception as e:
                logger.warning(f"Failed to save thumbnail from frontend: {e}")
                # Nie blokuj uploadu, backend wygeneruje w tle

        # Jeśli NIE było thumbnail z frontendu, zakolejkuj pełne generowanie
        if not thumbnail:
            background_tasks.add_task(
                process_thumbnail_background,
                clip_id=new_clip.id,
                file_path=str(file_path),
                clip_type=validated.clip_type
            )
            logger.info(f"Thumbnail generation queued (backend fallback)")

        # Response
        return {
            "message": "Plik został przesłany pomyślnie",
            "clip_id": new_clip.id,
            "filename": validated.original_filename,
            "file_size_mb": validated.size_mb,
            "clip_type": validated.clip_type.value,
            "uploader": current_user.username,
            "created_at": new_clip.created_at.isoformat(),
            "thumbnail_status": "ready" if thumbnail else "processing",
            "thumbnail_ready": thumbnail is not None,
            "duration": new_clip.duration,
            "width": new_clip.width,
            "height": new_clip.height
        }

    except (ValidationError, FileUploadError, StorageError):
        raise
    except Exception as e:
        logger.error(f"Unexpected upload error: {e}", exc_info=True)
        raise FileUploadError(
            message="Nieoczekiwany błąd podczas uploadu",
            filename=file.filename,
            reason=str(e)
        )


# ============================================================================
# LIST & DETAIL ENDPOINTS
# ============================================================================

@router.get("/clips/random")
async def get_random_clips(
        limit: int = Query(10, le=50, description="Max liczba klipów do zwrócenia"),
        exclude_ids: List[int] = Query([], description="ID klipów do pominięcia"),
        prefer_awarded: bool = Query(False, description="Preferuj klipy z nagrodami"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Zwraca losowe klipy dla vertical feed (mobile TikTok-style).
    """
    # Base query — wszystkie aktywne klipy (bez is_deleted)
    query = db.query(Clip).filter(Clip.is_deleted == False)

    # Wykluczenie już wyświetlonych
    if exclude_ids:
        query = query.filter(~Clip.id.in_(exclude_ids))

    # Preferuj klipy z nagrodami (opcjonalnie)
    if prefer_awarded:
        # Subquery: klipy z nagrodami
        awarded_clips = (
            db.query(Award.clip_id)
            .group_by(Award.clip_id)
            .subquery()
        )

        # Sortuj: najpierw z nagrodami, potem losowo
        query = query.outerjoin(
            awarded_clips,
            Clip.id == awarded_clips.c.clip_id
        ).order_by(
            awarded_clips.c.clip_id.isnot(None).desc(),
            func.random()
        )
    else:
        # Zwykła losowa kolejność
        query = query.order_by(func.random())

    # Eager load relacji
    query = query.options(
        selectinload(Clip.uploader),
        selectinload(Clip.awards)
    )

    # Limit
    clips = query.limit(limit).all()

    # Pobierz wszystkie award types (batch)
    all_award_names = {
        award.award_name
        for clip in clips
        for award in clip.awards
    }

    award_types_map = {}
    if all_award_names:
        award_types = db.query(AwardType).filter(
            AwardType.name.in_(all_award_names)
        ).all()
        award_types_map = {at.name: at for at in award_types}

    # Format response
    result = []
    for clip in clips:
        # Agreguj award counts
        award_counts = {}
        for award in clip.awards:
            award_counts[award.award_name] = award_counts.get(award.award_name, 0) + 1

        # Format award icons properly using get_icon_info()
        formatted_award_icons = []
        for award_name, count in award_counts.items():
            award_type = award_types_map.get(award_name)

            if award_type:
                icon_info = award_type.get_icon_info()
                formatted_award_icons.append({
                    "award_name": award_name,
                    "icon": award_type.icon,
                    "lucide_icon": icon_info.get("icon_value") if icon_info["icon_type"] == "lucide" else None,
                    "icon_type": icon_info["icon_type"],
                    "icon_url": icon_info.get("icon_url"),
                    "count": count
                })
            else:
                # Fallback if award type not found
                formatted_award_icons.append({
                    "award_name": award_name,
                    "icon": "🏆",
                    "lucide_icon": None,
                    "icon_type": "emoji",
                    "icon_url": None,
                    "count": count
                })

        result.append({
            "id": clip.id,
            "filename": clip.filename,
            "clip_type": clip.clip_type.value,  # Konwertuj enum na string
            "file_size_mb": round(clip.file_size / (1024 * 1024), 2),
            "duration": clip.duration,
            "width": clip.width,
            "height": clip.height,
            "has_thumbnail": clip.thumbnail_path is not None,
            "created_at": clip.created_at.isoformat(),
            "uploader_username": clip.uploader.username,
            "uploader_id": clip.uploader_id,
            "award_count": len(clip.awards),
            "award_icons": formatted_award_icons
        })

    return {
        "clips": result,
        "total": len(result),
        "has_more": len(result) == limit
    }


@router.get("/clips", response_model=ClipListResponse)
async def list_clips(
        response: Response,
        page: int = 1,
        limit: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        clip_type: Optional[str] = None,
        uploader_id: Optional[int] = None,
        db: Session = Depends(get_db),
):
    """
    Listowanie klipów z paginacją, sortowaniem i filtrowaniem

    **Parametry:**
    - page: Numer strony (min: 1)
    - limit: Liczba klipów na stronę (1-100)
    - sort_by: Pole sortowania (created_at, filename, file_size, duration)
    - sort_order: Kierunek sortowania (asc, desc)
    - clip_type: Filtrowanie po typie (video, screenshot)
    - uploader_id: Filtrowanie po uploaderze

    **Returns:**
    - Lista klipów z metadanymi
    - Prefetch hints dla miniatur (HTTP/2)
    """
    # Walidacja i normalizacja parametrów
    page = max(1, page)
    limit = min(max(1, limit), 100)
    offset = (page - 1) * limit

    # Bazowe query z optymalizacją
    query = db.query(Clip).options(
        selectinload(Clip.awards).selectinload(Award.user)
    ).filter(Clip.is_deleted == False)

    # Filtrowanie po typie klipa
    if clip_type:
        try:
            filter_type = ClipType(clip_type.lower())
            query = query.filter(Clip.clip_type == filter_type)
        except ValueError:
            raise ValidationError(
                message=f"Nieprawidłowy typ klipa: {clip_type}",
                field="clip_type"
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
            field="sort_by"
        )

    sort_field = allowed_sort_fields[sort_by]
    query = query.order_by(
        asc(sort_field) if sort_order.lower() == "asc" else desc(sort_field)
    )

    # Paginacja i wykonanie query
    total = query.count()
    clips = query.offset(offset).limit(limit).all()

    # Pobierz typy nagród (batch query)
    all_award_names = {
        award.award_name
        for clip in clips
        for award in clip.awards
    }
    award_types = []
    if all_award_names:
        award_types = db.query(AwardType).filter(
            AwardType.name.in_(all_award_names)
        ).all()
    award_types_map = {at.name: at for at in award_types}

    # Przygotowanie response
    clips_response = []
    prefetch_candidates = []

    for clip in clips:
        # Agregacja nagród
        award_counts = {}
        for award in clip.awards:
            award_counts[award.award_name] = award_counts.get(award.award_name, 0) + 1

        # Przygotowanie ikon nagród
        award_icons = []
        for award_name, count in award_counts.items():
            award_type = award_types_map.get(award_name)
            icon_url = None

            if award_type and award_type.custom_icon_path:
                icon_url = f"/api/admin/award-types/{award_type.id}/icon"

            award_icons.append({
                "award_name": award_name,
                "icon_url": icon_url,
                "icon": award_type.icon if award_type else "🏆",
                "lucide_icon": award_type.lucide_icon if award_type else None,
                "count": count
            })

        # Prefetch tylko jeśli plik FAKTYCZNIE istnieje
        thumbnail_ready = False
        if clip.thumbnail_webp_path:
            webp_path = Path(clip.thumbnail_webp_path)
            if webp_path.exists() and webp_path.stat().st_size > 0:
                thumbnail_ready = True
                prefetch_candidates.append(f"/api/files/thumbnails/{clip.id}")
        elif clip.thumbnail_path:
            jpeg_path = Path(clip.thumbnail_path)
            if jpeg_path.exists() and jpeg_path.stat().st_size > 0:
                thumbnail_ready = True
                prefetch_candidates.append(f"/api/files/thumbnails/{clip.id}")

        clips_response.append(ClipResponse(
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
            has_thumbnail=thumbnail_ready,
            has_webp_thumbnail=clip.thumbnail_webp_path is not None and Path(clip.thumbnail_webp_path).exists(),
            award_icons=award_icons
        ))

    pages = (total + limit - 1) // limit

    # Resource Hints: prefetch thumbnails (HTTP/2)
    # Używamy rel=prefetch zamiast rel=preload aby uniknąć ostrzeżeń w konsoli
    if prefetch_candidates:
        link_headers = [
            f'<{url}>; rel=prefetch'
            for url in prefetch_candidates[:5]  # Max 5 prefetches
        ]
        response.headers["Link"] = ", ".join(link_headers)

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
):
    """
    Szczegóły pojedynczego klipa

    **Returns:**
    - Pełne informacje o klipie
    - Lista wszystkich nagród z użytkownikami
    - URLe do thumbnails i downloadu
    """
    clip = db.query(Clip).options(
        joinedload(Clip.uploader),
        joinedload(Clip.awards).joinedload(Award.user)
    ).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Przygotowanie listy nagród
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
        has_webp_thumbnail=clip.thumbnail_webp_path is not None,
        awards=awards_info,
        thumbnail_url=f"/api/files/thumbnails/{clip.id}" if clip.thumbnail_path else None,
        thumbnail_webp_url=f"/api/files/thumbnails/{clip.id}" if clip.thumbnail_webp_path else None,
        download_url=f"/api/files/download/{clip.id}"
    )


# ============================================================================
# DOWNLOAD ENDPOINTS
# ============================================================================

@router.get("/download/{clip_id}")
async def download_clip(
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_flexible)
):
    """
    Pobieranie pojedynczego pliku

    **Autoryzacja:**
    - Token JWT (preferred)
    - Query param token (fallback)

    **Returns:**
    - FileResponse z odpowiednim Content-Type
    - Accept-Ranges dla video streaming
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    if not can_access_clip(clip, current_user):
        raise AuthorizationError(
            message="Nie masz uprawnień do pobrania tego pliku"
        )

    file_path = Path(clip.file_path)

    if not file_path.exists():
        raise StorageError(
            message="Plik nie został znaleziony",
            path=str(file_path),
            status_code=status.HTTP_404_NOT_FOUND
        )

    media_type = "video/mp4" if clip.clip_type == ClipType.VIDEO else "image/png"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=clip.filename,
        headers={
            "Content-Disposition": f'attachment; filename="{clip.filename}"',
            "Accept-Ranges": "bytes"
        }
    )


@router.post("/download-bulk")
async def download_bulk(
        request: BulkDownloadRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Bulk download - pobieranie wielu klipów jako ZIP

    **Limity:**
    - Max 50 klipów na raz
    - Max 1GB total size

    **Returns:**
    - StreamingResponse z archiwum ZIP
    """
    clip_ids = request.clip_ids

    if len(clip_ids) > 50:
        raise ValidationError(
            message="Zbyt wiele plików - maksymalnie 50 naraz",
            field="clip_ids"
        )

    # Pobranie klipów
    clips = db.query(Clip).filter(
        Clip.id.in_(clip_ids),
        Clip.is_deleted == False
    ).all()

    if not clips:
        raise NotFoundError(resource="Klipy", resource_id=None)

    # Sprawdzenie uprawnień
    accessible_clips = [
        clip for clip in clips
        if can_access_clip(clip, current_user)
    ]

    if not accessible_clips:
        raise AuthorizationError(
            message="Nie masz dostępu do żadnego z wybranych plików"
        )

    # Sprawdzenie istnienia plików i rozmiaru
    existing_clips = []
    total_size = 0

    for clip in accessible_clips:
        file_path = Path(clip.file_path)
        if file_path.exists():
            existing_clips.append(clip)
            total_size += clip.file_size

    if not existing_clips:
        raise StorageError(
            message="Żaden z plików nie został znaleziony na dysku"
        )

    # Limit rozmiaru (1GB)
    MAX_TOTAL_SIZE = 1 * 1024 * 1024 * 1024
    if total_size > MAX_TOTAL_SIZE:
        raise ValidationError(
            message=f"Całkowity rozmiar przekracza limit: {total_size / (1024 ** 3):.2f}GB"
        )

    # Generator ZIP
    async def zip_generator():
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for clip in existing_clips:
                try:
                    zip_file.write(
                        Path(clip.file_path),
                        arcname=f"{clip.id}_{clip.filename}"
                    )
                except OSError as e:
                    logger.error(f"Failed to add file to ZIP: {e}")

        buffer.seek(0)
        while True:
            chunk = buffer.read(8192)
            if not chunk:
                break
            yield chunk

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        zip_generator(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="tamteklipy_{timestamp}.zip"'
        }
    )


# ============================================================================
# BULK ACTIONS
# ============================================================================

@router.post("/clips/bulk-action", response_model=BulkActionResponse)
async def bulk_action(
        request: BulkActionRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Masowa operacja na klipach

    **Dostępne akcje:**
    - **delete**: usuń zaznaczone klipy (soft delete)
    - **add-tags**: dodaj tagi (TODO)
    - **add-to-session**: dodaj do sesji (TODO)

    **Limity:**
    - Max 100 klipów na raz
    - Max 10 tagów
    - Tylko właściciel lub admin może usuwać
    """
    if not request.clip_ids:
        raise ValidationError(
            message="Nie wybrano żadnych klipów",
            field="clip_ids"
        )

    if len(request.clip_ids) > 100:
        raise ValidationError(
            message="Zbyt wiele klipów - maksymalnie 100 na raz",
            field="clip_ids",
            details={"provided": len(request.clip_ids), "max": 100}
        )

    logger.info(
        f"Bulk action: {request.action} on {len(request.clip_ids)} clips "
        f"by user {current_user.username}"
    )

    # Routing do odpowiedniej akcji
    if request.action == BulkActionType.DELETE:
        result = await bulk_action_delete(request.clip_ids, db, current_user)
        message = f"Usunięto {result['processed']} klipów"

    elif request.action == BulkActionType.ADD_TAGS:
        if not request.tags:
            raise ValidationError(
                message="Nie podano tagów do dodania",
                field="tags"
            )
        result = await bulk_action_add_tags(
            request.clip_ids
        )
        message = f"Dodano tagi do {result['processed']} klipów"

    elif request.action == BulkActionType.ADD_TO_SESSION:
        if not request.session_name:
            raise ValidationError(
                message="Nie podano nazwy sesji",
                field="session_name"
            )
        result = await bulk_action_add_to_session(
            request.clip_ids,
        )
        message = f"Dodano {result['processed']} klipów do sesji"

    else:
        raise ValidationError(
            message=f"Nieznana akcja: {request.action}",
            field="action",
            details={
                "provided": request.action,
                "allowed": [a.value for a in BulkActionType]
            }
        )

    # Przygotowanie odpowiedzi
    success = result['failed'] == 0

    if not success and result['processed'] == 0:
        message = "Nie udało się przetworzyć żadnego klipu"
    elif result['failed'] > 0:
        message += f" (błędów: {result['failed']})"

    return BulkActionResponse(
        success=success,
        action=request.action.value,
        processed=result['processed'],
        failed=result['failed'],
        message=message,
        details={
            "errors": result.get('errors'),
            "total_requested": len(request.clip_ids)
        }
    )


async def bulk_action_delete(
        clip_ids: List[int],
        db: Session,
        current_user: User
) -> dict:
    """
    Masowe usuwanie klipów (soft delete)

    **Uprawnienia:**
    - Właściciel może usunąć swoje klipy
    - Admin może usunąć wszystkie klipy
    """
    processed = 0
    failed = 0
    errors = []

    for clip_id in clip_ids:
        try:
            clip = db.query(Clip).filter(
                Clip.id == clip_id,
                Clip.is_deleted == False
            ).first()

            if not clip:
                failed += 1
                errors.append(f"Klip {clip_id} nie istnieje")
                continue

            # Sprawdzenie uprawnień
            if clip.uploader_id != current_user.id and not current_user.is_admin:
                failed += 1
                errors.append(f"Brak uprawnień do usunięcia klipu {clip_id}")
                continue

            # Soft delete
            clip.is_deleted = True
            processed += 1

        except Exception as e:
            logger.error(f"Failed to delete clip {clip_id}: {e}")
            failed += 1
            errors.append(f"Błąd podczas usuwania klipu {clip_id}: {str(e)}")

    # Commit zmian
    try:
        db.commit()
        logger.info(f"Bulk delete completed: {processed} processed, {failed} failed")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit bulk delete: {e}")
        raise StorageError(
            message="Nie udało się zapisać zmian w bazie danych",
            path="database"
        )

    return {
        "processed": processed,
        "failed": failed,
        "errors": errors if errors else None
    }


async def bulk_action_add_tags(
        clip_ids: List[int]
) -> dict:
    """
    Masowe dodawanie tagów (placeholder - wymaga modelu Tag)

    TODO: Implementacja po dodaniu modelu Tag
    """
    logger.warning("Add tags action not implemented yet")
    return {
        "processed": 0,
        "failed": len(clip_ids),
        "errors": ["Funkcja dodawania tagów nie jest jeszcze zaimplementowana"]
    }


async def bulk_action_add_to_session(
        clip_ids: List[int],
) -> dict:
    """
    Masowe dodawanie do sesji (placeholder - wymaga modelu Session)

    TODO: Implementacja po dodaniu modelu Session
    """
    logger.warning("Add to session action not implemented yet")
    return {
        "processed": 0,
        "failed": len(clip_ids),
        "errors": ["Funkcja dodawania do sesji nie jest jeszcze zaimplementowana"]
    }


# ============================================================================
# THUMBNAIL ENDPOINTS
# ============================================================================

@router.get("/thumbnails/{clip_id}")
async def get_thumbnail(
        clip_id: int,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Pobieranie thumbnail (endpoint publiczny)

    **WebP Support:**
    - Sprawdza Accept header
    - Zwraca WebP jeśli dostępne i wspierane
    - Fallback do JPEG
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    if not clip.thumbnail_path:
        raise NotFoundError(resource="Thumbnail dla klipa", resource_id=clip_id)

    # Sprawdź wsparcie WebP
    accept_header = request.headers.get("accept", "")
    supports_webp = "image/webp" in accept_header

    # Spróbuj zwrócić WebP jeśli wspierane i dostępne
    if supports_webp and clip.thumbnail_webp_path:
        thumbnail_path = Path(clip.thumbnail_webp_path)
        media_type = "image/webp"

        if thumbnail_path.exists():
            return FileResponse(
                path=str(thumbnail_path),
                media_type=media_type,
                headers={"Cache-Control": "public, max-age=3600"}
            )

    # Fallback do JPEG
    thumbnail_path = Path(clip.thumbnail_path)

    if not thumbnail_path.exists():
        raise NotFoundError(resource="Thumbnail dla klipa", resource_id=clip_id)

    return FileResponse(
        path=str(thumbnail_path),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/clips/{clip_id}/thumbnail-status")
async def get_thumbnail_status(
        clip_id: int,
        db: Session = Depends(get_db),
):
    """
    Sprawdzenie statusu generowania thumbnail

    **Użycie:**
    - Polling co 1-2 sekundy po uploaddzie
    - Pokazuj spinner podczas processing
    - Gdy ready=true, odśwież thumbnail

    **Statusy:**
    - pending: Oczekuje na przetworzenie
    - processing: Generowanie w trakcie
    - ready: Thumbnail gotowy
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Określ status
    has_thumbnail = clip.thumbnail_path is not None
    has_webp = clip.thumbnail_webp_path is not None
    has_metadata = clip.duration is not None or clip.width is not None

    if has_thumbnail:
        status = "ready"
        message = "Miniaturka jest gotowa"
    elif has_metadata:
        status = "processing"
        message = "Generowanie miniaturki w trakcie..."
    else:
        status = "pending"
        message = "Oczekuje na przetworzenie"

    return {
        "clip_id": clip_id,
        "status": status,
        "message": message,
        "thumbnail_ready": has_thumbnail,
        "thumbnail_url": f"/api/files/thumbnails/{clip_id}" if has_thumbnail else None,
        "has_webp": has_webp,
        "metadata": {
            "duration": clip.duration,
            "width": clip.width,
            "height": clip.height
        } if has_metadata else None
    }


# ============================================================================
# VIDEO STREAMING ENDPOINT
# ============================================================================

@router.get("/stream/{clip_id}")
async def stream_video(
        clip_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_flexible)
):
    """
    Streaming video z obsługą Range requests (HTTP 206)

    **Range Requests:**
    - Umożliwia seeking w video
    - Oszczędza bandwidth
    - Required dla <video> tag w przeglądarce

    **Headers:**
    - Accept-Ranges: bytes
    - Content-Range: bytes start-end/total
    - Content-Length: chunk size

    **Returns:**
    - 200: Full file (bez Range header)
    - 206: Partial content (z Range header)
    - 416: Range not satisfiable
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False,
        Clip.clip_type == ClipType.VIDEO
    ).first()

    if not clip:
        raise NotFoundError(resource="Video klip", resource_id=clip_id)

    if not can_access_clip(clip, current_user):
        raise AuthorizationError(
            message="Nie masz uprawnień do odtworzenia tego pliku"
        )

    file_path = Path(clip.file_path)

    if not file_path.exists():
        raise StorageError(
            message="Plik nie został znaleziony",
            path=str(file_path),
            status_code=status.HTTP_404_NOT_FOUND
        )

    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    # Jeśli brak Range header, zwróć cały plik
    if not range_header:
        return FileResponse(
            path=str(file_path),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
                "Cache-Control": "public, max-age=3600"
            }
        )

    # Parsowanie Range header
    try:
        range_str = range_header.replace("bytes=", "")
        start_str, end_str = range_str.split("-")

        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1

        # Walidacja zakresu
        if start >= file_size or end >= file_size or start > end:
            raise ValueError("Invalid range")

        chunk_size = end - start + 1

    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid Range header: {range_header}")
        raise ValidationError(
            message="Nieprawidłowy header Range",
            field="Range",
            details={"range": range_header, "error": str(e)}
        )

    # Generator dla streaming
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

    # Zwróć partial content (HTTP 206)
    return StreamingResponse(
        file_iterator(),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(chunk_size),
            "Cache-Control": "public, max-age=3600"
        }
    )


# ============================================================================
# HEALTH CHECK & DIAGNOSTICS
# ============================================================================

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint dla monitorowania

    **Sprawdza:**
    - Połączenie z bazą danych
    - Dostępność storage directories
    - Podstawowe statystyki

    **Returns:**
    - 200: System działa prawidłowo
    - 503: System ma problemy
    """
    try:
        # Sprawdź połączenie z bazą
        total_clips = db.query(Clip).filter(Clip.is_deleted == False).count()

        # Sprawdź storage directories
        from app.services.file_processor import get_storage_directory
        video_dir = get_storage_directory(ClipType.VIDEO)
        screenshot_dir = get_storage_directory(ClipType.SCREENSHOT)

        storage_ok = video_dir.exists() and screenshot_dir.exists()

        # Sprawdź dostępne miejsce
        import shutil
        video_space = shutil.disk_usage(video_dir)
        free_gb = video_space.free / (1024 ** 3)

        return {
            "status": "healthy",
            "database": "connected",
            "storage": "available" if storage_ok else "unavailable",
            "total_clips": total_clips,
            "free_space_gb": round(free_gb, 2),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# ADMIN ENDPOINTS (Optional)
# ============================================================================

@router.delete("/clips/{clip_id}/hard-delete")
async def hard_delete_clip(
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Hard delete - trwałe usunięcie klipu i pliku z dysku

    **Uwaga:** Ta operacja jest nieodwracalna!

    **Uprawnienia:** Tylko admin

    **Usuwa:**
    - Rekord z bazy danych
    - Plik wideo/screenshot
    - Thumbnail (JPEG i WebP)
    - Wszystkie powiązane nagrody
    """
    if not current_user.is_admin:
        raise AuthorizationError(
            message="Tylko admin może wykonać hard delete"
        )

    clip = db.query(Clip).filter(Clip.id == clip_id).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    files_to_delete = []

    # Zbierz ścieżki do plików
    if clip.file_path:
        files_to_delete.append(Path(clip.file_path))
    if clip.thumbnail_path:
        files_to_delete.append(Path(clip.thumbnail_path))
    if clip.thumbnail_webp_path:
        files_to_delete.append(Path(clip.thumbnail_webp_path))

    # Usuń pliki z dysku
    deleted_files = []
    failed_files = []

    for file_path in files_to_delete:
        try:
            if file_path.exists():
                file_path.unlink()
                deleted_files.append(str(file_path))
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            failed_files.append(str(file_path))

    # Usuń rekord z bazy (cascade usuwa też awards)
    try:
        db.delete(clip)
        db.commit()
        logger.info(f"Hard deleted clip {clip_id} by {current_user.username}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete clip from database: {e}")
        raise StorageError(
            message="Nie udało się usunąć klipu z bazy danych",
            path="database"
        )

    return {
        "message": f"Klip {clip_id} został trwale usunięty",
        "clip_id": clip_id,
        "deleted_files": deleted_files,
        "failed_files": failed_files if failed_files else None
    }


@router.post("/clips/{clip_id}/regenerate-thumbnail")
async def regenerate_thumbnail(
        clip_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Regeneracja thumbnail dla klipa

    **Użycie:**
    - Gdy thumbnail się nie wygenerował
    - Gdy thumbnail jest uszkodzony
    - Gdy chcesz zaktualizować miniaturkę

    **Uprawnienia:** Właściciel lub admin
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Sprawdź uprawnienia
    if clip.uploader_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError(
            message="Nie masz uprawnień do regeneracji thumbnail"
        )

    # Usuń stare thumbnails
    if clip.thumbnail_path:
        try:
            Path(clip.thumbnail_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to delete old thumbnail: {e}")

    if clip.thumbnail_webp_path:
        try:
            Path(clip.thumbnail_webp_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to delete old WebP thumbnail: {e}")

    # Wyczyść thumbnail paths w bazie
    clip.thumbnail_path = None
    clip.thumbnail_webp_path = None
    db.commit()

    # Zakolejkuj nowe generowanie
    background_tasks.add_task(
        process_thumbnail_background,
        clip_id=clip.id,
        file_path=str(clip.file_path),
        clip_type=clip.clip_type
    )

    logger.info(f"Thumbnail regeneration queued for clip {clip_id}")

    return {
        "message": "Regeneracja thumbnail została zakolejkowana",
        "clip_id": clip_id,
        "status": "processing"
    }


@router.post("/clips/{clip_id}/generate-thumbnail")
async def generate_thumbnail_on_demand(
        clip_id: int,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db),
):
    """
    Generuje thumbnail on-demand dla klipa który go nie ma.
    Używane gdy user ogląda klip pierwszy raz.
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Jeśli już ma thumbnail, nie generuj ponownie
    if clip.thumbnail_path:
        return {
            "message": "Thumbnail already exists",
            "thumbnail_url": f"/api/files/thumbnails/{clip_id}"
        }

    # Zakolejkuj generowanie w tle
    background_tasks.add_task(
        process_thumbnail_background,
        clip_id=clip.id,
        file_path=str(clip.file_path),
        clip_type=clip.clip_type
    )

    return {
        "message": "Thumbnail generation started",
        "clip_id": clip_id,
        "status": "processing"
    }
