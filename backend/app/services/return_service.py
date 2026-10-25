"""Returns: requested -> approved | rejected; approved -> completed. Completing restocks the item and marks it returned.

The refund is SIMULATED (like checkout): no money moves; the record only states the amount.
"""
from pymongo.errors import DuplicateKeyError

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.services import audit_service, notification_service
from app.services.time_utils import iso, utcnow

# action -> (status it can start from, status it ends in)
TRANSITIONS = {"approve": ("requested", "approved"), "reject": ("requested", "rejected"), "complete": ("approved", "completed")}


def serialize(db, d: dict) -> dict:
    item = db.order_items.find_one({"_id": d["order_item_id"]}) or {}
    return {
        "id": str(d["_id"]), "order_id": str(d["order_id"]), "order_item_id": str(d["order_item_id"]),
        "product_title": item.get("title_snapshot", ""), "quantity": d["quantity"], "refund_paisa": d["refund_paisa"],
        "currency": "BDT", "refund_mode": "simulated", "reason": d["reason"], "details": d.get("details", ""),
        "status": d["status"], "seller_note": d.get("seller_note"),
        "created_at": iso(d.get("created_at")), "updated_at": iso(d.get("updated_at")),
    }


def _staff(db, d: dict) -> dict:
    u = db.users.find_one({"_id": d["user_id"]}) or {}
    return {**serialize(db, d), "shopper_name": u.get("full_name", ""), "shopper_email": u.get("email", ""),
            "seller_id": str(d["seller_id"])}


def _page(items, total, page, page_size):
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def create(db, user: dict, data) -> dict:
    item = db.order_items.find_one({"_id": to_object_id(data.order_item_id, "Order item")})
    order = item and db.orders.find_one({"_id": item["order_id"]})
    if not item or not order or order["user_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Order item not found.")
    if item.get("item_status") != "delivered":
        raise AppError(409, "NOT_DELIVERED", "You can return an item only after it has been delivered.")
    if db.return_requests.find_one({"user_id": user["_id"], "order_item_id": item["_id"]}):
        raise AppError(409, "ALREADY_REQUESTED", "You already asked to return this item.")
    now = utcnow()
    doc = {"order_id": order["_id"], "order_item_id": item["_id"], "user_id": user["_id"], "seller_id": item["seller_id"],
           "product_id": item["seller_product_id"], "quantity": item["quantity"], "refund_paisa": item["line_total_paisa"],
           "reason": data.reason, "details": data.details, "status": "requested", "seller_note": None,
           "created_at": now, "updated_at": now}
    try:
        doc["_id"] = db.return_requests.insert_one(doc).inserted_id
    except DuplicateKeyError:
        raise AppError(409, "ALREADY_REQUESTED", "You already asked to return this item.")
    notification_service.notify(db, item["seller_id"], "return", "A shopper asked to return an item",
                                item.get("title_snapshot", ""), "returns")
    return serialize(db, doc)


def cancel(db, user: dict, return_id: str) -> dict:
    d = db.return_requests.find_one({"_id": to_object_id(return_id, "Return")})
    if not d or d["user_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Return request not found.")
    if d["status"] != "requested":
        raise AppError(409, "INVALID_TRANSITION", "Only a request that has not been decided can be cancelled.")
    db.return_requests.update_one({"_id": d["_id"]}, {"$set": {"status": "cancelled", "updated_at": utcnow()}})
    return serialize(db, db.return_requests.find_one({"_id": d["_id"]}))


def list_mine(db, user: dict, page: int, page_size: int) -> dict:
    flt = {"user_id": user["_id"]}
    total = db.return_requests.count_documents(flt)
    cur = db.return_requests.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    return _page([serialize(db, d) for d in cur], total, page, page_size)


def list_for_seller(db, seller: dict, status: str | None, page: int, page_size: int) -> dict:
    return _list(db, {"seller_id": seller["_id"]}, status, page, page_size)


def list_all(db, status: str | None, page: int, page_size: int) -> dict:
    return _list(db, {}, status, page, page_size)


def _list(db, flt: dict, status, page, page_size) -> dict:
    if status:
        flt = {**flt, "status": status}
    total = db.return_requests.count_documents(flt)
    cur = db.return_requests.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    return _page([_staff(db, d) for d in cur], total, page, page_size)


def _decide(db, d: dict, data) -> dict:
    start, end = TRANSITIONS[data.action]
    if d["status"] != start:
        raise AppError(409, "INVALID_TRANSITION", f"Cannot {data.action} a request that is {d['status']}.")
    changes = {"status": end, "updated_at": utcnow()}
    if data.note:
        changes["seller_note"] = data.note
    db.return_requests.update_one({"_id": d["_id"], "status": start}, {"$set": changes})
    if end == "completed":  # goods are back: restock once and mark the item
        db.seller_products.update_one({"_id": d["product_id"]}, {"$inc": {"stock_qty": d["quantity"]}})
        db.order_items.update_one({"_id": d["order_item_id"]}, {"$set": {"item_status": "returned"}})
        notification_service.notify(db, d["user_id"], "return", f"Your return request was {end}",
                                    data.note, "returns")
    return db.return_requests.find_one({"_id": d["_id"]})


def decide_as_seller(db, seller: dict, return_id: str, data) -> dict:
    d = db.return_requests.find_one({"_id": to_object_id(return_id, "Return")})
    if not d or d["seller_id"] != seller["_id"]:
        raise AppError(404, "NOT_FOUND", "Return request not found.")
    return _staff(db, _decide(db, d, data))


def decide_as_admin(db, admin: dict, return_id: str, data) -> dict:
    d = db.return_requests.find_one({"_id": to_object_id(return_id, "Return")})
    if not d:
        raise AppError(404, "NOT_FOUND", "Return request not found.")
    out = _decide(db, d, data)
    audit_service.log(db, admin, "return.decide", str(d["_id"]), {"action": data.action})
    return _staff(db, out)