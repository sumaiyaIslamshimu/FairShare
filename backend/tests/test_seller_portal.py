"""Stage 1 & Stage 2 tests: M3 model contracts and Seller Portal endpoints."""
from datetime import date, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models.cart_order import CartItemIn, OrderStatus, SELLER_ALLOWED_TRANSITIONS
from app.models.message import MessageCreateIn
from app.models.rental import RentalListingCreate, RentalRequestCreate
from app.models.seller import PromotionCreate, SellerProfileUpdate


def test_stage1_promotion_model_bounds_and_dates():
    now = datetime.now(timezone.utc)
    valid = PromotionCreate(
        product_ids=["507f1f77bcf86cd799439011"],
        discount_percent=25,
        starts_at=now,
        ends_at=now + timedelta(days=3),
    )
    assert valid.discount_percent == 25
    assert len(valid.product_ids) == 1

    # Discount < 1 or > 90 is rejected
    with pytest.raises(ValidationError):
        PromotionCreate(
            product_ids=["507f1f77bcf86cd799439011"],
            discount_percent=0,
            starts_at=now,
            ends_at=now + timedelta(days=1),
        )
    with pytest.raises(ValidationError):
        PromotionCreate(
            product_ids=["507f1f77bcf86cd799439011"],
            discount_percent=95,
            starts_at=now,
            ends_at=now + timedelta(days=1),
        )

    # ends_at <= starts_at is rejected
    with pytest.raises(ValidationError):
        PromotionCreate(
            product_ids=["507f1f77bcf86cd799439011"],
            discount_percent=15,
            starts_at=now,
            ends_at=now - timedelta(hours=1),
        )


def test_stage1_seller_profile_update_validates_phone():
    ok = SellerProfileUpdate(business_name="Dhaka Mart", contact_phone="+8801711223344")
    assert ok.business_name == "Dhaka Mart"
    with pytest.raises(ValidationError):
        SellerProfileUpdate(contact_phone="bad-phone-!!!")


def test_stage1_cart_ignores_client_price_and_seller_id():
    item = CartItemIn(
        seller_product_id="507f1f77bcf86cd799439011",
        quantity=2,
        price_paisa=1,
        seller_id="spoofed_seller",
    )
    dumped = item.model_dump()
    assert "price_paisa" not in dumped
    assert "seller_id" not in dumped
    assert dumped["seller_product_id"] == "507f1f77bcf86cd799439011"
    assert dumped["quantity"] == 2


def test_stage1_order_transitions_contract():
    assert SELLER_ALLOWED_TRANSITIONS[OrderStatus.confirmed.value] == OrderStatus.shipped.value
    assert SELLER_ALLOWED_TRANSITIONS[OrderStatus.shipped.value] == OrderStatus.delivered.value
    assert OrderStatus.delivered.value not in SELLER_ALLOWED_TRANSITIONS


def test_stage1_message_normalizes_body_and_recipient():
    msg = MessageCreateIn(recipient_id="507f1f77bcf86cd799439012", content="  Hello seller!  ")
    assert msg.body == "Hello seller!"
    with pytest.raises(ValidationError):
        MessageCreateIn(recipient_id="507f1f77bcf86cd799439012", body="   ")


def test_stage1_rental_models_validate_dates_and_no_taxonomy():
    listing = RentalListingCreate(
        title="DSLR Camera Kit",
        description="Canon body + 50mm lens",
        daily_rate_paisa=150000,
        deposit_paisa=500000,
        location="Banani, Dhaka",
    )
    assert listing.daily_rate_paisa == 150000
    assert "category_slug" not in listing.model_dump()

    req = RentalRequestCreate(start_date=date(2026, 11, 1), end_date=date(2026, 11, 5))
    assert req.end_date >= req.start_date

    with pytest.raises(ValidationError):
        RentalRequestCreate(start_date=date(2026, 11, 10), end_date=date(2026, 11, 5))


# --- STAGE 2 API TESTS ---
from bson import ObjectId
from tests.helpers_m2 import approved_seller, create_product


def test_stage2_seller_profile_read_and_update(client, db, make_account):
    user, h = approved_seller(make_account, db)

    # Read Profile
    res = client.get("/api/seller/profile", headers=h)
    assert res.status_code == 200
    assert res.json()["business_name"] == "Test Store"
    assert res.json()["status"] == "approved"

    # Update Profile
    update = client.put("/api/seller/profile", json={"contact_phone": "+8801912345678", "address": "Block C"},
                        headers=h)
    assert update.status_code == 200
    assert update.json()["contact_phone"] == "+8801912345678"
    assert update.json()["address"] == "Block C"


def test_stage2_create_promotion_verifies_ownership(client, db, make_account):
    user, h = approved_seller(make_account, db)
    prod = create_product(client, h)

    now = datetime.now(timezone.utc)
    promo_data = {
        "name": "Eid Sale",
        "product_ids": [prod["id"]],
        "discount_percent": 15,
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=7)).isoformat()
    }

    # Create successful
    res = client.post("/api/seller/promotions", json=promo_data, headers=h)
    assert res.status_code == 201
    assert res.json()["discount_percent"] == 15
    assert res.json()["product_ids"] == [prod["id"]]

    # Create fails for product owned by someone else
    bad_id = str(ObjectId())
    res_bad = client.post("/api/seller/promotions", json={**promo_data, "product_ids": [bad_id]}, headers=h)
    assert res_bad.status_code == 403
    assert res_bad.json()["error"]["code"] == "FORBIDDEN"


def test_stage2_seller_insights_aggregation(client, db, make_account):
    user, h = approved_seller(make_account, db)
    p1 = create_product(client, h, title="Item 1", price_paisa=1000)
    p2 = create_product(client, h, title="Item 2", stock_qty=3)  # Low stock

    db.order_items.insert_one({
        "order_id": ObjectId(),
        "seller_id": ObjectId(user["id"]),
        "seller_product_id": ObjectId(p1["id"]),
        "title_snapshot": "Item 1",
        "unit_price_paisa": 1000,
        "quantity": 2,
        "line_total_paisa": 2000,
        "item_status": "confirmed"
    })

    res = client.get("/api/seller/insights", headers=h)
    assert res.status_code == 200
    data = res.json()
    assert data["total_products"] == 2
    assert data["total_revenue_paisa"] == 2000
    assert data["total_units_sold"] == 2
    assert data["orders_by_status"]["confirmed"] == 1
    assert len(data["low_stock_items"]) == 1
    assert data["low_stock_items"][0]["id"] == p2["id"]