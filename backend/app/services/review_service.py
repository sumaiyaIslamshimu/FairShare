"""Reviews: only a shopper who received an item can rate it, once per purchased item."""
from pymongo.errors import DuplicateKeyError

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.services import audit_service, notification_service
from app.services.time_utils import iso, utcnow


def _first_name(user: dict | None) -> str:
    name = ((user or {}).get("full_name") or "").strip()
    return name.split(" ")[0] if name else "Shopper"


def _title(db, product_id) -> str:
    p = db.seller_products.find_one({"_id": product_id}) or {}
    return p.get("title", "")


def _public(db, d: dict) -> dict:
    return {"id": str(d["_id"]), "product_id": str(d["product_id"]), "rating": d["rating"], "comment": d.get("comment", ""),
            "reviewer_name": _first_name(db.users.find_one({"_id": d["user_id"]})), "created_at": iso(d.get("created_at"))}


def _own(db, d: dict) -> dict:
    return {**_public(db, d), "order_item_id": str(d["order_item_id"]), "product_title": _title(db, d["product_id"]),
            "status": d["status"]}


def _page(items, total, page, page_size, **extra):
    return {"items": items, "total": total, "page": page, "page_size": page_size, **extra}


def create(db, user: dict, data) -> dict:
    item = db.order_items.find_one({"_id": to_object_id(data.order_item_id, "Order item")})
    order = item and db.orders.find_one({"_id": item["order_id"]})
    if not item or not order or order["user_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Order item not found.")
    if item.get("item_status") != "delivered":
        raise AppError(409, "NOT_DELIVERED", "You can review an item only after it has been delivered.")
    if db.reviews.find_one({"user_id": user["_id"], "order_item_id": item["_id"]}):
        raise AppError(409, "ALREADY_REVIEWED", "You already reviewed this item. You can edit your review.")
    now = utcnow()
    doc = {"product_id": item["seller_product_id"], "order_item_id": item["_id"], "user_id": user["_id"],
           "seller_id": item["seller_id"], "rating": data.rating, "comment": data.comment, "status": "visible",
           "created_at": now, "updated_at": now}
    try:
        doc["_id"] = db.reviews.insert_one(doc).inserted_id
    except DuplicateKeyError:
        raise AppError(409, "ALREADY_REVIEWED", "You already reviewed this item. You can edit your review.")
    notification_service.notify(db, item["seller_id"], "review", f"New {data.rating}-star review",
                                _title(db, item["seller_product_id"]), "reviews")
    return _own(db, doc)


def update(db, user: dict, review_id: str, data) -> dict:
    doc = db.reviews.find_one({"_id": to_object_id(review_id, "Review")})
    if not doc or doc["user_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Review not found.")
    db.reviews.update_one({"_id": doc["_id"]}, {"$set": {"rating": data.rating, "comment": data.comment, "updated_at": utcnow()}})
    return _own(db, db.reviews.find_one({"_id": doc["_id"]}))


def delete(db, user: dict, review_id: str) -> None:
    doc = db.reviews.find_one({"_id": to_object_id(review_id, "Review")})
    if not doc or doc["user_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Review not found.")
    db.reviews.delete_one({"_id": doc["_id"]})


def list_mine(db, user: dict, page: int, page_size: int) -> dict:
    flt = {"user_id": user["_id"]}
    total = db.reviews.count_documents(flt)
    cur = db.reviews.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    return _page([_own(db, d) for d in cur], total, page, page_size)


def _average(db, flt: dict):
    ratings = [d["rating"] for d in db.reviews.find(flt, {"rating": 1})]
    return (round(sum(ratings) / len(ratings), 2), len(ratings)) if ratings else (None, 0)


def list_for_product(db, product_id: str, page: int, page_size: int) -> dict:
    oid = to_object_id(product_id, "Product")
    flt = {"product_id": oid, "status": "visible"}  # hidden reviews never count and never show
    total = db.reviews.count_documents(flt)
    cur = db.reviews.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    avg, n = _average(db, flt)
    return _page([_public(db, d) for d in cur], total, page, page_size, average=avg, count=n)


def list_for_seller(db, seller: dict, page: int, page_size: int) -> dict:
    flt = {"seller_id": seller["_id"], "status": "visible"}
    total = db.reviews.count_documents(flt)
    cur = db.reviews.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    avg, _ = _average(db, flt)
    items = [{**_public(db, d), "product_title": _title(db, d["product_id"]), "status": d["status"]} for d in cur]
    return _page(items, total, page, page_size, average=avg)


# ---------- admin ----------

def list_all(db, status: str | None, page: int, page_size: int) -> dict:
    flt = {"status": status} if status else {}
    total = db.reviews.count_documents(flt)
    cur = db.reviews.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    items = []
    for d in cur:
        u = db.users.find_one({"_id": d["user_id"]}) or {}
        items.append({**_own(db, d), "seller_id": str(d["seller_id"]), "reviewer_email": u.get("email", "")})
    return _page(items, total, page, page_size)


def moderate(db, admin: dict, review_id: str, status: str) -> dict:
    doc = db.reviews.find_one({"_id": to_object_id(review_id, "Review")})
    if not doc:
        raise AppError(404, "NOT_FOUND", "Review not found.")
    db.reviews.update_one({"_id": doc["_id"]}, {"$set": {"status": status, "updated_at": utcnow()}})
    audit_service.log(db, admin, "review.moderate", str(doc["_id"]), {"status": status})
    if status == "hidden":
        notification_service.notify(db, doc["user_id"], "review", "One of your reviews was hidden",
                                    "An administrator hid it because it broke the rules.", "reviews")
    d = db.reviews.find_one({"_id": doc["_id"]})
    u = db.users.find_one({"_id": d["user_id"]}) or {}
    return {**_own(db, d), "seller_id": str(d["seller_id"]), "reviewer_email": u.get("email", "")}