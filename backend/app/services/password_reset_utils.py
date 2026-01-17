"""
Password reset token generation and validation utilities.

This module provides secure token generation using Python's secrets module.
"""
import secrets
import string
from datetime import datetime
from typing import Optional

from app.core.database import SessionLocal
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from sqlalchemy.orm import Session


def generate_reset_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Uses secrets.token_urlsafe() which is recommended by Python docs
    for security-sensitive applications like password resets.

    Args:
        length: Length of the token in bytes (default: 32)
                The actual string will be longer due to base64 encoding

    Returns:
        str: URL-safe token string (43 characters for 32 bytes)

    Example:
        >>> token = generate_reset_token()
        >>> len(token)  # Approximately 43 characters
        43
        >>> token  # Example: 'xvT5h8Jq2kL9mNpR3sWuX7yZ0aB4cD6e'
    """
    return secrets.token_urlsafe(length)


def generate_reset_token_hex(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token using hex encoding.

    Alternative to token_urlsafe() if you prefer hex encoding.

    Args:
        length: Length of the token in bytes (default: 32)
                The actual string will be 2x longer (64 chars for 32 bytes)

    Returns:
        str: Hex-encoded token string (64 characters for 32 bytes)

    Example:
        >>> token = generate_reset_token_hex()
        >>> len(token)
        64
    """
    return secrets.token_hex(length)


def create_password_reset_token(
        user_id: int,
        db: Session,
        expiration_minutes: int = 30
) -> PasswordResetToken:
    """
    Create a new password reset token for a user.

    This function:
    1. Generates a secure random token
    2. Creates a database record
    3. Sets expiration time
    4. Invalidates any existing unused tokens for this user

    Args:
        user_id: ID of the user requesting password reset
        db: Database session
        expiration_minutes: Token validity period in minutes (default: 30)

    Returns:
        PasswordResetToken: Created token object

    Raises:
        ValueError: If user_id is invalid

    Example:
        >>> with get_db_context() as db:
        ...     token_obj = create_password_reset_token(user_id=1, db=db)
        ...     print(f"Token: {token_obj.token}")
        ...     print(f"Expires: {token_obj.expires_at}")
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User with id {user_id} not found")

    # Invalidate any existing unused tokens for this user
    # This prevents token accumulation and ensures only latest token is valid
    existing_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used == False
    ).all()

    for old_token in existing_tokens:
        old_token.used = True
        old_token.used_at = datetime.utcnow()

    # Generate new token
    token_string = generate_reset_token()

    # Create token record
    token_obj = PasswordResetToken(
        token=token_string,
        user_id=user_id,
        expires_at=PasswordResetToken.create_expiration_time(expiration_minutes),
        used=False
    )

    db.add(token_obj)
    db.commit()
    db.refresh(token_obj)

    return token_obj


def verify_reset_token(
        token: str,
        db: Session
) -> Optional[PasswordResetToken]:
    """
    Verify and retrieve a password reset token.

    Checks:
    1. Token exists in database
    2. Token has not been used
    3. Token has not expired

    Args:
        token: Token string to verify
        db: Database session

    Returns:
        PasswordResetToken: Token object if valid, None otherwise

    Example:
        >>> with get_db_context() as db:
        ...     token_obj = verify_reset_token("abc123...", db)
        ...     if token_obj:
        ...         print(f"Valid token for user: {token_obj.user_id}")
        ...     else:
        ...         print("Invalid or expired token")
    """
    token_obj = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token
    ).first()

    if not token_obj:
        return None

    if not token_obj.is_valid:
        return None

    return token_obj


def cleanup_expired_tokens(db: Session) -> int:
    """
    Clean up expired and used tokens from database.

    This should be run periodically (e.g., daily cron job) to prevent
    database bloat.

    Args:
        db: Database session

    Returns:
        int: Number of tokens deleted

    Example:
        >>> with get_db_context() as db:
        ...     deleted = cleanup_expired_tokens(db)
        ...     print(f"Cleaned up {deleted} expired tokens")
    """
    # Delete tokens that are:
    # 1. Used, OR
    # 2. Expired (even if not used)

    now = datetime.utcnow()

    deleted_count = db.query(PasswordResetToken).filter(
        (PasswordResetToken.used == True) |
        (PasswordResetToken.expires_at < now)
    ).delete()

    db.commit()

    return deleted_count


def get_user_from_token(
        token: str,
        db: Session
) -> Optional[User]:
    """
    Get user associated with a valid reset token.

    Convenience function that combines token verification and user retrieval.

    Args:
        token: Token string
        db: Database session

    Returns:
        User: User object if token is valid, None otherwise

    Example:
        >>> with get_db_context() as db:
        ...     user = get_user_from_token("abc123...", db)
        ...     if user:
        ...         print(f"Reset requested by: {user.username}")
    """
    token_obj = verify_reset_token(token, db)

    if not token_obj:
        return None

    return token_obj.user