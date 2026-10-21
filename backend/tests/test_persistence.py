from app.scrapers.persistence import mark_store_stale
from tests.helpers_m2 import make_ext, save_ext


def test_insert_and_price_history(db):
    assert save_ext(db, make_ext())["inserted"] == 1
    doc = db.external_products.find_one({})
    assert doc["price_paisa"] == 70000 and doc["freshness"] == "fresh" and doc["source"] == "external"
    assert db.price_observations.count_documents({}) == 1
    save_ext(db, make_ext())                                   # same price -> no new history row
    assert db.price_observations.count_documents({}) == 1
    stats = save_ext(db, make_ext(price="৳ 650"))
    assert stats["updated"] == 1 and stats["price_changes"] == 1
    assert db.price_observations.count_documents({}) == 2
    assert db.external_products.count_documents({}) == 1       # same product, not duplicated


def test_availability_change_is_recorded(db):
    save_ext(db, make_ext())
    save_ext(db, make_ext(availability="OutOfStock"))
    assert db.price_observations.count_documents({}) == 2
    assert db.external_products.find_one({})["availability"] == "out_of_stock"


def test_duplicate_inside_one_run_is_stored_once(db):
    stats = save_ext(db, make_ext(), make_ext())
    assert stats["inserted"] == 1 and stats["duplicates_in_run"] == 1
    assert db.external_products.count_documents({}) == 1


def test_category_mapping_and_review_flag(db):
    save_ext(db, make_ext(category_text="Rice"), make_ext(name="Mystery Thing", brand=None, category_text="Misc", url="/p/x"))
    ok = db.external_products.find_one({"name": "Pran Miniket Rice 5 kg"})
    assert ok["category_slug"] == "groceries-food" and ok["subcategory_slug"] == "rice-pulses-grains"
    assert ok["category_status"] == "mapped"
    odd = db.external_products.find_one({"name": "Mystery Thing"})
    assert odd["category_slug"] is None and odd["category_status"] == "needs_review"


def test_exact_groups_are_synced(db):
    save_ext(db, make_ext(store="daraz"))
    assert db.product_matches.count_documents({}) == 0            # one product is not a group
    save_ext(db, make_ext(store="chaldal", price="৳ 650"))
    m = db.product_matches.find_one({})
    assert m["match_type"] == "exact" and len(m["external_product_ids"]) == 2
    save_ext(db, make_ext(store="agora", name="Pran Miniket Rice 1 kg", price="৳ 150"))   # other size: separate key
    assert db.product_matches.count_documents({}) == 1
    keys = {d["group_key"] for d in db.external_products.find({})}
    assert len(keys) == 2


def test_mark_store_stale_only_touches_that_store(db):
    save_ext(db, make_ext(store="daraz"), make_ext(store="chaldal"))
    assert mark_store_stale(db, "daraz") == 1
    assert db.external_products.find_one({"store": "daraz"})["freshness"] == "stale"
    assert db.external_products.find_one({"store": "chaldal"})["freshness"] == "fresh"