"""Business logic for Seller Portal (Profile, Promotions, Insights)."""
from typing import Any, Dict

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.services.time_utils import iso, utcnow


def get_profile(db, seller: dict) -> dict:
    profile = db.seller_profiles.find_one({"user_id": seller["_id"]})
    if not profile:
        raise AppError(404, "NOT_FOUND", "Seller profile not found.")
    return {
        "id": str(profile["_id"]),
        "user_id": str(profile["user_id"]),
        "business_name": profile.get("business_name", ""),
        "description": profile.get("description", ""),
        "contact_phone": profile.get("contact_phone", ""),
        "address": profile.get("address", ""),
        "status": profile.get("status", "pending"),
        "created_at": iso(profile.get("created_at")),
        "updated_at": iso(profile.get("updated_at"))
    }


def update_profile(db, seller: dict, data) -> dict:
    profile = db.seller_profiles.find_one({"user_id": seller["_id"]})
    if not profile:
        raise AppError(404, "NOT_FOUND", "Seller profile not found.")

    updates = {"updated_at": utcnow()}
    dump = data.model_dump(exclude_unset=True)
    for key, value in dump.items():
        updates[key] = value

    db.seller_profiles.update_one({"_id": profile["_id"]}, {"$set": updates})
    return get_profile(db, seller)


def serialize_promo(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "seller_id": str(doc["seller_id"]),
        "name": doc.get("name", "Store Promotion"),
        "product_ids": [str(pid) for pid in doc["product_ids"]],
        "discount_percent": doc["discount_percent"],
        "starts_at": iso(doc["starts_at"]),
        "ends_at": iso(doc["ends_at"]),
        "is_active": doc["is_active"],
        "created_at": iso(doc.get("created_at")),
        "updated_at": iso(doc.get("updated_at"))
    }


def create_promotion(db, seller: dict, data) -> dict:
    # 1. Verify the seller owns all provided product IDs
    product_obj_ids = []
    for pid in data.product_ids:
        product_obj_ids.append(to_object_id(pid, "Product"))

    owned_count = db.seller_products.count_documents({
        "_id": {"$in": product_obj_ids},
        "seller_id": seller["_id"],
        "status": {"$ne": "removed"}
    })

    if owned_count != len(product_obj_ids):
        raise AppError(403, "FORBIDDEN", "You do not own all provided products, or they are invalid.")

    # 2. Create promotion
    now = utcnow()
    doc = {
        "seller_id": seller["_id"],
        "name": data.name,
        "product_ids": product_obj_ids,
        "discount_percent": data.discount_percent,
        "starts_at": data.starts_at,
        "ends_at": data.ends_at,
        "is_active": data.is_active,
        "created_at": now,
        "updated_at": now
    }
    doc["_id"] = db.promotions.insert_one(doc).inserted_id
    return serialize_promo(doc)


def list_promotions(db, seller: dict) -> list[dict]:
    docs = db.promotions.find({"seller_id": seller["_id"]}).sort("created_at", -1)
    return [serialize_promo(d) for d in docs]


def update_promotion(db, seller: dict, promo_id: str, data) -> dict:
    promo = db.promotions.find_one({"_id": to_object_id(promo_id, "Promotion")})
    if not promo or promo["seller_id"] != seller["_id"]:
        raise AppError(404, "NOT_FOUND", "Promotion not found.")

    updates = {"updated_at": utcnow()}
    dump = data.model_dump(exclude_unset=True)

    if "product_ids" in dump:
        obj_ids = [to_object_id(pid, "Product") for pid in dump["product_ids"]]
        owned_count = db.seller_products.count_documents({
            "_id": {"$in": obj_ids}, "seller_id": seller["_id"], "status": {"$ne": "removed"}
        })
        if owned_count != len(obj_ids):
            raise AppError(403, "FORBIDDEN", "You do not own all provided products.")
        updates["product_ids"] = obj_ids

    for k in ["name", "discount_percent", "starts_at", "ends_at", "is_active"]:
        if k in dump:
            updates[k] = dump[k]

    db.promotions.update_one({"_id": promo["_id"]}, {"$set": updates})
    return serialize_promo(db.promotions.find_one({"_id": promo["_id"]}))


def delete_promotion(db, seller: dict, promo_id: str) -> None:
    promo = db.promotions.find_one({"_id": to_object_id(promo_id, "Promotion")})
    if not promo or promo["seller_id"] != seller["_id"]:
        raise AppError(404, "NOT_FOUND", "Promotion not found.")
    db.promotions.delete_one({"_id": promo["_id"]})


def get_insights(db, seller: dict) -> dict:
    now = utcnow()

    total_products = db.seller_products.count_documents({"seller_id": seller["_id"], "status": {"$ne": "removed"}})
    active_products = db.seller_products.count_documents({"seller_id": seller["_id"], "status": "active"})
    out_of_stock = db.seller_products.count_documents(
        {"seller_id": seller["_id"], "stock_qty": 0, "status": {"$ne": "removed"}})

    active_promos = db.promotions.count_documents({
        "seller_id": seller["_id"],
        "is_active": True,
        "starts_at": {"$lte": now},
        "ends_at": {"$gt": now}
    })

    # Manual aggregation for safe mongomock compatibility
    order_items = db.order_items.find({"seller_id": seller["_id"]})
    orders_by_status: Dict[str, int] = {}
    total_revenue = 0
    total_units = 0
    unique_orders = set()

    for item in order_items:
        unique_orders.add(str(item["order_id"]))
        st = item.get("item_status", "pending")
        orders_by_status[st] = orders_by_status.get(st, 0) + 1

        if st != "cancelled":
            total_revenue += item.get("line_total_paisa", 0)
            total_units += item.get("quantity", 0)

    # Low stock logic (1 to 5 items left)
    low_stock_cursor = db.seller_products.find({
        "seller_id": seller["_id"],
        "stock_qty": {"$gt": 0, "$lte": 5},
        "status": {"$ne": "removed"}
    }).limit(10)

    low_stock = [
        {"id": str(p["_id"]), "title": p["title"], "stock_qty": p["stock_qty"], "price_paisa": p["price_paisa"]}
        for p in low_stock_cursor
    ]

    return {
        "seller_id": str(seller["_id"]),
        "total_products": total_products,
        "active_products": active_products,
        "out_of_stock_products": out_of_stock,
        "active_promotions": active_promos,
        "total_orders": len(unique_orders),
        "orders_by_status": orders_by_status,
        "total_revenue_paisa": total_revenue,
        "total_units_sold": total_units,
        "low_stock_items": low_stock
    }