"""Verification: submission, validation, masking, access control, audit."""
from bson import ObjectId

from tests.helpers_m4 import JPG, NID, PDF, PNG, submit_verification, upload_dir  # noqa: F401


def test_submit_creates_pending_record_and_returns_status_only(client, db, make_account, upload_dir):
    user, h = make_account(email="a@example.com")
    r = submit_verification(client, h)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "pending" and body["manual_review"] is True
    assert NID not in r.text and "nid" not in body
    assert db.users.find_one({"_id": ObjectId(user["id"])})["verification_status"] == "pending"
    rec = db.verification_records.find_one({"user_id": ObjectId(user["id"])})
    assert rec["nid_encrypted"] != NID and rec["nid_last4"] == NID[-4:]
    assert len(list(upload_dir.iterdir())) == 1


def test_status_endpoint_shows_status_only(client, make_account, upload_dir):
    _, h = make_account(email="a@example.com")
    assert client.get("/api/verification/status", headers=h).json()["status"] == "none"
    submit_verification(client, h)
    s = client.get("/api/verification/status", headers=h)
    assert s.json()["status"] == "pending"
    assert NID not in s.text


def test_requires_login_and_role(client, admin_headers, upload_dir):
    assert submit_verification(client, {}).status_code == 401
    assert client.get("/api/verification/status").status_code == 401
    assert submit_verification(client, admin_headers).status_code == 403  # admins are not verified here


def test_rejects_bad_nid(client, make_account, upload_dir):
    _, h = make_account(email="a@example.com")
    for bad in ["123", "abcdefghij", "12345678901234567890", ""]:
        r = submit_verification(client, h, nid=bad)
        assert r.status_code in (422,), (bad, r.status_code)
    assert not list(upload_dir.iterdir()) if upload_dir.exists() else True


def test_rejects_wrong_type_even_with_pdf_name(client, make_account, upload_dir):
    _, h = make_account(email="a@example.com")
    r = submit_verification(client, h, content=b"<html>not a pdf</html>", filename="id.pdf", ctype="application/pdf")
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_DOCUMENT"
    assert not upload_dir.exists() or not list(upload_dir.iterdir())  # nothing saved


def test_rejects_large_and_empty_files(client, make_account, upload_dir):
    _, h = make_account(email="a@example.com")
    big = PDF + b"0" * (5 * 1024 * 1024)
    r = submit_verification(client, h, content=big)
    assert r.status_code == 413 and r.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert submit_verification(client, h, content=b"").status_code == 422


def test_accepts_png_and_jpg(client, make_account, upload_dir):
    for i, (content, name) in enumerate([(PNG, "id.png"), (JPG, "id.jpg")]):
        _, h = make_account(email=f"p{i}@example.com")
        assert submit_verification(client, h, nid=f"123456789{i}", content=content, filename=name).status_code == 201
    exts = sorted(p.suffix for p in upload_dir.iterdir())
    assert exts == [".jpg", ".png"]


def test_stored_filename_is_random_not_user_supplied(client, make_account, upload_dir):
    _, h = make_account(email="a@example.com")
    submit_verification(client, h, filename="../../evil name.pdf")
    names = [p.name for p in upload_dir.iterdir()]
    assert len(names) == 1 and "evil" not in names[0] and ".." not in names[0]


def test_cannot_submit_twice_while_pending_or_after_approval(client, db, make_account, upload_dir):
    user, h = make_account(email="a@example.com")
    submit_verification(client, h)
    assert submit_verification(client, h).json()["error"]["code"] == "ALREADY_PENDING"
    db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"verification_status": "approved"}})
    assert submit_verification(client, h).json()["error"]["code"] == "ALREADY_VERIFIED"


def test_same_nid_on_two_accounts_is_blocked(client, make_account, upload_dir):
    _, h1 = make_account(email="a@example.com")
    _, h2 = make_account(email="b@example.com")
    assert submit_verification(client, h1).status_code == 201
    r = submit_verification(client, h2)
    assert r.status_code == 409 and r.json()["error"]["code"] == "NID_ALREADY_USED"


