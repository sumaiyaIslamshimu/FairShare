"""Admin rules: statistics, users, sellers, moderation, taxonomy management and the scraping monitor."""
import re
from datetime import timedelta

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.scrapers import all_stores
from app.services import audit_service, compare_service
from app.services.time_utils import aware, iso, utcnow
from app.services import audit_service, compare_service, notification_service

REFRESH_COOLDOWN_SECONDS = 60


def _like(text: str) -> dict:
    return {"$regex": re.escape(text.strip()), "$options": "i"}


def _page(cursor, page: int, page_size: int):
    return cursor.skip((page - 1) * page_size).limit(page_size)


# ---------------- statistics ----------------

def stats(db) -> dict:
    count = lambda coll, flt=None: db[coll].count_documents(flt or {})  # noqa: E731
    sources = compare_service.store_sources(db)
    by_status: dict[str, int] = {}
    for s in sources:
        by_status[s["status"]] = by_status.get(s["status"], 0) + 1
    return {
        "users": {"total": count("users"), "shoppers": count("users", {"role": "user"}),
                  "sellers": count("users", {"role": "seller"}), "admins": count("users", {"role": "admin"}),
                  "suspended": count("users", {"is_active": False})},
        "sellers": {"pending": count("seller_profiles", {"status": "pending"}),
                    "approved": count("seller_profiles", {"status": "approved"}),
                    "suspended": count("seller_profiles", {"status": "suspended"})},
        "verifications": {"pending": count("verification_records", {"status": "pending"}),
                          "approved": count("verification_records", {"status": "approved"}),
                          "rejected": count("verification_records", {"status": "rejected"})},
        "products": {"fairshare": count("seller_products", {"status": {"$ne": "removed"}}),
                     "hidden": count("seller_products", {"moderation_status": "hidden"}),
                     "external": count("external_products")},
        "orders": {"total": count("orders"), "pending": count("orders", {"status": "pending"})},
        "rentals": {"listings": count("rental_listings", {"status": {"$ne": "removed"}}),
                    "requests": count("rental_requests"), "bookings": count("rental_bookings")},
        "complaints": {"open": count("complaints", {"status": "open"}),
                       "in_review": count("complaints", {"status": "in_review"}),
                       "total": count("complaints")},
        "scraping": {"stores": len(sources), "by_status": by_status},
    }


# ---------------- users and sellers ----------------

def _user_out(db, u: dict) -> dict:
    seller_status = None
    if u["role"] == "seller":
        p = db.seller_profiles.find_one({"user_id": u["_id"]})
        seller_status = p["status"] if p else None
    return {"id": str(u["_id"]), "full_name": u.get("full_name", ""), "email": u["email"], "phone": u.get("phone", ""),
            "role": u["role"], "is_active": u.get("is_active", True),
            "verification_status": u.get("verification_status", "none"), "seller_status": seller_status,
            "created_at": iso(u.get("created_at"))}


def list_users(db, q, role, is_active, page, page_size) -> dict:
    flt: dict = {}
    if q:
        flt["$or"] = [{"email": _like(q)}, {"full_name": _like(q)}]
    if role:
        flt["role"] = role
    if is_active is not None:
        flt["is_active"] = is_active
    total = db.users.count_documents(flt)
    cur = _page(db.users.find(flt, {"password_hash": 0}).sort("created_at", -1), page, page_size)
    return {"items": [_user_out(db, u) for u in cur], "total": total, "page": page, "page_size": page_size}


def set_user_active(db, admin: dict, user_id: str, active: bool) -> dict:
    user = db.users.find_one({"_id": to_object_id(user_id, "User")})
    if not user:
        raise AppError(404, "NOT_FOUND", "User not found.")
    if user["_id"] == admin["_id"]:
        raise AppError(409, "CANNOT_MODIFY_SELF", "You cannot suspend your own account.")
    if user["role"] == "admin":
        raise AppError(403, "FORBIDDEN", "Admin accounts cannot be suspended here.")
    db.users.update_one({"_id": user["_id"]}, {"$set": {"is_active": active, "updated_at": utcnow()}})
    audit_service.log(db, admin, "user.activate" if active else "user.suspend", str(user["_id"]))
    return _user_out(db, db.users.find_one({"_id": user["_id"]}))


