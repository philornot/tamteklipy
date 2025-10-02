"""
Pydantic schemas dla User
"""
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Bazowe pola użytkownika"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    """Schema do tworzenia użytkownika"""
    password: str = Field(..., min_length=8, max_length=100)
    award_scopes: Optional[List[str]] = Field(default_factory=list)

    @validator('password')
    def validate_password(cls, v):
        """Walidacja siły hasła"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną cyfrę')
        if not any(char.isupper() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną wielką literę')
        if not any(char.islower() for char in v):
            raise ValueError('Hasło musi zawierać przynajmniej jedną małą literę')
        return v

    @validator('username')
    def validate_username(cls, v):
        """Walidacja nazwy użytkownika"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username może zawierać tylko litery, cyfry, _ i -')
        return v.lower()  # Zawsze lowercase


class UserUpdate(BaseModel):
    """Schema do aktualizacji użytkownika"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    award_scopes: Optional[List[str]] = None

    @validator('password')
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
    hashed_password: str
    award_scopes: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True  # Umożliwia tworzenie z modeli SQLAlchemy


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
