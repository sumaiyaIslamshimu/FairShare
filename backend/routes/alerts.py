from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from config.database import db
from routes.auth import get_current_user
from schemas.alert import (
    PriceAlertCreate,
    PriceAlertResponse,
)
from services.alert_service import (
    create_price_alert,
    delete_price_alert,
    get_user_price_alerts,
)
from services.alert_checker import check_alerts


router = APIRouter(
    prefix="/alerts",
    tags=["Price Alerts"],
)


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the MongoDB database instance.
    """
    return db


@router.post(
    "",
    response_model=PriceAlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_alert(
    data: PriceAlertCreate,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Create a price alert for the authenticated user.
    """
    alert = await create_price_alert(
        database,
        str(current_user["_id"]),
        data,
    )

    return PriceAlertResponse(
        id=alert.id,
        user_id=alert.user_id,
        product_id=alert.product_id,
        product_name="",
        current_lowest_price=0.0,
        target_price=alert.target_price,
        status=alert.status,
        created_at=alert.created_at,
        triggered_at=alert.triggered_at,
    )


@router.get(
    "",
    response_model=list[PriceAlertResponse],
)
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get all price alerts belonging to the authenticated user.
    """
    alerts = await get_user_price_alerts(
        database,
        str(current_user["_id"]),
    )

    return [
        PriceAlertResponse(**alert)
        for alert in alerts
    ]


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Delete an alert belonging to the authenticated user.
    """
    await delete_price_alert(
        database,
        str(current_user["_id"]),
        alert_id,
    )

    return None


@router.post("/check")
async def run_alert_checker(
    current_user: dict = Depends(get_current_user),
):
    """
    Run the alert checker manually for testing.
    """
    triggered_count = await check_alerts(db)

    return {
        "message": "Alert check completed.",
        "triggered_count": triggered_count,
    }