def list_sellers(db, status, page, page_size) -> dict:
    flt = {"status": status} if status else {}
    total = db.seller_profiles.count_documents(flt)
    cur = _page(db.seller_profiles.find(flt).sort("created_at", -1), page, page_size)
    return {"items": [_seller_row(db, p) for p in cur], "total": total, "page": page, "page_size": page_size}


def _seller_row(db, p: dict) -> dict:
    u = db.users.find_one({"_id": p["user_id"]}) or {}
    return {"user_id": str(p["user_id"]), "business_name": p.get("business_name", ""),
            "full_name": u.get("full_name", ""), "email": u.get("email", ""), "status": p["status"],
            "verification_status": u.get("verification_status", "none"), "created_at": iso(p.get("created_at"))}


def set_seller_status(db, admin: dict, user_id: str, status: str) -> dict:
    uid = to_object_id(user_id, "Seller")
    profile = db.seller_profiles.find_one({"user_id": uid})
    user = db.users.find_one({"_id": uid})
    if not profile or not user:
        raise AppError(404, "NOT_FOUND", "Seller not found.")
    if status == "approved" and user.get("verification_status") != "approved":
        raise AppError(409, "SELLER_NOT_VERIFIED", "Approve the seller's identity verification first.")
    db.seller_profiles.update_one({"_id": profile["_id"]}, {"$set": {"status": status, "updated_at": utcnow()}})
    audit_service.log(db, admin, f"seller.{status}", str(uid))
    notification_service.notify(db, uid, "seller", f"Your seller account is now {status}", "", "profile")
    return _seller_row(db, db.seller_profiles.find_one({"_id": profile["_id"]}))


# ---------------- moderation ----------------

def list_products(db, q, moderation_status, page, page_size) -> dict:
    flt: dict = {"status": {"$ne": "removed"}}
    if q:
        flt["title"] = _like(q)
    if moderation_status:
        flt["moderation_status"] = moderation_status
    total = db.seller_products.count_documents(flt)
    cur = _page(db.seller_products.find(flt).sort("created_at", -1), page, page_size)
    items = []
    for p in cur:
        owner = db.users.find_one({"_id": p["seller_id"]}) or {}
        items.append({"id": str(p["_id"]), "title": p["title"], "seller_id": str(p["seller_id"]),
                      "seller_name": owner.get("full_name", ""), "price_paisa": p["price_paisa"],
                      "stock_qty": p.get("stock_qty", 0), "status": p.get("status", "active"),
                      "moderation_status": p.get("moderation_status", "visible"),
                      "category_slug": p.get("category_slug", ""), "subcategory_slug": p.get("subcategory_slug", "")})
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def moderate_product(db, admin: dict, product_id: str, moderation_status: str) -> dict:
    prod = db.seller_products.find_one({"_id": to_object_id(product_id, "Product")})
    if not prod or prod.get("status") == "removed":
        raise AppError(404, "NOT_FOUND", "Product not found.")
    changes = {"moderation_status": moderation_status, "updated_at": utcnow()}
    if moderation_status == "removed":
        changes["status"] = "removed"  # soft delete: old orders can still refer to it
    db.seller_products.update_one({"_id": prod["_id"]}, {"$set": changes})
    audit_service.log(db, admin, f"product.{moderation_status}", str(prod["_id"]))
    if prod.get("group_key"):
        try:  # keep M2's match groups consistent with what shoppers can see
            from app.services.match_service import sync_group
            sync_group(db, prod["group_key"])
        except Exception:  # moderation must succeed even if regrouping fails
            pass
    owner = db.users.find_one({"_id": prod["seller_id"]}) or {}
    return {"id": str(prod["_id"]), "title": prod["title"], "seller_id": str(prod["seller_id"]),
            "seller_name": owner.get("full_name", ""), "price_paisa": prod["price_paisa"],
            "stock_qty": prod.get("stock_qty", 0), "status": changes.get("status", prod.get("status", "active")),
            "moderation_status": moderation_status, "category_slug": prod.get("category_slug", ""),
            "subcategory_slug": prod.get("subcategory_slug", "")}


