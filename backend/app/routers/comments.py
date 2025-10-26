"""
Router dla systemu komentarzy
"""
import logging
import re
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.models.clip import Clip
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentWithReplies,
    CommentListResponse,
    MentionSuggestion,
    CommentUserInfo
)
from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

router = APIRouter()
logger = logging.getLogger(__name__)


def parse_mentions(content: str, db: Session) -> tuple[str, List[str]]:
    """
    Parsuje @mentions w treści komentarza

    Returns:
        tuple: (content_html, mentioned_usernames)
    """
    # Regex dla @username (litery, cyfry, _, -)
    mention_pattern = r'@(\w+(?:[-_]\w+)*)'

    mentioned_usernames = []
    content_html = content

    for match in re.finditer(mention_pattern, content):
        username = match.group(1).lower()

        # Sprawdź czy użytkownik istnieje
        user = db.query(User).filter(
            func.lower(User.username) == username,
            User.is_active == True
        ).first()

        if user:
            mentioned_usernames.append(user.username)
            # Zamień @username na link
            content_html = content_html.replace(
                match.group(0),
                f'<a href="/profile/{user.username}" class="mention">@{user.username}</a>'
            )

    return content_html, list(set(mentioned_usernames))


def build_comment_response(
        comment: Comment,
        current_user: User,
        db: Session,
        include_replies: bool = False
) -> CommentResponse | CommentWithReplies:
    """
    Buduje response dla komentarza z parsed mentions
    """
    content_html, mentioned_users = parse_mentions(comment.content, db)

    user_info = CommentUserInfo(
        id=comment.user.id,
        username=comment.user.username,
        full_name=comment.user.full_name,
        is_admin=comment.user.is_admin
    )

    base_data = {
        "id": comment.id,
        "clip_id": comment.clip_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "timestamp": comment.timestamp,
        "parent_id": comment.parent_id,
        "created_at": comment.created_at,
        "edited_at": comment.edited_at,
        "is_deleted": comment.is_deleted,
        "is_edited": comment.is_edited,
        "can_edit": comment.can_edit and comment.user_id == current_user.id,
        "reply_count": comment.reply_count,
        "user": user_info,
        "content_html": content_html,
        "mentioned_users": mentioned_users
    }

    if include_replies:
        # Pobierz replies (nie-usunięte)
        replies_data = []
        for reply in comment.replies:
            if not reply.is_deleted:
                reply_response = build_comment_response(reply, current_user, db, include_replies=False)
                replies_data.append(reply_response)

        return CommentWithReplies(**base_data, replies=replies_data)

    return CommentResponse(**base_data)


