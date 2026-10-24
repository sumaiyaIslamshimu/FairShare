"""Business logic for Checkout and Order Fulfillment."""
from typing import Any

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.models.cart_order import OrderStatus, SELLER_ALLOWED_TRANSITIONS
from app.services.cart_service import clear_cart, get_cart
from app.services.time_utils import iso, utcnow
from app.services import notification_service

def _generate_order_number(user_id: str) -> str:
    now = utcnow()
    return f"ORD-{now.strftime('%y%m%d')}-{user_id[-6:].upper()}"


def serialize_order_item(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "order_id": str(doc["order_id"]),
        "seller_id": str(doc["seller_id"]),
        "seller_product_id": str(doc["seller_product_id"]),
        "title_snapshot": doc["title_snapshot"],
        "unit_price_paisa": doc["unit_price_paisa"],
        "quantity": doc["quantity"],
        "line_total_paisa": doc["line_total_paisa"],
        "item_status": doc["item_status"],
    }


def serialize_order(db, doc: dict) -> dict:
    items = db.order_items.find({"order_id": doc["_id"]})
    return {
        "id": str(doc["_id"]),
        "order_number": doc["order_number"],
        "user_id": str(doc["user_id"]),
        "status": doc["status"],
        "subtotal_paisa": doc.get("subtotal_paisa", 0),
        "total_paisa": doc.get("total_paisa", 0),
        "currency": doc.get("currency", "BDT"),
        "payment": doc.get("payment", {"mode": "simulated", "status": "paid"}),
        "shipping_address": doc["shipping_address"],
        "phone": doc.get("phone"),
        "notes": doc.get("notes"),
        "items": [serialize_order_item(i) for i in items],
        "created_at": iso(doc.get("created_at")),
        "updated_at": iso(doc.get("updated_at"))
    }


def _reserve_stock(db, items: list[dict]) -> list[tuple]:
    """Takes stock for every item with ONE conditional update each (stock_qty >= quantity), so two checkouts
    racing for the last units can never both succeed. If any item fails, everything already taken is given back."""
    taken: list[tuple] = []
    for item in items:
        pid = to_object_id(item["seller_product_id"], "Product")
        res = db.seller_products.update_one({"_id": pid, "stock_qty": {"$gte": item["quantity"]}},
                                            {"$inc": {"stock_qty": -item["quantity"]}})
        if res.modified_count != 1:
            _release_stock(db, taken)
            raise AppError(409, "OUT_OF_STOCK", f"Not enough stock for {item['title']}.")
        taken.append((pid, item["quantity"]))
    return taken


def _release_stock(db, taken: list[tuple]) -> None:
    for pid, qty in taken:
        db.seller_products.update_one({"_id": pid}, {"$inc": {"stock_qty": qty}})


def checkout(db, user: dict, data) -> dict:
    cart = get_cart(db, user)
    if not cart["items"]:
        raise AppError(400, "CART_EMPTY", "Your cart is empty.")

    # 1. Quick check against the cart view, for a clear message (the real guard is the reservation in step 2).
    for item in cart["items"]:
        if item["quantity"] > item["stock_qty"]:
            raise AppError(409, "OUT_OF_STOCK", f"Not enough stock for {item['title']}. Available: {item['stock_qty']}")

    # 2. Reserve the stock atomically BEFORE anything else is written.
    taken = _reserve_stock(db, cart["items"])
    now = utcnow()
    try:
        # 3. Create the master Order
        order_doc = {
            "user_id": user["_id"],
            "order_number": _generate_order_number(str(user["_id"])),
            "status": OrderStatus.pending.value,
            "subtotal_paisa": cart["subtotal_paisa"],
            "total_paisa": cart["total_paisa"],
            "payment": {"mode": "simulated", "status": "paid"},
            "shipping_address": data.shipping_address,
            "phone": data.phone,
            "notes": data.notes,
            "created_at": now,
            "updated_at": now
        }
        order_id = db.orders.insert_one(order_doc).inserted_id

        # 4. Snapshot prices and create the order items (stock was already taken in step 2)
        for item in cart["items"]:
            db.order_items.insert_one({
                "order_id": order_id,
                "seller_id": to_object_id(item["seller_id"], "Seller"),
                "seller_product_id": to_object_id(item["seller_product_id"], "Product"),
                "title_snapshot": item["title"],
                "unit_price_paisa": item["effective_price_paisa"],
                "quantity": item["quantity"],
                "line_total_paisa": item["line_total_paisa"],
                "item_status": OrderStatus.confirmed.value,
            })
    except Exception:
        # Could not finish the order: give the stock back and remove any half-written order.
        _release_stock(db, taken)
        if "order_id" in locals():
            db.order_items.delete_many({"order_id": order_id})
            db.orders.delete_one({"_id": order_id})
        raise

    # 5. Clear the cart
    clear_cart(db, user)

    # 6. Tell each seller they have a new order
    for seller_id in {to_object_id(i["seller_id"], "Seller") for i in cart["items"]}:
        notification_service.notify(db, seller_id, "order", "You have a new order",
                                    f"Order {order_doc['order_number']} includes your items.", "orders")

    return serialize_order(db, db.orders.find_one({"_id": order_id}))


