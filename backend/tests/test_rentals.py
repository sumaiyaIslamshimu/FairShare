"""Tests for the Rentals module (Listings, Requests, 409 Overlaps, Verification)."""
from bson import ObjectId


def test_stage6_unverified_users_cannot_rent(client, db, make_account):
    user, h_user = make_account(email="unverified@test.com", role="user")

    # Attempt to list an item
    res1 = client.post("/api/rentals/listings", json={
        "title": "Camera", "daily_rate_paisa": 1000, "location": "Dhaka"
    }, headers=h_user)
    assert res1.status_code == 403
    assert res1.json()["error"]["code"] == "UNVERIFIED_USER"

    # Attempt to request an item
    res2 = client.post("/api/rentals/requests", json={
        "listing_id": str(ObjectId()), "start_date": "2026-11-01", "end_date": "2026-11-05"
    }, headers=h_user)
    assert res2.status_code == 403


def test_stage6_rental_overlap_prevention(client, db, make_account):
    owner, h_owner = make_account(email="owner@test.com", role="user")
    renter, h_renter = make_account(email="renter@test.com", role="user")

    # Force verification for tests
    db.users.update_many({"_id": {"$in": [ObjectId(owner["id"]), ObjectId(renter["id"])]}},
                         {"$set": {"verification_status": "approved"}})

    # Create listing
    res = client.post("/api/rentals/listings", json={
        "title": "Tent", "daily_rate_paisa": 50000, "location": "Dhaka"
    }, headers=h_owner)
    assert res.status_code == 201
    listing_id = res.json()["id"]

    # Renter requests Nov 10 to Nov 15
    req_res = client.post("/api/rentals/requests", json={
        "listing_id": listing_id, "start_date": "2026-11-10", "end_date": "2026-11-15"
    }, headers=h_renter)
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # Owner accepts (creates Booking)
    client.post(f"/api/rentals/requests/{req_id}/decision", json={"action": "accept"}, headers=h_owner)

    # Renter 2 attempts overlapping dates (Nov 12 to Nov 18) -> 409 Conflict
    renter2, h_r2 = make_account(email="renter2@test.com", role="user")
    db.users.update_one({"_id": ObjectId(renter2["id"])}, {"$set": {"verification_status": "approved"}})

    overlap_res = client.post("/api/rentals/requests", json={
        "listing_id": listing_id, "start_date": "2026-11-12", "end_date": "2026-11-18"
    }, headers=h_r2)
    assert overlap_res.status_code == 409
    assert overlap_res.json()["error"]["code"] == "DATE_OVERLAP"

    # ---- rental history (events) ----
    def _verified(db, *accounts):
        db.users.update_many({"_id": {"$in": [ObjectId(a["id"]) for a in accounts]}},
                             {"$set": {"verification_status": "approved"}})

    def _listing_and_request(client, db, make_account, start="2026-12-01", end="2026-12-03"):
        owner, h_owner = make_account(email="owner@test.com", role="user")
        renter, h_renter = make_account(email="renter@test.com", role="user")
        _verified(db, owner, renter)
        listing_id = client.post("/api/rentals/listings", json={
            "title": "Tent", "daily_rate_paisa": 50000, "location": "Dhaka"}, headers=h_owner).json()["id"]
        req_id = client.post("/api/rentals/requests", json={
            "listing_id": listing_id, "start_date": start, "end_date": end}, headers=h_renter).json()["id"]
        return h_owner, h_renter, listing_id, req_id

    def test_request_history_records_create_then_accept_then_booking_in_order(client, db, make_account):
        h_owner, h_renter, _, req_id = _listing_and_request(client, db, make_account)
        assert client.post(f"/api/rentals/requests/{req_id}/decision", json={"action": "accept"},
                           headers=h_owner).status_code == 200

        for h in (h_owner, h_renter):  # both sides see the same history
            res = client.get(f"/api/rentals/requests/{req_id}/events", headers=h)
            assert res.status_code == 200
            events = [e["event"] for e in res.json()]
            assert events == ["request_created", "request_accepted", "booking_created"]

    def test_request_history_records_cancellation(client, db, make_account):
        h_owner, h_renter, _, req_id = _listing_and_request(client, db, make_account)
        assert client.post(f"/api/rentals/requests/{req_id}/cancel", headers=h_renter).status_code == 200
        events = [e["event"] for e in client.get(f"/api/rentals/requests/{req_id}/events", headers=h_renter).json()]
        assert events == ["request_created", "request_cancelled"]

    def test_request_history_records_rejection(client, db, make_account):
        h_owner, h_renter, _, req_id = _listing_and_request(client, db, make_account)
        assert client.post(f"/api/rentals/requests/{req_id}/decision", json={"action": "reject"},
                           headers=h_owner).status_code == 200
        events = [e["event"] for e in client.get(f"/api/rentals/requests/{req_id}/events", headers=h_owner).json()]
        assert events == ["request_created", "request_rejected"]

    def test_request_history_is_private_to_owner_and_renter(client, db, make_account):
        _, _, _, req_id = _listing_and_request(client, db, make_account)
        stranger, h_stranger = make_account(email="stranger@test.com", role="user")
        _verified(db, stranger)
        assert client.get(f"/api/rentals/requests/{req_id}/events", headers=h_stranger).status_code == 404
        assert client.get(f"/api/rentals/requests/{req_id}/events").status_code in (401, 403)
        assert client.get(f"/api/rentals/requests/{ObjectId()}/events", headers=h_stranger).status_code == 404

    def test_events_name_the_actor_and_listing(client, db, make_account):
        h_owner, h_renter, listing_id, req_id = _listing_and_request(client, db, make_account)
        events = client.get(f"/api/rentals/requests/{req_id}/events", headers=h_renter).json()
        renter_id = db.users.find_one({"email": "renter@test.com"})["_id"]
        assert events[0]["actor_id"] == str(renter_id)
        assert events[0]["listing_id"] == listing_id and events[0]["request_id"] == req_id