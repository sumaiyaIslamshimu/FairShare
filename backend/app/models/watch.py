"""Price-watch schemas: a shopper follows an offer (an external store listing or a FairShare product)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class WatchCreate(BaseModel):
    source: Literal["external", "fairshare"]
    product_id: str = Field(min_length=1, max_length=64)
    target_price_paisa: Optional[int] = Field(default=None, gt=0, le=1_000_000_000)  # alert at or below this; None = any drop


class WatchUpdate(BaseModel):
    target_price_paisa: Optional[int] = Field(default=None, gt=0, le=1_000_000_000)  # None clears the target


class WatchOut(BaseModel):
    id: str
    source: str
    product_id: str
    name: str = ""
    store_name: str = ""
    store_url: Optional[str] = None      # external offers only: where to buy
    image_url: Optional[str] = None
    currency: Optional[str] = None
    availability: str = "unknown"
    freshness: str = "fresh"
    price_when_added_paisa: int
    current_price_paisa: Optional[int] = None   # None when the offer no longer exists / is not for sale
    lowest_seen_paisa: Optional[int] = None
    target_price_paisa: Optional[int] = None
    change_paisa: Optional[int] = None          # current minus price when added (negative = cheaper)
    status: str                                  # target_reached | dropped | unchanged | increased | unavailable
    created_at: Optional[str] = None


class WatchPage(BaseModel):
    items: list[WatchOut]
    total: int
    page: int
    page_size: int


class WatchRef(BaseModel):
    id: str
    source: str
    product_id: str


class PricePoint(BaseModel):
    price_paisa: int
    availability: Optional[str] = None
    observed_at: Optional[str] = None


class WatchHistory(BaseModel):
    available: bool          # FairShare prices have no stored history; only the price when added is known
    points: list[PricePoint]