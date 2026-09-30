from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class SellerProfileModel(BaseModel):
    """
    Seller profile model for MongoDB documents.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    shop_name: str
    shop_description: Optional[str] = None
    phone: str
    address: str
    is_verified: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        populate_by_name = True