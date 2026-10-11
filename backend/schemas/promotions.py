from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from routes.seller_listings import (
    _get_owned_listing,
    get_database,
    require_seller,
)
from schemas.promotion import (
    ActiveDiscount,
    ActiveDiscountsResponse,
    DiscountIn,
    DiscountView,
    SpotlightSeller,
)
from services.promotion_service import (
    MAX_BATCH_IDS,
    build_discount_view,
    select_spotlight_sellers,
    shorten_description,
    utc_now,
    validate_discount,
)

router = APIRouter(
    prefix="/promotions",
    tags=["Promotions"],
)

# Collection used by services/seller_service.py for seller profiles.
# Check the name there; change this one line if it differs.
SELLER_PROFILES_COLLECTION = "seller_profiles"


def _to_object_id(listing_id: str) -> ObjectId:
    if not ObjectId.is_valid(listing_id):
        raise HTTPException(status_code=404, detail="Listing not found.")
    return ObjectId(listing_id)


# --------------------------------------------------
# Discounts
# --------------------------------------------------

@router.put(
    "/listings/{listing_id}/discount",
    response_model=DiscountView,
)
async def set_listing_discount(
    listing_id: str,
    data: DiscountIn,
    seller: dict = Depends(require_seller),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create or update the discount on the seller's own listing.
    404 if the listing does not exist, 403 if it belongs to another seller.
    The listing's original price is never changed.
    """
    listing = await _get_owned_listing(database, listing_id, str(seller["_id"]))

    try:
        percentage, starts_at, ends_at = validate_discount(
            data.percentage,
            data.starts_at,
            data.ends_at,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    await database.products.update_one(
        {"_id": listing["_id"]},
        {
            "$set": {
                "discount": {
                    "percentage": percentage,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                }
            }
        },
    )

    updated = await database.products.find_one({"_id": listing["_id"]})
    return build_discount_view(updated)


@router.get(
    "/listings/{listing_id}/discount",
    response_model=DiscountView,
)
async def get_listing_discount(
    listing_id: str,
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Public. Returns the stored discount with its status
    (upcoming / active / expired) and the calculated prices.
    """
    listing = await database.products.find_one({"_id": _to_object_id(listing_id)})
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found.")
    return build_discount_view(listing)


@router.delete(
    "/listings/{listing_id}/discount",
    response_model=DiscountView,
)
async def remove_listing_discount(
    listing_id: str,
    seller: dict = Depends(require_seller),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    listing = await _get_owned_listing(database, listing_id, str(seller["_id"]))

    await database.products.update_one(
        {"_id": listing["_id"]},
        {"$unset": {"discount": ""}},
    )

    updated = await database.products.find_one({"_id": listing["_id"]})
    return build_discount_view(updated)


@router.get(
    "/active",
    response_model=ActiveDiscountsResponse,
)
async def get_active_discounts(
    ids: str = Query("", description="Comma-separated listing ids"),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Public batch lookup used by product cards and the comparison table.
    Only discounts that are active right now are returned, so upcoming and
    expired discounts never change a displayed price.
    """
    object_ids = []
    for raw in ids.split(",")[:MAX_BATCH_IDS]:
        raw = raw.strip()
        if raw and ObjectId.is_valid(raw):
            object_ids.append(ObjectId(raw))

    if not object_ids:
        return ActiveDiscountsResponse(discounts={})

    now = utc_now()
    docs = await database.products.find(
        {"_id": {"$in": object_ids}, "discount": {"$exists": True}}
    ).to_list(length=len(object_ids))

    discounts = {}
    for doc in docs:
        view = build_discount_view(doc, now)
        if view["is_active"]:
            discounts[view["listing_id"]] = ActiveDiscount(
                percentage=view["percentage"],
                original_price=view["original_price"],
                discounted_price=view["discounted_price"],
                ends_at=view["ends_at"],
            )

    return ActiveDiscountsResponse(discounts=discounts)


# --------------------------------------------------
# Seller Spotlight
# --------------------------------------------------

@router.get(
    "/spotlight",
    response_model=List[SpotlightSeller],
)
async def get_spotlight_sellers(
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Real sellers only. A seller needs at least one listing and a seller
    profile (that is where the business name comes from). Rating is the
    average of the seller's rated listings; sellers with no rated listings
    are not penalised. See services/promotion_service.py for the rules.
    """
    pipeline = [
        {"$match": {"seller_id": {"$exists": True, "$nin": [None, ""]}}},
        {
            "$group": {
                "_id": "$seller_id",
                "listing_count": {"$sum": 1},
                "rated_sum": {
                    "$sum": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$rating", 0]}, 0]},
                            "$rating",
                            0,
                        ]
                    }
                },
                "rated_count": {
                    "$sum": {
                        "$cond": [
                            {"$gt": [{"$ifNull": ["$rating", 0]}, 0]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
    ]

    groups = await database.products.aggregate(pipeline).to_list(length=1000)
    if not groups:
        return []

    seller_ids = [group["_id"] for group in groups]
    profiles = await database[SELLER_PROFILES_COLLECTION].find(
        {"user_id": {"$in": seller_ids}}
    ).to_list(length=1000)
    profile_by_user = {profile["user_id"]: profile for profile in profiles}

    candidates = []
    for group in groups:
        profile = profile_by_user.get(group["_id"])
        if not profile:
            continue  # no business name to show, so no card

        rated_count = group["rated_count"]
        rating = round(group["rated_sum"] / rated_count, 1) if rated_count else None

        candidates.append(
            {
                "seller_id": group["_id"],
                "business_name": profile.get("shop_name"),
                "is_verified": bool(profile.get("is_verified", False)),
                "rating": rating,
                "description": shorten_description(profile.get("shop_description")),
                "listing_count": group["listing_count"],
            }
        )

    return [SpotlightSeller(**seller) for seller in select_spotlight_sellers(candidates)]