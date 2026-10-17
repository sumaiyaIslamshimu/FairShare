"""Registration, login and profile lookup."""
from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password


def user_public(db, user: dict) -> dict:
    seller_status = None
    if user["role"] == "seller":
        profile = db.seller_profiles.find_one({"user_id": user["_id"]})
        seller_status = profile["status"] if profile else None
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "phone": user.get("phone", ""),
        "role": user["role"],
        "is_active": user.get("is_active", True),
        "verification_status": user.get("verification_status", "none"),
        "seller_status": seller_status,
    }


def register(db, data) -> dict:
    email = data.email.lower().strip()
    now = datetime.now(timezone.utc)
    doc = {
        "email": email,
        "full_name": data.full_name.strip(),
        "phone": data.phone,
        "password_hash": hash_password(data.password),
        "role": data.role,
        "is_active": True,
        "verification_status": "none",
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = db.users.insert_one(doc)
    except DuplicateKeyError:
        raise AppError(409, "EMAIL_EXISTS", "An account with this email already exists.")
    doc["_id"] = result.inserted_id
    if data.role == "seller":
        db.seller_profiles.insert_one({
            "user_id": doc["_id"],
            "business_name": data.business_name.strip(),
            "description": "",
            "contact_phone": data.phone,
            "address": "",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        })
    return user_public(db, doc)


def login(db, email: str, password: str) -> dict:
    user = db.users.find_one({"email": email.lower().strip()})
    # Same message for unknown email and wrong password (no account enumeration).
    if not user or not verify_password(password, user["password_hash"]):
        raise AppError(401, "INVALID_CREDENTIALS", "Incorrect email or password.")
    if not user.get("is_active", True):
        raise AppError(403, "ACCOUNT_DISABLED", "This account has been disabled.")
    return {
        "access_token": create_access_token(str(user["_id"]), user["role"]),
        "token_type": "bearer",
        "user": user_public(db, user),
    }