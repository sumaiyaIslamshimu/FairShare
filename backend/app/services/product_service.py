"""FairShare seller products: seller CRUD, public browse, and effective_price (reads M3's promotions)."""
import re

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.scrapers.matcher import exact_group_key
from app.scrapers.normalizer import parse_quantity_unit
from app.services.category_service import validate_category_pair
from app.services.match_service import sync_group
from app.services.time_utils import aware, iso, utcnow


def _rx(text: str) -> dict:
    return {"$regex": re.escape(text.strip()), "$options": "i"}


def availability_of(doc: dict) -> str:
    return "in_stock" if doc.get("stock_qty", 0) > 0 else "out_of_stock"


def effective_price(db, doc: dict, now=None):
    """(price_paisa to pay, discount_percent or None). The server decides; clients never send prices.
    Promotion contract (docs/DATABASE.md): seller_id, product_ids[], discount_percent 1-90, starts_at, ends_at, is_active."""
    now = now or utcnow()
    price = doc["price_paisa"]
    best = 0.0
    promos = db.promotions.find({
        "seller_id": {"$in": [doc["seller_id"], str(doc["seller_id"])]},
        "is_active": True,
        "product_ids": {"$in": [doc["_id"], str(doc["_id"])]},
    })
    for promo in promos:
        start, end = aware(promo.get("starts_at")), aware(promo.get("ends_at"))
        if (start and start > now) or (end and end < now):
            continue
        best = max(best, float(promo.get("discount_percent") or 0))
    if best <= 0:
        return price, None
    best = min(best, 90.0)
    return max(1, round(price * (100 - best) / 100)), best


def business_names(db, seller_ids) -> dict:
    ids = list(set(seller_ids))
    return {p["user_id"]: p.get("business_name") for p in db.seller_profiles.find({"user_id": {"$in": ids}})}


def public_filter(db) -> dict:
    """Products shoppers may see: active, not hidden by moderation, and the seller is approved."""
    approved = [p["user_id"] for p in db.seller_profiles.find({"status": "approved"})]
    return {"status": "active", "moderation_status": "visible", "seller_id": {"$in": approved}}


def serialize(db, doc: dict, names=None, owner: bool = False, now=None) -> dict:
    price, pct = effective_price(db, doc, now)
    if names is None:
        names = business_names(db, [doc["seller_id"]])
    out = {
        "id": str(doc["_id"]), "seller_id": str(doc["seller_id"]), "seller_name": names.get(doc["seller_id"]),
        "title": doc["title"], "description": doc.get("description", ""), "brand": doc.get("brand"),
        "category_slug": doc["category_slug"], "subcategory_slug": doc["subcategory_slug"],
        "price_paisa": doc["price_paisa"], "effective_price_paisa": price, "discount_percent": pct,
        "currency": doc.get("currency", "BDT"), "availability": availability_of(doc),
        "images": doc.get("images", []), "quantity": doc.get("quantity"), "unit": doc.get("unit"),
        "attributes": doc.get("attributes", {}), "source": "fairshare",
    }
    if owner:
        out.update({"stock_qty": doc["stock_qty"], "status": doc["status"],
                    "moderation_status": doc.get("moderation_status", "visible"),
                    "created_at": iso(doc.get("created_at")), "updated_at": iso(doc.get("updated_at"))})
    return out


def _page(items, total, page, page_size) -> dict:
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def _fields(db, data) -> dict:
    validate_category_pair(db, data.category_slug, data.subcategory_slug)
    quantity, unit = data.quantity, data.unit
    if quantity is None:
        parsed = parse_quantity_unit(data.title)   # e.g. "Rice 5 kg" -> (5000.0, "g")
        if parsed:
            quantity, unit = parsed
    return {
        "title": data.title, "description": data.description, "brand": data.brand,
        "category_slug": data.category_slug, "subcategory_slug": data.subcategory_slug,
        "price_paisa": data.price_paisa, "currency": "BDT", "stock_qty": data.stock_qty,
        "status": data.status, "images": data.images, "quantity": quantity, "unit": unit,
        "attributes": data.attributes,
        "group_key": exact_group_key({"name": data.title, "brand": data.brand, "quantity": quantity, "unit": unit}),
    }


