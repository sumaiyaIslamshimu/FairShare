from typing import Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from config.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from models.user import UserModel
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
    SellerRegisterRequest,
)

USERS_COLLECTION = "users"


async def register_user(
    db: AsyncIOMotorDatabase,
    data: RegisterRequest,
) -> UserModel:
    """
    Register a new shopper.
    """

    existing_user = await db[USERS_COLLECTION].find_one(
        {"email": data.email}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    hashed_password = hash_password(data.password)

    user = UserModel(
        name=data.name,
        email=data.email,
        hashed_password=hashed_password,
        role=data.role,
    )

    user_data = user.model_dump(
        by_alias=True,
        exclude_none=True,
    )
    user_data["is_verified"] = False
    result = await db[USERS_COLLECTION].insert_one(user_data)

    user.id = str(result.inserted_id)

    return user


async def register_seller(
    db: AsyncIOMotorDatabase,
    data: SellerRegisterRequest,
) -> UserModel:
    """
    Register a new seller.
    """

    existing_user = await db[USERS_COLLECTION].find_one(
        {"email": data.email}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered.",
        )

    hashed_password = hash_password(data.password)

    user = UserModel(
        name=data.name,
        email=data.email,
        hashed_password=hashed_password,
        role="seller",
    )

    user_data = user.model_dump(
        by_alias=True,
        exclude_none=True,
    )

    result = await db[USERS_COLLECTION].insert_one(user_data)

    user.id = str(result.inserted_id)

    return user


async def login_user(
    db: AsyncIOMotorDatabase,
    data: LoginRequest,
) -> str:
    """
    Authenticate a user and return an access token.
    """

    user_data = await db[USERS_COLLECTION].find_one(
        {"email": data.email}
    )

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(
        data.password,
        user_data["hashed_password"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    token_data = {
        "sub": str(user_data["_id"]),
        "email": user_data["email"],
        "role": user_data.get("role", "shopper"),
    }

    return create_access_token(token_data)


async def get_user_by_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> Optional[dict]:
    """
    Get a user by MongoDB ID.
    """

    try:
        object_id = ObjectId(user_id)
    except Exception:
        return None

    return await db[USERS_COLLECTION].find_one(
        {"_id": object_id}
    )