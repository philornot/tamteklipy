"""
SQLAlchemy model dla Clip (klipy i screenshoty)
"""
import enum
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy import event
from sqlalchemy.orm import relationship
from sqlalchemy.orm import validates


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

    def __repr__(self):
        return f"<Clip(id={self.id}, filename='{self.filename}', type={self.clip_type}, uploader_id={self.uploader_id})>"

    @property
    def award_count(self) -> int:
        """Zwraca liczbę nagród przyznanych do klipa"""
        return len(self.awards) if self.awards else 0

    @property
    def file_size_mb(self) -> float:
        """Zwraca rozmiar pliku w MB"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0

    @validates('file_path', 'thumbnail_path')
    def validate_path_is_absolute(self, key, value):
        """Waliduje że ścieżki są absolutne"""
        if value is None:
            return value

        path = Path(value)

        if not path.is_absolute():
            logger.warning(
                f"Próba zapisu względnej ścieżki do {key}: {value}. "
                f"Ścieżki muszą być absolutne!"
            )
            raise ValueError(
                f"{key} musi być ścieżką absolutną. Otrzymano: {value}"
            )

        return value


@event.listens_for(Clip, 'before_insert')
@event.listens_for(Clip, 'before_update')
def validate_clip_paths(mapper, connection, target):
    """
    Event listener - waliduje ścieżki przed zapisem do bazy

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Instance of Clip being saved

    Raises:
        ValueError: Jeśli ścieżki nie są absolutne
    """
    from pathlib import Path

    # Waliduj file_path
    if target.file_path:
        if not Path(target.file_path).is_absolute():
            raise ValueError(
                f"file_path musi być absolutną ścieżką. "
                f"Otrzymano: {target.file_path}"
            )

    # Waliduj thumbnail_path (jeśli nie None)
    if target.thumbnail_path:
        if not Path(target.thumbnail_path).is_absolute():
            raise ValueError(
                f"thumbnail_path musi być absolutną ścieżką. "
                f"Otrzymano: {target.thumbnail_path}"
            )
