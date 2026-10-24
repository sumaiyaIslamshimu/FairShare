"""Price tracking. A watch records the price when it was added and (optionally) a target price.

Alerts are in-app notifications, sent when a price DROPS: below the last seen price, or (with a target) when it
crosses down to the target. The comparison always uses the price a shopper would actually pay.
"""
import logging

from pymongo.errors import DuplicateKeyError

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.services import compare_service, notification_service, product_service
from app.services.time_utils import iso, utcnow

log = logging.getLogger(__name__)
MAX_WATCHES = 50


# ---------- the current offer behind a watch ----------

def _external(db, pid):
    d = db.external_products.find_one({"_id": pid})
    if not d:
        return None
    item = compare_service.external_item(d, utcnow())
    return {"name": item["name"], "store_name": item["store_name"], "store_url": item.get("store_url"),
            "image_url": item.get("image_url"), "currency": item.get("currency"), "price": item["price_paisa"],
            "availability": item["availability"], "freshness": item["freshness"]}


def _fairshare(db, pid):
    d = db.seller_products.find_one({"_id": pid, **product_service.public_filter(db)})
    if not d:
        return None
    price, _ = product_service.effective_price(db, d)
    images = d.get("images") or []
    return {"name": d["title"], "store_name": "FairShare", "store_url": None, "image_url": images[0] if images else None,
            "currency": d.get("currency", "BDT"), "price": price, "availability": product_service.availability_of(d),
            "freshness": "fresh"}


def _offer(db, source: str, pid):
    return _external(db, pid) if source == "external" else _fairshare(db, pid)


# ---------- shopper actions ----------

def create(db, user: dict, data) -> dict:
    pid = to_object_id(data.product_id, "Product")
    offer = _offer(db, data.source, pid)
    if not offer:
        raise AppError(404, "NOT_FOUND", "That product is not available to track.")
    if data.target_price_paisa is not None and data.target_price_paisa >= offer["price"]:
        raise AppError(422, "TARGET_TOO_HIGH", "Choose a target below the current price, or leave it empty to be told about any drop.")
    if db.price_watches.count_documents({"user_id": user["_id"]}) >= MAX_WATCHES:
        raise AppError(409, "WATCH_LIMIT", f"You can track up to {MAX_WATCHES} products. Remove one first.")
    if db.price_watches.find_one({"user_id": user["_id"], "source": data.source, "product_id": pid}):
        raise AppError(409, "ALREADY_WATCHING", "You are already tracking this product.")
    now = utcnow()
    doc = {"user_id": user["_id"], "source": data.source, "product_id": pid, "target_price_paisa": data.target_price_paisa,
           "price_when_added_paisa": offer["price"], "last_price_paisa": offer["price"], "lowest_seen_paisa": offer["price"],
           "created_at": now, "updated_at": now}
    try:
        doc["_id"] = db.price_watches.insert_one(doc).inserted_id
    except DuplicateKeyError:
        raise AppError(409, "ALREADY_WATCHING", "You are already tracking this product.")
    return serialize(db, doc)


def _own(db, user: dict, watch_id: str) -> dict:
    d = db.price_watches.find_one({"_id": to_object_id(watch_id, "Watch")})
    if not d or d["user_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Tracked product not found.")
    return d


def update(db, user: dict, watch_id: str, data) -> dict:
    d = _own(db, user, watch_id)
    if data.target_price_paisa is not None:
        offer = _offer(db, d["source"], d["product_id"])
        if offer and data.target_price_paisa >= offer["price"]:
            raise AppError(422, "TARGET_TOO_HIGH", "Choose a target below the current price, or clear it.")
    db.price_watches.update_one({"_id": d["_id"]}, {"$set": {"target_price_paisa": data.target_price_paisa, "updated_at": utcnow()}})
    return serialize(db, db.price_watches.find_one({"_id": d["_id"]}))


def delete(db, user: dict, watch_id: str) -> None:
    d = _own(db, user, watch_id)
    db.price_watches.delete_one({"_id": d["_id"]})


