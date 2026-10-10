from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status

from config.database import db
from routes.auth import get_current_user
from schemas.rental import RentalRequestCreate, RentalStatusUpdate
from services.rental_service import (
    check_rental_availability,
    create_rental_request,
    get_rental_requests,
    update_rental_request_status,
)


router = APIRouter(
    prefix="/rentals",
    tags=["Rental Requests"],
)


def require_role(current_user: dict, expected_role: str) -> str:
    if current_user.get("role", "shopper") != expected_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only {expected_role}s can access this endpoint.",
        )

    return str(current_user["_id"])


@router.get("/{product_id}/availability")
async def rental_availability(
    product_id: str,
    start_date: date,
    end_date: date,
    current_user: dict = Depends(get_current_user),
):
    return await check_rental_availability(
        db,
        product_id,
        start_date,
        end_date,
    )


@router.post(
    "/requests",
    status_code=status.HTTP_201_CREATED,
)
async def submit_rental_request(
    data: RentalRequestCreate,
    current_user: dict = Depends(get_current_user),
):
    shopper_id = require_role(current_user, "shopper")

    return await create_rental_request(
        db,
        shopper_id,
        data,
    )


@router.get("/requests/mine")
async def my_rental_requests(
    current_user: dict = Depends(get_current_user),
):
    shopper_id = require_role(current_user, "shopper")

    return {
        "requests": await get_rental_requests(
            db,
            "shopper_id",
            shopper_id,
        )
    }


@router.get("/requests/received")
async def received_rental_requests(
    current_user: dict = Depends(get_current_user),
):
    owner_id = require_role(current_user, "seller")

    return {
        "requests": await get_rental_requests(
            db,
            "owner_id",
            owner_id,
        )
    }


@router.patch("/requests/{request_id}/status")
async def change_rental_request_status(
    request_id: str,
    data: RentalStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    owner_id = require_role(current_user, "seller")

    return await update_rental_request_status(
        db,
        request_id,
        owner_id,
        data.status,
    )