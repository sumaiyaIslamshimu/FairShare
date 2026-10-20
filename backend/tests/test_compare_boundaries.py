from bson import ObjectId

from tests.helpers_m2 import make_ext, save_ext


def test_compare_routes_are_read_only(client):
    paths = client.get("/openapi.json").json()["paths"]
    compare_paths = [p for p in paths if p.startswith("/api/compare")]
    assert compare_paths
    for path in compare_paths:
        assert set(paths[path]) == {"get"}, path


def test_external_products_have_no_stock_cart_or_owner_fields(db):
    save_ext(db, make_ext())
    doc = db.external_products.find_one({})
    assert not ({"stock_qty", "cart", "seller_id", "status"} & set(doc))
    assert doc["source"] == "external" and doc["product_url"].startswith("http")


def test_external_id_is_not_a_fairshare_product(client, db):
    save_ext(db, make_ext())
    ext_id = str(db.external_products.find_one({})["_id"])
    assert client.get(f"/api/seller-products/{ext_id}").status_code == 404
    assert client.get(f"/api/seller-products/{ObjectId()}").status_code == 404


def test_every_external_result_has_a_store_link(client, db):
    save_ext(db, make_ext(), make_ext(store="chaldal", price="৳ 650"))
    items = client.get("/api/compare/search").json()["items"]
    assert items and all(i["source"] == "external" and i["store_url"].startswith("http") for i in items)