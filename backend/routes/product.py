from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from config.database import db
from schemas.price_history import PriceHistoryResponse
from services.price_history_service import get_price_history


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


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