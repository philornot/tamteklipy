"""
Router dla autoryzacji — logowanie, rejestracja, tokeny JWT
"""
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user_from_token
)
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserResponse, UserWithToken
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    Endpoint logowania - zwraca JWT token

    POST /api/auth/login
    Body (form-data):
        - username: str
        - password: str

    Returns:
        Token: JWT access token i typ tokenu
    """
    # Znajdź użytkownika po username
    user = db.query(User).filter(User.username == form_data.username.lower()).first()

    if not user:
        raise AuthenticationError(
            message="Nieprawidłowa nazwa użytkownika lub hasło",
            details={"username": form_data.username}
        )

    # Sprawdź czy użytkownik jest aktywny
    if not user.is_active:
        raise AuthenticationError(
            message="Konto jest nieaktywne",
            details={"username": user.username}
        )

    # Zweryfikuj hasło
    if not verify_password(form_data.password, user.hashed_password):
        raise AuthenticationError(
            message="Nieprawidłowa nazwa użytkownika lub hasło"
        )

    # Utwórz JWT token ze scope użytkownika
    access_token = create_access_token(
        user_id=user.id,
        username=user.username,
        scopes=user.award_scopes or []
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(
        current_user: dict = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)
):
    """
    Endpoint zwracający dane zalogowanego użytkownika

    GET /api/auth/me
    Header: Authorization: Bearer <token>

    Returns:
        UserResponse: Dane użytkownika (bez hasła)
    """
    user_id = current_user.get("user_id")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise NotFoundError(resource="Użytkownik", resource_id=user_id)

    return user
