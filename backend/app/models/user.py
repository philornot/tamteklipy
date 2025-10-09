"""
SQLAlchemy model dla User
"""
from app.core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship


class User(Base):
    """Model użytkownika w bazie danych"""

    __tablename__ = "users"

    # Podstawowe pola
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Scope-based permissions (deprecated - używamy teraz is_admin + system uprawnień)
    award_scopes = Column(JSON, default=list, nullable=False)

    # Relacje
    clips = relationship("Clip", back_populates="uploader", cascade="all, delete-orphan")
    awards_given = relationship("Award", back_populates="user", cascade="all, delete-orphan")

    # Komentarze
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', admin={self.is_admin})>"

    def has_scope(self, scope: str) -> bool:
        """
        Sprawdza czy użytkownik ma dany scope (uprawnienie)

        Args:
            scope: Scope do sprawdzenia, np. "award:epic_clip"

        Returns:
            True jeśli użytkownik ma scope, False w przeciwnym razie
        """
        return scope in (self.award_scopes or [])

    def can_give_award(self, award_type) -> bool:
        """
        Sprawdza, czy użytkownik może przyznać daną nagrodę

        Args:
            award_type: Obiekt AwardType

        Returns:
            True jeśli użytkownik może przyznać nagrodę
        """
        # Admin może przyznać wszystkie nagrody
        if self.is_admin:
            return True

        # Systemowe nagrody może przyznać każdy
        if award_type.is_system_award:
            return True

        # Osobiste nagrody może przyznać tylko twórca (i admin)
        if award_type.is_personal:
            return award_type.created_by_user_id == self.id

        # Custom publiczne nagrody może przyznać każdy
        if not award_type.is_personal and not award_type.is_system_award:
            # Custom nagrody utworzone przez usera
            if award_type.created_by_user_id is not None:
                return True

        return False
