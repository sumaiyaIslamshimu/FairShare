"""Admin schemas: statistics, users, verification review, moderation, categories, monitor, audit."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class Page(BaseModel):
    total: int
    page: int
    page_size: int


class StatsOut(BaseModel):
    users: dict
    sellers: dict
    verifications: dict
    products: dict
    orders: dict
    rentals: dict
    complaints: dict
    scraping: dict


class AdminUserOut(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str
    role: str
    is_active: bool
    verification_status: str
    seller_status: Optional[str] = None
    created_at: Optional[str] = None


class AdminUserPage(Page):
    items: list[AdminUserOut]


class UserActiveUpdate(BaseModel):
    is_active: bool


class AdminSellerOut(BaseModel):
    user_id: str
    business_name: str
    full_name: str
    email: str
    status: str
    verification_status: str
    created_at: Optional[str] = None


class AdminSellerPage(Page):
    items: list[AdminSellerOut]


class SellerStatusUpdate(BaseModel):
    status: Literal["approved", "rejected", "suspended", "pending"]


class VerificationReviewOut(BaseModel):
    """Admin view. The NID is ALWAYS masked: only the last 4 digits are ever shown."""
    id: str
    user_id: str
    user_name: str
    user_email: str
    user_role: str
    nid_masked: str
    has_document: bool
    document_type: Optional[str] = None
    status: str
    note: Optional[str] = None
    submitted_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None


class VerificationReviewPage(Page):
    items: list[VerificationReviewOut]


class VerificationDecision(BaseModel):
    decision: Literal["approve", "reject"]
    note: Optional[str] = Field(default=None, max_length=500)


class ProductModerationOut(BaseModel):
    id: str
    title: str
    seller_id: str
    seller_name: str = ""
    price_paisa: int
    stock_qty: int
    status: str
    moderation_status: str
    category_slug: str = ""
    subcategory_slug: str = ""


class ProductModerationPage(Page):
    items: list[ProductModerationOut]


class ProductModerationUpdate(BaseModel):
    moderation_status: Literal["visible", "hidden", "removed"]


class RentalModerationOut(BaseModel):
    id: str
    title: str
    owner_id: str
    owner_name: str = ""
    location: str = ""
    daily_rate_paisa: int
    status: str


class RentalModerationPage(Page):
    items: list[RentalModerationOut]


class RentalModerationUpdate(BaseModel):
    status: Literal["active", "inactive", "removed"]


class CategoryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=60, pattern=SLUG_PATTERN)
    name: str = Field(min_length=2, max_length=80)
    order: Optional[int] = Field(default=None, ge=0, le=1000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class CategoryUpdate(BaseModel):
    """The slug never changes (listings refer to it)."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    order: Optional[int] = Field(default=None, ge=0, le=1000)
    is_active: Optional[bool] = None


class SubcategoryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=60, pattern=SLUG_PATTERN)
    category_slug: str = Field(min_length=2, max_length=60)
    name: str = Field(min_length=2, max_length=80)


class SubcategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    is_active: Optional[bool] = None


class AuditOut(BaseModel):
    id: str
    actor_id: str
    actor_email: str = ""
    action: str
    target: str
    details: dict = {}
    at: Optional[str] = None


class AuditPage(Page):
    items: list[AuditOut]