"""Shared helpers for Member 4's tests (kept out of M1's conftest.py)."""
import io

import pytest
from bson import ObjectId

from app.core.config import get_settings

PDF = b"%PDF-1.4\n%fake test document\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
NID = "1234567890123"  # 13 digits (test value, not a real person)


@pytest.fixture()
def upload_dir(tmp_path, monkeypatch):
    """Every test writes documents to its own temp folder, never to the real private_uploads/."""
    path = tmp_path / "private_uploads"
    monkeypatch.setattr(get_settings(), "private_upload_dir", str(path))
    return path


def submit_verification(client, headers, nid=NID, content=PDF, filename="id.pdf", ctype="application/pdf"):
    return client.post("/api/verification/submit", data={"nid_number": nid},
                       files={"document": (filename, io.BytesIO(content), ctype)}, headers=headers)


def admin_user(db):
    return db.users.find_one({"role": "admin"})


def approve_seller(db, user_id: str):
    db.seller_profiles.update_one({"user_id": ObjectId(user_id)}, {"$set": {"status": "approved"}})
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"verification_status": "approved"}})