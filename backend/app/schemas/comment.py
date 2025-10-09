"""
Pydantic schemas dla Comment
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class CommentBase(BaseModel):
    """Bazowe pola komentarza"""
    content: str = Field(..., min_length=1, max_length=1000)
    timestamp: Optional[int] = Field(None, ge=0)
    parent_id: Optional[int] = None


class CommentCreate(CommentBase):
    """Schema do tworzenia komentarza"""

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Walidacja treści - usuń zbędne białe znaki"""
        if not v or not v.strip():
            raise ValueError('Komentarz nie może być pusty')
        return v.strip()


class CommentUpdate(BaseModel):
    """Schema do aktualizacji komentarza"""
    content: str = Field(..., min_length=1, max_length=1000)

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Walidacja treści - usuń zbędne białe znaki"""
        if not v or not v.strip():
            raise ValueError('Komentarz nie może być pusty')
        return v.strip()


class CommentUserInfo(BaseModel):
    """Informacje o użytkowniku w komentarzu"""
    id: int
    username: str
    full_name: Optional[str] = None
    is_admin: bool = False

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Schema komentarza w odpowiedzi API"""
    id: int
    clip_id: int
    user_id: int
    content: str
    timestamp: Optional[int] = None
    parent_id: Optional[int] = None
    created_at: datetime
    edited_at: Optional[datetime] = None
    is_deleted: bool = False
    is_edited: bool = False
    can_edit: bool = False
    reply_count: int = 0

    # Informacje o użytkowniku
    user: CommentUserInfo

    # Parsed content z mentions
    content_html: str
    mentioned_users: List[str] = []

    class Config:
        from_attributes = True


class CommentWithReplies(CommentResponse):
    """Komentarz z zagnieżdżonymi odpowiedziami"""
    replies: List['CommentResponse'] = []

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Odpowiedź z listą komentarzy i metadanymi paginacji"""
    comments: List[CommentWithReplies]
    total: int
    page: int
    limit: int
    pages: int


class MentionSuggestion(BaseModel):
    """Sugestia użytkownika do mention"""
    username: str
    full_name: Optional[str] = None
    user_id: int


# Update forward references
CommentWithReplies.model_rebuild()
