"""
Router dla admina – zarządzanie systemem
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, DuplicateError, AuthorizationError, DatabaseError, ValidationError, \
    StorageError
from app.models.award import Award
from app.models.award_type import AwardType
from app.models.clip import Clip
from app.models.user import User
from fastapi import APIRouter, Depends, status, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

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


@router.get("/award-types/detailed")
async def get_award_types_detailed(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz szczegółowe informacje o wszystkich typach nagród
    GET /api/admin/award-types/detailed

    Zwraca pełne info z icon_type, icon_url, uprawnieniami
    """
    award_types = db.query(AwardType).all()

    result = []
    for at in award_types:
        # Określ typ ikony
        if at.custom_icon_path:
            icon_type = "custom"
            icon_url = f"/api/admin/award-types/{at.id}/icon"
        elif at.lucide_icon:
            icon_type = "lucide"
            icon_url = None
        else:
            icon_type = "emoji"
            icon_url = None

        # Pobierz username creatora jeśli istnieje
        created_by_username = None
        if at.created_by_user_id:
            creator = db.query(User).filter(User.id == at.created_by_user_id).first()
            if creator:
                created_by_username = creator.username

        # Sprawdź czy current_user może edytować/usuwać
        can_edit = current_user.is_admin or at.created_by_user_id == current_user.id
        can_delete = can_edit and not at.is_system_award and not at.is_personal

        result.append({
            "id": at.id,
            "name": at.name,
            "display_name": at.display_name,
            "description": at.description,
            "icon": at.icon,
            "lucide_icon": at.lucide_icon,
            "color": at.color,
            "icon_type": icon_type,
            "icon_url": icon_url,
            "is_system_award": at.is_system_award,
            "is_personal": at.is_personal,
            "created_by_user_id": at.created_by_user_id,
            "created_by_username": created_by_username,
            "can_edit": can_edit,
            "can_delete": can_delete,
            "created_at": at.created_at.isoformat(),
            "updated_at": at.updated_at.isoformat()
        })

    return result


