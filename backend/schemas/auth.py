from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """
    Schema for user registration.
    """

    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default="buyer")


class LoginRequest(BaseModel):
    """
    Schema for user login.
    """

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Schema for authentication response.
    """

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    Schema for returning user information.
    """

    id: str
    name: str
    email: EmailStr
    role: str
    is_active: bool