"""Complaints: filing rules, ownership of the target, admin management."""
from bson import ObjectId

from tests.helpers_m2 import approved_seller, create_product


def make_order(client, db, make_account):
    """A real order created through the public API: seller + product + shopper + checkout."""
    seller, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    shopper, hu = make_account(email="shopper@example.com")
    assert client.post("/api/cart/items", json={"seller_product_id": product["id"], "quantity": 1},
                       headers=hu).status_code in (200, 201)
    r = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"}, headers=hu)
    assert r.status_code == 201, r.text
    return seller, hs, shopper, hu, r.json()["id"]


def test_shopper_files_complaint_about_own_order(client, db, make_account):
    _, _, _, hu, order_id = make_order(client, db, make_account)
    r = client.post("/api/complaints", json={"target_type": "order", "target_id": order_id,
                                             "description": "The item never arrived."}, headers=hu)
    assert r.status_code == 201 and r.json()["status"] == "open"
    assert client.get("/api/complaints", headers=hu).json()["total"] == 1


def test_seller_can_complain_about_an_order_containing_their_item(client, db, make_account):
    _, hs, _, _, order_id = make_order(client, db, make_account)
    r = client.post("/api/complaints", json={"target_type": "order", "target_id": order_id,
                                             "description": "Buyer is not answering messages."}, headers=hs)
    assert r.status_code == 201


def test_cannot_complain_about_someone_elses_order(client, db, make_account):
    _, _, _, _, order_id = make_order(client, db, make_account)
    _, other = make_account(email="other@example.com")
    r = client.post("/api/complaints", json={"target_type": "order", "target_id": order_id,
                                             "description": "This is not my order at all."}, headers=other)
    assert r.status_code == 404


def test_seller_target_and_self_complaint(client, db, make_account):
    seller, hs = approved_seller(make_account, db)
    _, hu = make_account(email="u@example.com")
    ok = client.post("/api/complaints", json={"target_type": "seller", "target_id": seller["id"],
                                              "description": "Seller sent the wrong size."}, headers=hu)
    assert ok.status_code == 201
    me = client.post("/api/complaints", json={"target_type": "seller", "target_id": seller["id"],
                                              "description": "Complaining about myself."}, headers=hs)
    assert me.status_code == 400
    ghost = client.post("/api/complaints", json={"target_type": "seller", "target_id": str(ObjectId()),
                                                 "description": "A seller that does not exist."}, headers=hu)
    assert ghost.status_code == 404


def test_rental_target_requires_participation(client, db, make_account):
    owner, ho = make_account(email="owner@example.com")
    renter, hr = make_account(email="renter@example.com")
    stranger, hx = make_account(email="stranger@example.com")
    db.users.update_many({"_id": {"$in": [ObjectId(owner["id"]), ObjectId(renter["id"])]}},
                         {"$set": {"verification_status": "approved"}})
    listing = client.post("/api/rentals/listings", json={"title": "Tent", "daily_rate_paisa": 50000,
                                                         "location": "Dhaka"}, headers=ho).json()
    req = client.post("/api/rentals/requests", json={"listing_id": listing["id"], "start_date": "2026-12-01",
                                                     "end_date": "2026-12-03"}, headers=hr).json()
    body = {"target_type": "rental", "target_id": req["id"], "description": "Item was damaged on return."}
    assert client.post("/api/complaints", json=body, headers=hr).status_code == 201
    assert client.post("/api/complaints", json=body, headers=ho).status_code == 201
    assert client.post("/api/complaints", json=body, headers=hx).status_code == 404


def test_validation_and_duplicates(client, db, make_account):
    seller, _ = approved_seller(make_account, db)
    _, hu = make_account(email="u@example.com")
    base = {"target_type": "seller", "target_id": seller["id"]}
    assert client.post("/api/complaints", json={**base, "description": "short"}, headers=hu).status_code == 422
    assert client.post("/api/complaints", json={**base, "target_type": "product", "description": "x" * 20},
                       headers=hu).status_code == 422
    assert client.post("/api/complaints", json={**base, "description": "x" * 2001}, headers=hu).status_code == 422
    assert client.post("/api/complaints", json={**base, "description": "Wrong item delivered."}, headers=hu
                       ).status_code == 201
    dup = client.post("/api/complaints", json={**base, "description": "Wrong item delivered again."}, headers=hu)
    assert dup.status_code == 409 and dup.json()["error"]["code"] == "DUPLICATE_COMPLAINT"


def test_users_only_see_their_own_complaints(client, db, make_account):
    seller, _ = approved_seller(make_account, db)
    _, h1 = make_account(email="u1@example.com")
    _, h2 = make_account(email="u2@example.com")
    client.post("/api/complaints", json={"target_type": "seller", "target_id": seller["id"],
                                         "description": "Late delivery of my parcel."}, headers=h1)
    assert client.get("/api/complaints", headers=h1).json()["total"] == 1
    assert client.get("/api/complaints", headers=h2).json()["total"] == 0


def test_admin_manages_complaints_and_it_is_audited(client, db, make_account, admin_headers):
    seller, _ = approved_seller(make_account, db)
    _, hu = make_account(email="u@example.com")
    cid = client.post("/api/complaints", json={"target_type": "seller", "target_id": seller["id"],
                                               "description": "Rude replies to my messages."}, headers=hu).json()["id"]
    listing = client.get("/api/admin/complaints?status=open", headers=admin_headers).json()
    assert listing["total"] == 1 and listing["items"][0]["filer_email"] == "u@example.com"
    r = client.patch(f"/api/admin/complaints/{cid}", json={"status": "in_review", "admin_note": "Looking into it."},
                     headers=admin_headers)
    assert r.status_code == 200 and r.json()["status"] == "in_review"
    mine = client.get("/api/complaints", headers=hu).json()["items"][0]
    assert mine["status"] == "in_review" and mine["admin_note"] == "Looking into it."
    assert db.audit_logs.count_documents({"action": "complaint.update"}) == 1
    assert client.patch(f"/api/admin/complaints/{cid}", json={}, headers=admin_headers).status_code == 422
    assert client.patch(f"/api/admin/complaints/{cid}", json={"status": "bogus"}, headers=admin_headers
                        ).status_code == 422
    assert client.patch(f"/api/admin/complaints/{ObjectId()}", json={"status": "resolved"},
                        headers=admin_headers).status_code == 404