from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class RentalRequestModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")

    product_id: str
    shopper_id: str
    owner_id: str

    start_date: str
    end_date: str
    total_days: int
    total_cost: float

    status: str = "pending"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        populate_by_name = True