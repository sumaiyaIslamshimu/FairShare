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


# PyObjectId: a Pydantic-compatible type that validates Mongo's ObjectId
# on the way in, but is treated as a plain field so it can be serialized
# to a string on the way out (via UserOut below).
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


class UserCreate(BaseModel):
    """
    Shape of the data accepted by POST /register.
    Password is plain text here ONLY because it's in-transit from the
    client; it is hashed before anything touches the database.
    Phone is required, non-empty; no format validation is enforced yet.
    """
    name: str = Field(min_length=1)
    email: EmailStr
    phone: str = Field(min_length=1)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Shape of the data accepted by POST /login. Unchanged: email + password only."""
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """
    Shape of a shopper document as stored in / read from MongoDB.
    Never expose this model directly in an API response —
    it contains hashed_password.
    """
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: PyObjectId = Field(alias="_id")
    name: str
    email: EmailStr
    phone: str
    hashed_password: str
    role: str = "shopper"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserOut(BaseModel):
    """
    Shape of a shopper returned to the client (e.g. after register/login,
    or from an auth dependency). No password field exists here at all,
    so it can never accidentally leak.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    email: EmailStr
    phone: str | None = None
    role: str
    created_at: datetime

    @staticmethod
    def from_mongo(doc: dict) -> "UserOut":
        """
        Build a UserOut directly from a raw MongoDB document,
        converting _id (ObjectId) to a plain string id.
        Uses doc.get("phone") for backward compatibility with
        test users created before the phone field existed.
        """
        return UserOut(
            id=str(doc["_id"]),
            name=doc["name"],
            email=doc["email"],
            phone=doc.get("phone"),
            role=doc.get("role", "shopper"),
            created_at=doc["created_at"],
        )


class TokenResponse(BaseModel):
    """
    Response shape for POST /login: the JWT plus the authenticated
    user's public info (via UserOut, so no password fields exist here).
    """
    access_token: str
    token_type: str = "bearer"
    user: UserOut