@router.post("/clips/{clip_id}/comments", response_model=CommentResponse)
async def create_comment(
        clip_id: int,
        comment_data: CommentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Dodaj nowy komentarz do klipa

    POST /api/clips/{clip_id}/comments
    Body: {
        "content": "Haha pamiętam jak Konrad spadł 😂",
        "timestamp": 83,  // opcjonalny - sekundy w video
        "parent_id": null  // opcjonalny - dla replies
    }
    """
    # Sprawdź czy klip istnieje
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Sprawdź parent (jeśli reply)
    parent = None
    if comment_data.parent_id:
        parent = db.query(Comment).filter(
            Comment.id == comment_data.parent_id,
            Comment.clip_id == clip_id,  # Musi być w tym samym clipie
            Comment.is_deleted == False
        ).first()

        if not parent:
            raise NotFoundError(resource="Komentarz nadrzędny", resource_id=comment_data.parent_id)

        # Sprawdź max depth (2 poziomy)
        if not parent.can_reply():
            raise ValidationError(
                message="Nie można dodać odpowiedzi - osiągnięto maksymalną głębokość (2 poziomy)",
                field="parent_id"
            )

    # Walidacja timestamp dla video
    if comment_data.timestamp is not None:
        if clip.clip_type.value != "video":
            raise ValidationError(
                message="Timestamp można dodać tylko do video",
                field="timestamp"
            )

        if clip.duration and comment_data.timestamp > clip.duration:
            raise ValidationError(
                message=f"Timestamp przekracza długość video ({clip.duration}s)",
                field="timestamp"
            )

    try:
        # Utwórz komentarz
        new_comment = Comment(
            clip_id=clip_id,
            user_id=current_user.id,
            content=comment_data.content,
            timestamp=comment_data.timestamp,
            parent_id=comment_data.parent_id
        )

        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)

        # Załaduj relacje
        db.refresh(new_comment)
        new_comment.user  # Trigger lazy load

        logger.info(f"Comment created: ID={new_comment.id}, clip={clip_id}, user={current_user.username}")

        return build_comment_response(new_comment, current_user, db)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating comment: {e}")
        from app.core.exceptions import DatabaseError
        raise DatabaseError(
            message="Nie można utworzyć komentarza",
            operation="create_comment"
        )


@router.get("/clips/{clip_id}/comments", response_model=CommentListResponse)
async def get_comments(
        clip_id: int,
        page: int = 1,
        limit: int = 20,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz komentarze do klipa z paginacją
    Zwraca top-level komentarze z zagnieżdżonymi replies

    GET /api/clips/{clip_id}/comments?page=1&limit=20
    """
    # Sprawdź czy klip istnieje
    clip = db.query(Clip).filter(
        Clip.id == clip_id,
        Clip.is_deleted == False
    ).first()

    if not clip:
        raise NotFoundError(resource="Klip", resource_id=clip_id)

    # Walidacja parametrów
    if page < 1:
        page = 1
    if limit < 1:
        limit = 20
    elif limit > 100:
        limit = 100

    offset = (page - 1) * limit

    # Query dla top-level komentarzy (parent_id = None)
    query = db.query(Comment).options(
        joinedload(Comment.user),
        joinedload(Comment.replies).joinedload(Comment.user)
    ).filter(
        Comment.clip_id == clip_id,
        Comment.parent_id == None,
        Comment.is_deleted == False
    ).order_by(desc(Comment.created_at))

    # Total przed paginacją
    total = query.count()

    # Paginacja
    comments = query.offset(offset).limit(limit).all()

    # Konwertuj do response z replies
    comments_response = []
    for comment in comments:
        comment_with_replies = build_comment_response(
            comment,
            current_user,
            db,
            include_replies=True
        )
        comments_response.append(comment_with_replies)

    pages = (total + limit - 1) // limit

    return CommentListResponse(
        comments=comments_response,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
        comment_id: int,
        comment_data: CommentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Edytuj komentarz (tylko własny, w ciągu 5 minut)

    PUT /api/comments/{comment_id}
    Body: {"content": "Zaktualizowana treść"}
    """
    comment = db.query(Comment).options(
        joinedload(Comment.user)
    ).filter(
        Comment.id == comment_id,
        Comment.is_deleted == False
    ).first()

    if not comment:
        raise NotFoundError(resource="Komentarz", resource_id=comment_id)

    # Sprawdź uprawnienia
    if comment.user_id != current_user.id:
        raise AuthorizationError(
            message="Możesz edytować tylko swoje komentarze"
        )

    # Sprawdź edit window (5 minut)
    if not comment.can_edit:
        raise ValidationError(
            message="Czas na edycję komentarza minął (5 minut od utworzenia)",
            field="edit_window"
        )

    try:
        # Aktualizuj komentarz
        comment.content = comment_data.content
        comment.edited_at = datetime.utcnow()

        db.commit()
        db.refresh(comment)

        logger.info(f"Comment updated: ID={comment_id}, user={current_user.username}")

        return build_comment_response(comment, current_user, db)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating comment: {e}")
        from app.core.exceptions import DatabaseError
        raise DatabaseError(
            message="Nie można zaktualizować komentarza",
            operation="update_comment"
        )


@router.delete("/comments/{comment_id}")
async def delete_comment(
        comment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Usuń komentarz (soft delete)
    Tylko własny komentarz lub admin

    DELETE /api/comments/{comment_id}
    """
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.is_deleted == False
    ).first()

    if not comment:
        raise NotFoundError(resource="Komentarz", resource_id=comment_id)

    # Sprawdź uprawnienia - własny komentarz lub admin
    if comment.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError(
            message="Możesz usuwać tylko swoje komentarze"
        )

    try:
        # Soft delete
        comment.is_deleted = True

        db.commit()

        logger.info(f"Comment deleted: ID={comment_id}, user={current_user.username}")

        return {"message": "Komentarz został usunięty"}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting comment: {e}")
        from app.core.exceptions import DatabaseError
        raise DatabaseError(
            message="Nie można usunąć komentarza",
            operation="delete_comment"
        )


@router.get("/users/mentions", response_model=List[MentionSuggestion])
async def get_mention_suggestions(
        query: str,
        limit: int = 5,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Pobierz sugestie użytkowników do @mention

    GET /api/users/mentions?query=phi&limit=5
    """
    if not query or len(query) < 2:
        return []

    # Szukaj użytkowników po username (case-insensitive)
    users = db.query(User).filter(
        func.lower(User.username).like(f"{query.lower()}%"),
        User.is_active == True
    ).limit(limit).all()

    return [
        MentionSuggestion(
            username=user.username,
            full_name=user.full_name,
            user_id=user.id
        )
        for user in users
    ]
