"""Keeps `product_matches` (exact-match groups) in sync with external_products and seller_products."""
from app.services.time_utils import utcnow


def sync_group(db, group_key) -> None:
    """A group exists only while at least 2 products share the key; otherwise its record is removed."""
    if not group_key:
        return
    ext = list(db.external_products.find({"group_key": group_key}))
    sel = list(db.seller_products.find({"group_key": group_key, "status": "active", "moderation_status": "visible"}))
    if len(ext) + len(sel) < 2:
        db.product_matches.delete_one({"group_key": group_key})
        return
    sample = (ext or sel)[0]
    reasons = ["same brand", "same model/variant words"]
    if sample.get("quantity") and sample.get("unit"):
        reasons.append("same size")
    db.product_matches.update_one(
        {"group_key": group_key},
        {"$set": {
            "external_product_ids": [d["_id"] for d in ext],
            "seller_product_ids": [d["_id"] for d in sel],
            "match_type": "exact",
            "reasons": reasons,
            "differences": [],
            "updated_at": utcnow(),
        }},
        upsert=True,
    )