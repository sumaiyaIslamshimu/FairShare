"""Rokomari adapter (stationery, superstore and book items on rokomari.com).

VERIFIED on 2026-10-29 with the recon tool and two saved real pages (search results + one product page):
- robots.txt allowed fetching the search page.
- Search URL:  https://www.rokomari.com/search?term=<query>&dt=n        (page 1)
               https://www.rokomari.com/search?term=<query>&dt=n&page=2 (page 2 and later)
  60 results per page.
- The search page has NO JSON-LD. Every result is an HTML card:
      <a class="productContainer_productDetailsBody__*" href="/product/<id>/<slug>">   (books: /book/<id>/<slug>)
          title   <p class="productContainer_productTitle__*">
          brand   <p class="productContainer_productAuthor__*">   ("Non-Brand" when the store lists no brand)
          price   <p class="productContainer_productPrice__*">    ("৳269"), crossed-out old price in <del>
          image   <img data-src="https://rokbucket...">            (src is only a loading placeholder)
          stock   <p>Product in stock</p>                          (the line is simply absent on some cards)
  Class names end in a build hash (e.g. "__jdlDj") that can change when the site is redeployed, so this parser
  matches on the part BEFORE the hash.
- Product pages DO carry JSON-LD, but it is not used here on purpose: its "name" is the page title ("Domes Mini
  Sign Pen 1Pc: null | Rokomari.com"), it has no "url", and it would cost one extra request per product.
- Menu and footer links such as /product/activity-wise-recommendation/browse-page and
  /product/category/2102/Gift-Voucher are NOT result cards, so they are never read.

If the page layout changes, run recon again and update the selectors below; run() then reports a failure
instead of an empty success (see parse_listing).
Respect robots.txt and the site terms; a 403/429/captcha means "failure/unsupported", never a workaround.
"""
import re
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import JsonLdSearchScraper, ParseOutcome, RawProduct

_PRODUCT_HREF = re.compile(r"^/(?:product|book)/(\d+)/[^/?#\s]+")
_PLACEHOLDER_IMAGE = "placeholder-image"


def _text(tag) -> str | None:
    if tag is None:
        return None
    value = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
    return value or None


def _image_url(card) -> str | None:
    img = card.select_one('[class*="productContainer_bookImage"] img')
    if img is None:
        return None
    for attr in ("data-src", "src"):
        value = (img.get(attr) or "").strip()
        if value and _PLACEHOLDER_IMAGE not in value and not value.startswith("data:"):
            return value
    return None


class RokomariScraper(JsonLdSearchScraper):
    store = "rokomari"
    base_url = "https://www.rokomari.com"
    search_url_template = "https://www.rokomari.com/search?term={query}&dt=n&page={page}"
    verified_on = "2026-10-29"
    extraction_method = "html-cards"

    def search_url(self, query: str, page: int = 1) -> str:
        url = f"{self.base_url}/search?term={quote_plus(query)}&dt=n"
        return url if page <= 1 else f"{url}&page={page}"   # page 1 is the address without "page" (as the site links it)

    def parse_listing(self, html: str, page_url: str) -> ParseOutcome:
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select('a[class*="productContainer_productDetailsBody"]')
        if not cards:
            if soup.select_one("#ts--desktop-search-page") is not None:
                return ParseOutcome(products=[], notes=["the search page has no results."])
            # No results container at all: a layout change, a block page or an error page. Never report that as an
            # empty success: skipped=1 makes run() return "failure".
            return ParseOutcome(products=[], skipped=1,
                                notes=["no search results container found; the page layout may have changed "
                                       "or this is not a results page."])
        products, skipped = [], 0
        for card in cards:
            match = _PRODUCT_HREF.match((card.get("href") or "").strip())
            name = _text(card.select_one('p[class*="productContainer_productTitle"]'))
            price = _text(card.select_one('p[class*="productContainer_productPrice"]'))
            if not (match and name and price):
                skipped += 1
                continue
            products.append(RawProduct(
                store=self.store,
                name=name,
                product_url=urljoin(page_url, card["href"].strip()),
                price=price,                                   # raw text such as "৳269"; the normalizer parses it
                original_price=_text(card.select_one("del")),
                image_url=_image_url(card),
                brand=_text(card.select_one('p[class*="productContainer_productAuthor"]')),
                # The page only says "Product in stock"; when that line is missing the stock is unknown, not "out".
                availability="In Stock" if "product in stock" in card.get_text(" ").lower() else None,
                store_product_id=match.group(1),
            ))
        notes = [f"read {len(products)} of {len(cards)} result cards from the search page (html cards)."]
        return ParseOutcome(products=products, skipped=skipped, notes=notes)
