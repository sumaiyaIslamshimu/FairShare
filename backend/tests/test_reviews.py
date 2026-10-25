"""Reviews: only delivered items, one per item, hidden reviews vanish, ownership, admin moderation."""
from bson import ObjectId

from tests.helpers_m2 import approved_seller, create_product


def delivered_order(client, db, make_account, deliver=True):
    seller, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    shopper, hu = make_account(email="shopper@example.com")
    client.post("/api/cart/items", json={"seller_product_id": product["id"], "quantity": 1}, headers=hu)
    order = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"}, headers=hu).json()
    item = order["items"][0]
    if deliver:
        db.order_items.update_one({"_id": ObjectId(item["id"])}, {"$set": {"item_status": "delivered"}})
    return seller, hs, shopper, hu, product, item["id"]


def review(client, hu, item_id, rating=5, comment="Great rice"):
    return client.post("/api/reviews", json={"order_item_id": item_id, "rating": rating, "comment": comment}, headers=hu)


def test_review_after_delivery_works_and_shows_publicly_with_average(client, db, make_account):
    _, _, _, hu, product, item_id = delivered_order(client, db, make_account)
    r = review(client, hu, item_id, 4)
    assert r.status_code == 201 and r.json()["status"] == "visible"
    pub = client.get(f"/api/seller-products/{product['id']}/reviews").json()
    assert pub["count"] == 1 and pub["average"] == 4.0
    assert pub["items"][0]["reviewer_name"] == "Test"  # first name only
    assert "email" not in str(pub) and "user_id" not in str(pub)


def test_cannot_review_before_delivery(client, db, make_account):
    _, _, _, hu, _, item_id = delivered_order(client, db, make_account, deliver=False)
    assert review(client, hu, item_id).status_code == 409


def test_one_review_per_item_but_it_can_be_edited_and_deleted(client, db, make_account):
    _, _, _, hu, product, item_id = delivered_order(client, db, make_account)
    first = review(client, hu, item_id, 5).json()
    assert review(client, hu, item_id, 1).status_code == 409
    up = client.put(f"/api/reviews/{first['id']}", json={"rating": 2, "comment": "Changed my mind"}, headers=hu)
    assert up.status_code == 200 and up.json()["rating"] == 2
    assert client.get(f"/api/seller-products/{product['id']}/reviews").json()["average"] == 2.0
    assert client.delete(f"/api/reviews/{first['id']}", headers=hu).status_code == 204
    assert client.get(f"/api/seller-products/{product['id']}/reviews").json()["count"] == 0


def test_cannot_review_someone_elses_purchase_or_edit_their_review(client, db, make_account):
    _, _, _, hu, _, item_id = delivered_order(client, db, make_account)
    _, other = make_account(email="other@example.com")
    assert review(client, other, item_id).status_code == 404
    mine = review(client, hu, item_id).json()
    assert client.put(f"/api/reviews/{mine['id']}", json={"rating": 1, "comment": ""}, headers=other).status_code == 404
    assert client.delete(f"/api/reviews/{mine['id']}", headers=other).status_code == 404


def test_rating_must_be_1_to_5_and_sellers_cannot_write_reviews(client, db, make_account):
    _, hs, _, hu, _, item_id = delivered_order(client, db, make_account)
    for bad in (0, 6):
        assert client.post("/api/reviews", json={"order_item_id": item_id, "rating": bad}, headers=hu).status_code == 422
    assert review(client, hs, item_id).status_code == 403
    assert client.post("/api/reviews", json={"order_item_id": item_id, "rating": 5}).status_code == 401


def test_admin_can_hide_a_review_and_it_leaves_the_average(client, db, make_account, admin_headers):
    _, hs, _, hu, product, item_id = delivered_order(client, db, make_account)
    rid = review(client, hu, item_id, 1, "Rude comment").json()["id"]
    assert client.get("/api/seller/reviews", headers=hs).json()["total"] == 1
    r = client.patch(f"/api/admin/reviews/{rid}", json={"status": "hidden"}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["reviewer_email"] == "shopper@example.com"
    pub = client.get(f"/api/seller-products/{product['id']}/reviews").json()
    assert pub["count"] == 0 and pub["average"] is None
    assert client.get("/api/seller/reviews", headers=hs).json()["total"] == 0
    assert client.get("/api/reviews/mine", headers=hu).json()["items"][0]["status"] == "hidden"
    logs = client.get("/api/admin/audit?action=review.", headers=admin_headers).json()
    assert logs["total"] == 1


def test_admin_review_routes_refuse_non_admins(client, db, make_account):
    _, hs, _, hu, _, item_id = delivered_order(client, db, make_account)
    rid = review(client, hu, item_id).json()["id"]
    for h in (hu, hs, {}):
        assert client.get("/api/admin/reviews", headers=h).status_code in (401, 403)
        assert client.patch(f"/api/admin/reviews/{rid}", json={"status": "hidden"}, headers=h).status_code in (401, 403)