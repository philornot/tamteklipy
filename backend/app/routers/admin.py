"""
Router dla admina - zarządzanie systemem
"""
import logging
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, DuplicateError, AuthorizationError, DatabaseError
from app.models.award_type import AwardType
from app.models.user import User
from fastapi import APIRouter, Depends, status
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
