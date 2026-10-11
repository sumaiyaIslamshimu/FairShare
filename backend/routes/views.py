from fastapi import APIRouter, Depends, status

from config.database import db
from routes.auth import get_current_user
from services.recommendation_service import record_viewed_product


router = APIRouter(
    prefix="/views",
    tags=["Recently Viewed"],
)


@router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def record_product_view(
    product_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Record a product viewed by the authenticated shopper.
    """

    await record_viewed_product(
        db,
        str(current_user["_id"]),
        product_id,
    )

    return None