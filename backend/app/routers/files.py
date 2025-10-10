"""
Router dla zarządzania plikami
Tylko endpointy, logika w services
"""
import io
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiofiles
from app.core.cache import cache_key_builder
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
from app.services.file_processor import (
    save_file_to_disk, generate_thumbnails_sync,
    create_clip_record, invalidate_clips_cache
)
from app.services.file_validator import (
    validate_file_type, validate_file_size,
    generate_unique_filename, check_disk_space
)
from app.utils.file_helpers import can_access_clip
from fastapi import APIRouter, UploadFile, File, Depends, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi_cache.decorator import cache
from pydantic import BaseModel, Field
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Upload pliku
    """
    logger.info(f"Upload from {current_user.username}: {file.filename} ({file.content_type})")

    try:
        # 1. Waliduj typ
        clip_type, extension = validate_file_type(file.content_type)

        # 2. Przeczytaj plik
        file_content = await file.read()
        file_size = len(file_content)

        # 3. Waliduj rozmiar
        validate_file_size(file_size, clip_type)

        # 4. Wygeneruj nazwę
        unique_filename = generate_unique_filename(file.filename, extension)

        # 5. Sprawdź miejsce
        from app.services.file_processor import get_storage_directory
        storage_dir = get_storage_directory(clip_type)
        check_disk_space(storage_dir, file_size)

        # 6. Zapisz plik
        file_path = await save_file_to_disk(file_content, unique_filename, clip_type)

        # 7. Generuj thumbnail
        thumbnail_path, thumbnail_webp_path, metadata = generate_thumbnails_sync(
            file_path, clip_type
        )

        # 8. Zapisz do bazy
        new_clip = await create_clip_record(
            db=db,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            clip_type=clip_type,
            uploader_id=current_user.id,
            thumbnail_path=thumbnail_path,
            thumbnail_webp_path=thumbnail_webp_path,
            metadata=metadata
        )

        # 9. Invaliduj cache
        await invalidate_clips_cache()

        # 10. Zwróć response
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
            response["webp_generated"] = thumbnail_webp_path is not None

        if metadata:
            response["duration"] = metadata.get("duration")
            response["resolution"] = f"{metadata.get('width')}x{metadata.get('height')}"

        return response

    except (ValidationError, FileUploadError, StorageError):
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
@cache(expire=30, key_builder=cache_key_builder)
async def list_clips(
        request: Request,
        response: Response,
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
    """

    # Walidacja parametrów
    page = max(1, page)
    limit = min(max(1, limit), 100)
    offset = (page - 1) * limit

    # Query z optymalizacją
    query = db.query(Clip).options(
        selectinload(Clip.awards).selectinload(Award.user)
    ).filter(Clip.is_deleted == False)

    # Filtrowanie
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
    query = query.order_by(asc(sort_field) if sort_order.lower() == "asc" else desc(sort_field))

    # Paginacja
    total = query.count()
    clips = query.offset(offset).limit(limit).all()

    # Pobierz AwardTypes
    all_award_names = {award.award_name for clip in clips for award in clip.awards}
    award_types = db.query(AwardType).filter(AwardType.name.in_(all_award_names)).all() if all_award_names else []
    award_types_map = {at.name: at for at in award_types}

    # Konwertuj do response
    clips_response = []
    for clip in clips:
        award_counts = {}
        for award in clip.awards:
            award_counts[award.award_name] = award_counts.get(award.award_name, 0) + 1

        award_icons = []
        for award_name, count in award_counts.items():
            award_type = award_types_map.get(award_name)
            icon_url = f"/api/admin/award-types/{award_type.id}/icon" if (
                    award_type and award_type.custom_icon_path) else None

            award_icons.append({
                "award_name": award_name,
                "icon_url": icon_url,
                "icon": award_type.icon if award_type else "🏆",
                "lucide_icon": award_type.lucide_icon if award_type else None,
                "count": count
            })

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
            has_thumbnail=clip.thumbnail_path is not None,
            has_webp_thumbnail=clip.thumbnail_webp_path is not None,
            award_icons=award_icons
        ))

    pages = (total + limit - 1) // limit

    # HTTP/2 Server Push
    if clips_response:
        link_headers = []
        for clip_resp in clips_response[:5]:
            if clip_resp.has_thumbnail:
                thumbnail_url = f"/api/files/thumbnails/{clip_resp.id}"
                img_type = "image/webp" if clip_resp.has_webp_thumbnail else "image/jpeg"
                link_headers.append(f'<{thumbnail_url}>; rel=preload; as=image; type={img_type}')

        if link_headers:
            response.headers["Link"] = ", ".join(link_headers)

    return ClipListResponse(
        clips=clips_response,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/clips/{clip_id}", response_model=ClipDetailResponse)
@cache(expire=300, key_builder=cache_key_builder)
async def get_clip(
        request: Request,
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Szczegóły klipa - bez zmian"""
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


@router.get("/download/{clip_id}")
async def download_clip(
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_flexible)
):
    """Pobierz plik - bez zmian"""
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    if not can_access_clip(clip, current_user):
        raise AuthorizationError(message="Nie masz uprawnień do pobrania tego pliku")

    file_path = Path(clip.file_path)
    if not file_path.exists():
        raise StorageError(message="Plik nie został znaleziony", path=str(file_path))

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


class BulkDownloadRequest(BaseModel):
    clip_ids: List[int] = Field(..., min_length=1, max_length=50)


@router.post("/download-bulk")
async def download_bulk(
        request: BulkDownloadRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Bulk download - bez zmian (za długi, ale prosty)"""
    clip_ids = request.clip_ids

    if len(clip_ids) > 50:
        raise ValidationError(message="Zbyt wiele plików - maksymalnie 50 naraz", field="clip_ids")

    clips = db.query(Clip).filter(Clip.id.in_(clip_ids), Clip.is_deleted == False).all()

    if not clips:
        raise NotFoundError(resource="Klipy", resource_id=None)

    accessible_clips = [clip for clip in clips if can_access_clip(clip, current_user)]

    if not accessible_clips:
        raise AuthorizationError(message="Nie masz dostępu do żadnego z wybranych plików")

    existing_clips = []
    total_size = 0

    for clip in accessible_clips:
        file_path = Path(clip.file_path)
        if file_path.exists():
            existing_clips.append(clip)
            total_size += clip.file_size

    if not existing_clips:
        raise StorageError(message="Żaden z plików nie został znaleziony na dysku")

    MAX_TOTAL_SIZE = 1 * 1024 * 1024 * 1024
    if total_size > MAX_TOTAL_SIZE:
        raise ValidationError(message=f"Całkowity rozmiar przekracza limit: {total_size / (1024 ** 3):.2f}GB")

    async def zip_generator():
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for clip in existing_clips:
                try:
                    zip_file.write(Path(clip.file_path), arcname=f"{clip.id}_{clip.filename}")
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
        headers={"Content-Disposition": f'attachment; filename="tamteklipy_{timestamp}.zip"'}
    )


@router.get("/thumbnails/{clip_id}")
async def get_thumbnail(
        clip_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_flexible)
):
    """Pobierz thumbnail - bez zmian"""
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    if not clip.thumbnail_path:
        raise NotFoundError(resource="Thumbnail dla klipa", resource_id=clip_id)

    # Sprawdź WebP support
    accept_header = request.headers.get("accept", "")
    supports_webp = "image/webp" in accept_header

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
        raise StorageError(message="Thumbnail nie został znaleziony", path=str(thumbnail_path))

    return FileResponse(
        path=str(thumbnail_path),
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/stream/{clip_id}")
async def stream_video(
        clip_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user_flexible)
):
    """Stream video z Range requests - bez zmian"""
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False,
        Clip.clip_type == ClipType.VIDEO
    ).first()

    if not clip:
        raise NotFoundError(resource="Video klip", resource_id=clip_id)

    file_path = Path(clip.file_path)

    if not file_path.exists():
        raise StorageError(message="Plik nie został znaleziony", path=str(file_path))

    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(
            path=str(file_path),
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size)
            }
        )

    try:
        range_str = range_header.replace("bytes=", "")
        start_str, end_str = range_str.split("-")

        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1

        if start >= file_size or end >= file_size or start > end:
            raise ValueError("Invalid range")

        chunk_size = end - start + 1

    except (ValueError, AttributeError):
        raise ValidationError(
            message="Nieprawidłowy header Range",
            field="Range",
            details={"range": range_header}
        )

    async def file_iterator():
        async with aiofiles.open(file_path, mode='rb') as f:
            await f.seek(start)
            remaining = chunk_size

            while remaining > 0:
                read_size = min(8192, remaining)
                data = await f.read(read_size)

                if not data:
                    break

                remaining -= len(data)
                yield data

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
