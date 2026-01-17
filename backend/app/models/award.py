"""
SQLAlchemy model dla Award — nagrody przyznawane do klipów
"""
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship


class Award(Base):
    """
    Model nagrody przyznanych do klipów
    Junction table łącząca User -> Clip z informacją o typie nagrody
    """

    __tablename__ = "awards"

    # Podstawowe pola
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    clip_id = Column(Integer, ForeignKey("clips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Typ nagrody - scope który użytkownik użył
    award_name = Column(String(100), nullable=False)  # np. "award:epic_clip", "award:funny"

    # Data przyznania
    awarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacje
    clip = relationship("Clip", back_populates="awards")
    user = relationship("User", back_populates="awards_given")

    __table_args__ = (
        # Constraint - użytkownik może przyznać daną nagrodę tylko raz dla klipa
        UniqueConstraint('clip_id', 'user_id', 'award_name', name='uq_clip_user_award'),

        # Index for awards by clip (most common query)
        Index('ix_awards_clip_awarded', 'clip_id', 'awarded_at'),

        # Index for user's awards
        Index('ix_awards_user_awarded', 'user_id', 'awarded_at'),

        # Index for award type filtering
        Index('ix_awards_name', 'award_name'),
    )

    def __repr__(self):
        return f"<Award(id={self.id}, clip_id={self.clip_id}, user_id={self.user_id}, award='{self.award_name}')>"
