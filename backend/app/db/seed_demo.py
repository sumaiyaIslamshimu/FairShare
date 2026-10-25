"""Demo accounts and sample data.   python -m app.db.seed_demo      (run from backend/, after python -m app.db.seed)

- Every demo account uses DEMO_PASSWORD from backend/.env. No password is written in this file.
- Safe to run twice: existing demo accounts and listings are left alone.
- All listings are clearly labelled demo data. Nothing here pretends to be scraped store data.
"""
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.indexes import ensure_indexes
from app.db.mongo import get_db
from app.db.seed import seed_categories
from app.models.rental import RentalListingCreate
from app.models.seller_product import SellerProductCreate
from app.services import product_service, rental_service

DEMO_USERS = [
    # email, name, role, verification, seller profile status
    ("demo.shopper@fairshare.test", "Demo Shopper", "user", "none", None),
    ("demo.renter@fairshare.test", "Demo Renter", "user", "approved", None),
    ("demo.seller@fairshare.test", "Demo Seller", "seller", "approved", "approved"),
    ("demo.pending.seller@fairshare.test", "Pending Seller", "seller", "none", "pending"),
]

DEMO_PRODUCTS = [
    dict(title="Demo Miniket Rice 5 kg", brand="Demo Farms", category_slug="groceries-food",
         subcategory_slug="rice-pulses-grains", price_paisa=72000, stock_qty=40, quantity=5000, unit="g"),
    dict(title="Demo Wireless Headphones", brand="DemoSound", category_slug="electronics-gadgets",
         subcategory_slug="headphones-speakers", price_paisa=250000, stock_qty=12),
    dict(title="Demo Cotton T-Shirt", brand="DemoWear", category_slug="fashion-accessories",
         subcategory_slug="mens-clothing", price_paisa=45000, stock_qty=25),
]


def _now():
    return datetime.now(timezone.utc)


def _ensure_user(db, email, name, role, verification, password):
    user = db.users.find_one({"email": email})
    if user:
        return user, False
    now = _now()
    doc = {"email": email, "full_name": name, "phone": "+8801700000000", "password_hash": hash_password(password),
           "role": role, "is_active": True, "verification_status": verification, "created_at": now, "updated_at": now}
    doc["_id"] = db.users.insert_one(doc).inserted_id
    return doc, True


def seed_demo(db, password: str) -> dict:
    if len(password) < 8:
        raise ValueError("DEMO_PASSWORD must be at least 8 characters (set it in backend/.env).")
    seed_categories(db)
    created = {"users": 0, "products": 0, "rentals": 0}
    users = {}
    for email, name, role, verification, seller_status in DEMO_USERS:
        user, new = _ensure_user(db, email, name, role, verification, password)
        created["users"] += int(new)
        users[email] = user
        if seller_status and not db.seller_profiles.find_one({"user_id": user["_id"]}):
            now = _now()
            db.seller_profiles.insert_one({
                "user_id": user["_id"], "business_name": f"{name} Store", "description": "Demo seller account.",
                "contact_phone": "+8801700000000", "address": "Dhaka (demo)", "status": seller_status,
                "created_at": now, "updated_at": now})

    seller = users["demo.seller@fairshare.test"]
    if not db.seller_products.find_one({"seller_id": seller["_id"]}):
        for p in DEMO_PRODUCTS:
            product_service.create_product(db, seller, SellerProductCreate(**p, description="Demo listing."))
            created["products"] += 1

    renter_owner = users["demo.renter@fairshare.test"]
    if not db.rental_listings.find_one({"owner_id": renter_owner["_id"]}):
        rental_service.create_listing(db, renter_owner, RentalListingCreate(
            title="Demo Camping Tent (4 person)", description="Demo rental listing.", daily_rate_paisa=80000,
            deposit_paisa=200000, location="Dhaka (demo)",
            available_from=_now().date(), available_to=(_now() + timedelta(days=90)).date()))
        created["rentals"] += 1
    return created


def main() -> None:
    s = get_settings()
    db = get_db()
    ensure_indexes(db)
    result = seed_demo(db, s.demo_password)
    print(f"Demo data ready: {result}")
    print("Log in with the demo emails in docs/DEMO_GUIDE.md and the DEMO_PASSWORD from your .env.")


if __name__ == "__main__":
    main()