def get_shopper_orders(db, user: dict, page: int, page_size: int) -> dict:
    flt = {"user_id": user["_id"]}
    total = db.orders.count_documents(flt)
    cur = db.orders.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    return {
        "items": [serialize_order(db, d) for d in cur],
        "total": total,
        "page": page,
        "page_size": page_size
    }


def cancel_shopper_order(db, user: dict, order_id: str) -> dict:
    order = db.orders.find_one({"_id": to_object_id(order_id, "Order")})
    if not order or order["user_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Order not found.")

    if order["status"] not in [OrderStatus.pending.value, OrderStatus.confirmed.value]:
        raise AppError(403, "CANNOT_CANCEL", "Order cannot be cancelled at this stage.")

    db.orders.update_one({"_id": order["_id"]},
                         {"$set": {"status": OrderStatus.cancelled.value, "updated_at": utcnow()}})

    # Also cancel all line items
    db.order_items.update_many({"order_id": order["_id"]}, {"$set": {"item_status": OrderStatus.cancelled.value}})

    # Restore stock
    items = db.order_items.find({"order_id": order["_id"]})
    for item in items:
        db.seller_products.update_one(
            {"_id": item["seller_product_id"]},
            {"$inc": {"stock_qty": item["quantity"]}}
        )

    return serialize_order(db, db.orders.find_one({"_id": order["_id"]}))


def get_seller_orders(db, seller: dict, page: int, page_size: int) -> dict:
    # Sellers view OrderItems that belong to them, grouped conceptually or just listed.
    # For M3, we list the order items specifically assigned to this seller.
    flt = {"seller_id": seller["_id"]}
    total = db.order_items.count_documents(flt)
    cur = db.order_items.find(flt).sort("_id", -1).skip((page - 1) * page_size).limit(page_size)

    return {
        "items": [serialize_order_item(d) for d in cur],
        "total": total,
        "page": page,
        "page_size": page_size
    }


def update_seller_item_status(db, seller: dict, item_id: str, new_status: str) -> dict:
    item = db.order_items.find_one({"_id": to_object_id(item_id, "OrderItem")})
    if not item or item["seller_id"] != seller["_id"]:
        raise AppError(404, "NOT_FOUND", "Order item not found.")

    current_status = item.get("item_status")
    allowed_next = SELLER_ALLOWED_TRANSITIONS.get(current_status)

    if new_status != allowed_next:
        raise AppError(403, "INVALID_TRANSITION", f"Cannot move from {current_status} to {new_status}.")

    db.order_items.update_one({"_id": item["_id"]}, {"$set": {"item_status": new_status}})
    order = db.orders.find_one({"_id": item["order_id"]})
    if order:
        notification_service.notify(db, order["user_id"], "order", f"Your item is now {new_status}",
                                    f"{item['title_snapshot']} (order {order['order_number']})", "orders")
    return serialize_order_item(db.order_items.find_one({"_id": item["_id"]}))