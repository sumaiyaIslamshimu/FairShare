from fastapi import Depends, HTTPException
from routes.auth import get_current_user


def require_role(*allowed_roles):
    async def checker(user=Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to do this.",
            )
        return user

    return checker