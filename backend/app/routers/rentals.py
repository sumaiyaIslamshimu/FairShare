"""FastAPI endpoints for the Rentals module."""
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.models.rental import RentalListingCreate, RentalListingOut, RentalListingPageOut, RentalRequestCreate, RentalRequestDecision, RentalRequestOut
from app.services import rental_service

router = APIRouter(prefix="/rentals", tags=["Rentals"])


@router.get("/listings", response_model=RentalListingPageOut)
def browse_rentals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db=Depends(get_db)
):
    return rental_service.list_public_rentals(db, page, page_size)


@router.post("/listings", response_model=RentalListingOut, status_code=201)
def create_rental_listing(body: RentalListingCreate, user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.create_listing(db, user, body)


@router.post("/requests", response_model=RentalRequestOut, status_code=201)
def request_rental(body: RentalRequestCreate, user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.submit_request(db, user, body)


@router.post("/requests/{request_id}/decision", response_model=RentalRequestOut)
def decide_rental_request(request_id: str, body: RentalRequestDecision, user=Depends(get_current_user), db=Depends(get_db)):
    return rental_service.process_request(db, user, request_id, body.action)