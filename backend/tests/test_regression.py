"""Acceptance 6: the full journey across all four modules, using only the public API.

register -> identity verification -> seller approved -> product -> scraped comparison fixture -> cart -> checkout
-> order status -> rental request -> booking -> complaint -> admin moderation -> audit trail.
"""
from tests.helpers_m2 import make_ext, save_ext
from tests.helpers_m4 import NID, submit_verification, upload_dir  # noqa: F401

PRODUCT = {
    "title": "Pran Miniket Rice 5 kg", "description": "Good rice", "brand": "Pran",
    "category_slug": "groceries-food", "subcategory_slug": "rice-pulses-grains",
    "price_paisa": 70000, "stock_qty": 10, "images": ["https://img.test/rice.jpg"],
}


def verify_via_ui_flow(client, headers, admin_headers, nid):
    """What a person and an admin really do: submit, then the admin approves."""
    assert submit_verification(client, headers, nid=nid).status_code == 201
    rec = next(r for r in client.get("/api/admin/verifications?status=pending", headers=admin_headers).json()["items"]
               if r["nid_masked"].endswith(nid[-4:]))
    r = client.patch(f"/api/admin/verifications/{rec['id']}", json={"decision": "approve"}, headers=admin_headers)
    assert r.status_code == 200, r.text


def test_full_platform_journey(client, db, make_account, admin_headers, upload_dir):
    # 1. accounts
    seller, hs = make_account(email="seller@example.com", role="seller")
    shopper, hu = make_account(email="shopper@example.com")
    owner, ho = make_account(email="owner@example.com")
    assert client.post("/api/seller/products", json=PRODUCT, headers=hs).status_code == 403  # not approved yet

    # 2. verification -> seller approved (seller approval flows from identity approval)
    verify_via_ui_flow(client, hs, admin_headers, "1111111111")
    me = client.get("/api/auth/me", headers=hs).json()
    assert me["verification_status"] == "approved" and me["seller_status"] == "approved"

    # 3. seller publishes a product; a scraped store offer exists for comparison
    p = client.post("/api/seller/products", json=PRODUCT, headers=hs)
    assert p.status_code == 201, p.text
    product_id = p.json()["id"]
    ext = make_ext(store="daraz", name="Pran Miniket Rice 5 kg", price="৳ 760", brand="Pran")
    save_ext(db, ext)

    # 4. comparison shows BOTH, and only the FairShare one is buyable
    found = client.get("/api/compare/search?q=rice").json()["items"]
    sources = {i["source"] for i in found}
    assert sources == {"external", "fairshare"}
    assert all(i["store_url"] for i in found if i["source"] == "external")
    external_id = next(i["id"] for i in found if i["source"] == "external")
    bad = client.post("/api/cart/items", json={"seller_product_id": external_id, "quantity": 1}, headers=hu)
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "NOT_A_FAIRSHARE_PRODUCT"

    # 5. cart + simulated checkout; stock drops; the order is visible to both sides
    assert client.post("/api/cart/items", json={"seller_product_id": product_id, "quantity": 2}, headers=hu
                       ).status_code in (200, 201)
    order = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"},
                        headers=hu)
    assert order.status_code == 201, order.text
    order = order.json()
    assert order["payment"]["mode"] == "simulated" and order["total_paisa"] == 140000
    item = client.get("/api/seller/orders", headers=hs).json()["items"][0]
    shipped = client.patch(f"/api/seller/orders/{item['id']}/status", json={"status": "shipped"}, headers=hs)
    assert shipped.status_code == 200 and shipped.json()["item_status"] == "shipped"

    # 6. rentals: both people verify through the real flow, then request -> accept -> booking
    renter_nid = "2222222222"
    verify_via_ui_flow(client, ho, admin_headers, "3333333333")
    verify_via_ui_flow(client, hu, admin_headers, renter_nid)
    listing = client.post("/api/rentals/listings", json={"title": "Camping Tent", "daily_rate_paisa": 50000,
                                                         "location": "Dhaka"}, headers=ho)
    assert listing.status_code == 201, listing.text
    lid = listing.json()["id"]
    assert client.get("/api/rentals/listings").json()["total"] == 1
    # rentals never leak into shopping
    assert "Tent" not in client.get("/api/compare/search?q=tent").text
    req = client.post("/api/rentals/requests", json={"listing_id": lid, "start_date": "2026-12-01",
                                                     "end_date": "2026-12-03"}, headers=hu)
    assert req.status_code == 201, req.text
    rid = req.json()["id"]
    acc = client.post(f"/api/rentals/requests/{rid}/decision", json={"action": "accept"}, headers=ho)
    assert acc.status_code == 200 and acc.json()["status"] == "accepted"
    assert len(client.get("/api/rentals/bookings", headers=hu).json()) == 1
    overlap = client.post("/api/rentals/requests", json={"listing_id": lid, "start_date": "2026-12-02",
                                                         "end_date": "2026-12-04"}, headers=hu)
    assert overlap.status_code == 409

    # 7. complaint about the rental, handled by an admin
    c = client.post("/api/complaints", json={"target_type": "rental", "target_id": rid,
                                             "description": "Tent was returned dirty."}, headers=ho)
    assert c.status_code == 201
    upd = client.patch(f"/api/admin/complaints/{c.json()['id']}", json={"status": "resolved", "admin_note": "Fixed."},
                       headers=admin_headers)
    assert upd.status_code == 200

    # 8. admin moderation: hide the product, remove the rental
    assert client.patch(f"/api/admin/products/{product_id}", json={"moderation_status": "hidden"},
                        headers=admin_headers).status_code == 200
    assert {i["source"] for i in client.get("/api/compare/search?q=rice").json()["items"]} == {"external"}
    assert client.patch(f"/api/admin/rentals/{lid}", json={"status": "removed"}, headers=admin_headers
                        ).status_code == 200
    assert client.get("/api/rentals/listings").json()["total"] == 0

    # 9. suspend a user: the token stops working at once
    assert client.patch(f"/api/admin/users/{owner['id']}", json={"is_active": False}, headers=admin_headers
                        ).status_code == 200
    assert client.get("/api/auth/me", headers=ho).status_code == 403

    # 10. everything the admin did is in the audit log, and no NID is
    audit = client.get("/api/admin/audit?page_size=100", headers=admin_headers).json()
    actions = {e["action"] for e in audit["items"]}
    assert {"verification.approved", "seller.approved", "complaint.update", "product.hidden", "rental.removed",
            "user.suspend"} <= actions
    for n in ("1111111111", "2222222222", "3333333333"):
        assert n not in str(audit)

    # 11. final numbers are consistent
    st = client.get("/api/admin/stats", headers=admin_headers).json()
    assert st["orders"]["total"] == 1 and st["rentals"]["bookings"] == 1 and st["verifications"]["approved"] == 3
    assert st["users"]["suspended"] == 1 and st["complaints"]["total"] == 1


def test_orders_survive_a_removed_product(client, db, make_account, admin_headers):
    """Soft delete keeps order history readable."""
    from tests.helpers_m2 import approved_seller, create_product
    seller, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    _, hu = make_account(email="u@example.com")
    client.post("/api/cart/items", json={"seller_product_id": product["id"], "quantity": 1}, headers=hu)
    order = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"},
                        headers=hu).json()
    client.patch(f"/api/admin/products/{product['id']}", json={"moderation_status": "removed"}, headers=admin_headers)
    mine = client.get("/api/orders", headers=hu).json()
    assert mine["total"] == 1 and mine["items"][0]["id"] == order["id"]