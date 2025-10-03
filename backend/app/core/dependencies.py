"""
FastAPI dependencies — funkcje pomocnicze używane jako Depends()
"""
from app.core.database import get_db
from app.core.exceptions import NotFoundError, AuthenticationError
from app.core.security import get_current_user_from_token
from app.models.user import User
from fastapi import Depends
from sqlalchemy.orm import Session


async def get_current_user(
        current_user_data: dict = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
) -> User:
    """
    Dependency do pobierania pełnego obiektu User z bazy danych

    Użycie:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"username": user.username}

    Args:
        current_user_data: Dane z tokenu JWT
        db: Sesja bazy danych

    Returns:
        User: Obiekt użytkownika z bazy

    Raises:
        AuthenticationError: Jeśli token nieprawidłowy lub użytkownik nieaktywny
        NotFoundError: Jeśli użytkownik nie istnieje w bazie
    """
    user_id = current_user_data.get("user_id")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundError(resource="Użytkownik", resource_id=user_id)

    if not user.is_active:
        raise AuthenticationError(message="Konto jest nieaktywne")

    return user
