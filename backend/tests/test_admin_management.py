"""Users, sellers, moderation, category management (acceptance 4) and the audit viewer."""
from bson import ObjectId

from tests.helpers_m2 import SELLER_BODY, approved_seller, create_product
from tests.helpers_m4 import approve_seller


# ---------- users ----------
def test_list_search_and_suspend_user(client, db, make_account, admin_headers):
    user, h = make_account(email="target@example.com")
    make_account(email="other@example.com")
    r = client.get("/api/admin/users?q=target", headers=admin_headers).json()
    assert r["total"] == 1 and r["items"][0]["email"] == "target@example.com"
    assert client.get("/api/admin/users?role=seller", headers=admin_headers).json()["total"] == 0
    assert client.patch(f"/api/admin/users/{user['id']}", json={"is_active": False}, headers=admin_headers
                        ).json()["is_active"] is False
    assert client.get("/api/auth/me", headers=h).status_code == 403          # takes effect immediately
    assert client.post("/api/auth/login", json={"email": "target@example.com", "password": "Password123"}
                       ).status_code == 403
    client.patch(f"/api/admin/users/{user['id']}", json={"is_active": True}, headers=admin_headers)
    assert client.get("/api/auth/me", headers=h).status_code == 200
    actions = [e["action"] for e in db.audit_logs.find({})]
    assert actions.count("user.suspend") == 1 and actions.count("user.activate") == 1


def test_admin_cannot_suspend_self_or_other_admins_or_unknown(client, db, admin_headers):
    from app.db.seed import seed_admin
    seed_admin(db, "second@example.com", "AdminPass123")
    me = db.users.find_one({"email": "admin@example.com"})
    other = db.users.find_one({"email": "second@example.com"})
    assert client.patch(f"/api/admin/users/{me['_id']}", json={"is_active": False}, headers=admin_headers
                        ).status_code == 409
    assert client.patch(f"/api/admin/users/{other['_id']}", json={"is_active": False}, headers=admin_headers
                        ).status_code == 403
    assert client.patch(f"/api/admin/users/{ObjectId()}", json={"is_active": False}, headers=admin_headers
                        ).status_code == 404
    assert client.patch("/api/admin/users/not-an-id", json={"is_active": False}, headers=admin_headers
                        ).status_code == 404


