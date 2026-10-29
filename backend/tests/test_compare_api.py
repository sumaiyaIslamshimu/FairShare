from tests.helpers_m2 import approved_seller, create_product, make_ext, save_ext


def _seed_three(db):
    save_ext(
        db,
        make_ext(store="daraz", name="Pran Miniket Rice 5 kg", price="৳ 700"),
        make_ext(store="chaldal", name="Teer Soybean Oil 1 L", brand="Teer", price="৳ 190", category_text="Cooking Oil"),
        make_ext(store="daraz", name="Sony Headphones WH 100", brand="Sony", price="৳ 5,000", category_text="Headphones"),
    )


def test_search_filters_sort_and_pagination(client, db):
    _seed_three(db)
    get = lambda qs: client.get("/api/compare/search" + qs).json()
    assert get("?q=rice")["total"] == 1
    assert [i["store"] for i in get("?store=chaldal")["items"]] == ["chaldal"]
    assert get("?category=groceries-food")["total"] == 2
    assert get("?subcategory=headphones-speakers")["total"] == 1
    assert get("?sort=price_asc")["items"][0]["price_paisa"] == 19000
    assert get("?sort=price_desc")["items"][0]["price_paisa"] == 500000
    p1, p2 = get("?page_size=2&page=1"), get("?page_size=2&page=2")
    assert p1["total"] == 3 and len(p1["items"]) == 2 and len(p2["items"]) == 1
    r = client.get("/api/compare/search?store=nope")
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_STORE"


def test_search_includes_fairshare_listings(client, db, make_account):
    _seed_three(db)
    _, h = approved_seller(make_account, db)
    create_product(client, h)
    all_items = client.get("/api/compare/search?q=rice").json()["items"]
    assert {i["source"] for i in all_items} == {"external", "fairshare"}
    only = client.get("/api/compare/search?store=fairshare").json()["items"]
    assert len(only) == 1 and only[0]["store_url"] is None and only[0]["store_name"] == "FairShare"


def test_group_exact_possible_and_cheapest(client, db, make_account):
    save_ext(db,
             make_ext(store="daraz", price="৳ 700"),
             make_ext(store="chaldal", price="৳ 650"),
             make_ext(store="agora", name="Pran Miniket Rice 1 kg", price="৳ 150"))
    _, h = approved_seller(make_account, db)
    create_product(client, h, price_paisa=68000)
    key = db.external_products.find_one({"store": "daraz"})["group_key"]

    g = client.get(f"/api/compare/groups/{key}").json()
    assert len(g["exact"]) == 3
    best = next(i for i in g["exact"] if i["id"] == g["cheapest_id"])
    assert best["store"] == "chaldal"
    possible = {p["item"]["name"]: p for p in g["possible"]}
    assert "Pran Miniket Rice 1 kg" in possible
    assert any(d["field"] == "package_size" for d in possible["Pran Miniket Rice 1 kg"]["differences"])

    # a stale price can never be the verified "cheapest"
    db.external_products.update_one({"store": "chaldal"}, {"$set": {"freshness": "stale"}})
    g2 = client.get(f"/api/compare/groups/{key}").json()
    assert next(i for i in g2["exact"] if i["id"] == g2["cheapest_id"])["store"] == "fairshare"


def test_group_not_found_and_search_reports_group_size(client, db):
    assert client.get("/api/compare/groups/doesnotexist").status_code == 404
    save_ext(db, make_ext(store="daraz"), make_ext(store="chaldal", price="৳ 650"))
    items = client.get("/api/compare/search?q=rice").json()["items"]
    assert all(i["group_size"] == 2 and i["group_key"] for i in items)


def test_sources_endpoint_is_honest(client, db):
    from app.scrapers import get_scraper
    from app.scrapers.base import FetchError, Fetcher
    from app.scrapers.runner import refresh_all

    class NoNetwork(Fetcher):   # nothing may reach a real site from a test; robots.txt becomes unreadable -> unsupported
        def get(self, url):
            raise FetchError("network", "no network in tests")

    r = client.get("/api/compare/sources").json()
    assert len(r) == 6 and all(s["status"] == "never_run" and s["configured"] is get_scraper(s["store"]).configured for s in r)
    refresh_all(db, fetcher=NoNetwork())
    r = client.get("/api/compare/sources").json()
    assert all(s["status"] == "unsupported" for s in r)