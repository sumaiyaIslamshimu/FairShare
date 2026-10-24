"""Identity verification: encrypted NID, private document storage, masked admin review.

Rules (see docs/SECURITY.md):
- The raw NID is encrypted with Fernet and is never returned, logged or written to the audit log.
- Only the last 4 digits are kept in the clear, for display as ******1234.
- The document is saved under a random name in a private folder that is never served statically.
- Verification is MANUAL: an admin looks at the document and approves or rejects.
"""
import hashlib
import hmac
import re
import uuid
from pathlib import Path

from fastapi import UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import encrypt_text
from app.db.mongo import to_object_id
from app.services import audit_service
from app.services.time_utils import iso, utcnow
from app.services import audit_service, notification_service

MAX_DOC_BYTES = 5 * 1024 * 1024  # 5 MB
NID_RE = re.compile(r"^(\d{10}|\d{13}|\d{17})$")  # Bangladesh NID: 10, 13 (old) or 17 digits
# Real file type is decided from the first bytes, never from the client's file name or Content-Type.
_SIGNATURES = (
    (b"%PDF-", "pdf", "application/pdf"),
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
)
_MEDIA = {ext: media for _, ext, media in _SIGNATURES}


def upload_dir() -> Path:
    path = Path(get_settings().private_upload_dir).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_nid(raw: str) -> str:
    digits = re.sub(r"[\s\-]", "", raw or "")
    if not NID_RE.match(digits):
        raise AppError(422, "INVALID_NID", "Enter a valid NID number (10, 13 or 17 digits).")
    return digits


def mask_nid(last4: str, length: int) -> str:
    return "*" * max(length - 4, 0) + last4


def _nid_fingerprint(nid: str) -> str:
    """Keyed hash used only to detect the same NID on two accounts. It cannot be reversed to the NID."""
    key = get_settings().fernet_key.encode("utf-8")
    return hmac.new(key, nid.encode("utf-8"), hashlib.sha256).hexdigest()


def detect_file_type(head: bytes) -> tuple[str, str]:
    for sig, ext, media in _SIGNATURES:
        if head.startswith(sig):
            return ext, media
    raise AppError(422, "INVALID_DOCUMENT", "The document must be a PDF, JPG or PNG file.")


def _save_document(data: bytes) -> tuple[str, str]:
    ext, _ = detect_file_type(data[:16])
    name = f"{uuid.uuid4().hex}.{ext}"  # random name: nothing from the user is in the path
    (upload_dir() / name).write_bytes(data)
    return name, ext


def _delete_document(name: str | None) -> None:
    if not name:
        return
    try:
        (upload_dir() / Path(name).name).unlink(missing_ok=True)
    except OSError:
        pass


def _read_limited(upload: UploadFile) -> bytes:
    data = upload.file.read(MAX_DOC_BYTES + 1)
    if len(data) > MAX_DOC_BYTES:
        raise AppError(413, "FILE_TOO_LARGE", "The document is too large (maximum 5 MB).")
    if not data:
        raise AppError(422, "INVALID_DOCUMENT", "The document is empty.")
    return data


# ---------- the account owner ----------

def submit(db, user: dict, nid_number: str, document: UploadFile) -> dict:
    if user["role"] == "admin":
        raise AppError(403, "FORBIDDEN", "Admin accounts do not need identity verification.")
    current = user.get("verification_status", "none")
    if current == "pending":
        raise AppError(409, "ALREADY_PENDING", "Your verification is already waiting for review.")
    if current == "approved":
        raise AppError(409, "ALREADY_VERIFIED", "Your identity is already verified.")

    nid = normalize_nid(nid_number)
    fingerprint = _nid_fingerprint(nid)
    clash = db.verification_records.find_one({"nid_fingerprint": fingerprint, "user_id": {"$ne": user["_id"]},
                                              "status": {"$in": ["pending", "approved"]}})
    if clash:
        raise AppError(409, "NID_ALREADY_USED", "This NID is already linked to another account.")

    data = _read_limited(document)
    detect_file_type(data[:16])  # validate BEFORE touching the disk

    old = db.verification_records.find_one({"user_id": user["_id"]})
    name, ext = _save_document(data)
    now = utcnow()
    record = {
        "user_id": user["_id"],
        "nid_encrypted": encrypt_text(nid),
        "nid_last4": nid[-4:],
        "nid_length": len(nid),
        "nid_fingerprint": fingerprint,
        "doc_path": name,
        "doc_type": ext,
        "status": "pending",
        "reviewed_by": None,
        "reviewed_at": None,
        "note": None,
        "submitted_at": now,
        "updated_at": now,
    }
    db.verification_records.update_one({"user_id": user["_id"]}, {"$set": record}, upsert=True)
    if old:
        _delete_document(old.get("doc_path"))  # a resubmission replaces the old file
    db.users.update_one({"_id": user["_id"]}, {"$set": {"verification_status": "pending", "updated_at": now}})
    return status_for(db, {**user, "verification_status": "pending"})


