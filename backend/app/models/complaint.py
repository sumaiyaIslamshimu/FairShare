"""Complaint schemas (Member 4)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

TargetType = Literal["order", "seller", "rental"]
ComplaintStatus = Literal["open", "in_review", "resolved", "dismissed"]


class ComplaintCreate(BaseModel):
    target_type: TargetType
    target_id: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=10, max_length=2000)

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Please describe the problem in at least 10 characters.")
        return v


class ComplaintOut(BaseModel):
    id: str
    target_type: str
    target_id: str
    description: str
    status: str
    admin_note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ComplaintAdminOut(ComplaintOut):
    filer_id: str
    filer_name: str = ""
    filer_email: str = ""


class ComplaintPage(BaseModel):
    items: list[ComplaintOut]
    total: int
    page: int
    page_size: int


class ComplaintAdminPage(BaseModel):
    items: list[ComplaintAdminOut]
    total: int
    page: int
    page_size: int


class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatus] = None
    admin_note: Optional[str] = Field(default=None, max_length=1000)