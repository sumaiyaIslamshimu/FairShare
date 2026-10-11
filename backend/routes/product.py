import re
from typing import List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, status

from app.models import ListingOut, Product, ProductCompareResponse, ProductHeader
from app.ranking_models import ListingScoreOut, ProductRankingResponse
from app.scoring import rank_listings
from config.database import db
from schemas.price_history import PriceHistoryResponse
from services.price_history_service import get_price_history


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# --------------------------------------------------
# Product search (same filters as before)
# --------------------------------------------------

@router.get("/search", response_model=List[Product])
async def search_products(
    q: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    sort: Optional[str] = None,
):
    query = {}

    if q:
        query["name"] = {"$regex": q, "$options": "i"}

    if min_price is not None or max_price is not None:
        query["price"] = {}

        if min_price is not None:
            query["price"]["$gte"] = min_price

        if max_price is not None:
            query["price"]["$lte"] = max_price

    if category and category != "All":
        query["category"] = category

    if brand:
        query["brand"] = {"$in": brand.split(",")}

    cursor = db["products"].find(query)

    if sort == "Price: low to high":
        cursor = cursor.sort("price", 1)

    elif sort == "Price: high to low":
        cursor = cursor.sort("price", -1)

    elif sort == "Rating":
        cursor = cursor.sort("rating", -1)

    return await cursor.to_list(length=100)


# --------------------------------------------------
# Shared helper for compare + ranking
# --------------------------------------------------

async def _get_anchor_and_matches(product_id: str):
    try:
        object_id = ObjectId(product_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail="Product not found")

    anchor_doc = await db["products"].find_one({"_id": object_id})
    if anchor_doc is None:
        raise HTTPException(status_code=404, detail="Product not found")

    match_query = {
        "name": {"$regex": f"^{re.escape(anchor_doc['name'])}$", "$options": "i"},
        "brand": {"$regex": f"^{re.escape(anchor_doc['brand'])}$", "$options": "i"},
        "category": {"$regex": f"^{re.escape(anchor_doc['category'])}$", "$options": "i"},
    }

    matching_docs = await db["products"].find(match_query).to_list(length=50)
    return anchor_doc, matching_docs


def _product_header(anchor_doc: dict) -> ProductHeader:
    return ProductHeader(
        id=str(anchor_doc["_id"]),
        name=anchor_doc["name"],
        brand=anchor_doc["brand"],
        category=anchor_doc["category"],
        image_url=anchor_doc.get("image_link"),
    )


# --------------------------------------------------
# Compare listings across marketplaces
# --------------------------------------------------

@router.get("/{product_id}/compare", response_model=ProductCompareResponse)
async def compare_product(product_id: str):
    """
    seller and delivery_cost do not exist on products yet, so they are null.
    """
    anchor_doc, matching_docs = await _get_anchor_and_matches(product_id)

    listings = [
        ListingOut(
            id=str(doc["_id"]),
            marketplace=doc.get("marketplace_name", ""),
            seller=None,
            price=doc["price"],
            delivery_cost=None,
            rating=doc.get("rating", 0),
            product_url=doc.get("product_link"),
        )
        for doc in matching_docs
    ]
    listings.sort(key=lambda listing: listing.price)

    return ProductCompareResponse(
        product=_product_header(anchor_doc),
        listings=listings,
    )


# --------------------------------------------------
# Best-value ranking
# --------------------------------------------------

@router.get("/{product_id}/ranking", response_model=ProductRankingResponse)
async def rank_product_listings(product_id: str):
    """
    delivery_cost and discount are not stored yet, so they are None and
    the scoring engine treats them neutrally.
    """
    anchor_doc, matching_docs = await _get_anchor_and_matches(product_id)

    raw_listings = [
        {
            "id": str(doc["_id"]),
            "marketplace": doc.get("marketplace_name", ""),
            "seller": None,
            "price": doc["price"],
            "delivery_cost": None,
            "rating": doc.get("rating", 0),
            "discount": None,
            "product_url": doc.get("product_link"),
        }
        for doc in matching_docs
    ]

    ranked = rank_listings(raw_listings)

    return ProductRankingResponse(
        product=_product_header(anchor_doc),
        listings=[ListingScoreOut(**listing) for listing in ranked],
    )


# --------------------------------------------------
# Price history (unchanged)
# --------------------------------------------------

@router.get(
    "/{product_id}/price-history",
    response_model=list[PriceHistoryResponse],
)
async def get_product_price_history(
    product_id: str,
):
    """
    Get price history for a product in ascending date order.
    """

    try:
        product_object_id = ObjectId(product_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    product = await db["products"].find_one(
        {"_id": product_object_id}
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    history = await get_price_history(
        db,
        product_id,
    )

    return [
        PriceHistoryResponse(
            id=item.id,
            product_id=item.product_id,
            price=item.price,
            recorded_at=item.recorded_at,
        )
        for item in history
    ]