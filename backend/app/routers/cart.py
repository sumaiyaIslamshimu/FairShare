"""FastAPI endpoints for the Shopper Cart."""
from fastapi import APIRouter, Depends, Response

from app.core.deps import require_role
from app.db.mongo import get_db
from app.models.cart_order import CartItemIn, CartItemUpdateIn, CartOut
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartOut)
def get_cart(user=Depends(require_role("user")), db=Depends(get_db)):
    return cart_service.get_cart(db, user)


@router.post("/items", response_model=CartOut)
def add_to_cart(body: CartItemIn, user=Depends(require_role("user")), db=Depends(get_db)):
    return cart_service.add_item(db, user, body)


@router.put("/items/{product_id}", response_model=CartOut)
def update_cart_item(product_id: str, body: CartItemUpdateIn, user=Depends(require_role("user")), db=Depends(get_db)):
    return cart_service.update_item(db, user, product_id, body.quantity)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_cart_item(product_id: str, user=Depends(require_role("user")), db=Depends(get_db)):
    return cart_service.remove_item(db, user, product_id)


@router.delete("", status_code=204)
def clear_cart(user=Depends(require_role("user")), db=Depends(get_db)):
    cart_service.clear_cart(db, user)
    return Response(status_code=204)