def test_admin_list_shows_masked_nid_only(client, make_account, admin_headers, upload_dir):
    _, h = make_account(email="a@example.com")
    submit_verification(client, h)
    r = client.get("/api/admin/verifications", headers=admin_headers)
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["nid_masked"] == "*********" + NID[-4:]
    assert NID not in r.text and "nid_encrypted" not in r.text and "doc_path" not in r.text


def test_admin_approve_sets_user_and_approves_pending_seller(client, db, make_account, admin_headers, upload_dir):
    seller, h = make_account(email="s@example.com", role="seller")
    submit_verification(client, h)
    rec_id = client.get("/api/admin/verifications", headers=admin_headers).json()["items"][0]["id"]
    r = client.patch(f"/api/admin/verifications/{rec_id}", json={"decision": "approve"}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert db.users.find_one({"_id": ObjectId(seller["id"])})["verification_status"] == "approved"
    assert db.seller_profiles.find_one({"user_id": ObjectId(seller["id"])})["status"] == "approved"
    assert client.get("/api/auth/me", headers=h).json()["verification_status"] == "approved"
    # a decision cannot be repeated
    again = client.patch(f"/api/admin/verifications/{rec_id}", json={"decision": "reject", "note": "x"},
                         headers=admin_headers)
    assert again.status_code == 409


def test_reject_needs_note_then_user_can_resubmit_and_old_file_is_deleted(client, db, make_account, admin_headers,
                                                                         upload_dir):
    user, h = make_account(email="a@example.com")
    submit_verification(client, h)
    rec_id = client.get("/api/admin/verifications", headers=admin_headers).json()["items"][0]["id"]
    assert client.patch(f"/api/admin/verifications/{rec_id}", json={"decision": "reject"},
                        headers=admin_headers).status_code == 422
    r = client.patch(f"/api/admin/verifications/{rec_id}", json={"decision": "reject", "note": "Photo is blurry"},
                     headers=admin_headers)
    assert r.json()["status"] == "rejected"
    st = client.get("/api/verification/status", headers=h).json()
    assert st["status"] == "rejected" and st["note"] == "Photo is blurry"
    first_files = {p.name for p in upload_dir.iterdir()}
    assert submit_verification(client, h, content=PNG, filename="new.png").status_code == 201
    now_files = {p.name for p in upload_dir.iterdir()}
    assert len(now_files) == 1 and now_files != first_files  # old document removed
    assert db.verification_records.count_documents({"user_id": ObjectId(user["id"])}) == 1


def test_document_access_is_audit_logged_and_served_with_safe_headers(client, db, make_account, admin_headers,
                                                                      upload_dir):
    _, h = make_account(email="a@example.com")
    submit_verification(client, h)
    rec_id = client.get("/api/admin/verifications", headers=admin_headers).json()["items"][0]["id"]
    before = db.audit_logs.count_documents({"action": "verification.document_view"})
    r = client.get(f"/api/admin/verifications/{rec_id}/document", headers=admin_headers)
    assert r.status_code == 200 and r.content == PDF
    assert r.headers["content-type"] == "application/pdf" and r.headers["cache-control"] == "no-store"
    assert db.audit_logs.count_documents({"action": "verification.document_view"}) == before + 1
    entry = db.audit_logs.find_one({"action": "verification.document_view"})
    assert NID not in str(entry)


def test_document_not_reachable_by_non_admins_or_static_urls(client, make_account, admin_headers, upload_dir):
    _, h = make_account(email="a@example.com")
    submit_verification(client, h)
    rec_id = client.get("/api/admin/verifications", headers=admin_headers).json()["items"][0]["id"]
    assert client.get(f"/api/admin/verifications/{rec_id}/document").status_code == 401
    assert client.get(f"/api/admin/verifications/{rec_id}/document", headers=h).status_code == 403
    stored = next(upload_dir.iterdir()).name
    for url in (f"/private_uploads/{stored}", f"/uploads/{stored}", f"/static/{stored}", f"/{stored}",
                f"/api/private_uploads/{stored}"):
        assert client.get(url).status_code == 404


def test_unknown_record_is_404(client, admin_headers):
    assert client.get(f"/api/admin/verifications/{ObjectId()}/document", headers=admin_headers).status_code == 404
    assert client.patch(f"/api/admin/verifications/{ObjectId()}", json={"decision": "approve"},
                        headers=admin_headers).status_code == 404