import re
from fastapi import Request, HTTPException, APIRouter
from bson import ObjectId
from bson.errors import InvalidId
from config.database import db # Assuming db is exported from your config

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request

from app.models import Product
from services.scoring import rank_listings

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/search", response_model=List[Product])
async def search_products(
        request: Request,
        q: Optional[str] = None,
        min_price: Optional[float] = Query(default=None, ge=0),
        max_price: Optional[float] = Query(default=None, ge=0),
        category: Optional[str] = None,
        rating_min: Optional[float] = Query(default=None, ge=0, le=5),
        sort: Optional[str] = None,
):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="Minimum price cannot exceed maximum price.")

    db = request.app.mongodb
    query = {}

    if q:
        escaped_query = re.escape(q.strip())
        query["$or"] = [
            {"name": {"$regex": escaped_query, "$options": "i"}},
            {"brand": {"$regex": escaped_query, "$options": "i"}},
            {"category": {"$regex": escaped_query, "$options": "i"}},
        ]
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    if category and category != "All":
        categories = [re.escape(item.strip()) for item in category.split(",") if item.strip()]
        if categories:
            query["category"] = {
                "$in": [re.compile(f"^{item}$", re.IGNORECASE) for item in categories]
            }
    if rating_min is not None:
        query["rating"] = {"$gte": rating_min}

    cursor = db.products.find(query)

    if sort in ("Price: low to high", "price_asc"):
        cursor = cursor.sort("price", 1)
    elif sort in ("Price: high to low", "price_desc"):
        cursor = cursor.sort("price", -1)
    elif sort in ("Rating", "rating_desc"):
        cursor = cursor.sort("rating", -1)

    products = await cursor.to_list(length=100)
    return products


 #Ranking Endpoint ---

@router.get("/{product_id}/ranking")
async def get_product_rankings(product_id: str, request: Request):
    """
    Fetches all listings for a given product ID, scores them,
    and returns them ranked from highest to lowest best-value score.
    """
    db = request.app.mongodb

    # Fetch listings associated with this product
    # Note: Assuming your collection for individual seller offers is called 'listings'
    cursor = db.listings.find({"product_id": product_id})
    listings = await cursor.to_list(length=100)

    if not listings:
        raise HTTPException(status_code=404, detail="No listings found for this product.")

    # Convert ObjectIds to strings so FastAPI can serialize them to JSON
    for listing in listings:
        if "_id" in listing:
            listing["_id"] = str(listing["_id"])

    # Rank the listings using our scoring engine
    ranked_listings = rank_listings(listings)

    return {
        "product_id": product_id,
        "total_listings": len(ranked_listings),
        "rankings": ranked_listings
    }


#  Product Comparison Endpoint ---

@router.get("/{product_id}/compare")
async def compare_products(product_id: str):
    """
    Finds a product by ID, then returns all products in the same matching group
    to be compared across marketplaces.
    """
    # 1. Validate and convert the ID to a MongoDB ObjectId
    try:
        obj_id = ObjectId(product_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid product ID format.")

    # 2. Find the requested base product
    base_product = await db.products.find_one({"_id": obj_id})

    if not base_product:
        raise HTTPException(status_code=404, detail="Product not found.")

    # Safely convert the base ObjectId to string
    base_product["_id"] = str(base_product["_id"])
    group_id = base_product.get("group_id")

    # 3. Find all products sharing this group_id
    if group_id:
        cursor = db.products.find({"group_id": group_id})
        matching_products = await cursor.to_list(length=100)
    else:
        # Fallback if the grouping script hasn't run on this product yet
        matching_products = [base_product]

    # Convert ObjectIds to strings for the response list
    for p in matching_products:
        p["_id"] = str(p["_id"])

    # 4. Return the base product details AND the full comparison list
    return {
        "base_product": base_product,
        "comparisons": matching_products
    }