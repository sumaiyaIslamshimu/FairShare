"""Shared helpers for Member 2's tests (kept out of M1's conftest.py)."""
from bson import ObjectId

from app.scrapers.base import RawProduct
from app.scrapers.normalizer import normalize_product
from app.scrapers.persistence import save_normalized

BASE = "https://shop.test"

SELLER_BODY = {
    "title": "Pran Miniket Rice 5 kg", "description": "Good rice", "brand": "Pran",
    "category_slug": "groceries-food", "subcategory_slug": "rice-pulses-grains",
    "price_paisa": 70000, "stock_qty": 10, "images": ["https://img.test/rice.jpg"],
}


def make_ext(store="daraz", name="Pran Miniket Rice 5 kg", price="৳ 700", brand="Pran", category_text="Rice",
             availability="InStock", url=None, pid=None, original=None):
    raw = RawProduct(store=store, name=name, product_url=url or f"/p/{store}/{name.replace(' ', '-')}", price=price,
                     brand=brand, category_text=category_text, availability=availability,
                     store_product_id=pid, original_price=original)
    return normalize_product(raw, BASE)


def save_ext(db, *products):
    return save_normalized(db, list(products))


def approved_seller(make_account, db, email="seller@example.com"):
    user, headers = make_account(email=email, role="seller")
    db.seller_profiles.update_one({"user_id": ObjectId(user["id"])}, {"$set": {"status": "approved"}})
    return user, headers


def create_product(client, headers, **overrides):
    r = client.post("/api/seller/products", json={**SELLER_BODY, **overrides}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()