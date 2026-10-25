"""In-app notifications. A notification is a small message for ONE person; only that person can read or change it.

notify() is called from other services after their real work succeeded. It never raises: a failed notification
must not undo or block the action that caused it (the failure is logged instead).
"""
import logging

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.services.time_utils import iso, utcnow

log = logging.getLogger(__name__)


def notify(db, user_id, kind: str, title: str, body: str = "", link: str = "") -> None:
    try:
        db.notifications.insert_one({
            "user_id": user_id, "kind": kind, "title": title[:150], "body": body[:500], "link": link[:200],
            "is_read": False, "created_at": utcnow(),
        })
    except Exception:  # noqa: BLE001 - see module docstring
        log.exception("Could not store a notification (kind=%s)", kind)


def serialize(d: dict) -> dict:
    return {"id": str(d["_id"]), "kind": d["kind"], "title": d["title"], "body": d.get("body", ""),
            "link": d.get("link", ""), "is_read": bool(d.get("is_read")), "created_at": iso(d.get("created_at"))}


def unread_count(db, user: dict) -> int:
    return db.notifications.count_documents({"user_id": user["_id"], "is_read": False})


def list_mine(db, user: dict, unread_only: bool, page: int, page_size: int) -> dict:
    flt = {"user_id": user["_id"]}
    if unread_only:
        flt["is_read"] = False
    total = db.notifications.count_documents(flt)
    cur = db.notifications.find(flt).sort([("created_at", -1), ("_id", -1)]).skip((page - 1) * page_size).limit(page_size)
    return {"items": [serialize(d) for d in cur], "total": total, "unread": unread_count(db, user),
            "page": page, "page_size": page_size}


def mark_read(db, user: dict, notification_id: str) -> dict:
    oid = to_object_id(notification_id, "Notification")
    d = db.notifications.find_one({"_id": oid})
    if not d or d["user_id"] != user["_id"]:  # someone else's notification looks exactly like a missing one
        raise AppError(404, "NOT_FOUND", "Notification not found.")
    db.notifications.update_one({"_id": oid}, {"$set": {"is_read": True}})
    return serialize(db.notifications.find_one({"_id": oid}))


def mark_all_read(db, user: dict) -> int:
    res = db.notifications.update_many({"user_id": user["_id"], "is_read": False}, {"$set": {"is_read": True}})
    return res.modified_count