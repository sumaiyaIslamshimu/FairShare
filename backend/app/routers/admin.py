"""Admin API. EVERY route requires role 'admin' (checked against the database on each request)."""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.admin import (AdminSellerPage, AdminUserOut, AdminUserPage, AuditPage, CategoryCreate, CategoryUpdate,
                              ProductModerationOut, ProductModerationPage, ProductModerationUpdate,
                              RentalModerationOut, RentalModerationPage, RentalModerationUpdate, SellerStatusUpdate,
                              StatsOut, SubcategoryCreate, SubcategoryUpdate, UserActiveUpdate, VerificationDecision,
                              VerificationReviewOut, VerificationReviewPage, AdminSellerOut)
from app.models.complaint import ComplaintAdminOut, ComplaintAdminPage, ComplaintUpdate
from app.models.returns import ReturnDecision, ReturnStaffOut, ReturnStaffPage
from app.services import admin_service, audit_service, complaint_service, return_service, review_service, verification_service
from app.models.review import ReviewAdmin, ReviewAdminPage, ReviewModeration

router = APIRouter(prefix="/admin", tags=["Admin"])
Admin = Depends(require_role("admin"))
PageQ = Query(1, ge=1)
SizeQ = Query(20, ge=1, le=100)


@router.get("/stats", response_model=StatsOut)
def stats(_=Admin, db=Depends(get_db)):
    return admin_service.stats(db)


# ---- users and sellers ----
@router.get("/users", response_model=AdminUserPage)
def users(q: Optional[str] = None, role: Optional[Literal["user", "seller", "admin"]] = None,
          is_active: Optional[bool] = None, page: int = PageQ, page_size: int = SizeQ,
          _=Admin, db=Depends(get_db)):
    return admin_service.list_users(db, q, role, is_active, page, page_size)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def set_user_active(user_id: str, body: UserActiveUpdate, admin=Admin, db=Depends(get_db)):
    return admin_service.set_user_active(db, admin, user_id, body.is_active)


@router.get("/sellers", response_model=AdminSellerPage)
def sellers(status: Optional[Literal["pending", "approved", "rejected", "suspended"]] = None,
            page: int = PageQ, page_size: int = SizeQ, _=Admin, db=Depends(get_db)):
    return admin_service.list_sellers(db, status, page, page_size)


@router.patch("/sellers/{user_id}", response_model=AdminSellerOut)
def set_seller_status(user_id: str, body: SellerStatusUpdate, admin=Admin, db=Depends(get_db)):
    return admin_service.set_seller_status(db, admin, user_id, body.status)


# ---- verification (NID is masked; the document is audit-logged) ----
@router.get("/verifications", response_model=VerificationReviewPage)
def verifications(status: Optional[Literal["pending", "approved", "rejected"]] = None,
                  page: int = PageQ, page_size: int = SizeQ, _=Admin, db=Depends(get_db)):
    return verification_service.list_records(db, status, page, page_size)


@router.get("/verifications/{record_id}/document")
def verification_document(record_id: str, admin=Admin, db=Depends(get_db)):
    return verification_service.document_response(db, admin, record_id)


@router.patch("/verifications/{record_id}", response_model=VerificationReviewOut)
def decide_verification(record_id: str, body: VerificationDecision, admin=Admin, db=Depends(get_db)):
    return verification_service.review(db, admin, record_id, body.decision, body.note)


# ---- moderation ----
@router.get("/products", response_model=ProductModerationPage)
def products(q: Optional[str] = None, moderation_status: Optional[Literal["visible", "hidden"]] = None,
             page: int = PageQ, page_size: int = SizeQ, _=Admin, db=Depends(get_db)):
    return admin_service.list_products(db, q, moderation_status, page, page_size)


@router.patch("/products/{product_id}", response_model=ProductModerationOut)
def moderate_product(product_id: str, body: ProductModerationUpdate, admin=Admin, db=Depends(get_db)):
    return admin_service.moderate_product(db, admin, product_id, body.moderation_status)


@router.get("/rentals", response_model=RentalModerationPage)
def rentals(q: Optional[str] = None, status: Optional[Literal["active", "inactive", "removed"]] = None,
            page: int = PageQ, page_size: int = SizeQ, _=Admin, db=Depends(get_db)):
    return admin_service.list_rental_listings(db, q, status, page, page_size)


