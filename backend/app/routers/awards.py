# backend/app/routers/awards.py

"""
Router dla systemu nagród — przyznawanie i zarządzanie nagrodami
"""
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError, DuplicateError
from app.models.award import Award
from app.models.award_type import AwardType
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
from sqlalchemy import desc, asc
from sqlalchemy.orm import Session, joinedload

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/user/{username}", response_model=dict)
async def get_user_awards(
        username: str,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "awarded_at",
        sort_order: str = "desc",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz wszystkie nagrody przyznane przez użytkownika

    GET /api/awards/user/{username}?page=1&limit=20&sort_by=awarded_at&sort_order=desc
    """
    # Znajdź użytkownika
    user = db.query(User).filter(User.username == username.lower()).first()

    if not user:
        raise NotFoundError(resource="Użytkownik", resource_id=username)

    # Walidacja paginacji
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    offset = (page - 1) * limit

    # Bazowe query z joinami
    query = db.query(Award).options(
        joinedload(Award.clip).joinedload(Clip.uploader),
        joinedload(Award.user)
    ).filter(
        Award.user_id == user.id
    ).join(
        Clip, Award.clip_id == Clip.id
    ).filter(
        Clip.is_deleted == False
    )

    # Sortowanie
    sort_fields = {
        "awarded_at": Award.awarded_at,
        "clip_id": Award.clip_id,
        "award_name": Award.award_name
    }

    if sort_by not in sort_fields:
        sort_by = "awarded_at"

    sort_field = sort_fields[sort_by]

    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_field))
    else:
        query = query.order_by(desc(sort_field))

    # Total przed paginacją
    total = query.count()

    # Pobierz z paginacją
    awards = query.offset(offset).limit(limit).all()

    # Przygotuj response
    awards_response = [
        {
            "id": award.id,
            "award_name": award.award_name,
            "awarded_at": award.awarded_at.isoformat(),
            "clip": {
                "id": award.clip.id,
                "filename": award.clip.filename,
                "clip_type": award.clip.clip_type.value,
                "uploader_username": award.clip.uploader.username,
                "created_at": award.clip.created_at.isoformat()
            }
        }
        for award in awards
    ]

    pages = (total + limit - 1) // limit

    return {
        "username": user.username,
        "user_id": user.id,
        "total_awards": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "awards": awards_response
    }


@router.get("/my-awards", response_model=MyAwardsResponse)
async def get_my_awards(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz nagrody które aktualny użytkownik może przyznawać
    Używa User.can_give_award() do filtrowania
    """
    available_awards = []

    # Pobierz wszystkie typy nagród z bazy
    all_award_types = db.query(AwardType).all()

    for award_type in all_award_types:
        # Sprawdź czy user może przyznać tę nagrodę
        if current_user.can_give_award(award_type):
            available_awards.append(
                UserAwardScope(
                    award_name=award_type.name,
                    display_name=award_type.display_name,
                    description=award_type.description,
                    icon=award_type.icon,
                    icon_url=f"/api/admin/award-types/{award_type.id}/icon" if award_type.custom_icon_path else None
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
    """
    award_name = award_data.award_name

    # 1. Sprawdź czy klip istnieje
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # 2. Pobierz AwardType z bazy (zamiast AWARD_DEFINITIONS)
    award_type = db.query(AwardType).filter(
        AwardType.name == award_name
    ).first()

    if not award_type:
        raise ValidationError(
            message=f"Nieznany typ nagrody: {award_name}",
            field="award_name",
            details={"received": award_name}
        )

    # 3. Sprawdź czy użytkownik może przyznać tę nagrodę
    if not current_user.can_give_award(award_type):
        raise AuthorizationError(
            message=f"Nie masz uprawnień do przyznania nagrody: {award_name}",
            details={"award_type": award_type.display_name}
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
            value=f"Już przyznałeś {award_type.display_name} do tego klipa"
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
        permanent: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Usuń nagrodę z klipa (tylko własną)

    DELETE /api/awards/clips/{clip_id}/awards/{award_id}?permanent=false
    """
    # Znajdź nagrodę
    award = db.query(Award).filter(
        Award.id == award_id,
        Award.clip_id == clip_id
    ).first()

    if not award:
        raise NotFoundError(resource="Nagroda", resource_id=award_id)

    # Sprawdź czy użytkownik jest właścicielem nagrody
    if award.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError(
            message="Możesz usunąć tylko swoje nagrody"
        )

    # Usuń nagrodę
    try:
        db.delete(award)
        db.commit()

        delete_type = "permanent" if permanent else "soft"
        logger.info(
            f"Award deleted ({delete_type}): award_id={award_id}, "
            f"clip_id={clip_id}, user={current_user.username}, "
            f"award_name={award.award_name}"
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete award: {e}", exc_info=True)
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
    total_awards = db.query(func.count(Award.id)).scalar() or 0

    # Najpopularniejszy typ nagrody z join do AwardType
    most_popular = db.query(
        Award.award_name,
        func.count(Award.id).label('count')
    ).group_by(
        Award.award_name
    ).order_by(
        func.count(Award.id).desc()
    ).first()

    # Pobierz AwardType dla najpopularniejszej nagrody
    most_popular_type = None
    if most_popular:
        most_popular_type = db.query(AwardType).filter(
            AwardType.name == most_popular[0]
        ).first()

    # Najbardziej aktywni użytkownicy (top 5)
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

    # Top klipy według nagród (top 10)
    top_clips = db.query(
        Clip.id,
        Clip.filename,
        Clip.clip_type,
        User.username.label('uploader_username'),
        func.count(Award.id).label('award_count')
    ).join(
        Award, Clip.id == Award.clip_id
    ).join(
        User, Clip.uploader_id == User.id
    ).filter(
        Clip.is_deleted == False
    ).group_by(
        Clip.id
    ).order_by(
        func.count(Award.id).desc()
    ).limit(10).all()

    # Breakdown nagród per użytkownik (dla zalogowanego)
    user_awards_breakdown = db.query(
        Award.award_name,
        func.count(Award.id).label('count')
    ).filter(
        Award.user_id == current_user.id
    ).group_by(
        Award.award_name
    ).all()

    return {
        "total_awards": total_awards,
        "most_popular_award": {
            "award_name": most_popular[0] if most_popular else None,
            "count": most_popular[1] if most_popular else 0,
            "display_name": most_popular_type.display_name if most_popular_type else None,
            "icon": most_popular_type.icon if most_popular_type else None
        },
        "most_active_users": [
            {
                "user_id": user.id,
                "username": user.username,
                "awards_given": user.awards_given
            }
            for user in most_active_users
        ],
        "top_clips_by_awards": [
            {
                "clip_id": clip.id,
                "filename": clip.filename,
                "clip_type": clip.clip_type.value,
                "uploader_username": clip.uploader_username,
                "award_count": clip.award_count
            }
            for clip in top_clips
        ],
        "current_user_breakdown": {
            award.award_name: award.count
            for award in user_awards_breakdown
        }
    }
