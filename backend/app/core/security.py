"""
Security utilities - hashowanie haseł, JWT, dependencies
"""
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from jose import JWTError, jwt
from passlib.context import CryptContext

# Konfiguracja bcrypt do hashowania haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashuje hasło używając bcrypt

    Args:
        password: Hasło w plain text

    Returns:
        Zahashowane hasło
    """
    # Konwertuj na bajty i obetnij do 72 bajtów (limit bcrypt)
    password_bytes = password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password_truncated)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Weryfikuje czy hasło zgadza się z hashem

    Args:
        plain_password: Hasło w plain text
        hashed_password: Zahashowane hasło z bazy

    Returns:
        True jeśli hasło jest poprawne, False w przeciwnym razie
    """
    # Ta sama logika obcinania
    password_bytes = plain_password.encode('utf-8')[:72]
    password_truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(password_truncated, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tworzy JWT access token

    Args:
        data: Dane do zakodowania w tokenie (np. user_id, scopes)
        expires_delta: Czas życia tokenu (opcjonalnie)

    Returns:
        JWT token jako string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Dekoduje JWT token

    Args:
        token: JWT token

    Returns:
        Zdekodowane dane z tokenu lub None jeśli token nieprawidłowy
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError:
        return None
