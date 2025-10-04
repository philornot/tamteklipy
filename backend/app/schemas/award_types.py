"""
Pydantic schemas dla AwardType
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, validator


class AwardTypeBase(BaseModel):
    """Bazowe pola typu nagrody"""
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: str = Field(default="#FFD700", pattern="^#[0-9A-Fa-f]{6}$")


class AwardTypeCreate(AwardTypeBase):
    """Schema do tworzenia nowego typu nagrody"""
    lucide_icon: Optional[str] = Field(None, max_length=100,
                                       description="Lucide React icon name (e.g. 'trophy', 'star')")
    is_personal: bool = Field(default=False, description="Whether this award can only be given by creator")

    @validator('lucide_icon')
    def validate_lucide_icon(cls, v):
        """Validate that it's a reasonable icon name"""
        if v and not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Icon name can only contain letters, numbers, hyphens and underscores')
        return v.lower() if v else v


class AwardTypeUpdate(BaseModel):
    """Schema do aktualizacji typu nagrody"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    lucide_icon: Optional[str] = Field(None, max_length=100)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_personal: Optional[bool] = None


class AwardTypeResponse(BaseModel):
    """Schema typu nagrody w odpowiedzi API"""
    id: int
    name: str
    display_name: str
    description: Optional[str]

    # Icon info
    icon_type: str  # "lucide" or "custom"
    icon_value: str  # lucide icon name or custom icon URL
    lucide_icon: Optional[str]
    custom_icon_url: Optional[str] = None

    color: str

    # Ownership
    created_by_user_id: Optional[int]
    created_by_username: Optional[str]
    is_system_award: bool
    is_personal: bool

    # Permissions
    can_user_give: bool = Field(default=True, description="Whether current user can give this award")

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AwardTypeListResponse(BaseModel):
    """Lista typów nagród"""
    award_types: List[AwardTypeResponse]
    total: int
    system_awards: int
    personal_awards: int
    custom_awards: int


class AvailableAwardsResponse(BaseModel):
    """Nagrody dostępne dla aktualnego użytkownika"""
    available_awards: List[AwardTypeResponse]
    can_create_awards: bool = True

    class Config:
        from_attributes = True


class LucideIconOption(BaseModel):
    """Opcja ikony Lucide do wyboru"""
    name: str
    category: str


class LucideIconsResponse(BaseModel):
    """Lista dostępnych ikon Lucide"""
    icons: List[LucideIconOption]
    categories: List[str]