# ---------- sellers ----------
def test_seller_cannot_be_approved_before_identity_is_verified(client, db, make_account, admin_headers):
    seller, _ = make_account(email="s@example.com", role="seller")
    r = client.patch(f"/api/admin/sellers/{seller['id']}", json={"status": "approved"}, headers=admin_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "SELLER_NOT_VERIFIED"
    db.users.update_one({"_id": ObjectId(seller["id"])}, {"$set": {"verification_status": "approved"}})
    ok = client.patch(f"/api/admin/sellers/{seller['id']}", json={"status": "approved"}, headers=admin_headers)
    assert ok.status_code == 200 and ok.json()["status"] == "approved"
    sus = client.patch(f"/api/admin/sellers/{seller['id']}", json={"status": "suspended"}, headers=admin_headers)
    assert sus.json()["status"] == "suspended"
    assert client.get("/api/admin/sellers?status=suspended", headers=admin_headers).json()["total"] == 1


def test_suspended_seller_cannot_publish_and_products_leave_the_shop(client, db, make_account, admin_headers):
    seller, hs = approved_seller(make_account, db)
    approve_seller(db, seller["id"])
    create_product(client, hs)
    assert client.get("/api/seller-products").json()["total"] == 1
    client.patch(f"/api/admin/sellers/{seller['id']}", json={"status": "suspended"}, headers=admin_headers)
    assert client.post("/api/seller/products", json=SELLER_BODY, headers=hs).status_code == 403
    assert client.get("/api/seller-products").json()["total"] == 0


# ---------- product moderation ----------
def test_hidden_product_disappears_from_shop_and_cannot_be_bought(client, db, make_account, admin_headers):
    seller, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    _, hu = make_account(email="buyer@example.com")
    assert client.post("/api/cart/items", json={"seller_product_id": product["id"], "quantity": 1}, headers=hu
                       ).status_code in (200, 201)
    r = client.patch(f"/api/admin/products/{product['id']}", json={"moderation_status": "hidden"},
                     headers=admin_headers)
    assert r.status_code == 200 and r.json()["moderation_status"] == "hidden"
    assert client.get("/api/seller-products").json()["total"] == 0
    assert client.get("/api/admin/products?moderation_status=hidden", headers=admin_headers).json()["total"] == 1
    # the item already sitting in a cart can no longer be checked out
    cart = client.get("/api/cart", headers=hu).json()
    assert cart["items"] == []
    out = client.post("/api/checkout", json={"shipping_address": "Road 1, Dhaka", "phone": "+8801700000000"}, headers=hu)
    assert out.status_code >= 400
    client.patch(f"/api/admin/products/{product['id']}", json={"moderation_status": "visible"}, headers=admin_headers)
    assert client.get("/api/seller-products").json()["total"] == 1


def test_removed_product_is_soft_deleted(client, db, make_account, admin_headers):
    _, hs = approved_seller(make_account, db)
    product = create_product(client, hs)
    r = client.patch(f"/api/admin/products/{product['id']}", json={"moderation_status": "removed"},
                     headers=admin_headers)
    assert r.json()["status"] == "removed"
    assert client.get("/api/admin/products", headers=admin_headers).json()["total"] == 0
    assert db.seller_products.find_one({"_id": ObjectId(product["id"])}) is not None  # kept for order history
    assert client.patch(f"/api/admin/products/{product['id']}", json={"moderation_status": "visible"},
                        headers=admin_headers).status_code == 404
    assert client.patch(f"/api/admin/products/{product['id']}", json={"moderation_status": "weird"},
                        headers=admin_headers).status_code == 422


def test_rental_listing_moderation_is_separate_from_shopping(client, db, make_account, admin_headers):
    owner, ho = make_account(email="o@example.com")
    db.users.update_one({"_id": ObjectId(owner["id"])}, {"$set": {"verification_status": "approved"}})
    lid = client.post("/api/rentals/listings", json={"title": "Tent", "daily_rate_paisa": 50000,
                                                     "location": "Dhaka"}, headers=ho).json()["id"]
    assert client.get("/api/rentals/listings").json()["total"] == 1
    r = client.patch(f"/api/admin/rentals/{lid}", json={"status": "removed"}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["status"] == "removed"
    assert client.get("/api/rentals/listings").json()["total"] == 0
    assert client.get("/api/admin/rentals", headers=admin_headers).json()["total"] == 0
    assert client.get("/api/admin/products", headers=admin_headers).json()["total"] == 0


# ---------- categories ----------
def test_taxonomy_list_includes_usage_counts(client, make_account, db, admin_headers):
    _, hs = approved_seller(make_account, db)
    create_product(client, hs)
    tree = client.get("/api/admin/categories", headers=admin_headers).json()
    assert len(tree) == 6
    groceries = next(c for c in tree if c["slug"] == "groceries-food")
    assert groceries["in_use"] == 1 and sum(s["in_use"] for s in groceries["subcategories"]) == 1


def test_category_crud_and_slug_rules(client, admin_headers):
    r = client.post("/api/admin/categories", json={"slug": "pet-supplies", "name": "Pet Supplies"},
                    headers=admin_headers)
    assert r.status_code == 201 and r.json()["is_active"] is True
    assert client.post("/api/admin/categories", json={"slug": "pet-supplies", "name": "Again"},
                       headers=admin_headers).status_code == 409
    for bad in ("Pet Supplies", "pet_supplies", "-pet", "x"):
        assert client.post("/api/admin/categories", json={"slug": bad, "name": "Bad slug"},
                           headers=admin_headers).status_code == 422
    up = client.put("/api/admin/categories/pet-supplies", json={"name": "Pets"}, headers=admin_headers)
    assert up.json()["name"] == "Pets" and up.json()["slug"] == "pet-supplies"
    sub = client.post("/api/admin/subcategories", json={"slug": "dog-food", "category_slug": "pet-supplies",
                                                        "name": "Dog Food"}, headers=admin_headers)
    assert sub.status_code == 201
    assert client.post("/api/admin/subcategories", json={"slug": "x-y", "category_slug": "nope", "name": "Nope"},
                       headers=admin_headers).status_code == 422
    # the public taxonomy and seller validation see the new pair
    pub = client.get("/api/categories").json()
    assert any(c["slug"] == "pet-supplies" and c["subcategories"][0]["slug"] == "dog-food" for c in pub)
    assert client.delete("/api/admin/categories/pet-supplies", headers=admin_headers).status_code == 409  # has a sub
    assert client.delete("/api/admin/subcategories/dog-food", headers=admin_headers).status_code == 204
    assert client.delete("/api/admin/categories/pet-supplies", headers=admin_headers).status_code == 204
    assert client.delete("/api/admin/categories/pet-supplies", headers=admin_headers).status_code == 404


def test_in_use_category_cannot_be_deleted_or_deactivated(client, db, make_account, admin_headers):
    _, hs = approved_seller(make_account, db)
    create_product(client, hs)  # groceries-food / rice-pulses-grains
    r = client.put("/api/admin/categories/groceries-food", json={"is_active": False}, headers=admin_headers)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CATEGORY_IN_USE"
    assert client.delete("/api/admin/categories/groceries-food", headers=admin_headers).status_code == 409
    s = client.put("/api/admin/subcategories/rice-pulses-grains", json={"is_active": False}, headers=admin_headers)
    assert s.status_code == 409
    assert client.delete("/api/admin/subcategories/rice-pulses-grains", headers=admin_headers).status_code == 409
    # nothing changed: sellers can still use it
    assert db.categories.find_one({"slug": "groceries-food"})["is_active"] is True
    assert client.post("/api/seller/products", json=SELLER_BODY, headers=hs).status_code == 201


def test_unused_category_can_be_deactivated_and_shopping_stays_consistent(client, db, make_account, admin_headers):
    _, hs = approved_seller(make_account, db)
    r = client.put("/api/admin/categories/groceries-food", json={"is_active": False}, headers=admin_headers)
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert all(c["slug"] != "groceries-food" for c in client.get("/api/categories").json())
    bad = client.post("/api/seller/products", json=SELLER_BODY, headers=hs)
    assert bad.status_code == 422 and bad.json()["error"]["code"] == "INVALID_CATEGORY"
    client.put("/api/admin/categories/groceries-food", json={"is_active": True}, headers=admin_headers)
    assert client.post("/api/seller/products", json=SELLER_BODY, headers=hs).status_code == 201


def test_external_products_also_protect_a_category(client, db, admin_headers):
    from tests.helpers_m2 import make_ext, save_ext
    save_ext(db, make_ext())  # maps to a taxonomy category
    used = db.external_products.find_one({})
    assert used.get("category_slug")
    r = client.delete(f"/api/admin/categories/{used['category_slug']}", headers=admin_headers)
    assert r.status_code == 409


# ---------- audit ----------
def test_audit_log_lists_admin_actions_newest_first_with_filter(client, db, make_account, admin_headers):
    user, _ = make_account(email="t@example.com")
    client.patch(f"/api/admin/users/{user['id']}", json={"is_active": False}, headers=admin_headers)
    client.post("/api/admin/categories", json={"slug": "pet-supplies", "name": "Pet Supplies"}, headers=admin_headers)
    r = client.get("/api/admin/audit", headers=admin_headers).json()
    assert r["total"] == 2 and r["items"][0]["action"] == "category.create"
    assert r["items"][0]["actor_email"] == "admin@example.com"
    only = client.get("/api/admin/audit?action=user.", headers=admin_headers).json()
    assert only["total"] == 1 and only["items"][0]["action"] == "user.suspend"
    assert client.get("/api/admin/audit?page_size=1", headers=admin_headers).json()["items"].__len__() == 1
    assert client.get("/api/admin/audit?page_size=1000", headers=admin_headers).status_code == 422


def test_stats_are_real_counts(client, db, make_account, admin_headers):
    make_account(email="u@example.com")
    make_account(email="s@example.com", role="seller")
    st = client.get("/api/admin/stats", headers=admin_headers).json()
    assert st["users"]["total"] == 3 and st["users"]["shoppers"] == 1 and st["users"]["sellers"] == 1
    assert st["sellers"]["pending"] == 1 and st["orders"]["total"] == 0 and st["complaints"]["total"] == 0