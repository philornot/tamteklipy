"""
Pydantic schemas dla Award
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AwardBase(BaseModel):
    """Bazowe pola nagrody"""
    award_name: str = Field(..., min_length=1, max_length=100)


class AwardCreate(BaseModel):
    """Schema do przyznawania nagrody"""
    award_name: str = Field(..., min_length=1, max_length=100, description="Nazwa nagrody (np. award:epic_clip)")


class AwardResponse(BaseModel):
    """Schema nagrody w odpowiedzi API"""
    id: int
    clip_id: int
    user_id: int
    username: str
    award_name: str
    award_display_name: str = ""  # ← DODAJ TO
    award_icon: str = "🏆"  # ← DODAJ TO (opcjonalnie)
    awarded_at: datetime

    class Config:
        from_attributes = True


class AwardListResponse(BaseModel):
    """Lista nagród dla klipa"""
    clip_id: int
    total_awards: int
    awards: List[AwardResponse]
    awards_by_type: dict  # {"award:epic_clip": 3, "award:funny": 2}


class UserAwardScope(BaseModel):
    """Nagrody które użytkownik może przyznawać"""
    award_name: str
    display_name: str
    description: str
    icon: str = "🏆"
    icon_url: Optional[str] = None


class MyAwardsResponse(BaseModel):
    """Odpowiedź z nagrodami użytkownika"""
    available_awards: List[UserAwardScope]
