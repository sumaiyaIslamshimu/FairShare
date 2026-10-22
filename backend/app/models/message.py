"""Schemas for shared messaging (/api/messages) between participants."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MessageCreateIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipient_id: Optional[str] = None
    seller_id: Optional[str] = Field(default=None, exclude=True)
    customer_id: Optional[str] = Field(default=None, exclude=True)
    body: Optional[str] = Field(default=None, max_length=2000)
    content: Optional[str] = Field(default=None, max_length=2000, exclude=True)
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    request_id: Optional[str] = None

    @model_validator(mode="after")
    def normalize_fields(self) -> "MessageCreateIn":
        target = self.recipient_id or self.seller_id or self.customer_id
        if not target or not target.strip():
            raise ValueError("recipient_id is required.")
        self.recipient_id = target.strip()

        text = (self.body if self.body is not None else self.content) or ""
        text = text.strip()
        if not text:
            raise ValueError("Message body cannot be empty.")
        if len(text) > 2000:
            raise ValueError("Message body cannot exceed 2000 characters.")
        self.body = text
        return self


class MessageOut(BaseModel):
    id: str
    thread_id: str
    customer_id: str
    seller_id: str
    participants: list[str]
    sender_id: str
    recipient_id: str
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    request_id: Optional[str] = None
    body: str
    read: bool = False
    created_at: str


class ThreadSummaryOut(BaseModel):
    thread_id: str
    participants: list[str]
    customer_id: str
    seller_id: str
    order_id: Optional[str] = None
    product_id: Optional[str] = None
    last_message: MessageOut
    unread_count: int = 0