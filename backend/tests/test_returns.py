"""Returns: only delivered items, one request per item, seller decides, completion restocks, ownership, admin override."""
from bson import ObjectId

from tests.helpers_m2 import approved_seller, create_product


def delivered(client, db, make_account, qty=2, deliver=True):
    seller, hs = approved_seller(make_account, db)
    product = create_product(client, hs, stock_qty=10)
    shopper, hu = make_account(email="shopper@example.com")
    client.post("/api/cart/items", json={"seller_product_id": product["id"], "quantity": qty}, headers=hu)
    order = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"}, headers=hu).json()
    item = order["items"][0]
    if deliver:
        db.order_items.update_one({"_id": ObjectId(item["id"])}, {"$set": {"item_status": "delivered"}})
    return hs, hu, product, item


def ask(client, hu, item, reason="damaged", details=""):
    return client.post("/api/returns", json={"order_item_id": item["id"], "reason": reason, "details": details}, headers=hu)


def stock(db, product):
    return db.seller_products.find_one({"_id": ObjectId(product["id"])})["stock_qty"]


def test_full_flow_request_approve_complete_restocks_once(client, db, make_account):
    hs, hu, product, item = delivered(client, db, make_account, qty=2)
    assert stock(db, product) == 8
    r = ask(client, hu, item)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "requested" and body["refund_paisa"] == item["line_total_paisa"] and body["refund_mode"] == "simulated"
    rid = body["id"]
    assert client.patch(f"/api/seller/returns/{rid}", json={"action": "complete"}, headers=hs).status_code == 409  # not approved yet
    assert client.patch(f"/api/seller/returns/{rid}", json={"action": "approve"}, headers=hs).json()["status"] == "approved"
    assert stock(db, product) == 8
    done = client.patch(f"/api/seller/returns/{rid}", json={"action": "complete"}, headers=hs)
    assert done.json()["status"] == "completed" and stock(db, product) == 10
    assert client.patch(f"/api/seller/returns/{rid}", json={"action": "complete"}, headers=hs).status_code == 409
    assert stock(db, product) == 10  # never restocked twice
    assert db.order_items.find_one({"_id": ObjectId(item["id"])})["item_status"] == "returned"


def test_cannot_return_before_delivery_or_twice(client, db, make_account):
    _, hu, _, item = delivered(client, db, make_account, deliver=False)
    assert ask(client, hu, item).status_code == 409
    db.order_items.update_one({"_id": ObjectId(item["id"])}, {"$set": {"item_status": "delivered"}})
    assert ask(client, hu, item).status_code == 201
    assert ask(client, hu, item).status_code == 409


def test_rejection_needs_a_reason_and_is_final(client, db, make_account):
    hs, hu, _, item = delivered(client, db, make_account)
    rid = ask(client, hu, item, "changed_mind").json()["id"]
    assert client.patch(f"/api/seller/returns/{rid}", json={"action": "reject"}, headers=hs).status_code == 422
    r = client.patch(f"/api/seller/returns/{rid}", json={"action": "reject", "note": "Opened and used"}, headers=hs)
    assert r.json()["status"] == "rejected"
    assert client.patch(f"/api/seller/returns/{rid}", json={"action": "approve"}, headers=hs).status_code == 409
    mine = client.get("/api/returns/mine", headers=hu).json()["items"][0]
    assert mine["seller_note"] == "Opened and used"


def test_other_reason_needs_details_and_bad_reason_is_refused(client, db, make_account):
    _, hu, _, item = delivered(client, db, make_account)
    assert ask(client, hu, item, "other", "short").status_code == 422
    assert ask(client, hu, item, "because", "").status_code == 422
    assert ask(client, hu, item, "other", "The colour is different from the photo").status_code == 201


def test_ownership_nobody_else_can_request_view_or_decide(client, db, make_account):
    hs, hu, _, item = delivered(client, db, make_account)
    _, other_shopper = make_account(email="other@example.com")
    _, other_seller = approved_seller(make_account, db, email="seller2@example.com")
    assert ask(client, other_shopper, item).status_code == 404
    assert ask(client, hs, item).status_code == 403  # sellers cannot request
    rid = ask(client, hu, item).json()["id"]
    assert client.patch(f"/api/seller/returns/{rid}", json={"action": "approve"}, headers=other_seller).status_code == 404
    assert client.get("/api/seller/returns", headers=other_seller).json()["total"] == 0
    assert client.get("/api/returns/mine", headers=other_shopper).json()["total"] == 0
    assert client.post(f"/api/returns/{rid}/cancel", headers=other_shopper).status_code == 404
    assert client.get("/api/seller/returns", headers=hs).json()["items"][0]["shopper_email"] == "shopper@example.com"


def test_shopper_can_cancel_before_a_decision(client, db, make_account):
    hs, hu, _, item = delivered(client, db, make_account)
    rid = ask(client, hu, item).json()["id"]
    assert client.post(f"/api/returns/{rid}/cancel", headers=hu).json()["status"] == "cancelled"
    assert client.patch(f"/api/seller/returns/{rid}", json={"action": "approve"}, headers=hs).status_code == 409


def test_shopper_cannot_cancel_after_a_decision(client, db, make_account):
    hs, hu, _, item = delivered(client, db, make_account)
    rid = ask(client, hu, item).json()["id"]
    client.patch(f"/api/seller/returns/{rid}", json={"action": "approve"}, headers=hs)
    assert client.post(f"/api/returns/{rid}/cancel", headers=hu).status_code == 409


def test_admin_can_decide_and_it_is_audited(client, db, make_account, admin_headers):
    _, hu, product, item = delivered(client, db, make_account, qty=1)
    rid = ask(client, hu, item).json()["id"]
    assert client.get("/api/admin/returns", headers=admin_headers).json()["total"] == 1
    assert client.patch(f"/api/admin/returns/{rid}", json={"action": "approve"}, headers=admin_headers).json()["status"] == "approved"
    assert client.patch(f"/api/admin/returns/{rid}", json={"action": "complete"}, headers=admin_headers).json()["status"] == "completed"
    assert stock(db, product) == 10
    assert client.get("/api/admin/audit?action=return.", headers=admin_headers).json()["total"] == 2


def test_admin_return_routes_refuse_non_admins(client, db, make_account):
    hs, hu, _, item = delivered(client, db, make_account)
    rid = ask(client, hu, item).json()["id"]
    for h in (hu, hs, {}):
        assert client.get("/api/admin/returns", headers=h).status_code in (401, 403)
        assert client.patch(f"/api/admin/returns/{rid}", json={"action": "approve"}, headers=h).status_code in (401, 403)