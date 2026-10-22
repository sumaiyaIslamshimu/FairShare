"""Tests for Checkout and Order Fulfillment."""
from tests.helpers_m2 import approved_seller, create_product


def test_stage4_checkout_reduces_stock_and_clears_cart(client, db, make_account):
    seller, h_seller = approved_seller(make_account, db)
    prod = create_product(client, h_seller, price_paisa=1000, stock_qty=5)

    user, h_user = make_account(email="buyer3@test.com", role="user")

    # 1. Add to cart
    client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 2}, headers=h_user)

    # 2. Checkout
    checkout_data = {"shipping_address": "123 Test St", "phone": "01700000000"}
    res = client.post("/api/checkout", json=checkout_data, headers=h_user)

    assert res.status_code == 201
    order = res.json()
    assert order["subtotal_paisa"] == 2000
    assert len(order["items"]) == 1

    # 3. Verify Cart is Empty
    cart = client.get("/api/cart", headers=h_user).json()
    assert cart["total_items"] == 0

    # 4. Verify Stock was reduced to 3
    p_check = client.get(f"/api/seller-products/{prod['id']}").json()
    assert p_check["availability"] == "in_stock"
    # Owner fetch to see actual number
    p_owner = client.get("/api/seller/products", headers=h_seller).json()
    assert p_owner["items"][0]["stock_qty"] == 3


def test_stage4_out_of_stock_prevents_checkout(client, db, make_account):
    seller, h_seller = approved_seller(make_account, db)
    prod = create_product(client, h_seller, stock_qty=1)

    user, h_user = make_account(email="buyer4@test.com", role="user")
    client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 5}, headers=h_user)

    res = client.post("/api/checkout", json={"shipping_address": "123 St"}, headers=h_user)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "OUT_OF_STOCK"


def test_stage4_seller_fulfillment_pipeline(client, db, make_account):
    seller, h_seller = approved_seller(make_account, db)
    prod = create_product(client, h_seller, price_paisa=1000, stock_qty=10)

    user, h_user = make_account(email="buyer5@test.com", role="user")
    client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 1}, headers=h_user)
    client.post("/api/checkout", json={"shipping_address": "123 St"}, headers=h_user)

    # Seller views orders
    res = client.get("/api/seller/orders", headers=h_seller)
    item_id = res.json()["items"][0]["id"]

    # Attempt invalid jump: confirmed -> delivered (should fail 403)
    bad_jump = client.patch(f"/api/seller/orders/{item_id}/status", json={"status": "delivered"}, headers=h_seller)
    assert bad_jump.status_code == 403

    # Valid flow: confirmed -> shipped -> delivered
    r1 = client.patch(f"/api/seller/orders/{item_id}/status", json={"status": "shipped"}, headers=h_seller)
    assert r1.status_code == 200
    assert r1.json()["item_status"] == "shipped"

    r2 = client.patch(f"/api/seller/orders/{item_id}/status", json={"status": "delivered"}, headers=h_seller)
    assert r2.status_code == 200
    assert r2.json()["item_status"] == "delivered"