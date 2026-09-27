from typing import Optional

from pydantic import BaseModel, Field


class SellerProfileCreate(BaseModel):
    """
    Schema for creating a seller profile.
    """

    shop_name: str = Field(..., min_length=2, max_length=150)
    shop_description: Optional[str] = Field(
        default=None,
        max_length=1000,
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class SellerProfileUpdate(BaseModel):
    """
    Schema for updating a seller profile.
    """

    shop_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    shop_description: Optional[str] = Field(
        default=None,
        max_length=1000,
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
    )
    address: Optional[str] = Field(
        default=None,
        max_length=500,
    )


class SellerProfileResponse(BaseModel):
    """
    Schema for returning seller profile information.
    """

    id: str
    user_id: str
    shop_name: str
    shop_description: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_verified: bool