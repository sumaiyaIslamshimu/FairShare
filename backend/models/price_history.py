from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class PriceHistoryModel(BaseModel):
    """
    Price history model for MongoDB documents.
    """

    id: Optional[str] = Field(
        default=None,
        alias="_id",
    )

    product_id: str

    price: float

    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        populate_by_name = True