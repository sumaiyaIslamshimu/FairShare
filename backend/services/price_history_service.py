from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase

from models.price_history import PriceHistoryModel


PRICE_HISTORY_COLLECTION = "price_history"


async def get_price_history(
    db: AsyncIOMotorDatabase,
    product_id: str,
) -> List[PriceHistoryModel]:
    """
    Get price history for a product in ascending date order.
    """

    cursor = db[
        PRICE_HISTORY_COLLECTION
    ].find(
        {"product_id": product_id}
    ).sort(
        "recorded_at",
        1,
    )

    history = []

    async for document in cursor:
        document["_id"] = str(document["_id"])

        history.append(
            PriceHistoryModel(**document)
        )

    return history