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
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="🏆", nullable=False)  # Emoji fallback
    color = Column(String(7), default="#FFD700", nullable=False)

    # NEW: Path to uploaded icon image
    icon_path = Column(String(500), nullable=True)

    # NEW: User ownership (null = system award)
    created_by_user_id = Column(Integer, nullable=True, index=True)

    def __repr__(self):
        return f"<AwardType(name='{self.name}', display_name='{self.display_name}')>"
