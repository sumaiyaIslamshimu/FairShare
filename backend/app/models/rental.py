"""Schemas for the completely separate Rentals module (listings, requests, bookings, events, messages)."""
from datetime import date
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class RentalListingStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    removed = "removed"


class RentalRequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    cancelled = "cancelled"


class RentalBookingStatus(str, Enum):
    confirmed = "confirmed"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class RentalEventType(str, Enum):
    """Kinds of entries written to the immutable rental event log.

    Names are UPPER_CASE (used in code); stored values are lowercase snake_case.
    Every ``RentalEventType.X`` used anywhere in the backend must exist here.
    """
    LISTING_CREATED = "listing_created"
    LISTING_UPDATED = "listing_updated"
    LISTING_REMOVED = "listing_removed"
    REQUEST_CREATED = "request_created"
    REQUEST_ACCEPTED = "request_accepted"
    REQUEST_REJECTED = "request_rejected"
    REQUEST_CANCELLED = "request_cancelled"
    BOOKING_CREATED = "booking_created"
    BOOKING_ACTIVATED = "booking_activated"
    BOOKING_COMPLETED = "booking_completed"
    BOOKING_CANCELLED = "booking_cancelled"
    MESSAGE_SENT = "message_sent"


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _check_image_urls(urls: list[str]) -> list[str]:
    for url in urls:
        if not url.lower().startswith(("http://", "https://")) or len(url) > 500:
            raise ValueError("Images must be http(s) URLs (max 500 characters).")
    return urls


# --------------------------------------------------------------------------- #
# Listings
# --------------------------------------------------------------------------- #
class RentalListingCreate(BaseModel):
    """Uses NO shopping taxonomy (no category_slug / subcategory_slug)."""
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=2000)
    daily_rate_paisa: int = Field(gt=0, le=1_000_000_000)
    deposit_paisa: int = Field(default=0, ge=0, le=1_000_000_000)
    security_deposit_paisa: Optional[int] = Field(default=None, ge=0, le=1_000_000_000, exclude=True)
    location: str = Field(min_length=2, max_length=200)
    images: list[str] = Field(default_factory=list, max_length=8)
    status: Literal["active", "inactive"] = "active"
    available_from: Optional[date] = None
    available_to: Optional[date] = None

    @field_validator("title", "location")
    @classmethod
    def strip_required_text(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Must be at least 2 characters.")
        return v

    @field_validator("description")
    @classmethod
    def strip_description(cls, v: str) -> str:
        return v.strip()

    @field_validator("images")
    @classmethod
    def check_images(cls, v: list[str]) -> list[str]:
        return _check_image_urls(v)

    @model_validator(mode="after")
    def normalize_deposit_and_window(self) -> "RentalListingCreate":
        if self.deposit_paisa == 0 and self.security_deposit_paisa is not None:
            self.deposit_paisa = self.security_deposit_paisa
        if self.available_from and self.available_to and self.available_to < self.available_from:
            raise ValueError("available_to cannot be before available_from.")
        return self


class RentalListingUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    daily_rate_paisa: Optional[int] = Field(default=None, gt=0, le=1_000_000_000)
    deposit_paisa: Optional[int] = Field(default=None, ge=0, le=1_000_000_000)
    location: Optional[str] = Field(default=None, min_length=2, max_length=200)
    images: Optional[list[str]] = Field(default=None, max_length=8)
    status: Optional[Literal["active", "inactive"]] = None
    available_from: Optional[date] = None
    available_to: Optional[date] = None

    @field_validator("title", "location")
    @classmethod
    def strip_optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Must be at least 2 characters.")
        return v

    @field_validator("images")
    @classmethod
    def check_images(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        return v if v is None else _check_image_urls(v)

    @model_validator(mode="after")
    def check_window(self) -> "RentalListingUpdate":
        if self.available_from and self.available_to and self.available_to < self.available_from:
            raise ValueError("available_to cannot be before available_from.")
        return self


class RentalListingOut(BaseModel):
    id: str
    owner_id: str
    owner_name: Optional[str] = None
    title: str
    description: str = ""
    daily_rate_paisa: int
    deposit_paisa: int = 0
    currency: str = "BDT"
    location: str
    images: list[str] = Field(default_factory=list)
    status: str = "active"
    available_from: Optional[str] = None
    available_to: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RentalListingPageOut(BaseModel):
    items: list[RentalListingOut]
    total: int
    page: int
    page_size: int


# --------------------------------------------------------------------------- #
# Requests
# --------------------------------------------------------------------------- #
class RentalRequestCreate(BaseModel):
    """Date range validation: end_date < start_date triggers 422 VALIDATION_ERROR."""
    model_config = ConfigDict(extra="ignore")

    listing_id: str = Field(min_length=1)
    start_date: date
    end_date: date
    note: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_date_range(self) -> "RentalRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        return self


class RentalRequestDecision(BaseModel):
    """The owner's decision on a pending rental request.

    Only these two words are accepted, so a typo can never be treated as an accept.
    """
    action: Literal["accept", "reject"]


class RentalRequestOut(BaseModel):
    id: str
    listing_id: str
    listing_title: Optional[str] = None
    owner_id: str
    renter_id: str
    start_date: str
    end_date: str
    days: int
    daily_rate_paisa: int
    deposit_paisa: int
    total_paisa: int
    status: RentalRequestStatus
    note: Optional[str] = None
    booking_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# --------------------------------------------------------------------------- #
# Bookings and events
# --------------------------------------------------------------------------- #
class RentalBookingOut(BaseModel):
    id: str
    request_id: str
    listing_id: str
    listing_title: Optional[str] = None
    owner_id: str
    renter_id: str
    start_date: str
    end_date: str
    days: int
    daily_rate_paisa: int
    deposit_paisa: int
    total_paisa: int
    status: RentalBookingStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RentalEventOut(BaseModel):
    id: str
    booking_id: Optional[str] = None
    request_id: Optional[str] = None
    listing_id: Optional[str] = None
    event: str
    actor_id: str
    at: str


# --------------------------------------------------------------------------- #
# Messages
# --------------------------------------------------------------------------- #
class RentalMessageIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    body: Optional[str] = Field(default=None, max_length=2000)
    content: Optional[str] = Field(default=None, max_length=2000, exclude=True)

    @model_validator(mode="after")
    def check_body(self) -> "RentalMessageIn":
        text = (self.body if self.body is not None else self.content) or ""
        text = text.strip()
        if not text:
            raise ValueError("Message body cannot be empty.")
        self.body = text
        return self


class RentalMessageOut(BaseModel):
    id: str
    request_id: str
    sender_id: str
    body: str
    created_at: str