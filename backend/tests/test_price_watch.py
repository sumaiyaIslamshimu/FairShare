"""Price tracking: who can watch what, the alert rules, privacy, limits."""
from bson import ObjectId

from app.scrapers.persistence import save_normalized
from app.services import watch_service
from tests.helpers_m2 import approved_seller, create_product, make_ext, save_ext


def ext_product(db, price="৳ 700"):
    save_ext(db, make_ext(price=price))
    return db.external_products.find_one({})


def watch(client, h, source, pid, target=None):
    body = {"source": source, "product_id": str(pid)}
    if target is not None:
        body["target_price_paisa"] = target
    return client.post("/api/watches", json=body, headers=h)


def notes(client, h):
    return [n for n in client.get("/api/notifications", headers=h).json()["items"] if n["kind"] == "price"]


def test_watch_an_external_offer_and_see_current_price(client, db, make_account):
    _, hu = make_account()
    p = ext_product(db)
    r = watch(client, hu, "external", p["_id"])
    assert r.status_code == 201
    w = r.json()
    assert w["price_when_added_paisa"] == 70000 and w["current_price_paisa"] == 70000
    assert w["status"] == "unchanged" and w["store_url"]
    assert client.get("/api/watches", headers=hu).json()["total"] == 1
    assert client.get("/api/watches/refs", headers=hu).json()[0]["product_id"] == str(p["_id"])


def test_cannot_watch_twice_or_something_missing_or_with_a_target_above_the_price(client, db, make_account):
    _, hu = make_account()
    p = ext_product(db)
    assert watch(client, hu, "external", p["_id"]).status_code == 201
    assert watch(client, hu, "external", p["_id"]).status_code == 409
    assert watch(client, hu, "external", ObjectId()).status_code == 404
    other = make_ext(name="Another Rice 2 kg", price="৳ 300")
    save_ext(db, other)
    p2 = db.external_products.find_one({"name": "Another Rice 2 kg"})
    assert watch(client, hu, "external", p2["_id"], target=30000).status_code == 422
    assert watch(client, hu, "external", p2["_id"], target=0).status_code == 422


def test_an_external_price_drop_sends_one_alert_and_a_rise_sends_none(client, db, make_account):
    _, hu = make_account()
    p = ext_product(db, "৳ 700")
    watch(client, hu, "external", p["_id"])
    save_ext(db, make_ext(price="৳ 800"))           # price rose
    assert notes(client, hu) == []
    save_ext(db, make_ext(price="৳ 650"))           # price dropped
    got = notes(client, hu)
    assert len(got) == 1 and got[0]["link"] == "pricewatch"
    save_ext(db, make_ext(price="৳ 650"))           # unchanged: no second alert
    assert len(notes(client, hu)) == 1
    w = client.get("/api/watches", headers=hu).json()["items"][0]
    assert w["current_price_paisa"] == 65000 and w["lowest_seen_paisa"] == 65000 and w["status"] == "dropped"
    assert w["change_paisa"] == -5000


def test_with_a_target_only_the_crossing_alerts(client, db, make_account):
    _, hu = make_account()
    p = ext_product(db, "৳ 700")
    watch(client, hu, "external", p["_id"], target=60000)
    save_ext(db, make_ext(price="৳ 650"))           # dropped but still above the target
    assert notes(client, hu) == []
    save_ext(db, make_ext(price="৳ 590"))           # crosses the target
    assert len(notes(client, hu)) == 1
    save_ext(db, make_ext(price="৳ 580"))           # already below the target: no repeat
    assert len(notes(client, hu)) == 1
    assert client.get("/api/watches", headers=hu).json()["items"][0]["status"] == "target_reached"


