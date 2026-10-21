"""Tests for Cart isolation and dynamic pricing."""
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from tests.helpers_m2 import approved_seller, create_product


def test_stage3_cart_rejects_external_products(client, db, make_account):
    user, h_user = make_account(email="shopper@test.com", role="user")

    # Fake an external product from M2
    ext_id = ObjectId()
    db.external_products.insert_one({
        "_id": ext_id,
        "store": "daraz",
        "store_product_id": "123",
        "name": "External Item",
        "price_paisa": 500,
        "product_url": "http://daraz.test",
        "status": "active"
    })

    res = client.post("/api/cart/items", json={"seller_product_id": str(ext_id), "quantity": 1}, headers=h_user)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "NOT_A_FAIRSHARE_PRODUCT"


def test_stage3_cart_dynamic_pricing_and_promotions(client, db, make_account):
    seller, h_seller = approved_seller(make_account, db)
    prod = create_product(client, h_seller, price_paisa=1000)

    user, h_user = make_account(email="buyer@test.com", role="user")

    # Add to cart
    res = client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 2}, headers=h_user)
    assert res.status_code == 200
    cart = res.json()
    assert cart["subtotal_paisa"] == 2000
    assert cart["items"][0]["effective_price_paisa"] == 1000

    # Seller creates a 50% promotion
    now = datetime.now(timezone.utc)
    client.post("/api/seller/promotions", json={
        "name": "Half Price",
        "product_ids": [prod["id"]],
        "discount_percent": 50,
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=7)).isoformat()
    }, headers=h_seller)

    # Fetch cart again - price should automatically drop to 500 per item
    res = client.get("/api/cart", headers=h_user)
    cart = res.json()
    assert cart["items"][0]["effective_price_paisa"] == 500
    assert cart["items"][0]["discount_percent"] == 50
    assert cart["subtotal_paisa"] == 1000  # 500 * 2


def test_stage3_cart_update_remove_clear(client, db, make_account):
    seller, h_seller = approved_seller(make_account, db)
    prod = create_product(client, h_seller)
    user, h_user = make_account(email="buyer2@test.com", role="user")

    client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 1}, headers=h_user)

    # Update
    res = client.put(f"/api/cart/items/{prod['id']}", json={"quantity": 5}, headers=h_user)
    assert res.json()["total_items"] == 5

    # Remove
    res = client.delete(f"/api/cart/items/{prod['id']}", headers=h_user)
    assert res.json()["total_items"] == 0

    # Clear
    client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 1}, headers=h_user)
    assert client.delete("/api/cart", headers=h_user).status_code == 204
    assert client.get("/api/cart", headers=h_user).json()["total_items"] == 0