# services/scoring.py

# Ticket Requirements: Price 40, rating 30, delivery cost 20, discount 10.
WEIGHTS = {
    "price": 0.40,
    "rating": 0.30,
    "delivery": 0.20,
    "discount": 0.10
}


def rank_listings(listings: list[dict]) -> list[dict]:
    """
    Takes a list of listings, calculates relative group stats,
    and returns them with total scores (0-100) and score breakdowns.
    """
    if not listings:
        return []

    # 1. Calculate group stats to scale relatively to other listings
    valid_prices = [l["price"] for l in listings if l.get("price")]
    valid_deliveries = [l["delivery_cost"] for l in listings if l.get("delivery_cost") is not None]

    group_stats = {
        "min_price": min(valid_prices) if valid_prices else 0,
        "min_delivery": min(valid_deliveries) if valid_deliveries else 0
    }

    scored_listings = []

    # 2. Score each listing
    for listing in listings:
        score_breakdown = {}
        total_score = 0.0

        # Price Score (Inverse: cheapest relative to group scores highest)
        price_pts = (group_stats["min_price"] / listing["price"]) * 100 * WEIGHTS["price"]
        score_breakdown["price_points"] = round(price_pts, 2)
        total_score += price_pts

        # Rating Score (Direct: highest rating out of 5 scores highest)
        rating_pts = (listing["rating"] / 5.0) * 100 * WEIGHTS["rating"]
        score_breakdown["rating_points"] = round(rating_pts, 2)
        total_score += rating_pts

        # Delivery Score (Inverse: lowest delivery relative to group scores highest)
        safe_delivery = max(listing["delivery_cost"], 0.01)
        safe_min_delivery = max(group_stats["min_delivery"], 0.01)
        delivery_pts = (safe_min_delivery / safe_delivery) * 100 * WEIGHTS["delivery"]
        score_breakdown["delivery_points"] = round(delivery_pts, 2)
        total_score += delivery_pts

        # Discount Score (Direct: assumed 50% discount is max cap)
        discount_pts = min((listing["discount"] / 50.0) * 100, 100) * WEIGHTS["discount"]
        score_breakdown["discount_points"] = round(discount_pts, 2)
        total_score += discount_pts

        # Attach to listing
        listing["best_value_score"] = min(round(total_score, 2), 100.0)
        listing["score_breakdown"] = score_breakdown
        scored_listings.append(listing)

    # Return sorted by best value score
    return sorted(scored_listings, key=lambda x: x["best_value_score"], reverse=True)


