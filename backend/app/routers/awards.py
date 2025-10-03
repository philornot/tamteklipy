"""
Router dla systemu nagród - przyznawanie i zarządzanie nagrodami
"""
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scope
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError, DuplicateError
from app.models.award import Award
from app.models.clip import Clip
from app.models.user import User
from app.schemas.award import (
    AwardCreate,
    AwardResponse,
    AwardListResponse,
    MyAwardsResponse,
    UserAwardScope
)
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload

router = APIRouter()
logger = logging.getLogger(__name__)

# Mapowanie scope -> display info
AWARD_DEFINITIONS = {
    "award:epic_clip": {
        "display_name": "Epic Clip",
        "description": "Za epicki moment w grze",
        "icon": "🔥"
    },
    "award:funny": {
        "display_name": "Funny Moment",
        "description": "Za zabawną sytuację",
        "icon": "😂"
    },
    "award:pro_play": {
        "display_name": "Pro Play",
        "description": "Za profesjonalną zagrywkę",
        "icon": "⭐"
    },
    "award:clutch": {
        "display_name": "Clutch",
        "description": "Za clutch w trudnej sytuacji",
        "icon": "💪"
    }
}


@router.get("/my-awards", response_model=MyAwardsResponse)
async def get_my_awards(current_user: User = Depends(get_current_user)):
    """
    Pobierz nagrody które aktualny użytkownik może przyznawać

    GET /api/awards/my-awards
    Wymaga: Authorization header
    """
    available_awards = []

    for scope in current_user.award_scopes or []:
        if scope in AWARD_DEFINITIONS:
            definition = AWARD_DEFINITIONS[scope]
            available_awards.append(
                UserAwardScope(
                    award_name=scope,
                    display_name=definition["display_name"],
                    description=definition["description"],
                    icon=definition["icon"]
                )
            )

    return MyAwardsResponse(available_awards=available_awards)


