"""Business logic for the shopping cart. Computes prices dynamically."""
from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.services.product_service import effective_price


def _get_cart_doc(db, user_id: str) -> dict:
    cart = db.carts.find_one({"user_id": user_id})
    if not cart:
        cart = {"user_id": user_id, "items": []}
        db.carts.insert_one(cart)
    return cart


def get_cart(db, user: dict) -> dict:
    cart = _get_cart_doc(db, str(user["_id"]))
    items_out = []
    subtotal = 0
    total_items = 0

    for item in cart["items"]:
        pid_str = item["seller_product_id"]
        try:
            prod = db.seller_products.find_one({"_id": to_object_id(pid_str, "Product")})
        except AppError:
            prod = None

        # Silently drop items that were removed, deactivated, or hidden by an admin (Member 4 fix:
        # checkout reads this view, so a hidden or inactive product can no longer be bought).
        if (not prod or prod.get("status") != "active"
                or prod.get("moderation_status", "visible") != "visible"):
            continue

        price, pct = effective_price(db, prod)
        qty = item["quantity"]
        line_total = price * qty

        items_out.append({
            "seller_product_id": pid_str,
            "seller_id": str(prod["seller_id"]),
            "title": prod["title"],
            "price_paisa": prod["price_paisa"],
            "unit_price_paisa": prod["price_paisa"],
            "effective_price_paisa": price,
            "discount_percent": pct,
            "quantity": qty,
            "stock_qty": prod.get("stock_qty", 0),
            "line_total_paisa": line_total,
            "images": prod.get("images", []),
            "currency": prod.get("currency", "BDT"),
        })
        subtotal += line_total
        total_items += qty

    return {
        "user_id": str(user["_id"]),
        "items": items_out,
        "total_items": total_items,
        "subtotal_paisa": subtotal,
        "total_paisa": subtotal,
        "currency": "BDT",
    }


def add_item(db, user: dict, data) -> dict:
    pid = data.seller_product_id

    # 1. Strict Isolation Check: Is it an external product?
    try:
        obj_id = to_object_id(pid, "Product")
    except AppError:
        raise AppError(404, "NOT_FOUND", "Product not found.")

    is_external = db.external_products.find_one({"_id": obj_id})
    if is_external:
        raise AppError(400, "NOT_A_FAIRSHARE_PRODUCT", "External comparison products cannot be added to the cart.")

    prod = db.seller_products.find_one({"_id": obj_id})
    if not prod or prod.get("status") != "active":
        raise AppError(404, "NOT_FOUND", "Product is not available for purchase.")

    # 2. Add or update quantity in DB
    cart = _get_cart_doc(db, str(user["_id"]))
    existing = next((i for i in cart["items"] if i["seller_product_id"] == pid), None)

    if existing:
        new_qty = existing["quantity"] + data.quantity
        db.carts.update_one(
            {"user_id": str(user["_id"]), "items.seller_product_id": pid},
            {"$set": {"items.$.quantity": new_qty}}
        )
    else:
        db.carts.update_one(
            {"user_id": str(user["_id"])},
            {"$push": {"items": {"seller_product_id": pid, "quantity": data.quantity}}}
        )

    return get_cart(db, user)


def update_item(db, user: dict, product_id: str, quantity: int) -> dict:
    db.carts.update_one(
        {"user_id": str(user["_id"]), "items.seller_product_id": product_id},
        {"$set": {"items.$.quantity": quantity}}
    )
    return get_cart(db, user)


def remove_item(db, user: dict, product_id: str) -> dict:
    db.carts.update_one(
        {"user_id": str(user["_id"])},
        {"$pull": {"items": {"seller_product_id": product_id}}}
    )
    return get_cart(db, user)


def clear_cart(db, user: dict) -> dict:
    db.carts.update_one(
        {"user_id": str(user["_id"])},
        {"$set": {"items": []}}
    )
    return get_cart(db, user)