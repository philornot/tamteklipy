"""
SQLAlchemy model dla AwardType - definicje typów nagród
"""
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime


class AwardType(Base):
    """
    Model typu nagrody - centralna definicja dostępnych nagród w systemie

    Typy nagród:
    - System awards (is_system_award=True): Predefiniowane, nikt nie może usunąć
    - Personal awards (is_personal=True): Imienna nagroda użytkownika, tylko właściciel i admin mogą edytować
    - Custom awards (created_by_user_id != None, is_personal=False): Zwykłe custom nagrody użytkowników
    """
    __tablename__ = "award_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Ikona - albo emoji fallback, albo lucide, albo custom upload
    icon = Column(String(50), default="🏆", nullable=False)  # Emoji fallback
    lucide_icon = Column(String(100), nullable=True)  # np. "trophy", "star", "flame"
    custom_icon_path = Column(String(500), nullable=True)  # Ścieżka do uploadu

    color = Column(String(7), default="#FFD700", nullable=False)

    # Typy nagród
    is_system_award = Column(Boolean, default=False, nullable=False)  # Systemowa, nie można usunąć
    is_personal = Column(Boolean, default=False, nullable=False)  # Imienna, nie można usunąć

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Deprecated field (do usunięcia w migracji)
    icon_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_icon_info(self):
        """
        Zwraca informacje o ikonie do użycia w API
        Returns: dict with icon_type ("emoji"|"lucide"|"custom") and icon_value
        """
        if self.custom_icon_path:
            return {
                "icon_type": "custom",
                "icon_value": f"/api/admin/award-types/{self.id}/icon",
                "icon_url": f"/api/admin/award-types/{self.id}/icon"
            }
        elif self.lucide_icon:
            return {
                "icon_type": "lucide",
                "icon_value": self.lucide_icon,
                "icon_url": None
            }
        else:
            return {
                "icon_type": "emoji",
                "icon_value": self.icon,
                "icon_url": None
            }

    def __repr__(self):
        return f"<AwardType(name='{self.name}', display_name='{self.display_name}', personal={self.is_personal})>"
