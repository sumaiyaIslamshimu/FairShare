import json

from app.scrapers import SCRAPERS, all_stores, get_scraper
from app.scrapers.base import (FetchError, FetchResponse, Fetcher, JsonLdSearchScraper, RobotsChecker, ScrapeStatus)

SIX = ["daraz", "pickaboo", "chaldal", "shwapno", "agora", "rokomari"]


class CountingFetcher(Fetcher):
    def __init__(self, routes=None):
        self.routes, self.calls = routes or {}, []

    def get(self, url):
        self.calls.append(url)
        item = self.routes.get(url)
        if item is None:
            raise FetchError("not_found", "x", 404)
        if isinstance(item, FetchError):
            raise item
        return item


def test_six_separate_adapters_exist():
    assert sorted(all_stores()) == sorted(SIX)
    assert len({type(s) for s in SCRAPERS.values()}) == 6          # six distinct classes, one per store
    for store in SIX:
        assert get_scraper(store).store == store


def test_unconfigured_adapters_report_unsupported_and_make_no_requests():
    f = CountingFetcher()
    for store in [s for s in SIX if not get_scraper(s).configured]:   # configured stores are tested in their own file
        res = get_scraper(store).run("rice", f, robots=RobotsChecker(f))
        assert res.status == ScrapeStatus.unsupported and res.items_found == 0, store
        assert any("not configured" in n for n in res.notes), store
    assert f.calls == []                                           # nothing fetched, nothing fabricated


def test_no_adapter_claims_verification_it_does_not_have():
    for s in SCRAPERS.values():
        if s.configured:   # configured means verified from a real page: it must say when and how
            assert s.verified_on != "" and s.extraction_method != "unverified"
        else:
            assert s.verified_on == "" and s.extraction_method == "unverified"


class ConfiguredDemo(JsonLdSearchScraper):
    store = "daraz"                       # stands in for any store AFTER it has been configured from recon
    base_url = "https://shop.test"
    search_url_template = "https://shop.test/s?q={query}&page={page}"


def _ld(*items):
    return "<script type='application/ld+json'>" + json.dumps(list(items)) + "</script>"


def test_configured_jsonld_adapter_end_to_end_with_fixture():
    html = _ld({"@type": "Product", "name": "Rice 1kg", "url": "/p/1",
                "offers": {"price": "120", "priceCurrency": "BDT"}})
    url = "https://shop.test/s?q=rice+bran&page=2"
    f = CountingFetcher({url: FetchResponse(200, html, "text/html", url)})
    res = ConfiguredDemo().run("rice bran", f, page=2)
    assert res.status == ScrapeStatus.success and res.items_found == 1 and f.calls == [url]


def test_configured_adapter_without_jsonld_explains_what_is_needed():
    url = "https://shop.test/s?q=rice&page=1"
    f = CountingFetcher({url: FetchResponse(200, "<html><body><div class='x'>items</div></body></html>", "text/html", url)})
    res = ConfiguredDemo().run("rice", f)
    assert res.status == ScrapeStatus.success and res.items_found == 0
    assert any("store-specific parser" in n for n in res.notes)