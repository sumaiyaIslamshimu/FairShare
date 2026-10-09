# services/scoring.py

WEIGHTS = {
    "price": 0.40,
    "rating": 0.30,
    "delivery": 0.20,
    "discount": 0.10
}


def rank_listings(listings: list[dict]) -> list[dict]:
    """
    Takes a list of listings, scores them based on relative group stats,
    handles missing data using group averages or neutral defaults,
    and sorts them highest to lowest.
    """
    if not listings:
        return []

    # 1. Calculate safe group stats for relative scoring and missing value fallbacks
    valid_prices = [l.get("price") for l in listings if l.get("price") is not None]
    valid_ratings = [l.get("rating") for l in listings if l.get("rating") is not None]
    valid_deliveries = [l.get("delivery_cost") for l in listings if l.get("delivery_cost") is not None]

    min_price = min(valid_prices) if valid_prices else 0.01
    min_delivery = min(valid_deliveries) if valid_deliveries else 0.0

    # Averages for fallbacks (Ticket requirement: "use a neutral default for example the group average")
    avg_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 3.0
    avg_delivery = sum(valid_deliveries) / len(valid_deliveries) if valid_deliveries else 5.0

    scored_listings = []

    for listing in listings:
        score_breakdown = {}
        total_score = 0.0

        # Price Score (Ticket requirement: "if all listings have the same value... give each the same points")
        price = listing.get("price")
        if price is not None and price > 0:
            price_pts = (min_price / price) * 100 * WEIGHTS["price"]
        else:
            price_pts = 0.0
        score_breakdown["price_points"] = round(price_pts, 2)
        total_score += price_pts

        # Rating Score (Ticket requirement: "if a rating... is missing, use a neutral default")
        rating = listing.get("rating")
        if rating is None:
            rating = avg_rating
        rating_pts = (rating / 5.0) * 100 * WEIGHTS["rating"]
        score_breakdown["rating_points"] = round(rating_pts, 2)
        total_score += rating_pts

        # Delivery Score
        delivery = listing.get("delivery_cost")
        if delivery is None:
            delivery = avg_delivery

        safe_delivery = max(delivery, 0.01)
        safe_min_delivery = max(min_delivery, 0.01)
        delivery_pts = (safe_min_delivery / safe_delivery) * 100 * WEIGHTS["delivery"]
        delivery_pts = min(delivery_pts, 100 * WEIGHTS["delivery"])  # Cap at max points
        score_breakdown["delivery_points"] = round(delivery_pts, 2)
        total_score += delivery_pts

        # Discount Score (Ticket requirement: "if a... discount is missing, use... zero discount")
        discount = listing.get("discount")
        if discount is None:
            discount = 0.0
        discount_pts = min((discount / 50.0) * 100, 100) * WEIGHTS["discount"]
        score_breakdown["discount_points"] = round(discount_pts, 2)
        total_score += discount_pts

        # Attach to listing
        listing["best_value_score"] = min(round(total_score, 2), 100.0)
        listing["score_breakdown"] = score_breakdown
        scored_listings.append(listing)

    # Return sorted by highest best value score
    return sorted(scored_listings, key=lambda x: x["best_value_score"], reverse=True)


