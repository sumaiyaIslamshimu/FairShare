from fastapi import Depends

from app.core.deps import require_approved_seller, require_role
from app.main import app


# Test-only routes to exercise the role dependencies.
@app.get("/api/_t/admin-only")
def _admin_only(user=Depends(require_role("admin"))):
    return {"ok": True}


@app.get("/api/_t/seller-approved")
def _seller_approved(user=Depends(require_approved_seller)):
    return {"ok": True}


def test_register_user_hides_password_hash(client):
    r = client.post("/api/auth/register", json={
        "full_name": "Ana", "email": "Ana@Example.com", "phone": "+8801700000000", "password": "Password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "user" and body["email"] == "ana@example.com"
    assert "password" not in str(body).lower().replace("verification", "")


def test_password_is_stored_hashed(client, db):
    client.post("/api/auth/register", json={
        "full_name": "Ana", "email": "ana@example.com", "phone": "+8801700000000", "password": "Password123"})
    stored = db.users.find_one({"email": "ana@example.com"})
    assert stored["password_hash"] != "Password123" and stored["password_hash"].startswith("$2")


def test_duplicate_email_returns_409(client, make_account):
    make_account(email="dup@example.com")
    r = client.post("/api/auth/register", json={
        "full_name": "Other", "email": "dup@example.com", "phone": "+8801700000000", "password": "Password123"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "EMAIL_EXISTS"


def test_cannot_self_register_as_admin(client):
    r = client.post("/api/auth/register", json={
        "full_name": "Eve", "email": "eve@example.com", "phone": "+8801700000000",
        "password": "Password123", "role": "admin"})
    assert r.status_code == 422


def test_short_password_and_bad_phone_rejected(client):
    base = {"full_name": "Ana", "email": "a@example.com"}
    assert client.post("/api/auth/register", json={**base, "phone": "+8801700000000", "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={**base, "phone": "abc", "password": "Password123"}).status_code == 422


def test_seller_requires_business_name_and_starts_pending(client, db):
    r = client.post("/api/auth/register", json={
        "full_name": "Sam", "email": "sam@example.com", "phone": "+8801700000000",
        "password": "Password123", "role": "seller"})
    assert r.status_code == 422
    r = client.post("/api/auth/register", json={
        "full_name": "Sam", "email": "sam@example.com", "phone": "+8801700000000",
        "password": "Password123", "role": "seller", "business_name": "Sam's Shop"})
    assert r.status_code == 201 and r.json()["seller_status"] == "pending"
    assert db.seller_profiles.count_documents({}) == 1


def test_login_success_and_wrong_password(client, make_account):
    make_account(email="login@example.com")
    bad = client.post("/api/auth/login", json={"email": "login@example.com", "password": "WrongPass1"})
    assert bad.status_code == 401 and bad.json()["error"]["code"] == "INVALID_CREDENTIALS"
    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "WrongPass1"})
    assert unknown.json()["error"]["message"] == bad.json()["error"]["message"]


def test_me_requires_valid_token(client, make_account):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    user, headers = make_account(email="me@example.com")
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200 and r.json()["email"] == "me@example.com"


def test_role_guard_blocks_non_admin(client, make_account, admin_headers):
    _, user_h = make_account(email="u@example.com")
    _, seller_h = make_account(email="s@example.com", role="seller")
    assert client.get("/api/_t/admin-only").status_code == 401
    assert client.get("/api/_t/admin-only", headers=user_h).status_code == 403
    assert client.get("/api/_t/admin-only", headers=seller_h).status_code == 403
    assert client.get("/api/_t/admin-only", headers=admin_headers).status_code == 200


def test_unapproved_seller_is_blocked_until_approved(client, make_account, db):
    seller, headers = make_account(email="s2@example.com", role="seller")
    r = client.get("/api/_t/seller-approved", headers=headers)
    assert r.status_code == 403 and r.json()["error"]["code"] == "SELLER_NOT_APPROVED"
    db.seller_profiles.update_one({}, {"$set": {"status": "approved"}})
    assert client.get("/api/_t/seller-approved", headers=headers).status_code == 200


def test_shopper_cannot_use_seller_guard(client, make_account):
    _, headers = make_account(email="shopper@example.com")
    assert client.get("/api/_t/seller-approved", headers=headers).status_code == 403


def test_disabled_account_cannot_use_old_token(client, make_account, db):
    _, headers = make_account(email="off@example.com")
    db.users.update_one({"email": "off@example.com"}, {"$set": {"is_active": False}})
    assert client.get("/api/auth/me", headers=headers).status_code == 403
    r = client.post("/api/auth/login", json={"email": "off@example.com", "password": "Password123"})
    assert r.status_code == 403