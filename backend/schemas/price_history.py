from datetime import datetime

from pydantic import BaseModel


class PriceHistoryResponse(BaseModel):
    """
    Schema for returning product price history.
    """

    id: str

    product_id: str

    price: float

    recorded_at: datetime