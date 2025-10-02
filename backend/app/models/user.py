"""
SQLAlchemy model dla User
"""
from app.core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, JSON


class User(Base):
    """Model użytkownika w bazie danych"""

    __tablename__ = "users"

    # Podstawowe pola
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Scope-based permissions - lista nagród które użytkownik może przyznawać
    # Przechowywane jako JSON array, np: ["award:epic_clip", "award:funny", "award:clutch"]
    award_scopes = Column(JSON, default=list, nullable=False)

    # Relacje (dodamy później gdy będą inne modele)
    # awards = relationship("Award", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def has_scope(self, scope: str) -> bool:
        """
        Sprawdza czy użytkownik ma dany scope (uprawnienie)

        Args:
            scope: Scope do sprawdzenia, np. "award:epic_clip"

        Returns:
            True jeśli użytkownik ma scope, False w przeciwnym razie
        """
        return scope in (self.award_scopes or [])
