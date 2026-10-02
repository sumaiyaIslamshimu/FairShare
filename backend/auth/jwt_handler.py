import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))


def create_access_token(user_id: str, role: str) -> str:
    """
    Create a signed JWT containing the user's id and role.
    Expires after JWT_EXPIRE_MINUTES minutes.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT.
    Raises jose.JWTError if the token is invalid, tampered, or expired.
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])