def list_rental_listings(db, q, status, page, page_size) -> dict:
    flt: dict = {}
    if q:
        flt["title"] = _like(q)
    flt["status"] = status if status else {"$ne": "removed"}
    total = db.rental_listings.count_documents(flt)
    cur = _page(db.rental_listings.find(flt).sort("created_at", -1), page, page_size)
    items = []
    for r in cur:
        owner = db.users.find_one({"_id": r["owner_id"]}) or {}
        items.append({"id": str(r["_id"]), "title": r["title"], "owner_id": str(r["owner_id"]),
                      "owner_name": owner.get("full_name", ""), "location": r.get("location", ""),
                      "daily_rate_paisa": r["daily_rate_paisa"], "status": r.get("status", "active")})
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def moderate_rental(db, admin: dict, listing_id: str, status: str) -> dict:
    doc = db.rental_listings.find_one({"_id": to_object_id(listing_id, "Listing")})
    if not doc:
        raise AppError(404, "NOT_FOUND", "Listing not found.")
    db.rental_listings.update_one({"_id": doc["_id"]}, {"$set": {"status": status, "updated_at": utcnow()}})
    audit_service.log(db, admin, f"rental.{status}", str(doc["_id"]))
    owner = db.users.find_one({"_id": doc["owner_id"]}) or {}
    return {"id": str(doc["_id"]), "title": doc["title"], "owner_id": str(doc["owner_id"]),
            "owner_name": owner.get("full_name", ""), "location": doc.get("location", ""),
            "daily_rate_paisa": doc["daily_rate_paisa"], "status": status}


# ---------------- taxonomy management ----------------

def _category_out(c: dict) -> dict:
    return {"slug": c["slug"], "name": c["name"], "is_active": c.get("is_active", True), "order": c.get("order", 0)}


def list_taxonomy(db) -> list[dict]:
    """Every category and subcategory, including inactive ones, with usage counts for the admin screen."""
    subs: dict[str, list] = {}
    for s in db.subcategories.find({}).sort("name", 1):
        subs.setdefault(s["category_slug"], []).append({
            "slug": s["slug"], "name": s["name"], "is_active": s.get("is_active", True),
            "in_use": _sub_usage(db, s["slug"])})
    out = []
    for c in db.categories.find({}).sort("order", 1):
        out.append({**_category_out(c), "in_use": _cat_usage(db, c["slug"]), "subcategories": subs.get(c["slug"], [])})
    return out


def _cat_usage(db, slug: str) -> int:
    return (db.seller_products.count_documents({"category_slug": slug, "status": {"$ne": "removed"}})
            + db.external_products.count_documents({"category_slug": slug}))


def _sub_usage(db, slug: str) -> int:
    return (db.seller_products.count_documents({"subcategory_slug": slug, "status": {"$ne": "removed"}})
            + db.external_products.count_documents({"subcategory_slug": slug}))


def create_category(db, admin: dict, data) -> dict:
    if db.categories.find_one({"slug": data.slug}):
        raise AppError(409, "SLUG_EXISTS", "A category with this slug already exists.")
    order = data.order if data.order is not None else db.categories.count_documents({})
    doc = {"slug": data.slug, "name": data.name, "is_active": True, "order": order}
    db.categories.insert_one(doc)
    audit_service.log(db, admin, "category.create", data.slug)
    return _category_out(doc)


def update_category(db, admin: dict, slug: str, data) -> dict:
    cat = db.categories.find_one({"slug": slug})
    if not cat:
        raise AppError(404, "NOT_FOUND", "Category not found.")
    changes = data.model_dump(exclude_none=True)
    if changes.get("is_active") is False and db.seller_products.count_documents(
            {"category_slug": slug, "status": {"$ne": "removed"}}):
        raise AppError(409, "CATEGORY_IN_USE",
                       "Active or inactive seller listings still use this category. Move or remove them first.")
    if changes:
        db.categories.update_one({"slug": slug}, {"$set": changes})
        audit_service.log(db, admin, "category.update", slug, {"fields": sorted(changes)})
    return _category_out(db.categories.find_one({"slug": slug}))


def delete_category(db, admin: dict, slug: str) -> None:
    if not db.categories.find_one({"slug": slug}):
        raise AppError(404, "NOT_FOUND", "Category not found.")
    if db.subcategories.count_documents({"category_slug": slug}):
        raise AppError(409, "CATEGORY_HAS_SUBCATEGORIES", "Delete or move its subcategories first.")
    if _cat_usage(db, slug):
        raise AppError(409, "CATEGORY_IN_USE", "Listings still use this category, so it cannot be deleted.")
    db.categories.delete_one({"slug": slug})
    audit_service.log(db, admin, "category.delete", slug)


