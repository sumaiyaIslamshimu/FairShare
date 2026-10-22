"""Stage 7: Cross-Module Security and Isolation Boundary Tests."""
from bson import ObjectId

from tests.helpers_m2 import approved_seller, create_product


def test_boundary_cart_rejects_external_scraped_products(client, db, make_account):
    """Proves M2's read-only external catalog cannot be purchased in M3's cart."""
    user, h_user = make_account(email="shopper_iso@test.com", role="user")

    # Fake an external product (M2 structure)
    ext_id = ObjectId()
    db.external_products.insert_one({
        "_id": ext_id,
        "store": "chaldal",
        "store_product_id": "ext_999",
        "name": "Scraped Rice",
        "price_paisa": 500,
        "product_url": "http://chaldal.test",
        "status": "active"
    })

    res = client.post("/api/cart/items", json={"seller_product_id": str(ext_id), "quantity": 1}, headers=h_user)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "NOT_A_FAIRSHARE_PRODUCT"


def test_boundary_seller_cannot_promote_others_inventory(client, db, make_account):
    """Proves a seller cannot create a discount that affects a competitor's product."""
    seller1, h_s1 = approved_seller(make_account, db, email="seller1_iso@test.com")
    seller2, h_s2 = approved_seller(make_account, db, email="seller2_iso@test.com")

    # Seller 1 creates a product
    prod = create_product(client, h_s1)

    # Seller 2 attempts to create a promotion for Seller 1's product
    promo_data = {
        "name": "Hacked Sale",
        "product_ids": [prod["id"]],
        "discount_percent": 90,
        "starts_at": "2026-01-01T00:00:00Z",
        "ends_at": "2026-12-31T23:59:59Z"
    }
    res = client.post("/api/seller/promotions", json=promo_data, headers=h_s2)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_boundary_order_state_machine_prevents_skipping(client, db, make_account):
    """Proves a seller cannot bypass the 'shipped' state to immediately mark an order 'delivered'."""
    seller, h_seller = approved_seller(make_account, db, email="seller3_iso@test.com")
    prod = create_product(client, h_seller, price_paisa=1000, stock_qty=10)

    user, h_user = make_account(email="buyer_iso@test.com", role="user")

    # Buy the item
    client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 1}, headers=h_user)
    client.post("/api/checkout", json={"shipping_address": "Dhaka"}, headers=h_user)

    # Seller retrieves the order item ID
    orders = client.get("/api/seller/orders", headers=h_seller).json()
    item_id = orders["items"][0]["id"]

    # Attempt invalid jump: confirmed -> delivered
    res = client.patch(f"/api/seller/orders/{item_id}/status", json={"status": "delivered"}, headers=h_seller)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INVALID_TRANSITION"


def test_boundary_unverified_users_blocked_from_rentals(client, db, make_account):
    """Proves M1's unverified users are strictly blocked from M3's rental ecosystem."""
    # Renter account with 'pending' verification status
    renter, h_renter = make_account(email="unverified_renter@test.com", role="user")
    db.users.update_one({"_id": ObjectId(renter["id"])}, {"$set": {"verification_status": "pending"}})

    res = client.post("/api/rentals/listings", json={
        "title": "Camera", "daily_rate_paisa": 1000, "location": "Dhaka"
    }, headers=h_renter)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "UNVERIFIED_USER"


def test_boundary_messaging_strictly_isolated_to_participants(client, db, make_account):
    """Proves User C receives a 403 when trying to fetch a thread between User A and User B."""
    userA, h_A = make_account(email="msgA@test.com", role="user")
    userB, h_B = make_account(email="msgB@test.com", role="user")
    userC, h_C = make_account(email="msgC@test.com", role="user")

    # User A messages User B
    res = client.post("/api/messages", json={
        "recipient_id": userB["id"],
        "body": "Private message"
    }, headers=h_A)
    thread_id = res.json()["thread_id"]

    # User C attempts to read the thread
    res_c = client.get(f"/api/messages/threads/{thread_id}", headers=h_C)
    assert res_c.status_code == 403
    assert res_c.json()["error"]["code"] == "FORBIDDEN"