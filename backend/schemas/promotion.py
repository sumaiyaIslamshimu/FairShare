from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class DiscountIn(BaseModel):
    percentage: float
    starts_at: datetime
    ends_at: datetime


class DiscountView(BaseModel):
    listing_id: str
    original_price: float
    has_discount: bool
    percentage: Optional[float] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    status: Optional[str] = None  # "upcoming" | "active" | "expired"
    is_active: bool = False
    discounted_price: Optional[float] = None
    effective_price: float


class ActiveDiscount(BaseModel):
    percentage: float
    original_price: float
    discounted_price: float
    ends_at: datetime


class ActiveDiscountsResponse(BaseModel):
    discounts: Dict[str, ActiveDiscount]


class SpotlightSeller(BaseModel):
    seller_id: str
    business_name: str
    is_verified: bool
    rating: Optional[float] = None
    description: Optional[str] = None
    listing_count: int