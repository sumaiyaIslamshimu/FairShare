"""Comparison search over external products + FairShare listings. Reads only from the database (never scrapes)."""
import os
import re
import random
import urllib.parse
from datetime import timedelta

from app.core.errors import AppError
from app.scrapers import all_stores, get_scraper
from app.scrapers.matcher import match_products
from app.services import product_service
from app.services.time_utils import aware, iso, utcnow

STORE_NAMES = {"daraz": "Daraz", "pickaboo": "Pickaboo", "chaldal": "Chaldal", "shwapno": "Shwapno",
               "agora": "Agora", "rokomari": "Rokomari", "fairshare": "FairShare"}


def stale_after_hours() -> int:
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
    store = doc.get("store")
    name = doc.get("name", "Unknown")

    url = doc.get("product_url")
    if not url:
        val = doc.get("store_product_id", "")
        if isinstance(val, str) and (val.startswith("http") or val.startswith("/")):
            url = val

    url = str(url).strip() if url else ""
    item_freshness = compute_freshness(doc, now)

    # --- AGGRESSIVE CHALDAL ROUTING FIX ---
    if store == "chaldal" and url:
        url = url.replace("/p/", "/", 1)

    # --- SHWAPNO SMART HYBRID ROUTING ---
    # If the item is stale, Shwapno likely deleted it (causing a redirect to home).
    # We route stale Shwapno items to search, but keep fresh ones direct!
    if store == "shwapno" and item_freshness == "stale":
        encoded_name = urllib.parse.quote(name.strip())
        url = f"https://www.shwapno.com/search?q={encoded_name}"
    else:
        # STRICT DIRECT ROUTING for everything else (and fresh Shwapno items)
        if url.startswith("/"):
            domains = {
                "chaldal": "https://chaldal.com",
                "shwapno": "https://www.shwapno.com",
                "agora": "https://agorasuperstores.com",
                "rokomari": "https://www.rokomari.com",
                "daraz": "https://www.daraz.com.bd",
                "pickaboo": "https://www.pickaboo.com"
            }
            url = domains.get(store, "") + url
        elif url and not url.startswith("http"):
            url = "https://" + url

    return {
        "id": str(doc["_id"]), "source": "external", "store": store,
        "store_name": STORE_NAMES.get(store, store), "seller_name": None,
        "name": name, "brand": doc.get("brand"), "price_paisa": doc.get("price_paisa", 0),
        "original_price_paisa": doc.get("original_price_paisa"), "discount_percent": doc.get("discount_percent"),
        "currency": doc.get("currency", "৳"), "image_url": doc.get("image_url"),
        "availability": doc.get("availability", "unknown"), "quantity": doc.get("quantity"), "unit": doc.get("unit"),
        "category_slug": doc.get("category_slug") or doc.get("category"), "subcategory_slug": doc.get("subcategory_slug"),
        "freshness": item_freshness, "last_updated": iso(doc.get("last_successful_at")),
        "store_url": url if url else None,
        "group_key": doc.get("group_key"), "group_size": 1,
    }


