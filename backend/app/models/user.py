"""Pydantic schemas for users and authentication."""
import re
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

PHONE_RE = re.compile(r"^\+?[0-9\- ]{7,20}$")


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str
    password: str = Field(min_length=8, max_length=72)  # bcrypt limit is 72 bytes
    role: Literal["user", "seller"] = "user"  # "admin" is rejected here on purpose
    business_name: Optional[str] = Field(default=None, max_length=120)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        if not PHONE_RE.match(v):
            raise ValueError("Enter a valid phone number.")
        return v

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password is too long (max 72 bytes).")
        return v

    @model_validator(mode="after")
    def seller_needs_business_name(self):
        if self.role == "seller" and not (self.business_name or "").strip():
            raise ValueError("business_name is required for sellers.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserPublic(BaseModel):
    """Safe user shape. Never includes password_hash or identity data."""
    id: str
    full_name: str
    email: str
    phone: str
    role: str
    is_active: bool
    verification_status: str
    seller_status: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic