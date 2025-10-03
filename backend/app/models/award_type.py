"""
SQLAlchemy model dla AwardType - definicje typów nagród
"""
from app.core.database import Base
from sqlalchemy import Column, Integer, String, Text


class AwardType(Base):
    """
    Model typu nagrody - centralna definicja dostępnych nagród w systemie
    """
    __tablename__ = "award_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # np. "award:epic_clip"
    display_name = Column(String(100), nullable=False)  # "Epic Clip"
    description = Column(Text, nullable=True)  # "Za epicki moment w grze"
    icon = Column(String(50), default="🏆", nullable=False)  # Emoji lub path do ikony
    color = Column(String(7), default="#FFD700", nullable=False)  # Hex color

    def __repr__(self):
        return f"<AwardType(name='{self.name}', display_name='{self.display_name}')>"