def create_subcategory(db, admin: dict, data) -> dict:
    if not db.categories.find_one({"slug": data.category_slug}):
        raise AppError(422, "INVALID_CATEGORY", "The parent category does not exist.")
    if db.subcategories.find_one({"slug": data.slug}):
        raise AppError(409, "SLUG_EXISTS", "A subcategory with this slug already exists.")
    doc = {"slug": data.slug, "category_slug": data.category_slug, "name": data.name, "is_active": True}
    db.subcategories.insert_one(doc)
    audit_service.log(db, admin, "subcategory.create", data.slug)
    return {"slug": doc["slug"], "category_slug": doc["category_slug"], "name": doc["name"], "is_active": True}


def update_subcategory(db, admin: dict, slug: str, data) -> dict:
    sub = db.subcategories.find_one({"slug": slug})
    if not sub:
        raise AppError(404, "NOT_FOUND", "Subcategory not found.")
    changes = data.model_dump(exclude_none=True)
    if changes.get("is_active") is False and db.seller_products.count_documents(
            {"subcategory_slug": slug, "status": {"$ne": "removed"}}):
        raise AppError(409, "CATEGORY_IN_USE", "Seller listings still use this subcategory.")
    if changes:
        db.subcategories.update_one({"slug": slug}, {"$set": changes})
        audit_service.log(db, admin, "subcategory.update", slug, {"fields": sorted(changes)})
    s = db.subcategories.find_one({"slug": slug})
    return {"slug": s["slug"], "category_slug": s["category_slug"], "name": s["name"],
            "is_active": s.get("is_active", True)}


def delete_subcategory(db, admin: dict, slug: str) -> None:
    if not db.subcategories.find_one({"slug": slug}):
        raise AppError(404, "NOT_FOUND", "Subcategory not found.")
    if _sub_usage(db, slug):
        raise AppError(409, "CATEGORY_IN_USE", "Listings still use this subcategory, so it cannot be deleted.")
    db.subcategories.delete_one({"slug": slug})
    audit_service.log(db, admin, "subcategory.delete", slug)


# ---------------- scraping monitor ----------------

def scraping_status(db) -> list[dict]:
    """Per-store state exactly as recorded by the runner (success / partial / failure / unsupported / never_run).
    `stale` is added when the last success is older than the freshness threshold."""
    now = utcnow()
    limit = timedelta(hours=compare_service.stale_after_hours())
    out = []
    for s in compare_service.store_sources(db):
        last = s.get("last_success_at")
        s["stale"] = bool(last) and now - aware(_parse(last)) > limit
        out.append(s)
    return out


def _parse(value):
    from datetime import datetime
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def scraping_runs(db, store: str | None, page: int, page_size: int) -> dict:
    if store is not None and store not in all_stores():
        raise AppError(404, "NOT_FOUND", "Unknown store.")
    flt = {"store": store} if store else {}
    total = db.scrape_runs.count_documents(flt)
    cur = _page(db.scrape_runs.find(flt).sort("started_at", -1), page, page_size)
    items = [{"id": str(r["_id"]), "store": r["store"], "status": r.get("status", ""),
              "started_at": iso(r.get("started_at")), "finished_at": iso(r.get("finished_at")),
              "items_found": r.get("items_found", 0), "errors": r.get("errors", [])} for r in cur]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def refresh_store_now(db, admin: dict, store: str) -> dict:
    """Admin-triggered refresh. Calls M2's runner (which never raises) once per store per cooldown period."""
    if store not in all_stores():
        raise AppError(404, "NOT_FOUND", "Unknown store.")
    last = db.scrape_runs.find_one({"store": store}, sort=[("started_at", -1)])
    if last and last.get("started_at"):
        wait = REFRESH_COOLDOWN_SECONDS - (utcnow() - aware(last["started_at"])).total_seconds()
        if wait > 0:
            raise AppError(429, "REFRESH_COOLDOWN", f"This store was refreshed moments ago. Try again in {int(wait) + 1}s.")
    from app.scrapers import runner
    result = runner.refresh_store(db, store)
    audit_service.log(db, admin, "scraping.refresh", store, {"status": result.get("status")})
    return {"store": store, "status": result.get("status"), "items_found": result.get("items_found", 0),
            "errors": result.get("errors", []), "notes": result.get("notes", []),
            "started_at": iso(result.get("started_at")), "finished_at": iso(result.get("finished_at"))}