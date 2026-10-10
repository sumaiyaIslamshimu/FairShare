
from fastapi import APIRouter, Query

from config.database import db


router = APIRouter(
    prefix="/rentals",
    tags=["Rentals"],
)


@router.get("/search")
async def search_rentals(
    keyword: str | None = Query(default=None, min_length=1),
    category: str | None = Query(default=None, min_length=1),
    max_price_per_day: float | None = Query(default=None, gt=0),
):
    """
    Search rentable products by keyword, category,
    and maximum daily rental price.
    """

    query = {
        "is_rentable": True,
        "price_per_day": {"$ne": None},
    }

    if keyword:
        query["$or"] = [
            {"name": {"$regex": keyword, "$options": "i"}},
            {"category": {"$regex": keyword, "$options": "i"}},
        ]

    if category:
        query["category"] = {
            "$regex": f"^{category}$",
            "$options": "i",
        }

    if max_price_per_day is not None:
        query["price_per_day"]["$lte"] = max_price_per_day

    cursor = db["products"].find(query)

    products = await cursor.to_list(length=100)

    items = []

    for product in products:
        items.append({
            "id": str(product["_id"]),
            "name": product.get("name", ""),
            "image": product.get("image"),
            "price_per_day": product["price_per_day"],
            "location": product.get("location"),
            "is_available": True,
        })

    return {
        "items": items,
        "total": len(items),
    }
