from fastapi import APIRouter, Request
from typing import List, Optional
from app.models import Product

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/search", response_model=List[Product])
async def search_products(
        request: Request,
        q: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,  # Matched to React frontend parameter
        sort: Optional[str] = None
):
    # Fixed database reference: main.py already selected 'fairshare'
    db = request.app.mongodb
    query = {}

    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None: query["price"]["$gte"] = min_price
        if max_price is not None: query["price"]["$lte"] = max_price
    if category and category != "All":
        query["category"] = category

    # Matched to React frontend filter logic
    if brand:
        query["brand"] = {"$in": brand.split(",")}

    cursor = db.products.find(query)

    if sort == "Price: low to high":
        cursor = cursor.sort("price", 1)
    elif sort == "Price: high to low":
        cursor = cursor.sort("price", -1)
    elif sort == "Rating":
        cursor = cursor.sort("rating", -1)

    products = await cursor.to_list(length=100)
    return products