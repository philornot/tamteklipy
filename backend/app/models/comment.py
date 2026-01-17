"""
SQLAlchemy model dla Comment (komentarze do klipów)
"""
import logging
from datetime import datetime, timedelta

from app.core.database import Base
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy import Index
from sqlalchemy.orm import relationship, validates

logger = logging.getLogger(__name__)


class Comment(Base):
    """Model komentarza do klipa"""

    __tablename__ = "comments"

    # Podstawowe pola
    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(Integer, ForeignKey("clips.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)

    # Timestamp w video (opcjonalny) - w sekundach
    timestamp = Column(Integer, nullable=True)

    # Parent dla threaded comments (replies)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True, index=True)

    # Daty
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    edited_at = Column(DateTime, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Relacje
    clip = relationship("Clip", back_populates="comments")
    user = relationship("User", back_populates="comments")

    # Self-referential relationship dla replies
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_id]
    )
    __table_args__ = (
        # Index for comments by clip (top-level only)
        Index('ix_comments_clip_parent_created', 'clip_id', 'parent_id', 'created_at'),

        # Index for user's comments
        Index('ix_comments_user_created', 'user_id', 'created_at'),

        # Index for deleted filter
        Index('ix_comments_deleted', 'is_deleted'),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, clip_id={self.clip_id}, user_id={self.user_id}, parent_id={self.parent_id})>"

    @validates('content')
    def validate_content(self, key, value):
        """Walidacja treści komentarza - max 1000 znaków"""
        if not value or not value.strip():
            raise ValueError("Komentarz nie może być pusty")

        if len(value) > 1000:
            raise ValueError("Komentarz nie może przekraczać 1000 znaków")

        return value.strip()

    @validates('timestamp')
    def validate_timestamp(self, key, value):
        """Walidacja timestampu - musi być >= 0"""
        if value is not None and value < 0:
            raise ValueError("Timestamp nie może być ujemny")

        return value

    @property
    def can_edit(self) -> bool:
        """
        Sprawdza czy komentarz można jeszcze edytować (5 min od utworzenia)

        Returns:
            bool: True jeśli można edytować
        """
        if self.is_deleted:
            return False

        # 5 minut od utworzenia
        edit_window = timedelta(minutes=5)
        time_since_creation = datetime.utcnow() - self.created_at

        return time_since_creation <= edit_window

    @property
    def is_edited(self) -> bool:
        """Sprawdza czy komentarz był edytowany"""
        return self.edited_at is not None

    @property
    def reply_count(self) -> int:
        """Zwraca liczbę odpowiedzi (nie-usuniętych)"""
        return len([r for r in self.replies if not r.is_deleted]) if self.replies else 0

    def get_thread_depth(self) -> int:
        """
        Zwraca głębokość w drzewie komentarzy (0 = top-level, 1 = reply, etc.)

        Returns:
            int: Głębokość w drzewie
        """
        depth = 0
        current = self

        while current.parent_id is not None:
            depth += 1
            current = current.parent

            # Zabezpieczenie przed nieskończoną pętlą
            if depth > 10:
                logger.warning(f"Comment {self.id} has depth > 10, possible circular reference")
                break

        return depth

    def can_reply(self) -> bool:
        """
        Sprawdza, czy do tego komentarza można dodać odpowiedź
        Max 2 poziomy (top-level → reply → reply's reply = max)

        Returns:
            bool: True, jeśli można dodać reply
        """
        return self.get_thread_depth() < 2
