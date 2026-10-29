import json
from datetime import datetime, timedelta, timezone

from app.scrapers.base import FetchError, FetchResponse, Fetcher, JsonLdSearchScraper
from app.scrapers.runner import refresh_all, refresh_store
from tests.helpers_m2 import make_ext, save_ext

URL = "https://shop.test/s?q=rice&page=1"
URL2 = "https://shop2.test/s?q=rice&page=1"


class Demo(JsonLdSearchScraper):
    store = "daraz"
    base_url = "https://shop.test"
    search_url_template = "https://shop.test/s?q={query}&page={page}"


class Demo2(Demo):
    store = "pickaboo"
    base_url = "https://shop2.test"
    search_url_template = "https://shop2.test/s?q={query}&page={page}"


class Crashing(Demo):
    def run(self, *args, **kwargs):
        raise RuntimeError("boom")


class Routes(Fetcher):
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url):
        self.calls.append(url)
        item = self.routes.get(url)
        if item is None:
            raise FetchError("not_found", "no route", 404)
        if isinstance(item, FetchError):
            raise item
        return item


def ld(*items):
    return "<script type='application/ld+json'>" + json.dumps(list(items)) + "</script>"


def prod(name, price, url):
    return {"@type": "Product", "name": name, "url": url, "offers": {"price": price, "priceCurrency": "BDT"}}


def ok_page(url, *items):
    return FetchResponse(200, ld(*items), "text/html", url)


def test_successful_run_saves_data_and_status(db):
    f = Routes({URL: ok_page(URL, prod("Pran Rice 1 kg", "120", "/p/1"))})
    res = refresh_store(db, "daraz", queries=["rice"], fetcher=f, scraper=Demo())
    assert res["status"] == "success" and res["saved"]["inserted"] == 1
    src = db.scrape_sources.find_one({"store": "daraz"})
    assert src["status"] == "success" and src["last_success_at"] is not None
    run = db.scrape_runs.find_one({"store": "daraz"})
    assert run["status"] == "success" and run["items_found"] == 1


def test_unconfigured_real_adapters_are_unsupported_and_fetch_nothing(db):
    from app.scrapers import all_stores, get_scraper
    unconfigured = [s for s in all_stores() if not get_scraper(s).configured]
    f = Routes({})
    results = [r for r in refresh_all(db, fetcher=f) if r["store"] in unconfigured]
    assert [r["status"] for r in results] == ["unsupported"] * len(unconfigured)
    assert not any("/search" in c for c in f.calls if "daraz" in c or "pickaboo" in c)   # unconfigured: no requests
    assert db.external_products.count_documents({"store": {"$in": unconfigured}}) == 0


def test_failed_refresh_marks_old_data_stale(client, db):
    ok = Routes({URL: ok_page(URL, prod("Pran Rice 1 kg", "120", "/p/1"))})
    refresh_store(db, "daraz", queries=["rice"], fetcher=ok, scraper=Demo())
    assert db.external_products.find_one({})["freshness"] == "fresh"
    first_success = db.scrape_sources.find_one({"store": "daraz"})["last_success_at"]

    blocked = Routes({URL: FetchError("blocked", "Access refused", 403)})
    res = refresh_store(db, "daraz", queries=["rice"], fetcher=blocked, scraper=Demo())
    assert res["status"] == "failure"
    assert blocked.calls == ["https://shop.test/robots.txt", URL]      # one attempt, no workaround
    assert db.external_products.find_one({})["freshness"] == "stale"
    src = db.scrape_sources.find_one({"store": "daraz"})
    assert src["status"] == "failure" and "blocked" in src["last_error"] and src["last_success_at"] == first_success
    assert client.get("/api/compare/search?q=rice").json()["items"][0]["freshness"] == "stale"


def test_one_broken_store_does_not_stop_the_others(db):
    f = Routes({URL2: ok_page(URL2, prod("Teer Oil 1 L", "190", "/p/9"))})
    results = refresh_all(db, stores=["daraz", "pickaboo"], queries=["rice"], fetcher=f,
                          scrapers={"daraz": Crashing(), "pickaboo": Demo2()})
    by = {r["store"]: r for r in results}
    assert by["daraz"]["status"] == "failure" and "runner error: RuntimeError" in by["daraz"]["errors"]
    assert by["pickaboo"]["status"] == "success"
    assert db.external_products.count_documents({"store": "pickaboo"}) == 1


def test_unusable_items_make_the_run_partial(db):
    page = ok_page(URL, prod("Good Rice 1 kg", "120", "/p/1"), prod("Bad Link Rice", "99", "javascript:void(0)"))
    res = refresh_store(db, "daraz", queries=["rice"], fetcher=Routes({URL: page}), scraper=Demo())
    assert res["status"] == "partial" and res["invalid_items"] == 1 and res["saved"]["inserted"] == 1
    assert db.scrape_sources.find_one({"store": "daraz"})["status"] == "partial"


def test_old_successful_data_is_stale_by_age(client, db):
    save_ext(db, make_ext())
    db.external_products.update_one({}, {"$set": {"last_successful_at": datetime.now(timezone.utc) - timedelta(days=5)}})
    assert client.get("/api/compare/search").json()["items"][0]["freshness"] == "stale"