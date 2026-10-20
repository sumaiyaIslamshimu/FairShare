import pytest

from app.core.errors import AppError
from app.services.category_service import validate_category_pair

SIX = {"fashion-accessories", "electronics-gadgets", "home-household",
       "groceries-food", "books-stationery", "sports-fitness"}


def test_api_returns_the_six_required_categories(client):
    r = client.get("/api/categories")
    assert r.status_code == 200
    data = r.json()
    assert {c["slug"] for c in data} == SIX
    assert all(len(c["subcategories"]) >= 4 for c in data)
    assert sum(len(c["subcategories"]) for c in data) == 43


def test_valid_pair_passes(db):
    validate_category_pair(db, "electronics-gadgets", "smartphones-tablets")


@pytest.mark.parametrize("cat,sub", [
    ("electronics-gadgets", "shoes-footwear"),   # subcategory belongs elsewhere
    ("made-up-category", "smartphones-tablets"), # unknown category
    ("electronics-gadgets", "made-up-sub"),      # unknown subcategory
])
def test_invalid_pairs_rejected(db, cat, sub):
    with pytest.raises(AppError) as exc:
        validate_category_pair(db, cat, sub)
    assert exc.value.status_code == 422 and exc.value.code == "INVALID_CATEGORY"


def test_inactive_category_is_hidden_and_invalid(client, db):
    db.categories.update_one({"slug": "sports-fitness"}, {"$set": {"is_active": False}})
    slugs = {c["slug"] for c in client.get("/api/categories").json()}
    assert "sports-fitness" not in slugs
    with pytest.raises(AppError):
        validate_category_pair(db, "sports-fitness", "football-cricket-equipment")


def test_seeding_twice_does_not_duplicate(db):
    from app.db.seed import seed_categories
    seed_categories(db)
    assert db.categories.count_documents({}) == 6
    assert db.subcategories.count_documents({}) == 43


def test_old_subcategories_are_deactivated_on_reseed(db):
    from app.db.seed import seed_categories
    db.subcategories.insert_one({"slug": "shoes", "category_slug": "fashion-accessories", "name": "Shoes", "is_active": True})
    seed_categories(db)
    assert db.subcategories.find_one({"slug": "shoes"})["is_active"] is False