def seller_item(db, doc: dict, now, names: dict) -> dict:
    try:
        price, pct = product_service.effective_price(db, doc, now)
    except Exception:
        price, pct = doc.get("price_paisa", 0), 0

    try:
        avail = product_service.availability_of(doc)
    except Exception:
        avail = "in_stock"

    images = doc.get("images") or []
    item_name = doc.get("title") or doc.get("name") or "Unknown Product"

    return {
        "id": str(doc["_id"]), "source": "fairshare", "store": "fairshare", "store_name": "FairShare",
        "seller_name": names.get(doc.get("seller_id"), "FairShare Seller"), "name": item_name, "brand": doc.get("brand"),
        "price_paisa": price, "original_price_paisa": doc.get("price_paisa") if pct else None, "discount_percent": pct,
        "currency": doc.get("currency", "৳"), "image_url": images[0] if images else doc.get("image_url"),
        "availability": avail, "quantity": doc.get("quantity", 1), "unit": doc.get("unit", "pcs"),
        "category_slug": doc.get("category_slug") or doc.get("category", "general"), "subcategory_slug": doc.get("subcategory_slug"),
        "freshness": "fresh", "last_updated": iso(doc.get("updated_at") or now),
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

    items, total = [], 0

    def _build_filter(base_store_filter, is_external=False):
        and_clauses = []
        if base_store_filter:
            and_clauses.append(base_store_filter)

        if q and q.strip():
            and_clauses.append({"$or": [{"name": _rx(q)}, {"title": _rx(q)}, {"brand": _rx(q)}]})

        if category:
            cat_term = category.strip().lower()

            if cat_term in ["groceries", "grocery"]:
                regex_str = "grocer"
            elif cat_term in ["electronics", "electronic"]:
                regex_str = "electronic"
            elif cat_term == "lifestyle":
                regex_str = "lifestyle|fashion"
            else:
                regex_str = re.escape(cat_term)

            cat_rx = {"$regex": regex_str, "$options": "i"}
            cat_or = [{"category_slug": cat_rx}, {"category": cat_rx}]

            if is_external:
                if "grocer" in regex_str:
                    cat_or.append({"store": {"$in": ["chaldal", "agora"]}})
                elif "electronic" in regex_str:
                    cat_or.append({"store": {"$in": ["pickaboo", "daraz"]}})
                elif "lifestyle" in regex_str or "fashion" in regex_str:
                    cat_or.append({"store": {"$in": ["shwapno", "rokomari"]}})

            and_clauses.append({"$or": cat_or})

        if subcategory:
            sub_rx = {"$regex": f"^{re.escape(subcategory.strip())}$", "$options": "i"}
            and_clauses.append({"$or": [{"subcategory_slug": sub_rx}, {"subcategory": sub_rx}]})

        return {"$and": and_clauses} if and_clauses else {}


    if store != "fairshare":
        flt = _build_filter({"store": store} if store else {}, is_external=True)
        total += db.external_products.count_documents(flt)
        for d in db.external_products.find(flt):
            try:
                items.append(external_item(d, now))
            except Exception:
                continue

    if not store or store == "fairshare":
        flt = _build_filter({}, is_external=False)
        total += db.products.count_documents(flt)
        docs = list(db.products.find(flt))
        names = product_service.business_names(db, [d.get("seller_id") for d in docs if d.get("seller_id")])

        for d in docs:
            try:
                items.append(seller_item(db, d, now, names))
            except Exception as e:
                print(f"Skipped a FairShare product due to mapping error: {e}")

    seed_value = hash(q) if q else (hash(category) if category else 42)
    random.Random(seed_value).shuffle(items)

    window = items[(page - 1) * page_size: page * page_size]
    _attach_group_sizes(db, window)

    return {"items": window, "total": total, "page": page, "page_size": page_size}


def get_group(db, group_key: str, now=None) -> dict:
    now = now or utcnow()
    match = db.product_matches.find_one({"group_key": group_key})
    if not match:
        raise AppError(404, "NOT_FOUND", "Comparison group not found.")

    exact = [external_item(d, now) for d in db.external_products.find({"_id": {"$in": match.get("external_product_ids", [])}})]

    sel_docs = list(db.products.find({"_id": {"$in": match.get("seller_product_ids", [])}}))
    names = product_service.business_names(db, [d.get("seller_id") for d in sel_docs if d.get("seller_id")])
    exact += [seller_item(db, d, now, names) for d in sel_docs]

    exact.sort(key=lambda i: (i.get("price_paisa", 0), i["id"]))
    for i in exact:
        i["group_size"] = len(exact)

    candidates = [i for i in exact if i.get("availability") != "out_of_stock" and i.get("freshness") == "fresh"]
    cheapest_id = min(candidates, key=lambda i: i.get("price_paisa", 0))["id"] if candidates else None

    possible = []
    anchor = exact[0] if exact else None
    brand = ((anchor or {}).get("brand") or "").strip()

    if anchor and brand:
        brx = {"$regex": f"^{re.escape(brand)}$", "$options": "i"}
        taken = {i["id"] for i in exact}

        pool = [external_item(d, now) for d in db.external_products.find({"brand": brx}).limit(60)]
        sdocs = list(db.products.find({"brand": brx}).limit(60))
        snames = product_service.business_names(db, [d.get("seller_id") for d in sdocs if d.get("seller_id")])

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