"""Schemas for the comparison API (external stores + FairShare listings in one shape)."""
from typing import Optional

from pydantic import BaseModel


class CompareItem(BaseModel):
    id: str
    source: str                      # "external" | "fairshare"
    store: str                       # daraz, pickaboo, ... or "fairshare"
    store_name: str
    seller_name: Optional[str] = None
    name: str
    brand: Optional[str] = None
    price_paisa: int                 # the price to pay now (FairShare: after promotion)
    original_price_paisa: Optional[int] = None
    discount_percent: Optional[float] = None
    currency: Optional[str] = None   # "BDT" only when confirmed; None means "not stated"
    image_url: Optional[str] = None
    availability: str                # in_stock | out_of_stock | unknown
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category_slug: Optional[str] = None
    subcategory_slug: Optional[str] = None
    freshness: str                   # fresh | stale | unavailable
    last_updated: Optional[str] = None
    store_url: Optional[str] = None  # external products only: link to the original store
    group_key: Optional[str] = None
    group_size: int = 1


class SearchPage(BaseModel):
    items: list[CompareItem]
    total: int
    page: int
    page_size: int


class PossibleMatchOut(BaseModel):
    item: CompareItem
    score: float
    reasons: list[str]
    differences: list[dict]


class GroupOut(BaseModel):
    group_key: str
    exact: list[CompareItem]
    possible: list[PossibleMatchOut]
    cheapest_id: Optional[str] = None  # cheapest FRESH, not-out-of-stock exact match; None if none qualifies


class SourceStatusOut(BaseModel):
    store: str
    store_name: str
    configured: bool
    status: str                      # success | partial | failure | unsupported | never_run
    last_attempt_at: Optional[str] = None
    last_success_at: Optional[str] = None
    items_found: int = 0
    robots_allowed: Optional[bool] = None
    notes: list[str] = []
    last_error: Optional[str] = None