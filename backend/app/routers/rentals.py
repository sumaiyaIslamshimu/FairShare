"""FastAPI endpoints for the Rentals module."""
from fastapi import APIRouter, Depends, Query, Response

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.models.rental import (
    RentalBookingOut,
    RentalEventOut,
    RentalListingCreate,
    RentalListingOut,
    RentalListingPageOut,
    RentalListingUpdate,
    RentalRequestCreate,
    RentalRequestDecision,
    RentalRequestOut,
)
from app.services import rental_service

router = APIRouter(prefix="/rentals", tags=["Rentals"])


# --- Listings --------------------------------------------------------------- #
@router.get("/listings", response_model=RentalListingPageOut)
def browse_rentals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db=Depends(get_db)
):
    return rental_service.list_public_rentals(db, page, page_size)


@router.get("/listings/{listing_id}", response_model=RentalListingOut)
def get_rental_listing(listing_id: str, db=Depends(get_db)):
    return rental_service.get_public_listing(db, listing_id)


@router.post("/listings", response_model=RentalListingOut, status_code=201)
def create_rental_listing(body: RentalListingCreate, user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.create_listing(db, user, body)


@router.put("/listings/{listing_id}", response_model=RentalListingOut)
def update_rental_listing(listing_id: str, body: RentalListingUpdate, user=Depends(get_current_user),
                          db=Depends(get_db)):
    return rental_service.update_listing(db, user, listing_id, body)


@router.delete("/listings/{listing_id}", status_code=204)
def remove_rental_listing(listing_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    rental_service.remove_listing(db, user, listing_id)
    return Response(status_code=204)


@router.get("/my/listings", response_model=list[RentalListingOut])
def my_rental_listings(user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.list_my_listings(db, user)


# --- Requests --------------------------------------------------------------- #
@router.post("/requests", response_model=RentalRequestOut, status_code=201)
def request_rental(body: RentalRequestCreate, user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.submit_request(db, user, body)


@router.get("/my/requests", response_model=list[RentalRequestOut])
def my_rental_requests(user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.list_my_requests(db, user)


@router.get("/incoming-requests", response_model=list[RentalRequestOut])
def incoming_rental_requests(user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.list_incoming_requests(db, user)


@router.post("/requests/{request_id}/decision", response_model=RentalRequestOut)
def decide_rental_request(request_id: str, body: RentalRequestDecision, user=Depends(get_current_user),
                          db=Depends(get_db)):
    return rental_service.process_request(db, user, request_id, body.action)


@router.post("/requests/{request_id}/cancel", response_model=RentalRequestOut)
def cancel_rental_request(request_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.cancel_request(db, user, request_id)


@router.get("/requests/{request_id}/events", response_model=list[RentalEventOut])
def rental_request_events(request_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.list_request_events(db, user, request_id)


# --- Bookings --------------------------------------------------------------- #
@router.get("/bookings", response_model=list[RentalBookingOut])
def my_rental_bookings(user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.list_my_bookings(db, user)