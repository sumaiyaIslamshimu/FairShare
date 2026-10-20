from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Response

from app.core.deps import require_approved_seller, require_role
from app.db.mongo import get_db
from app.models.seller_product import (InventoryUpdate, OwnerProductPage, SellerProductCreate, SellerProductOwner,
                                       SellerProductPage, SellerProductPublic)
from app.services import product_service

router = APIRouter(tags=["Seller products"])


# ---------- public (approved sellers, active listings only) ----------
@router.get("/seller-products", response_model=SellerProductPage)
def browse(
    q: str = Query("", max_length=100),
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    sort: Literal["price_asc", "price_desc", "newest"] = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db=Depends(get_db),
):
    return product_service.list_public(db, q, category, subcategory, sort, page, page_size)


@router.get("/seller-products/{product_id}", response_model=SellerProductPublic)
def detail(product_id: str, db=Depends(get_db)):
    return product_service.get_public(db, product_id)


# ---------- seller (owner only) ----------
@router.post("/seller/products", response_model=SellerProductOwner, status_code=201)
def create(body: SellerProductCreate, seller=Depends(require_approved_seller), db=Depends(get_db)):
    return product_service.create_product(db, seller, body)


@router.get("/seller/products", response_model=OwnerProductPage)
def my_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    seller=Depends(require_role("seller")),
    db=Depends(get_db),
):
    return product_service.list_own(db, seller, page, page_size)


@router.put("/seller/products/{product_id}", response_model=SellerProductOwner)
def update(product_id: str, body: SellerProductCreate, seller=Depends(require_approved_seller), db=Depends(get_db)):
    return product_service.update_product(db, seller, product_id, body)


@router.delete("/seller/products/{product_id}", status_code=204)
def remove(product_id: str, seller=Depends(require_approved_seller), db=Depends(get_db)):
    product_service.remove_product(db, seller, product_id)
    return Response(status_code=204)


@router.patch("/seller/products/{product_id}/inventory", response_model=SellerProductOwner)
def inventory(product_id: str, body: InventoryUpdate, seller=Depends(require_approved_seller), db=Depends(get_db)):
    return product_service.set_inventory(db, seller, product_id, body.stock_qty)