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


class UserCreate(UserBase):
    """Schema do tworzenia użytkownika"""
    password: Optional[str] = Field(None, min_length=8, max_length=100)  # Opcjonalne
    award_scopes: Optional[List[str]] = Field(default_factory=list)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Walidacja siły hasła (jeśli podane)"""
        if v is None or v == "":
            return None
        if not any(char.isdigit() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną cyfrę')
        if not any(char.isupper() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną wielką literę')
        if not any(char.islower() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną małą literę')
        return v

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
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    award_scopes: Optional[List[str]] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Walidacja siły hasła"""
        if v is None:
            return v
        if not any(char.isdigit() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną cyfrę')
        if not any(char.isupper() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną wielką literę')
        if not any(char.islower() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną małą literę')
        return v


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
