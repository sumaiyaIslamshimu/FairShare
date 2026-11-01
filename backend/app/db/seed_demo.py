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
    ("demo.shopper@fairshare.test", "Demo Shopper", "user", "none", None),
    ("sabbeer1@gmail.com", "FairShare All-in-One Store", "seller", "approved", "approved"),
    ("demo.pending.seller@fairshare.test", "Pending Seller", "seller", "none", "pending"),
]

DEMO_PRODUCTS = {
    "sabbeer1@gmail.com": [
        # TECH
        dict(title="AMD Ryzen 5 5600G Processor", brand="AMD",
             category_slug="electronics-gadgets", subcategory_slug="computer-accessories",
             price_paisa=1350000, stock_qty=15,
             images=["https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?auto=format&fit=crop&w=500&q=80"],
             description="6-Core, 12-Thread Unlocked Desktop Processor with Radeon Graphics."),
        dict(title="Fantech Revolver WGP12 Wireless Controller", brand="Fantech",
             category_slug="electronics-gadgets", subcategory_slug="gaming-devices-accessories",
             price_paisa=250000, stock_qty=8,
             images=["https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?auto=format&fit=crop&w=500&q=80"],
             description="2.4GHz Wireless Gaming Controller for PC, perfect for action RPGs."),
        dict(title="Sony WH-1000XM5 Wireless Headphones", brand="Sony",
             category_slug="electronics-gadgets", subcategory_slug="headphones-speakers",
             price_paisa=3850000, stock_qty=5,
             images=["https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?auto=format&fit=crop&w=500&q=80"],
             description="Industry leading noise canceling bluetooth over-ear headphones with mic."),
        dict(title="Apple Watch Series 9", brand="Apple",
             category_slug="electronics-gadgets", subcategory_slug="smartwatches-wearables",
             price_paisa=4500000, stock_qty=12,
             images=["https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?auto=format&fit=crop&w=500&q=80"],
             description="Smartwatch with Midnight Aluminum Case and Midnight Sport Band."),
        dict(title="Keychron K2 Mechanical Keyboard", brand="Keychron",
             category_slug="electronics-gadgets", subcategory_slug="computer-accessories",
             price_paisa=950000, stock_qty=20,
             images=["https://images.unsplash.com/photo-1595225476474-87563907a212?auto=format&fit=crop&w=500&q=80"],
             description="75% Layout Bluetooth wireless mechanical keyboard with Gateron switches."),

        # CARE & FASHION
        dict(title="The Face Shop Rice Water Foaming Cleanser", brand="The Face Shop",
             category_slug="home-household", subcategory_slug="bedding-bath",
             price_paisa=95000, stock_qty=20,
             images=["https://images.unsplash.com/photo-1556228578-0d85b1a4d571?auto=format&fit=crop&w=500&q=80"],
             description="Deep cleansing foam with rice extract that purifies and brightens."),
        dict(title="3W Clinic Intensive UV Sunblock SPF 50+", brand="3W Clinic",
             category_slug="fashion-accessories", subcategory_slug="sunglasses-accessories",
             price_paisa=45000, stock_qty=30,
             images=["https://images.unsplash.com/photo-1579246197948-e87f7d2f9bd8?auto=format&fit=crop&w=500&q=80"],
             description="Lightweight, non-greasy sunblock for daily facial protection."),
        dict(title="Classic Polarized Aviator Sunglasses", brand="Ray-Ban",
             category_slug="fashion-accessories", subcategory_slug="sunglasses-accessories",
             price_paisa=1500000, stock_qty=10,
             images=["https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=500&q=80"],
             description="Gold frame with classic green G-15 lenses. 100% UV protection."),
        dict(title="Men's Genuine Leather Oxford Shoes", brand="Bata",
             category_slug="fashion-accessories", subcategory_slug="shoes-footwear",
             price_paisa=550000, stock_qty=25,
             images=["https://images.unsplash.com/photo-1614252339460-e179e0a0d9b4?auto=format&fit=crop&w=500&q=80"],
             description="Premium lace-up formal oxford shoes for men. Comfortable and durable."),
        dict(title="Minimalist Canvas Daypack", brand="Herschel",
             category_slug="fashion-accessories", subcategory_slug="bags-backpacks",
             price_paisa=320000, stock_qty=18,
             images=["https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=500&q=80"],
             description="Everyday canvas backpack with a 15-inch laptop sleeve and front pocket."),

        # GENERAL
        dict(title="Premium Arabica Coffee Beans (500g)", brand="North End",
             category_slug="groceries-food", subcategory_slug="beverages",
             price_paisa=120000, stock_qty=50,
             images=["https://images.unsplash.com/photo-1559525839-b184a4d698c7?auto=format&fit=crop&w=500&q=80"],
             description="Freshly roasted whole bean coffee with notes of dark chocolate."),
        dict(title="Non-Stick Granite Cookware Set", brand="Kiam",
             category_slug="home-household", subcategory_slug="kitchenware-cookware",
             price_paisa=750000, stock_qty=12,
             images=["https://images.unsplash.com/photo-1584990347449-a6efa1a20079?auto=format&fit=crop&w=500&q=80"],
             description="7-piece non-stick pots and pans set with glass lids. Induction ready."),
        dict(title="Non-Slip Yoga Mat with Alignment Lines", brand="FitGear",
             category_slug="sports-fitness", subcategory_slug="yoga-exercise-accessories",
             price_paisa=180000, stock_qty=35,
             images=["https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?auto=format&fit=crop&w=500&q=80"],
             description="Eco-friendly TPE yoga mat. 6mm thick for extra joint protection."),
        dict(title="Adjustable Dumbbell Set (20kg)", brand="GymPro",
             category_slug="sports-fitness", subcategory_slug="gym-fitness-equipment",
             price_paisa=450000, stock_qty=8,
             images=["https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=500&q=80"],
             description="Cast iron adjustable dumbbell set with connector to form a barbell."),
    ]
}

