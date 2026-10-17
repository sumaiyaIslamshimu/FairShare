"""Test setup: fake env vars + in-memory MongoDB (mongomock). No real database needed."""
import os

from cryptography.fernet import Fernet

# Must be set BEFORE the app is imported.
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["DB_NAME"] = "fairshare_test"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-use-0123456789"
os.environ["FERNET_KEY"] = Fernet.generate_key().decode()

import mongomock  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import mongo  # noqa: E402
from app.db.seed import seed_admin, seed_categories  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def db():
    database = mongomock.MongoClient()["fairshare_test"]
    mongo.set_db(database)
    seed_categories(database)
    return database


@pytest.fixture()
def client(db):
    with TestClient(app) as c:
        yield c


def register_and_login(client, email="user@example.com", role="user", password="Password123", **extra):
    body = {"full_name": "Test Person", "email": email, "phone": "+8801700000000",
            "password": password, "role": role, **extra}
    if role == "seller":
        body.setdefault("business_name", "Test Store")
    r = client.post("/api/auth/register", json=body)
    assert r.status_code == 201, r.text
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    return data["user"], {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture()
def make_account(client):
    return lambda **kw: register_and_login(client, **kw)


@pytest.fixture()
def admin_headers(client, db):
    seed_admin(db, "admin@example.com", "AdminPass123")
    r = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "AdminPass123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}