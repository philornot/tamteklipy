"""
Router dla chunked upload - upload dużych plików w kawałkach
UŻYWA NOWYCH MODUŁÓW z refaktoryzacji
"""
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional

import aiofiles
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.clip import ClipType
from app.models.user import User
from app.services.background_tasks import process_thumbnail_background
from app.services.file_processor import (
    get_storage_directory,
    create_clip_record,
    invalidate_clips_cache
)
# Importy z nowych modułów
from app.services.file_validator import validate_file_type, guess_content_type, generate_unique_filename
from fastapi import APIRouter, UploadFile, File, Depends, Form, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter()

# Katalog na tymczasowe chunki
CHUNKS_DIR = Path(settings.storage_path) / "chunks"
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


class ChunkUploadResponse(BaseModel):
    upload_id: str
    chunk_number: int
    total_chunks: int
    received: bool
    complete: bool = False
    clip_id: Optional[int] = None
    message: str = "Chunk received"


class UploadStatusResponse(BaseModel):
    upload_id: str
    chunks_received: int
    total_chunks: int
    complete: bool
    clip_id: Optional[int] = None


@router.post("/upload-chunk", response_model=ChunkUploadResponse)
async def upload_chunk(
        background_tasks: BackgroundTasks,
        chunk: UploadFile = File(...),
        upload_id: str = Form(...),
        chunk_number: int = Form(...),
        total_chunks: int = Form(...),
        filename: str = Form(...),
        file_hash: Optional[str] = Form(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Upload pojedynczego chunku

    Workflow:
    1. Frontend dzieli plik na chunki (5MB każdy)
    2. Wysyła każdy chunk z metadanymi
    3. Backend zapisuje do temp
    4. Po ostatnim - składa i przetwarza
    """

    # Katalog dla tego uploadu
    upload_dir = CHUNKS_DIR / upload_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Zapisz chunk
    chunk_path = upload_dir / f"chunk_{chunk_number:04d}"

    try:
        content = await chunk.read()

        async with aiofiles.open(chunk_path, "wb") as f:
            await f.write(content)

        logger.info(f"✅ Chunk {chunk_number + 1}/{total_chunks} saved for {upload_id}")

        # Sprawdź czy wszystkie chunki są
        received_chunks = sorted(upload_dir.glob("chunk_*"))
        is_complete = len(received_chunks) == total_chunks

        response = ChunkUploadResponse(
            upload_id=upload_id,
            chunk_number=chunk_number,
            total_chunks=total_chunks,
            received=True,
            complete=is_complete
        )

        # Jeśli ostatni chunk - złóż plik
        if is_complete:
            logger.info(f"🎉 All chunks received for {upload_id}, assembling...")

            clip_id = await assemble_and_process_file(
                upload_dir=upload_dir,
                filename=filename,
                file_hash=file_hash,
                user_id=current_user.id,
                db=db,
                background_tasks=background_tasks
            )

            response.clip_id = clip_id
            response.message = "Upload complete and processed"

            logger.info(f"✨ Upload complete! Clip ID: {clip_id}")

        return response

    except Exception as e:
        logger.error(f"❌ Chunk upload failed: {e}")

        # Cleanup przy błędzie
        if chunk_path.exists():
            chunk_path.unlink()

        raise


async def assemble_and_process_file(
        upload_dir: Path,
        filename: str,
        file_hash: Optional[str],
        user_id: int,
        db: Session,
        background_tasks: BackgroundTasks
) -> int:
    """
    Składa chunki w jeden plik, weryfikuje i zapisuje do bazy
    Thumbnail generuje w tle przez BackgroundTasks

    UŻYWA NOWYCH SERVICE LAYER FUNCTIONS
    """

    # Pobierz wszystkie chunki
    chunks = sorted(upload_dir.glob("chunk_*"))

    if not chunks:
        raise ValueError("No chunks found")

    # Wykryj typ pliku
    content_type = guess_content_type(filename)
    clip_type, extension = validate_file_type(filename, content_type)

    # Wygeneruj unikalną nazwę
    unique_filename = generate_unique_filename(filename, extension)

    # Katalog docelowy (używa funkcji z file_processor)
    storage_dir = get_storage_directory(clip_type)
    storage_dir.mkdir(parents=True, exist_ok=True)
    final_path = storage_dir / unique_filename

    # Złóż chunki i oblicz hash
    hasher = hashlib.sha256()
    total_size = 0

    logger.info(f"📦 Assembling {len(chunks)} chunks into {final_path}")

    async with aiofiles.open(final_path, "wb") as outfile:
        for chunk_path in chunks:
            async with aiofiles.open(chunk_path, "rb") as infile:
                data = await infile.read()
                await outfile.write(data)
                hasher.update(data)
                total_size += len(data)

    # Weryfikuj hash jeśli podany
    computed_hash = hasher.hexdigest()

    if file_hash and computed_hash != file_hash:
        logger.error(f"❌ Hash mismatch! Expected: {file_hash}, Got: {computed_hash}")
        final_path.unlink()
        raise ValueError("File integrity check failed - hash mismatch")

    logger.info(f"✅ File assembled: {total_size} bytes, hash OK")

    # Zapisz do bazy (BEZ thumbnail - będzie w tle)
    new_clip = await create_clip_record(
        db=db,
        filename=filename,
        file_path=final_path,
        file_size=total_size,
        clip_type=clip_type,
        uploader_id=user_id,
        thumbnail_path=None,  # Będzie uzupełnione w tle
        thumbnail_webp_path=None,
        metadata=None  # Będzie uzupełnione w tle
    )

    logger.info(f"💾 Clip saved to DB: ID={new_clip.id}")

    # Wyczyść chunki
    try:
        shutil.rmtree(upload_dir)
        logger.info(f"🧹 Cleaned up chunks for {upload_dir.name}")
    except OSError as e:
        logger.warning(f"Failed to cleanup chunks: {e}")

    # Zakolejkuj thumbnail w tle (NIE CZEKAJ NA NIEGO!)
    background_tasks.add_task(
        process_thumbnail_background,
        clip_id=new_clip.id,
        file_path=str(final_path),
        clip_type=clip_type
    )

    logger.info(f"🎨 Thumbnail processing queued in background")

    # Invaliduj cache
    await invalidate_clips_cache()

    return new_clip.id


@router.get("/upload-status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
        upload_id: str,
        current_user: User = Depends(get_current_user)
):
    """
    Sprawdź status uploadu (ile chunków otrzymano)
    Przydatne dla wznowienia przerwanego uploadu
    """
    upload_dir = CHUNKS_DIR / upload_id

    if not upload_dir.exists():
        return UploadStatusResponse(
            upload_id=upload_id,
            chunks_received=0,
            total_chunks=0,
            complete=False
        )

    chunks = list(upload_dir.glob("chunk_*"))

    return UploadStatusResponse(
        upload_id=upload_id,
        chunks_received=len(chunks),
        total_chunks=0,  # Nie znamy dopóki nie dostaniemy info z frontendu
        complete=False
    )


@router.delete("/upload-chunk/{upload_id}")
async def cancel_upload(
        upload_id: str,
        current_user: User = Depends(get_current_user)
):
    """
    Anuluj upload i wyczyść chunki
    Przydatne gdy user anuluje upload z UI
    """
    upload_dir = CHUNKS_DIR / upload_id

    if upload_dir.exists():
        try:
            shutil.rmtree(upload_dir)
            logger.info(f"🚫 Upload cancelled: {upload_id}")
            return {"message": "Upload cancelled", "upload_id": upload_id}
        except OSError as e:
            logger.error(f"Failed to cancel upload: {e}")
            raise

    return {"message": "Upload not found", "upload_id": upload_id}