class AwardTypeUpdate(BaseModel):
    """Schema do aktualizacji typu nagrody"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    lucide_icon: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_personal: Optional[bool] = None


@router.patch("/award-types/{award_type_id}")
async def update_award_type(
        award_type_id: int,
        update_data: AwardTypeUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Aktualizuj typ nagrody
    PATCH /api/admin/award-types/{award_type_id}

    Uprawnienia:
    - Admin może edytować wszystkie
    - Twórca może edytować tylko swoje (nie-systemowe, nie-personal)
    """
    award_type = db.query(AwardType).filter(AwardType.id == award_type_id).first()

    if not award_type:
        raise NotFoundError(resource="AwardType", resource_id=award_type_id)

    # Sprawdź uprawnienia
    can_edit = current_user.is_admin or (
            award_type.created_by_user_id == current_user.id
            and not award_type.is_system_award
    )

    if not can_edit:
        raise AuthorizationError(
            message="Nie masz uprawnień do edycji tego typu nagrody"
        )

    # Aktualizuj pola
    if update_data.display_name is not None:
        award_type.display_name = update_data.display_name

    if update_data.description is not None:
        award_type.description = update_data.description

    if update_data.icon is not None:
        award_type.icon = update_data.icon

    if update_data.color is not None:
        award_type.color = update_data.color

    # Lucide icon - jeśli ustawiamy na pusty string, wyczyść
    if update_data.lucide_icon is not None:
        if update_data.lucide_icon == "":
            award_type.lucide_icon = None
            # Nie usuwaj custom_icon_path - może być zachowany
        else:
            award_type.lucide_icon = update_data.lucide_icon
            # Przy ustawieniu lucide, NIE usuwamy custom_icon_path
            # Frontend powinien decydować który używać

    # is_personal - tylko admin może zmieniać
    if update_data.is_personal is not None and current_user.is_admin:
        # Nie pozwól na zmianę is_personal dla systemowych nagród
        if not award_type.is_system_award:
            award_type.is_personal = update_data.is_personal

    try:
        db.commit()
        db.refresh(award_type)
        logger.info(
            f"AwardType {award_type_id} updated by {current_user.username}: "
            f"{update_data.model_dump(exclude_none=True)}"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update AwardType: {e}")
        raise DatabaseError(message="Nie można zaktualizować typu nagrody")

    return {
        "id": award_type.id,
        "name": award_type.name,
        "display_name": award_type.display_name,
        "description": award_type.description,
        "icon": award_type.icon,
        "lucide_icon": award_type.lucide_icon,
        "color": award_type.color,
        "icon_type": "custom" if award_type.custom_icon_path else (
            "lucide" if award_type.lucide_icon else "emoji"
        ),
        "icon_url": f"/api/admin/award-types/{award_type.id}/icon" if award_type.custom_icon_path else None,
        "is_system_award": award_type.is_system_award,
        "is_personal": award_type.is_personal,
        "updated_at": award_type.updated_at.isoformat()
    }


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
    except SQLAlchemyError as e:
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
            except OSError as e:
                logger.warning(f"Could not delete old icon: {e}")

    # Zapisz nowy plik
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except OSError as e:
        logger.error(f"Failed to save icon: {e}")
        raise StorageError(message="Nie można zapisać ikony", path=str(file_path))

    # Zaktualizuj w bazie
    award_type.custom_icon_path = str(file_path)
    award_type.lucide_icon = None  # Wyczyść lucide icon przy uploadzie custom

    try:
        db.commit()
    except SQLAlchemyError as e:
        # Jeśli commit fail, usuń plik
        try:
            file_path.unlink()
        except OSError:
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


@router.delete("/clips/{clip_id}")
async def delete_clip(
        clip_id: int,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Usuwa klip (soft delete) - tylko dla adminów
    DELETE /api/admin/clips/{clip_id}
    """
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    try:
        clip.is_deleted = True
        db.commit()

        logger.info(f"Admin {admin_user.username} deleted clip {clip_id} ({clip.filename})")

        return {
            "message": "Klip został usunięty",
            "clip_id": clip_id,
            "filename": clip.filename
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete clip {clip_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nie udało się usunąć klipu"
        )


@router.get("/clips/{clip_id}/restore")
async def restore_clip(
        clip_id: int,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Przywraca usunięty klip - tylko dla adminów

    GET /api/admin/clips/{clip_id}/restore
    """
    # Znajdź usunięty klip
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == True
    ).first()

    if not clip:
        raise NotFoundError(
            resource="Usunięty klip",
            resource_id=clip_id,
            message="Nie znaleziono usuniętego klipu o podanym ID"
        )

    try:
        # Przywróć klip
        clip.is_deleted = False
        db.commit()

        logger.info(f"Admin {admin_user.username} restored clip {clip_id} ({clip.filename})")

        return {
            "message": "Klip został przywrócony",
            "clip_id": clip_id,
            "filename": clip.filename
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to restore clip {clip_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nie udało się przywrócić klipu"
        )


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
        user_id: int,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Dezaktywuje użytkownika - tylko dla adminów

    PATCH /api/admin/users/{user_id}/deactivate
    """
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie możesz dezaktywować własnego konta"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundError(resource="Użytkownik", resource_id=user_id)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik jest już nieaktywny"
        )

    user.is_active = False
    db.commit()

    logger.info(f"Admin {admin_user.username} deactivated user {user_id} ({user.username})")

    return {
        "message": "Użytkownik został dezaktywowany",
        "user_id": user_id,
        "username": user.username
    }


@router.patch("/users/{user_id}/activate")
async def activate_user(
        user_id: int,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Aktywuje użytkownika - tylko dla adminów

    PATCH /api/admin/users/{user_id}/activate
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundError(resource="Użytkownik", resource_id=user_id)

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik jest już aktywny"
        )

    user.is_active = True
    db.commit()

    logger.info(f"Admin {admin_user.username} activated user {user_id} ({user.username})")

    return {
        "message": "Użytkownik został aktywowany",
        "user_id": user_id,
        "username": user.username
    }


@router.delete("/award-types/{award_type_id}/force")
@router.delete("/award-types/{award_type_id}")
async def delete_award_type(
        award_type_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Usuwa typ nagrody

    DELETE /api/admin/award-types/{award_type_id}
    DELETE /api/admin/award-types/{award_type_id}/force

    Uprawnienia:
    - Admin może usuwać wszystkie (poza system/personal)
    - Twórca może usuwać tylko swoje (poza personal)
    """
    award_type = db.query(AwardType).filter(AwardType.id == award_type_id).first()

    if not award_type:
        raise NotFoundError(resource="Typ nagrody", resource_id=award_type_id)

    # Blokada systemowych i personal
    if award_type.is_system_award:
        raise ValidationError(
            message="Nie można usunąć systemowej nagrody",
            field="is_system_award"
        )

    if award_type.is_personal:
        raise ValidationError(
            message="Nie można usunąć imiennej nagrody",
            field="is_personal"
        )

    # Sprawdź uprawnienia
    can_delete = current_user.is_admin or award_type.created_by_user_id == current_user.id

    if not can_delete:
        raise AuthorizationError(
            message="Nie masz uprawnień do usunięcia tego typu nagrody"
        )

    # Sprawdź czy typ jest używany
    from app.models.award import Award
    awards_count = db.query(Award).filter(Award.award_name == award_type.name).count()

    if awards_count > 0:
        raise ValidationError(
            message=f"Nie można usunąć - typ nagrody jest używany w {awards_count} nagrodach",
            field="usage_count",
            details={"count": awards_count}
        )

    # Usuń plik ikony jeśli istnieje
    if award_type.custom_icon_path:
        icon_path = Path(award_type.custom_icon_path)
        if icon_path.exists():
            try:
                icon_path.unlink()
                logger.info(f"Deleted icon file: {icon_path}")
            except OSError as e:
                logger.warning(f"Could not delete icon file: {e}")

    db.delete(award_type)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete award type {award_type_id}: {e}")
        raise DatabaseError(message="Nie można usunąć typu nagrody")

    logger.info(f"User {current_user.username} deleted award type {award_type_id} ({award_type.name})")

    return {
        "message": "Typ nagrody został usunięty",
        "award_type_id": award_type_id,
        "name": award_type.name
    }


class AwardUpdate(BaseModel):
    """Schema do aktualizacji nagrody"""
    award_name: Optional[str] = None
    clip_id: Optional[int] = None


@router.get("/awards")
async def get_all_awards(
        page: int = 1,
        limit: int = 20,
        sort_by: str = "awarded_at",
        sort_order: str = "desc",
        user_id: Optional[int] = None,
        clip_id: Optional[int] = None,
        award_name: Optional[str] = None,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Lista wszystkich nagród z filtrami (admin only)
    GET /api/admin/awards?page=1&limit=20&sort_by=awarded_at&sort_order=desc
    """
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    offset = (page - 1) * limit

    # Bazowe query z joinami
    query = db.query(Award).options(
        joinedload(Award.clip).joinedload(Clip.uploader),
        joinedload(Award.user)
    ).join(
        Clip, Award.clip_id == Clip.id
    ).filter(
        Clip.is_deleted == False
    )

    # Filtry
    if user_id:
        query = query.filter(Award.user_id == user_id)
    if clip_id:
        query = query.filter(Award.clip_id == clip_id)
    if award_name:
        query = query.filter(Award.award_name == award_name)

    # Sortowanie
    sort_fields = {
        "awarded_at": Award.awarded_at,
        "clip_id": Award.clip_id,
        "user_id": Award.user_id,
        "award_name": Award.award_name
    }

    if sort_by not in sort_fields:
        sort_by = "awarded_at"

    sort_field = sort_fields[sort_by]

    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_field))
    else:
        query = query.order_by(desc(sort_field))

    # Total
    total = query.count()

    # Pobierz z paginacją
    awards = query.offset(offset).limit(limit).all()

    # Response
    awards_data = []
    for award in awards:
        # Pobierz AwardType
        award_type = db.query(AwardType).filter(
            AwardType.name == award.award_name
        ).first()

        awards_data.append({
            "id": award.id,
            "award_name": award.award_name,
            "award_display_name": award_type.display_name if award_type else award.award_name,
            "award_icon": award_type.icon if award_type else "🏆",
            "awarded_at": award.awarded_at.isoformat(),
            "user": {
                "id": award.user_id,
                "username": award.user.username
            },
            "clip": {
                "id": award.clip.id,
                "filename": award.clip.filename,
                "clip_type": award.clip.clip_type.value,
                "uploader_username": award.clip.uploader.username
            }
        })

    pages = (total + limit - 1) // limit

    return {
        "awards": awards_data,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages
    }


@router.patch("/awards/{award_id}")
async def update_award(
        award_id: int,
        award_data: AwardUpdate,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Aktualizuj nagrodę (admin only)
    PATCH /api/admin/awards/{award_id}
    """
    award = db.query(Award).filter(Award.id == award_id).first()

    if not award:
        raise NotFoundError(resource="Nagroda", resource_id=award_id)

    # Aktualizuj pola
    if award_data.award_name is not None:
        # Sprawdź czy AwardType istnieje
        award_type = db.query(AwardType).filter(
            AwardType.name == award_data.award_name
        ).first()
        if not award_type:
            raise ValidationError(
                message=f"Nieznany typ nagrody: {award_data.award_name}",
                field="award_name"
            )
        award.award_name = award_data.award_name

    if award_data.clip_id is not None:
        # Sprawdź czy klip istnieje
        clip = db.query(Clip).filter(
            Clip.id == award_data.clip_id,
            Clip.is_deleted == False
        ).first()
        if not clip:
            raise NotFoundError(resource="Klip", resource_id=award_data.clip_id)
        award.clip_id = award_data.clip_id

    try:
        db.commit()
        db.refresh(award)
        logger.info(f"Admin {admin_user.username} updated award {award_id}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update award: {e}")
        raise DatabaseError(message="Nie można zaktualizować nagrody")

    return {
        "id": award.id,
        "award_name": award.award_name,
        "clip_id": award.clip_id,
        "user_id": award.user_id,
        "awarded_at": award.awarded_at.isoformat()
    }


@router.delete("/awards/{award_id}")
async def delete_award(
        award_id: int,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Usuń nagrodę (admin only)
    DELETE /api/admin/awards/{award_id}
    """
    award = db.query(Award).filter(Award.id == award_id).first()

    if not award:
        raise NotFoundError(resource="Nagroda", resource_id=award_id)

    try:
        db.delete(award)
        db.commit()
        logger.info(f"Admin {admin_user.username} deleted award {award_id}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete award: {e}")
        raise DatabaseError(message="Nie można usunąć nagrody")

    return {
        "message": "Nagroda została usunięta",
        "award_id": award_id
    }


class UserUpdate(BaseModel):
    """Schema do aktualizacji użytkownika"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


@router.patch("/users/{user_id}")
async def update_user(
        user_id: int,
        user_update: UserUpdate,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Aktualizuj użytkownika (admin only)
    PATCH /api/admin/users/{user_id}
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundError(resource="Użytkownik", resource_id=user_id)

    # Sprawdź duplikat username
    if user_update.username and user_update.username != user.username:
        existing = db.query(User).filter(
            User.username == user_update.username.lower(),
            User.id != user_id
        ).first()

        if existing:
            raise DuplicateError(
                resource="Użytkownik",
                field="username",
                value=user_update.username
            )

    # Sprawdź duplikat email
    if user_update.email and user_update.email != user.email:
        existing = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()

        if existing:
            raise DuplicateError(
                resource="Użytkownik",
                field="email",
                value=user_update.email
            )

    # Aktualizuj pola
    if user_update.username:
        user.username = user_update.username.lower()

    if user_update.email is not None:
        user.email = user_update.email

    if user_update.full_name is not None:
        user.full_name = user_update.full_name

    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin

    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Admin {admin_user.username} updated user {user_id} ({user.username})")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to update user: {e}")
        raise DatabaseError(message="Nie można zaktualizować użytkownika")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_admin": user.is_admin
    }


@router.delete("/users/{user_id}")
async def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Usuń użytkownika (admin only)
    DELETE /api/admin/users/{user_id}

    Blokuje usunięcie samego siebie
    Automatycznie usuwa nagrodę imienną użytkownika
    """
    # BLOKADA - nie można usunąć samego siebie
    if user_id == admin_user.id:
        raise ValidationError(
            message="Nie możesz usunąć własnego konta",
            field="user_id"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundError(resource="Użytkownik", resource_id=user_id)

    # Sprawdź, czy user ma uploadowane klipy — to blokuje usunięcie
    clips_count = db.query(Clip).filter(Clip.uploader_id == user_id).count()

    if clips_count > 0:
        raise ValidationError(
            message=f"Nie można usunąć - użytkownik ma {clips_count} klipów. Usuń najpierw klipy.",
            field="user_data",
            details={"clips": clips_count}
        )

    # Znajdź wszystkie nagrody przyznane przez tego użytkownika
    awards_to_delete = db.query(Award).filter(Award.user_id == user_id).all()
    awards_count = len(awards_to_delete)

    # Znajdź i usuń nagrodę imienną użytkownika (AwardType)
    personal_award_name = f"award:personal_{user.username}"
    personal_award_type = db.query(AwardType).filter(
        AwardType.name == personal_award_name
    ).first()

    try:
        # Usuń najpierw nagrodę imienną, jeśli istnieje
        if personal_award_type:
            # Usuń plik ikony jeśli istnieje
            if personal_award_type.custom_icon_path:
                icon_path = Path(personal_award_type.custom_icon_path)
                if icon_path.exists():
                    try:
                        icon_path.unlink()
                        logger.info(f"Deleted personal award icon: {icon_path}")
                    except OSError as e:
                        logger.warning(f"Could not delete personal award icon: {e}")

            db.delete(personal_award_type)
            logger.info(f"Deleted personal award type: {personal_award_name}")

        # Usuń użytkownika
        db.delete(user)
        db.commit()
        logger.info(f"Admin {admin_user.username} deleted user {user_id} ({user.username})")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to delete user: {e}")
        raise DatabaseError(message="Nie można usunąć użytkownika")

    return {
        "message": "Użytkownik został usunięty (wraz z nagrodą imienną)",
        "user_id": user_id,
        "username": user.username
    }


class UserCreate(BaseModel):
    """Schema do tworzenia użytkownika przez admina"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_admin: bool = False


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
        user_data: UserCreate,
        db: Session = Depends(get_db),
        admin_user: User = Depends(require_admin)
):
    """
    Utwórz nowego użytkownika (admin only)
    POST /api/admin/users

    Użytkownik jest tworzony bez hasła — może je ustawić później w profilu
    """
    # Sprawdź duplikat username
    existing = db.query(User).filter(
        User.username == user_data.username.lower()
    ).first()

    if existing:
        raise DuplicateError(
            resource="Użytkownik",
            field="username",
            value=user_data.username
        )

    # Sprawdź duplikat email
    if user_data.email:
        existing_email = db.query(User).filter(
            User.email == user_data.email
        ).first()

        if existing_email:
            raise DuplicateError(
                resource="Użytkownik",
                field="email",
                value=user_data.email
            )

    # Utwórz użytkownika bez hasła (pusty hash)
    from app.core.security import hash_password
    new_user = User(
        username=user_data.username.lower(),
        email=user_data.email,
        hashed_password=hash_password(""),  # Puste hasło
        full_name=user_data.full_name,
        is_active=True,
        is_admin=user_data.is_admin,
        award_scopes=[]
    )

    db.add(new_user)
    db.flush()

    # Utwórz imienną nagrodę
    from app.models.award_type import AwardType
    personal_award = AwardType(
        name=f"award:personal_{new_user.username}",
        display_name=f"Nagroda {new_user.username}",
        description=f"Osobista nagroda użytkownika {new_user.username}",
        icon="⭐",
        color="#FFD700",
        is_personal=True,
        created_by_user_id=new_user.id
    )
    db.add(personal_award)

    try:
        db.commit()
        db.refresh(new_user)
        logger.info(f"Admin {admin_user.username} created user {new_user.username}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create user: {e}")
        raise DatabaseError(message="Nie można utworzyć użytkownika")

    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "is_active": new_user.is_active,
        "is_admin": new_user.is_admin,
        "message": "Użytkownik utworzony bez hasła - może je ustawić w profilu"
    }