# ---------- seller side (owner only) ----------

def create_product(db, seller: dict, data) -> dict:
    now = utcnow()
    doc = {**_fields(db, data), "seller_id": seller["_id"], "moderation_status": "visible",
           "source": "fairshare", "created_at": now, "updated_at": now}
    doc["_id"] = db.seller_products.insert_one(doc).inserted_id
    sync_group(db, doc["group_key"])
    return serialize(db, doc, owner=True)


def get_owned(db, seller: dict, product_id: str) -> dict:
    doc = db.seller_products.find_one({"_id": to_object_id(product_id, "Product")})
    if not doc or doc.get("status") == "removed":
        raise AppError(404, "NOT_FOUND", "Product not found.")
    if doc["seller_id"] != seller["_id"]:
        raise AppError(403, "FORBIDDEN", "You can only manage your own products.")
    return doc


def list_own(db, seller: dict, page: int, page_size: int) -> dict:
    flt = {"seller_id": seller["_id"], "status": {"$ne": "removed"}}
    total = db.seller_products.count_documents(flt)
    cur = db.seller_products.find(flt).sort([("created_at", -1), ("_id", 1)]).skip((page - 1) * page_size).limit(page_size)
    names = business_names(db, [seller["_id"]])
    return _page([serialize(db, d, names, owner=True) for d in cur], total, page, page_size)


def update_product(db, seller: dict, product_id: str, data) -> dict:
    old = get_owned(db, seller, product_id)
    before, _ = effective_price(db, old)
    fields = {**_fields(db, data), "updated_at": utcnow()}
    db.seller_products.update_one({"_id": old["_id"]}, {"$set": fields})
    for key in {old.get("group_key"), fields["group_key"]}:
        sync_group(db, key)
    after, _ = effective_price(db, db.seller_products.find_one({"_id": old["_id"]}))
    if after != before:
        from app.services import watch_service  # imported here: watch_service itself imports this module
        watch_service.check_price(db, "fairshare", old["_id"], after)
    return serialize(db, db.seller_products.find_one({"_id": old["_id"]}), owner=True)


def remove_product(db, seller: dict, product_id: str) -> None:
    """Soft delete (status 'removed'), so future order history can still refer to the product."""
    old = get_owned(db, seller, product_id)
    db.seller_products.update_one({"_id": old["_id"]}, {"$set": {"status": "removed", "updated_at": utcnow()}})
    sync_group(db, old.get("group_key"))


def set_inventory(db, seller: dict, product_id: str, stock_qty: int) -> dict:
    old = get_owned(db, seller, product_id)
    db.seller_products.update_one({"_id": old["_id"]}, {"$set": {"stock_qty": stock_qty, "updated_at": utcnow()}})
    return serialize(db, db.seller_products.find_one({"_id": old["_id"]}), owner=True)


# ---------- public side ----------

def list_public(db, q, category, subcategory, sort, page, page_size) -> dict:
    flt = public_filter(db)
    if q and q.strip():
        flt["$or"] = [{"title": _rx(q)}, {"brand": _rx(q)}]
    if category:
        flt["category_slug"] = category
    if subcategory:
        flt["subcategory_slug"] = subcategory
    order = {"price_asc": [("price_paisa", 1), ("_id", 1)], "price_desc": [("price_paisa", -1), ("_id", 1)],
             "newest": [("created_at", -1), ("_id", 1)]}[sort]
    total = db.seller_products.count_documents(flt)
    docs = list(db.seller_products.find(flt).sort(order).skip((page - 1) * page_size).limit(page_size))
    names = business_names(db, [d["seller_id"] for d in docs])
    return _page([serialize(db, d, names) for d in docs], total, page, page_size)


def get_public(db, product_id: str) -> dict:
    doc = db.seller_products.find_one({"_id": to_object_id(product_id, "Product")})
    if not doc:
        raise AppError(404, "NOT_FOUND", "Product not found.")
    visible = db.seller_products.find_one({**public_filter(db), "_id": doc["_id"]})
    if not visible:
        raise AppError(404, "NOT_FOUND", "Product not found.")
    return serialize(db, visible)