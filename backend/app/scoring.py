"""
Best-value scoring engine for FairShare listings (SCRUM-131 / Backend 1.2).
"""

from typing import Optional, Tuple, Dict


PRICE_WEIGHT = 40.0
RATING_WEIGHT = 25.0
DELIVERY_WEIGHT = 15.0
DISCOUNT_WEIGHT = 20.0

DELIVERY_COST_CAP = 200.0
DISCOUNT_PERCENT_CAP = 100.0
RATING_MAX = 5.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def calculate_price_points(
    price: float,
    group_min_price: float,
    group_max_price: float
) -> float:

    if group_max_price == group_min_price:
        return PRICE_WEIGHT

    ratio = (group_max_price - price) / (
        group_max_price - group_min_price
    )

    return _clamp(
        PRICE_WEIGHT * ratio,
        0.0,
        PRICE_WEIGHT
    )


def calculate_rating_points(
    rating: Optional[float]
) -> float:

    if rating is None:
        return RATING_WEIGHT / 2

    ratio = rating / RATING_MAX

    return _clamp(
        RATING_WEIGHT * ratio,
        0.0,
        RATING_WEIGHT
    )


def calculate_delivery_points(
    delivery_cost: Optional[float]
) -> float:

    if delivery_cost is None:
        return DELIVERY_WEIGHT / 2

    capped = _clamp(
        delivery_cost,
        0.0,
        DELIVERY_COST_CAP
    )

    ratio = 1 - (
        capped / DELIVERY_COST_CAP
    )

    return _clamp(
        DELIVERY_WEIGHT * ratio,
        0.0,
        DELIVERY_WEIGHT
    )


def calculate_discount_points(
    discount: Optional[float]
) -> float:

    if discount is None:
        return DISCOUNT_WEIGHT / 2

    capped = _clamp(
        discount,
        0.0,
        DISCOUNT_PERCENT_CAP
    )

    ratio = capped / DISCOUNT_PERCENT_CAP

    return _clamp(
        DISCOUNT_WEIGHT * ratio,
        0.0,
        DISCOUNT_WEIGHT
    )


def score_listing(
    price: float,
    rating: Optional[float],
    delivery_cost: Optional[float],
    discount: Optional[float],
    group_min_price: float,
    group_max_price: float,
) -> Tuple[float, Dict[str, float]]:

    price_points = round(
        calculate_price_points(
            price,
            group_min_price,
            group_max_price
        ),
        2
    )

    rating_points = round(
        calculate_rating_points(rating),
        2
    )

    delivery_points = round(
        calculate_delivery_points(delivery_cost),
        2
    )

    discount_points = round(
        calculate_discount_points(discount),
        2
    )

    breakdown = {
        "price_points": price_points,
        "rating_points": rating_points,
        "delivery_points": delivery_points,
        "discount_points": discount_points,
    }

    total = (
        price_points
        + rating_points
        + delivery_points
        + discount_points
    )

    total = round(
        _clamp(total, 0.0, 100.0),
        2
    )

    return total, breakdown


def rank_listings(listings: list) -> list:

    if not listings:
        return []

    prices = [
        listing["price"]
        for listing in listings
    ]

    group_min_price = min(prices)
    group_max_price = max(prices)

    scored = []

    for listing in listings:

        total, breakdown = score_listing(
            price=listing["price"],
            rating=listing.get("rating"),
            delivery_cost=listing.get("delivery_cost"),
            discount=listing.get("discount"),
            group_min_price=group_min_price,
            group_max_price=group_max_price,
        )

        scored_listing = dict(listing)

        scored_listing["score"] = total
        scored_listing["score_breakdown"] = breakdown

        scored.append(scored_listing)

    scored.sort(
        key=lambda item: (
            -item["score"],
            item["price"]
        )
    )

    return scored