"""Return-request schemas: a shopper asks to return a delivered item; the seller (or an admin) decides."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

Reason = Literal["damaged", "wrong_item", "not_as_described", "changed_mind", "other"]


class ReturnCreate(BaseModel):
    order_item_id: str = Field(min_length=1, max_length=64)
    reason: Reason
    details: str = Field(default="", max_length=1000)

    @field_validator("details")
    @classmethod
    def strip_details(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def other_needs_details(self):
        if self.reason == "other" and len(self.details) < 10:
            raise ValueError("Please explain the reason in at least 10 characters.")
        return self


class ReturnDecision(BaseModel):
    action: Literal["approve", "reject", "complete"]
    note: str = Field(default="", max_length=500)

    @field_validator("note")
    @classmethod
    def strip_note(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def reject_needs_note(self):
        if self.action == "reject" and not self.note:
            raise ValueError("Give the shopper a reason when rejecting.")
        return self


class ReturnOut(BaseModel):
    id: str
    order_id: str
    order_item_id: str
    product_title: str = ""
    quantity: int
    refund_paisa: int
    currency: str = "BDT"
    refund_mode: str = "simulated"
    reason: str
    details: str = ""
    status: str
    seller_note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ReturnStaffOut(ReturnOut):
    shopper_name: str = ""
    shopper_email: str = ""
    seller_id: str


class ReturnPage(BaseModel):
    items: list[ReturnOut]
    total: int
    page: int
    page_size: int


class ReturnStaffPage(BaseModel):
    items: list[ReturnStaffOut]
    total: int
    page: int
    page_size: int