"""
Router dla custom user awards - każdy user może tworzyć własne nagrody
"""
import logging
import re
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import ValidationError, NotFoundError, DuplicateError, DatabaseError
from app.models.award_type import AwardType
from app.models.user import User
from app.routers.admin import AwardTypeResponse
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()
logger = logging.getLogger(__name__)


def sanitize_award_name(name: str) -> str:
    """Sanitize name dla scope: tylko alfanumeryczne + underscore"""
    return re.sub(r'[^a-z0-9_]', '_', name.lower())


@router.get("/my-award-types", response_model=List[AwardTypeResponse])
async def get_my_custom_awards(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz custom nagrody użytkownika
    GET /api/my-awards/my-award-types
    """
    custom_awards = db.query(AwardType).filter(
        AwardType.created_by_user_id == current_user.id
    ).all()

    return [
        AwardTypeResponse(
            id=a.id,
            name=a.name,
            display_name=a.display_name,
            description=a.description,
            icon=a.icon,
            color=a.color
        )
        for a in custom_awards
    ]


@router.post("/my-award-types", response_model=AwardTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_award(
        display_name: str,
        description: str = "",
        color: str = "#FFD700",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Utwórz własną nagrodę
    POST /api/my-awards/my-award-types
    Body: {display_name, description?, color?}
    """
    # 1. Sprawdź limit (max 5 per user)
    custom_count = db.query(AwardType).filter(
        AwardType.created_by_user_id == current_user.id
    ).count()

    if custom_count >= 5:
        raise ValidationError(
            message="Maksymalnie 5 własnych nagród per user",
            field="limit",
            details={"current": custom_count, "max": 5}
        )

    # 2. Waliduj display_name
    if not display_name or len(display_name) < 3 or len(display_name) > 50:
        raise ValidationError(
            message="Nazwa musi mieć 3-50 znaków",
            field="display_name"
        )

    # 3. Generuj unique scope name
    base_name = sanitize_award_name(display_name)
    scope_name = f"award:user_{current_user.id}_{base_name}"

    # Sprawdź czy już istnieje
    existing = db.query(AwardType).filter(AwardType.name == scope_name).first()
    if existing:
        raise DuplicateError(
            resource="AwardType",
            field="name",
            value=scope_name
        )

    # 4. Waliduj color (hex)
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        color = "#FFD700"  # Default gold

    # 5. Utwórz AwardType
    new_award = AwardType(
        name=scope_name,
        display_name=display_name,
        description=description,
        icon="🏆",  # Default emoji
        color=color,
        created_by_user_id=current_user.id
    )

    db.add(new_award)

    # 6. Auto-assign scope do usera
    if current_user.award_scopes is None:
        current_user.award_scopes = []

    if scope_name not in current_user.award_scopes:
        current_user.award_scopes = [*current_user.award_scopes, scope_name]

    try:
        db.commit()
        db.refresh(new_award)
        logger.info(f"Custom award created: {scope_name} by {current_user.username}")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to create custom award: {e}")
        raise DatabaseError(message="Nie można utworzyć nagrody", operation="create_custom_award")

    return AwardTypeResponse(
        id=new_award.id,
        name=new_award.name,
        display_name=new_award.display_name,
        description=new_award.description,
        icon=new_award.icon,
        color=new_award.color
    )


@router.delete("/my-award-types/{award_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_award(
        award_type_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Usuń własną nagrodę
    DELETE /api/my-awards/my-award-types/{award_type_id}
    """
    from app.models.award import Award
    from pathlib import Path

    award_type = db.query(AwardType).filter(
        AwardType.id == award_type_id,
        AwardType.created_by_user_id == current_user.id
    ).first()

    if not award_type:
        raise NotFoundError(resource="Custom AwardType", resource_id=award_type_id)

    # Sprawdź czy używana
    usage_count = db.query(Award).filter(Award.award_name == award_type.name).count()

    if usage_count > 0:
        # Soft delete - nie usuwaj z bazy, tylko usuń scope z usera
        if award_type.name in (current_user.award_scopes or []):
            current_user.award_scopes = [s for s in current_user.award_scopes if s != award_type.name]

        db.commit()
        logger.info(f"Soft delete custom award: {award_type.name} (used {usage_count} times)")
        return None

    # Hard delete - usuń z bazy i plik
    if award_type.icon_path:
        icon_path = Path(award_type.icon_path)
        if icon_path.exists():
            try:
                icon_path.unlink()
            except OSError:
                pass

    # Remove scope z usera
    if award_type.name in (current_user.award_scopes or []):
        current_user.award_scopes = [s for s in current_user.award_scopes if s != award_type.name]

    db.delete(award_type)
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Failed to hard delete custom award: {e}")
        raise DatabaseError(message="Nie można usunąć nagrody", operation="delete_custom_award")

    logger.info(f"Hard delete custom award: {award_type.name}")
    return None
