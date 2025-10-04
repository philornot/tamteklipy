"""
Router dla admina — zarządzanie systemem
"""
import logging
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, DuplicateError, AuthorizationError, DatabaseError
from app.models.award_type import AwardType
from app.models.user import User
from fastapi import APIRouter, Depends, status, File, UploadFile
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
    if "admin" not in (current_user.award_scopes or []):
        raise AuthorizationError(
            message="Wymagane uprawnienia administratora",
            details={"required_scope": "admin"}
        )
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
        admin_user: User = Depends(require_admin)
):
    """
    Upload ikony dla typu nagrody (hybrid: frontend już zresizował)
    POST /api/admin/award-types/{award_type_id}/icon
    """
    award_type = db.query(AwardType).filter(AwardType.id == award_type_id).first()
    if not award_type:
        raise NotFoundError(resource="AwardType", resource_id=award_type_id)

    if file.content_type not in ['image/png', 'image/jpeg']:
        from app.core.exceptions import ValidationError
        raise ValidationError(
            message="Tylko PNG i JPG są dozwolone",
            field="file",
            details={"received": file.content_type}
        )

    content = await file.read()
    file_size = len(content)
    if file_size > 500 * 1024:
        from app.core.exceptions import ValidationError
        raise ValidationError(
            message="Plik za duży (max 500KB)",
            field="file",
            details={"size": file_size}
        )

    from PIL import Image
    from io import BytesIO
    try:
        img = Image.open(BytesIO(content))
        width, height = img.size
        if not (118 <= width <= 138 and 118 <= height <= 138):
            from app.core.exceptions import ValidationError
            raise ValidationError(
                message=f"Nieprawidłowe wymiary: {width}x{height}px (oczekiwano ~128x128px)",
                field="file",
                details={"width": width, "height": height}
            )
    except Exception:
        from app.core.exceptions import ValidationError
        raise ValidationError(
            message="Nie można odczytać obrazka",
            field="file"
        )

    icons_dir = Path(settings.award_icons_path)
    if getattr(settings, "environment", "production") == "development":
        icons_dir = Path("uploads/award_icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extension = ".png" if file.content_type == "image/png" else ".jpg"
    filename = f"{award_type_id}_{timestamp}{extension}"
    file_path = icons_dir / filename

    if getattr(award_type, "icon_path", None):
        old_path = Path(award_type.icon_path)
        if old_path.exists():
            try:
                old_path.unlink()
            except Exception:
                pass

    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        from app.core.exceptions import StorageError
        logger.error(f"Failed to save icon: {e}")
        raise StorageError(message="Nie można zapisać ikony", path=str(file_path))

    award_type.icon_path = str(file_path)
    db.commit()

    logger.info(f"Icon uploaded for AwardType {award_type_id}: {file_path}")

    return {
        "message": "Ikona uploaded",
        "icon_url": f"/api/admin/award-types/{award_type_id}/icon"
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
    if not award_type or not getattr(award_type, "icon_path", None):
        raise NotFoundError(resource="Icon", resource_id=award_type_id)

    icon_path = Path(award_type.icon_path)
    if not icon_path.exists():
        logger.error(f"Icon file not found: {icon_path}")
        raise NotFoundError(resource="Icon file", resource_id=award_type_id)

    media_type = "image/png" if icon_path.suffix == ".png" else "image/jpeg"
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
            "award_scopes": u.award_scopes or []
        }
        for u in users
    ]