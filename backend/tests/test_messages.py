"""Tests for Unified Messaging."""
from tests.helpers_m2 import approved_seller


def test_stage5_messaging_flow_and_isolation(client, db, make_account):
    user1, h1 = make_account(email="buyer_msg@test.com", role="user")
    user2, h2 = approved_seller(make_account, db, email="seller_msg@test.com")
    user3, h3 = make_account(email="stranger@test.com", role="user")

    # User 1 sends message to User 2
    res = client.post("/api/messages", json={
        "recipient_id": user2["id"],
        "body": "Is this available?",
        "product_id": "prod_123"
    }, headers=h1)

    assert res.status_code == 201
    msg = res.json()
    assert msg["body"] == "Is this available?"
    thread_id = msg["thread_id"]

    # User 2 reads threads and sees unread
    threads = client.get("/api/messages/threads", headers=h2).json()
    assert len(threads) == 1
    assert threads[0]["unread_count"] == 1

    # User 2 opens thread (marks read)
    msgs = client.get(f"/api/messages/threads/{thread_id}", headers=h2).json()
    assert len(msgs) == 1

    # User 2 threads now show 0 unread
    threads_after = client.get("/api/messages/threads", headers=h2).json()
    assert threads_after[0]["unread_count"] == 0

    # User 3 attempts to read thread (Isolation Check)
    bad_req = client.get(f"/api/messages/threads/{thread_id}", headers=h3)
    assert bad_req.status_code == 403