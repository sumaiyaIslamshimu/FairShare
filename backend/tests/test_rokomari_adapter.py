"""Rokomari adapter tests. The small fixture (tests/fixtures/rokomari/search_cards.html) is a trimmed copy of the
real result cards saved from https://www.rokomari.com/search?term=bottle&dt=n on 2026-10-29. No live website is used.
If a full recon copy exists at tests/fixtures/rokomari/recon_page.html it is checked too (skipped otherwise)."""
from pathlib import Path

import pytest

from app.scrapers import get_scraper
from app.scrapers.base import FetchError, FetchResponse, Fetcher, RobotsChecker, ScrapeStatus
from app.scrapers.normalizer import normalize_product

FIXTURES = Path(__file__).parent / "fixtures" / "rokomari"
SEARCH = "https://www.rokomari.com/search?term=bottle&dt=n"


class Routes(Fetcher):
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url):
        self.calls.append(url)
        item = self.routes.get(url)
        if item is None:
            raise FetchError("not_found", "no route", 404)
        return item


def html_page(url, html):
    return FetchResponse(200, html, "text/html; charset=utf-8", url)


def cards_html():
    return (FIXTURES / "search_cards.html").read_text(encoding="utf-8")


def test_rokomari_is_configured_and_verified():
    s = get_scraper("rokomari")
    assert s.configured and s.verified_on == "2026-10-29" and s.extraction_method == "html-cards"


def test_search_urls_match_the_real_site():
    s = get_scraper("rokomari")
    assert s.search_url("bottle") == SEARCH
    assert s.search_url("bottle", 1) == SEARCH
    assert s.search_url("bottle", 2) == SEARCH + "&page=2"
    assert s.search_url("water bottle") == "https://www.rokomari.com/search?term=water+bottle&dt=n"


def test_parses_only_real_result_cards():
    out = get_scraper("rokomari").parse_listing(cards_html(), SEARCH)
    assert [p.store_product_id for p in out.products] == ["417949", "535165", "536663", "212947"]
    assert out.skipped == 1                                   # the card with no price
    urls = [p.product_url for p in out.products]
    assert not any("browse-page" in u or "Gift-Voucher" in u for u in urls)   # menu/footer links are not products
    assert urls[0].startswith("https://www.rokomari.com/product/417949/")
    assert urls[3].startswith("https://www.rokomari.com/book/212947/")


def test_fields_are_copied_exactly_as_the_page_states_them():
    by_id = {p.store_product_id: p for p in get_scraper("rokomari").parse_listing(cards_html(), SEARCH).products}
    muk = by_id["417949"]
    assert muk.name.startswith("Mukoko Half Gallon 64oz Water Bottle") and ": null" not in muk.name
    assert muk.price == "৳269" and muk.original_price == "৳320" and muk.brand == "Non-Brand"
    assert muk.image_url.startswith("https://rokbucket.rokomari.io/") and "placeholder" not in muk.image_url
    assert muk.availability == "In Stock"
    assert by_id["535165"].original_price is None             # no crossed-out price on this card
    assert by_id["536663"].availability is None               # no stock line: unknown, never "out of stock"


def test_normalizes_end_to_end():
    out = get_scraper("rokomari").parse_listing(cards_html(), SEARCH)
    n = normalize_product(out.products[0], "https://www.rokomari.com")
    assert n.price_paisa == 26900 and n.original_price_paisa == 32000 and n.discount_percent == 15.9
    assert n.currency == "BDT" and n.availability == "in_stock" and n.store_product_id == "417949"
    unknown = normalize_product(out.products[2], "https://www.rokomari.com")
    assert unknown.availability == "unknown"
    book = normalize_product(out.products[3], "https://www.rokomari.com")
    assert book.price_paisa == 37000 and book.brand == "ওয়াসি আহমেদ"


def test_run_checks_robots_and_reads_one_page():
    robots = FetchResponse(200, "User-agent: *\nAllow: /\n", "text/plain", "")
    f = Routes({"https://www.rokomari.com/robots.txt": robots, SEARCH: html_page(SEARCH, cards_html())})
    res = get_scraper("rokomari").run("bottle", f, robots=RobotsChecker(f))
    assert res.status == ScrapeStatus.partial and res.items_found == 4 and res.skipped == 1
    assert res.robots_allowed is True and f.calls == ["https://www.rokomari.com/robots.txt", SEARCH]


def test_robots_disallow_means_unsupported_and_no_page_fetch():
    robots = FetchResponse(200, "User-agent: *\nDisallow: /search\n", "text/plain", "")
    f = Routes({"https://www.rokomari.com/robots.txt": robots})
    res = get_scraper("rokomari").run("bottle", f, robots=RobotsChecker(f))
    assert res.status == ScrapeStatus.unsupported and SEARCH not in f.calls


def test_block_or_unknown_layout_is_a_failure_not_an_empty_success():
    f = Routes({SEARCH: html_page(SEARCH, "<html><body><h1>Please verify you are human</h1></body></html>")})
    res = get_scraper("rokomari").run("bottle", f)
    assert res.status == ScrapeStatus.failure and res.items_found == 0 and res.errors


def test_results_page_without_cards_is_a_valid_empty_result():
    html = '<html><body><main><div id="ts--desktop-search-page"><p>(Showing 0 items)</p></div></main></body></html>'
    url = "https://www.rokomari.com/search?term=zzzz&dt=n"
    f = Routes({url: html_page(url, html)})
    res = get_scraper("rokomari").run("zzzz", f)
    assert res.status == ScrapeStatus.success and res.items_found == 0


@pytest.mark.skipif(not (FIXTURES / "recon_page.html").exists(), reason="full recon copy not present")
def test_full_saved_search_page_if_available():
    html = (FIXTURES / "recon_page.html").read_text(encoding="utf-8")
    out = get_scraper("rokomari").parse_listing(html, SEARCH)
    ids = [p.store_product_id for p in out.products]
    assert len(out.products) >= 40 and len(ids) == len(set(ids))   # the real page lists 60 results
    for p in out.products:
        n = normalize_product(p, "https://www.rokomari.com")        # every parsed card must normalize cleanly
        assert n.price_paisa > 0 and n.currency == "BDT" and ": null" not in n.name
