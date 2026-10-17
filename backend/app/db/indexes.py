"""Creates database indexes. Each member appends only their own collections."""


def ensure_indexes(db) -> None:
    # --- Member 1 ---
    db.users.create_index("email", unique=True)
    db.seller_profiles.create_index("user_id", unique=True)
    db.categories.create_index("slug", unique=True)
    db.subcategories.create_index("slug", unique=True)
    db.subcategories.create_index("category_slug")