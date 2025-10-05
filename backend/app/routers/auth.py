"""
Router dla autoryzacji — logowanie, rejestracja, tokeny JWT
"""
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import hash_password
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user_from_token
)
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.schemas.user import UserResponse, UserWithToken
from fastapi import APIRouter, Depends
from fastapi import status
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: Session = Depends(get_db)
):
    """
    Endpoint rejestracji nowego użytkownika
    UWAGA: Ten endpoint powinien być chroniony (tylko admin) - TODO: dodać middleware

    POST /api/auth/register
    Body:
        - username: str
        - email: str
        - password: str
        - full_name: str (optional)
        - award_scopes: List[str] (optional)

    Returns:
        UserResponse: Dane utworzonego użytkownika
    """
    from app.core.exceptions import DuplicateError

    # Sprawdź czy username już istnieje
    existing_user = db.query(User).filter(
        User.username == user_data.username.lower()
    ).first()

    if existing_user:
        raise DuplicateError(
            resource="Użytkownik",
            field="username",
            value=user_data.username
        )

    # Sprawdź czy email już istnieje
    existing_email = db.query(User).filter(
        User.email == user_data.email
    ).first()

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

    # Utwórz nowego użytkownika
    new_user = User(
        username=user_data.username.lower(),
        email=user_data.email,
        hashed_password=hash_password(user_data.password) if user_data.password else None,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        award_scopes=user_data.award_scopes or []
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# Endpoint zwracający aktualnego użytkownika na podstawie tokenu JWT
@router.get("/me", response_model=UserResponse)
async def read_me(current_user: User = Depends(get_current_user)):
    """
    Zwraca dane aktualnie zalogowanego użytkownika.
    Wymaga nagłówka Authorization: Bearer <token>

    GET /api/auth/me
    """
    # DEBUG: Log przed zwróceniem
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"User {current_user.username}: is_admin={current_user.is_admin}")
    logger.info(f"Full user object: {current_user}")

    return current_user
