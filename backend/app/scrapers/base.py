"""Shared scraper foundation: polite fetching, robots.txt, result types, JSON-LD helpers.

Rules built in here (every store adapter inherits them):
- robots.txt is checked before any page is fetched. Disallowed -> status "unsupported".
- Honest User-Agent, request timeouts, minimum interval between requests.
- 403/401/429 are NOT retried and NOT bypassed; they are reported as failures.
- Only 5xx and timeouts are retried (bounded).
- Nothing here ever invents products. No products found -> empty list, never mock data.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from app.scrapers.robot_parser import WildcardRobotParser

USER_AGENT = "FairShareBot/0.1 (university project; price comparison; respects robots.txt)"


class ScrapeStatus(str, Enum):
    success = "success"          # fetched and parsed; items may be 0 (a valid empty result)
    partial = "partial"          # some items parsed, some skipped as invalid
    failure = "failure"          # blocked, HTTP error, timeout, or unparseable
    unsupported = "unsupported"  # robots.txt disallows, or no permitted extraction method


@dataclass
class RawProduct:
    """What an adapter extracted, before normalization. Values are raw strings/numbers."""
    store: str
    name: str | None = None
    product_url: str | None = None
    price: Any = None                 # raw: "৳ 1,299", 1299, "1299.00"
    currency: str | None = None       # raw: "BDT", "৳", None
    original_price: Any = None
    image_url: str | None = None
    brand: str | None = None
    category_text: str | None = None
    availability: str | None = None   # raw: "InStock", "In Stock", "Sold out"
    rating: Any = None
    review_count: Any = None
    store_product_id: str | None = None
    specs: dict = field(default_factory=dict)


@dataclass
class ParseOutcome:
    products: list[RawProduct]
    skipped: int = 0                  # items found on the page but unusable
    notes: list[str] = field(default_factory=list)


@dataclass
class ScrapeResult:
    store: str
    status: ScrapeStatus
    products: list[RawProduct] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    robots_allowed: bool | None = None
    skipped: int = 0
    http_status: int | None = None
    url: str | None = None

    @property
    def items_found(self) -> int:
        return len(self.products)


class FetchError(Exception):
    """kind: timeout | network | blocked (401/403) | rate_limited (429) | not_found | server_error | other"""

    def __init__(self, kind: str, message: str, status_code: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code


@dataclass
class FetchResponse:
    status_code: int
    text: str
    content_type: str = ""
    url: str = ""


class Fetcher(ABC):
    @abstractmethod
    def get(self, url: str) -> FetchResponse:
        """Returns the response for 2xx, raises FetchError otherwise."""


class HttpxFetcher(Fetcher):
    """Real HTTP fetcher (needs `httpx`). Polite: interval between requests, timeouts, bounded retries."""

    def __init__(self, min_interval: float = 2.0, timeout: float = 10.0, retries: int = 2):
        self.min_interval = min_interval
        self.timeout = timeout
        self.retries = retries
        self._last = 0.0

    def get(self, url: str) -> FetchResponse:
        import httpx  # imported here so tests do not need httpx

        attempt = 0
        while True:
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = httpx.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
                              timeout=httpx.Timeout(self.timeout, connect=5.0), follow_redirects=True)
            except httpx.TimeoutException:
                err = FetchError("timeout", "Request timed out.")
            except httpx.HTTPError:
                err = FetchError("network", "Network error while fetching the page.")
            else:
                code = r.status_code
                if 200 <= code < 300:
                    return FetchResponse(code, r.text, r.headers.get("content-type", ""), str(r.url))
                if code in (401, 403):
                    raise FetchError("blocked", f"Access refused by the site (HTTP {code}). Not bypassed.", code)
                if code == 429:
                    raise FetchError("rate_limited", "Rate limited by the site (HTTP 429). Not retried.", 429)
                if code == 404:
                    raise FetchError("not_found", "Page not found (HTTP 404).", 404)
                if code >= 500:
                    err = FetchError("server_error", f"Site error (HTTP {code}).", code)
                else:
                    raise FetchError("other", f"Unexpected HTTP status {code}.", code)
            attempt += 1
            if attempt > self.retries:  # only timeouts / network / 5xx reach here
                raise err
            time.sleep(min(2 ** attempt, 8))


class RobotsChecker:
    """Caches robots.txt per site. Conservative: if robots.txt cannot be read reliably, do NOT fetch."""

    def __init__(self, fetcher: Fetcher):
        self.fetcher = fetcher
        self._cache: dict[str, WildcardRobotParser | bool] = {}

    def allowed(self, url: str) -> bool:
        p = urlparse(url)
        origin = f"{p.scheme}://{p.netloc}"
        if origin not in self._cache:
            self._cache[origin] = self._load(origin)
        entry = self._cache[origin]
        if entry is True:       # no robots.txt (404) -> nothing is disallowed
            return True
        if entry is False:      # robots.txt unreadable -> be conservative
            return False
        return entry.allowed(url)

    def _load(self, origin: str):
        try:
            resp = self.fetcher.get(origin + "/robots.txt")
        except FetchError as e:
            return True if e.kind == "not_found" else False
        rp = WildcardRobotParser(user_agent=USER_AGENT)
        rp.parse(resp.text)
        return rp


class BaseScraper(ABC):
    """One subclass per store. Subclasses implement search_url() and parse_listing() only."""

    store: str = ""
    base_url: str = ""

    @abstractmethod
    def search_url(self, query: str, page: int = 1) -> str: ...

    @abstractmethod
    def parse_listing(self, html: str, page_url: str) -> ParseOutcome: ...

    def run(self, query: str, fetcher: Fetcher, robots: RobotsChecker | None = None,
            limit: int = 20, page: int = 1) -> ScrapeResult:
        """Never raises: every problem becomes a structured ScrapeResult for THIS store only."""
        url = self.search_url(query, page)
        result = ScrapeResult(store=self.store, status=ScrapeStatus.failure, url=url)
        try:
            if robots is not None:
                allowed = robots.allowed(url)
                result.robots_allowed = allowed
                if not allowed:
                    result.status = ScrapeStatus.unsupported
                    result.notes.append("robots.txt disallows (or could not confirm) automated access to this page.")
                    return result
            try:
                resp = fetcher.get(url)
            except FetchError as e:
                result.errors.append(f"{e.kind}: {e}")
                result.http_status = e.status_code
                return result
            result.http_status = resp.status_code
            ctype = resp.content_type.lower()
            if ctype and "html" not in ctype and "json" not in ctype:
                result.errors.append(f"unexpected content type: {ctype.split(';')[0]}")
                return result
            outcome = self.parse_listing(resp.text, resp.url or url)
            result.products = outcome.products[: max(0, limit)]
            result.skipped = outcome.skipped
            result.notes.extend(outcome.notes)
            if outcome.skipped and result.products:
                result.status = ScrapeStatus.partial
            elif outcome.skipped and not result.products:
                result.status = ScrapeStatus.failure
                result.errors.append("items were found on the page but none could be parsed (page layout may have changed).")
            else:
                result.status = ScrapeStatus.success
                if not result.products:
                    result.notes.append("valid empty result: the page contained no products.")
            return result
        except Exception as e:  # parser bug or unexpected markup must not crash a multi-store run
            result.status = ScrapeStatus.failure
            result.errors.append(f"parse error: {type(e).__name__}")
            return result


# ---------- structured data (JSON-LD) helpers ----------

def _type_matches(node: dict, wanted: str) -> bool:
    t = node.get("@type")
    return wanted in t if isinstance(t, list) else t == wanted


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for key in ("@graph", "itemListElement", "item", "mainEntity"):
            if key in node:
                yield from _walk(node[key])
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)


def extract_jsonld_products(html: str) -> list[dict]:
    """Returns schema.org Product objects found in <script type="application/ld+json"> blocks.
    Malformed JSON blocks are skipped, not fatal."""
    soup = BeautifulSoup(html, "lxml")
    found: list[dict] = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        text = tag.string or tag.get_text()
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            continue
        for node in _walk(data):
            if _type_matches(node, "Product"):
                found.append(node)
    return found


def jsonld_product_to_raw(store: str, node: dict) -> RawProduct:
    """Generic schema.org Product -> RawProduct. Only copies what the page actually states."""
    offers = node.get("offers")
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    offers = offers if isinstance(offers, dict) else {}
    price = offers.get("price")
    if price is None and isinstance(offers.get("priceSpecification"), dict):
        price = offers["priceSpecification"].get("price")
    image = node.get("image")
    if isinstance(image, list):
        image = image[0] if image else None
    if isinstance(image, dict):
        image = image.get("url")
    brand = node.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")
    rating = node.get("aggregateRating") if isinstance(node.get("aggregateRating"), dict) else {}
    category = node.get("category")
    return RawProduct(
        store=store,
        name=node.get("name"),
        product_url=node.get("url") or offers.get("url"),
        price=price,
        currency=offers.get("priceCurrency"),
        image_url=image if isinstance(image, str) else None,
        brand=brand if isinstance(brand, str) else None,
        category_text=category if isinstance(category, str) else None,
        availability=offers.get("availability"),
        rating=rating.get("ratingValue"),
        review_count=rating.get("reviewCount") or rating.get("ratingCount"),
        store_product_id=str(node.get("sku") or node.get("productID") or "") or None,
    )


class JsonLdSearchScraper(BaseScraper):
    """Store adapter for sites that publish schema.org Product data (JSON-LD) on public listing pages.

    A subclass must be CONFIGURED from a real recon report (python -m app.scrapers.recon <url>):
      base_url, search_url_template (with {query} and {page}), and the date/method it was verified.
    Until configured, run() reports status "unsupported" and makes NO network request.
    If a store does not publish JSON-LD, its subclass overrides parse_listing() with store-specific parsing
    written from the saved fixture, never from guesses."""

    search_url_template: str = ""        # e.g. "https://<host>/search?q={query}&page={page}"  (fill from recon)
    verified_on: str = ""                # date the URL pattern + method were checked on the real site
    extraction_method: str = "json-ld"   # what the recon report showed the page offers

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.search_url_template)

    def search_url(self, query: str, page: int = 1) -> str:
        from urllib.parse import quote_plus
        return self.search_url_template.format(query=quote_plus(query), page=page)

    def parse_listing(self, html: str, page_url: str) -> ParseOutcome:
        raws = [jsonld_product_to_raw(self.store, n) for n in extract_jsonld_products(html)]
        usable = [r for r in raws if r.name and r.price is not None and r.product_url]
        notes = [] if raws else ["page has no JSON-LD Product data; a store-specific parser is needed (see recon report)."]
        return ParseOutcome(products=usable, skipped=len(raws) - len(usable), notes=notes)

    def run(self, query, fetcher, robots=None, limit=20, page=1):
        if not self.configured:
            return ScrapeResult(
                store=self.store, status=ScrapeStatus.unsupported,
                notes=["not configured: no verified search URL / extraction method yet. "
                       "Run the recon tool on a real public page for this store, then fill in the adapter."])
        return super().run(query, fetcher, robots, limit, page)