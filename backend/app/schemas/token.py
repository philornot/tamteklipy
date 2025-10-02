"""
Pydantic schemas dla JWT tokenów
"""
from typing import Optional, List

from pydantic import BaseModel


class Token(BaseModel):
    """Schema tokenu JWT"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema danych w tokenie JWT"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: List[str] = []
