from datetime import datetime

from pydantic import BaseModel, Field


class PriceAlertCreate(BaseModel):
    """
    Schema for creating a price alert.
    """

    product_id: str

    target_price: float = Field(
        ...,
        gt=0,
    )


class PriceAlertResponse(BaseModel):
    """
    Schema for returning price alert information.
    """

    id: str

    user_id: str

    product_id: str

    product_name: str

    current_lowest_price: float

    target_price: float

    status: str

    created_at: datetime

    triggered_at: datetime | None = None