def serialize(db, d: dict) -> dict:
    offer = _offer(db, d["source"], d["product_id"])
    current = offer["price"] if offer else None
    lowest = d.get("lowest_seen_paisa")
    if d["source"] == "external":
        seen = [o["price_paisa"] for o in db.price_observations.find({"external_product_id": d["product_id"]}, {"price_paisa": 1})]
        lowest = min(seen + ([lowest] if lowest else [])) if seen else lowest
    base = d["price_when_added_paisa"]
    target = d.get("target_price_paisa")
    if current is None:
        status = "unavailable"
    elif target is not None and current <= target:
        status = "target_reached"
    elif current < base:
        status = "dropped"
    elif current > base:
        status = "increased"
    else:
        status = "unchanged"
    return {
        "id": str(d["_id"]), "source": d["source"], "product_id": str(d["product_id"]),
        "name": (offer or {}).get("name", ""), "store_name": (offer or {}).get("store_name", ""),
        "store_url": (offer or {}).get("store_url"), "image_url": (offer or {}).get("image_url"),
        "currency": (offer or {}).get("currency"), "availability": (offer or {}).get("availability", "unknown"),
        "freshness": (offer or {}).get("freshness", "fresh"), "price_when_added_paisa": base, "current_price_paisa": current,
        "lowest_seen_paisa": lowest, "target_price_paisa": target,
        "change_paisa": None if current is None else current - base, "status": status, "created_at": iso(d.get("created_at")),
    }

def recheck_fairshare(db, product_ids, user_id=None) -> int:
    """Re-reads the current price (promotions included) of FairShare products and alerts on a drop.
    Used when a seller changes a promotion, and when a shopper opens their list, which also catches a promotion
    that started or ended on its own with nobody editing anything. Never raises."""
    sent = 0
    try:
        flt = {"source": "fairshare", "product_id": {"$in": list(product_ids)}}
        if user_id is not None:
            flt["user_id"] = user_id
        for pid in {w["product_id"] for w in db.price_watches.find(flt)}:
            doc = db.seller_products.find_one({"_id": pid, **product_service.public_filter(db)})
            if doc:
                price, _ = product_service.effective_price(db, doc)
                sent += check_price(db, "fairshare", pid, price)
    except Exception:  # noqa: BLE001
        log.exception("Price re-check failed")
    return sent

def list_mine(db, user: dict, page: int, page_size: int) -> dict:
    flt = {"user_id": user["_id"]}
    mine = [w["product_id"] for w in db.price_watches.find({**flt, "source": "fairshare"})]
    if mine:
        recheck_fairshare(db, mine, user["_id"])
    total = db.price_watches.count_documents(flt)
    # ... নিচের অংশ আগের মতোই
    cur = db.price_watches.find(flt).sort([("created_at", -1), ("_id", -1)]).skip((page - 1) * page_size).limit(page_size)
    return {"items": [serialize(db, d) for d in cur], "total": total, "page": page, "page_size": page_size}


def refs(db, user: dict) -> list[dict]:
    return [{"id": str(d["_id"]), "source": d["source"], "product_id": str(d["product_id"])}
            for d in db.price_watches.find({"user_id": user["_id"]})]


def history(db, user: dict, watch_id: str) -> dict:
    d = _own(db, user, watch_id)
    if d["source"] != "external":
        return {"available": False, "points": []}
    cur = db.price_observations.find({"external_product_id": d["product_id"]}).sort("observed_at", 1).limit(200)
    return {"available": True, "points": [{"price_paisa": o["price_paisa"], "availability": o.get("availability"),
                                           "observed_at": iso(o.get("observed_at"))} for o in cur]}


# ---------- alerts (called by the scraper and by the seller product update) ----------

def check_price(db, source: str, product_id, new_price_paisa: int) -> int:
    """Looks at every watch on this product. Never raises: a failed alert must not break the price update."""
    sent = 0
    try:
        for w in list(db.price_watches.find({"source": source, "product_id": product_id})):
            last = w.get("last_price_paisa", w["price_when_added_paisa"])
            target = w.get("target_price_paisa")
            dropped = new_price_paisa < last
            alert = dropped and (target is None or (new_price_paisa <= target and last > target))
            changes = {"last_price_paisa": new_price_paisa, "updated_at": utcnow()}
            if new_price_paisa < w.get("lowest_seen_paisa", new_price_paisa):
                changes["lowest_seen_paisa"] = new_price_paisa
            db.price_watches.update_one({"_id": w["_id"]}, {"$set": changes})
            if alert:
                offer = _offer(db, source, product_id) or {}
                notification_service.notify(
                    db, w["user_id"], "price", "A price you are tracking dropped",
                    f"{offer.get('name', 'A product')}: {last / 100:g} to {new_price_paisa / 100:g} (BDT)", "pricewatch")
                sent += 1
    except Exception:  # noqa: BLE001 - see docstring
        log.exception("Price alert check failed")
    return sent