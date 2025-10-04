"""
SQLAlchemy model dla AwardType - definicje typów nagród
"""
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime


class AwardType(Base):
    """
    Model typu nagrody - centralna definicja dostępnych nagród w systemie
    """
    __tablename__ = "award_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="🏆", nullable=False)  # Emoji fallback
    color = Column(String(7), default="#FFD700", nullable=False)
    icon_path = Column(String(500), nullable=True)
    is_system_award = Column(Boolean, default=False, nullable=False)
    is_personal = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    lucide_icon = Column(String(100), nullable=True)
    custom_icon_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AwardType(name='{self.name}', display_name='{self.display_name}')>"