def test_fairshare_price_change_by_the_seller_alerts_the_watcher(client, db, make_account):
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs, price_paisa=70000)
    _, hu = make_account(email="shopper@example.com")
    assert watch(client, hu, "fairshare", product["id"]).status_code == 201
    body = {k: product[k] for k in ("title", "description", "brand", "category_slug", "subcategory_slug", "stock_qty")}
    body.update(price_paisa=60000, images=product["images"], status="active")
    assert client.put(f"/api/seller/products/{product['id']}", json=body, headers=hs).status_code == 200
    got = notes(client, hu)
    assert len(got) == 1
    w = client.get("/api/watches", headers=hu).json()["items"][0]
    assert w["current_price_paisa"] == 60000 and w["store_name"] == "FairShare" and w["store_url"] is None
    assert client.get(f"/api/watches/{w['id']}/history", headers=hu).json() == {"available": False, "points": []}


def test_hidden_fairshare_product_cannot_be_tracked_and_becomes_unavailable(client, db, make_account, admin_headers):
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    _, hu = make_account(email="shopper@example.com")
    watch(client, hu, "fairshare", product["id"])
    client.patch(f"/api/admin/products/{product['id']}", json={"moderation_status": "hidden"}, headers=admin_headers)
    w = client.get("/api/watches", headers=hu).json()["items"][0]
    assert w["status"] == "unavailable" and w["current_price_paisa"] is None
    _, hu2 = make_account(email="two@example.com")
    assert watch(client, hu2, "fairshare", product["id"]).status_code == 404


def test_history_target_edit_and_remove(client, db, make_account):
    _, hu = make_account()
    p = ext_product(db, "৳ 700")
    wid = watch(client, hu, "external", p["_id"]).json()["id"]
    save_ext(db, make_ext(price="৳ 650"))
    hist = client.get(f"/api/watches/{wid}/history", headers=hu).json()
    assert hist["available"] is True and [pt["price_paisa"] for pt in hist["points"]] == [70000, 65000]
    up = client.patch(f"/api/watches/{wid}", json={"target_price_paisa": 60000}, headers=hu)
    assert up.status_code == 200 and up.json()["target_price_paisa"] == 60000
    assert client.patch(f"/api/watches/{wid}", json={"target_price_paisa": 65000}, headers=hu).status_code == 422
    assert client.patch(f"/api/watches/{wid}", json={}, headers=hu).json()["target_price_paisa"] is None
    assert client.delete(f"/api/watches/{wid}", headers=hu).status_code == 204
    assert client.get("/api/watches", headers=hu).json()["total"] == 0


def test_privacy_and_roles(client, db, make_account):
    _, hu = make_account()
    _, other = make_account(email="other@example.com")
    _, hs = approved_seller(make_account, db)
    p = ext_product(db)
    wid = watch(client, hu, "external", p["_id"]).json()["id"]
    assert client.get("/api/watches", headers=other).json()["total"] == 0
    for call in (lambda: client.get(f"/api/watches/{wid}/history", headers=other),
                 lambda: client.patch(f"/api/watches/{wid}", json={}, headers=other),
                 lambda: client.delete(f"/api/watches/{wid}", headers=other)):
        assert call().status_code == 404
    assert client.get("/api/watches", headers=hs).status_code == 403   # sellers cannot track
    assert client.get("/api/watches").status_code == 401
    assert notes(client, other) == []


def test_limit_and_a_failing_alert_never_breaks_the_price_update(client, db, make_account, monkeypatch):
    _, hu = make_account()
    monkeypatch.setattr(watch_service, "MAX_WATCHES", 1)
    p = ext_product(db, "৳ 700")
    assert watch(client, hu, "external", p["_id"]).status_code == 201
    save_ext(db, make_ext(name="Second Rice 1 kg", price="৳ 100"))
    p2 = db.external_products.find_one({"name": "Second Rice 1 kg"})
    assert watch(client, hu, "external", p2["_id"]).status_code == 409
    monkeypatch.setattr(watch_service, "notification_service", None)  # makes every alert blow up
    stats = save_normalized(db, [make_ext(price="৳ 600")])
    assert stats["price_changes"] == 1
    assert db.external_products.find_one({"_id": p["_id"]})["price_paisa"] == 60000



