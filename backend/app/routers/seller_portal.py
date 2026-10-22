"""FastAPI endpoints for Seller Profile, Promotions, and Insights."""
from fastapi import APIRouter, Depends, Response

from app.core.deps import require_approved_seller, require_role
from app.db.mongo import get_db
from app.models.seller import (PromotionCreate, PromotionOut, PromotionUpdate,
                               SellerInsightsOut, SellerProfileOut, SellerProfileUpdate)
from app.services import seller_service

router = APIRouter(prefix="/seller", tags=["Seller Portal"])


@router.get("/profile", response_model=SellerProfileOut)
def get_my_profile(seller=Depends(require_role("seller")), db=Depends(get_db)):
    """Any logged-in seller can view their profile, even if pending."""
    return seller_service.get_profile(db, seller)


@router.put("/profile", response_model=SellerProfileOut)
def update_my_profile(body: SellerProfileUpdate, seller=Depends(require_role("seller")), db=Depends(get_db)):
    """Any logged-in seller can update their contact info."""
    return seller_service.update_profile(db, seller, body)


@router.get("/insights", response_model=SellerInsightsOut)
def get_insights(seller=Depends(require_role("seller")), db=Depends(get_db)):
    """Dashboard analytics for the seller."""
    return seller_service.get_insights(db, seller)


@router.post("/promotions", response_model=PromotionOut, status_code=201)
def create_promotion(body: PromotionCreate, seller=Depends(require_approved_seller), db=Depends(get_db)):
    """Only approved sellers can create active promotions."""
    return seller_service.create_promotion(db, seller, body)


@router.get("/promotions", response_model=list[PromotionOut])
def list_promotions(seller=Depends(require_approved_seller), db=Depends(get_db)):
    return seller_service.list_promotions(db, seller)


@router.put("/promotions/{promo_id}", response_model=PromotionOut)
def update_promotion(promo_id: str, body: PromotionUpdate, seller=Depends(require_approved_seller), db=Depends(get_db)):
    return seller_service.update_promotion(db, seller, promo_id, body)


@router.delete("/promotions/{promo_id}", status_code=204)
def delete_promotion(promo_id: str, seller=Depends(require_approved_seller), db=Depends(get_db)):
    seller_service.delete_promotion(db, seller, promo_id)
    return Response(status_code=204)