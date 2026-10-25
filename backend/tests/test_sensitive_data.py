"""Acceptance 2 and 3: no full NID, no password hash and no secrets in any response, log line or audit entry."""
import json
import logging

from bson import ObjectId

from tests.helpers_m4 import NID, submit_verification, upload_dir  # noqa: F401

SECRET_WORDS = ("password_hash", "nid_encrypted", "nid_fingerprint", "doc_path", "$2b$")


def walk_get(client, headers, paths):
    out = []
    for p in paths:
        r = client.get(p, headers=headers)
        assert r.status_code == 200, (p, r.status_code, r.text)
        out.append((p, r.text))
    return out


def test_no_response_or_log_contains_the_raw_nid(client, db, make_account, admin_headers, upload_dir, caplog):
    caplog.set_level(logging.DEBUG)
    user, h = make_account(email="a@example.com")
    texts = [submit_verification(client, h).text]
    texts.append(client.get("/api/verification/status", headers=h).text)
    texts.append(client.get("/api/auth/me", headers=h).text)
    rec_id = None
    for p, t in walk_get(client, admin_headers, ["/api/admin/verifications", "/api/admin/users", "/api/admin/sellers",
                                                  "/api/admin/stats", "/api/admin/audit"]):
        texts.append(t)
    rec_id = client.get("/api/admin/verifications", headers=admin_headers).json()["items"][0]["id"]
    texts.append(client.patch(f"/api/admin/verifications/{rec_id}", json={"decision": "approve"},
                              headers=admin_headers).text)
    texts.append(client.get("/api/admin/audit", headers=admin_headers).text)
    for t in texts:
        assert NID not in t
        for w in SECRET_WORDS:
            assert w not in t, w
    assert NID not in caplog.text


def test_nid_is_encrypted_at_rest_and_never_in_audit_logs(client, db, make_account, admin_headers, upload_dir):
    from app.core.security import decrypt_text
    user, h = make_account(email="a@example.com")
    submit_verification(client, h)
    rec = db.verification_records.find_one({"user_id": ObjectId(user["id"])})
    assert NID not in json.dumps({k: str(v) for k, v in rec.items() if k != "nid_encrypted"})
    assert decrypt_text(rec["nid_encrypted"]) == NID  # recoverable only with the server's Fernet key
    rec_id = str(rec["_id"])
    client.get(f"/api/admin/verifications/{rec_id}/document", headers=admin_headers)
    client.patch(f"/api/admin/verifications/{rec_id}", json={"decision": "approve"}, headers=admin_headers)
    for entry in db.audit_logs.find({}):
        assert NID not in str(entry)


def test_audit_service_drops_forbidden_keys(db):
    from app.services import audit_service
    actor = {"_id": ObjectId(), "email": "x@example.com"}
    audit_service.log(db, actor, "test", "t", {"nid": NID, "password": "p", "ok": "yes", "nid_number": NID})
    e = db.audit_logs.find_one({"action": "test"})
    assert e["details"] == {"ok": "yes"}


def test_no_password_hash_in_any_admin_or_user_listing(client, make_account, admin_headers):
    make_account(email="a@example.com")
    make_account(email="s@example.com", role="seller")
    for p in ("/api/admin/users", "/api/admin/users?q=a", "/api/admin/sellers", "/api/admin/complaints"):
        t = client.get(p, headers=admin_headers).text
        assert "password" not in t.lower()


def test_private_upload_folder_is_not_inside_a_static_mount():
    from app.main import app
    mounts = [r for r in app.routes if r.__class__.__name__ == "Mount"]
    assert mounts == [], "No static file mounts are allowed; documents are served only by the audited admin route."
    from app.core.config import get_settings
    assert "static" not in get_settings().private_upload_dir.lower()


def test_gitignore_keeps_uploads_out_of_git():
    from pathlib import Path
    for candidate in (Path("../.gitignore"), Path(".gitignore")):
        if candidate.exists():
            assert "private_uploads" in candidate.read_text()
            return
    # not found when run outside the repo layout: nothing to assert