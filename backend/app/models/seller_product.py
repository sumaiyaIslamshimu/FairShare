"""Schemas for FairShare seller products (the ONLY products that can be bought)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SellerProductCreate(BaseModel):
    """Used for both POST (create) and PUT (full update). seller_id/moderation/source are never read from the client."""
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=2000)
    brand: Optional[str] = Field(default=None, max_length=80)
    category_slug: str = Field(min_length=1, max_length=60)
    subcategory_slug: str = Field(min_length=1, max_length=60)
    price_paisa: int = Field(gt=0, le=1_000_000_000)           # BDT x 100
    stock_qty: int = Field(ge=0, le=1_000_000)
    images: list[str] = Field(default_factory=list, max_length=8)  # URLs only, no uploads
    quantity: Optional[float] = Field(default=None, gt=0)      # in g / ml / pcs / pack
    unit: Optional[Literal["g", "ml", "pcs", "pack"]] = None
    attributes: dict[str, str] = Field(default_factory=dict)
    status: Literal["active", "inactive"] = "active"

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Title is too short.")
        return v

    @field_validator("brand")
    @classmethod
    def clean_brand(cls, v):
        v = (v or "").strip()
        return v or None

    @field_validator("images")
    @classmethod
    def check_images(cls, v: list[str]) -> list[str]:
        for url in v:
            if not url.lower().startswith(("http://", "https://")) or len(url) > 500:
                raise ValueError("Images must be http(s) URLs (max 500 characters).")
        return v

    @field_validator("attributes")
    @classmethod
    def check_attributes(cls, v: dict[str, str]) -> dict[str, str]:
        if len(v) > 20 or any(len(k) > 100 or len(x) > 100 for k, x in v.items()):
            raise ValueError("Max 20 attributes, each key/value up to 100 characters.")
        return v

    @model_validator(mode="after")
    def quantity_and_unit_together(self):
        if (self.quantity is None) != (self.unit is None):
            raise ValueError("Give both quantity and unit, or neither.")
        return self


class InventoryUpdate(BaseModel):
    stock_qty: int = Field(ge=0, le=1_000_000)


class SellerProductPublic(BaseModel):
    id: str
    seller_id: str
    seller_name: Optional[str] = None
    title: str
    description: str = ""
    brand: Optional[str] = None
    category_slug: str
    subcategory_slug: str
    price_paisa: int
    effective_price_paisa: int
    discount_percent: Optional[float] = None
    currency: str
    availability: str
    images: list[str] = []
    quantity: Optional[float] = None
    unit: Optional[str] = None
    attributes: dict = {}
    source: str


class SellerProductOwner(SellerProductPublic):
    stock_qty: int
    status: str
    moderation_status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SellerProductPage(BaseModel):
    items: list[SellerProductPublic]
    total: int
    page: int
    page_size: int


class OwnerProductPage(BaseModel):
    items: list[SellerProductOwner]
    total: int
    page: int
    page_size: int