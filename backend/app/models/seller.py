"""Pydantic schemas for the Seller Portal: profile, promotions, and insights."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.user import PHONE_RE
from app.services.time_utils import aware


class SellerProfileUpdate(BaseModel):
    """Fields a seller may update on their own profile. status is admin-only."""
    model_config = ConfigDict(extra="ignore")

    business_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    contact_phone: Optional[str] = Field(default=None, max_length=20)
    address: Optional[str] = Field(default=None, max_length=300)

    @field_validator("business_name")
    @classmethod
    def clean_business_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("business_name must be at least 2 characters.")
        return v

    @field_validator("contact_phone")
    @classmethod
    def check_contact_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not PHONE_RE.match(v):
                raise ValueError("Enter a valid contact phone number.")
        return v


class SellerProfileOut(BaseModel):
    id: str
    user_id: str
    business_name: str
    description: str = ""
    contact_phone: str = ""
    address: str = ""
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PromotionCreate(BaseModel):
    """Contract matching product_service.effective_price and docs/DATABASE.md."""
    model_config = ConfigDict(extra="ignore")

    name: str = Field(default="Store Promotion", min_length=1, max_length=120)
    product_ids: list[str] = Field(default_factory=list)
    seller_product_id: Optional[str] = Field(default=None, exclude=True)
    discount_percent: float = Field(ge=1, le=90)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    start_date: Optional[datetime] = Field(default=None, exclude=True)
    end_date: Optional[datetime] = Field(default=None, exclude=True)
    is_active: bool = True

    @model_validator(mode="after")
    def normalize_and_validate(self) -> "PromotionCreate":
        if not self.product_ids and self.seller_product_id:
            self.product_ids = [self.seller_product_id]
        self.product_ids = [pid.strip() for pid in self.product_ids if pid and pid.strip()]
        if not self.product_ids:
            raise ValueError("At least one product ID is required in product_ids.")

        if self.starts_at is None and self.start_date is not None:
            self.starts_at = self.start_date
        if self.ends_at is None and self.end_date is not None:
            self.ends_at = self.end_date

        if self.starts_at is None or self.ends_at is None:
            raise ValueError("Both starts_at and ends_at are required.")

        start_utc = aware(self.starts_at)
        end_utc = aware(self.ends_at)
        if end_utc <= start_utc:
            raise ValueError("ends_at must be strictly after starts_at.")

        self.starts_at = start_utc
        self.ends_at = end_utc
        return self


class PromotionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    product_ids: Optional[list[str]] = None
    discount_percent: Optional[float] = Field(default=None, ge=1, le=90)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_dates_and_products(self) -> "PromotionUpdate":
        if self.product_ids is not None:
            cleaned = [pid.strip() for pid in self.product_ids if pid and pid.strip()]
            if not cleaned:
                raise ValueError("product_ids cannot be empty when provided.")
            self.product_ids = cleaned

        if self.starts_at is not None:
            self.starts_at = aware(self.starts_at)
        if self.ends_at is not None:
            self.ends_at = aware(self.ends_at)

        if self.starts_at is not None and self.ends_at is not None:
            if self.ends_at <= self.starts_at:
                raise ValueError("ends_at must be strictly after starts_at.")
        return self


class PromotionOut(BaseModel):
    id: str
    seller_id: str
    name: str = "Store Promotion"
    product_ids: list[str]
    discount_percent: float
    starts_at: str
    ends_at: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LowStockItemOut(BaseModel):
    id: str
    title: str
    stock_qty: int
    price_paisa: int


class SellerInsightsOut(BaseModel):
    seller_id: str
    total_products: int = 0
    active_products: int = 0
    out_of_stock_products: int = 0
    active_promotions: int = 0
    total_orders: int = 0
    orders_by_status: dict[str, int] = Field(default_factory=dict)
    total_revenue_paisa: int = 0
    total_units_sold: int = 0
    low_stock_items: list[LowStockItemOut] = Field(default_factory=list)