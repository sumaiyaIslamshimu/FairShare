from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase


PRICE_HISTORY_COLLECTION = "price_history"
PRICE_ALERTS_COLLECTION = "price_alerts"


async def check_alerts(
    db: AsyncIOMotorDatabase,
    product_id: str | None = None,
) -> int:
    """
    Check active price alerts and trigger alerts when the
    latest product price is at or below the target price.

    Returns:
        Number of alerts triggered.
    """

    alert_query = {"status": "active"}

    if product_id:
        alert_query["product_id"] = product_id

    alerts_cursor = db[PRICE_ALERTS_COLLECTION].find(alert_query)

    triggered_count = 0

    async for alert in alerts_cursor:
        alert_product_id = alert["product_id"]
        target_price = alert["target_price"]

        latest_price = await db[PRICE_HISTORY_COLLECTION].find_one(
            {"product_id": alert_product_id},
            sort=[("recorded_at", -1)],
        )

        if not latest_price:
            continue

        current_price = latest_price["price"]

        if current_price <= target_price:
            await db[PRICE_ALERTS_COLLECTION].update_one(
                {"_id": alert["_id"]},
                {
                    "$set": {
                        "status": "triggered",
                        "triggered_at": datetime.now(timezone.utc),
                    }
                },
            )

            triggered_count += 1

    return triggered_count