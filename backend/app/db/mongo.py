"""MongoDB access. Uses the synchronous PyMongo client (simple for beginners)."""
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

from app.core.config import get_settings
from app.core.errors import AppError

_client = None
_db = None


def get_db():
    """Returns the shared database object. Also used as a FastAPI dependency."""
    global _client, _db
    if _db is None:
        s = get_settings()
        _client = MongoClient(s.mongodb_uri, serverSelectionTimeoutMS=5000)
        _db = _client[s.db_name]
    return _db


def set_db(db) -> None:
    """Lets tests inject an in-memory database."""
    global _db
    _db = db


def ping_db() -> bool:
    try:
        get_db().command("ping")
        return True
    except Exception:
        return False


def to_object_id(value: str, label: str = "id") -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise AppError(404, "NOT_FOUND", f"{label} not found.")