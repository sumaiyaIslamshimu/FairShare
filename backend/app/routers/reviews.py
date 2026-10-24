from fastapi import APIRouter, Depends, Query, Response

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.review import (ReviewCreate, ReviewOwn, ReviewOwnPage, ReviewPublicPage, ReviewSellerPage, ReviewUpdate)
from app.services import review_service

router = APIRouter(tags=["Reviews"])
PageQ = Query(1, ge=1)
SizeQ = Query(20, ge=1, le=50)


@router.post("/reviews", response_model=ReviewOwn, status_code=201)
def create(body: ReviewCreate, user=Depends(require_role("user")), db=Depends(get_db)):
    return review_service.create(db, user, body)


@router.get("/reviews/mine", response_model=ReviewOwnPage)
def mine(page: int = PageQ, page_size: int = SizeQ, user=Depends(require_role("user")), db=Depends(get_db)):
    return review_service.list_mine(db, user, page, page_size)


@router.put("/reviews/{review_id}", response_model=ReviewOwn)
def update(review_id: str, body: ReviewUpdate, user=Depends(require_role("user")), db=Depends(get_db)):
    return review_service.update(db, user, review_id, body)


@router.delete("/reviews/{review_id}", status_code=204)
def remove(review_id: str, user=Depends(require_role("user")), db=Depends(get_db)):
    review_service.delete(db, user, review_id)
    return Response(status_code=204)


@router.get("/seller-products/{product_id}/reviews", response_model=ReviewPublicPage)
def product_reviews(product_id: str, page: int = PageQ, page_size: int = SizeQ, db=Depends(get_db)):
    return review_service.list_for_product(db, product_id, page, page_size)


@router.get("/seller/reviews", response_model=ReviewSellerPage)
def seller_reviews(page: int = PageQ, page_size: int = SizeQ, seller=Depends(require_role("seller")), db=Depends(get_db)):
    return review_service.list_for_seller(db, seller, page, page_size)