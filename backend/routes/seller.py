from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from config.database import db
from routes.auth import get_current_user
from schemas.seller import (
    SellerProfileCreate,
    SellerProfileResponse,
    SellerProfileUpdate,
)
from services.seller_service import (
    create_seller_profile,
    delete_seller_profile,
    get_seller_profile,
    update_seller_profile,
)

import re
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Request
from dependencies.roles import require_role
router = APIRouter(
    prefix="/seller",
    tags=["Seller"],
)


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the MongoDB database instance.
    """
    return db


@router.post(
    "/profile",
    response_model=SellerProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    data: SellerProfileCreate,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a seller profile for the authenticated seller.
    """

    profile = await create_seller_profile(
        database,
        str(current_user["_id"]),
        data,
    )

    return SellerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        shop_name=profile.shop_name,
        shop_description=profile.shop_description,
        phone=profile.phone,
        address=profile.address,
        is_verified=profile.is_verified,
    )


@router.get(
    "/profile",
    response_model=SellerProfileResponse,
)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get the authenticated seller's profile.
    """

    profile = await get_seller_profile(
        database,
        str(current_user["_id"]),
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found.",
        )

    return SellerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        shop_name=profile.shop_name,
        shop_description=profile.shop_description,
        phone=profile.phone,
        address=profile.address,
        is_verified=profile.is_verified,
    )


@router.put(
    "/profile",
    response_model=SellerProfileResponse,
)
async def update_profile(
    data: SellerProfileUpdate,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update the authenticated seller's profile.
    """

    profile = await update_seller_profile(
        database,
        str(current_user["_id"]),
        data,
    )

    return SellerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        shop_name=profile.shop_name,
        shop_description=profile.shop_description,
        phone=profile.phone,
        address=profile.address,
        is_verified=profile.is_verified,
    )


@router.delete(
    "/profile",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_profile(
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Delete the authenticated seller's profile.
    """

    await delete_seller_profile(
        database,
        str(current_user["_id"]),
    )

    return None



async def find_group_listings(db, listing):
    name = re.escape(listing["name"].strip())

    cursor = db.products.find({
        "_id": {"$ne": listing["_id"]},
        "seller_id": {"$ne": listing.get("seller_id")},
        "name": {"$regex": f"^{name}$", "$options": "i"},
    })

    return [doc async for doc in cursor]


@router.get("/listings/{listing_id}/price-insights")
async def price_insights(
    listing_id: str,
    request: Request,
    seller=Depends(require_role("seller")),
):
    db = get_database()

    try:
        oid = ObjectId(listing_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid listing id.")

    listing = await db.products.find_one({"_id": oid})

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found.")

    if str(listing.get("seller_id")) != str(seller.get("id") or seller.get("_id")):
        raise HTTPException(
            status_code=403,
            detail="You can only view insights for your own listings.",
        )

    own_price = listing["price"]
    others = await find_group_listings(db, listing)

    prices = [
        item["price"]
        for item in others
        if isinstance(item.get("price"), (int, float))
    ]

    if not prices:
        return {
            "has_competitors": False,
            "own_price": own_price,
            "message": "No other sellers list this product.",
        }

    return {
        "has_competitors": True,
        "own_price": own_price,
        "lowest": min(prices),
        "average": round(sum(prices) / len(prices), 2),
        "highest": max(prices),
        "count": len(prices),
    }