"""
SQLAlchemy model dla Clip (klipy i screenshoty)
"""
import enum
import logging
from datetime import datetime
from pathlib import Path

from app.core.database import Base
from sqlalchemy import Boolean, Enum as SQLEnum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship, validates

logger = logging.getLogger(__name__)


class ClipType(str, enum.Enum):
    """Typ pliku - video lub screenshot"""
    VIDEO = "video"
    SCREENSHOT = "screenshot"


class Clip(Base):
    """Model klipa/screenshota w bazie danych"""

    __tablename__ = "clips"

    # Podstawowe pola
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)  # Oryginalna nazwa pliku
    file_path = Column(String(500), nullable=False, unique=True)  # Ścieżka na dysku
    thumbnail_path = Column(String(500), nullable=True)  # Ścieżka do miniatury (dla video)
    thumbnail_webp_path = Column(String, nullable=True, index=True)

    # Typ pliku
    clip_type = Column(SQLEnum(ClipType), nullable=False, default=ClipType.VIDEO)

    # Metadane
    file_size = Column(Integer, nullable=False)  # Rozmiar w bajtach
    duration = Column(Integer, nullable=True)  # Czas trwania w sekundach (tylko dla video)
    width = Column(Integer, nullable=True)  # Szerokość w pikselach
    height = Column(Integer, nullable=True)  # Wysokość w pikselach

    # Informacje o uploaderze
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Daty
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relacje
    uploader = relationship("User", back_populates="clips")
    awards = relationship("Award", back_populates="clip", cascade="all, delete-orphan")

    # Komentarze
    comments = relationship("Comment", back_populates="clip", cascade="all, delete-orphan")

    # Composite indexes for common queries
    __table_args__ = (
        # Index for /clips endpoint (created_at DESC, is_deleted filter)
        Index('ix_clips_created_at_deleted', 'created_at', 'is_deleted'),

        # Index for /clips endpoint filtered by type
        Index('ix_clips_type_deleted', 'clip_type', 'is_deleted'),

        # Index for uploader filtering
        Index('ix_clips_uploader_deleted', 'uploader_id', 'is_deleted'),
    )

    def __repr__(self):
        return f"<Clip(id={self.id}, filename='{self.filename}', type={self.clip_type}, uploader_id={self.uploader_id})>"

    @property
    def award_count(self) -> int:
        """Zwraca liczbę nagród przyznanych do klipu"""
        return len(self.awards) if self.awards else 0

    @property
    def file_size_mb(self) -> float:
        """Zwraca rozmiar pliku w MB"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0

    @property
    def comment_count(self) -> int:
        """Zwraca liczbę komentarzy (nie-usuniętych)"""
        from app.models.comment import Comment
        if not hasattr(self, '_comment_count'):
            self._comment_count = len([c for c in self.comments if not c.is_deleted]) if self.comments else 0
        return self._comment_count

    @validates('file_path', 'thumbnail_path')
    def validate_path_is_absolute(self, key, value):
        """
        Waliduje, że ścieżki są absolutne przy zapisie do bazy

        Args:
            key: Nazwa pola (file_path lub thumbnail_path)
            value: Wartość ścieżki

        Returns:
            str: Zwalidowana ścieżka

        Raises:
            ValueError: Jeśli ścieżka nie jest absolutna
        """
        if value is None:
            return value

        path = Path(value)

        if not path.is_absolute():
            logger.warning(
                f"Attempted to save relative path to {key}: '{value}'. "
                f"Paths must be absolute!"
            )
            raise ValueError(
                f"{key} must be an absolute path. Received: {value}"
            )

        logger.debug(f"Path validation OK for {key}: {value}")
        return value
