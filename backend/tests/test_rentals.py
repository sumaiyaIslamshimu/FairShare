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