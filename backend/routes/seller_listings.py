import math
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Body, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from config.database import db
from routes.auth import get_current_user

router = APIRouter(
    prefix="/seller/listings",
    tags=["Seller Listings"],
)

# Must match the role value that register_seller() stores on the user.
SELLER_ROLE = "seller"

# Defaults so seller listings carry the fields product search expects.
DEFAULT_MARKETPLACE_NAME = "FairShare Seller"
DEFAULT_RATING = 0.0


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the MongoDB database instance.
    """
    return db


# --------------------------------------------------
# Seller-only dependency
# --------------------------------------------------

async def require_seller(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    get_current_user already returns 401 for a missing/invalid token.
    This adds the seller-role check (403 for any other role).
    """
    if current_user.get("role") != SELLER_ROLE:
        raise HTTPException(
            status_code=403,
            detail="Only sellers can manage listings.",
        )
    return current_user


# --------------------------------------------------
# Validation helpers (all raise 400)
# --------------------------------------------------

def _bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=400, detail=message)


def _clean_text(value: Any, label: str, required: bool = False) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value.strip()
    else:
        raise _bad_request(f"{label} must be text")

    if required and not text:
        raise _bad_request(f"{label} is required")
    return text


def _validate_price(value: Any) -> float:
    if value is None or value == "":
        raise _bad_request("Price is required")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _bad_request("Price must be a number")
    if not math.isfinite(value):
        raise _bad_request("Price must be a number")
    if value <= 0:
        raise _bad_request("Price must be greater than 0")
    return float(value)


def _validate_stock(value: Any) -> int:
    if value is None or value == "":
        raise _bad_request("Stock is required")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _bad_request("Stock must be a whole number")
    if isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise _bad_request("Stock must be a whole number")
        value = int(value)
    if value < 0:
        raise _bad_request("Stock must be 0 or greater")
    return int(value)


def _validate_listing_payload(payload: dict) -> dict:
    """
    Shared by POST and PUT. Only these fields are ever read from the
    request, so a seller_id (or anything else) in the body is ignored.
    """
    return {
        "name": _clean_text(payload.get("name"), "Product name", required=True),
        "brand": _clean_text(payload.get("brand"), "Brand"),
        "category": _clean_text(payload.get("category"), "Category", required=True),
        "price": _validate_price(payload.get("price")),
        "stock": _validate_stock(payload.get("stock")),
        "description": _clean_text(payload.get("description"), "Description"),
        "image_link": _clean_text(payload.get("image_link"), "Image link"),
    }


# --------------------------------------------------
# Other helpers
# --------------------------------------------------

def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name", ""),
        "brand": doc.get("brand", ""),
        "category": doc.get("category", ""),
        "price": doc.get("price", 0),
        "stock": doc.get("stock", 0),
        "description": doc.get("description", ""),
        "image_link": doc.get("image_link") or "",
        "seller_id": doc.get("seller_id"),
    }


async def record_price_change(
    database: AsyncIOMotorDatabase,
    product_id: ObjectId,
    new_price: float,
) -> None:
    """
    Placeholder hook for price history. It does nothing until the price
    history storage is wired in; it is already called from PUT and
    quick-update whenever the price actually changes.
    """
    return None


async def _get_owned_listing(
    database: AsyncIOMotorDatabase,
    listing_id: str,
    seller_id: str,
) -> dict:
    try:
        object_id = ObjectId(listing_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Listing not found.")

    doc = await database.products.find_one({"_id": object_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Listing not found.")

    # Products without a seller_id (for example seed data) belong to
    # nobody, so no seller can edit or delete them.
    if doc.get("seller_id") != seller_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to modify this listing.",
        )
    return doc


# --------------------------------------------------
# Endpoints
# --------------------------------------------------

@router.post("", status_code=201)
async def create_listing(
    payload: dict = Body(...),
    seller: dict = Depends(require_seller),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    fields = _validate_listing_payload(payload)

    new_doc = {
        **fields,
        "in_stock": fields["stock"] > 0,
        "marketplace_name": DEFAULT_MARKETPLACE_NAME,
        "rating": DEFAULT_RATING,
        "product_link": None,
        "seller_id": str(seller["_id"]),  # always from the authenticated seller
    }

    result = await database.products.insert_one(new_doc)
    created = await database.products.find_one({"_id": result.inserted_id})
    return _serialize(created)


@router.get("")
async def get_my_listings(
    seller: dict = Depends(require_seller),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    cursor = database.products.find({"seller_id": str(seller["_id"])})
    docs = await cursor.to_list(length=500)
    return [_serialize(doc) for doc in docs]


@router.put("/{listing_id}")
async def update_listing(
    listing_id: str,
    payload: dict = Body(...),
    seller: dict = Depends(require_seller),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    existing = await _get_owned_listing(database, listing_id, str(seller["_id"]))
    fields = _validate_listing_payload(payload)

    # seller_id is never part of the update.
    updates = {**fields, "in_stock": fields["stock"] > 0}

    await database.products.update_one(
        {"_id": existing["_id"]},
        {"$set": updates},
    )

    if existing.get("price") != fields["price"]:
        await record_price_change(database, existing["_id"], fields["price"])

    updated = await database.products.find_one({"_id": existing["_id"]})
    return _serialize(updated)


@router.delete("/{listing_id}")
async def delete_listing(
    listing_id: str,
    seller: dict = Depends(require_seller),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    existing = await _get_owned_listing(database, listing_id, str(seller["_id"]))

    await database.products.delete_one({"_id": existing["_id"]})
    return {"message": "Listing deleted successfully.", "id": listing_id}


@router.patch("/{listing_id}/quick-update")
async def quick_update_listing(
    listing_id: str,
    payload: dict = Body(...),
    seller: dict = Depends(require_seller),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    existing = await _get_owned_listing(database, listing_id, str(seller["_id"]))

    if "price" not in payload and "stock" not in payload:
        raise _bad_request("Provide price and/or stock to update")

    # Only price and stock are ever read; any other key in the body is ignored.
    updates = {}
    if "price" in payload:
        updates["price"] = _validate_price(payload["price"])
    if "stock" in payload:
        stock = _validate_stock(payload["stock"])
        updates["stock"] = stock
        updates["in_stock"] = stock > 0

    await database.products.update_one(
        {"_id": existing["_id"]},
        {"$set": updates},
    )

    if "price" in updates and existing.get("price") != updates["price"]:
        await record_price_change(database, existing["_id"], updates["price"])

    updated = await database.products.find_one({"_id": existing["_id"]})
    return _serialize(updated)