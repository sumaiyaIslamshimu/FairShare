from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class ViewedProductModel(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    product_id: str
    viewed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Config:
        populate_by_name = True