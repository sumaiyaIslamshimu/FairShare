"""Notifications: privacy (only the owner), read state, and that real events create them."""
from bson import ObjectId

from tests.helpers_m2 import approved_seller, create_product


def mine(client, h, **params):
    return client.get("/api/notifications", params=params, headers=h).json()


def order_for(client, db, make_account):
    seller, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    shopper, hu = make_account(email="shopper@example.com")
    client.post("/api/cart/items", json={"seller_product_id": product["id"], "quantity": 1}, headers=hu)
    order = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"}, headers=hu).json()
    return seller, hs, shopper, hu, product, order


def test_checkout_notifies_the_seller_and_only_the_seller(client, db, make_account):
    _, hs, _, hu, _, order = order_for(client, db, make_account)
    got = mine(client, hs)
    assert got["total"] == 1 and got["unread"] == 1 and got["items"][0]["kind"] == "order"
    assert order["order_number"] in got["items"][0]["body"]
    assert mine(client, hu)["total"] == 0


def test_seller_moving_an_item_notifies_the_shopper(client, db, make_account):
    _, hs, _, hu, _, order = order_for(client, db, make_account)
    item_id = order["items"][0]["id"]
    assert client.patch(f"/api/seller/orders/{item_id}/status", json={"status": "shipped"}, headers=hs).status_code == 200
    got = mine(client, hu)
    assert got["total"] == 1 and "shipped" in got["items"][0]["title"]


def test_complaint_update_and_verification_notify_the_right_person(client, db, make_account, admin_headers):
    _, hs, shopper, hu, _, order = order_for(client, db, make_account)
    cid = client.post("/api/complaints", json={"target_type": "order", "target_id": order["id"],
                                               "description": "The item never arrived."}, headers=hu).json()["id"]
    client.patch(f"/api/admin/complaints/{cid}", json={"status": "in_review", "admin_note": "Looking"}, headers=admin_headers)
    titles = [n["title"] for n in mine(client, hu)["items"]]
    assert "Your complaint was updated" in titles
    assert all(n["kind"] != "complaint" for n in mine(client, hs)["items"])


def test_review_and_return_notify_the_seller(client, db, make_account):
    _, hs, _, hu, _, order = order_for(client, db, make_account)
    item_id = order["items"][0]["id"]
    db.order_items.update_one({"_id": ObjectId(item_id)}, {"$set": {"item_status": "delivered"}})
    client.post("/api/reviews", json={"order_item_id": item_id, "rating": 5}, headers=hu)
    client.post("/api/returns", json={"order_item_id": item_id, "reason": "damaged"}, headers=hu)
    kinds = {n["kind"] for n in mine(client, hs)["items"]}
    assert {"order", "review", "return"} <= kinds


def test_unread_count_mark_one_and_mark_all(client, db, make_account):
    _, hs, _, hu, product, _ = order_for(client, db, make_account)
    other = approved_seller(make_account, db, email="s2@example.com")[1]
    assert client.get("/api/notifications/unread-count", headers=hs).json() == {"unread": 1}
    first = mine(client, hs)["items"][0]
    r = client.post(f"/api/notifications/{first['id']}/read", headers=hs)
    assert r.status_code == 200 and r.json()["is_read"] is True
    assert client.get("/api/notifications/unread-count", headers=hs).json() == {"unread": 0}
    assert mine(client, hs, unread_only=True)["total"] == 0
    # two more notifications, then read them all at once
    from app.services import notification_service
    seller_id = db.users.find_one({"email": "seller@example.com"})["_id"]
    notification_service.notify(db, seller_id, "x", "one")
    notification_service.notify(db, seller_id, "x", "two")
    assert client.post("/api/notifications/read-all", headers=hs).json()["marked"] == 2
    assert client.get("/api/notifications/unread-count", headers=hs).json() == {"unread": 0}
    assert mine(client, other)["total"] == 0


def test_nobody_can_read_or_change_someone_elses_notification(client, db, make_account):
    _, hs, _, hu, _, _ = order_for(client, db, make_account)
    nid = mine(client, hs)["items"][0]["id"]
    assert client.post(f"/api/notifications/{nid}/read", headers=hu).status_code == 404
    assert client.post(f"/api/notifications/{str(ObjectId())}/read", headers=hs).status_code == 404
    assert mine(client, hs)["unread"] == 1  # untouched by the stranger
    assert client.post("/api/notifications/read-all", headers=hu).json()["marked"] == 0
    assert mine(client, hs)["unread"] == 1


def test_login_is_required(client):
    assert client.get("/api/notifications").status_code == 401
    assert client.get("/api/notifications/unread-count").status_code == 401
    assert client.post("/api/notifications/read-all").status_code == 401


def test_a_failing_notification_never_breaks_the_action(client, db, make_account, monkeypatch):
    from app.services import notification_service

    def boom():
        raise RuntimeError("clock exploded")

    monkeypatch.setattr(notification_service, "utcnow", boom)  # makes every notify() fail inside its try block
    seller, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    _, hu = make_account(email="shopper@example.com")
    client.post("/api/cart/items", json={"seller_product_id": product["id"], "quantity": 1}, headers=hu)
    r = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"}, headers=hu)
    assert r.status_code == 201  # the order still went through
    assert db.notifications.count_documents({}) == 0