"""FastAPI dependencies for authentication and role-based authorization."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.mongo import get_db, to_object_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db=Depends(get_db),
) -> dict:
    """Loads the user from the DB on every request, so role changes and
    deactivation take effect immediately (the role is NOT trusted from the token)."""
    if creds is None:
        raise AppError(401, "NOT_AUTHENTICATED", "Please log in.")
    payload = decode_access_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise AppError(401, "INVALID_TOKEN", "Your session is invalid or has expired.")
    try:
        user = db.users.find_one({"_id": to_object_id(payload["sub"])})
    except AppError:
        user = None
    if not user:
        raise AppError(401, "INVALID_TOKEN", "Your session is invalid or has expired.")
    if not user.get("is_active", True):
        raise AppError(403, "ACCOUNT_DISABLED", "This account has been disabled.")
    return user


def require_role(*roles: str):
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise AppError(403, "FORBIDDEN", "You do not have permission to do this.")
        return user

    return checker


def require_approved_seller(user: dict = Depends(require_role("seller")), db=Depends(get_db)) -> dict:
    """Seller whose profile an admin has approved (needed to publish listings)."""
    profile = db.seller_profiles.find_one({"user_id": user["_id"]})
    if not profile or profile.get("status") != "approved":
        raise AppError(403, "SELLER_NOT_APPROVED", "Your seller account is not approved yet.")
    return user