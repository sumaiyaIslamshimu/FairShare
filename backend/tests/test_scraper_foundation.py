"""Tests for the scraper base + normalizer. Uses fake fetchers and constructed HTML only:
NO live websites, NO database. Constructed HTML is NOT proof that any real store works."""
import json

from app.scrapers.base import (BaseScraper, FetchError, FetchResponse, Fetcher, ParseOutcome, RawProduct,
                               RobotsChecker, ScrapeStatus, extract_jsonld_products, jsonld_product_to_raw)
from app.scrapers.normalizer import (InvalidProduct, canonical_url, detect_currency, normalize_availability,
                                     normalize_product, parse_price_to_paisa, parse_quantity_unit)


# ---------- fakes ----------
class FakeFetcher(Fetcher):
    """routes: url -> FetchResponse | FetchError (raised). Records every URL requested."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url):
        self.calls.append(url)
        item = self.routes.get(url)
        if item is None:
            raise FetchError("not_found", "no route", 404)
        if isinstance(item, FetchError):
            raise item
        return item


def page(html, ctype="text/html; charset=utf-8"):
    return FetchResponse(200, html, ctype, "")


class DemoScraper(BaseScraper):
    store = "demo"
    base_url = "https://shop.test"

    def search_url(self, query, page=1):
        return f"https://shop.test/search?q={query}&page={page}"

    def parse_listing(self, html, page_url):
        raws = [jsonld_product_to_raw(self.store, n) for n in extract_jsonld_products(html)]
        good = [r for r in raws if r.name and r.price is not None]
        return ParseOutcome(products=good, skipped=len(raws) - len(good))


def ld(*products):
    return "<html><script type='application/ld+json'>" + json.dumps(list(products)) + "</script></html>"


def product(name="Rice 1kg", price="120", url="/p/1", cur="BDT", avail="https://schema.org/InStock"):
    return {"@type": "Product", "name": name, "url": url,
            "offers": {"@type": "Offer", "price": price, "priceCurrency": cur, "availability": avail}}


# ---------- price normalization ----------
def test_price_formats():
    assert parse_price_to_paisa("৳ 1,299") == 129900
    assert parse_price_to_paisa("Tk. 12,999.50") == 1299950
    assert parse_price_to_paisa("BDT 1,23,456") == 12345600          # lakh grouping
    assert parse_price_to_paisa("৳ ১,২৯৯") == 129900                 # Bengali digits
    assert parse_price_to_paisa(1299) == 129900
    assert parse_price_to_paisa(99.5) == 9950
    assert parse_price_to_paisa("120.00") == 12000


def test_price_rejects_bad_or_ambiguous_values():
    for bad in [None, "", "free", "0", "-50", 0, -3, True, "৳ 1,000 - ৳ 2,000", "was 1500 now 1200", "N/A"]:
        assert parse_price_to_paisa(bad) is None, bad


def test_currency_only_when_confirmed():
    assert detect_currency("BDT") == "BDT"
    assert detect_currency(None, "৳ 500") == "BDT"
    assert detect_currency(None, "Tk. 500") == "BDT"
    assert detect_currency(None, "500") is None
    assert detect_currency("USD") is None


def test_availability_mapping():
    assert normalize_availability("https://schema.org/InStock") == "in_stock"
    assert normalize_availability("https://schema.org/OutOfStock") == "out_of_stock"
    assert normalize_availability("Sold Out") == "out_of_stock"
    assert normalize_availability("In Stock") == "in_stock"
    assert normalize_availability(None) == "unknown"
    assert normalize_availability("preorder soon") == "unknown"


def test_quantity_units_are_comparable():
    assert parse_quantity_unit("Miniket Rice 1 kg") == (1000.0, "g")
    assert parse_quantity_unit("Miniket Rice 500g") == (500.0, "g")
    assert parse_quantity_unit("Soybean Oil 2 L") == (2000.0, "ml")
    assert parse_quantity_unit("Eggs 12 pcs") == (12.0, "pcs")
    assert parse_quantity_unit("Phone X") is None
    assert parse_quantity_unit("Mix 500g or 1kg option") is None     # ambiguous -> no guess


def test_canonical_url():
    assert canonical_url("/p/1?utm_source=x&color=red#frag", "https://shop.test") == "https://shop.test/p/1?color=red"
    assert canonical_url("javascript:alert(1)") is None
    assert canonical_url("/relative-only") is None
    assert canonical_url(None) is None


# ---------- normalize_product ----------
def raw(**kw):
    base = dict(store="demo", name="Brand Rice 1 kg", product_url="/p/1", price="৳ 120", availability="InStock")
    base.update(kw)
    return RawProduct(**base)


def test_normalize_success_and_discount():
    n = normalize_product(raw(original_price="৳ 150", brand="Brand", rating="4.5", review_count="1,200"),
                          base_url="https://shop.test")
    assert n.price_paisa == 12000 and n.original_price_paisa == 15000 and n.discount_percent == 20.0
    assert n.currency == "BDT" and n.source == "external" and n.availability == "in_stock"
    assert n.product_url == "https://shop.test/p/1" and n.quantity == 1000.0 and n.unit == "g"
    assert n.review_count == 1200 and n.rating == 4.5
    assert n.normalized_key == "brand brand rice 1 kg"


def test_fake_discount_is_ignored():
    n = normalize_product(raw(original_price="৳ 100"), base_url="https://shop.test")  # "original" lower than price
    assert n.original_price_paisa is None and n.discount_percent is None


def test_missing_optional_fields_stay_none():
    n = normalize_product(raw(price="120"), base_url="https://shop.test")
    assert n.currency is None and n.image_url is None and n.rating is None and n.brand is None


def test_required_fields_are_enforced():
    cases = {"missing_name": dict(name="  "), "missing_or_invalid_url": dict(product_url="javascript:void(0)"),
             "missing_or_invalid_price": dict(price="0")}
    for reason, kw in cases.items():
        try:
            normalize_product(raw(**kw), base_url="https://shop.test")
        except InvalidProduct as e:
            assert e.reason == reason
        else:
            raise AssertionError(f"expected InvalidProduct({reason})")


def test_protocol_relative_image():
    n = normalize_product(raw(image_url="//cdn.test/i.jpg"), base_url="https://shop.test")
    assert n.image_url == "https://cdn.test/i.jpg"


# ---------- JSON-LD ----------
def test_jsonld_graph_list_and_malformed():
    html = ("<script type='application/ld+json'>{not json</script>"
            "<script type='application/ld+json'>" + json.dumps({"@graph": [{"@type": "WebSite"}, product("A")]}) + "</script>"
            "<script type='application/ld+json'>" + json.dumps({"@type": "ItemList", "itemListElement": [
                {"@type": "ListItem", "item": product("B")}]}) + "</script>")
    names = sorted(p["name"] for p in extract_jsonld_products(html))
    assert names == ["A", "B"]


def test_jsonld_to_raw_handles_offer_lists_and_images():
    node = product("X")
    node["offers"] = [node["offers"]]
    node["image"] = ["https://i.test/1.jpg", "https://i.test/2.jpg"]
    node["brand"] = {"@type": "Brand", "name": "Acme"}
    node["aggregateRating"] = {"ratingValue": "4.2", "reviewCount": "30"}
    r = jsonld_product_to_raw("demo", node)
    assert r.image_url == "https://i.test/1.jpg" and r.brand == "Acme" and r.rating == "4.2" and r.review_count == "30"


# ---------- scraper.run: status handling ----------
URL = "https://shop.test/search?q=rice&page=1"


def test_run_success():
    f = FakeFetcher({URL: page(ld(product("A"), product("B", url="/p/2")))})
    res = DemoScraper().run("rice", f)
    assert res.status == ScrapeStatus.success and res.items_found == 2 and not res.errors


def test_run_valid_empty_result_is_success_not_error():
    f = FakeFetcher({URL: page("<html><body>No results</body></html>")})
    res = DemoScraper().run("rice", f)
    assert res.status == ScrapeStatus.success and res.items_found == 0
    assert any("valid empty" in n for n in res.notes)


def test_run_partial_when_some_items_unusable():
    f = FakeFetcher({URL: page(ld(product("A"), {"@type": "Product", "name": "No price"}))})
    res = DemoScraper().run("rice", f)
    assert res.status == ScrapeStatus.partial and res.items_found == 1 and res.skipped == 1


def test_run_all_items_unusable_is_failure_with_layout_hint():
    f = FakeFetcher({URL: page(ld({"@type": "Product", "name": "No price"}))})
    res = DemoScraper().run("rice", f)
    assert res.status == ScrapeStatus.failure and any("layout" in e for e in res.errors)


def test_run_blocked_403_is_reported_not_bypassed():
    f = FakeFetcher({URL: FetchError("blocked", "Access refused", 403)})
    res = DemoScraper().run("rice", f)
    assert res.status == ScrapeStatus.failure and res.http_status == 403 and res.items_found == 0
    assert f.calls == [URL]                                  # exactly one attempt, no workaround


def test_run_rate_limit_timeout_and_server_errors():
    for kind, code in [("rate_limited", 429), ("timeout", None), ("server_error", 503), ("not_found", 404)]:
        f = FakeFetcher({URL: FetchError(kind, "x", code)})
        res = DemoScraper().run("rice", f)
        assert res.status == ScrapeStatus.failure and res.errors[0].startswith(kind), kind


def test_run_unexpected_content_type():
    f = FakeFetcher({URL: page("%PDF-1.4", ctype="application/pdf")})
    res = DemoScraper().run("rice", f)
    assert res.status == ScrapeStatus.failure and "content type" in res.errors[0]


def test_run_parser_crash_is_contained():
    class Broken(DemoScraper):
        def parse_listing(self, html, page_url):
            raise ValueError("layout changed")
    f = FakeFetcher({URL: page("<html></html>")})
    res = Broken().run("rice", f)                            # must not raise
    assert res.status == ScrapeStatus.failure and res.errors == ["parse error: ValueError"]


def test_run_limit_is_applied():
    f = FakeFetcher({URL: page(ld(*[product(f"P{i}", url=f"/p/{i}") for i in range(5)]))})
    assert DemoScraper().run("rice", f, limit=3).items_found == 3


# ---------- robots.txt ----------
ROBOTS = "https://shop.test/robots.txt"


def test_robots_disallow_stops_before_fetching_the_page():
    f = FakeFetcher({ROBOTS: page("User-agent: *\nDisallow: /search"), URL: page(ld(product()))})
    res = DemoScraper().run("rice", f, robots=RobotsChecker(f))
    assert res.status == ScrapeStatus.unsupported and res.robots_allowed is False
    assert URL not in f.calls


def test_robots_allow_then_fetch():
    f = FakeFetcher({ROBOTS: page("User-agent: *\nDisallow: /admin"), URL: page(ld(product()))})
    res = DemoScraper().run("rice", f, robots=RobotsChecker(f))
    assert res.status == ScrapeStatus.success and res.robots_allowed is True


def test_robots_missing_404_means_allowed():
    f = FakeFetcher({URL: page(ld(product()))})              # robots.txt route absent -> 404
    assert DemoScraper().run("rice", f, robots=RobotsChecker(f)).status == ScrapeStatus.success


def test_robots_unreadable_is_treated_conservatively():
    f = FakeFetcher({ROBOTS: FetchError("server_error", "x", 503), URL: page(ld(product()))})
    res = DemoScraper().run("rice", f, robots=RobotsChecker(f))
    assert res.status == ScrapeStatus.unsupported and URL not in f.calls