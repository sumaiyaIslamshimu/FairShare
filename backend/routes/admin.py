from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from dependencies.roles import require_role

router = APIRouter()


class VerifyBody(BaseModel):
    is_verified: bool


@router.patch("/admin/sellers/{seller_id}/verify")
async def set_seller_verified(
    seller_id: str,
    body: VerifyBody,
    request: Request,
    admin=Depends(require_role("admin")),
):
    try:
        oid = ObjectId(seller_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid seller id.",
        )

    result = await request.app.mongodb.sellers.update_one(
        {"_id": oid},
        {"$set": {"is_verified": body.is_verified}},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Seller not found.",
        )

    return {
        "id": seller_id,
        "is_verified": body.is_verified,
    }