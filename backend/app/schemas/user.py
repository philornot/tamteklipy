"""
Pydantic schemas dla User
"""
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """Bazowe pola użytkownika"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)  # Opcjonalny
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    is_admin: bool = False


class UserCreate(UserBase):
    """Schema do tworzenia użytkownika"""
    password: Optional[str] = Field(None, max_length=100)  # Opcjonalne
    award_scopes: Optional[List[str]] = Field(default_factory=list)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Walidacja nazwy użytkownika"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username może zawierać tylko litery, cyfry, _ i -')
        return v.lower()


class UserUpdate(BaseModel):
    """Schema do aktualizacji użytkownika"""
    email: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    award_scopes: Optional[List[str]] = None


class UserInDB(UserBase):
    """Schema użytkownika w bazie danych (z hashem hasła)"""
    id: int
    hashed_password: Optional[str] = None
    award_scopes: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schema użytkownika w odpowiedzi API (bez hasła)"""
    id: int
    is_admin: bool = False
    award_scopes: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema do logowania"""
    username: str
    password: str


class UserWithToken(UserResponse):
    """Schema użytkownika z tokenem JWT (po zalogowaniu)"""
    access_token: str
    token_type: str = "bearer"
