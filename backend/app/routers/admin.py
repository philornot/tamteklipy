from datetime import datetime
from pathlib import Path

from fastapi import UploadFile, File


@router.post("/award-types/{award_type_id}/icon")
async def upload_award_icon(
        award_type_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Upload ikony dla typu nagrody (hybrid: frontend już zresizował)
    POST /api/admin/award-types/{award_type_id}/icon
    """
    # 1. Znajdź award type
    award_type = db.query(AwardType).filter(AwardType.id == award_type_id).first()
    if not award_type:
        raise NotFoundError(resource="AwardType", resource_id=award_type_id)

    # 2. Waliduj format
    if file.content_type not in ['image/png', 'image/jpeg']:
        raise ValidationError(
            message="Tylko PNG i JPG są dozwolone",
            field="file",
            details={"received": file.content_type}
        )

    # 3. Przeczytaj plik
    content = await file.read()
    file_size = len(content)

    # 4. Waliduj rozmiar (max 500KB - już zresizowany z frontu)
    if file_size > 500 * 1024:
        raise ValidationError(
            message="Plik za duży (max 500KB)",
            field="file",
            details={"size": file_size}
        )

    # 5. Opcjonalna walidacja wymiarów (możesz użyć PIL.Image ale tylko do sprawdzenia)
    from PIL import Image
    from io import BytesIO
    try:
        img = Image.open(BytesIO(content))
        width, height = img.size

        # Tolerance ±10px
        if not (118 <= width <= 138 and 118 <= height <= 138):
            raise ValidationError(
                message=f"Nieprawidłowe wymiary: {width}x{height}px (oczekiwano ~128x128px)",
                field="file",
                details={"width": width, "height": height}
            )
    except Exception as e:
        raise ValidationError(
            message="Nie można odczytać obrazka",
            field="file"
        )

    # 6. Określ ścieżkę zapisu
    icons_dir = Path(settings.award_icons_path)
    if settings.environment == "development":
        icons_dir = Path("uploads/award_icons")

    icons_dir.mkdir(parents=True, exist_ok=True)

    # Nazwa: {award_type_id}_{timestamp}.png
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = ".png" if file.content_type == "image/png" else ".jpg"
    filename = f"{award_type_id}_{timestamp}{extension}"
    file_path = icons_dir / filename

    # 7. Usuń starą ikonę jeśli istnieje
    if award_type.icon_path:
        old_path = Path(award_type.icon_path)
        if old_path.exists():
            try:
                old_path.unlink()
            except:
                pass

    # 8. Zapisz nowy plik
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save icon: {e}")
        raise StorageError(message="Nie można zapisać ikony", path=str(file_path))

    # 9. Update w bazie
    award_type.icon_path = str(file_path)
    db.commit()

    logger.info(f"Icon uploaded for AwardType {award_type_id}: {file_path}")

    return {
        "message": "Ikona uploaded",
        "icon_url": f"/api/admin/award-types/{award_type_id}/icon"
    }