# ---- promotions move a FairShare price too, even when the seller edits nothing on the product ----
def _promo(client, hs, product, percent=20, start=None, end=None, **extra):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    body = {"name": "Sale", "product_ids": [product["id"]], "discount_percent": percent,
            "starts_at": (start or now - timedelta(hours=1)).isoformat(), "ends_at": (end or now + timedelta(days=3)).isoformat(), **extra}
    return client.post("/api/seller/promotions", json=body, headers=hs)


def test_creating_a_promotion_alerts_the_watcher_once(client, db, make_account):
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs, price_paisa=100000)
    _, hu = make_account(email="shopper@example.com")
    assert watch(client, hu, "fairshare", product["id"]).status_code == 201
    assert _promo(client, hs, product, 20).status_code == 201
    assert len(notes(client, hu)) == 1
    w = client.get("/api/watches", headers=hu).json()["items"][0]
    assert w["current_price_paisa"] == 80000
    assert len(notes(client, hu)) == 1            # opening the list again does not repeat the alert


def test_a_promotion_that_starts_later_alerts_when_it_begins(client, db, make_account):
    from datetime import datetime, timedelta, timezone
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs, price_paisa=100000)
    _, hu = make_account(email="shopper@example.com")
    watch(client, hu, "fairshare", product["id"])
    soon = datetime.now(timezone.utc) + timedelta(hours=2)
    assert _promo(client, hs, product, 30, start=soon, end=soon + timedelta(days=1)).status_code == 201
    assert notes(client, hu) == []                # not started yet: nothing to say
    db.promotions.update_one({}, {"$set": {"starts_at": datetime.now(timezone.utc) - timedelta(minutes=1)}})  # time passes
    client.get("/api/watches", headers=hu)
    assert len(notes(client, hu)) == 1
    assert client.get("/api/watches", headers=hu).json()["items"][0]["current_price_paisa"] == 70000


def test_an_ended_promotion_is_not_an_alert_and_a_deeper_one_later_is(client, db, make_account):
    from datetime import datetime, timedelta, timezone
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs, price_paisa=100000)
    _, hu = make_account(email="shopper@example.com")
    _promo(client, hs, product, 20)
    watch(client, hu, "fairshare", product["id"])                     # starts watching at 80000
    db.promotions.update_one({}, {"$set": {"ends_at": datetime.now(timezone.utc) - timedelta(minutes=1)}})
    client.get("/api/watches", headers=hu)                            # price went back UP to 100000: no alert
    assert notes(client, hu) == []
    assert client.get("/api/watches", headers=hu).json()["items"][0]["current_price_paisa"] == 100000
    _promo(client, hs, product, 10)                                   # 90000 is a drop from 100000
    assert len(notes(client, hu)) == 1


def test_deactivating_or_deleting_a_promotion_is_never_an_alert(client, db, make_account):
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs, price_paisa=100000)
    promo = _promo(client, hs, product, 20).json()
    _, hu = make_account(email="shopper@example.com")
    watch(client, hu, "fairshare", product["id"])
    assert client.put(f"/api/seller/promotions/{promo['id']}", json={"is_active": False}, headers=hs).status_code == 200
    assert notes(client, hu) == []
    assert client.delete(f"/api/seller/promotions/{promo['id']}", headers=hs).status_code in (200, 204)
    assert notes(client, hu) == []


def test_a_promotion_with_a_target_only_alerts_when_it_reaches_the_target(client, db, make_account):
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs, price_paisa=100000)
    _, hu = make_account(email="shopper@example.com")
    watch(client, hu, "fairshare", product["id"], target=70000)
    _promo(client, hs, product, 10)                                   # 90000: a drop, but above the target
    assert notes(client, hu) == []
    _promo(client, hs, product, 40)                                   # 60000: crosses the target
    assert len(notes(client, hu)) == 1