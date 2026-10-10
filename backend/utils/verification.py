async def verified_map(db, seller_names):
    """Returns {seller business name: is_verified} for the given names."""
    names = list({n for n in seller_names if n})

    if not names:
        return {}

    cursor = db.sellers.find(
        {"businessName": {"$in": names}},
        {"_id": 0, "businessName": 1, "is_verified": 1},
    )

    return {
        s["businessName"]: s.get("is_verified", False)
        async for s in cursor
    }