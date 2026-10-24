"""Notification schemas (in-app only; nothing is emailed or texted)."""
from typing import Optional

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: str
    kind: str
    title: str
    body: str = ""
    link: str = ""
    is_read: bool
    created_at: Optional[str] = None


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    total: int
    unread: int
    page: int
    page_size: int


class UnreadCount(BaseModel):
    unread: int


class MarkedRead(BaseModel):
    marked: int