"""Saves normalized external products, price history, and scrape status/run records (sync PyMongo)."""
from app.scrapers.category_map import map_category
from app.scrapers.matcher import exact_group_key
from app.services.match_service import sync_group
from app.services.time_utils import utcnow


def _size_text(n):
    return f"{n.quantity:g} {n.unit}" if n.quantity is not None and n.unit else None


def save_normalized(db, products, now=None) -> dict:
    """Upserts by (store, store_product_id). A price observation is appended only when the price or
    availability changed (append-only history). Duplicates inside one run are counted, not stored twice."""
    now = now or utcnow()
    stats = {"inserted": 0, "updated": 0, "price_changes": 0, "duplicates_in_run": 0, "needs_review": 0}
    seen, touched = set(), set()
    for n in products:
        sid = n.store_product_id or n.product_url
        if (n.store, sid) in seen:
            stats["duplicates_in_run"] += 1
            continue
        seen.add((n.store, sid))
        mapping = map_category(n.category_text, n.name)
        mapped = mapping.status == "mapped"
        if not mapped:
            stats["needs_review"] += 1
        key = exact_group_key({"name": n.name, "brand": n.brand, "quantity": n.quantity, "unit": n.unit})
        fields = {
            "name": n.name, "brand": n.brand, "model": None,
            "price_paisa": n.price_paisa, "original_price_paisa": n.original_price_paisa,
            "discount_percent": n.discount_percent, "currency": n.currency,
            "image_url": n.image_url, "product_url": n.product_url,
            "category_slug": mapping.category_slug if mapped else None,
            "subcategory_slug": mapping.subcategory_slug if mapped else None,
            "category_status": mapping.status, "category_text": n.category_text,
            "specs": {}, "quantity": n.quantity, "unit": n.unit, "package_size": _size_text(n),
            "availability": n.availability, "normalized_key": n.normalized_key, "group_key": key,
            "last_seen_at": now, "last_successful_at": now, "freshness": "fresh",
            "source": "external", "updated_at": now,
        }
        where = {"store": n.store, "store_product_id": sid}
        existing = db.external_products.find_one(where)
        db.external_products.update_one(where, {"$set": fields, "$setOnInsert": {"first_seen_at": now}}, upsert=True)
        doc = db.external_products.find_one(where)
        changed_price = existing is not None and existing.get("price_paisa") != n.price_paisa
        stats["inserted" if existing is None else "updated"] += 1
        if changed_price:
            stats["price_changes"] += 1
        if existing is None or changed_price or existing.get("availability") != n.availability:
            db.price_observations.insert_one({
                "external_product_id": doc["_id"], "price_paisa": n.price_paisa,
                "availability": n.availability, "observed_at": now})
        for k in (existing.get("group_key") if existing else None, key):
            if k:
                touched.add(k)
    for k in touched:
        sync_group(db, k)
    return stats


def mark_store_stale(db, store: str) -> int:
    """After a failed/unsupported refresh, old data stays but is flagged stale (never shown as verified)."""
    res = db.external_products.update_many({"store": store, "freshness": "fresh"}, {"$set": {"freshness": "stale"}})
    return res.modified_count


def record_run(db, store, status, started_at, finished_at, items_found, errors, notes, robots_allowed) -> None:
    db.scrape_runs.insert_one({
        "store": store, "started_at": started_at, "finished_at": finished_at,
        "status": status, "items_found": items_found, "errors": errors})
    fields = {"status": status, "last_attempt_at": finished_at, "items_found": items_found,
              "robots_allowed": robots_allowed, "notes": notes, "last_error": errors[0] if errors else None}
    if status in ("success", "partial"):
        fields["last_success_at"] = finished_at
    db.scrape_sources.update_one({"store": store}, {"$set": fields}, upsert=True)