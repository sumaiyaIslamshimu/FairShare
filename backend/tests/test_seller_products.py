from datetime import datetime, timedelta, timezone

from bson import ObjectId

from tests.helpers_m2 import SELLER_BODY, approved_seller, create_product


def test_create_and_list_own_product(client, db, make_account):
    user, h = approved_seller(make_account, db)
    p = create_product(client, h)
    assert p["seller_id"] == user["id"] and p["currency"] == "BDT" and p["stock_qty"] == 10
    assert p["source"] == "fairshare" and p["quantity"] == 5000 and p["unit"] == "g"   # parsed from "5 kg"
    lst = client.get("/api/seller/products", headers=h).json()
    assert lst["total"] == 1 and lst["items"][0]["id"] == p["id"]


def test_client_cannot_set_owner_moderation_or_source(client, db, make_account):
    user, h = approved_seller(make_account, db)
    p = create_product(client, h, seller_id="someone-else", moderation_status="hidden", source="external")
    assert p["seller_id"] == user["id"] and p["moderation_status"] == "visible" and p["source"] == "fairshare"


def test_invalid_category_pair_and_bad_numbers(client, db, make_account):
    _, h = approved_seller(make_account, db)
    r = client.post("/api/seller/products", json={**SELLER_BODY, "subcategory_slug": "smartphones-tablets"}, headers=h)
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_CATEGORY"
    for bad in [{"price_paisa": 0}, {"price_paisa": -5}, {"stock_qty": -1}, {"unit": "kg"}, {"unit": "g"},
                {"images": ["javascript:x"]}, {"title": " "}]:
        r = client.post("/api/seller/products", json={**SELLER_BODY, **bad}, headers=h)
        assert r.status_code == 422, bad


def test_only_approved_sellers_can_publish(client, db, make_account):
    _, pending = make_account(email="p@example.com", role="seller")
    r = client.post("/api/seller/products", json=SELLER_BODY, headers=pending)
    assert r.status_code == 403 and r.json()["error"]["code"] == "SELLER_NOT_APPROVED"
    _, shopper = make_account(email="u@example.com")
    assert client.post("/api/seller/products", json=SELLER_BODY, headers=shopper).status_code == 403
    assert client.post("/api/seller/products", json=SELLER_BODY).status_code == 401


def test_other_seller_cannot_touch_product(client, db, make_account):
    _, a = approved_seller(make_account, db, "a@example.com")
    _, b = approved_seller(make_account, db, "b@example.com")
    pid = create_product(client, a)["id"]
    assert client.put(f"/api/seller/products/{pid}", json=SELLER_BODY, headers=b).status_code == 403
    assert client.delete(f"/api/seller/products/{pid}", headers=b).status_code == 403
    assert client.patch(f"/api/seller/products/{pid}/inventory", json={"stock_qty": 1}, headers=b).status_code == 403
    assert client.get("/api/seller/products", headers=b).json()["total"] == 0
    assert client.put(f"/api/seller/products/{ObjectId()}", json=SELLER_BODY, headers=b).status_code == 404
    assert client.put("/api/seller/products/not-an-id", json=SELLER_BODY, headers=b).status_code == 404


def test_update_and_inventory(client, db, make_account):
    _, h = approved_seller(make_account, db)
    pid = create_product(client, h)["id"]
    r = client.put(f"/api/seller/products/{pid}", json={**SELLER_BODY, "title": "Pran Miniket Rice 1 kg", "price_paisa": 15000}, headers=h)
    assert r.status_code == 200 and r.json()["price_paisa"] == 15000 and r.json()["quantity"] == 1000
    assert client.patch(f"/api/seller/products/{pid}/inventory", json={"stock_qty": -1}, headers=h).status_code == 422
    r = client.patch(f"/api/seller/products/{pid}/inventory", json={"stock_qty": 0}, headers=h)
    assert r.status_code == 200 and r.json()["stock_qty"] == 0
    assert client.get(f"/api/seller-products/{pid}").json()["availability"] == "out_of_stock"


def test_public_listing_rules(client, db, make_account):
    user, h = approved_seller(make_account, db)
    p = create_product(client, h)
    pid = p["id"]
    assert client.get("/api/seller-products").json()["total"] == 1
    detail = client.get(f"/api/seller-products/{pid}").json()
    assert "stock_qty" not in detail and detail["availability"] == "in_stock" and detail["seller_name"] == "Test Store"

    client.put(f"/api/seller/products/{pid}", json={**SELLER_BODY, "status": "inactive"}, headers=h)
    assert client.get("/api/seller-products").json()["total"] == 0
    assert client.get(f"/api/seller-products/{pid}").status_code == 404
    client.put(f"/api/seller/products/{pid}", json=SELLER_BODY, headers=h)

    db.seller_products.update_one({"_id": ObjectId(pid)}, {"$set": {"moderation_status": "hidden"}})
    assert client.get(f"/api/seller-products/{pid}").status_code == 404
    db.seller_products.update_one({"_id": ObjectId(pid)}, {"$set": {"moderation_status": "visible"}})

    db.seller_profiles.update_one({"user_id": ObjectId(user["id"])}, {"$set": {"status": "suspended"}})
    assert client.get("/api/seller-products").json()["total"] == 0


def test_delete_is_soft_and_hides_everywhere(client, db, make_account):
    _, h = approved_seller(make_account, db)
    pid = create_product(client, h)["id"]
    assert client.delete(f"/api/seller/products/{pid}", headers=h).status_code == 204
    assert db.seller_products.find_one({"_id": ObjectId(pid)})["status"] == "removed"
    assert client.get("/api/seller/products", headers=h).json()["total"] == 0
    assert client.get(f"/api/seller-products/{pid}").status_code == 404
    assert client.put(f"/api/seller/products/{pid}", json=SELLER_BODY, headers=h).status_code == 404


def test_effective_price_uses_active_promotions_only(client, db, make_account):
    user, h = approved_seller(make_account, db)
    pid = create_product(client, h)["id"]
    now = datetime.now(timezone.utc)
    promo = {"seller_id": ObjectId(user["id"]), "product_ids": [ObjectId(pid)], "discount_percent": 20,
             "starts_at": now - timedelta(days=1), "ends_at": now + timedelta(days=1), "is_active": True}
    db.promotions.insert_one(promo.copy())
    d = client.get(f"/api/seller-products/{pid}").json()
    assert d["price_paisa"] == 70000 and d["effective_price_paisa"] == 56000 and d["discount_percent"] == 20
    db.promotions.delete_many({})
    db.promotions.insert_one({**promo, "ends_at": now - timedelta(hours=1)})            # expired
    db.promotions.insert_one({**promo, "starts_at": now + timedelta(days=1), "ends_at": now + timedelta(days=2)})  # future
    db.promotions.insert_one({**promo, "is_active": False})                              # switched off
    assert client.get(f"/api/seller-products/{pid}").json()["effective_price_paisa"] == 70000