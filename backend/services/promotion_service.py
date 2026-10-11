"""
Pure promotion logic for SCRUM-203 (discounts + Seller Spotlight).

No FastAPI or MongoDB imports here, so every rule can be tested on its own.
"""

import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

MIN_DISCOUNT_PERCENT = 1
MAX_DISCOUNT_PERCENT = 90
MAX_BATCH_IDS = 100

# Seller Spotlight rules. products.rating uses a 0-5 scale.
MIN_SPOTLIGHT_RATING = 3.0
SPOTLIGHT_MAX_SELLERS = 5
SPOTLIGHT_ROTATION_SECONDS = 3600  # the selection rotates once per hour
DESCRIPTION_MAX_LENGTH = 140


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    """MongoDB returns naive datetimes that were stored as UTC, so a
    naive value read from the database is treated as UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def validate_discount(
    percentage: Any,
    starts_at: Any,
    ends_at: Any,
) -> Tuple[float, datetime, datetime]:
    """Returns (percentage, starts_at_utc, ends_at_utc) or raises ValueError
    with a message that is safe to show to the seller."""
    if isinstance(percentage, bool) or not isinstance(percentage, (int, float)):
        raise ValueError("Discount percentage must be a number")
    if not math.isfinite(percentage):
        raise ValueError("Discount percentage must be a number")
    if percentage < MIN_DISCOUNT_PERCENT or percentage > MAX_DISCOUNT_PERCENT:
        raise ValueError(
            f"Discount percentage must be between {MIN_DISCOUNT_PERCENT} "
            f"and {MAX_DISCOUNT_PERCENT}"
        )

    for label, value in (("Start", starts_at), ("End", ends_at)):
        if not isinstance(value, datetime):
            raise ValueError(f"{label} date/time is required")
        if value.tzinfo is None:
            raise ValueError(f"{label} date/time must include a timezone")

    start_utc = ensure_utc(starts_at)
    end_utc = ensure_utc(ends_at)

    if end_utc <= start_utc:
        raise ValueError("End date/time must be after the start date/time")

    return round(float(percentage), 2), start_utc, end_utc


def calculate_discounted_price(price: float, percentage: float) -> float:
    return round(float(price) * (1 - float(percentage) / 100), 2)


def get_discount_status(discount: Dict[str, Any], now: Optional[datetime] = None) -> str:
    """'upcoming', 'active' or 'expired'. Active means start <= now < end,
    so a discount stops applying by itself when its end time passes."""
    now = now or utc_now()
    start = ensure_utc(discount["starts_at"])
    end = ensure_utc(discount["ends_at"])

    if now < start:
        return "upcoming"
    if now >= end:
        return "expired"
    return "active"


def build_discount_view(listing: Dict[str, Any], now: Optional[datetime] = None) -> Dict[str, Any]:
    """Everything the frontend needs, so it never has to guess whether a
    discount is active. original_price is never modified."""
    original = listing.get("price", 0)
    discount = listing.get("discount")

    view = {
        "listing_id": str(listing["_id"]),
        "original_price": original,
        "has_discount": False,
        "percentage": None,
        "starts_at": None,
        "ends_at": None,
        "status": None,
        "is_active": False,
        "discounted_price": None,
        "effective_price": original,
    }

    if not discount:
        return view

    status = get_discount_status(discount, now)
    discounted = calculate_discounted_price(original, discount["percentage"])

    view.update(
        {
            "has_discount": True,
            "percentage": discount["percentage"],
            "starts_at": ensure_utc(discount["starts_at"]),
            "ends_at": ensure_utc(discount["ends_at"]),
            "status": status,
            "is_active": status == "active",
            "discounted_price": discounted,
            "effective_price": discounted if status == "active" else original,
        }
    )
    return view


def shorten_description(text: Optional[str]) -> Optional[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    if len(cleaned) > DESCRIPTION_MAX_LENGTH:
        return cleaned[: DESCRIPTION_MAX_LENGTH - 1].rstrip() + "…"
    return cleaned


def select_spotlight_sellers(
    candidates: List[Dict[str, Any]],
    now: Optional[datetime] = None,
    limit: int = SPOTLIGHT_MAX_SELLERS,
) -> List[Dict[str, Any]]:
    """
    candidates: dicts with seller_id, business_name, is_verified,
    rating (float or None when the seller has no rated listings) and
    listing_count.

    Eligible: at least one listing, a business name, and either no rating
    yet or a rating of MIN_SPOTLIGHT_RATING or higher.
    Verified sellers come first. Inside each group the order is a shuffle
    seeded by the current hour, so it is stable within an hour, rotates
    between hours, and does not depend on database order.
    """
    eligible = [
        c
        for c in candidates
        if c.get("listing_count", 0) >= 1
        and c.get("business_name")
        and (c.get("rating") is None or c["rating"] >= MIN_SPOTLIGHT_RATING)
    ]

    now = now or utc_now()
    bucket = int(now.timestamp() // SPOTLIGHT_ROTATION_SECONDS)
    rng = random.Random(bucket)

    ordered = sorted(eligible, key=lambda c: c["seller_id"])
    verified = [c for c in ordered if c.get("is_verified")]
    others = [c for c in ordered if not c.get("is_verified")]

    rng.shuffle(verified)
    rng.shuffle(others)

    return (verified + others)[:limit]