@router.post("/clips/{clip_id}", response_model=AwardResponse, status_code=status.HTTP_201_CREATED)
async def give_award_to_clip(
        clip_id: int,
        award_data: AwardCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Przyznaj nagrodę do klipa

    POST /api/awards/clips/{clip_id}
    Body: { "award_name": "award:epic_clip" }
    Wymaga: Authorization header z odpowiednim scope
    """
    award_name = award_data.award_name

    # 1. Sprawdź czy klip istnieje
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # 2. Waliduj czy award_name jest poprawny
    if award_name not in AWARD_DEFINITIONS:
        raise ValidationError(
            message=f"Nieznany typ nagrody: {award_name}",
            field="award_name",
            details={
                "received": award_name,
                "allowed": list(AWARD_DEFINITIONS.keys())
            }
        )

    # 3. Sprawdź czy użytkownik ma uprawnienia do tej nagrody
    if not current_user.has_scope(award_name):
        raise AuthorizationError(
            message=f"Nie masz uprawnień do przyznania nagrody: {award_name}",
            details={
                "required_scope": award_name,
                "user_scopes": current_user.award_scopes
            }
        )

    # 4. Sprawdź czy użytkownik już nie przyznał tej nagrody
    existing_award = db.query(Award).filter(
        Award.clip_id == clip_id,
        Award.user_id == current_user.id,
        Award.award_name == award_name
    ).first()

    if existing_award:
        raise DuplicateError(
            resource="Nagroda",
            field="award",
            value=f"Użytkownik {current_user.username} już przyznał {award_name} do klipa {clip_id}"
        )

    # 5. Utwórz nagrodę
    new_award = Award(
        clip_id=clip_id,
        user_id=current_user.id,
        award_name=award_name
    )

    db.add(new_award)

    try:
        db.commit()
        db.refresh(new_award)
        logger.info(f"Award created: {award_name} for clip {clip_id} by user {current_user.username}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create award: {e}")
        from app.core.exceptions import DatabaseError
        raise DatabaseError(
            message="Nie można zapisać nagrody do bazy",
            operation="create_award"
        )

    # 6. Zwróć response z danymi użytkownika
    return AwardResponse(
        id=new_award.id,
        clip_id=new_award.clip_id,
        user_id=new_award.user_id,
        username=current_user.username,
        award_name=new_award.award_name,
        awarded_at=new_award.awarded_at
    )


@router.delete("/clips/{clip_id}/awards/{award_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_award_from_clip(
        clip_id: int,
        award_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Usuń nagrodę z klipa (tylko własną)

    DELETE /api/awards/clips/{clip_id}/awards/{award_id}
    Wymaga: Authorization header
    """
    # Znajdź nagrodę
    award = db.query(Award).filter(
        Award.id == award_id,
        Award.clip_id == clip_id
    ).first()

    if not award:
        raise NotFoundError(resource="Nagroda", resource_id=award_id)

    # Sprawdź czy użytkownik jest właścicielem nagrody
    if award.user_id != current_user.id:
        raise AuthorizationError(
            message="Możesz usunąć tylko swoje nagrody"
        )

    # Usuń nagrodę
    try:
        db.delete(award)
        db.commit()
        logger.info(f"Award deleted: {award_id} by user {current_user.username}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete award: {e}")
        from app.core.exceptions import DatabaseError
        raise DatabaseError(
            message="Nie można usunąć nagrody",
            operation="delete_award"
        )

    return None


@router.get("/clips/{clip_id}", response_model=AwardListResponse)
async def get_clip_awards(
        clip_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz wszystkie nagrody przyznane do klipa

    GET /api/awards/clips/{clip_id}
    """
    # Sprawdź czy klip istnieje
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Pobierz nagrody z joinami
    awards = db.query(Award).options(
        joinedload(Award.user)
    ).filter(
        Award.clip_id == clip_id
    ).order_by(Award.awarded_at.desc()).all()

    # Pogrupuj po typach
    awards_by_type = {}
    for award in awards:
        if award.award_name not in awards_by_type:
            awards_by_type[award.award_name] = 0
        awards_by_type[award.award_name] += 1

    # Przygotuj response
    awards_response = [
        AwardResponse(
            id=award.id,
            clip_id=award.clip_id,
            user_id=award.user_id,
            username=award.user.username,
            award_name=award.award_name,
            awarded_at=award.awarded_at
        )
        for award in awards
    ]

    return AwardListResponse(
        clip_id=clip_id,
        total_awards=len(awards),
        awards=awards_response,
        awards_by_type=awards_by_type
    )


@router.get("/leaderboard")
async def get_leaderboard(
        limit: int = 10,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Ranking klipów według liczby nagród

    GET /api/awards/leaderboard?limit=10
    """
    from sqlalchemy import func

    # Query z agregacją
    leaderboard = db.query(
        Clip.id,
        Clip.filename,
        Clip.clip_type,
        func.count(Award.id).label('award_count')
    ).outerjoin(
        Award, Clip.id == Award.clip_id
    ).filter(
        Clip.is_deleted == False
    ).group_by(
        Clip.id
    ).order_by(
        func.count(Award.id).desc()
    ).limit(limit).all()

    return {
        "leaderboard": [
            {
                "clip_id": row.id,
                "filename": row.filename,
                "clip_type": row.clip_type.value,
                "award_count": row.award_count
            }
            for row in leaderboard
        ],
        "limit": limit
    }


@router.get("/stats")
async def get_award_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Statystyki nagród w systemie

    GET /api/awards/stats
    """
    from sqlalchemy import func

    # Całkowita liczba nagród
    total_awards = db.query(func.count(Award.id)).scalar()

    # Najpopularniejszy typ nagrody
    most_popular = db.query(
        Award.award_name,
        func.count(Award.id).label('count')
    ).group_by(
        Award.award_name
    ).order_by(
        func.count(Award.id).desc()
    ).first()

    # Najbardziej aktywni użytkownicy
    most_active_users = db.query(
        User.id,
        User.username,
        func.count(Award.id).label('awards_given')
    ).join(
        Award, User.id == Award.user_id
    ).group_by(
        User.id
    ).order_by(
        func.count(Award.id).desc()
    ).limit(5).all()

    return {
        "total_awards": total_awards,
        "most_popular_award": {
            "award_name": most_popular[0] if most_popular else None,
            "count": most_popular[1] if most_popular else 0,
            "display_name": AWARD_DEFINITIONS.get(most_popular[0], {}).get("display_name") if most_popular else None
        },
        "most_active_users": [
            {
                "user_id": user.id,
                "username": user.username,
                "awards_given": user.awards_given
            }
            for user in most_active_users
        ]
    }
