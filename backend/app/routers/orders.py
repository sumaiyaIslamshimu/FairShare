"""FastAPI endpoints for Checkout and Order Management."""
from fastapi import APIRouter, Depends, Query

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.cart_order import CheckoutRequest, OrderOut, OrderPageOut, SellerOrderStatusUpdate
from app.services import order_service

router = APIRouter(tags=["Orders & Checkout"])


# --- Shopper Endpoints ---
@router.post("/checkout", response_model=OrderOut, status_code=201)
def process_checkout(body: CheckoutRequest, user=Depends(require_role("user")), db=Depends(get_db)):
    return order_service.checkout(db, user, body)


@router.get("/orders", response_model=OrderPageOut)
def get_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user=Depends(require_role("user")),
    db=Depends(get_db)
):
    return order_service.get_shopper_orders(db, user, page, page_size)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(order_id: str, user=Depends(require_role("user")), db=Depends(get_db)):
    return order_service.cancel_shopper_order(db, user, order_id)


# --- Seller Endpoints ---
@router.get("/seller/orders")
def get_seller_order_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    seller=Depends(require_role("seller")),
    db=Depends(get_db)
):
    return order_service.get_seller_orders(db, seller, page, page_size)


@router.patch("/seller/orders/{item_id}/status")
def update_item_status(
    item_id: str,
    body: SellerOrderStatusUpdate,
    seller=Depends(require_role("seller")),
    db=Depends(get_db)
):
    return order_service.update_seller_item_status(db, seller, item_id, body.status)