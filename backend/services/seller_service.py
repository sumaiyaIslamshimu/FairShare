from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.seller_profile import SellerProfileModel
from schemas.seller import (
    SellerProfileCreate,
    SellerProfileUpdate,
)


SELLER_PROFILES_COLLECTION = "seller_profiles"
USERS_COLLECTION = "users"


async def create_seller_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
    data: SellerProfileCreate,
) -> SellerProfileModel:
    """
    Create a seller profile for a user.
    """

    try:
        user_object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID.",
        )

    user = await db[USERS_COLLECTION].find_one(
        {"_id": user_object_id}
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.get("role") != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can create a seller profile.",
        )

    existing_profile = await db[
        SELLER_PROFILES_COLLECTION
    ].find_one(
        {"user_id": user_id}
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seller profile already exists.",
        )

    profile = SellerProfileModel(
        user_id=user_id,
        shop_name=data.shop_name,
        shop_description=data.shop_description,
        phone=data.phone,
        address=data.address,
    )

    profile_data = profile.model_dump(
        by_alias=True,
        exclude_none=True,
    )
    profile_data["is_verified"] = False
    result = await db[
        SELLER_PROFILES_COLLECTION
    ].insert_one(profile_data)

    profile.id = str(result.inserted_id)

    return profile


async def get_seller_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[SellerProfileModel]:
    """
    Get a seller profile by user ID.
    """

    profile_data = await db[
        SELLER_PROFILES_COLLECTION
    ].find_one(
        {"user_id": user_id}
    )

    if not profile_data:
        return None

    profile_data["_id"] = str(profile_data["_id"])

    return SellerProfileModel(**profile_data)


async def update_seller_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
    data: SellerProfileUpdate,
) -> SellerProfileModel:
    """
    Update an existing seller profile.
    """

    update_data = data.model_dump(
        exclude_none=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update.",
        )

    result = await db[
        SELLER_PROFILES_COLLECTION
    ].find_one_and_update(
        {"user_id": user_id},
        {"$set": update_data},
        return_document=True,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found.",
        )

    result["_id"] = str(result["_id"])

    return SellerProfileModel(**result)


async def delete_seller_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> bool:
    """
    Delete a seller profile.
    """

    result = await db[
        SELLER_PROFILES_COLLECTION
    ].delete_one(
        {"user_id": user_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller profile not found.",
        )

    return True