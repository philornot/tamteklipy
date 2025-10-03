"""
FastAPI dependencies — funkcje pomocnicze używane jako Depends()
"""
from typing import List

from app.core.database import get_db
from app.core.exceptions import AuthorizationError
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


def require_scope(required_scope: str):
    """
    Factory dependency do sprawdzania czy użytkownik ma wymagany scope

    Użycie:
        @app.post("/give-award", dependencies=[Depends(require_scope("award:epic_clip"))])
        async def give_award():
            return {"message": "Nagroda przyznana"}

    Args:
        required_scope: Wymagane uprawnienie (np. "award:epic_clip")

    Returns:
        Dependency function która sprawdza uprawnienia
    """

    async def verify_scope(user: User = Depends(get_current_user)) -> User:
        """Weryfikuje czy użytkownik ma wymagany scope"""
        if not user.has_scope(required_scope):
            raise AuthorizationError(
                message=f"Brak uprawnień: wymagany scope '{required_scope}'",
                required_scope=required_scope
            )
        return user

    return verify_scope


def require_any_scope(required_scopes: List[str]):
    """
    Factory dependency - sprawdza czy użytkownik ma przynajmniej jeden z podanych scope'ów

    Użycie:
        @app.post("/give-award", dependencies=[Depends(require_any_scope(["award:epic_clip", "award:funny"]))])
        async def give_award():
            return {"message": "Nagroda przyznana"}

    Args:
        required_scopes: Lista możliwych uprawnień

    Returns:
        Dependency function która sprawdza uprawnienia
    """

    async def verify_any_scope(user: User = Depends(get_current_user)) -> User:
        """Weryfikuje czy użytkownik ma przynajmniej jeden z wymaganych scope'ów"""
        user_scopes = user.award_scopes or []

        has_any = any(scope in user_scopes for scope in required_scopes)

        if not has_any:
            raise AuthorizationError(
                message=f"Brak uprawnień: wymagany jeden z scope'ów: {', '.join(required_scopes)}",
                required_scope=", ".join(required_scopes)
            )

        return user

    return verify_any_scope


def require_all_scopes(required_scopes: List[str]):
    """
    Factory dependency - sprawdza czy użytkownik ma wszystkie podane scope'y

    Użycie:
        @app.post("/admin-action", dependencies=[Depends(require_all_scopes(["admin:users", "admin:delete"]))])
        async def admin_action():
            return {"message": "Akcja wykonana"}

    Args:
        required_scopes: Lista wymaganych uprawnień

    Returns:
        Dependency function która sprawdza uprawnienia
    """

    async def verify_all_scopes(user: User = Depends(get_current_user)) -> User:
        """Weryfikuje czy użytkownik ma wszystkie wymagane scope'y"""
        user_scopes = user.award_scopes or []

        missing_scopes = [scope for scope in required_scopes if scope not in user_scopes]

        if missing_scopes:
            raise AuthorizationError(
                message=f"Brak uprawnień: brakujące scope'y: {', '.join(missing_scopes)}",
                required_scope=", ".join(missing_scopes)
            )

        return user

    return verify_all_scopes
