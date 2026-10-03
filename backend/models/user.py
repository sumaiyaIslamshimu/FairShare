from datetime import datetime, timezone
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, BeforeValidator, ConfigDict


def validate_object_id(value: Any) -> ObjectId:
    """
    Accepts either an ObjectId (from Mongo) or a valid ObjectId string
    and returns an ObjectId. Raises if the value isn't a valid ObjectId.
    """
    if isinstance(value, ObjectId):
        return value

    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)

    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class UserCreate(BaseModel):
    """
    Shape of the data accepted by POST /register.
    Password is plain text here only because it is received from
    the client and should be hashed before being stored in MongoDB.
    """
    name: str = Field(min_length=1)
    email: EmailStr
    phone: str = Field(min_length=1)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Shape of the data accepted by POST /login."""
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """
    Shape of a shopper document stored in / read from MongoDB.
    Never expose this model directly because it contains hashed_password.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    id: PyObjectId = Field(alias="_id")
    name: str
    email: EmailStr
    phone: str
    hashed_password: str
    role: str = "shopper"
    is_active: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class UserOut(BaseModel):
    """
    Public user information returned to the frontend.
    Password and hashed_password are never exposed.
    """

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: EmailStr
    phone: str | None = None
    role: str
    is_active: bool = True
    created_at: datetime

    @staticmethod
    def from_mongo(doc: dict) -> "UserOut":
        """
        Build a UserOut from a raw MongoDB document.
        Converts MongoDB ObjectId to a string.
        """

        return UserOut(
            id=str(doc["_id"]),
            name=doc["name"],
            email=doc["email"],
            phone=doc.get("phone"),
            role=doc.get("role", "shopper"),
            is_active=doc.get("is_active", True),
            created_at=doc["created_at"],
        )


class TokenResponse(BaseModel):
    """
    Response shape for POST /login.
    Contains the JWT and public user information.
    """

    access_token: str
    token_type: str = "bearer"
    user: UserOut