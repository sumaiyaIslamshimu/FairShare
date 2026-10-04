from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class PriceAlertModel(BaseModel):
    """
    Price alert model for MongoDB documents.
    """

    id: Optional[str] = Field(
        default=None,
        alias="_id",
    )

    user_id: str

    product_id: str

    target_price: float

    status: str = "active"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    triggered_at: Optional[datetime] = None

    class Config:
        populate_by_name = True