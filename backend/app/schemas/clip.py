"""
Pydantic schemas dla Clip
"""
from datetime import datetime
from typing import Optional, List

from app.models.clip import ClipType
from pydantic import BaseModel


class ClipBase(BaseModel):
    """Bazowe pola klipa"""
    filename: str
    clip_type: ClipType
    file_size: int
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ClipCreate(ClipBase):
    """Schema do tworzenia klipa (internal use)"""
    file_path: str
    thumbnail_path: Optional[str] = None
    uploader_id: int


class ClipResponse(BaseModel):
    """Schema klipa w odpowiedzi API"""
    id: int
    filename: str
    clip_type: str
    file_size: int
    file_size_mb: float
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime
    uploader_username: str
    uploader_id: int
    award_count: int = 0
    has_thumbnail: bool = False
    has_webp_thumbnail: bool = False
    award_icons: List[dict] = []  # [{award_name, icon_url, count}]

    class Config:
        from_attributes = True


class ClipDetailResponse(ClipResponse):
    """Szczegółowa odpowiedź z nagrodami"""
    awards: List[dict] = []
    thumbnail_url: Optional[str] = None
    thumbnail_webp_url: Optional[str] = None
    download_url: str

    class Config:
        from_attributes = True


class ClipListResponse(BaseModel):
    """Odpowiedź z listą klipów i metadanymi paginacji"""
    clips: List[ClipResponse]
    total: int
    page: int
    limit: int
    pages: int
