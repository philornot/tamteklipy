"""
Pydantic schemas for password reset functionality
"""
from pydantic import BaseModel, Field, EmailStr


class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset"""
    email: EmailStr = Field(..., description="User's email address")


class PasswordResetResponse(BaseModel):
    """Generic success response for password reset request"""
    message: str = Field(
        default="If the email exists, a password reset link has been sent",
        description="Generic message for security"
    )


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset with token"""
    token: str = Field(..., min_length=40, max_length=100, description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")