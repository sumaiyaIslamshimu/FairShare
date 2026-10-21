"""Business logic for Rentals (Listings, Requests, Bookings, History)."""
from typing import Any, Optional

from app.core.errors import AppError
from app.db.mongo import to_object_id
from app.models.rental import RentalBookingStatus, RentalEventType, RentalListingStatus, RentalRequestStatus
from app.services.time_utils import iso, utcnow


def _require_verified(user: dict):
    if user.get("verification_status") != "approved":
        raise AppError(403, "UNVERIFIED_USER", "You must be a verified user to participate in rentals.")


def _date_str(value) -> Optional[str]:
    """Calendar dates are stored as 'YYYY-MM-DD' strings (BSON cannot store datetime.date)."""
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _log_event(db, actor_id: str, event_type: str, listing_id: str, request_id: str = None, booking_id: str = None,
               details: dict = None):
    doc = {
        "listing_id": to_object_id(listing_id, "Listing"),
        "actor_id": to_object_id(actor_id, "User"),
        "event_type": event_type,
        "details": details or {},
        "created_at": utcnow()
    }
    if request_id:
        doc["request_id"] = to_object_id(request_id, "Request")
    if booking_id:
        doc["booking_id"] = to_object_id(booking_id, "Booking")
    db.rental_events.insert_one(doc)


def serialize_listing(db, doc: dict) -> dict:
    owner = db.users.find_one({"_id": doc["owner_id"]})
    return {
        "id": str(doc["_id"]),
        "owner_id": str(doc["owner_id"]),
        "owner_name": owner.get("full_name", "Unknown") if owner else "Unknown",
        "title": doc["title"],
        "description": doc.get("description", ""),
        "daily_rate_paisa": doc["daily_rate_paisa"],
        "deposit_paisa": doc["deposit_paisa"],
        "currency": doc.get("currency", "BDT"),
        "location": doc["location"],
        "images": doc.get("images", []),
        "status": doc.get("status", "active"),
        "available_from": _date_str(doc.get("available_from")),
        "available_to": _date_str(doc.get("available_to")),
        "created_at": iso(doc.get("created_at")),
        "updated_at": iso(doc.get("updated_at"))
    }


def create_listing(db, user: dict, data) -> dict:
    _require_verified(user)
    now = utcnow()
    doc = {
        "owner_id": user["_id"],
        "title": data.title,
        "description": data.description,
        "daily_rate_paisa": data.daily_rate_paisa,
        "deposit_paisa": data.deposit_paisa,
        "currency": "BDT",
        "location": data.location,
        "images": data.images,
        "status": data.status,
        # Stored as 'YYYY-MM-DD' strings: real MongoDB rejects datetime.date objects.
        "available_from": _date_str(data.available_from),
        "available_to": _date_str(data.available_to),
        "created_at": now,
        "updated_at": now
    }
    listing_id = db.rental_listings.insert_one(doc).inserted_id
    _log_event(db, str(user["_id"]), RentalEventType.LISTING_CREATED.value, str(listing_id))
    return serialize_listing(db, db.rental_listings.find_one({"_id": listing_id}))


def list_public_rentals(db, page: int, page_size: int) -> dict:
    flt = {"status": RentalListingStatus.active.value}
    total = db.rental_listings.count_documents(flt)
    cur = db.rental_listings.find(flt).sort("created_at", -1).skip((page - 1) * page_size).limit(page_size)
    return {
        "items": [serialize_listing(db, d) for d in cur],
        "total": total,
        "page": page,
        "page_size": page_size
    }


def serialize_request(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "listing_id": str(doc["listing_id"]),
        "owner_id": str(doc["owner_id"]),
        "renter_id": str(doc["renter_id"]),
        "start_date": _date_str(doc["start_date"]),
        "end_date": _date_str(doc["end_date"]),
        "days": doc["days"],
        "daily_rate_paisa": doc["daily_rate_paisa"],
        "deposit_paisa": doc["deposit_paisa"],
        "total_paisa": doc["total_paisa"],
        "status": doc["status"],
        "note": doc.get("note"),
        "booking_id": str(doc["booking_id"]) if doc.get("booking_id") else None,
        "created_at": iso(doc.get("created_at")),
        "updated_at": iso(doc.get("updated_at"))
    }


def check_date_overlap(db, listing_id: Any, start_date, end_date):
    """Returns True if there is an active booking overlapping the requested dates."""
    # Dates are compared as 'YYYY-MM-DD' strings, which sort correctly in mongomock and MongoDB.
    s_str = _date_str(start_date)
    e_str = _date_str(end_date)

    overlapping = db.rental_bookings.find_one({
        "listing_id": listing_id,
        "status": {"$in": [RentalBookingStatus.confirmed.value, RentalBookingStatus.active.value]},
        "start_date": {"$lte": e_str},
        "end_date": {"$gte": s_str}
    })
    return bool(overlapping)


