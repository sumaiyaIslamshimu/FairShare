"""Append-only audit log: admin actions and every verification-document access."""
from app.db.mongo import to_object_id
from app.services.time_utils import iso, utcnow

# Keys that must never be stored in an audit entry, whatever a caller passes.
_FORBIDDEN_KEYS = {"nid", "nid_number", "nid_encrypted", "password", "password_hash", "token"}


def log(db, actor: dict, action: str, target: str = "", details: dict | None = None) -> None:
    safe = {k: v for k, v in (details or {}).items() if k.lower() not in _FORBIDDEN_KEYS}
    db.audit_logs.insert_one({
        "actor_id": actor["_id"],
        "actor_email": actor.get("email", ""),
        "action": action,
        "target": str(target),
        "details": safe,
        "at": utcnow(),
    })


def serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]), "actor_id": str(doc["actor_id"]), "actor_email": doc.get("actor_email", ""),
        "action": doc["action"], "target": doc.get("target", ""), "details": doc.get("details", {}),
        "at": iso(doc.get("at")),
    }


def list_logs(db, page: int, page_size: int, action: str | None = None, actor_id: str | None = None) -> dict:
    flt: dict = {}
    if action:
        flt["action"] = {"$regex": f"^{_escape(action)}"}
    if actor_id:
        flt["actor_id"] = to_object_id(actor_id, "Actor")
    total = db.audit_logs.count_documents(flt)
    cur = db.audit_logs.find(flt).sort("at", -1).skip((page - 1) * page_size).limit(page_size)
    return {"items": [serialize(d) for d in cur], "total": total, "page": page, "page_size": page_size}


def _escape(text: str) -> str:
    import re
    return re.escape(text.strip())