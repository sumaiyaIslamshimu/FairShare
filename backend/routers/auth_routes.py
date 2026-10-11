from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from auth.security import hash_password, verify_password
from auth.jwt_handler import create_access_token
from models.user import UserCreate, UserLogin, UserOut, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    from main import db

    existing_user = await db["users"].find_one({"email": user_in.email})

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    new_user_doc = {
        "name": user_in.name,
        "email": user_in.email,
        "phone": user_in.phone,
        "hashed_password": hash_password(user_in.password),
        "role": "shopper",
        "created_at": datetime.now(timezone.utc),
    }

    result = await db["users"].insert_one(new_user_doc)

    created_doc = await db["users"].find_one(
        {"_id": result.inserted_id}
    )

    return UserOut.from_mongo(created_doc)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(user_in: UserLogin):

    from main import db

    existing_user = await db["users"].find_one({"email": user_in.email})

    if existing_user is None or not verify_password(
        user_in.password,
        existing_user["hashed_password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        user_id=str(existing_user["_id"]),
        role=existing_user.get("role", "shopper"),
    )

    return TokenResponse(
        access_token=access_token,
        user=UserOut.from_mongo(existing_user),
    )