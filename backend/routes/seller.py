from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

from config.database import db
from routes.auth import get_current_user
from schemas.seller import (
    SellerProfileCreate,
    SellerProfileResponse,
    SellerProfileUpdate,
    RentalSettingsUpdate,
)
from services.seller_service import (
    create_seller_profile,
    delete_seller_profile,
    get_seller_profile,
    update_seller_profile,
)

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


@router.patch(
    "/listings/{id}/rental",
    status_code=status.HTTP_200_OK,
)
async def update_rental_settings(
        id: str,
        data: RentalSettingsUpdate,
        current_user: dict = Depends(get_current_user),
        database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Update rental settings (is_rentable, price_per_day) for a specific listing.
    Only the owning seller can modify these settings.
    """

    # 1. Validate that price_per_day is greater than 0 if the item is rentable
    if data.is_rentable and (data.price_per_day is None or data.price_per_day <= 0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid price_per_day greater than 0 is required when making an item rentable."
        )

    try:
        obj_id = ObjectId(id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid listing ID format."
        )

    # 2. Fetch the listing to verify it exists and belongs to this seller
    listing = await database.products.find_one({"_id": obj_id})

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found."
        )

    # 3. Ownership check (returns 403 if it belongs to someone else)
    listing_owner_id = str(listing.get("seller_id", listing.get("user_id")))
    if listing_owner_id != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this listing's rental settings."
        )

    # 4. Save the changes
    update_data = {
        "is_rentable": data.is_rentable,
        "price_per_day": data.price_per_day
    }

    await database.products.update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )

    return {
        "message": "Rental settings updated successfully",
        "is_rentable": data.is_rentable,
        "price_per_day": data.price_per_day
    }