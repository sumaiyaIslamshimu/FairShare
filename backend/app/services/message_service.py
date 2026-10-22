"""Business logic for shared messaging between participants."""
from app.core.errors import AppError
from app.services.time_utils import iso, utcnow


def _make_thread_id(user1: str, user2: str, order_id: str = None, product_id: str = None,
                    request_id: str = None) -> str:
    """Generates a deterministic thread ID based on the participants and context."""
    p1, p2 = sorted([user1, user2])
    ctx = ""
    if order_id:
        ctx = f"_ord_{order_id}"
    elif request_id:
        ctx = f"_req_{request_id}"
    elif product_id:
        ctx = f"_prod_{product_id}"
    return f"thr_{p1}_{p2}{ctx}"


def serialize_message(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "thread_id": doc["thread_id"],
        "customer_id": str(doc.get("customer_id", "")),
        "seller_id": str(doc.get("seller_id", "")),
        "participants": [str(p) for p in doc.get("participants", [])],
        "sender_id": str(doc["sender_id"]),
        "recipient_id": str(doc["recipient_id"]),
        "order_id": str(doc["order_id"]) if doc.get("order_id") else None,
        "product_id": str(doc["product_id"]) if doc.get("product_id") else None,
        "request_id": str(doc["request_id"]) if doc.get("request_id") else None,
        "body": doc["body"],
        "read": doc.get("read", False),
        "created_at": iso(doc["created_at"])
    }


def send_message(db, sender: dict, data) -> dict:
    sender_id = str(sender["_id"])
    recipient_id = data.recipient_id

    if sender_id == recipient_id:
        raise AppError(400, "BAD_REQUEST", "You cannot send a message to yourself.")

    thread_id = _make_thread_id(sender_id, recipient_id, data.order_id, data.product_id, data.request_id)

    # Map customer and seller conceptually based on who is who, but participants array is what secures it
    is_seller = sender["role"] == "seller"
    customer_id = recipient_id if is_seller else sender_id
    seller_id = sender_id if is_seller else recipient_id

    doc = {
        "thread_id": thread_id,
        "participants": [sender_id, recipient_id],
        "customer_id": customer_id,
        "seller_id": seller_id,
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "order_id": data.order_id,
        "product_id": data.product_id,
        "request_id": data.request_id,
        "body": data.body,
        "read": False,
        "created_at": utcnow()
    }

    doc["_id"] = db.messages.insert_one(doc).inserted_id
    return serialize_message(doc)


def get_threads(db, user: dict) -> list[dict]:
    """Returns a summary of all threads for the user."""
    user_id = str(user["_id"])

    # Manual aggregation for mongomock compatibility
    all_msgs = db.messages.find({"participants": user_id}).sort("created_at", 1)

    threads = {}
    for msg in all_msgs:
        tid = msg["thread_id"]
        if tid not in threads:
            threads[tid] = {
                "thread_id": tid,
                "participants": [str(p) for p in msg["participants"]],
                "customer_id": str(msg.get("customer_id", "")),
                "seller_id": str(msg.get("seller_id", "")),
                "order_id": str(msg["order_id"]) if msg.get("order_id") else None,
                "product_id": str(msg["product_id"]) if msg.get("product_id") else None,
                "unread_count": 0,
                "last_message": None
            }

        threads[tid]["last_message"] = serialize_message(msg)
        if not msg.get("read") and str(msg["recipient_id"]) == user_id:
            threads[tid]["unread_count"] += 1

    # Sort by last message time descending
    sorted_threads = sorted(threads.values(), key=lambda t: t["last_message"]["created_at"], reverse=True)
    return sorted_threads


def get_messages(db, user: dict, thread_id: str) -> list[dict]:
    user_id = str(user["_id"])

    # Check access
    first_msg = db.messages.find_one({"thread_id": thread_id})
    if not first_msg:
        return []

    if user_id not in [str(p) for p in first_msg.get("participants", [])]:
        raise AppError(403, "FORBIDDEN", "You do not have access to this thread.")

    # Mark as read
    db.messages.update_many(
        {"thread_id": thread_id, "recipient_id": user_id, "read": False},
        {"$set": {"read": True}}
    )

    msgs = db.messages.find({"thread_id": thread_id}).sort("created_at", 1)
    return [serialize_message(m) for m in msgs]