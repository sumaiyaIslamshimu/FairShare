from fastapi import Header, HTTPException, status
from jose import JWTError

from auth.jwt_handler import decode_access_token


async def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Reusable auth dependency for future protected routes.
    Reads the Authorization header, expects "Bearer <token>",
    verifies it, and returns the decoded payload (user id + role).
    Raises 401 if the header is missing or the token is invalid/expired.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if authorization is None or not authorization.startswith("Bearer "):
        raise credentials_error

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise credentials_error

    user_id = payload.get("sub")
    role = payload.get("role")
    if user_id is None or role is None:
        raise credentials_error

    return {"id": user_id, "role": role}