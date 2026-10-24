"""Acceptance 1: every admin route rejects anonymous, shopper and seller callers.

The routes are discovered from the app itself, so a route added later is covered automatically.
"""
import re

import pytest
from bson import ObjectId

from app.main import app

ID = str(ObjectId())


def admin_routes():
    """Reads the public OpenAPI schema, which lists every route however routers were included."""
    found = []
    for path, methods in app.openapi()["paths"].items():
        if path.startswith("/api/admin"):
            for method in methods:
                found.append((method.upper(), re.sub(r"\{[^}]+\}", ID, path)))
    return sorted(found)


ROUTES = admin_routes()


def test_admin_routes_were_discovered():
    assert len(ROUTES) >= 20
    assert ("GET", "/api/admin/stats") in ROUTES


def call(client, method, path, headers=None):
    # An empty JSON body is enough: authorization is checked BEFORE the body, so 401/403 must win.
    return client.request(method, path, headers=headers or {}, json={})


@pytest.mark.parametrize("method,path", ROUTES)
def test_anonymous_gets_401(client, method, path):
    r = call(client, method, path)
    assert r.status_code == 401, (method, path, r.status_code)


@pytest.mark.parametrize("method,path", ROUTES)
def test_shopper_gets_403(client, make_account, method, path):
    _, h = make_account(email="shopper@example.com", role="user")
    assert call(client, method, path, h).status_code == 403, (method, path)


@pytest.mark.parametrize("method,path", ROUTES)
def test_seller_gets_403(client, make_account, method, path):
    _, h = make_account(email="seller@example.com", role="seller")
    assert call(client, method, path, h).status_code == 403, (method, path)


def test_a_token_for_a_suspended_admin_stops_working(client, db, admin_headers):
    assert client.get("/api/admin/stats", headers=admin_headers).status_code == 200
    db.users.update_one({"role": "admin"}, {"$set": {"is_active": False}})
    assert client.get("/api/admin/stats", headers=admin_headers).status_code == 403


def test_role_in_token_is_not_trusted(client, db, make_account):
    """Demoting an admin in the database takes effect at once, even though the old token says 'admin'."""
    from app.db.seed import seed_admin
    seed_admin(db, "boss@example.com", "AdminPass123")
    token = client.post("/api/auth/login", json={"email": "boss@example.com", "password": "AdminPass123"}
                        ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/admin/stats", headers=h).status_code == 200
    db.users.update_one({"email": "boss@example.com"}, {"$set": {"role": "user"}})
    assert client.get("/api/admin/stats", headers=h).status_code == 403


def test_verification_and_complaint_routes_reject_admin_and_anonymous(client, admin_headers):
    assert client.get("/api/complaints").status_code == 401
    assert client.get("/api/complaints", headers=admin_headers).status_code == 403
    assert client.get("/api/verification/status", headers=admin_headers).status_code == 403