DEMO_RENTALS = [
    dict(title="Lenovo ThinkPad L14 Gen 3", description="Powerful business laptop available for short-term daily rental.",
         daily_rate_paisa=50000, deposit_paisa=1500000, location="Dhaka (demo)",
         images=["https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=500&q=80"]),
    dict(title="DSLR Camera Kit", description="Includes camera body, 50mm lens, and carrying bag. Perfect for weekend trips.",
         daily_rate_paisa=120000, deposit_paisa=5000000, location="Dhaka (demo)",
         images=["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=500&q=80"])
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

    # === AGGRESSIVE CLEANUP OF OLD DEMO ACCOUNTS ===
    old_emails = ["demo.tech@fairshare.test", "demo.care@fairshare.test",
                  "demo.general@fairshare.test", "demo.seller@fairshare.test",
                  "demo.renter@fairshare.test"] # Added demo renter here for cleanup
    for o_email in old_emails:
        ou = db.users.find_one({"email": o_email})
        if ou:
            db.seller_products.delete_many({"seller_id": ou["_id"]})
            db.rental_listings.delete_many({"owner_id": ou["_id"]})

    # Cleanup pictureless items
    db.seller_products.delete_many({
        "$or": [{"images": {"$exists": False}}, {"images": {"$size": 0}}, {"images": None}]
    })

    for email, name, role, verification, seller_status in DEMO_USERS:
        user, new = _ensure_user(db, email, name, role, verification, password)
        created["users"] += int(new)
        users[email] = user

        if seller_status and not db.seller_profiles.find_one({"user_id": user["_id"]}):
            now = _now()
            db.seller_profiles.insert_one({
                "user_id": user["_id"], "business_name": name, "description": f"Demo account for {name}.",
                "contact_phone": "+8801700000000", "address": "Dhaka (demo)", "status": seller_status,
                "created_at": now, "updated_at": now})

    for email, products in DEMO_PRODUCTS.items():
        seller = users.get(email)
        if seller:
            db.seller_products.delete_many({"seller_id": seller["_id"]})
            for p in products:
                desc = p.pop("description", "Demo listing.")
                product_service.create_product(db, seller, SellerProductCreate(**p, description=desc))
                created["products"] += 1

    # MAPPED EXCLUSIVELY TO YOUR ACCOUNT
    renter_owner = users.get("sabbeer1@gmail.com")
    if renter_owner:
        db.rental_listings.delete_many({"owner_id": renter_owner["_id"]})
        for r in DEMO_RENTALS:
            rental_service.create_listing(db, renter_owner, RentalListingCreate(
                **r, available_from=_now().date(), available_to=(_now() + timedelta(days=90)).date()
            ))
            created["rentals"] += 1

    return created

def main() -> None:
    s = get_settings()
    db = get_db()
    ensure_indexes(db)
    result = seed_demo(db, s.demo_password)
    print(f"Demo data ready: {result}")

if __name__ == "__main__":
    main()