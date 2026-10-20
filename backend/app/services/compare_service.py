"""Comparison search over external products + FairShare listings. Reads only from the database (never scrapes)."""
import os
import re
from datetime import timedelta

from app.core.errors import AppError
from app.scrapers import all_stores, get_scraper
from app.scrapers.matcher import match_products
from app.services import product_service
from app.services.time_utils import aware, iso, utcnow

STORE_NAMES = {"daraz": "Daraz", "pickaboo": "Pickaboo", "chaldal": "Chaldal", "shwapno": "Shwapno",
               "agora": "Agora", "rokomari": "Rokomari", "fairshare": "FairShare"}


def stale_after_hours() -> int:
    """Prices older than this are labelled stale. Optional env var STALE_AFTER_HOURS (default 48)."""
    try:
        return max(1, int(os.getenv("STALE_AFTER_HOURS", "48")))
    except ValueError:
        return 48


def compute_freshness(doc: dict, now) -> str:
    stored = doc.get("freshness", "fresh")
    if stored == "unavailable":
        return "unavailable"
    last = aware(doc.get("last_successful_at"))
    if stored == "stale" or last is None or now - last > timedelta(hours=stale_after_hours()):
        return "stale"
    return "fresh"


def _rx(text: str) -> dict:
    return {"$regex": re.escape(text.strip()), "$options": "i"}


def external_item(doc: dict, now) -> dict:
    return {
        "id": str(doc["_id"]), "source": "external", "store": doc["store"],
        "store_name": STORE_NAMES.get(doc["store"], doc["store"]), "seller_name": None,
        "name": doc["name"], "brand": doc.get("brand"), "price_paisa": doc["price_paisa"],
        "original_price_paisa": doc.get("original_price_paisa"), "discount_percent": doc.get("discount_percent"),
        "currency": doc.get("currency"), "image_url": doc.get("image_url"),
        "availability": doc.get("availability", "unknown"), "quantity": doc.get("quantity"), "unit": doc.get("unit"),
        "category_slug": doc.get("category_slug"), "subcategory_slug": doc.get("subcategory_slug"),
        "freshness": compute_freshness(doc, now), "last_updated": iso(doc.get("last_successful_at")),
        "store_url": doc.get("product_url"), "group_key": doc.get("group_key"), "group_size": 1,
    }


def seller_item(db, doc: dict, now, names: dict) -> dict:
    price, pct = product_service.effective_price(db, doc, now)
    images = doc.get("images") or []
    return {
        "id": str(doc["_id"]), "source": "fairshare", "store": "fairshare", "store_name": "FairShare",
        "seller_name": names.get(doc["seller_id"]), "name": doc["title"], "brand": doc.get("brand"),
        "price_paisa": price, "original_price_paisa": doc["price_paisa"] if pct else None, "discount_percent": pct,
        "currency": doc.get("currency", "BDT"), "image_url": images[0] if images else None,
        "availability": product_service.availability_of(doc), "quantity": doc.get("quantity"), "unit": doc.get("unit"),
        "category_slug": doc["category_slug"], "subcategory_slug": doc["subcategory_slug"],
        "freshness": "fresh", "last_updated": iso(doc.get("updated_at")),
        "store_url": None, "group_key": doc.get("group_key"), "group_size": 1,
    }


def _attach_group_sizes(db, items: list) -> None:
    keys = list({i["group_key"] for i in items if i["group_key"]})
    if not keys:
        return
    sizes = {m["group_key"]: len(m.get("external_product_ids", [])) + len(m.get("seller_product_ids", []))
             for m in db.product_matches.find({"group_key": {"$in": keys}})}
    for i in items:
        i["group_size"] = sizes.get(i["group_key"], 1)