def submit_request(db, user: dict, data) -> dict:
    _require_verified(user)
    listing = db.rental_listings.find_one({"_id": to_object_id(data.listing_id, "Listing")})
    if not listing or listing.get("status") != RentalListingStatus.active.value:
        raise AppError(404, "NOT_FOUND", "Listing not found or inactive.")

    if listing["owner_id"] == user["_id"]:
        raise AppError(400, "BAD_REQUEST", "You cannot rent your own item.")

    start_str = _date_str(data.start_date)
    end_str = _date_str(data.end_date)

    # The requested dates must fall inside the owner's availability window, when one is set.
    window_from = _date_str(listing.get("available_from"))
    window_to = _date_str(listing.get("available_to"))
    if (window_from and start_str < window_from) or (window_to and end_str > window_to):
        raise AppError(400, "OUTSIDE_AVAILABILITY", "The requested dates are outside the listing's availability.")

    if check_date_overlap(db, listing["_id"], start_str, end_str):
        raise AppError(409, "DATE_OVERLAP", "These dates are already booked by someone else.")

    days = (data.end_date - data.start_date).days + 1
    # Total = rental days x daily rate + refundable deposit (all integer paisa).
    total_paisa = (days * listing["daily_rate_paisa"]) + listing["deposit_paisa"]

    now = utcnow()
    doc = {
        "listing_id": listing["_id"],
        "owner_id": listing["owner_id"],
        "renter_id": user["_id"],
        "start_date": start_str,
        "end_date": end_str,
        "days": days,
        "daily_rate_paisa": listing["daily_rate_paisa"],
        "deposit_paisa": listing["deposit_paisa"],
        "total_paisa": total_paisa,
        "status": RentalRequestStatus.pending.value,
        "note": data.note,
        "created_at": now,
        "updated_at": now
    }

    req_id = db.rental_requests.insert_one(doc).inserted_id
    _log_event(db, str(user["_id"]), RentalEventType.REQUEST_CREATED.value, str(listing["_id"]), str(req_id))
    return serialize_request(db.rental_requests.find_one({"_id": req_id}))


def process_request(db, user: dict, request_id: str, action: str) -> dict:
    """Owner accepts or rejects a rental request."""
    req = db.rental_requests.find_one({"_id": to_object_id(request_id, "Request")})
    # A non-owner gets 404 so the request's existence is not revealed.
    if not req or req["owner_id"] != user["_id"]:
        raise AppError(404, "NOT_FOUND", "Request not found.")

    if req["status"] != RentalRequestStatus.pending.value:
        raise AppError(400, "BAD_REQUEST", "This request is no longer pending.")

    now = utcnow()
    if action == "reject":
        db.rental_requests.update_one({"_id": req["_id"]},
                                      {"$set": {"status": RentalRequestStatus.rejected.value, "updated_at": now}})
        _log_event(db, str(user["_id"]), RentalEventType.REQUEST_REJECTED.value, str(req["listing_id"]),
                   str(req["_id"]))
        return serialize_request(db.rental_requests.find_one({"_id": req["_id"]}))

    # Action is accept
    if check_date_overlap(db, req["listing_id"], req["start_date"], req["end_date"]):
        # Auto-reject if dates were taken while this request was pending.
        db.rental_requests.update_one({"_id": req["_id"]},
                                      {"$set": {"status": RentalRequestStatus.rejected.value, "updated_at": now}})
        _log_event(db, str(user["_id"]), RentalEventType.REQUEST_REJECTED.value, str(req["listing_id"]),
                   str(req["_id"]), details={"reason": "date_overlap"})
        raise AppError(409, "DATE_OVERLAP", "Dates are no longer available. Request auto-rejected.")

    # Create booking
    booking = {
        "request_id": req["_id"],
        "listing_id": req["listing_id"],
        "owner_id": req["owner_id"],
        "renter_id": req["renter_id"],
        "start_date": req["start_date"],
        "end_date": req["end_date"],
        "days": req["days"],
        "daily_rate_paisa": req["daily_rate_paisa"],
        "deposit_paisa": req["deposit_paisa"],
        "total_paisa": req["total_paisa"],
        "status": RentalBookingStatus.confirmed.value,
        "created_at": now,
        "updated_at": now
    }
    booking_id = db.rental_bookings.insert_one(booking).inserted_id
    db.rental_requests.update_one(
        {"_id": req["_id"]},
        {"$set": {"status": RentalRequestStatus.accepted.value, "booking_id": booking_id, "updated_at": now}}
    )

    _log_event(db, str(user["_id"]), RentalEventType.REQUEST_ACCEPTED.value, str(req["listing_id"]), str(req["_id"]),
               str(booking_id))
    _log_event(db, str(user["_id"]), RentalEventType.BOOKING_CREATED.value, str(req["listing_id"]), str(req["_id"]),
               str(booking_id))

    return serialize_request(db.rental_requests.find_one({"_id": req["_id"]}))