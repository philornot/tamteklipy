"""
Router dla zarządzania plikami - upload, download, listowanie klipów i screenshotów
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status

router = APIRouter()


@router.get("/clips")
async def list_clips(skip: int = 0, limit: int = 50):
    """
    Listowanie klipów z paginacją
    GET /api/files/clips?skip=0&limit=50
    """
    # TODO: Implementacja po dodaniu bazy danych
    # 1. Pobierz klipy z bazy
    # 2. Zastosuj paginację
    # 3. Zwróć listę klipów z metadanymi

    return {
        "clips": [],
        "total": 0,
        "skip": skip,
        "limit": limit,
        "message": "Implementacja wkrótce"
    }


@router.get("/clips/{clip_id}")
async def get_clip(clip_id: int):
    """
    Pobierz szczegóły pojedynczego klipa
    GET /api/files/clips/{clip_id}
    """
    # TODO: Implementacja po dodaniu bazy danych

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Klip {clip_id} nie znaleziony (endpoint w budowie)"
    )


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload pliku (klip lub screenshot)
    POST /api/files/upload
    Body: multipart/form-data z plikiem
    """
    # TODO: Implementacja po dodaniu storage service
    # 1. Waliduj typ pliku (video/image)
    # 2. Zapisz na dysku (/mnt/tamteklipy)
    # 3. Wygeneruj thumbnail (jeśli video)
    # 4. Zapisz metadane w bazie
    # 5. Zwróć info o uploadowanym pliku

    return {
        "message": "Upload endpoint - implementacja wkrótce",
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "not_implemented"
    }


@router.delete("/clips/{clip_id}")
async def delete_clip(clip_id: int):
    """
    Usuń klip
    DELETE /api/files/clips/{clip_id}
    """
    # TODO: Implementacja po dodaniu bazy danych
    # 1. Sprawdź uprawnienia użytkownika
    # 2. Usuń plik z dysku
    # 3. Usuń z bazy danych

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Usuwanie będzie dostępne wkrótce"
    )


@router.get("/download/{clip_id}")
async def download_clip(clip_id: int):
    """
    Pobierz plik klipa
    GET /api/files/download/{clip_id}
    """
    # TODO: Implementacja po dodaniu storage
    # 1. Pobierz ścieżkę do pliku z bazy
    # 2. Zwróć plik używając FileResponse

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Plik nie znaleziony (endpoint w budowie)"
    )


@router.get("/thumbnails/{clip_id}")
async def get_thumbnail(clip_id: int):
    """
    Pobierz miniaturę klipa
    GET /api/files/thumbnails/{clip_id}
    """
    # TODO: Implementacja po dodaniu thumbnail service

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Miniatura nie znaleziona (endpoint w budowie)"
    )
