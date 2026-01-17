"""
SQLAlchemy model for PasswordResetToken - password reset functionality

This model handles secure password reset tokens with expiration.
"""
from datetime import datetime, timedelta

from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship


class PasswordResetToken(Base):
    """
    Model for password reset tokens.

    Features:
    - Secure token generation using secrets module
    - 30-minute expiration by default
    - One-time use tokens (used flag)
    - Automatic cleanup of expired tokens
    """
    __tablename__ = "password_reset_tokens"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Token (unique, indexed for fast lookup)
    token = Column(String(64), unique=True, nullable=False, index=True)

    # Foreign key to user
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Usage tracking
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Relationship to User
    user = relationship("User", backref="password_reset_tokens")

    # Composite index for cleanup queries
    __table_args__ = (
        Index('ix_password_reset_tokens_expires_used', 'expires_at', 'used'),
    )

    def __repr__(self):
        """String representation for debugging."""
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.used}, expires_at={self.expires_at})>"

    @property
    def is_expired(self) -> bool:
        """
        Check if token has expired.

        Returns:
            bool: True if token is expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """
        Check if token is valid (not used and not expired).

        Returns:
            bool: True if token can be used, False otherwise
        """
        return not self.used and not self.is_expired

    def mark_as_used(self):
        """
        Mark token as used.

        This should be called after successful password reset.
        """
        self.used = True
        self.used_at = datetime.utcnow()

    @staticmethod
    def create_expiration_time(minutes: int = 30) -> datetime:
        """
        Create expiration timestamp.

        Args:
            minutes: Number of minutes until expiration (default: 30)

        Returns:
            datetime: Expiration timestamp
        """
        return datetime.utcnow() + timedelta(minutes=minutes)