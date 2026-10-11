from datetime import date, datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from models.rental_request import RentalRequestModel
from schemas.rental import RentalRequestCreate


RENTAL_REQUESTS_COLLECTION = "rental_requests"
PRODUCTS_COLLECTION = "products"


def parse_object_id(value: str, label: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {label}.",
        )

    return ObjectId(value)


async def get_rentable_product(
    database: AsyncIOMotorDatabase,
    product_id: str,
) -> dict:
    product_object_id = parse_object_id(product_id, "product ID")

    product = await database[PRODUCTS_COLLECTION].find_one({
        "_id": product_object_id,
        "is_rentable": True,
        "price_per_day": {"$gt": 0},
    })

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rentable product not found.",
        )

    return product


async def check_rental_availability(
    database: AsyncIOMotorDatabase,
    product_id: str,
    start_date: date,
    end_date: date,
    exclude_request_id: ObjectId | None = None,
) -> dict:
    if start_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rental start date cannot be in the past.",
        )

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be on or after the start date.",
        )

    await get_rentable_product(database, product_id)

    conflict_query = {
        "product_id": product_id,
        "status": {"$in": ["pending", "accepted"]},
        "start_date": {"$lte": end_date.isoformat()},
        "end_date": {"$gte": start_date.isoformat()},
    }

    if exclude_request_id is not None:
        conflict_query["_id"] = {"$ne": exclude_request_id}

    conflict = await database[
        RENTAL_REQUESTS_COLLECTION
    ].find_one(conflict_query)

    return {
        "product_id": product_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "is_available": conflict is None,
    }


async def create_rental_request(
    database: AsyncIOMotorDatabase,
    shopper_id: str,
    data: RentalRequestCreate,
) -> dict:
    product = await get_rentable_product(
        database,
        data.product_id,
    )

    owner = product.get("owner_id") or product.get("seller_id")

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The product has no assigned owner.",
        )

    owner_id = str(owner)

    if owner_id == shopper_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot rent your own product.",
        )

    availability = await check_rental_availability(
        database,
        data.product_id,
        data.start_date,
        data.end_date,
    )

    if not availability["is_available"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The product is unavailable for these dates.",
        )

    total_days = (data.end_date - data.start_date).days + 1
    total_cost = float(product["price_per_day"]) * total_days

    rental = RentalRequestModel(
        product_id=data.product_id,
        shopper_id=shopper_id,
        owner_id=owner_id,
        start_date=data.start_date.isoformat(),
        end_date=data.end_date.isoformat(),
        total_days=total_days,
        total_cost=total_cost,
    )

    document = rental.model_dump(
        by_alias=True,
        exclude_none=True,
    )
    document.pop("_id", None)

    result = await database[
        RENTAL_REQUESTS_COLLECTION
    ].insert_one(document)

    document["id"] = str(result.inserted_id)

    return document


async def get_rental_requests(
    database: AsyncIOMotorDatabase,
    field: str,
    user_id: str,
) -> list[dict]:
    requests = await database[
        RENTAL_REQUESTS_COLLECTION
    ].find({
        field: user_id,
    }).sort("created_at", -1).to_list(length=100)

    for item in requests:
        item["id"] = str(item.pop("_id"))

    return requests


async def update_rental_request_status(
    database: AsyncIOMotorDatabase,
    request_id: str,
    owner_id: str,
    new_status: str,
) -> dict:
    request_object_id = parse_object_id(
        request_id,
        "rental request ID",
    )

    rental = await database[
        RENTAL_REQUESTS_COLLECTION
    ].find_one({
        "_id": request_object_id,
    })

    if not rental:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rental request not found.",
        )

    if rental["owner_id"] != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the product owner can update this request.",
        )

    if rental["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending requests can be updated.",
        )

    if new_status == "accepted":
        availability = await check_rental_availability(
            database,
            rental["product_id"],
            date.fromisoformat(rental["start_date"]),
            date.fromisoformat(rental["end_date"]),
            exclude_request_id=request_object_id,
        )

        if not availability["is_available"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="These dates overlap another rental request.",
            )

    updated = await database[
        RENTAL_REQUESTS_COLLECTION
    ].find_one_and_update(
        {
            "_id": request_object_id,
            "owner_id": owner_id,
            "status": "pending",
        },
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The request status has already changed.",
        )

    updated["id"] = str(updated.pop("_id"))

    return updated