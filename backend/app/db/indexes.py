"""Creates database indexes. Each member appends only their own collections."""


def ensure_indexes(db) -> None:
    # --- Member 1 ---
    db.users.create_index("email", unique=True)
    db.seller_profiles.create_index("user_id", unique=True)
    db.categories.create_index("slug", unique=True)
    db.subcategories.create_index("slug", unique=True)
    db.subcategories.create_index("category_slug")

    # --- Member 2 ---
    db.seller_products.create_index("seller_id")
    db.seller_products.create_index([("category_slug", 1), ("subcategory_slug", 1)])
    db.seller_products.create_index("group_key")
    db.external_products.create_index([("store", 1), ("store_product_id", 1)], unique=True)
    db.external_products.create_index("normalized_key")
    db.external_products.create_index("category_slug")
    db.external_products.create_index("group_key")
    db.price_observations.create_index([("external_product_id", 1), ("observed_at", 1)])
    db.product_matches.create_index("group_key", unique=True)
    db.scrape_sources.create_index("store", unique=True)
    db.scrape_runs.create_index([("store", 1), ("started_at", 1)])

    # --- Member 3 ---
    db.promotions.create_index("seller_id")
    # --- Member 3 ---
    db.promotions.create_index("seller_id")
    db.carts.create_index("user_id", unique=True)
    # --- Member 3 ---
    db.promotions.create_index("seller_id")
    db.carts.create_index("user_id", unique=True)
    db.orders.create_index("user_id")
    db.order_items.create_index("order_id")
    db.order_items.create_index("seller_id")
    # --- Member 3 ---
    db.promotions.create_index("seller_id")
    db.carts.create_index("user_id", unique=True)
    db.orders.create_index("user_id")
    db.order_items.create_index("order_id")
    db.order_items.create_index("seller_id")
    db.messages.create_index("participants")
    db.messages.create_index("thread_id")
    # --- Member 3 ---
    db.rental_listings.create_index("owner_id")
    db.rental_requests.create_index("listing_id")
    db.rental_bookings.create_index("listing_id")
    db.rental_events.create_index("listing_id")
    # --- Member 4 ---