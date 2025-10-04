"""
Router dla admina – zarządzanie systemem
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, DuplicateError, AuthorizationError, DatabaseError, ValidationError, \
    StorageError
from app.models.award_type import AwardType
from app.models.user import User
from fastapi import APIRouter, Depends, status, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


class AwardTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    icon: str = Field(default="🏆", max_length=50)
    color: str = Field(default="#FFD700", pattern="^#[0-9A-Fa-f]{6}$")


class AwardTypeResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str
    icon: str
    color: str

    class Config:
        from_attributes = True


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency do sprawdzania uprawnień admina"""
    if not current_user.is_admin:
        raise AuthorizationError(message="Wymagane uprawnienia administratora")
    return current_user


@router.get("/award-types", response_model=List[AwardTypeResponse])
async def get_award_types(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz wszystkie typy nagród
    GET /api/admin/award-types
    """
    award_types = db.query(AwardType).all()
    return award_types


@router.post("/award-types", response_model=AwardTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_award_type(
        award_type_data: AwardTypeCreate,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Utwórz nowy typ nagrody (admin only)
    POST /api/admin/award-types
    """
    # Sprawdź duplikaty
    existing = db.query(AwardType).filter(AwardType.name == award_type_data.name).first()
    if existing:
        raise DuplicateError(
            resource="AwardType",
            field="name",
            value=award_type_data.name
        )

    new_award_type = AwardType(**award_type_data.model_dump())

    try:
        db.add(new_award_type)
        db.commit()
        db.refresh(new_award_type)
        logger.info(f"AwardType created: {new_award_type.name} by {admin_user.username}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create AwardType: {e}")
        raise DatabaseError(message="Nie można utworzyć typu nagrody", operation="create_award_type")

    return new_award_type


@router.post("/award-types/{award_type_id}/icon")
async def upload_award_icon(
        award_type_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Upload ikony dla typu nagrody
    POST /api/admin/award-types/{award_type_id}/icon

    Każdy użytkownik może uploadować ikonę do swoich własnych custom nagród.
    Admin może do wszystkich.
    """
    award_type = db.query(AwardType).filter(AwardType.id == award_type_id).first()
    if not award_type:
        raise NotFoundError(resource="AwardType", resource_id=award_type_id)

    # Sprawdź uprawnienia
    if not current_user.is_admin:
        # Nie-admin może tylko do swoich własnych nagród
        if award_type.created_by_user_id != current_user.id:
            raise AuthorizationError(message="Możesz uploadować ikony tylko do swoich własnych nagród")

        # Nie można modyfikować systemowych ani osobistych
        if award_type.is_system_award or award_type.is_personal:
            raise AuthorizationError(message="Nie można uploadować ikon do systemowych ani osobistych nagród")

    # Walidacja typu pliku
    if file.content_type not in ['image/png', 'image/jpeg', 'image/webp']:
        raise ValidationError(
            message="Tylko PNG, JPG i WebP są dozwolone",
            field="file",
            details={"received": file.content_type}
        )

    # Walidacja rozmiaru
    content = await file.read()
    file_size = len(content)
    max_size = 500 * 1024  # 500KB

    if file_size > max_size:
        raise ValidationError(
            message=f"Plik za duży (max {max_size // 1024}KB)",
            field="file",
            details={"size": file_size, "max_size": max_size}
        )

    # Minimalna walidacja - plik musi zaczynać się od magic bytes
    if content[:8] not in [
        b'\x89PNG\r\n\x1a\n',  # PNG
        b'\xff\xd8\xff',  # JPEG (pierwsze 3 bajty)
        b'RIFF',  # WebP (RIFF container)
    ]:
        # Sprawdź JPEG dokładniej
        if not content[:2] == b'\xff\xd8':
            raise ValidationError(
                message="Nieprawidłowy format pliku",
                field="file"
            )

    # Katalog na ikony
    icons_dir = Path(settings.award_icons_path)
    if getattr(settings, "environment", "production") == "development":
        icons_dir = Path("uploads/award_icons")

    icons_dir.mkdir(parents=True, exist_ok=True)

    # Generuj nazwę pliku
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp"
    }.get(file.content_type, ".png")

    filename = f"award_{award_type_id}_{timestamp}{extension}"
    file_path = icons_dir / filename

    # Usuń starą ikonę jeśli istnieje
    if award_type.custom_icon_path:
        old_path = Path(award_type.custom_icon_path)
        if old_path.exists():
            try:
                old_path.unlink()
                logger.info(f"Deleted old icon: {old_path}")
            except Exception as e:
                logger.warning(f"Could not delete old icon: {e}")

    # Zapisz nowy plik
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save icon: {e}")
        raise StorageError(message="Nie można zapisać ikony", path=str(file_path))

    # Zaktualizuj w bazie
    award_type.custom_icon_path = str(file_path)
    award_type.lucide_icon = None  # Wyczyść lucide icon jeśli była

    try:
        db.commit()
    except Exception as e:
        # Jeśli commit fail, usuń plik
        try:
            file_path.unlink()
        except:
            pass
        db.rollback()
        raise DatabaseError(message="Nie można zaktualizować typu nagrody")

    logger.info(f"Icon uploaded for AwardType {award_type_id} by {current_user.username}: {file_path}")

    return {
        "message": "Ikona uploaded",
        "icon_url": f"/api/admin/award-types/{award_type_id}/icon",
        "filename": filename
    }


@router.get("/award-types/{award_type_id}/icon")
async def get_award_icon(
        award_type_id: int,
        db: Session = Depends(get_db)
):
    """
    Pobierz ikonę typu nagrody
    GET /api/admin/award-types/{award_type_id}/icon
    """
    award_type = db.query(AwardType).filter(AwardType.id == award_type_id).first()
    if not award_type or not award_type.custom_icon_path:
        raise NotFoundError(resource="Icon", resource_id=award_type_id)

    icon_path = Path(award_type.custom_icon_path)
    if not icon_path.exists():
        logger.error(f"Icon file not found: {icon_path}")
        raise NotFoundError(resource="Icon file", resource_id=award_type_id)

    # Określ media type na podstawie rozszerzenia
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp"
    }.get(icon_path.suffix.lower(), "image/png")

    return FileResponse(
        path=str(icon_path),
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=86400"
        }
    )


@router.get("/users")
async def get_all_users(
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Lista wszystkich użytkowników (admin only)
    GET /api/admin/users
    """
    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "award_scopes": u.award_scopes or []
        }
        for u in users
    ]
