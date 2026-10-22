"""Schemas for shopping cart, simulated checkout, and seller/shopper orders."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


# Seller order progression rule: confirmed -> shipped -> delivered only
SELLER_ALLOWED_TRANSITIONS: dict[str, str] = {
    OrderStatus.confirmed.value: OrderStatus.shipped.value,
    OrderStatus.shipped.value: OrderStatus.delivered.value,
}


class CartItemIn(BaseModel):
    """Client price and seller_id are ignored by design (extra='ignore').
    external_product_id/product_id are captured only so the service can raise 400 NOT_A_FAIRSHARE_PRODUCT."""
    model_config = ConfigDict(extra="ignore")

    seller_product_id: Optional[str] = Field(default=None)
    external_product_id: Optional[str] = Field(default=None, exclude=True)
    product_id: Optional[str] = Field(default=None, exclude=True)
    source: Optional[str] = Field(default=None, exclude=True)
    quantity: int = Field(default=1, ge=1, le=1000)


class CartItemUpdateIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    quantity: int = Field(ge=1, le=1000)


class CartItemOut(BaseModel):
    seller_product_id: str
    seller_id: str
    seller_name: Optional[str] = None
    title: str
    price_paisa: int
    unit_price_paisa: int
    effective_price_paisa: int
    discount_percent: Optional[float] = None
    quantity: int
    stock_qty: int
    line_total_paisa: int
    images: list[str] = Field(default_factory=list)
    currency: str = "BDT"


class CartOut(BaseModel):
    user_id: str
    items: list[CartItemOut] = Field(default_factory=list)
    total_items: int = 0
    subtotal_paisa: int = 0
    total_paisa: int = 0
    currency: str = "BDT"


class CheckoutRequest(BaseModel):
    """Simulated checkout request. Any client-sent price/total is ignored."""
    model_config = ConfigDict(extra="ignore")

    shipping_address: str = Field(min_length=5, max_length=500)
    phone: Optional[str] = Field(default=None, max_length=30)
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("shipping_address")
    @classmethod
    def clean_address(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Shipping address must be at least 5 characters.")
        return v


class PaymentInfoOut(BaseModel):
    mode: str = "simulated"
    status: str = "paid"


class OrderItemOut(BaseModel):
    id: Optional[str] = None
    order_id: str
    seller_id: str
    seller_product_id: str
    title_snapshot: str
    unit_price_paisa: int
    quantity: int
    line_total_paisa: int
    item_status: str


class OrderOut(BaseModel):
    id: str
    order_number: str
    user_id: str
    status: OrderStatus
    subtotal_paisa: int
    total_paisa: int
    currency: str = "BDT"
    payment: PaymentInfoOut
    shipping_address: str
    phone: Optional[str] = None
    notes: Optional[str] = None
    items: list[OrderItemOut] = Field(default_factory=list)
    created_at: str
    updated_at: Optional[str] = None


class OrderPageOut(BaseModel):
    items: list[OrderOut]
    total: int
    page: int
    page_size: int


class SellerOrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: OrderStatus