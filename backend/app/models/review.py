"""Review schemas: a shopper rates a product they actually received."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ReviewCreate(BaseModel):
    order_item_id: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, v: str) -> str:
        return v.strip()


class ReviewUpdate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, v: str) -> str:
        return v.strip()


class ReviewPublic(BaseModel):
    """What other shoppers see: first name only, never an email or an id of the person."""
    id: str
    product_id: str
    rating: int
    comment: str = ""
    reviewer_name: str = ""
    created_at: Optional[str] = None


class ReviewOwn(ReviewPublic):
    order_item_id: str
    product_title: str = ""
    status: str


class ReviewSeller(ReviewPublic):
    product_title: str = ""
    status: str


class ReviewAdmin(ReviewOwn):
    seller_id: str
    reviewer_email: str = ""


class ReviewPublicPage(BaseModel):
    items: list[ReviewPublic]
    total: int
    page: int
    page_size: int
    average: Optional[float] = None
    count: int = 0


class ReviewOwnPage(BaseModel):
    items: list[ReviewOwn]
    total: int
    page: int
    page_size: int


class ReviewSellerPage(BaseModel):
    items: list[ReviewSeller]
    total: int
    page: int
    page_size: int
    average: Optional[float] = None


class ReviewAdminPage(BaseModel):
    items: list[ReviewAdmin]
    total: int
    page: int
    page_size: int


class ReviewModeration(BaseModel):
    status: Literal["visible", "hidden"]