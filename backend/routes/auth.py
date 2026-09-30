from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from config.database import db
from config.security import decode_access_token
from schemas.auth import (
    LoginRequest,
    RegisterRequest,
    SellerRegisterRequest,
    TokenResponse,
    UserResponse,
)
from services.auth_service import (
    get_user_by_id,
    login_user,
    register_seller,
    register_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
)


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the MongoDB database instance.
    """
    return db


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """
    Get the currently authenticated user from JWT token.
    """

    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_id(
        database,
        user_id,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Register a new shopper.
    """

    user = await register_user(
        database,
        data,
    )

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


@router.post(
    "/seller/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_seller_account(
    data: SellerRegisterRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Register a new seller.
    """

    user = await register_seller(
        database,
        data,
    )

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    data: LoginRequest,
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Login an existing user.
    """

    access_token = await login_user(
        database,
        data,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: dict = Depends(get_current_user),
):
    """
    Get the currently authenticated user's information.
    """

    return UserResponse(
        id=str(current_user["_id"]),
        name=current_user["name"],
        email=current_user["email"],
        role=current_user.get("role", "shopper"),
        is_active=current_user.get("is_active", True),
    )