def search(db, q, category, subcategory, store, sort, page, page_size, now=None) -> dict:
    now = now or utcnow()
    if store and store not in STORE_NAMES:
        raise AppError(422, "INVALID_STORE", "Unknown store.")
    take = page * page_size
    order = 1 if sort == "price_asc" else -1
    items, total = [], 0
    if store != "fairshare":
        flt = {}
        if store:
            flt["store"] = store
        if q and q.strip():
            flt["$or"] = [{"name": _rx(q)}, {"brand": _rx(q)}]
        if category:
            flt["category_slug"] = category
        if subcategory:
            flt["subcategory_slug"] = subcategory
        total += db.external_products.count_documents(flt)
        for d in db.external_products.find(flt).sort([("price_paisa", order), ("_id", 1)]).limit(take):
            items.append(external_item(d, now))
    if not store or store == "fairshare":
        flt = product_service.public_filter(db)
        if q and q.strip():
            flt["$or"] = [{"title": _rx(q)}, {"brand": _rx(q)}]
        if category:
            flt["category_slug"] = category
        if subcategory:
            flt["subcategory_slug"] = subcategory
        total += db.seller_products.count_documents(flt)
        docs = list(db.seller_products.find(flt).sort([("price_paisa", order), ("_id", 1)]).limit(take))
        names = product_service.business_names(db, [d["seller_id"] for d in docs])
        items += [seller_item(db, d, now, names) for d in docs]
    items.sort(key=lambda i: (i["price_paisa"], i["id"]), reverse=(sort == "price_desc"))
    window = items[(page - 1) * page_size: page * page_size]
    _attach_group_sizes(db, window)
    return {"items": window, "total": total, "page": page, "page_size": page_size}


def get_group(db, group_key: str, now=None) -> dict:
    now = now or utcnow()
    match = db.product_matches.find_one({"group_key": group_key})
    if not match:
        raise AppError(404, "NOT_FOUND", "Comparison group not found.")
    exact = [external_item(d, now) for d in db.external_products.find({"_id": {"$in": match.get("external_product_ids", [])}})]
    sel_docs = list(db.seller_products.find({**product_service.public_filter(db),
                                             "_id": {"$in": match.get("seller_product_ids", [])}}))
    names = product_service.business_names(db, [d["seller_id"] for d in sel_docs])
    exact += [seller_item(db, d, now, names) for d in sel_docs]
    exact.sort(key=lambda i: (i["price_paisa"], i["id"]))
    for i in exact:
        i["group_size"] = len(exact)

    # Only FRESH, not-out-of-stock offers can be called "cheapest": a stale price is never presented as verified.
    candidates = [i for i in exact if i["availability"] != "out_of_stock" and i["freshness"] == "fresh"]
    cheapest_id = min(candidates, key=lambda i: i["price_paisa"])["id"] if candidates else None

    possible = []
    anchor = exact[0] if exact else None
    brand = ((anchor or {}).get("brand") or "").strip()
    if anchor and brand:
        brx = {"$regex": f"^{re.escape(brand)}$", "$options": "i"}
        taken = {i["id"] for i in exact}
        pool = [external_item(d, now) for d in db.external_products.find({"brand": brx}).limit(60)]
        sdocs = list(db.seller_products.find({**product_service.public_filter(db), "brand": brx}).limit(60))
        snames = product_service.business_names(db, [d["seller_id"] for d in sdocs])
        pool += [seller_item(db, d, now, snames) for d in sdocs]
        for cand in pool:
            if cand["id"] in taken:
                continue
            r = match_products(anchor, cand)
            if r.match_type == "possible":
                possible.append({"item": cand, "score": r.score, "reasons": r.reasons, "differences": r.differences})
        possible.sort(key=lambda p: -p["score"])
    return {"group_key": group_key, "exact": exact, "possible": possible[:20], "cheapest_id": cheapest_id}


def store_sources(db) -> list:
    docs = {d["store"]: d for d in db.scrape_sources.find({})}
    out = []
    for store in all_stores():
        d = docs.get(store, {})
        out.append({
            "store": store, "store_name": STORE_NAMES[store],
            "configured": bool(getattr(get_scraper(store), "configured", False)),
            "status": d.get("status", "never_run"),
            "last_attempt_at": iso(d.get("last_attempt_at")), "last_success_at": iso(d.get("last_success_at")),
            "items_found": d.get("items_found", 0), "robots_allowed": d.get("robots_allowed"),
            "notes": d.get("notes", []), "last_error": d.get("last_error"),
        })
    return out