from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


VIEWED_PRODUCTS_COLLECTION = "viewed_products"
PRODUCTS_COLLECTION = "products"

MIN_RECOMMENDATION_RATING = 4.0
MAX_RECENT_VIEWS = 20
MAX_ALTERNATIVES = 4


async def record_viewed_product(
    db: AsyncIOMotorDatabase,
    user_id: str,
    product_id: str,
) -> None:
    """
    Save a recently viewed product for a logged-in shopper.

    If the product was already viewed by the user,
    update its viewed time instead of creating a duplicate.

    Only the 20 most recent products are kept.
    """

    viewed_at = datetime.now(timezone.utc)

    await db[VIEWED_PRODUCTS_COLLECTION].update_one(
        {
            "user_id": user_id,
            "product_id": product_id,
        },
        {
            "$set": {
                "viewed_at": viewed_at,
            }
        },
        upsert=True,
    )

    cursor = (
        db[VIEWED_PRODUCTS_COLLECTION]
        .find({"user_id": user_id})
        .sort("viewed_at", -1)
        .skip(MAX_RECENT_VIEWS)
    )

    old_views = await cursor.to_list(length=None)

    if old_views:
        old_ids = [view["_id"] for view in old_views]

        await db[VIEWED_PRODUCTS_COLLECTION].delete_many(
            {
                "_id": {
                    "$in": old_ids,
                }
            }
        )


async def get_recently_viewed_products(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> list[str]:
    """
    Return the product IDs recently viewed by the user,
    newest first.
    """

    cursor = (
        db[VIEWED_PRODUCTS_COLLECTION]
        .find({"user_id": user_id})
        .sort("viewed_at", -1)
        .limit(MAX_RECENT_VIEWS)
    )

    views = await cursor.to_list(length=MAX_RECENT_VIEWS)

    return [
        view["product_id"]
        for view in views
    ]


async def get_budget_alternatives(
    db: AsyncIOMotorDatabase,
    product_id: str,
    budget: float,
) -> list[dict]:
    """
    Return up to four alternative products for a product.

    Alternatives must:
    - belong to the same category
    - be within the given budget
    - have a rating of at least 4.0
    - exclude the current product
    - exclude products from the same product group when
      product_group_id is available

    Products are ordered by the existing
    best_value_score field when available.
    """

    if budget <= 0:
        return []

    try:
        product_object_id = ObjectId(product_id)
    except Exception:
        return []

    product = await db[PRODUCTS_COLLECTION].find_one(
        {
            "_id": product_object_id,
        }
    )

    if not product:
        return []

    category = product.get("category")

    if not category:
        return []

    query = {
        "category": category,
        "rating": {
            "$gte": MIN_RECOMMENDATION_RATING,
        },
        "_id": {
            "$ne": product_object_id,
        },
        "$or": [
            {
                "lowest_price": {
                    "$lte": budget,
                }
            },
            {
                "lowest_price": {
                    "$exists": False,
                },
                "price": {
                    "$lte": budget,
                },
            },
        ],
    }

    product_group_id = product.get("product_group_id")

    if product_group_id is not None:
        query["product_group_id"] = {
            "$ne": product_group_id,
        }

    cursor = (
        db[PRODUCTS_COLLECTION]
        .find(query)
        .sort("best_value_score", -1)
        .limit(MAX_ALTERNATIVES)
    )

    alternatives = await cursor.to_list(
        length=MAX_ALTERNATIVES
    )

    return alternatives