def status_for(db, user: dict) -> dict:
    rec = db.verification_records.find_one({"user_id": user["_id"]})
    status = user.get("verification_status", "none")
    out = {"status": status, "submitted_at": None, "reviewed_at": None, "note": None, "manual_review": True}
    if rec:
        out.update({"submitted_at": iso(rec.get("submitted_at")), "reviewed_at": iso(rec.get("reviewed_at")),
                    "note": rec.get("note") if status == "rejected" else None})
    return out


# ---------- admin ----------

def _serialize_review(db, rec: dict) -> dict:
    user = db.users.find_one({"_id": rec["user_id"]}) or {}
    return {
        "id": str(rec["_id"]),
        "user_id": str(rec["user_id"]),
        "user_name": user.get("full_name", ""),
        "user_email": user.get("email", ""),
        "user_role": user.get("role", ""),
        "nid_masked": mask_nid(rec.get("nid_last4", "****"), rec.get("nid_length", 10)),
        "has_document": bool(rec.get("doc_path")),
        "document_type": rec.get("doc_type"),
        "status": rec["status"],
        "note": rec.get("note"),
        "submitted_at": iso(rec.get("submitted_at")),
        "reviewed_at": iso(rec.get("reviewed_at")),
        "reviewed_by": str(rec["reviewed_by"]) if rec.get("reviewed_by") else None,
    }


def list_records(db, status: str | None, page: int, page_size: int) -> dict:
    flt = {"status": status} if status else {}
    total = db.verification_records.count_documents(flt)
    cur = db.verification_records.find(flt).sort("submitted_at", -1).skip((page - 1) * page_size).limit(page_size)
    return {"items": [_serialize_review(db, r) for r in cur], "total": total, "page": page, "page_size": page_size}


def _get_record(db, record_id: str) -> dict:
    rec = db.verification_records.find_one({"_id": to_object_id(record_id, "Verification record")})
    if not rec:
        raise AppError(404, "NOT_FOUND", "Verification record not found.")
    return rec


def review(db, admin: dict, record_id: str, decision: str, note: str | None) -> dict:
    rec = _get_record(db, record_id)
    if rec["status"] != "pending":
        raise AppError(409, "NOT_PENDING", "Only a pending verification can be reviewed.")
    note = (note or "").strip() or None
    if decision == "reject" and not note:
        raise AppError(422, "NOTE_REQUIRED", "Give a short reason so the person can fix and resubmit.")
    new_status = "approved" if decision == "approve" else "rejected"
    now = utcnow()
    db.verification_records.update_one(
        {"_id": rec["_id"]},
        {"$set": {"status": new_status, "reviewed_by": admin["_id"], "reviewed_at": now, "note": note,
                  "updated_at": now}})
    db.users.update_one({"_id": rec["user_id"]}, {"$set": {"verification_status": new_status, "updated_at": now}})
    audit_service.log(db, admin, f"verification.{new_status}", str(rec["user_id"]), {"record_id": str(rec["_id"])})

    # Seller approval flows from verification: an approved identity approves a pending seller profile.
    if new_status == "approved":
        profile = db.seller_profiles.find_one({"user_id": rec["user_id"]})
        if profile and profile.get("status") == "pending":
            db.seller_profiles.update_one({"_id": profile["_id"]}, {"$set": {"status": "approved", "updated_at": now}})
            audit_service.log(db, admin, "seller.approved", str(rec["user_id"]), {"via": "verification"})
    if new_status == "approved":
         notification_service.notify(db, rec["user_id"], "verification", "Your identity was verified",
                        "An administrator approved your identity verification.", "verification")
    else:
         notification_service.notify(db, rec["user_id"], "verification", "Your verification was not approved",
                        f"Reason: {note}. You can fix this and submit again.", "verification")
    return _serialize_review(db, db.verification_records.find_one({"_id": rec["_id"]}))


def document_response(db, admin: dict, record_id: str) -> FileResponse:
    """Streams the private document to an admin. The access is audit-logged BEFORE any byte is sent."""
    rec = _get_record(db, record_id)
    name = rec.get("doc_path")
    path = upload_dir() / Path(name).name if name else None
    if not path or not path.is_file():
        raise AppError(404, "NOT_FOUND", "No document is stored for this record.")
    audit_service.log(db, admin, "verification.document_view", str(rec["user_id"]), {"record_id": str(rec["_id"])})
    media = _MEDIA.get(rec.get("doc_type"), "application/octet-stream")
    # Download name is generic on purpose; nothing about the person goes into headers.
    return FileResponse(path, media_type=media, filename=f"verification-document.{rec.get('doc_type', 'bin')}",
                        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})