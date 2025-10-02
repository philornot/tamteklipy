"""
Security utilities - hashowanie haseł, JWT, dependencies
"""
from datetime import datetime, timedelta
from typing import Optional, List

from app.core.config import settings
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Konfiguracja bcrypt do hashowania haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme do pobierania tokenu z headera
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    """
    Hashuje hasło używając bcrypt

    Args:
        password: Hasło w plain text

    Returns:
        Zahashowane hasło
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Weryfikuje czy hasło zgadza się z hashem

    Args:
        plain_password: Hasło w plain text
        hashed_password: Zahashowane hasło z bazy

    Returns:
        True jeśli hasło jest poprawne, False w przeciwnym razie
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
        user_id: int,
        username: str,
        scopes: List[str],
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tworzy JWT access token z scope (uprawnieniami)

    Args:
        user_id: ID użytkownika
        username: Nazwa użytkownika
        scopes: Lista uprawnień użytkownika (np. ["award:epic_clip", "award:funny"])
        expires_delta: Czas życia tokenu (opcjonalnie)

    Returns:
        JWT token jako string
    """
    # Przygotuj payload tokenu
    to_encode = {
        "sub": str(user_id),  # Subject - ID użytkownika (zawsze string w JWT)
        "username": username,
        "scopes": scopes,  # Lista uprawnień
    }

    # Ustaw czas wygaśnięcia
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    # Zakoduj token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Dekoduje i weryfikuje JWT token

    Args:
        token: JWT token

    Returns:
        Zdekodowane dane z tokenu (user_id, username, scopes) lub None jeśli nieprawidłowy
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        # Wyciągnij dane z payloadu
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        scopes: List[str] = payload.get("scopes", [])

        if user_id is None or username is None:
            return None

        return {
            "user_id": int(user_id),
            "username": username,
            "scopes": scopes
        }

    except JWTError:
        return None


async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency do pobierania aktualnego użytkownika z tokenu JWT
    Używane w endpointach które wymagają autoryzacji

    Args:
        token: JWT token z headera Authorization

    Returns:
        Dict z danymi użytkownika (user_id, username, scopes)

    Raises:
        HTTPException: Jeśli token nieprawidłowy lub wygasł
    """
    from app.core.exceptions import AuthenticationError

    token_data = verify_token(token)

    if token_data is None:
        raise AuthenticationError(
            message="Nieprawidłowy lub wygasły token",
            details={"token_valid": False}
        )

    return token_data


def require_scope(required_scope: str):
    """
    Dependency factory do sprawdzania czy użytkownik ma wymagany scope

    Args:
        required_scope: Wymagane uprawnienie (np. "award:epic_clip")

    Returns:
        Dependency function która sprawdza uprawnienia

    Example:
        @app.post("/api/awards/give", dependencies=[Depends(require_scope("award:epic_clip"))])
        async def give_award():
            ...
    """

    async def check_scope(current_user: dict = Depends(get_current_user_from_token)):
        from app.core.exceptions import AuthorizationError

        user_scopes = current_user.get("scopes", [])

        if required_scope not in user_scopes:
            raise AuthorizationError(
                message=f"Brak uprawnień: wymagany scope '{required_scope}'",
                required_scope=required_scope
            )

        return current_user

    return check_scope
