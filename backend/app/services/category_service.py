"""The one authoritative category system. Every module validates through here."""
from app.core.errors import AppError


def list_tree(db, include_inactive: bool = False) -> list[dict]:
    cat_filter = {} if include_inactive else {"is_active": True}
    sub_filter = {} if include_inactive else {"is_active": True}
    subs_by_cat: dict[str, list[dict]] = {}
    for s in db.subcategories.find(sub_filter).sort("name", 1):
        subs_by_cat.setdefault(s["category_slug"], []).append({"slug": s["slug"], "name": s["name"]})
    tree = []
    for c in db.categories.find(cat_filter).sort("order", 1):
        tree.append({"slug": c["slug"], "name": c["name"], "subcategories": subs_by_cat.get(c["slug"], [])})
    return tree


def validate_category_pair(db, category_slug: str, subcategory_slug: str) -> None:
    """Raises 422 unless the subcategory exists, is active, and belongs to the active category."""
    category = db.categories.find_one({"slug": category_slug, "is_active": True})
    sub = db.subcategories.find_one(
        {"slug": subcategory_slug, "category_slug": category_slug, "is_active": True}
    )
    if not category or not sub:
        raise AppError(422, "INVALID_CATEGORY", "Choose a valid category and matching subcategory.")