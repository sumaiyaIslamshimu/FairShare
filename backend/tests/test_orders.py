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

    # ---- overselling: the stock guard must hold even when the cart view is stale (a race between two checkouts) ----
    def _stock(db, prod):
        from bson import ObjectId
        return db.seller_products.find_one({"_id": ObjectId(prod["id"])})["stock_qty"]

    def test_two_checkouts_for_the_last_units_never_oversell(client, db, make_account):
        from app.services import order_service

        seller, h_seller = approved_seller(make_account, db)
        prod = create_product(client, h_seller, price_paisa=1000, stock_qty=5)
        _, ha = make_account(email="a@test.com")
        _, hb = make_account(email="b@test.com")
        for h in (ha, hb):
            assert client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 3},
                               headers=h).status_code in (200, 201)

        # B's checkout read its cart BEFORE A paid: freeze that stale view.
        b_user = db.users.find_one({"email": "b@test.com"})
        stale_cart = order_service.get_cart(db, b_user)

        body = {"shipping_address": "Road 1", "phone": "01700000000"}
        assert client.post("/api/checkout", json=body, headers=ha).status_code == 201
        assert _stock(db, prod) == 2

        original = order_service.get_cart
        order_service.get_cart = lambda _db, _u: stale_cart  # B still believes 5 are in stock
        try:
            res = client.post("/api/checkout", json=body, headers=hb)
        finally:
            order_service.get_cart = original
        assert res.status_code == 409 and res.json()["error"]["code"] == "OUT_OF_STOCK"
        assert _stock(db, prod) == 2  # not -1
        assert db.orders.count_documents({}) == 1  # B got no order

    def test_a_failed_multi_item_checkout_gives_back_everything_it_took(client, db, make_account, monkeypatch):
        from app.services import order_service

        seller, h_seller = approved_seller(make_account, db)
        p1 = create_product(client, h_seller, title="Rice 5 kg", price_paisa=1000, stock_qty=5)
        p2 = create_product(client, h_seller, title="Lentils 1 kg", price_paisa=500, stock_qty=1)
        _, hu = make_account(email="u@test.com")
        for p, q in ((p1, 2), (p2, 1)):
            client.post("/api/cart/items", json={"seller_product_id": p["id"], "quantity": q}, headers=hu)
        user = db.users.find_one({"email": "u@test.com"})
        stale = order_service.get_cart(db, user)
        from bson import ObjectId
        db.seller_products.update_one({"_id": ObjectId(p2["id"])}, {"$set": {"stock_qty": 0}})  # sold out meanwhile

        monkeypatch.setattr(order_service, "get_cart", lambda _db, _u: stale)
        res = client.post("/api/checkout", json={"shipping_address": "Road 1", "phone": "01700000000"}, headers=hu)
        assert res.status_code == 409
        assert _stock(db, p1) == 5  # the first item's stock was returned
        assert db.orders.count_documents({}) == 0 and db.order_items.count_documents({}) == 0
        assert client.get("/api/cart", headers=hu).json()["total_items"] >= 1  # cart untouched

    def test_a_crash_while_writing_the_order_releases_the_stock(client, db, make_account, monkeypatch):
        seller, h_seller = approved_seller(make_account, db)
        prod = create_product(client, h_seller, price_paisa=1000, stock_qty=5)
        _, hu = make_account(email="u@test.com")
        client.post("/api/cart/items", json={"seller_product_id": prod["id"], "quantity": 2}, headers=hu)

        def boom(*a, **k):
            raise RuntimeError("database went away")

        monkeypatch.setattr(db.order_items.__class__, "insert_one", boom)
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            res = c.post("/api/checkout", json={"shipping_address": "Road 1", "phone": "01700000000"}, headers=hu)
        assert res.status_code >= 500
        monkeypatch.undo()
        assert _stock(db, prod) == 5
        assert db.orders.count_documents({}) == 0