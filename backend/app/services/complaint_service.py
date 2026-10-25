"""Complaints filed by shoppers and sellers about an order, a seller or a rental."""
from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.services import audit_service
from app.services.time_utils import iso, utcnow
from app.services import audit_service, notification_service

OPEN_STATES = ("open", "in_review")


def serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]), "target_type": doc["target_type"], "target_id": str(doc["target_id"]),
        "description": doc["description"], "status": doc["status"], "admin_note": doc.get("admin_note"),
        "created_at": iso(doc.get("created_at")), "updated_at": iso(doc.get("updated_at")),
    }


def _check_target(db, user: dict, target_type: str, target_id: str):
    """The filer must really be part of the thing they complain about."""
    oid = to_object_id(target_id, "Complaint target")
    if target_type == "order":
        order = db.orders.find_one({"_id": oid})
        mine = order and order["user_id"] == user["_id"]
        sold = order and db.order_items.find_one({"order_id": oid, "seller_id": user["_id"]})
        if not (mine or sold):
            raise AppError(404, "NOT_FOUND", "Order not found.")
    elif target_type == "seller":
        profile = db.seller_profiles.find_one({"user_id": oid})
        if not profile:
            raise AppError(404, "NOT_FOUND", "Seller not found.")
        if oid == user["_id"]:
            raise AppError(400, "BAD_REQUEST", "You cannot file a complaint about yourself.")
    else:  # rental: a request that the filer owns or made
        req = db.rental_requests.find_one({"_id": oid})
        if not req or user["_id"] not in (req["owner_id"], req["renter_id"]):
            raise AppError(404, "NOT_FOUND", "Rental request not found.")
    return oid


def file_complaint(db, user: dict, data) -> dict:
    if user["role"] == "admin":
        raise AppError(403, "FORBIDDEN", "Admins manage complaints; they do not file them.")
    oid = _check_target(db, user, data.target_type, data.target_id)
    duplicate = db.complaints.find_one({"filer_id": user["_id"], "target_type": data.target_type, "target_id": oid,
                                        "status": {"$in": list(OPEN_STATES)}})
    if duplicate:
        raise AppError(409, "DUPLICATE_COMPLAINT", "You already have an open complaint about this.")
    now = utcnow()
    doc = {"filer_id": user["_id"], "target_type": data.target_type, "target_id": oid,
           "description": data.description, "status": "open", "admin_note": None,
           "created_at": now, "updated_at": now}
    doc["_id"] = db.complaints.insert_one(doc).inserted_id
    return serialize(doc)


def list_mine(db, user: dict, page: int, page_size: int) -> dict:
    flt = {"filer_id": user["_id"]}
    total = db.complaints.count_documents(flt)
    cur = db.complaints.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    return {"items": [serialize(d) for d in cur], "total": total, "page": page, "page_size": page_size}


# ---------- admin ----------

def list_all(db, status: str | None, target_type: str | None, page: int, page_size: int) -> dict:
    flt: dict = {}
    if status:
        flt["status"] = status
    if target_type:
        flt["target_type"] = target_type
    total = db.complaints.count_documents(flt)
    cur = db.complaints.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    return {"items": [_admin_row(db, d) for d in cur], "total": total, "page": page, "page_size": page_size}


def _admin_row(db, d: dict) -> dict:
    filer = db.users.find_one({"_id": d["filer_id"]}) or {}
    return {**serialize(d), "filer_id": str(d["filer_id"]), "filer_name": filer.get("full_name", ""),
            "filer_email": filer.get("email", "")}


def update(db, admin: dict, complaint_id: str, data) -> dict:
    doc = db.complaints.find_one({"_id": to_object_id(complaint_id, "Complaint")})
    if not doc:
        raise AppError(404, "NOT_FOUND", "Complaint not found.")
    changes = {}
    if data.status is not None:
        changes["status"] = data.status
    if data.admin_note is not None:
        changes["admin_note"] = data.admin_note.strip() or None
    if not changes:
        raise AppError(422, "NOTHING_TO_UPDATE", "Provide a status or a note.")
    changes["updated_at"] = utcnow()
    db.complaints.update_one({"_id": doc["_id"]}, {"$set": changes})
    audit_service.log(db, admin, "complaint.update", str(doc["_id"]),
                      {"status": changes.get("status"), "note_changed": "admin_note" in changes})
    notification_service.notify(db, doc["filer_id"], "complaint", "Your complaint was updated",
                                f"Status: {changes.get('status', doc['status'])}", "complaints")
    return _admin_row(db, db.complaints.find_one({"_id": doc["_id"]}))