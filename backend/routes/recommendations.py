from fastapi import APIRouter, Depends, HTTPException, Query, status

from config.database import db
from routes.auth import get_current_user
from services.recommendation_service import (
    get_budget_alternatives,
    get_recently_viewed_products,
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get("")
async def get_recommendations(
    product_id: str | None = Query(default=None, alias="productId"),
    budget: float | None = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Return recommendations for the authenticated shopper.

    If productId and budget are provided:
    return budget-based alternatives.

    If no productId and no budget are provided:
    return products related to the user's recently viewed products.
    """

    if budget is not None and budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than 0.",
        )

    if product_id is not None and budget is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget is required when productId is provided.",
        )

    if budget is not None and product_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="productId is required when budget is provided.",
        )

    if product_id is not None and budget is not None:
        alternatives = await get_budget_alternatives(
            db,
            product_id,
            budget,
        )

        return {
            "recommendations": alternatives,
        }

    user_id = str(current_user["_id"])

    recently_viewed_ids = await get_recently_viewed_products(
        db,
        user_id,
    )

    if not recently_viewed_ids:
        return {
            "recommendations": [],
        }

    viewed_products = await db["products"].find(
        {
            "_id": {
                "$in": recently_viewed_ids,
            }
        }
    ).to_list(length=20)

    viewed_categories = {
        product.get("category")
        for product in viewed_products
        if product.get("category")
    }

    if not viewed_categories:
        return {
            "recommendations": [],
        }

    recommendations = await db["products"].find(
        {
            "category": {
                "$in": list(viewed_categories),
            },
            "_id": {
                "$nin": recently_viewed_ids,
            },
        }
    ).sort(
        "best_value_score",
        -1,
    ).limit(6).to_list(length=6)

    return {
        "recommendations": recommendations,
    }