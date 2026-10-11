from typing import List

from bson import ObjectId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.price_alert import PriceAlertModel
from schemas.alert import PriceAlertCreate


PRICE_ALERTS_COLLECTION = "price_alerts"
PRODUCTS_COLLECTION = "products"


async def create_price_alert(
    db: AsyncIOMotorDatabase,
    user_id: str,
    data: PriceAlertCreate,
) -> PriceAlertModel:
    """
    Create an active price alert for a user.
    """

    try:
        product_object_id = ObjectId(data.product_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    product = await db[PRODUCTS_COLLECTION].find_one(
        {"_id": product_object_id}
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    alert = PriceAlertModel(
        user_id=user_id,
        product_id=data.product_id,
        target_price=data.target_price,
        status="active",
    )

    alert_data = alert.model_dump(
        by_alias=True,
        exclude_none=True,
    )

    result = await db[
        PRICE_ALERTS_COLLECTION
    ].insert_one(alert_data)

    alert.id = str(result.inserted_id)

    return alert


async def get_user_price_alerts(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> List[dict]:
    """
    Get all price alerts belonging to a user.
    """

    cursor = db[
        PRICE_ALERTS_COLLECTION
    ].find(
        {"user_id": user_id}
    ).sort(
        "created_at",
        -1,
    )

    alerts = []

    async for alert in cursor:
        try:
            product_object_id = ObjectId(
                alert["product_id"]
            )
        except Exception:
            continue

        product = await db[
            PRODUCTS_COLLECTION
        ].find_one(
            {"_id": product_object_id}
        )

        if not product:
            continue

        product_name = product.get(
            "name",
            "Unknown Product",
        )

        current_lowest_price = product.get(
            "price"
        )

        if current_lowest_price is None:
            current_lowest_price = 0.0

        alerts.append(
            {
                "id": str(alert["_id"]),
                "user_id": alert["user_id"],
                "product_id": alert["product_id"],
                "product_name": product_name,
                "current_lowest_price": float(
                    current_lowest_price
                ),
                "target_price": alert["target_price"],
                "status": alert.get(
                    "status",
                    "active",
                ),
                "created_at": alert["created_at"],
                "triggered_at": alert.get(
                    "triggered_at"
                ),
            }
        )

    return alerts


async def delete_price_alert(
    db: AsyncIOMotorDatabase,
    user_id: str,
    alert_id: str,
) -> bool:
    """
    Delete a price alert belonging to the user.
    """

    try:
        alert_object_id = ObjectId(alert_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    alert = await db[
        PRICE_ALERTS_COLLECTION
    ].find_one(
        {"_id": alert_object_id}
    )

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    if alert.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own alerts.",
        )

    result = await db[
        PRICE_ALERTS_COLLECTION
    ].delete_one(
        {"_id": alert_object_id}
    )

    return result.deleted_count > 0