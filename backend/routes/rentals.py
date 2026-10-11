import re
from typing import Optional

from fastapi import APIRouter, Query, Request

router = APIRouter()


async def has_open_dates(db, product_id: str, days: int = 90) -> bool:
    """
    Should check whether this item has any open dates in the next `days` days.
    The availability collection doesn't exist yet (story 2), so until then
    every rentable item counts as available.
    """
    # TODO (story 2): query the availability collection for open dates
    return True


@router.get("/rentals/search")
async def search_rentals(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    maxPricePerDay: Optional[float] = Query(None, gt=0),
):
    db = request.app.mongodb

    # Only rentable products, ever
    query = {"is_rentable": True}

    # Optional keyword: matches name or category, case-insensitive
    if q and q.strip():
        pattern = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"name": pattern}, {"category": pattern}]

    # Optional exact category (case-insensitive)
    if category and category.strip():
        query["category"] = {
            "$regex": f"^{re.escape(category.strip())}$",
            "$options": "i",
        }

    # Optional maximum price per day
    if maxPricePerDay is not None:
        query["price_per_day"] = {"$lte": maxPricePerDay}

    items = []
    async for doc in db.products.find(query):
        doc["id"] = str(doc.pop("_id"))
        doc["is_available"] = await has_open_dates(db, doc["id"])
        items.append(doc)

    return items