@router.patch("/rentals/{listing_id}", response_model=RentalModerationOut)
def moderate_rental(listing_id: str, body: RentalModerationUpdate, admin=Admin, db=Depends(get_db)):
    return admin_service.moderate_rental(db, admin, listing_id, body.status)


# ---- taxonomy ----
@router.get("/categories")
def categories(_=Admin, db=Depends(get_db)):
    return admin_service.list_taxonomy(db)


@router.post("/categories", status_code=201)
def create_category(body: CategoryCreate, admin=Admin, db=Depends(get_db)):
    return admin_service.create_category(db, admin, body)


@router.put("/categories/{slug}")
def update_category(slug: str, body: CategoryUpdate, admin=Admin, db=Depends(get_db)):
    return admin_service.update_category(db, admin, slug, body)


@router.delete("/categories/{slug}", status_code=204)
def delete_category(slug: str, admin=Admin, db=Depends(get_db)):
    admin_service.delete_category(db, admin, slug)


@router.post("/subcategories", status_code=201)
def create_subcategory(body: SubcategoryCreate, admin=Admin, db=Depends(get_db)):
    return admin_service.create_subcategory(db, admin, body)


@router.put("/subcategories/{slug}")
def update_subcategory(slug: str, body: SubcategoryUpdate, admin=Admin, db=Depends(get_db)):
    return admin_service.update_subcategory(db, admin, slug, body)


@router.delete("/subcategories/{slug}", status_code=204)
def delete_subcategory(slug: str, admin=Admin, db=Depends(get_db)):
    admin_service.delete_subcategory(db, admin, slug)


# ---- complaints ----
@router.get("/complaints", response_model=ComplaintAdminPage)
def complaints(status: Optional[Literal["open", "in_review", "resolved", "dismissed"]] = None,
               target_type: Optional[Literal["order", "seller", "rental"]] = None,
               page: int = PageQ, page_size: int = SizeQ, _=Admin, db=Depends(get_db)):
    return complaint_service.list_all(db, status, target_type, page, page_size)


@router.patch("/complaints/{complaint_id}", response_model=ComplaintAdminOut)
def update_complaint(complaint_id: str, body: ComplaintUpdate, admin=Admin, db=Depends(get_db)):
    return complaint_service.update(db, admin, complaint_id, body)


# ---- scraping monitor ----
@router.get("/scraping/status")
def scraping_status(_=Admin, db=Depends(get_db)):
    return admin_service.scraping_status(db)


@router.get("/scraping/runs")
def scraping_runs(store: Optional[str] = None, page: int = PageQ, page_size: int = SizeQ,
                  _=Admin, db=Depends(get_db)):
    return admin_service.scraping_runs(db, store, page, page_size)


@router.post("/scraping/refresh/{store}")
def scraping_refresh(store: str, admin=Admin, db=Depends(get_db)):
    return admin_service.refresh_store_now(db, admin, store)


# ---- audit ----
@router.get("/audit", response_model=AuditPage)
def audit(action: Optional[str] = Query(None, max_length=60), actor_id: Optional[str] = None,
          page: int = PageQ, page_size: int = SizeQ, _=Admin, db=Depends(get_db)):
    return audit_service.list_logs(db, page, page_size, action, actor_id)



# ---- reviews ----
@router.get("/reviews", response_model=ReviewAdminPage)
def admin_reviews(status: Optional[Literal["visible", "hidden"]] = None, page: int = PageQ, page_size: int = SizeQ,
                  _=Admin, db=Depends(get_db)):
    return review_service.list_all(db, status, page, page_size)


@router.patch("/reviews/{review_id}", response_model=ReviewAdmin)
def moderate_review(review_id: str, body: ReviewModeration, admin=Admin, db=Depends(get_db)):
    return review_service.moderate(db, admin, review_id, body.status)


# ---- returns ----
@router.get("/returns", response_model=ReturnStaffPage)
def admin_returns(status: Optional[Literal["requested", "approved", "rejected", "completed", "cancelled"]] = None,
                  page: int = PageQ, page_size: int = SizeQ, _=Admin, db=Depends(get_db)):
    return return_service.list_all(db, status, page, page_size)


@router.patch("/returns/{return_id}", response_model=ReturnStaffOut)
def decide_return(return_id: str, body: ReturnDecision, admin=Admin, db=Depends(get_db)):
    return return_service.decide_as_admin(db, admin, return_id, body)
