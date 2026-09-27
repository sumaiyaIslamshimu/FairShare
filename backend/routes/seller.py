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